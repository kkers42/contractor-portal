from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from db import fetch_query, execute_query
from auth import get_current_user
import requests
import os
from datetime import datetime, timedelta
import json

router = APIRouter()

# Weather API Configuration
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
WEATHER_API_BASE = "https://api.openweathermap.org/data/2.5"

# OpenAI for AI decision making
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

class WeatherAlert(BaseModel):
    property_ids: List[int]
    message: str
    forecast_hours: int = 24

@router.get("/weather/current/")
async def get_current_weather(
    lat: float,
    lon: float,
    current_user: dict = Depends(get_current_user)
):
    """Get current weather for a location"""
    if not WEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="Weather API key not configured")

    try:
        url = f"{WEATHER_API_BASE}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": WEATHER_API_KEY,
            "units": "imperial"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        return {
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather: {str(e)}")

@router.get("/weather/forecast/")
async def get_weather_forecast(
    lat: float,
    lon: float,
    current_user: dict = Depends(get_current_user)
):
    """Get 5-day weather forecast"""
    if not WEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="Weather API key not configured")

    try:
        url = f"{WEATHER_API_BASE}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": WEATHER_API_KEY,
            "units": "imperial"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Process forecast data
        forecasts = []
        for item in data["list"]:
            # Check for snow in weather conditions
            snow_amount = 0
            if "snow" in item and "3h" in item["snow"]:
                # Convert from mm to inches (1mm = 0.0393701 inches)
                snow_amount = item["snow"]["3h"] * 0.0393701

            forecasts.append({
                "datetime": item["dt_txt"],
                "temperature": item["main"]["temp"],
                "description": item["weather"][0]["description"],
                "snow_3h": snow_amount,
                "precipitation_probability": item.get("pop", 0) * 100,
                "wind_speed": item["wind"]["speed"]
            })

        return {
            "city": data["city"]["name"],
            "forecasts": forecasts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch forecast: {str(e)}")

@router.get("/weather/properties-forecast/")
async def get_properties_weather_forecast(
    current_user: dict = Depends(get_current_user)
):
    """Get weather forecast for all properties with coordinates"""

    # Get all properties with coordinates
    query = """
        SELECT id, name, address, latitude, longitude, trigger_type, trigger_amount,
               area_manager, open_by_time
        FROM locations
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """

    properties = fetch_query(query)

    if not properties:
        return {"message": "No properties with coordinates found", "properties": []}

    # Group properties by approximate location to reduce API calls
    # Round to 2 decimal places (~1km accuracy)
    location_groups = {}
    for prop in properties:
        lat_rounded = round(prop["latitude"], 2)
        lon_rounded = round(prop["longitude"], 2)
        key = f"{lat_rounded},{lon_rounded}"

        if key not in location_groups:
            location_groups[key] = {
                "lat": lat_rounded,
                "lon": lon_rounded,
                "properties": []
            }
        location_groups[key]["properties"].append(prop)

    # Fetch forecast for each location group
    results = []
    for key, group in location_groups.items():
        try:
            forecast = await get_weather_forecast(
                lat=group["lat"],
                lon=group["lon"],
                current_user=current_user
            )

            # Calculate total snow expected in next 24 hours
            total_snow_24h = 0
            now = datetime.now()
            cutoff = now + timedelta(hours=24)

            for f in forecast["forecasts"]:
                forecast_time = datetime.strptime(f["datetime"], "%Y-%m-%d %H:%M:%S")
                if forecast_time <= cutoff:
                    total_snow_24h += f["snow_3h"]

            # Check which properties will exceed trigger
            for prop in group["properties"]:
                trigger = prop.get("trigger_amount", 2.0)
                needs_service = total_snow_24h >= trigger

                results.append({
                    "property_id": prop["id"],
                    "property_name": prop["name"],
                    "address": prop["address"],
                    "area_manager": prop["area_manager"],
                    "trigger_amount": trigger,
                    "trigger_type": prop["trigger_type"],
                    "forecast_snow_24h": round(total_snow_24h, 2),
                    "needs_service": needs_service,
                    "open_by_time": prop["open_by_time"],
                    "forecast": forecast["forecasts"][:8]  # Next 24 hours (8 x 3-hour periods)
                })
        except Exception as e:
            print(f"Error fetching forecast for {key}: {str(e)}")
            continue

    return {
        "total_properties": len(results),
        "properties_needing_service": sum(1 for r in results if r["needs_service"]),
        "properties": results
    }

@router.get("/weather/ai-summary/")
async def get_weather_ai_summary(current_user: dict = Depends(get_current_user)):
    """Get AI-powered weather summary and recommendations"""

    if not OPENAI_API_KEY:
        return {
            "message": "AI summary requires OpenAI API key",
            "summary": "Configure OPENAI_API_KEY environment variable for AI-powered summaries."
        }

    # Get forecast for all properties
    forecast_data = await get_properties_weather_forecast(current_user)

    if forecast_data["properties_needing_service"] == 0:
        return {
            "summary": "No snow forecasted for the next 24 hours. All properties are clear.",
            "properties_needing_service": 0,
            "recommended_actions": []
        }

    # Prepare data for AI
    properties_needing_service = [
        p for p in forecast_data["properties"] if p["needs_service"]
    ]

    # Build AI prompt
    prompt = f"""You are a snow removal operations manager. Analyze this weather forecast and provide actionable recommendations.

Weather Forecast Summary:
- Total properties monitored: {forecast_data['total_properties']}
- Properties needing service: {forecast_data['properties_needing_service']}

Properties requiring service in next 24 hours:
"""

    for prop in properties_needing_service[:10]:  # Limit to first 10 for prompt size
        prompt += f"\n- {prop['property_name']} ({prop['address']})"
        prompt += f"\n  Trigger: {prop['trigger_amount']}\", Forecast: {prop['forecast_snow_24h']}\""
        if prop['open_by_time']:
            prompt += f", Must open by: {prop['open_by_time']}"
        prompt += f"\n  Manager: {prop['area_manager']}"

    prompt += "\n\nProvide:\n1. A 2-3 sentence executive summary\n2. Recommended start time for snow removal\n3. Priority properties (those with earliest open-by times)\n4. Estimated crew requirements"

    try:
        import openai
        openai.api_key = OPENAI_API_KEY

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a snow removal operations manager."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        ai_summary = response.choices[0].message.content

        return {
            "summary": ai_summary,
            "properties_needing_service": forecast_data["properties_needing_service"],
            "properties": properties_needing_service,
            "forecast_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "summary": f"Error generating AI summary: {str(e)}",
            "properties_needing_service": forecast_data["properties_needing_service"],
            "properties": properties_needing_service
        }

@router.post("/weather/send-alert/")
async def send_weather_alert(
    alert: WeatherAlert,
    current_user: dict = Depends(get_current_user)
):
    """Send weather alert email to managers"""

    # Get AI summary
    summary = await get_weather_ai_summary(current_user)

    # TODO: Implement email sending via Gmail API or SMTP
    # For now, just return the summary

    return {
        "message": "Weather alert prepared (email sending not yet configured)",
        "alert": alert,
        "summary": summary
    }

@router.get("/weather/settings/")
async def get_weather_settings(current_user: dict = Depends(get_current_user)):
    """Get weather monitoring settings"""

    return {
        "weather_api_configured": bool(WEATHER_API_KEY),
        "ai_enabled": bool(OPENAI_API_KEY),
        "api_provider": "OpenWeatherMap" if WEATHER_API_KEY else "Not configured",
        "forecast_interval_minutes": 30,
        "alert_threshold_hours": 24
    }

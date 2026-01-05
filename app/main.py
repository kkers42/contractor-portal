from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from routers.auth_oidc import router as auth_router
from pathlib import Path
import os

# Read version from VERSION file
VERSION_FILE = Path(__file__).parent.parent / "VERSION"
try:
    with open(VERSION_FILE, 'r') as f:
        APP_VERSION = f.read().strip()
except:
    APP_VERSION = "unknown"

# Initialize logging system with Discord integration
from utils.logger import get_logger
logger = get_logger(__name__)
logger.info(f"Starting Contractor App v{APP_VERSION}")

app = FastAPI(title="Contractor App", version=APP_VERSION)

# Add SessionMiddleware BEFORE other middleware (required for OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('APP_JWT_SECRET', 'change-me-in-production-please-use-a-long-random-string')
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
def serve_home():
    return FileResponse("static/Home.html")

from routes import (
    auth_routes,
    property_routes,
    product_routes,
    ops_routes,
    report_routes,
    misc_routes,
    equipment_routes,
    ai_routes,
    property_list_routes,
    route_routes,
    weather_routes,
    settings_routes,
    tenant_routes,
    winter_event_routes,
    assignment_routes,
    sms_routes,
    n8n_routes,
    n8n_auth_routes,
    quickbooks_routes,
    email_routes,
    checkin_routes
)

app.include_router(auth_routes.router)
app.include_router(property_routes.router)
app.include_router(product_routes.router)
app.include_router(ops_routes.router)
app.include_router(report_routes.router)
app.include_router(misc_routes.router)
app.include_router(equipment_routes.router)
app.include_router(ai_routes.router)
app.include_router(property_list_routes.router)
app.include_router(route_routes.router)
app.include_router(weather_routes.router)
app.include_router(settings_routes.router)
app.include_router(tenant_routes.router)
app.include_router(winter_event_routes.router)
app.include_router(assignment_routes.router)
app.include_router(sms_routes.router)
app.include_router(n8n_routes.router)
app.include_router(n8n_auth_routes.router)
app.include_router(quickbooks_routes.router)
app.include_router(email_routes.router)
app.include_router(checkin_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False) # change for server hose 0.0.0.0 port 8080



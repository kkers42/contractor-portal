from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user
from db import fetch_query
import os
import httpx
from typing import List, Dict

router = APIRouter()

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    page_context: str = None  # Which page user is on (e.g., 'WinterOpsLog', 'MyTickets')

class ChatResponse(BaseModel):
    message: str
    suggestions: List[str] = []

def get_user_context(current_user: dict) -> str:
    """Get relevant context about the current user"""
    user_id = current_user["id"]
    user_role = current_user["role"]
    user_name = current_user["name"]

    # Get user's assigned properties
    properties = fetch_query(
        """SELECT l.id, l.name, l.address
           FROM locations l
           JOIN property_assignments pa ON l.id = pa.property_id
           WHERE pa.contractor_id = %s""",
        (user_id,)
    )

    # Get active tickets
    active_tickets = fetch_query(
        """SELECT w.id, l.name as property_name, w.time_in
           FROM winter_ops_logs w
           JOIN locations l ON w.property_id = l.id
           WHERE w.contractor_id = %s AND w.time_out IS NULL
           AND DATE(w.time_in) = CURDATE()""",
        (user_id,)
    )

    context = f"User: {user_name} (Role: {user_role})\n"

    if properties:
        context += f"\nAssigned Properties ({len(properties)}):\n"
        for prop in properties[:5]:  # Limit to 5 to avoid token bloat
            context += f"- {prop['name']} ({prop['address']})\n"

    if active_tickets:
        context += f"\nActive Tickets ({len(active_tickets)}):\n"
        for ticket in active_tickets:
            context += f"- {ticket['property_name']} (started: {ticket['time_in']})\n"

    return context

def get_system_prompt(page_context: str, user_context: str) -> str:
    """Generate context-aware system prompt based on current page"""

    base_prompt = """You are a helpful AI assistant for a snow removal and landscaping contractor portal.
You help contractors and workers with:
- Filling out work logs and forms
- Finding property information
- Understanding their active tickets
- Answering questions about equipment and procedures

Be concise, friendly, and practical. Focus on helping them get work done quickly.
"""

    page_prompts = {
        "WinterOpsLog": """
The user is currently filling out a Winter Operations Log. Help them with:
- Choosing the right property from their assignments
- Selecting appropriate equipment
- Recording material quantities (salt, calcium chloride)
- Timing information (time in/out)
""",
        "GreenOpsLog": """
The user is currently filling out a Green Services Log. Help them with:
- Choosing the right property
- Selecting service type (mowing, trimming, etc.)
- Recording products used and quantities
""",
        "MyTickets": """
The user is viewing their active tickets. Help them with:
- Understanding which properties have active tickets
- How to start a new ticket
- How to finish an existing ticket
- Viewing ticket history
""",
        "PropertyInfo": """
The user is viewing property information. Help them with:
- Finding specific properties
- Understanding property details (size, services needed)
- Looking up addresses
"""
    }

    full_prompt = base_prompt + "\n" + user_context

    if page_context and page_context in page_prompts:
        full_prompt += "\n" + page_prompts[page_context]

    return full_prompt

@router.post("/ai/chat/")
async def chat_with_ai(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
) -> ChatResponse:
    """Chat with AI assistant using OpenAI API"""

    # Check if API key is configured
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="AI assistant is not configured. Please contact administrator to set up OpenAI API key."
        )

    # Get user context
    user_context = get_user_context(current_user)

    # Build system prompt
    system_prompt = get_system_prompt(request.page_context, user_context)

    # Build messages for OpenAI
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})

    # Call OpenAI API
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",  # Fast and cheap
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500  # Keep responses concise
                }
            )

            if response.status_code != 200:
                error_detail = response.json().get("error", {}).get("message", "Unknown error")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenAI API error: {error_detail}"
                )

            result = response.json()
            ai_message = result["choices"][0]["message"]["content"]

            return ChatResponse(
                message=ai_message,
                suggestions=[]  # TODO: Add smart suggestions based on context
            )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI assistant timed out. Please try again.")
    except Exception as e:
        print(f"[ERROR] AI chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI assistant error: {str(e)}")

@router.get("/ai/suggestions/")
async def get_suggestions(
    page: str = None,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, List[str]]:
    """Get context-aware suggestions for the current page"""

    suggestions = {
        "WinterOpsLog": [
            "What equipment should I use for this property?",
            "How much salt is typical for a small lot?",
            "What should I put in the notes field?",
        ],
        "MyTickets": [
            "Which properties need service today?",
            "How do I start a ticket?",
            "Show me my ticket history",
        ],
        "PropertyInfo": [
            "Which properties am I assigned to?",
            "What services does this property need?",
            "Where is this property located?",
        ],
        "default": [
            "How do I fill out a winter log?",
            "Where can I see my active tickets?",
            "What are my assigned properties?",
        ]
    }

    return {
        "suggestions": suggestions.get(page, suggestions["default"])
    }

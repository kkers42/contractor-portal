from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user
from db import fetch_query, execute_query
import os
import httpx
import json
from typing import List, Dict, Optional
from datetime import datetime

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
    # JWT payload has "sub" (user ID as string) and "role"
    user_id = int(current_user["sub"])
    user_role = current_user["role"]

    # Get user's name from database
    user_info = fetch_query("SELECT name FROM users WHERE id = %s", (user_id,))
    user_name = user_info[0]["name"] if user_info else "User"

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

def get_available_tools() -> List[Dict]:
    """Define tools (functions) that ChatGPT can call"""
    return [
        {
            "type": "function",
            "function": {
                "name": "query_winter_logs",
                "description": "Query winter operations logs with optional filters. Use this to view, search, or analyze winter logs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                        "property_id": {"type": "integer", "description": "Filter by property ID"},
                        "contractor_name": {"type": "string", "description": "Filter by contractor name"},
                        "limit": {"type": "integer", "description": "Max number of results (default 20)"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "update_winter_log",
                "description": "Update a specific winter operations log by ID. Use this to edit/fix log data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "log_id": {"type": "integer", "description": "The ID of the log to update"},
                        "contractor_name": {"type": "string", "description": "New contractor name"},
                        "worker_name": {"type": "string", "description": "New worker name"},
                        "equipment": {"type": "string", "description": "Equipment used"},
                        "bulk_salt_qty": {"type": "number", "description": "Bulk salt quantity in tons"},
                        "bag_salt_qty": {"type": "number", "description": "Bag salt quantity"},
                        "calcium_chloride_qty": {"type": "number", "description": "Calcium chloride in lbs"},
                        "notes": {"type": "string", "description": "Log notes"}
                    },
                    "required": ["log_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_report",
                "description": "Generate a summary report of winter logs with totals and statistics.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                        "property_id": {"type": "integer", "description": "Filter by property"},
                        "contractor_name": {"type": "string", "description": "Filter by contractor"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_properties",
                "description": "Get list of properties/locations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search": {"type": "string", "description": "Search by property name or address"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_winter_log",
                "description": "Create a new winter operations log. Use this to copy logs or create new entries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "property_id": {"type": "integer", "description": "Property ID"},
                        "contractor_name": {"type": "string", "description": "Contractor name"},
                        "worker_name": {"type": "string", "description": "Worker name"},
                        "equipment": {"type": "string", "description": "Equipment used"},
                        "time_in": {"type": "string", "description": "Time in (YYYY-MM-DD HH:MM:SS)"},
                        "time_out": {"type": "string", "description": "Time out (YYYY-MM-DD HH:MM:SS)"},
                        "bulk_salt_qty": {"type": "number", "description": "Bulk salt quantity in tons"},
                        "bag_salt_qty": {"type": "number", "description": "Bag salt quantity"},
                        "calcium_chloride_qty": {"type": "number", "description": "Calcium chloride in lbs"},
                        "winter_event_id": {"type": "integer", "description": "Winter event ID"},
                        "notes": {"type": "string", "description": "Log notes"}
                    },
                    "required": ["property_id", "contractor_name", "time_in"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_winter_events",
                "description": "Get list of winter events.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_name": {"type": "string", "description": "Filter by event name"}
                    }
                }
            }
        }
    ]

def execute_tool(tool_name: str, arguments: Dict, current_user: dict) -> Dict:
    """Execute a tool function and return the result"""

    if tool_name == "query_winter_logs":
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        property_id = arguments.get("property_id")
        contractor_name = arguments.get("contractor_name")
        limit = arguments.get("limit", 20)

        where_parts = []
        params = []

        if start_date and end_date:
            where_parts.append("w.time_in BETWEEN %s AND %s")
            params += [start_date, end_date]
        if property_id:
            where_parts.append("w.property_id = %s")
            params.append(property_id)
        if contractor_name:
            where_parts.append("w.contractor_name LIKE %s")
            params.append(f"%{contractor_name}%")

        where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""

        query = f"""
            SELECT w.id, l.name as property_name, w.contractor_name, w.worker_name,
                   w.equipment, w.time_in, w.time_out, w.bulk_salt_qty, w.bag_salt_qty,
                   w.calcium_chloride_qty, w.notes, we.event_name as winter_event
            FROM winter_ops_logs w
            JOIN locations l ON w.property_id = l.id
            LEFT JOIN winter_events we ON w.winter_event_id = we.id
            {where_clause}
            ORDER BY w.time_in DESC
            LIMIT {limit}
        """

        logs = fetch_query(query, params if params else None)

        # Convert datetime objects to strings for JSON serialization
        for log in logs:
            if log.get('time_in'):
                log['time_in'] = str(log['time_in'])
            if log.get('time_out'):
                log['time_out'] = str(log['time_out'])

        return {"status": "success", "logs": logs, "count": len(logs)}

    elif tool_name == "update_winter_log":
        # Check permissions
        if current_user.get("role") not in ["Admin", "Manager"]:
            return {"status": "error", "message": "Only Admins and Managers can edit logs"}

        log_id = arguments.get("log_id")
        if not log_id:
            return {"status": "error", "message": "log_id is required"}

        # Build UPDATE query dynamically
        updates = []
        params = []

        for field in ["contractor_name", "worker_name", "equipment", "bulk_salt_qty",
                      "bag_salt_qty", "calcium_chloride_qty", "notes"]:
            if field in arguments and arguments[field] is not None:
                updates.append(f"{field} = %s")
                params.append(arguments[field])

        if not updates:
            return {"status": "error", "message": "No fields to update"}

        params.append(log_id)
        query = f"UPDATE winter_ops_logs SET {', '.join(updates)} WHERE id = %s"

        try:
            execute_query(query, params)
            return {"status": "success", "message": f"Log {log_id} updated successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif tool_name == "generate_report":
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        property_id = arguments.get("property_id")
        contractor_name = arguments.get("contractor_name")

        where_parts = []
        params = []

        if start_date and end_date:
            where_parts.append("w.time_in BETWEEN %s AND %s")
            params += [start_date, end_date]
        if property_id:
            where_parts.append("w.property_id = %s")
            params.append(property_id)
        if contractor_name:
            where_parts.append("w.contractor_name LIKE %s")
            params.append(f"%{contractor_name}%")

        where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""

        query = f"""
            SELECT
                COUNT(*) as total_logs,
                SUM(TIMESTAMPDIFF(SECOND, w.time_in, w.time_out) / 3600) as total_hours,
                SUM(w.bulk_salt_qty) as total_bulk_salt,
                SUM(w.bag_salt_qty) as total_bag_salt,
                SUM(w.calcium_chloride_qty) as total_calcium,
                COUNT(DISTINCT w.property_id) as properties_serviced,
                COUNT(DISTINCT w.contractor_name) as contractors_used
            FROM winter_ops_logs w
            {where_clause}
        """

        result = fetch_query(query, params if params else None)
        if result:
            report = result[0]
            report["total_hours"] = round(float(report["total_hours"] or 0), 2)
            report["total_bulk_salt"] = round(float(report["total_bulk_salt"] or 0), 2)
            report["total_calcium"] = round(float(report["total_calcium"] or 0), 2)
            return {"status": "success", "report": report}
        return {"status": "error", "message": "No data found"}

    elif tool_name == "get_properties":
        search = arguments.get("search")

        if search:
            query = "SELECT id, name, address FROM locations WHERE name LIKE %s OR address LIKE %s LIMIT 10"
            params = (f"%{search}%", f"%{search}%")
        else:
            query = "SELECT id, name, address FROM locations LIMIT 20"
            params = None

        properties = fetch_query(query, params)
        return {"status": "success", "properties": properties}

    elif tool_name == "get_winter_events":
        event_name = arguments.get("event_name")

        if event_name:
            query = "SELECT id, event_name, start_date, end_date, status FROM winter_events WHERE event_name LIKE %s"
            params = (f"%{event_name}%",)
        else:
            query = "SELECT id, event_name, start_date, end_date, status FROM winter_events ORDER BY start_date DESC LIMIT 20"
            params = None

        events = fetch_query(query, params)

        # Convert datetime objects to strings
        for event in events:
            if event.get('start_date'):
                event['start_date'] = str(event['start_date'])
            if event.get('end_date'):
                event['end_date'] = str(event['end_date'])

        return {"status": "success", "events": events}

    elif tool_name == "create_winter_log":
        # Check permissions
        if current_user.get("role") not in ["Admin", "Manager"]:
            return {"status": "error", "message": "Only Admins and Managers can create logs"}

        # Get required fields
        property_id = arguments.get("property_id")
        contractor_name = arguments.get("contractor_name")
        time_in = arguments.get("time_in")

        if not property_id or not contractor_name or not time_in:
            return {"status": "error", "message": "property_id, contractor_name, and time_in are required"}

        # Get user ID from current_user
        user_id = int(current_user.get("sub"))

        # Build INSERT query
        query = """
            INSERT INTO winter_ops_logs
            (property_id, contractor_id, contractor_name, worker_name, equipment,
             time_in, time_out, bulk_salt_qty, bag_salt_qty, calcium_chloride_qty,
             winter_event_id, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        params = (
            property_id,
            user_id,  # contractor_id (user creating the log)
            contractor_name,
            arguments.get("worker_name", ""),
            arguments.get("equipment", ""),
            time_in,
            arguments.get("time_out"),
            arguments.get("bulk_salt_qty", 0),
            arguments.get("bag_salt_qty", 0),
            arguments.get("calcium_chloride_qty", 0),
            arguments.get("winter_event_id"),
            arguments.get("notes", "")
        )

        try:
            execute_query(query, params)
            return {"status": "success", "message": "Winter log created successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return {"status": "error", "message": f"Unknown tool: {tool_name}"}

def get_system_prompt(page_context: str, user_context: str) -> str:
    """Generate context-aware system prompt based on current page"""

    base_prompt = """You are a helpful AI assistant for a snow removal and landscaping contractor portal.
You help contractors and workers with:
- Viewing and analyzing work logs
- Editing and updating log data (Admins/Managers only)
- Generating reports and statistics
- Finding property information
- Understanding their active tickets
- Answering questions about equipment and procedures

You have access to tools/functions to query the database, edit logs, and generate reports.
Use these tools when the user asks to view logs, edit data, or generate reports.

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

    # Get available tools
    tools = get_available_tools()

    # Call OpenAI API with function calling
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # First API call
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4-turbo-preview",  # GPT-4 Turbo supports function calling well
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",  # Let GPT decide when to use tools
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )

            if response.status_code != 200:
                error_detail = response.json().get("error", {}).get("message", "Unknown error")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenAI API error: {error_detail}"
                )

            result = response.json()
            assistant_message = result["choices"][0]["message"]

            # Check if GPT wants to call a tool
            if assistant_message.get("tool_calls"):
                # Execute each tool call
                messages.append(assistant_message)

                for tool_call in assistant_message["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])

                    print(f"[INFO] Executing tool: {function_name} with args: {function_args}")

                    # Execute the tool
                    tool_result = execute_tool(function_name, function_args, current_user)

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tool_result)
                    })

                # Make second API call with tool results
                response2 = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4-turbo-preview",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )

                if response2.status_code != 200:
                    error_detail = response2.json().get("error", {}).get("message", "Unknown error")
                    raise HTTPException(
                        status_code=response2.status_code,
                        detail=f"OpenAI API error: {error_detail}"
                    )

                result2 = response2.json()
                final_message = result2["choices"][0]["message"]["content"]

                return ChatResponse(
                    message=final_message,
                    suggestions=[]
                )

            else:
                # No tool calls, just return the message
                ai_message = assistant_message.get("content", "I'm here to help!")

                return ChatResponse(
                    message=ai_message,
                    suggestions=[]
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
            "Show me recent logs for this property",
            "Generate a report for this week",
            "What equipment was used last time?",
        ],
        "ViewWinterLogs": [
            "Show logs from yesterday",
            "Generate a report for December",
            "Update log #10 to fix contractor name",
        ],
        "Reports": [
            "Generate a report for last month",
            "Show total hours for Agri Farms",
            "How much salt was used in total?",
        ],
        "MyTickets": [
            "Which properties need service today?",
            "Show my logs from this week",
            "What's my total hours?",
        ],
        "PropertyInfo": [
            "Show all properties",
            "Find property near Main St",
            "What logs exist for this property?",
        ],
        "default": [
            "Show my recent logs",
            "Generate a weekly report",
            "What properties do I have?",
        ]
    }

    return {
        "suggestions": suggestions.get(page, suggestions["default"])
    }

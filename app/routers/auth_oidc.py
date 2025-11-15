from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request as StarletteRequest
from jose import jwt
from datetime import datetime, timedelta

from config.auth_settings import settings
from db.identities import (
    get_user_by_identity, get_user_by_email, create_user,
    upsert_identity, touch_last_login,
)

router = APIRouter(prefix="/auth", tags=["auth"])
oauth = OAuth()

oauth.register(
    name="google",
    server_metadata_url=settings.GOOGLE_DISCOVERY_URL,
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"}
)

oauth.register(
    name="microsoft",
    server_metadata_url=settings.MS_DISCOVERY_URL,
    client_id=settings.MS_CLIENT_ID,
    client_secret=settings.MS_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"}
)

def _issue_app_jwt(user_id: int, role: str = "User"):
    exp = datetime.utcnow() + timedelta(minutes=settings.APP_JWT_EXP_MIN)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iss": settings.APP_JWT_ISS,
        "exp": int(exp.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
    }
    return jwt.encode(payload, settings.APP_JWT_SECRET, algorithm="HS256")

def _provider(name: str):
    if name not in ("google", "microsoft"):
        raise HTTPException(404, "Unknown provider")
    return oauth.create_client(name)

@router.get("/{provider}/start")
async def start(request: Request, provider: str):
    client = _provider(provider)
    redirect_uri = f"{settings.APP_BASE_URL}/auth/{provider}/callback"
    return await client.authorize_redirect(StarletteRequest(request.scope), redirect_uri)

@router.get("/{provider}/callback")
async def callback(request: Request, provider: str):
    client = _provider(provider)
    try:
        token = await client.authorize_access_token(StarletteRequest(request.scope))
    except Exception as e:
        raise HTTPException(400, f"OIDC authorization failed: {e}")

    userinfo = token.get("userinfo")
    if not userinfo:
        try:
            userinfo = await client.parse_id_token(StarletteRequest(request.scope), token)
        except Exception:
            userinfo = await client.userinfo(token=token)

    sub = userinfo.get("sub")
    email = userinfo.get("email")
    email_verified = bool(userinfo.get("email_verified", False))
    name = userinfo.get("name") or userinfo.get("given_name")
    picture = userinfo.get("picture")

    if not sub:
        raise HTTPException(400, "OIDC response missing 'sub'")

    user_id = get_user_by_identity(provider, sub)
    user_status = None
    user_role = "User"
    
    if not user_id:
        if email:
            existing = get_user_by_email(email)
            if existing:
                user_id, user_status, user_role = existing
        
        if not user_id:
            # New user - create in pending status
            user_id = create_user(email=email, display_name=name, avatar_url=picture)
            user_status = "pending"
        
        upsert_identity(user_id, provider, sub, email, email_verified)
    else:
        # Existing identity - get their status and role
        from db.identities import get_user_status_and_role
        user_status, user_role = get_user_status_and_role(user_id)

    # Check if user is approved
    if user_status == "pending":
        # Redirect to a "pending approval" page instead of giving them a token
        return RedirectResponse(f"{settings.APP_BASE_URL}/static/pending-approval.html", status_code=302)
    
    if user_status == "suspended":
        raise HTTPException(403, "Your account has been suspended. Contact an administrator.")

    touch_last_login(user_id)
    app_jwt = _issue_app_jwt(user_id=user_id, role=user_role)
    return RedirectResponse(f"{settings.APP_BASE_URL}/static/login.html#token={app_jwt}", status_code=302)

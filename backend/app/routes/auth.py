# Auth route — validates admin credentials against values loaded from config.
from fastapi import APIRouter, HTTPException
from app.models import LoginRequest
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD

router = APIRouter()


# Accepts a username/password pair and checks them against the single admin account.
# Returns {"success": True} on a match, or a 401 if credentials are incorrect.
# There is no session or token issued here — the frontend handles auth state client-side.
@router.post("/api/authenticate")
async def authenticate(body: LoginRequest):
    if body.username == ADMIN_USERNAME and body.password == ADMIN_PASSWORD:
        return {"success": True}
    raise HTTPException(status_code=401, detail="Invalid username or password")

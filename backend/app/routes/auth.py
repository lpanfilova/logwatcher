from fastapi import APIRouter, HTTPException
from app.models import LoginRequest
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD

router = APIRouter()


@router.post("/api/authenticate")
async def authenticate(body: LoginRequest):
    if body.username == ADMIN_USERNAME and body.password == ADMIN_PASSWORD:
        return {"success": True}
    raise HTTPException(status_code=401, detail="Invalid username or password")

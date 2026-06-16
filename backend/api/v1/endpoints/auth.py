"""Authentication Endpoints"""
from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from core.security import create_access_token, get_password_hash, verify_password
from schemas.invoice import TokenResponse, UserLogin

router = APIRouter()

# Demo user store (replace with real DB in production)
DEMO_USERS = {
    "admin": get_password_hash("admin123"),
    "demo": get_password_hash("demo123"),
}


@router.post("/token", response_model=TokenResponse, summary="Get JWT access token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate and get a JWT token.

    **Demo credentials:**
    - username: `admin` / password: `admin123`
    - username: `demo` / password: `demo123`
    """
    hashed = DEMO_USERS.get(form_data.username)
    if not hashed or not verify_password(form_data.password, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": form_data.username})
    return TokenResponse(access_token=token)


@router.post("/register", summary="Register a new user (demo)")
async def register(user: UserLogin):
    """Register endpoint (demo - stores in memory)."""
    if user.username in DEMO_USERS:
        raise HTTPException(status_code=400, detail="Username already exists.")
    DEMO_USERS[user.username] = get_password_hash(user.password)
    return {"message": f"User '{user.username}' registered successfully."}
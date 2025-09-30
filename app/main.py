"""
FastAPI JWT Authentication Demo
================================
This application demonstrates:
- User login with username/password
- JWT token generation and validation
- Password hashing with bcrypt
- Protected routes requiring authentication
- Role-based access control (admin routes)
- Token expiration handling

For educational purposes only - not production-ready!
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import jwt
import memcache
from passlib.context import CryptContext

# --- App Initialization ---
app = FastAPI()
# HTTPBearer extracts the token from the "Authorization: Bearer <token>" header
bearer = HTTPBearer()

# --- Security Settings ---
# WARNING: In production, never hardcode secrets! Use environment variables.
SECRET_KEY = "your-secret-key"  # Used to sign and verify JWT tokens
ALGORITHM = "HS256"  # HMAC with SHA-256 algorithm for signing tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 2  # Intentionally short to demonstrate expiration
# CryptContext handles password hashing - bcrypt is slow on purpose to prevent brute force attacks
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Connect to Memcached ---
# Memcached stores user data (simulates a database for this demo)
# 'memcached:11211' is the Docker service name and port
mc = memcache.Client(['memcached:11211'], debug=0)


# --- Pydantic Schemas ---
# These models define the structure of data coming in and going out of the API

class Token(BaseModel):
    """Response model for successful login - returns a JWT token"""
    access_token: str  # The JWT token string
    token_type: str    # Always "bearer" for this auth type

class LoginRequest(BaseModel):
    """Request model for login - user provides username and password"""
    username: str
    password: str

# --- Helper Functions ---

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Creates a JWT token with user information and expiration time.

    Args:
        data: Dictionary containing user info (typically {"sub": username})
        expires_delta: Optional custom expiration time, defaults to ACCESS_TOKEN_EXPIRE_MINUTES

    Returns:
        A signed JWT token string
    """
    to_encode = data.copy()  # Don't modify the original dict
    # Calculate when the token expires (current time + expiration duration)
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})  # Add expiration to the token payload
    # Sign the token with our secret key - only we can create valid tokens
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain: str, hashed: str) -> bool:
    """
    Securely compares a plain text password with a bcrypt hashed password.

    Args:
        plain: The password the user typed in
        hashed: The bcrypt hash stored in the database

    Returns:
        True if passwords match, False otherwise
    """
    return pwd_context.verify(plain, hashed)

def get_user(username: str) -> dict | None:
    """
    Retrieves user data from Memcached.

    Args:
        username: The username to look up

    Returns:
        User dict if found, None if not found
    """
    user = mc.get(f"user:{username}")  # Memcached key format: "user:alice"
    print(f"{user=}")  # Debug output to see what was retrieved
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    """
    Dependency function that validates JWT tokens and returns the current user.

    This function is used with FastAPI's Depends() to protect routes.
    It automatically extracts and validates the token from the Authorization header.

    Args:
        credentials: Automatically extracted by HTTPBearer from "Authorization: Bearer <token>" header

    Returns:
        User dict if token is valid

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found
    """
    token = credentials.credentials  # Extract the actual token string
    try:
        # Decode and verify the token signature
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Extract username from the "sub" (subject) claim
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        # Look up the user in our data store
        user = get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        # Token was valid but has expired (past the "exp" time)
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        # Token signature is invalid or token is malformed
        raise HTTPException(status_code=401, detail="Invalid token")

# --- Routes ---

@app.post("/token", response_model=Token)
async def login(form: LoginRequest):
    """
    Login endpoint - exchanges username/password for a JWT token.

    Flow:
    1. Look up user by username
    2. Verify password matches the stored hash
    3. Generate and return a JWT token

    Returns:
        Token object with access_token and token_type

    Raises:
        HTTPException: 401 if credentials are incorrect
    """
    user = get_user(form.username)
    # Check if user exists AND password is correct
    # Use .get() with default "" to avoid KeyError if hashed_password is missing
    if not user or not verify_password(form.password, user.get("hashed_password", "")):
        # Don't reveal whether username or password was wrong (security best practice)
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    # Create a JWT token with username as the "sub" (subject) claim
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    """
    A protected route that requires a valid JWT token.

    The 'user' parameter is automatically populated by the get_current_user dependency.
    If the token is invalid or expired, the user never reaches this function.

    Try this in your terminal:
        curl -H "Authorization: Bearer <your_token>" http://localhost:8000/protected
    """
    return {"message": f"Hello, {user['full_name']}! This is a protected endpoint."}

@app.get("/protected2")
async def protected_admin_route(user: dict = Depends(get_current_user)):
    """
    An admin-only route that requires BOTH authentication AND authorization.

    First checks: Is the user authenticated? (get_current_user dependency)
    Then checks: Does the user have admin privileges? (manual check below)

    This demonstrates the difference between:
    - Authentication (401): Who are you? (handled by get_current_user)
    - Authorization (403): Do you have permission? (checked here)
    """
    # Additional authorization check - user must have admin field set to True
    if not user.get("admin"):
        # 403 Forbidden = authenticated but not authorized
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"message": f"Welcome Admin {user['full_name']}! You have access to this route."}

# --- Run standalone ---
if __name__ == "__main__":
    pass

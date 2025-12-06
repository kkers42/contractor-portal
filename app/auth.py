from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
import os

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "default_secret_key")
APP_JWT_SECRET = os.environ.get("APP_JWT_SECRET", SECRET_KEY)  # OAuth secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", 60))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly"""
    # Ensure password is a string and encode to bytes
    password_bytes = str(password).encode('utf-8')
    # Truncate if needed (bcrypt max is 72 bytes)
    password_bytes = password_bytes[:72]
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string
    return hashed.decode('utf-8')

def verify_password(plain_password, hashed_password):
    """Verify a password against a hash using bcrypt directly"""
    try:
        # Convert to bytes
        password_bytes = str(plain_password).encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        # Verify
        result = bcrypt.checkpw(password_bytes, hash_bytes)
        print(f"✅ Password verification result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error verifying password: {e}")
        return False

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Try to decode with legacy password secret first
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        pass  # Try OAuth secret next

    # Try to decode with OAuth secret (APP_JWT_SECRET)
    try:
        payload = jwt.decode(token, APP_JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
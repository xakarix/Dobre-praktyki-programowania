from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import bcrypt

try:
    from . import database
except ImportError:
    import database

SECRET_KEY = "super_secret_key" # W produkcji użyj zmiennej środowiskowej 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()

def hash_password(password: str) -> str:
    # Hashowanie hasła algorytmem bcrypt 
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Weryfikacja hasła 
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # Generowanie tokena JWT 
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(database.get_db)
) -> database.User:
    # Weryfikacja poprawności tokena (podpis, ważność) 
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(status_code=401, detail="Token has expired or is invalid")
    
    user = db.query(database.User).filter(database.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_admin(current_user: database.User = Depends(get_current_user)) -> database.User:
    if "ROLE_ADMIN" not in (current_user.roles or []):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
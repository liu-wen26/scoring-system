from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import hashlib
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


def _hash_password(password: str, salt: str = None) -> str:
    """使用 SHA-256 + salt 哈希密码"""
    if salt is None:
        salt = secrets.token_hex(8)
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"sha256$${salt}$${hashed}"


def _verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    if not hashed or '$$' not in hashed:
        return False
    parts = hashed.split('$$')
    if len(parts) != 3 or parts[0] != 'sha256':
        return False
    salt = parts[1]
    expected = parts[2]
    actual = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return secrets.compare_digest(expected, actual)

# HTTP Bearer 认证
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return _verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return _hash_password(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户（依赖注入）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    if user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    return current_user

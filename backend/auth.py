import re
import httpx
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from models import User, UserPermission, get_db
from config import settings

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        steam_id: str = payload.get("sub")
        if steam_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return steam_id


def get_current_user(steam_id: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.steam_id == steam_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # 检查是否被封禁
    if user.permission and user.permission.is_banned:
        if user.permission.banned_until and user.permission.banned_until > datetime.utcnow():
            raise HTTPException(status_code=403, detail="用户已被封禁")
        elif not user.permission.banned_until:  # 永久封禁
            raise HTTPException(status_code=403, detail="用户已被永久封禁")

    return user


def require_super_admin(current_user: User = Depends(get_current_user)):
    if not current_user.permission or not current_user.permission.is_super_admin:
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user


def can_participate_match(current_user: User = Depends(get_current_user)):
    if not current_user.permission or not current_user.permission.can_participate_match:
        raise HTTPException(status_code=403, detail="用户无权参加匹配")
    if current_user.permission.is_banned:
        raise HTTPException(status_code=403, detail="用户已被封禁，无法参加匹配")
    return current_user


def extract_steam_id(claimed_id: str) -> str:
    """从Steam OpenID claimed_id中提取Steam ID"""
    match = re.search(r'https://steamcommunity\.com/openid/id/(\d+)', claimed_id)
    if match:
        return match.group(1)
    raise ValueError("Invalid Steam OpenID claimed_id")


async def get_steam_user_info(steam_id: str) -> dict:
    """从Steam API获取用户信息"""
    url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
    params = {
        "key": settings.STEAM_API_KEY,
        "steamids": steam_id
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

        if "response" in data and "players" in data["response"] and data["response"]["players"]:
            return data["response"]["players"][0]

    return {}

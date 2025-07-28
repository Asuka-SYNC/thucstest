from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator

from models import User, UserPermission, get_db
from auth import create_access_token, get_current_user, extract_steam_id, get_steam_user_info
from config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic模型
class UserResponse(BaseModel):
    id: int
    steam_id: str
    username: str
    avatar: Optional[str] = None
    profile_url: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    is_first_time_setup: bool = True
    is_profile_public: bool = True
    created_at: datetime
    last_login: datetime

    class Config:
        from_attributes = True


class UserWithPermissionResponse(UserResponse):
    permission: Optional[dict] = None


class FirstTimeSetupRequest(BaseModel):
    display_name: str
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    is_profile_public: bool = True

    @validator('display_name')
    def validate_display_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('显示名称至少需要2个字符')
        if len(v.strip()) > 50:
            raise ValueError('显示名称不能超过50个字符')
        return v.strip()

    @validator('bio')
    def validate_bio(cls, v):
        if v and len(v.strip()) > 500:
            raise ValueError('个人简介不能超过500个字符')
        return v.strip() if v else None

    @validator('location')
    def validate_location(cls, v):
        if v and len(v.strip()) > 100:
            raise ValueError('地理位置不能超过100个字符')
        return v.strip() if v else None

    @validator('website')
    def validate_website(cls, v):
        if v and v.strip():
            url = v.strip()
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            import re
            if not re.match(r'^https?://[^\s/$.?#].[^\s]*$', url):
                raise ValueError('请输入有效的网址')
            return url
        return None


def ensure_user_permission(user: User, db: Session):
    if not user.permission:
        permission = UserPermission(
            user_id=user.id,
            is_super_admin=(db.query(UserPermission).filter(
                UserPermission.is_super_admin == True
            ).count() == 0)
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        user.permission = permission
    return user.permission


def verify_steam_openid(request: Request, form_data: dict) -> Optional[str]:
    """验证Steam OpenID响应"""
    required_params = [
        'openid.assoc_handle', 'openid.signed', 'openid.sig',
        'openid.ns', 'openid.mode', 'openid.op_endpoint',
        'openid.claimed_id', 'openid.identity', 'openid.return_to'
    ]

    for param in required_params:
        if param not in form_data:
            return None

    return form_data['openid.claimed_id']


@router.get("/steam")
async def steam_login():
    """重定向到Steam OpenID登录"""
    steam_openid_url = "https://steamcommunity.com/openid/login"
    return_url = f"{settings.SITE_URL}/auth/steam/return"

    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.mode': 'checkid_setup',
        'openid.return_to': return_url,
        'openid.realm': settings.SITE_URL
    }

    url_params = '&'.join([f"{k}={v}" for k, v in params.items()])
    redirect_url = f"{steam_openid_url}?{url_params}"

    return RedirectResponse(url=redirect_url)


@router.get("/steam/return")
async def steam_return(request: Request, db: Session = Depends(get_db)):
    """处理Steam OpenID返回"""
    form = request.query_params
    form_data = dict(form)

    claimed_id = verify_steam_openid(request, form_data)
    if not claimed_id:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?error=auth_failed")

    try:
        steam_id = extract_steam_id(claimed_id)
        steam_user_info = await get_steam_user_info(steam_id)

        user = db.query(User).filter(User.steam_id == steam_id).first()

        if not user:
            user = User(
                steam_id=steam_id,
                username=steam_user_info.get('personaname', 'Unknown'),
                avatar=steam_user_info.get('avatarfull', ''),
                profile_url=steam_user_info.get('profileurl', ''),
                display_name=steam_user_info.get('personaname', 'Unknown'),
                is_first_time_setup=True,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            db.add(user)
        else:
            user.username = steam_user_info.get('personaname', user.username)
            user.avatar = steam_user_info.get('avatarfull', user.avatar)
            user.profile_url = steam_user_info.get('profileurl', user.profile_url)
            user.last_login = datetime.utcnow()

        db.commit()

        access_token = create_access_token(
            data={"sub": steam_id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        if user.is_first_time_setup:
            redirect_url = f"{settings.FRONTEND_URL}?token={access_token}&first_time=true"
        else:
            redirect_url = f"{settings.FRONTEND_URL}?token={access_token}"

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        print(f"Steam auth error: {e}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?error=auth_failed")


@router.get("/profile", response_model=UserWithPermissionResponse)
async def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户资料"""
    ensure_user_permission(current_user, db)

    # 转换权限数据
    permission_data = None
    if current_user.permission:
        permission_data = {
            "is_super_admin": current_user.permission.is_super_admin,
            "is_banned": current_user.permission.is_banned,
            "can_participate_match": current_user.permission.can_participate_match,
            "banned_until": current_user.permission.banned_until,
            "banned_reason": current_user.permission.banned_reason
        }

    # 修复bug: 先设置为None才能调用from_orm
    current_user.permission = None
    user_data = UserWithPermissionResponse.from_orm(current_user)
    user_data.permission = permission_data

    return user_data


@router.post("/first-time-setup")
async def complete_first_time_setup(
        setup_data: FirstTimeSetupRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """完成首次注册设置"""
    if not current_user.is_first_time_setup:
        raise HTTPException(status_code=400, detail="用户已完成首次设置")

    current_user.display_name = setup_data.display_name
    current_user.bio = setup_data.bio
    current_user.location = setup_data.location
    current_user.website = setup_data.website
    current_user.is_profile_public = setup_data.is_profile_public
    current_user.is_first_time_setup = False

    ensure_user_permission(current_user, db)
    db.commit()

    return {"message": "首次设置完成", "user": current_user}

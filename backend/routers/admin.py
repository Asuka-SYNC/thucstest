from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from models import User, UserPermission, MatchingUser, get_db
from auth import get_current_user
from routers.auth import UserWithPermissionResponse, ensure_user_permission

router = APIRouter(prefix="/admin", tags=["admin"])


class PermissionUpdateRequest(BaseModel):
    is_banned: bool = None
    banned_until: datetime = None
    banned_reason: str = None
    can_participate_match: bool = None


def require_super_admin(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_user_permission(current_user, db)

    if not current_user.permission.is_super_admin:
        raise HTTPException(status_code=403, detail="需要超级管理员权限")

    return current_user


@router.get("/users", response_model=List[UserWithPermissionResponse])
async def get_all_users_admin(
        current_user: User = Depends(require_super_admin),
        db: Session = Depends(get_db)
):
    """获取所有用户（管理员）"""
    users = db.query(User).all()
    result = []

    for user in users:
        ensure_user_permission(user, db)
        permission_data = {
            "is_super_admin": user.permission.is_super_admin,
            "is_banned": user.permission.is_banned,
            "can_participate_match": user.permission.can_participate_match,
            "banned_until": user.permission.banned_until,
            "banned_reason": user.permission.banned_reason
        }

        # 修复bug: 先设置为None才能调用from_orm
        user.permission = None
        user_data = UserWithPermissionResponse.from_orm(user)
        user_data.permission = permission_data
        result.append(user_data)

    return result


@router.get("/users/{user_id}", response_model=UserWithPermissionResponse)
async def get_user_admin(
        user_id: int,
        current_user: User = Depends(require_super_admin),
        db: Session = Depends(get_db)
):
    """获取指定用户详情（管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    ensure_user_permission(user, db)

    permission_data = {
        "is_super_admin": user.permission.is_super_admin,
        "is_banned": user.permission.is_banned,
        "can_participate_match": user.permission.can_participate_match,
        "banned_until": user.permission.banned_until,
        "banned_reason": user.permission.banned_reason
    }

    # 修复bug: 先设置为None才能调用from_orm
    user.permission = None
    user_data = UserWithPermissionResponse.from_orm(user)
    user_data.permission = permission_data

    return user_data


@router.put("/users/{user_id}/permissions")
async def update_user_permissions(
        user_id: int,
        permission_update: PermissionUpdateRequest,
        current_user: User = Depends(require_super_admin),
        db: Session = Depends(get_db)
):
    """更新用户权限（管理员）"""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能修改自己的权限")

    ensure_user_permission(target_user, db)

    if permission_update.is_banned is not None:
        target_user.permission.is_banned = permission_update.is_banned
        target_user.permission.banned_until = permission_update.banned_until
        target_user.permission.banned_reason = permission_update.banned_reason

        if not permission_update.is_banned:
            db.query(MatchingUser).filter(MatchingUser.user_id == user_id).delete()

    if permission_update.can_participate_match is not None:
        target_user.permission.can_participate_match = permission_update.can_participate_match

        if not permission_update.can_participate_match:
            db.query(MatchingUser).filter(MatchingUser.user_id == user_id).delete()

    target_user.permission.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "权限更新成功", "user": target_user}

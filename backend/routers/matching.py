import json
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, update
from pydantic import BaseModel

from models import User, MatchingUser, MatchSession, get_db
from auth import get_current_user
from routers.auth import ensure_user_permission

router = APIRouter(prefix="/matching", tags=["matching"])


class MatchingUserResponse(BaseModel):
    user_id: int
    display_name: str
    avatar: str
    status: str
    joined_at: datetime


class MatchConfirmRequest(BaseModel):
    session_id: str
    accept: bool


def can_participate_match(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_user_permission(current_user, db)

    if current_user.permission.is_banned:
        raise HTTPException(status_code=403, detail="用户已被封禁")

    if not current_user.permission.can_participate_match:
        raise HTTPException(status_code=403, detail="用户没有参与匹配的权限")

    return current_user


async def get_matching_users_list(db: Session) -> List[MatchingUserResponse]:
    matching_users = db.query(MatchingUser).join(User).filter(
        MatchingUser.status == "waiting"
    ).all()

    return [
        MatchingUserResponse(
            user_id=mu.user_id,
            display_name=mu.user.display_name or mu.user.username,
            avatar=mu.user.avatar or '',
            status=mu.status,
            joined_at=mu.joined_at
        )
        for mu in matching_users
    ]


@router.post("/join")
async def join_matching(
        current_user: User = Depends(can_participate_match),
        db: Session = Depends(get_db)
):
    """加入匹配队列"""
    existing_match = db.query(MatchingUser).filter(
        MatchingUser.user_id == current_user.id
    ).first()

    if existing_match:
        raise HTTPException(status_code=400, detail="您已在匹配队列中")

    matching_user = MatchingUser(
        user_id=current_user.id,
        status="waiting",
        joined_at=datetime.utcnow(),
        last_heartbeat=datetime.utcnow()
    )
    db.add(matching_user)
    db.commit()

    return {"message": "已加入匹配队列", "status": "waiting"}


@router.post("/leave")
async def leave_matching(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """离开匹配队列"""
    matching_user = db.query(MatchingUser).filter(
        MatchingUser.user_id == current_user.id
    ).first()

    if not matching_user:
        raise HTTPException(status_code=400, detail="您不在匹配队列中")

    db.delete(matching_user)
    db.commit()

    return {"message": "已离开匹配队列"}


@router.get("/status")
async def get_matching_status(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取当前用户匹配状态"""
    matching_user = db.query(MatchingUser).filter(
        MatchingUser.user_id == current_user.id
    ).first()

    return {
        "in_queue": matching_user is not None,
        "joined_at": matching_user.joined_at if matching_user else None,
        "status": matching_user.status if matching_user else None,
        "session_id": matching_user.match_session_id if matching_user else None
    }


@router.get("/queue", response_model=List[MatchingUserResponse])
async def get_matching_queue(db: Session = Depends(get_db)):
    """获取匹配队列"""
    return await get_matching_users_list(db)


@router.post("/confirm")
async def confirm_match(
        confirm_data: MatchConfirmRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """确认匹配 - 使用原子操作避免并发问题"""
    # 首先验证用户是否有有效的匹配确认
    matching_user = db.query(MatchingUser).filter(
        and_(
            MatchingUser.user_id == current_user.id,
            MatchingUser.match_session_id == confirm_data.session_id,
            MatchingUser.status == "confirming"
        )
    ).first()

    if not matching_user:
        raise HTTPException(status_code=400, detail="无效的匹配确认")

    # 验证匹配会话是否存在且状态正确
    match_session = db.query(MatchSession).filter(
        MatchSession.session_id == confirm_data.session_id
    ).first()

    if not match_session or match_session.status != "confirming":
        raise HTTPException(status_code=400, detail="匹配会话已失效")

    if confirm_data.accept:
        # 接受匹配 - 使用原子操作更新确认计数
        try:
            # 原子性地增加确认计数并获取更新后的值
            result = db.execute(
                update(MatchSession)
                .where(and_(
                    MatchSession.session_id == confirm_data.session_id,
                    MatchSession.status == "confirming"
                ))
                .values(confirmed_count=MatchSession.confirmed_count + 1)
                .returning(MatchSession.confirmed_count, MatchSession.required_confirmations)
            )
            
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=400, detail="匹配会话状态已改变")
            
            new_confirmed_count, required_confirmations = row
            
            # 更新用户状态
            matching_user.status = "confirmed"
            
            # 检查是否所有人都确认了
            if new_confirmed_count >= required_confirmations:
                from models import GameSession
                import uuid

                # 创建游戏会话
                game_session_id = str(uuid.uuid4())
                game_session = GameSession(
                    session_id=game_session_id,
                    player_ids=match_session.player_ids,
                    status="preparing"
                )
                db.add(game_session)

                # 更新匹配会话状态
                match_session.status = "ready"
                match_session.started_at = datetime.utcnow()

                # 移除匹配用户
                db.query(MatchingUser).filter(
                    MatchingUser.match_session_id == confirm_data.session_id
                ).delete()

                db.commit()

                return {"message": "匹配成功，正在进入游戏", "game_session_id": game_session_id}
            else:
                db.commit()
                return {"message": "确认成功，等待其他玩家", "confirmed": new_confirmed_count}
                
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="确认匹配时发生错误")
    else:
        # 拒绝匹配 - 使用悲观锁确保一致性
        try:
            # 使用悲观锁锁定匹配会话
            match_session_locked = db.query(MatchSession).filter(
                MatchSession.session_id == confirm_data.session_id
            ).with_for_update().first()
            
            if not match_session_locked or match_session_locked.status != "confirming":
                raise HTTPException(status_code=400, detail="匹配会话已失效")

            # 删除当前用户的匹配记录
            db.delete(matching_user)

            # 取消匹配会话
            match_session_locked.status = "cancelled"
            match_session_locked.cancelled_at = datetime.utcnow()

            # 将其他已确认的用户重新放回等待队列
            other_users = db.query(MatchingUser).filter(
                MatchingUser.match_session_id == confirm_data.session_id
            ).all()

            for user in other_users:
                user.status = "waiting"
                user.match_session_id = None
                user.confirm_timeout = None

            db.commit()
            return {"message": "已拒绝匹配"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="拒绝匹配时发生错误")

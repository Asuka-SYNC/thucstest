import asyncio
import uuid
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import SessionLocal, MatchingUser, MatchSession, GameSession
from utils.websocket import manager
from routers.matching import get_matching_users_list


async def heartbeat_checker():
    """心跳检查任务"""
    while True:
        await asyncio.sleep(5)  # 每5秒检查一次

        db = SessionLocal()
        try:
            current_time = datetime.utcnow()

            # 检查心跳超时的用户
            for user_id, last_heartbeat in manager.user_heartbeats.items():
                print(current_time)
                print(last_heartbeat)
                if current_time - last_heartbeat > timedelta(seconds=5):
                    # 更新心跳失败次数
                    matching_user = db.query(MatchingUser).filter(
                        MatchingUser.user_id == user_id
                    ).first()

                    if matching_user:
                        matching_user.heartbeat_failures += 1

                        if matching_user.heartbeat_failures >= 5:
                            # 移出匹配队列
                            db.delete(matching_user)
                            db.commit()

                            # 断开WebSocket连接
                            manager.disconnect(user_id)

                            # 广播更新
                            matching_users = await get_matching_users_list(db)
                            await manager.broadcast_matching_update([user.dict() for user in matching_users])
                        else:
                            db.commit()
        finally:
            db.close()


async def match_checker():
    """匹配检查任务"""
    while True:
        await asyncio.sleep(5)  # 每5秒检查一次

        db = SessionLocal()
        try:
            # 获取等待中的用户
            waiting_users = db.query(MatchingUser).filter(
                MatchingUser.status == "waiting"
            ).all()

            if len(waiting_users) >= 10:
                # 随机选择10人进行匹配
                selected_users = random.sample(waiting_users, 10)

                # 创建匹配会话
                session_id = str(uuid.uuid4())
                match_session = MatchSession(
                    session_id=session_id,
                    player_ids=[u.user_id for u in selected_users]
                )
                db.add(match_session)

                # 更新用户状态
                for user in selected_users:
                    user.status = "confirming"
                    user.match_session_id = session_id
                    user.confirm_timeout = datetime.utcnow() + timedelta(seconds=30)

                db.commit()

                # 发送匹配确认消息
                user_ids = [u.user_id for u in selected_users]
                await manager.send_match_found(user_ids, session_id)

                # 广播匹配列表更新
                matching_users = await get_matching_users_list(db)
                await manager.broadcast_matching_update([user.dict() for user in matching_users])

        finally:
            db.close()


async def confirm_timeout_checker():
    """确认超时检查任务"""
    while True:
        await asyncio.sleep(1)  # 每1秒检查一次

        db = SessionLocal()
        try:
            current_time = datetime.utcnow()

            # 检查确认超时的用户
            timeout_users = db.query(MatchingUser).filter(
                and_(
                    MatchingUser.status == "confirming",
                    MatchingUser.confirm_timeout <= current_time
                )
            ).all()

            if timeout_users:
                # 获取所有超时的会话
                session_ids = list(set([u.match_session_id for u in timeout_users]))

                for session_id in session_ids:
                    # 取消匹配会话
                    match_session = db.query(MatchSession).filter(
                        MatchSession.session_id == session_id
                    ).first()

                    if match_session:
                        match_session.status = "cancelled"
                        match_session.cancelled_at = current_time

                    # 处理该会话的所有用户
                    session_users = db.query(MatchingUser).filter(
                        MatchingUser.match_session_id == session_id
                    ).all()

                    for user in session_users:
                        if user.status == "confirming":
                            # 超时用户移出匹配队列
                            db.delete(user)
                        elif user.status == "confirmed":
                            # 已确认用户重新回到等待状态
                            user.status = "waiting"
                            user.match_session_id = None
                            user.confirm_timeout = None

                db.commit()

                # 广播匹配列表更新
                matching_users = await get_matching_users_list(db)
                await manager.broadcast_matching_update([user.dict() for user in matching_users])

        finally:
            db.close()

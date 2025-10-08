import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from models import User, MatchingUser, get_db
from auth import get_current_user
from config import settings
from utils.websocket import manager
from utils.tasks import heartbeat_checker, match_checker, confirm_timeout_checker

# 导入路由
from routers import auth, matching, admin, game, events_callback, matchzy

app = FastAPI(title="Steam Login API")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(matching.router)
app.include_router(admin.router)
app.include_router(game.router)
app.include_router(matchzy.router)
app.include_router(events_callback.router)

# Serve frontend static files
app.mount("/", StaticFiles(directory="./frontend_dist", html=True), name="static")


# SPA fallback: serve index.html for unknown routes
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    index_path = os.path.join(os.path.dirname(__file__), "./frontend_dist/index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html not found"}


# 启动后台任务
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(heartbeat_checker())
    asyncio.create_task(match_checker())
    asyncio.create_task(confirm_timeout_checker())


@app.get("/")
async def root():
    return {"message": "Steam Login API v2.0"}


@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    """获取所有用户列表（只显示已完成设置且公开的用户）"""
    users = db.query(User).filter(
        User.is_first_time_setup == False,
        User.is_profile_public == True
    ).order_by(User.last_login.desc()).all()

    from routers.auth import UserResponse
    return [UserResponse.from_orm(user) for user in users]


# WebSocket连接
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "heartbeat":
                    # 更新心跳时间
                    manager.update_heartbeat(user_id)

                    # 更新数据库中的心跳时间
                    matching_user = db.query(MatchingUser).filter(
                        MatchingUser.user_id == user_id
                    ).first()

                    if matching_user:
                        from datetime import datetime
                        matching_user.last_heartbeat = datetime.utcnow()
                        matching_user.heartbeat_failures = 0  # 重置失败次数
                        db.commit()

                    await websocket.send_text(json.dumps({"type": "heartbeat", "status": "ok"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(user_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

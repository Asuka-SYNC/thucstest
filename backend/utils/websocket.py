import json
from datetime import datetime
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.user_heartbeats: Dict[int, datetime] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_heartbeats[user_id] = datetime.utcnow()

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_heartbeats:
            del self.user_heartbeats[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except:
                self.disconnect(user_id)

    async def broadcast_matching_update(self, data: List[dict]):
        message = {"type": "matching_update", "data": data}
        disconnected_users = []

        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected_users.append(user_id)

        # 清理断开的连接
        for user_id in disconnected_users:
            self.disconnect(user_id)

    async def send_match_found(self, user_ids: List[int], session_id: str):
        message = {
            "type": "match_found",
            "data": {
                "session_id": session_id,
                "timeout": 30
            }
        }

        for user_id in user_ids:
            await self.send_personal_message(message, user_id)

    async def send_game_ready(self, user_ids: List[int], game_session_id: str):
        message = {
            "type": "game_ready",
            "data": {
                "game_session_id": game_session_id
            }
        }

        for user_id in user_ids:
            await self.send_personal_message(message, user_id)

    def update_heartbeat(self, user_id: int):
        from datetime import datetime
        self.user_heartbeats[user_id] = datetime.utcnow()


# 全局实例
manager = ConnectionManager()

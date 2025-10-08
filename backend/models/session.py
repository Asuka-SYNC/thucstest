from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from .database import Base


class MatchSession(Base):
    __tablename__ = "match_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False)
    status = Column(String, default="confirming")  # confirming, ready, started, cancelled
    required_confirmations = Column(Integer, default=10)
    confirmed_count = Column(Integer, default=0)
    player_ids = Column(JSON)  # 参与玩家ID列表
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    cancelled_at = Column(DateTime)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False)
    player_ids = Column(JSON)  # 参与玩家ID列表
    status = Column(String, default="preparing")  # preparing, in_progress, finished
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    game_data = Column(JSON)  # 游戏相关数据

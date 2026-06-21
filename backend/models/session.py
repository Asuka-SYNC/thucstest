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
    player_ids = Column(JSON)
    status = Column(String, default="voting")  # voting, provisioning, ready, in_progress, finished
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    game_data = Column(JSON)

    vote_deadline = Column(DateTime)
    selected_server = Column(String)
    server_ref = Column(String)
    server_public_ip = Column(String)
    server_connect_url = Column(String)
    match_id = Column(String)


class ServerVote(Base):
    __tablename__ = "server_votes"

    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(String, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    server_key = Column(String, nullable=False)
    voted_at = Column(DateTime, default=datetime.utcnow)

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import settings

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    steam_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    avatar = Column(String)
    profile_url = Column(String)

    # 用户信息字段
    display_name = Column(String)
    bio = Column(Text)
    location = Column(String)
    website = Column(String)
    is_first_time_setup = Column(Boolean, default=True)
    is_profile_public = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

    # 关系
    permission = relationship("UserPermission", back_populates="user", uselist=False)
    matching_user = relationship("MatchingUser", back_populates="user", uselist=False)


class UserPermission(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    is_super_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    banned_until = Column(DateTime)
    banned_reason = Column(Text)
    can_participate_match = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="permission")


class MatchingUser(Base):
    __tablename__ = "matching_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    status = Column(String, default="waiting")  # waiting, confirming, confirmed, timeout
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    heartbeat_failures = Column(Integer, default=0)
    match_session_id = Column(String)  # 匹配确认会话ID
    confirm_timeout = Column(DateTime)  # 确认超时时间

    # 关系
    user = relationship("User", back_populates="matching_user")


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


# Database setup
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

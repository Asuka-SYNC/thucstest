from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from .database import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String, unique=True, index=True, nullable=False)

    # Status can be: picking, veto, ready, live, finished, cancelled
    status = Column(String, default="picking", nullable=False)

    # --- Players and Teams ---
    player_ids = Column(JSON, nullable=False)  # List of all 10 player IDs
    captain_a_id = Column(Integer)
    captain_b_id = Column(Integer)
    team_a_ids = Column(JSON)  # List of player IDs in Team A
    team_b_ids = Column(JSON)  # List of player IDs in Team B

    # --- Veto Process ---
    map_pool = Column(JSON)
    banned_maps = Column(JSON)
    selected_map = Column(String)
    
    # --- Server and Game Info ---
    server_ip = Column(String)
    connect_password = Column(String)
    team_a_score = Column(Integer, default=0)
    team_b_score = Column(Integer, default=0)
    winner_team = Column(String)  # 'A' or 'B'

    # --- Timestamps ---
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


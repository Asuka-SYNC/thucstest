from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class MatchzyStatsMatches(Base):
    __tablename__ = 'matchzy_stats_matches'

    matchid = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    winner = Column(String(255), nullable=False, default='')
    series_type = Column(String(255), nullable=False, default='')
    team1_name = Column(String(255), nullable=False, default='')
    team1_score = Column(Integer, nullable=False, default=0)
    team2_name = Column(String(255), nullable=False, default='')
    team2_score = Column(Integer, nullable=False, default=0)
    server_ip = Column(String(255), nullable=False, default='0')

    # Relationships
    maps = relationship("MatchzyStatsMaps", back_populates="match", cascade="all, delete-orphan")
    players = relationship("MatchzyStatsPlayers", back_populates="match", cascade="all, delete-orphan")


class MatchzyStatsMaps(Base):
    __tablename__ = 'matchzy_stats_maps'

    matchid = Column(Integer, ForeignKey('matchzy_stats_matches.matchid'), primary_key=True)
    mapnumber = Column(Integer, primary_key=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    winner = Column(String(16), nullable=False, default='')
    mapname = Column(String(64), nullable=False, default='')
    team1_score = Column(Integer, nullable=False, default=0)
    team2_score = Column(Integer, nullable=False, default=0)

    # Relationships
    match = relationship("MatchzyStatsMatches", back_populates="maps")
    players = relationship("MatchzyStatsPlayers", back_populates="map", cascade="all, delete-orphan", overlaps="players")


class MatchzyStatsPlayers(Base):
    __tablename__ = 'matchzy_stats_players'

    matchid = Column(Integer, primary_key=True)
    mapnumber = Column(Integer, primary_key=True)
    steamid64 = Column(BigInteger, primary_key=True)
    team = Column(String(255), nullable=False, default='')
    name = Column(String(255), nullable=False)
    kills = Column(Integer, nullable=False, default=0)
    deaths = Column(Integer, nullable=False, default=0)
    damage = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)
    enemy5ks = Column(Integer, nullable=False, default=0)
    enemy4ks = Column(Integer, nullable=False, default=0)
    enemy3ks = Column(Integer, nullable=False, default=0)
    enemy2ks = Column(Integer, nullable=False, default=0)
    utility_count = Column(Integer, nullable=False, default=0)
    utility_damage = Column(Integer, nullable=False, default=0)
    utility_successes = Column(Integer, nullable=False, default=0)
    utility_enemies = Column(Integer, nullable=False, default=0)
    flash_count = Column(Integer, nullable=False, default=0)
    flash_successes = Column(Integer, nullable=False, default=0)
    health_points_removed_total = Column(Integer, nullable=False, default=0)
    health_points_dealt_total = Column(Integer, nullable=False, default=0)
    shots_fired_total = Column(Integer, nullable=False, default=0)
    shots_on_target_total = Column(Integer, nullable=False, default=0)
    v1_count = Column(Integer, nullable=False, default=0)
    v1_wins = Column(Integer, nullable=False, default=0)
    v2_count = Column(Integer, nullable=False, default=0)
    v2_wins = Column(Integer, nullable=False, default=0)
    entry_count = Column(Integer, nullable=False, default=0)
    entry_wins = Column(Integer, nullable=False, default=0)
    equipment_value = Column(Integer, nullable=False, default=0)
    money_saved = Column(Integer, nullable=False, default=0)
    kill_reward = Column(Integer, nullable=False, default=0)
    live_time = Column(Integer, nullable=False, default=0)
    head_shot_kills = Column(Integer, nullable=False, default=0)
    cash_earned = Column(Integer, nullable=False, default=0)
    enemies_flashed = Column(Integer, nullable=False, default=0)

    # Relationships
    match = relationship("MatchzyStatsMatches", back_populates="players",
                        primaryjoin="MatchzyStatsPlayers.matchid == MatchzyStatsMatches.matchid", overlaps="players")
    map = relationship("MatchzyStatsMaps", back_populates="players",
                       foreign_keys=[matchid, mapnumber], overlaps="match,players")

    # Foreign key constraints
    __table_args__ = (
        ForeignKeyConstraint(['matchid'], ['matchzy_stats_matches.matchid']),
        ForeignKeyConstraint(['matchid', 'mapnumber'],
                            ['matchzy_stats_maps.matchid', 'matchzy_stats_maps.mapnumber']),
    )

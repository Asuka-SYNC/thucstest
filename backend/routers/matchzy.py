from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, desc, case
from sqlalchemy.orm import Session

import models
from models import get_db

router = APIRouter(prefix="/matchzy", tags=["matchzy"])


class MatchBase(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    winner: str = ''
    series_type: str = ''
    team1_name: str = ''
    team1_score: int = 0
    team2_name: str = ''
    team2_score: int = 0
    server_ip: str = '0'


class MatchCreate(MatchBase):
    pass


class Match(MatchBase):
    matchid: int

    class Config:
        from_attributes = True


class MapBase(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    winner: str = ''
    mapname: str = ''
    team1_score: int = 0
    team2_score: int = 0


class MapCreate(MapBase):
    matchid: int
    mapnumber: int


class Map(MapBase):
    matchid: int
    mapnumber: int

    class Config:
        from_attributes = True


class PlayerBase(BaseModel):
    steamid64: int
    team: str = ''
    name: str
    kills: int = 0
    deaths: int = 0
    damage: int = 0
    assists: int = 0
    enemy5ks: int = 0
    enemy4ks: int = 0
    enemy3ks: int = 0
    enemy2ks: int = 0
    utility_count: int = 0
    utility_damage: int = 0
    utility_successes: int = 0
    utility_enemies: int = 0
    flash_count: int = 0
    flash_successes: int = 0
    health_points_removed_total: int = 0
    health_points_dealt_total: int = 0
    shots_fired_total: int = 0
    shots_on_target_total: int = 0
    v1_count: int = 0
    v1_wins: int = 0
    v2_count: int = 0
    v2_wins: int = 0
    entry_count: int = 0
    entry_wins: int = 0
    equipment_value: int = 0
    money_saved: int = 0
    kill_reward: int = 0
    live_time: int = 0
    head_shot_kills: int = 0
    cash_earned: int = 0
    enemies_flashed: int = 0


class PlayerCreate(PlayerBase):
    matchid: int
    mapnumber: int


class Player(PlayerBase):
    matchid: int
    mapnumber: int

    class Config:
        from_attributes = True


# 聚合数据模型
class PlayerAverageStats(BaseModel):
    steamid64: int
    name: str
    matches_played: int
    maps_played: int
    avg_kills: float
    avg_deaths: float
    avg_damage: float
    avg_assists: float
    kd_ratio: float
    adr: float  # Average Damage per Round
    headshot_percentage: float
    total_5ks: int
    total_4ks: int
    total_3ks: int
    win_rate: float


class TeamStats(BaseModel):
    team_name: str
    matches_played: int
    wins: int
    losses: int
    win_rate: float
    total_rounds_played: int
    rounds_won: int
    rounds_lost: int
    round_win_rate: float


class MatchDetail(BaseModel):
    match: Match
    maps: List[Map]
    players: List[Player]


# 基础CRUD接口

@router.get("/matches/", response_model=List[Match])
def get_matches(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """获取比赛列表"""
    matches = db.query(models.MatchzyStatsMatches).offset(skip).limit(limit).all()
    return matches


@router.get("/matches/{match_id}", response_model=MatchDetail)
def get_match_detail(match_id: int, db: Session = Depends(get_db)):
    """获取比赛详细信息，包括地图和玩家数据"""
    match = db.query(models.MatchzyStatsMatches).filter(
        models.MatchzyStatsMatches.matchid == match_id
    ).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    maps = db.query(models.MatchzyStatsMaps).filter(
        models.MatchzyStatsMaps.matchid == match_id
    ).all()

    players = db.query(models.MatchzyStatsPlayers).filter(
        models.MatchzyStatsPlayers.matchid == match_id
    ).all()

    return MatchDetail(match=match, maps=maps, players=players)


@router.get("/maps/{match_id}/{map_number}", response_model=List[Player])
def get_map_players(
        match_id: int,
        map_number: int,
        db: Session = Depends(get_db)
):
    """获取特定地图的玩家统计"""
    players = db.query(models.MatchzyStatsPlayers).filter(
        models.MatchzyStatsPlayers.matchid == match_id,
        models.MatchzyStatsPlayers.mapnumber == map_number
    ).all()

    if not players:
        raise HTTPException(status_code=404, detail="Map data not found")

    return players


# 玩家统计接口

@router.get("/players/{steamid64}/stats", response_model=PlayerAverageStats)
def get_player_average_stats(steamid64: int, db: Session = Depends(get_db)):
    """获取玩家场均数据"""

    # 基础统计查询
    stats_query = db.query(
        models.MatchzyStatsPlayers.steamid64,
        models.MatchzyStatsPlayers.name,
        func.count(func.distinct(models.MatchzyStatsPlayers.matchid)).label('matches_played'),
        func.count().label('maps_played'),
        func.avg(models.MatchzyStatsPlayers.kills.cast(float)).label('avg_kills'),
        func.avg(models.MatchzyStatsPlayers.deaths.cast(float)).label('avg_deaths'),
        func.avg(models.MatchzyStatsPlayers.damage.cast(float)).label('avg_damage'),
        func.avg(models.MatchzyStatsPlayers.assists.cast(float)).label('avg_assists'),
        func.sum(models.MatchzyStatsPlayers.enemy5ks).label('total_5ks'),
        func.sum(models.MatchzyStatsPlayers.enemy4ks).label('total_4ks'),
        func.sum(models.MatchzyStatsPlayers.enemy3ks).label('total_3ks'),
        func.sum(models.MatchzyStatsPlayers.kills).label('total_kills'),
        func.sum(models.MatchzyStatsPlayers.deaths).label('total_deaths'),
        func.sum(models.MatchzyStatsPlayers.head_shot_kills).label('total_headshots'),
    ).filter(
        models.MatchzyStatsPlayers.steamid64 == steamid64
    ).group_by(
        models.MatchzyStatsPlayers.steamid64,
        models.MatchzyStatsPlayers.name
    ).first()

    if not stats_query:
        raise HTTPException(status_code=404, detail="Player not found")

    # 计算胜率
    wins_query = db.query(
        func.count(func.distinct(models.MatchzyStatsPlayers.matchid)).label('wins')
    ).join(models.MatchzyStatsMaps).join(models.MatchzyStatsMatches).filter(
        models.MatchzyStatsPlayers.steamid64 == steamid64,
        models.MatchzyStatsMaps.winner == models.MatchzyStatsPlayers.team
    ).scalar()

    wins = wins_query or 0
    kd_ratio = stats_query.total_kills / max(stats_query.total_deaths, 1)
    headshot_percentage = (stats_query.total_headshots / max(stats_query.total_kills, 1)) * 100
    win_rate = (wins / max(stats_query.matches_played, 1)) * 100

    return PlayerAverageStats(
        steamid64=stats_query.steamid64,
        name=stats_query.name,
        matches_played=stats_query.matches_played,
        maps_played=stats_query.maps_played,
        avg_kills=round(stats_query.avg_kills, 2),
        avg_deaths=round(stats_query.avg_deaths, 2),
        avg_damage=round(stats_query.avg_damage, 2),
        avg_assists=round(stats_query.avg_assists, 2),
        kd_ratio=round(kd_ratio, 2),
        adr=round(stats_query.avg_damage, 2),  # ADR通常等于平均伤害
        headshot_percentage=round(headshot_percentage, 2),
        total_5ks=stats_query.total_5ks,
        total_4ks=stats_query.total_4ks,
        total_3ks=stats_query.total_3ks,
        win_rate=round(win_rate, 2)
    )


@router.get("/players/leaderboard", response_model=List[PlayerAverageStats])
def get_players_leaderboard(
        order_by: str = Query("avg_kills", description="排序字段"),
        limit: int = Query(50, description="返回数量"),
        min_matches: int = Query(3, description="最少比赛场数"),
        db: Session = Depends(get_db)
):
    """获取玩家排行榜"""

    # 子查询获取每个玩家的统计数据
    subquery = db.query(
        models.MatchzyStatsPlayers.steamid64,
        func.max(models.MatchzyStatsPlayers.name).label('name'),
        func.count(func.distinct(models.MatchzyStatsPlayers.matchid)).label('matches_played'),
        func.count().label('maps_played'),
        func.avg(models.MatchzyStatsPlayers.kills.cast(float)).label('avg_kills'),
        func.avg(models.MatchzyStatsPlayers.deaths.cast(float)).label('avg_deaths'),
        func.avg(models.MatchzyStatsPlayers.damage.cast(float)).label('avg_damage'),
        func.avg(models.MatchzyStatsPlayers.assists.cast(float)).label('avg_assists'),
        func.sum(models.MatchzyStatsPlayers.enemy5ks).label('total_5ks'),
        func.sum(models.MatchzyStatsPlayers.enemy4ks).label('total_4ks'),
        func.sum(models.MatchzyStatsPlayers.enemy3ks).label('total_3ks'),
        func.sum(models.MatchzyStatsPlayers.kills).label('total_kills'),
        func.sum(models.MatchzyStatsPlayers.deaths).label('total_deaths'),
        func.sum(models.MatchzyStatsPlayers.head_shot_kills).label('total_headshots'),
    ).group_by(
        models.MatchzyStatsPlayers.steamid64
    ).having(
        func.count(func.distinct(models.MatchzyStatsPlayers.matchid)) >= min_matches
    ).subquery()

    # 主查询添加计算字段
    query = db.query(
        subquery.c.steamid64,
        subquery.c.name,
        subquery.c.matches_played,
        subquery.c.maps_played,
        subquery.c.avg_kills,
        subquery.c.avg_deaths,
        subquery.c.avg_damage,
        subquery.c.avg_assists,
        subquery.c.total_5ks,
        subquery.c.total_4ks,
        subquery.c.total_3ks,
        (subquery.c.total_kills.cast(float) /
         func.greatest(subquery.c.total_deaths, 1)).label('kd_ratio'),
        (subquery.c.total_headshots.cast(float) /
         func.greatest(subquery.c.total_kills, 1) * 100).label('headshot_percentage')
    )

    # 排序
    order_column = getattr(subquery.c, order_by, subquery.c.avg_kills)
    query = query.order_by(desc(order_column))

    results = query.limit(limit).all()

    leaderboard = []
    for result in results:
        leaderboard.append(PlayerAverageStats(
            steamid64=result.steamid64,
            name=result.name,
            matches_played=result.matches_played,
            maps_played=result.maps_played,
            avg_kills=round(result.avg_kills, 2),
            avg_deaths=round(result.avg_deaths, 2),
            avg_damage=round(result.avg_damage, 2),
            avg_assists=round(result.avg_assists, 2),
            kd_ratio=round(result.kd_ratio, 2),
            adr=round(result.avg_damage, 2),
            headshot_percentage=round(result.headshot_percentage, 2),
            total_5ks=result.total_5ks,
            total_4ks=result.total_4ks,
            total_3ks=result.total_3ks,
            win_rate=0.0  # 需要单独查询胜率
        ))

    return leaderboard


@router.get("/teams/stats", response_model=List[TeamStats])
def get_team_stats(db: Session = Depends(get_db)):
    """获取队伍统计数据"""

    # 查询所有队伍的比赛数据
    team_matches = db.query(
        case(
            [(models.MatchzyStatsMatches.team1_name != '', models.MatchzyStatsMatches.team1_name)],
            else_=models.MatchzyStatsMatches.team2_name
        ).label('team_name'),
        func.count().label('matches_played'),
        func.sum(
            case([(models.MatchzyStatsMatches.winner == models.MatchzyStatsMatches.team1_name, 1)], else_=0) +
            case([(models.MatchzyStatsMatches.winner == models.MatchzyStatsMatches.team2_name, 1)], else_=0)
        ).label('wins')
    ).group_by('team_name').all()

    team_stats = []
    for team in team_matches:
        losses = team.matches_played - team.wins
        win_rate = (team.wins / max(team.matches_played, 1)) * 100

        # 查询回合数据
        rounds_data = db.query(
            func.sum(models.MatchzyStatsMaps.team1_score + models.MatchzyStatsMaps.team2_score).label('total_rounds'),
            func.sum(
                case([
                    (models.MatchzyStatsMaps.winner == team.team_name,
                     case([(models.MatchzyStatsMaps.winner == models.MatchzyStatsMatches.team1_name,
                            models.MatchzyStatsMaps.team1_score)],
                          else_=models.MatchzyStatsMaps.team2_score))
                ], else_=0)
            ).label('rounds_won')
        ).join(models.MatchzyStatsMatches).filter(
            (models.MatchzyStatsMatches.team1_name == team.team_name) |
            (models.MatchzyStatsMatches.team2_name == team.team_name)
        ).first()

        total_rounds = rounds_data.total_rounds or 0
        rounds_won = rounds_data.rounds_won or 0
        rounds_lost = total_rounds - rounds_won
        round_win_rate = (rounds_won / max(total_rounds, 1)) * 100

        team_stats.append(TeamStats(
            team_name=team.team_name,
            matches_played=team.matches_played,
            wins=team.wins,
            losses=losses,
            win_rate=round(win_rate, 2),
            total_rounds_played=total_rounds,
            rounds_won=rounds_won,
            rounds_lost=rounds_lost,
            round_win_rate=round(round_win_rate, 2)
        ))

    return team_stats


@router.get("/matches/recent", response_model=List[Match])
def get_recent_matches(
        limit: int = Query(10, description="返回数量"),
        db: Session = Depends(get_db)
):
    """获取最近的比赛"""
    matches = db.query(models.MatchzyStatsMatches).order_by(
        desc(models.MatchzyStatsMatches.start_time)
    ).limit(limit).all()

    return matches

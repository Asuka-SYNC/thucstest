from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from models import User, GameSession, ServerVote, get_db
from auth import get_current_user
from config import settings

router = APIRouter(prefix="/game", tags=["game"])


class VoteRequest(BaseModel):
    server_key: str


def _available_servers() -> list[str]:
    return list(settings.SERVER_HOSTS.keys())


@router.get("/{session_id}")
async def get_game_session(
        session_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取游戏会话信息"""
    game_session = db.query(GameSession).filter(
        GameSession.session_id == session_id
    ).first()

    if not game_session:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if current_user.id not in game_session.player_ids:
        raise HTTPException(status_code=403, detail="您不在此游戏中")

    players = db.query(User).filter(User.id.in_(game_session.player_ids)).all()
    player_data = [
        {
            "id": player.id,
            "display_name": player.display_name or player.username,
            "avatar": player.avatar,
            "steam_id": player.steam_id
        }
        for player in players
    ]

    return {
        "session_id": game_session.session_id,
        "status": game_session.status,
        "players": player_data,
        "created_at": game_session.created_at,
        "started_at": game_session.started_at,
        "vote_deadline": game_session.vote_deadline,
        "selected_server": game_session.selected_server,
        "connect_url": game_session.server_connect_url,
    }


@router.post("/{session_id}/vote")
async def cast_vote(
        session_id: str,
        vote_data: VoteRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    game_session = db.query(GameSession).filter(
        GameSession.session_id == session_id
    ).first()

    if not game_session:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if game_session.status != "voting":
        raise HTTPException(status_code=400, detail="当前阶段无法投票")

    if current_user.id not in game_session.player_ids:
        raise HTTPException(status_code=403, detail="您不在此游戏中")

    servers = _available_servers()
    if vote_data.server_key not in servers:
        raise HTTPException(status_code=400, detail=f"无效的服务器，可选: {servers}")

    if datetime.utcnow() > game_session.vote_deadline:
        raise HTTPException(status_code=400, detail="投票已结束")

    existing = db.query(ServerVote).filter(
        ServerVote.game_session_id == session_id,
        ServerVote.user_id == current_user.id,
    ).first()

    if existing:
        existing.server_key = vote_data.server_key
        existing.voted_at = datetime.utcnow()
    else:
        db.add(ServerVote(
            game_session_id=session_id,
            user_id=current_user.id,
            server_key=vote_data.server_key,
        ))

    db.commit()
    return {"message": "投票成功", "server_key": vote_data.server_key}


@router.get("/{session_id}/votes")
async def get_vote_tally(
        session_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    game_session = db.query(GameSession).filter(
        GameSession.session_id == session_id
    ).first()

    if not game_session:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if current_user.id not in game_session.player_ids:
        raise HTTPException(status_code=403, detail="您不在此游戏中")

    rows = db.query(
        ServerVote.server_key,
        func.count(ServerVote.id).label("count"),
    ).filter(
        ServerVote.game_session_id == session_id,
    ).group_by(ServerVote.server_key).all()

    tally = {r.server_key: r.count for r in rows}
    total_votes = sum(tally.values())

    server_labels = {
        k: v.get("label", k) for k, v in settings.SERVER_HOSTS.items()
    }

    return {
        "tally": tally,
        "total_votes": total_votes,
        "total_players": len(game_session.player_ids),
        "deadline": game_session.vote_deadline,
        "available_servers": _available_servers(),
        "server_labels": server_labels,
    }

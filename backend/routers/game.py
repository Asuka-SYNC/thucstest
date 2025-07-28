from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from models import User, GameSession, get_db
from auth import get_current_user

router = APIRouter(prefix="/game", tags=["game"])


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

    # 获取玩家信息
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
        "started_at": game_session.started_at
    }

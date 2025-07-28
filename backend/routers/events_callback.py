from enum import Enum
from typing import Optional, List
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import json
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel
from pydantic import Field

router = APIRouter(prefix="/matchzy", tags=["matchzy"])


class EventType(str, Enum):
    SERIES_START = "series_start"
    MAP_RESULT = "map_result"
    SERIES_END = "series_end"
    SIDE_PICKED = "side_picked"
    MAP_PICKED = "map_picked"
    MAP_VETOED = "map_vetoed"
    GOING_LIVE = "going_live"
    ROUND_END = "round_end"
    DEMO_UPLOAD_ENDED = "demo_upload_ended"


class MatchZyTeamWrapper(BaseModel):
    id: str
    name: str


class MatchZyPlayer(BaseModel):
    steam_id: Optional[str] = None
    name: Optional[str] = None
    kills: Optional[int] = 0
    deaths: Optional[int] = 0
    assists: Optional[int] = 0
    damage: Optional[int] = 0
    # 可以根据实际数据结构添加更多字段


class MatchZyStatsTeam(BaseModel):
    id: str
    name: str
    series_score: int = 0
    score: int = 0
    score_ct: Optional[int] = 0
    score_t: Optional[int] = 0
    players: List[MatchZyPlayer] = []
    side: Optional[str] = None
    starting_side: Optional[str] = None


class Winner(BaseModel):
    side: str
    team: str


# 各种事件的数据模型
class SeriesStartEvent(BaseModel):
    event: str = Field(..., description="事件名称")
    matchid: int = Field(..., description="比赛ID")
    num_maps: int = Field(..., ge=1, description="地图数量")
    team1: MatchZyTeamWrapper
    team2: MatchZyTeamWrapper


class MapResultEvent(BaseModel):
    event: str = Field(..., description="事件名称")
    matchid: int = Field(..., description="比赛ID")
    map_number: int = Field(..., ge=0, description="地图编号")
    team1: MatchZyStatsTeam
    team2: MatchZyStatsTeam
    winner: Winner


class SeriesEndEvent(BaseModel):
    event: str = Field(..., description="事件名称")
    matchid: int = Field(..., description="比赛ID")
    team1_series_score: int = Field(..., ge=0, description="队伍1系列赛分数")
    team2_series_score: int = Field(..., ge=0, description="队伍2系列赛分数")
    winner: Winner
    time_until_restore: int = Field(..., ge=0, description="恢复时间")


class SidePickedEvent(BaseModel):
    event: str = Field(..., description="事件名称")
    matchid: int = Field(..., description="比赛ID")
    team: str = Field(..., description="选择的队伍")
    map_name: str = Field(..., description="地图名称")
    side: str = Field(..., description="选择的阵营")
    map_number: int = Field(..., ge=0, description="地图编号")


class MapPickedEvent(BaseModel):
    event: str = Field(..., description="事件名称")
    matchid: int = Field(..., description="比赛ID")
    team: str = Field(..., description="选择的队伍")
    map_name: str = Field(..., description="地图名称")
    map_number: int = Field(..., ge=0, description="地图编号")


class MapVetoedEvent(BaseModel):
    event: str = Field(..., description="事件名称")
    matchid: int = Field(..., description="比赛ID")
    team: str = Field(..., description="禁用的队伍")
    map_name: str = Field(..., description="地图名称")
    map_number: int = Field(..., ge=0, description="地图编号")


class GoingLiveEvent(BaseModel):
    event: str = Field(..., description="事件名称")
    matchid: int = Field(..., description="比赛ID")
    map_number: int = Field(..., ge=0, description="地图编号")


class RoundEndEvent(BaseModel):
    event: str = Field(..., description="事件名称")
    matchid: int = Field(..., description="比赛ID")
    map_number: int = Field(..., ge=0, description="地图编号")
    round_number: int = Field(..., ge=0, description="回合编号")
    round_time: int = Field(..., ge=0, description="回合时间(毫秒)")
    reason: int = Field(..., ge=0, description="结束原因")
    winner: Winner
    team1: MatchZyStatsTeam
    team2: MatchZyStatsTeam


class DemoUploadEndedEvent(BaseModel):
    event: str = Field(..., description="事件名称")
    matchid: int = Field(..., description="比赛ID")
    map_number: int = Field(..., ge=0, description="地图编号")
    filename: str = Field(..., description="文件名")
    success: bool = Field(..., description="上传是否成功")


# 通用的webhook事件模型
class WebhookEvent(BaseModel):
    event: str
    # 其他字段根据实际事件类型动态解析


# 联合类型，用于类型提示
WebhookEventUnion = Union[
    SeriesStartEvent,
    MapResultEvent,
    SeriesEndEvent,
    SidePickedEvent,
    MapPickedEvent,
    MapVetoedEvent,
    GoingLiveEvent,
    RoundEndEvent,
    DemoUploadEndedEvent
]


def print_event_info(event_type: str, data: Dict[str, Any]):
    """打印事件信息的通用函数"""
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"事件类型: {event_type}")
    print(f"数据内容:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("=" * 60)


def handle_series_start(data: SeriesStartEvent):
    """处理系列赛开始事件"""
    print_event_info("系列赛开始", data.dict())
    print(f"比赛ID: {data.matchid}")
    print(f"地图数量: {data.num_maps}")
    print(f"队伍1: {data.team1.name} (ID: {data.team1.id})")
    print(f"队伍2: {data.team2.name} (ID: {data.team2.id})")


def handle_map_result(data: MapResultEvent):
    """处理地图结果事件"""
    print_event_info("地图结果", data.dict())
    print(f"比赛ID: {data.matchid}")
    print(f"地图编号: {data.map_number}")
    print(f"获胜方: {data.winner.team} ({data.winner.side})")
    print(f"队伍1 {data.team1.name}: {data.team1.score} (CT: {data.team1.score_ct}, T: {data.team1.score_t})")
    print(f"队伍2 {data.team2.name}: {data.team2.score} (CT: {data.team2.score_ct}, T: {data.team2.score_t})")
    print(f"队伍1玩家数: {len(data.team1.players)}")
    print(f"队伍2玩家数: {len(data.team2.players)}")


def handle_series_end(data: SeriesEndEvent):
    """处理系列赛结束事件"""
    print_event_info("系列赛结束", data.dict())
    print(f"比赛ID: {data.matchid}")
    print(f"队伍1分数: {data.team1_series_score}")
    print(f"队伍2分数: {data.team2_series_score}")
    print(f"获胜方: {data.winner.team} ({data.winner.side})")
    print(f"恢复时间: {data.time_until_restore}秒")


def handle_side_picked(data: SidePickedEvent):
    """处理阵营选择事件"""
    print_event_info("阵营选择", data.dict())
    print(f"比赛ID: {data.matchid}")
    print(f"选择队伍: {data.team}")
    print(f"地图名称: {data.map_name}")
    print(f"选择阵营: {data.side}")
    print(f"地图编号: {data.map_number}")


def handle_map_picked(data: MapPickedEvent):
    """处理地图选择事件"""
    print_event_info("地图选择", data.dict())
    print(f"比赛ID: {data.matchid}")
    print(f"选择队伍: {data.team}")
    print(f"地图名称: {data.map_name}")
    print(f"地图编号: {data.map_number}")


def handle_map_vetoed(data: MapVetoedEvent):
    """处理地图禁用事件"""
    print_event_info("地图禁用", data.dict())
    print(f"比赛ID: {data.matchid}")
    print(f"禁用队伍: {data.team}")
    print(f"地图名称: {data.map_name}")
    print(f"地图编号: {data.map_number}")


def handle_going_live(data: GoingLiveEvent):
    """处理比赛开始事件"""
    print_event_info("比赛开始", data.dict())
    print(f"比赛ID: {data.matchid}")
    print(f"地图编号: {data.map_number}")


def handle_round_end(data: RoundEndEvent):
    """处理回合结束事件"""
    print_event_info("回合结束", data.dict())
    print(f"比赛ID: {data.matchid}")
    print(f"地图编号: {data.map_number}")
    print(f"回合编号: {data.round_number}")
    print(f"回合时间: {data.round_time}ms")
    print(f"结束原因: {data.reason}")
    print(f"获胜方: {data.winner.team} ({data.winner.side})")
    print(f"队伍1 {data.team1.name}: {data.team1.score}")
    print(f"队伍2 {data.team2.name}: {data.team2.score}")


def handle_demo_upload_ended(data: DemoUploadEndedEvent):
    """处理演示上传结束事件"""
    print_event_info("演示上传结束", data.dict())
    print(f"比赛ID: {data.matchid}")
    print(f"地图编号: {data.map_number}")
    print(f"文件名: {data.filename}")
    print(f"上传成功: {data.success}")


# 事件处理器映射
EVENT_HANDLERS = {
    EventType.SERIES_START: handle_series_start,
    EventType.MAP_RESULT: handle_map_result,
    EventType.SERIES_END: handle_series_end,
    EventType.SIDE_PICKED: handle_side_picked,
    EventType.MAP_PICKED: handle_map_picked,
    EventType.MAP_VETOED: handle_map_vetoed,
    EventType.GOING_LIVE: handle_going_live,
    EventType.ROUND_END: handle_round_end,
    EventType.DEMO_UPLOAD_ENDED: handle_demo_upload_ended,
}

# 事件模型映射
EVENT_MODELS = {
    EventType.SERIES_START: SeriesStartEvent,
    EventType.MAP_RESULT: MapResultEvent,
    EventType.SERIES_END: SeriesEndEvent,
    EventType.SIDE_PICKED: SidePickedEvent,
    EventType.MAP_PICKED: MapPickedEvent,
    EventType.MAP_VETOED: MapVetoedEvent,
    EventType.GOING_LIVE: GoingLiveEvent,
    EventType.ROUND_END: RoundEndEvent,
    EventType.DEMO_UPLOAD_ENDED: DemoUploadEndedEvent,
}


@router.post("/hook")
async def webhook_receiver(request: Request):
    """
    MatchZy Webhook 接收端点
    接收所有的MatchZy事件
    """
    try:
        # 获取原始请求体
        body = await request.body()

        # 解析JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"原始数据: {body}")
            raise HTTPException(status_code=400, detail="Invalid JSON")

        # 打印原始数据
        print("\n" + "=" * 80)
        print("收到Webhook请求")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("原始数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("=" * 80)

        # 获取事件类型
        event_type = data.get("event")
        if not event_type:
            print("错误: 缺少event字段")
            raise HTTPException(status_code=400, detail="Missing event field")

        # 验证事件类型
        try:
            event_enum = EventType(event_type)
        except ValueError:
            print(f"警告: 未知的事件类型: {event_type}")
            print("支持的事件类型:")
            for et in EventType:
                print(f"  - {et.value}")
            # 对于未知事件类型，仍然返回200但不处理
            return JSONResponse(
                status_code=200,
                content={"status": "received", "message": f"Unknown event type: {event_type}"}
            )

        # 根据事件类型进行数据验证和处理
        if event_enum in EVENT_MODELS:
            model_class = EVENT_MODELS[event_enum]
            try:
                # 使用对应的模型验证数据
                validated_data = model_class(**data)

                # 调用对应的处理函数
                if event_enum in EVENT_HANDLERS:
                    EVENT_HANDLERS[event_enum](validated_data)
                else:
                    print(f"警告: 事件类型 {event_type} 没有对应的处理函数")
                    print_event_info(f"未处理事件: {event_type}", data)

            except ValidationError as e:
                print(f"数据验证错误: {e}")
                print("原始数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                # 即使验证失败，也返回200以避免MatchZy重试
                return JSONResponse(
                    status_code=200,
                    content={"status": "received", "message": "Data validation failed but received"}
                )
        else:
            print(f"警告: 事件类型 {event_type} 没有对应的模型")
            print_event_info(f"无模型事件: {event_type}", data)

        # 返回200状态码表示成功接收
        return JSONResponse(
            status_code=200,
            content={"status": "received", "event": event_type, "matchid": data.get("matchid")}
        )

    except Exception as e:
        print(f"处理Webhook时发生错误: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()

        # 即使发生错误，也返回200以避免MatchZy重试
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": str(e)}
        )


@router.get("/hook")
async def root():
    """健康检查端点"""
    return {"message": "MatchZy Webhook Receiver is running", "status": "healthy"}


@router.get("/hook/events")
async def supported_events():
    """返回支持的事件类型"""
    return {
        "supported_events": [event.value for event in EventType],
        "total_events": len(EventType)
    }

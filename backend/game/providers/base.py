from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServerInfo:
    server_ref: str
    container_name: str
    public_ip: str
    game_port: int
    gotv_port: int
    connect_url: str
    provider: str


class BaseServerProvider(ABC):
    @abstractmethod
    async def start_server(
        self, match_id: str, env_vars: Optional[dict] = None
    ) -> ServerInfo:
        ...

    @abstractmethod
    async def stop_server(self, server_ref: str) -> None:
        ...

    @abstractmethod
    async def get_server_status(self, server_ref: str) -> dict:
        ...

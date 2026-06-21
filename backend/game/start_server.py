import logging
from typing import Optional

from config import settings
from .providers.base import BaseServerProvider, ServerInfo

logger = logging.getLogger(__name__)

_PROVIDER_CACHE: dict[str, BaseServerProvider] = {}


def _create_provider(server_key: str) -> BaseServerProvider:
    host = settings.SERVER_HOSTS.get(server_key)
    if not host:
        raise ValueError(
            f"Unknown server '{server_key}'. "
            f"Available: {list(settings.SERVER_HOSTS.keys())}"
        )

    mode = host["mode"]

    if mode == "local_docker":
        from .providers.local_docker import LocalDockerProvider

        return LocalDockerProvider()

    if mode == "remote_docker":
        from .providers.remote_docker import RemoteDockerProvider

        return RemoteDockerProvider()

    if mode == "tencent_as":
        from .providers.tencent_as import TencentASProvider

        return TencentASProvider()

    if mode == "aliyun_eci":
        from .providers.aliyun_eci import AliyunECIProvider

        return AliyunECIProvider()

    raise ValueError(f"Unknown server mode '{mode}' for server '{server_key}'")


def get_provider(server_key: Optional[str] = None) -> BaseServerProvider:
    server_key = server_key or settings.SERVER_DEFAULT
    if server_key not in _PROVIDER_CACHE:
        _PROVIDER_CACHE[server_key] = _create_provider(server_key)
    return _PROVIDER_CACHE[server_key]


async def start_cs2_server(
    server_key: Optional[str] = None,
    match_id: str = "",
    env_vars: Optional[dict] = None,
) -> ServerInfo:
    provider = get_provider(server_key)
    return await provider.start_server(match_id=match_id, env_vars=env_vars)


async def stop_cs2_server(server_key: str, server_ref: str) -> None:
    provider = get_provider(server_key)
    await provider.stop_server(server_ref)


async def get_cs2_server_status(server_key: str, server_ref: str) -> dict:
    provider = get_provider(server_key)
    return await provider.get_server_status(server_ref)

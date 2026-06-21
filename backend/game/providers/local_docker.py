import asyncio
import logging
import socket
from typing import Optional

import docker
from docker.errors import NotFound

from .base import BaseServerProvider, ServerInfo
from config import settings

logger = logging.getLogger(__name__)

CS2_GAME_PORT = 27015
CS2_GOTV_PORT = 27020


class LocalDockerProvider(BaseServerProvider):
    def __init__(self):
        self.client = docker.from_env()
        self.image = settings.CS2_DOCKER_IMAGE
        if not self.image:
            raise ValueError("CS2_DOCKER_IMAGE is not configured")
        self.public_ip = (
            settings.LOCAL_DOCKER_PUBLIC_IP or self._detect_local_ip()
        )

    @staticmethod
    def _detect_local_ip() -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()

    def _build_env(self, match_id: str, env_vars: Optional[dict]) -> dict:
        env = {"MATCH_ID": match_id}
        if settings.MATCHZY_WEBHOOK_TOKEN:
            env["MATCHZY_REMOTE_LOG_URL"] = f"{settings.SITE_URL}/matchzy/hook"
            env["MATCHZY_REMOTE_LOG_HEADER_VALUE"] = settings.MATCHZY_WEBHOOK_TOKEN
        if env_vars:
            env.update({k: str(v) for k, v in env_vars.items()})
        return env

    async def start_server(
        self, match_id: str, env_vars: Optional[dict] = None
    ) -> ServerInfo:
        container_name = f"cs2-{match_id}"[:63]
        env = self._build_env(match_id, env_vars)
        nano_cpus = settings.CS2_DOCKER_CPU * 1_000_000_000

        logger.info(
            "Starting local container %s (cpu=%d, mem=%s)",
            container_name,
            settings.CS2_DOCKER_CPU,
            settings.CS2_DOCKER_MEMORY,
        )

        container = await asyncio.to_thread(
            self.client.containers.run,
            image=self.image,
            name=container_name,
            nano_cpus=nano_cpus,
            mem_limit=settings.CS2_DOCKER_MEMORY,
            restart_policy={"Name": "unless-stopped"},
            ports={
                f"{CS2_GAME_PORT}/tcp": CS2_GAME_PORT,
                f"{CS2_GAME_PORT}/udp": CS2_GAME_PORT,
                f"{CS2_GOTV_PORT}/udp": CS2_GOTV_PORT,
            },
            environment=env,
            detach=True,
        )

        logger.info("Container %s started (id=%s)", container_name, container.short_id)

        return ServerInfo(
            server_ref=container.id,
            container_name=container_name,
            public_ip=self.public_ip,
            game_port=CS2_GAME_PORT,
            gotv_port=CS2_GOTV_PORT,
            connect_url=f"steam://connect/{self.public_ip}:{CS2_GAME_PORT}",
            provider="local_docker",
        )

    async def stop_server(self, server_ref: str) -> None:
        try:
            container = await asyncio.to_thread(
                self.client.containers.get, server_ref
            )
            await asyncio.to_thread(container.stop, timeout=30)
            await asyncio.to_thread(container.remove, force=True)
            logger.info("Container %s stopped and removed", server_ref[:12])
        except NotFound:
            logger.warning("Container %s not found, already removed", server_ref[:12])

    async def get_server_status(self, server_ref: str) -> dict:
        try:
            container = await asyncio.to_thread(
                self.client.containers.get, server_ref
            )
            return {
                "server_ref": container.id,
                "status": container.status,
                "name": container.name,
                "provider": "local_docker",
            }
        except NotFound:
            return {
                "server_ref": server_ref,
                "status": "not_found",
                "provider": "local_docker",
            }

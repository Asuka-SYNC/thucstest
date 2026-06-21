import asyncio
import logging
import os
from typing import Optional

import paramiko

from .base import BaseServerProvider, ServerInfo
from config import settings

logger = logging.getLogger(__name__)

CS2_GAME_PORT = 27015
CS2_GOTV_PORT = 27020


class RemoteDockerProvider(BaseServerProvider):
    def __init__(self):
        self.host = settings.REMOTE_DOCKER_HOST
        self.ssh_user = settings.REMOTE_DOCKER_SSH_USER
        self.ssh_port = settings.REMOTE_DOCKER_SSH_PORT
        self.ssh_key = os.path.expanduser(settings.REMOTE_DOCKER_SSH_KEY)
        self.image = settings.CS2_DOCKER_IMAGE
        self.public_ip = settings.REMOTE_DOCKER_PUBLIC_IP or self.host

        if not self.host:
            raise ValueError("REMOTE_DOCKER_HOST is not configured")
        if not self.image:
            raise ValueError("CS2_DOCKER_IMAGE is not configured")

    def _run_ssh(self, command: str, timeout: int = 120) -> str:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                self.host,
                port=self.ssh_port,
                username=self.ssh_user,
                key_filename=self.ssh_key,
                timeout=15,
            )
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if exit_code != 0:
                raise RuntimeError(
                    f"SSH command failed (exit {exit_code}): {err or out}"
                )
            return out
        finally:
            client.close()

    def _build_env_flags(self, match_id: str, env_vars: Optional[dict]) -> str:
        flags = [f"-e MATCH_ID={match_id}"]
        if settings.MATCHZY_WEBHOOK_TOKEN:
            flags.append(
                f"-e MATCHZY_REMOTE_LOG_URL={settings.SITE_URL}/matchzy/hook"
            )
            flags.append(
                f"-e MATCHZY_REMOTE_LOG_HEADER_VALUE={settings.MATCHZY_WEBHOOK_TOKEN}"
            )
        if env_vars:
            for k, v in env_vars.items():
                flags.append(f"-e {k}={v}")
        return " ".join(flags)

    async def start_server(
        self, match_id: str, env_vars: Optional[dict] = None
    ) -> ServerInfo:
        container_name = f"cs2-{match_id}"[:63]
        env_flags = self._build_env_flags(match_id, env_vars)

        cmd = (
            f"docker run -d --name {container_name} "
            f"--restart unless-stopped "
            f"--cpus={settings.CS2_DOCKER_CPU} "
            f"--memory={settings.CS2_DOCKER_MEMORY} "
            f"-p {CS2_GAME_PORT}:{CS2_GAME_PORT}/tcp "
            f"-p {CS2_GAME_PORT}:{CS2_GAME_PORT}/udp "
            f"-p {CS2_GOTV_PORT}:{CS2_GOTV_PORT}/udp "
            f"{env_flags} "
            f"{self.image}"
        )

        logger.info("Starting remote container %s on %s", container_name, self.host)
        container_id = await asyncio.to_thread(self._run_ssh, cmd)
        logger.info(
            "Remote container %s started on %s (id=%s)",
            container_name,
            self.host,
            container_id[:12],
        )

        return ServerInfo(
            server_ref=container_id,
            container_name=container_name,
            public_ip=self.public_ip,
            game_port=CS2_GAME_PORT,
            gotv_port=CS2_GOTV_PORT,
            connect_url=f"steam://connect/{self.public_ip}:{CS2_GAME_PORT}",
            provider="remote_docker",
        )

    async def stop_server(self, server_ref: str) -> None:
        try:
            await asyncio.to_thread(
                self._run_ssh,
                f"docker rm -f {server_ref}",
            )
            logger.info("Remote container %s removed", server_ref[:12])
        except RuntimeError as e:
            if "No such container" in str(e) or "No such object" in str(e):
                logger.warning("Container %s not found", server_ref[:12])
            else:
                raise

    async def get_server_status(self, server_ref: str) -> dict:
        try:
            status = await asyncio.to_thread(
                self._run_ssh,
                f"docker inspect --format='{{{{.State.Status}}}}' {server_ref}",
            )
            return {
                "server_ref": server_ref,
                "status": status,
                "provider": "remote_docker",
            }
        except RuntimeError:
            return {
                "server_ref": server_ref,
                "status": "not_found",
                "provider": "remote_docker",
            }

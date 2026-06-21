import asyncio
import json
import logging
from typing import Optional

from alibabacloud_eci20180808.client import Client as EciClient
from alibabacloud_eci20180808 import models as eci_models
from alibabacloud_tea_openapi import models as open_api_models

from .base import BaseServerProvider, ServerInfo
from config import settings

logger = logging.getLogger(__name__)

CS2_GAME_PORT = 27015
CS2_GOTV_PORT = 27020
POLL_INTERVAL = 5
FAILED_STATES = frozenset({"Failed", "ScheduleFailed", "Terminating", "Expired"})


class AliyunECIProvider(BaseServerProvider):
    def __init__(self):
        if not settings.ALIYUN_ACCESS_KEY_ID or not settings.ALIYUN_ACCESS_KEY_SECRET:
            raise ValueError("ALIYUN_ACCESS_KEY_ID and ALIYUN_ACCESS_KEY_SECRET must be configured")
        if not settings.ECI_SECURITY_GROUP_ID or not settings.ECI_VSWITCH_ID:
            raise ValueError("ECI_SECURITY_GROUP_ID and ECI_VSWITCH_ID must be configured")
        if not settings.CS2_DOCKER_IMAGE:
            raise ValueError("CS2_DOCKER_IMAGE is not configured")

        self.region = settings.ECI_REGION
        self.image = settings.CS2_DOCKER_IMAGE
        self.security_group_id = settings.ECI_SECURITY_GROUP_ID
        self.vswitch_id = settings.ECI_VSWITCH_ID
        self.instance_type = settings.ECI_INSTANCE_TYPE or None
        self.cpu = float(settings.CS2_DOCKER_CPU)
        self.memory = settings.CS2_DOCKER_MEMORY.rstrip("gGmM")
        self.auto_create_eip = settings.ECI_AUTO_CREATE_EIP
        self.eip_bandwidth = settings.ECI_EIP_BANDWIDTH
        self.provision_timeout = settings.ECI_PROVISION_TIMEOUT

        api_config = open_api_models.Config(
            access_key_id=settings.ALIYUN_ACCESS_KEY_ID,
            access_key_secret=settings.ALIYUN_ACCESS_KEY_SECRET,
        )
        api_config.endpoint = f"eci.{self.region}.aliyuncs.com"
        self.client = EciClient(api_config)

    async def start_server(
        self, match_id: str, env_vars: Optional[dict] = None
    ) -> ServerInfo:
        group_name = f"cs2-{match_id}"[:63]
        logger.info("Creating ECI container group %s for match %s", group_name, match_id)

        container = self._build_container(match_id, env_vars)
        request = eci_models.CreateContainerGroupRequest(
            region_id=self.region,
            container_group_name=group_name,
            security_group_id=self.security_group_id,
            v_switch_id=self.vswitch_id,
            containers=[container],
            restart_policy="Always",
        )

        if self.auto_create_eip:
            request.auto_create_eip = True
            request.eip_bandwidth = self.eip_bandwidth
        if self.instance_type:
            request.instance_type = self.instance_type

        response = await asyncio.to_thread(self.client.create_container_group, request)
        cg_id = response.body.container_group_id
        logger.info("ECI container group created: %s", cg_id)

        public_ip = await self._wait_for_running(cg_id)

        return ServerInfo(
            server_ref=cg_id,
            container_name=group_name,
            public_ip=public_ip,
            game_port=CS2_GAME_PORT,
            gotv_port=CS2_GOTV_PORT,
            connect_url=f"steam://connect/{public_ip}:{CS2_GAME_PORT}",
            provider="aliyun_eci",
        )

    async def stop_server(self, server_ref: str) -> None:
        logger.info("Deleting ECI container group %s", server_ref)
        request = eci_models.DeleteContainerGroupRequest(
            region_id=self.region,
            container_group_id=server_ref,
            force=True,
        )
        try:
            await asyncio.to_thread(self.client.delete_container_group, request)
        except Exception as e:
            if "not found" in str(e).lower() or "not exist" in str(e).lower():
                logger.warning("ECI container group %s already removed", server_ref)
            else:
                raise

    async def get_server_status(self, server_ref: str) -> dict:
        try:
            cg = await asyncio.to_thread(self._describe_container_group, server_ref)
            return {
                "server_ref": server_ref,
                "status": cg.status,
                "provider": "aliyun_eci",
            }
        except Exception:
            return {
                "server_ref": server_ref,
                "status": "not_found",
                "provider": "aliyun_eci",
            }

    def _build_container(
        self, match_id: str, env_vars: Optional[dict]
    ) -> eci_models.CreateContainerGroupRequestContainer:
        ports = [
            eci_models.CreateContainerGroupRequestContainerPort(
                port=CS2_GAME_PORT, protocol="TCP"
            ),
            eci_models.CreateContainerGroupRequestContainerPort(
                port=CS2_GAME_PORT, protocol="UDP"
            ),
            eci_models.CreateContainerGroupRequestContainerPort(
                port=CS2_GOTV_PORT, protocol="UDP"
            ),
        ]

        env_list = []
        merged_env = self._build_env(match_id, env_vars)
        for key, value in merged_env.items():
            env_list.append(
                eci_models.CreateContainerGroupRequestContainerEnvironmentVar(
                    key=key, value=str(value),
                )
            )

        return eci_models.CreateContainerGroupRequestContainer(
            image=self.image,
            name="cs2-server",
            cpu=self.cpu,
            memory=float(self.memory),
            ports=ports,
            environment_vars=env_list,
        )

    @staticmethod
    def _build_env(match_id: str, env_vars: Optional[dict]) -> dict:
        env = {"MATCH_ID": match_id}
        if settings.MATCHZY_WEBHOOK_TOKEN:
            env["MATCHZY_REMOTE_LOG_URL"] = f"{settings.SITE_URL}/matchzy/hook"
            env["MATCHZY_REMOTE_LOG_HEADER_VALUE"] = settings.MATCHZY_WEBHOOK_TOKEN
        if env_vars:
            env.update({k: str(v) for k, v in env_vars.items()})
        return env

    def _describe_container_group(
        self, container_group_id: str
    ) -> eci_models.DescribeContainerGroupsResponseBodyContainerGroups:
        request = eci_models.DescribeContainerGroupsRequest(
            region_id=self.region,
            container_group_ids=json.dumps([container_group_id]),
        )
        response = self.client.describe_container_groups(request)
        if not response.body.container_groups:
            raise RuntimeError(f"Container group {container_group_id} not found")
        return response.body.container_groups[0]

    async def _wait_for_running(self, container_group_id: str) -> str:
        loop = asyncio.get_event_loop()
        deadline = loop.time() + self.provision_timeout

        while loop.time() < deadline:
            cg = await asyncio.to_thread(
                self._describe_container_group, container_group_id
            )

            if cg.status == "Running":
                if not cg.internet_ip:
                    raise RuntimeError(
                        f"ECI {container_group_id} is Running but has no public IP"
                    )
                logger.info(
                    "ECI %s running (ip=%s)", container_group_id, cg.internet_ip
                )
                return cg.internet_ip

            if cg.status in FAILED_STATES:
                raise RuntimeError(
                    f"ECI {container_group_id} entered bad state: {cg.status}"
                )

            logger.debug(
                "Waiting for ECI %s (state=%s, %ds remaining)",
                container_group_id,
                cg.status,
                int(deadline - loop.time()),
            )
            await asyncio.sleep(POLL_INTERVAL)

        raise TimeoutError(
            f"ECI {container_group_id} did not reach Running state "
            f"within {self.provision_timeout}s"
        )

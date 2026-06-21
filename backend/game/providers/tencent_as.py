import asyncio
import logging
from typing import Optional

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.autoscaling.v20180419 import autoscaling_client, models as as_models
from tencentcloud.cvm.v20170312 import cvm_client, models as cvm_models

from .base import BaseServerProvider, ServerInfo
from config import settings

logger = logging.getLogger(__name__)

CS2_GAME_PORT = 27015
CS2_GOTV_PORT = 27020
POLL_INTERVAL = 10


class TencentASProvider(BaseServerProvider):
    def __init__(self):
        if not settings.TENCENT_SECRET_ID or not settings.TENCENT_SECRET_KEY:
            raise ValueError("TENCENT_SECRET_ID and TENCENT_SECRET_KEY must be configured")
        if not settings.TENCENT_AS_GROUP_ID:
            raise ValueError("TENCENT_AS_GROUP_ID must be configured")

        self.group_id = settings.TENCENT_AS_GROUP_ID
        self.region = settings.TENCENT_AS_REGION
        self.provision_timeout = settings.TENCENT_AS_PROVISION_TIMEOUT

        cred = credential.Credential(
            settings.TENCENT_SECRET_ID, settings.TENCENT_SECRET_KEY
        )

        http_profile = HttpProfile()
        http_profile.scheme = "https"
        http_profile.reqTimeout = 30
        http_profile.endpoint = "as.tencentcloudapi.com"

        as_profile = ClientProfile()
        as_profile.httpProfile = http_profile

        cvm_http = HttpProfile()
        cvm_http.scheme = "https"
        cvm_http.reqTimeout = 30
        cvm_http.endpoint = "cvm.tencentcloudapi.com"
        cvm_profile = ClientProfile()
        cvm_profile.httpProfile = cvm_http

        self.as_client = autoscaling_client.AutoscalingClient(
            cred, self.region, as_profile
        )
        self.cvm_client = cvm_client.CvmClient(cred, self.region, cvm_profile)

    async def start_server(
        self, match_id: str, env_vars: Optional[dict] = None
    ) -> ServerInfo:
        logger.info(
            "Scaling out AS group %s to 1 instance for match %s",
            self.group_id,
            match_id,
        )
        await asyncio.to_thread(self._scale_to, 1)

        instance_id = await self._wait_for_healthy_instance()

        public_ip = await asyncio.to_thread(self._get_public_ip, instance_id)
        logger.info(
            "AS instance %s ready (ip=%s) for match %s",
            instance_id,
            public_ip,
            match_id,
        )

        return ServerInfo(
            server_ref=instance_id,
            container_name=f"tencent-{instance_id}",
            public_ip=public_ip,
            game_port=CS2_GAME_PORT,
            gotv_port=CS2_GOTV_PORT,
            connect_url=f"steam://connect/{public_ip}:{CS2_GAME_PORT}",
            provider="tencent_as",
        )

    async def stop_server(self, server_ref: str) -> None:
        logger.info("Removing AS instance %s from group %s", server_ref, self.group_id)
        try:
            await asyncio.to_thread(self._remove_instance, server_ref)
        except TencentCloudSDKException as e:
            if "not found" in str(e).lower() or "not exist" in str(e).lower():
                logger.warning("AS instance %s already removed", server_ref)
            else:
                raise

    async def get_server_status(self, server_ref: str) -> dict:
        try:
            status = await asyncio.to_thread(self._describe_instance, server_ref)
            return {
                "server_ref": server_ref,
                "status": status,
                "provider": "tencent_as",
            }
        except TencentCloudSDKException:
            return {
                "server_ref": server_ref,
                "status": "not_found",
                "provider": "tencent_as",
            }

    def _scale_to(self, desired: int) -> None:
        req = as_models.ModifyDesiredCapacityRequest()
        req.AutoScalingGroupId = self.group_id
        req.DesiredCapacity = desired
        self.as_client.ModifyDesiredCapacity(req)

    def _list_group_instances(self) -> list[as_models.Instance]:
        req = as_models.DescribeAutoScalingInstancesRequest()
        flt = as_models.Filter()
        flt.Name = "auto-scaling-group-id"
        flt.Values = [self.group_id]
        req.Filters = [flt]
        resp = self.as_client.DescribeAutoScalingInstances(req)
        return resp.AutoScalingInstanceSet

    def _get_public_ip(self, instance_id: str) -> str:
        req = cvm_models.DescribeInstancesRequest()
        req.InstanceIds = [instance_id]
        resp = self.cvm_client.DescribeInstances(req)
        if not resp.InstanceSet:
            raise RuntimeError(f"Instance {instance_id} not found in CVM")
        inst = resp.InstanceSet[0]
        if not inst.PublicIpAddresses:
            raise RuntimeError(f"Instance {instance_id} has no public IP")
        return inst.PublicIpAddresses[0]

    def _remove_instance(self, instance_id: str) -> None:
        req = as_models.RemoveInstancesRequest()
        req.AutoScalingGroupId = self.group_id
        req.InstanceIds = [instance_id]
        self.as_client.RemoveInstances(req)

    def _describe_instance(self, instance_id: str) -> str:
        req = as_models.DescribeAutoScalingInstancesRequest()
        req.InstanceIds = [instance_id]
        resp = self.as_client.DescribeAutoScalingInstances(req)
        if not resp.AutoScalingInstanceSet:
            raise TencentCloudSDKException("NotFound", "instance not found")
        inst = resp.AutoScalingInstanceSet[0]
        return inst.LifeCycleState

    async def _wait_for_healthy_instance(self) -> str:
        loop = asyncio.get_event_loop()
        deadline = loop.time() + self.provision_timeout

        while loop.time() < deadline:
            instances = await asyncio.to_thread(self._list_group_instances)
            for inst in instances:
                if (
                    inst.LifeCycleState == "IN_SERVICE"
                    and inst.HealthStatus == "HEALTHY"
                ):
                    return inst.InstanceId
            logger.debug(
                "Waiting for AS instance in group %s (%ds remaining)",
                self.group_id,
                int(deadline - loop.time()),
            )
            await asyncio.sleep(POLL_INTERVAL)

        raise TimeoutError(
            f"AS group {self.group_id} did not produce a healthy instance "
            f"within {self.provision_timeout}s"
        )

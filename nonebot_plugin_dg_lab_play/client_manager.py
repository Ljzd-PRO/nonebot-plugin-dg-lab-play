import asyncio
from functools import cached_property
from typing import Dict, Optional, Union, Self, Callable, Any, List

from loguru import logger
from nonebot import get_plugin_config, get_driver
from pydglab_ws import DGLabClient, DGLabWSServer, StrengthData, FeedbackButton, DGLabWSConnect, RetCode, DGLabWSClient, \
    PulseOperation, Channel

from .config import Config

__all__ = ["DGLabPlayClient", "client_manager"]

APP_PULSE_QUEUE_LEN = 50
"""DG-Lab App 波形队列最大持续时长"""

config = get_plugin_config(Config)
driver = get_driver()


class DGLabPlayClient:
    """
    单个终端的连接管理器

    :param user_id: 用户 ID，如 QQ 号
    :param client: pydglab-ws 的终端对象
    """

    def __init__(self, user_id: str, destroy_callback: Callable[[Self], Any], client: DGLabClient = None):
        self.user_id = user_id
        self.client: Optional[DGLabClient] = client
        self._destroy_callback = destroy_callback
        self.last_strength: Optional[StrengthData] = None
        self.last_feedback: Optional[FeedbackButton] = None
        self.fetch_task: Optional[asyncio.Task] = None
        self._pulse_data: List[PulseOperation] = []
        self.pulse_task: Optional[asyncio.Task] = None
        self.is_destroyed: bool = False

        self.register_finished_lock = asyncio.Lock()
        self.bind_finished_lock = asyncio.Lock()

    async def __aenter__(self) -> Self:
        for lock in self.register_finished_lock, self.bind_finished_lock:
            await lock.acquire()
        self.fetch_task = asyncio.create_task(self._serve())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return

    @cached_property
    def qrcode(self) -> Optional[str]:
        return self.client.get_qrcode(
            config.dg_lab_play.ws_server.remote_server_uri if config.dg_lab_play.ws_server.remote_server else
            config.dg_lab_play.ws_server.local_server_publish_uri
        )

    @property
    def pulse_data(self) -> List[PulseOperation]:
        return self._pulse_data

    async def _destroy(self):
        """断开终端的 WS 连接，调用回调函数，并解锁等待锁，以及取消消息获取的任务"""
        self.is_destroyed = True
        if self.client and isinstance(self.client, DGLabWSClient):
            await self.client.websocket.close()
        self._destroy_callback(self)
        for lock in self.register_finished_lock, self.bind_finished_lock:
            if lock.locked():
                lock.release()
        if self.fetch_task:
            self.fetch_task.cancel()

    async def wait_for_bind(self, rebind: bool = False) -> bool:
        """
        等待绑定

        :return: 是否超时
        """
        try:
            await asyncio.wait_for(
                self.client.bind() if not rebind else self.client.rebind(),
                timeout=config.dg_lab_play.dg_lab_client.bind_timeout
            )
            return True
        except asyncio.TimeoutError:
            await self._destroy()
            return False
        finally:
            if self.bind_finished_lock.locked():
                self.bind_finished_lock.release()

    def setup_pulse_job(self, pulse_data: List[PulseOperation], *channels: Channel):
        """
        设置波形发送任务

        :param pulse_data: 波形数据
        :param channels: 目标通道
        """
        self._pulse_data.clear()
        self._pulse_data.extend(pulse_data)
        if self.pulse_task and not self.pulse_task.cancelled() and not self.pulse_task.done():
            self.pulse_task.cancel()
        self.pulse_task = asyncio.create_task(
            self._pulse_job(pulse_data, *channels)
        )

    async def _handle_data(self, data: Union[StrengthData, FeedbackButton, RetCode]):
        """处理消息"""
        if isinstance(data, StrengthData):
            self.last_strength = data
        elif isinstance(data, FeedbackButton):
            self.last_feedback = data
        elif data == RetCode.CLIENT_DISCONNECTED:
            logger.info(f"终端 {self.client.client_id} 绑定的 App 已断开")
            async with self.bind_finished_lock:
                await self.wait_for_bind(rebind=True)

    async def _serve(self):
        """建立终端连接，并不断获取和处理消息"""
        if config.dg_lab_play.ws_server.remote_server:
            try:
                async with DGLabWSConnect(
                        config.dg_lab_play.ws_server.remote_server_uri,
                        config.dg_lab_play.dg_lab_client.register_timeout
                ) as client:
                    self.client = client
                    self.register_finished_lock.release()
                    logger.success(f"终端 {client.client_id} 成功注册")
                    if not await self.wait_for_bind():
                        logger.warning(f"终端 {client.client_id} 等待绑定超时")
                        return
                    logger.success(f"终端 {client.client_id} 成功与 App {client.target_id} 绑定")
                    async for data in client.data_generator():
                        await self._handle_data(data)
            except asyncio.TimeoutError:
                logger.error(f"终端从 {config.dg_lab_play.ws_server.remote_server_uri} 获取 clientId 超时")
                await self._destroy()
                return
        else:
            self.register_finished_lock.release()
            if not await self.wait_for_bind():
                logger.warning(f"终端 {self.client.client_id} 等待绑定超时")
                return
            logger.success(f"终端 {self.client.client_id} 成功与 App {self.client.target_id} 绑定")
            async for data in self.client.data_generator():
                await self._handle_data(data)

    async def _pulse_job(self, pulse_data: List[PulseOperation], *channels: Channel):
        if config.dg_lab_play.pulse_data.duration_per_post > APP_PULSE_QUEUE_LEN / 2:
            logger.warning("PulseDataConfig.duration_per_post 大于 DG-Lab App 队列最大时长的一半，可能导致波形出现中断")
        for channel in channels:
            await self.client.clear_pulses(channel)
        await asyncio.sleep(config.dg_lab_play.pulse_data.sleep_after_clear)

        pulse_data_duration = len(pulse_data) * 0.1
        replay_times = int(config.dg_lab_play.pulse_data.duration_per_post // pulse_data_duration)
        actual_duration = replay_times * pulse_data_duration
        max_pulse_num = int(APP_PULSE_QUEUE_LEN // actual_duration)
        pulse_data_for_post = pulse_data * replay_times

        for _ in range(max_pulse_num):
            for channel in channels:
                await self.client.add_pulses(channel, *pulse_data_for_post)
            await asyncio.sleep(config.dg_lab_play.pulse_data.post_interval)

        # 减去上面多余的睡眠时间
        await asyncio.sleep(abs(pulse_data_duration - config.dg_lab_play.pulse_data.post_interval))
        while True:
            for channel in channels:
                await self.client.add_pulses(channel, *pulse_data_for_post)
            await asyncio.sleep(pulse_data_duration)


class ClientManager:
    def __init__(self):
        self.user_id_to_client: Dict[str, DGLabPlayClient] = {}
        self.ws_server: Optional[DGLabWSServer] = None
        self.ws_server_task: Optional[asyncio.Task] = None

    async def _setup_server(self):
        if not config.dg_lab_play.ws_server.remote_server:
            async with DGLabWSServer(
                    config.dg_lab_play.ws_server.local_server_host,
                    config.dg_lab_play.ws_server.local_server_port,
                    config.dg_lab_play.ws_server.local_server_heartbeat_interval
            ) as server:
                self.ws_server = server
                logger.success(
                    f"已在 "
                    f"{config.dg_lab_play.ws_server.local_server_host}:{config.dg_lab_play.ws_server.local_server_port}"
                    f" 上启动 WebSocket 服务端"
                )
                await asyncio.Future()

    def serve(self):
        self.ws_server_task = asyncio.create_task(self._setup_server())

    async def new_client(self, user_id: str) -> Optional[DGLabPlayClient]:
        if not config.dg_lab_play.ws_server.remote_server:
            if self.ws_server:
                async with DGLabPlayClient(
                        user_id,
                        lambda x: self.user_id_to_client.pop(x.user_id),
                        self.ws_server.new_local_client()
                ) as play_client:
                    pass
                self.user_id_to_client[user_id] = play_client
                logger.info(f"用户 {user_id} 创建了 WebSocket 终端")
                return play_client
            else:
                return None
        else:
            async with DGLabPlayClient(
                    user_id,
                    lambda x: self.user_id_to_client.pop(x.user_id)
            ) as play_client:
                pass
            async with play_client.register_finished_lock:
                pass
            self.user_id_to_client[user_id] = play_client
            logger.info(f"用户 {user_id} 创建了本地终端")
            return play_client


client_manager = ClientManager()


@driver.on_startup
async def setup_ws_server():
    client_manager.serve()

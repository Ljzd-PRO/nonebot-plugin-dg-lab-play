from pathlib import Path
from typing import Optional

from loguru import logger
from nonebot import get_driver
from pydantic import BaseModel, model_validator

__all__ = [
    "DG_LAB_PLAY_DATA_LOCATION",
    "WSServerConfig",
    "DGLabClientConfig",
    "PulseDataConfig",
    "CommandTextConfig",
    "ReplyTextConfig",
    "DGLabPlayConfig",
    "Config"
]

DG_LAB_PLAY_DATA_LOCATION = Path("data/dg-lab-play")

driver = get_driver()


class WSServerConfig(BaseModel):
    """
    WebSocket 服务端设置

    :ivar remote_server: 是否连接到远程 WebSocket 服务端
    :ivar remote_server_uri: 远程服务端 URI
    :ivar local_server_host: 本地搭建的服务端 host
    :ivar local_server_port: 本地搭建的服务端监听端口
    :ivar local_server_publish_uri: 生成二维码时，使用的本地服务端 URI（需要郊狼用户能够连接）
    :ivar local_server_heartbeat_interval: 本地搭建的服务端心跳包发送间隔，为 ``None`` 关闭
    """
    remote_server: bool = False
    remote_server_uri: Optional[str] = None
    local_server_host: Optional[str] = "0.0.0.0"
    local_server_port: Optional[int] = 4567
    local_server_publish_uri: Optional[str] = "ws://192.168.1.162:4567"
    local_server_heartbeat_interval: Optional[float] = None

    @model_validator(mode="after")
    def validate_config(self):
        if self.remote_server:
            if not self.remote_server_uri:
                logger.error("启用了 remote_server，但没有配置 remote_server_uri")
                raise ValueError
        else:
            if not self.local_server_host or not self.local_server_port or not self.local_server_publish_uri:
                logger.error(
                    "未开启 remote_server，但没有配置 local_server_host, local_server_port, local_server_publish_uri")
                raise ValueError


class DGLabClientConfig(BaseModel):
    """
    DG-Lab 终端设置

    :ivar bind_timeout: 绑定超时时间（秒）
    :ivar register_timeout: 终端注册（获取 ``clientId``）超时时间（秒）
    """
    bind_timeout: float = 60
    register_timeout: float = 30


class PulseDataConfig(BaseModel):
    """
    郊狼波形数据设置

    DG-Lab App 波形队列最大长度为 50s，波形发送任务会先清空 App 波形队列，然后数次发送 最大为 ``duration_per_post`` 时长的波形，
    直到 App 队列无法继续放入。随后将会等待直到队列空出一段 最大为 ``duration_per_post`` 时长的空间，
    此时再发送一段 最大为 ``duration_per_post`` 时长的波形，然后再等待空间空出，再发送，如此循环。

    :ivar custom_pulse_data: 自定义波形的文件路径，\
        JSON 格式为 波形名称 -> 波形数据（``Array<Array<Number, Number, Number, Number>>``)
    :ivar duration_per_post: 每次发送的波形最大持续时长，建议小于 25s。即实际时长将会是 **设定的波形的时长** 的整数倍，倍数向下取整。\
        在此持续时间内，设定的波形会被重复播放
    :ivar post_interval: 波形发送间隔时间，应尽量小
    :ivar sleep_after_clear: 清除波形后的睡眠时间（避免由于网络波动等原因导致 清空队列指令晚于波形数据执行造成波形数据丢失 的情况）
    """
    custom_pulse_data: Path = DG_LAB_PLAY_DATA_LOCATION / "customPulseData.json"
    duration_per_post: float = 10
    post_interval: float = 1
    sleep_after_clear: float = 0.5


class CommandTextConfig(BaseModel):
    """命令触发文本设置"""
    append_pulse: str = "增加波形"
    current_pulse: str = "当前波形"
    current_strength: str = "当前力度"
    decrease_strength: str = "减小力度"
    dg_lab_device_join: str = "绑定郊狼"
    increase_strength: str = "加大力度"
    random_pulse: str = "随机波形"
    random_strength: str = "随机力度"
    reset_pulse: str = "重置波形"
    show_pulses: str = "可用波形"
    usage: str = "郊狼玩法"


class ReplyTextConfig(BaseModel):
    """命令响应文本设置"""
    bind_timeout: str = "绑定超时"
    failed_to_create_client: str = "创建 DG-Lab 控制终端失败"
    failed_to_fetch_strength_limit: str = "获取通道强度上限失败，控制失败"
    invalid_strength_param: str = "强度参数错误，控制失败"
    invalid_pulse_param: str = "波形参数错误，控制失败"
    invalid_target: str = "目标玩家不存在或郊狼 App 未绑定"
    please_at_target: str = "使用命令的同时请 @ 想要控制的玩家"
    please_scan_qrcode: str = "请用 DG-Lab App 扫描二维码以连接"
    successfully_bind: str = "绑定成功，可以开始色色了！"
    successfully_increased: str = "郊狼强度加强了 {}%！"
    successfully_decreased: str = "郊狼强度减小了 {}%"
    successfully_set_pulse: str = "郊狼波形成功设置为⌈{}⌋！"
    no_available_pulse: str = "无可用波形"


class DGLabPlayConfig(BaseModel):
    ws_server: WSServerConfig = WSServerConfig()
    dg_lab_client: DGLabClientConfig = DGLabClientConfig()
    pulse_data: PulseDataConfig = PulseDataConfig()
    command_text: CommandTextConfig = CommandTextConfig()
    reply_text: ReplyTextConfig = ReplyTextConfig()


class Config(BaseModel):
    dg_lab_play: DGLabPlayConfig = DGLabPlayConfig()


@driver.on_startup
async def create_data_directory():
    DG_LAB_PLAY_DATA_LOCATION.mkdir(parents=True)

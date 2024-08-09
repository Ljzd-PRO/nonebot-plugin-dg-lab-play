import ssl
from functools import cached_property
from pathlib import Path
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self

from loguru import logger
from nonebot import get_driver
from nonebot.config import BaseSettings
from pydantic import BaseModel, model_validator, field_validator
from pydantic_core import PydanticCustomError
from pydglab_ws import PULSE_DATA_MAX_LENGTH

__all__ = [
    "DG_LAB_PLAY_DATA_LOCATION",
    "WSServerConfig",
    "DGLabClientConfig",
    "PulseDataConfig",
    "CommandTextConfig",
    "ReplyTextConfig",
    "DGLabPlayConfig",
    "DicePlayConfig",
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
    :ivar local_server_secure: 是否启用 SSL 连接
    :ivar local_server_ssl_cert: SSL 证书文件路径
    :ivar local_server_ssl_key: SSL 私钥路径
    :ivar local_server_ssl_password: SSL 私钥密码
    """
    remote_server: bool = False
    remote_server_uri: Optional[str] = None
    local_server_host: Optional[str] = "0.0.0.0"
    local_server_port: Optional[int] = 4567
    local_server_publish_uri: Optional[str] = "ws://127.0.0.1:4567"
    local_server_heartbeat_interval: Optional[float] = None
    local_server_secure: bool = False
    local_server_ssl_cert: Optional[Path] = None
    local_server_ssl_key: Optional[Path] = None
    local_server_ssl_password: Optional[str] = None

    @cached_property
    def server_ssl_context(self) -> Optional[ssl.SSLContext]:
        if self.local_server_secure:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            try:
                context.load_cert_chain(
                    certfile=str(self.local_server_ssl_cert),
                    keyfile=str(self.local_server_ssl_key),
                    password=self.local_server_ssl_password
                )
                logger.success("已加载证书和私钥文件")
                return context
            except ssl.SSLError:
                logger.exception("私钥文件和证书文件不匹配")
                return None
        else:
            return None

    @model_validator(mode="after")
    def validate_config(self) -> "Self":
        if self.remote_server:
            if not self.remote_server_uri:
                logger.error("启用了 remote_server，但没有配置 remote_server_uri")
                raise PydanticCustomError
        else:
            if not self.local_server_host or not self.local_server_port or not self.local_server_publish_uri:
                logger.error(
                    "未使用远程服务端 remote_server，"
                    "但没有配置本地服务端的 local_server_host, local_server_port, local_server_publish_uri"
                )
                raise PydanticCustomError
            if self.local_server_secure:
                if self.local_server_ssl_cert and self.local_server_ssl_cert.is_file():
                    if self.local_server_ssl_password and (
                            not self.local_server_ssl_key or not self.local_server_ssl_key.is_file()
                    ):
                        logger.error(
                            "配置了 SSL 私钥密码 local_server_ssl_password，但没有指定私钥文件 local_server_ssl_key 或文件不存在")
                        raise PydanticCustomError
                else:
                    logger.error(
                        "启用了本地服务端安全连接 local_server_secure，但没有指定证书文件 local_server_ssl_cert 或文件不存在")
                    raise PydanticCustomError
        return self

    def validate_local_server_publish_uri(self) -> "Self":
        if (not self.remote_server and
                self.local_server_publish_uri == self.model_fields["local_server_publish_uri"].default):
            logger.warning(
                "未修改默认本地服务端的 local_server_publish_uri，DG-Lab App 将可能无法通过生成的二维码进行连接")
        return self


class DGLabClientConfig(BaseModel):
    """
    DG-Lab 终端设置

    :ivar bind_timeout: 绑定超时时间（秒）
    :ivar register_timeout: 终端注册（获取 ``clientId``）超时时间（秒）
    """
    bind_timeout: float = 90
    register_timeout: float = 30


class PulseDataConfig(BaseModel):
    """
    郊狼波形数据设置

    此处时间单位均为 秒。

    DG-Lab App 波形队列最大长度为 50s，波形发送任务会先清空 App 波形队列，然后数次发送 最大为 ``duration_per_post`` 时长的波形，
    直到 App 队列无法继续放入。随后将会等待直到队列空出一段 最大为 ``duration_per_post`` 时长的空间，
    此时再发送一段 最大为 ``duration_per_post`` 时长的波形，然后再等待空间空出，再发送，如此循环。

    :ivar custom_pulse_data: 自定义波形的文件路径，\
        JSON 格式为 波形名称 -> 波形数据（``Array<Array<Number, Number, Number, Number>>``)
    :ivar duration_per_post: 每次发送的波形最大持续时长，**必须小于等于 8.6**。实际时长将会是 **设定的波形的时长** 的整数倍，倍数向下取整。\
        在此持续时间内，设定的波形会被重复播放
    :ivar post_interval: 波形发送间隔时间，应尽量小
    :ivar sleep_after_clear: 清除波形后的睡眠时间（避免由于网络波动等原因导致 清空队列指令晚于波形数据执行造成波形数据丢失 的情况）
    """
    custom_pulse_data: Path = DG_LAB_PLAY_DATA_LOCATION / "customPulseData.json"
    duration_per_post: float = 8
    post_interval: float = 1
    sleep_after_clear: float = 0.5

    # noinspection PyNestedDecorators
    @field_validator("duration_per_post")
    @classmethod
    def validate_duration_per_post(cls, value: Any):
        if (isinstance(value, float) or isinstance(value, int)) and value > PULSE_DATA_MAX_LENGTH * 0.1:
            logger.error("PulseDataConfig.duration_per_post 大于每次发送的最大时长，消息过长将发送失败")
            raise PydanticCustomError
        else:
            return value


class DicePlayConfig(BaseModel):
    max_round: int = 10
    timeout: int = 30
    punish: int = 10.0


class CommandTextConfig(BaseModel):
    """命令触发文本设置"""
    append_pulse: str = "增加波形"
    current_pulse: str = "当前波形"
    current_strength: str = "当前强度"
    decrease_strength: str = "减小强度"
    dg_lab_device_join: str = "绑定郊狼"
    exit_game: str = "退出游戏"
    increase_strength: str = "加大强度"
    random_pulse: str = "随机波形"
    random_strength: str = "随机强度"
    reset_pulse: str = "重置波形"
    show_players: str = "当前玩家"
    show_pulses: str = "可用波形"
    usage: str = "郊狼玩法"
    start_dice: str = "开始骰子玩法"
    stop_dice: str = "停止骰子玩法"
    create_virtual_player: str = "创建虚拟玩家"


class ReplyTextConfig(BaseModel):
    """命令响应文本设置"""

    bind_timeout: str = "绑定超时"
    current_players: str = "当前玩家："
    current_pulse: str = "当前波形循环为：【{}】"
    current_strength: str = "A通道：{0}/{1} B通道：{2}/{3}"
    failed_to_create_client: str = "创建 DG-Lab 控制终端失败"
    failed_to_fetch_strength_info: str = "获取通道强度状态失败"
    failed_to_fetch_strength_limit: str = "获取通道强度上限失败，控制失败"
    game_exited: str = "已退出游戏"
    invalid_pulse_param: str = "波形参数错误，控制失败"
    invalid_strength_param: str = "强度参数错误，控制失败"
    invalid_target: str = "目标玩家不存在或郊狼 App 未绑定"
    no_available_pulse: str = "无可用波形"
    no_player: str = "当前没有已连接的玩家，你可以绑定试试~"
    not_bind_yet: str = "你目前没有绑定 DG-Lab App"
    please_at_target: str = "使用命令的同时请 @ 想要控制的玩家"
    please_scan_qrcode: str = "请用 DG-Lab App 扫描二维码以连接"
    please_set_pulse_first: str = "请先设置郊狼波形：{}"
    pulses_empty: str = "当前波形循环为空"
    successfully_bind: str = "绑定成功，可以开始色色了！"
    successfully_decreased: str = "郊狼强度减小了 {}%"
    successfully_increased: str = "郊狼强度加强了 {}%！"
    successfully_set_pulse: str = "郊狼波形成功设置为【{}】！"
    successfully_set_to_strength: str = "郊狼强度成功设置为 {}%！"

    dice_not_support: str = "本功能不支持当前平台，请换用OneBot协议适配器"
    dice_no_enough_players: str = "当前没有足够的玩家参与骰子玩法,至少需要两个玩家"
    dice_ready_start: str = "骰子玩法即将开始，游戏顺序如下："
    dice_already_started: str = "骰子玩法已经开始，不过现在仍可连接设备以加入游戏"
    dice_stopped: str = "骰子玩法已结束"
    dice_player_lost: str = "已失去连接"
    dice_require: str = "轮到你了，请在{second}秒内投掷骰子，否则本轮将判定为负"
    dice_round_start: str = "第({round}/{max_round})轮游戏开始"
    dice_timeout: str = "投掷超时，本轮判定为负"
    dice_defeat: str = "本轮结束，最低点数："
    dice_new_player: str = "新玩家加入，新游戏顺序如下："


class DebugConfig(BaseModel):
    """调试设置，使用 pydevd-pycharm 进行调试"""
    enable_debug: bool = False
    ide_host: str = "127.0.0.1"
    ide_port: int = 5678


class DGLabPlayConfig(BaseModel):
    ws_server: WSServerConfig = WSServerConfig()
    dg_lab_client: DGLabClientConfig = DGLabClientConfig()
    pulse_data: PulseDataConfig = PulseDataConfig()
    command_text: CommandTextConfig = CommandTextConfig()
    reply_text: ReplyTextConfig = ReplyTextConfig()
    debug: DebugConfig = DebugConfig()


class Config(BaseSettings):
    dg_lab_play: DGLabPlayConfig = DGLabPlayConfig()
    dice_play: DicePlayConfig = DicePlayConfig()


@driver.on_startup
async def create_data_directory():
    DG_LAB_PLAY_DATA_LOCATION.mkdir(parents=True, exist_ok=True)

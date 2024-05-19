from typing import Optional

from loguru import logger
from pydantic import BaseModel, model_validator


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


class CommandTextConfig(BaseModel):
    """命令触发文本设置"""
    dg_lab_device_join: str = "绑定郊狼"
    increase_strength: str = "加大力度"
    exit: str = "退出"


class ReplyTextConfig(BaseModel):
    """命令响应文本设置"""
    bind_timeout: str = "绑定超时"
    failed_to_create_client: str = "创建 DG-Lab 控制终端失败"
    failed_to_fetch_strength_limit: str = "获取通道强度上限失败，控制失败"
    invalid_strength_param: str = "强度参数错误，控制失败"
    invalid_target: str = "目标玩家不存在或郊狼 App 未绑定"
    please_at_target: str = "使用命令的同时请 @ 想要控制的玩家"
    please_scan_qrcode: str = "请用 DG-Lab App 扫描二维码以连接"
    successfully_bind: str = "绑定成功，可以开始色色了！"
    successfully_increased: str = "郊狼强度加强成功！"


class DGLabPlayConfig(BaseModel):
    ws_server: WSServerConfig = WSServerConfig()
    dg_lab_client: DGLabClientConfig = DGLabClientConfig()
    command_text: CommandTextConfig = CommandTextConfig()
    reply_text: ReplyTextConfig = ReplyTextConfig()


class Config(BaseModel):
    dg_lab_play: DGLabPlayConfig = DGLabPlayConfig()

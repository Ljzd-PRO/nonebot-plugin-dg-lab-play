from arclet.alconna import Args
from nonebot import get_plugin_config
from nonebot.internal.adapter import Event
from nonebot_plugin_alconna import on_alconna, Alconna, Match, At
from nonebot_plugin_saa import MessageFactory
from ..config import Config
from ..client_manager import client_manager
from ..utils import get_command_start_list

config = get_plugin_config(Config).dg_lab_play
__all__ = ["create_virtual_player", "VirtualPlayer"]


class VirtualPlayer:
    """
    虚拟玩家类
    警告：本类并不支持实际控制，只用于开发测试，调用DGLabPlayClient的特性会导致异常
    :param user_id: 虚拟玩家的QQ号
    :param group_id: 虚拟玩家所在的群号
    """

    def __init__(self, user_id: str, group_id: int = None):
        self.group_id = group_id
        self.user_id = user_id

    def set_group(self, group_id):
        self.group_id = group_id
        if group_id in client_manager.group_id_to_group:
            client_manager.group_id_to_group[group_id].append(self)
        else:
            client_manager.group_id_to_group[group_id] = [self]


create_virtual_player = on_alconna(
    Alconna(
        get_command_start_list(),
        config.command_text.create_virtual_player,
        Args["at?", At]
    ), block=True
)


@create_virtual_player.handle()
async def create_virtual_player(at: Match[At], event: Event):
    """
    使用VirtualPlayer类创建虚拟玩家
    默认用法：/创建虚拟玩家 @someone
    警告：仅做调试用途
    命令配置：create_virtual_player: str = "创建虚拟玩家"
    """
    target_user_id = at.result.target
    client_manager.user_id_to_client[target_user_id] = VirtualPlayer(target_user_id)
    client_manager.user_id_to_client[target_user_id].set_group(event.group_id)
    await MessageFactory(config.reply_text.successfully_bind).finish(at_sender=True)

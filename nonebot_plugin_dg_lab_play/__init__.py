from nonebot.plugin import PluginMetadata

from .commands import *
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="dg-lab-play",
    description="在群里和大家一起玩郊狼吧！",
    usage="",
    config=Config,
)

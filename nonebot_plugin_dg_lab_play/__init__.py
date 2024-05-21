from nonebot import require
from nonebot.plugin import PluginMetadata

from .commands import *
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="DG-Lab-Play",
    description="在群里和大家一起玩郊狼吧！",
    usage=USAGE_TEXT,
    type="application",
    homepage="https://github.com/Ljzd-PRO/nonebot-plugin-dg-lab-play",
    config=Config,
)

require("nonebot_plugin_saa")
# noinspection SpellCheckingInspection
require("nonebot_plugin_alconna")

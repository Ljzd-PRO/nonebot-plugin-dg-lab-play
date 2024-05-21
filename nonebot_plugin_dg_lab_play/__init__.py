from nonebot import require
from nonebot.plugin import PluginMetadata, get_plugin_config

require("nonebot_plugin_saa")
# noinspection SpellCheckingInspection
require("nonebot_plugin_alconna")

# import pydevd_pycharm
# pydevd_pycharm.settrace("127.0.0.1", port=5678, stdoutToServer=True, stderrToServer=True)

from .commands import *
from .config import Config

config = get_plugin_config(Config).dg_lab_play
if config.debug.enable_debug:
    import pydevd_pycharm

    pydevd_pycharm.settrace(config.debug.ide_host, port=config.debug.ide_port, stdoutToServer=True, stderrToServer=True)

__plugin_meta__ = PluginMetadata(
    name="DG-Lab-Play",
    description="在群里和大家一起玩郊狼吧！",
    usage=USAGE_TEXT,
    type="application",
    homepage="https://github.com/Ljzd-PRO/nonebot-plugin-dg-lab-play",
    config=Config,
)

# 检查 local_server_publish_uri 是否直接使用了默认值
config.ws_server.validate_local_server_publish_uri()

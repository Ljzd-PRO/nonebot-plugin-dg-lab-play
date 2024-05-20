from arclet.alconna import Alconna
from nonebot.plugin import get_plugin_config
from nonebot_plugin_alconna import on_alconna
from nonebot_plugin_saa import MessageFactory

from ..config import Config
from ..model import custom_pulse_data
from ..utils import get_command_start_list

__all__ = ["show_pulses"]

config = get_plugin_config(Config).dg_lab_play

show_pulses = on_alconna(
    Alconna(get_command_start_list(), config.command_text.show_pulses),
    block=True
)


@show_pulses.handle()
async def handle_show_pulses():
    if custom_pulse_data.root:
        await MessageFactory(
            "、".join(custom_pulse_data.root.keys())
        ).finish(at_sender=True)
    else:
        await MessageFactory(
            config.reply_text.no_available_pulse
        ).finish(at_sender=True)

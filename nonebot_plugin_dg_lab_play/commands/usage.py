from arclet.alconna import Alconna
from nonebot.plugin import get_plugin_config
from nonebot_plugin_alconna import on_alconna
from nonebot_plugin_saa import MessageFactory

from ..config import Config
from ..utils import get_command_start_list

__all__ = ["USAGE_TEXT", "usage"]

config = get_plugin_config(Config).dg_lab_play

fist_command_start = get_command_start_list()[0]

USAGE_TEXT = f"""\
⚡ DG-Lab-Play 郊狼玩法说明 ⚡

📲连接 DG-Lab App：{fist_command_start}{config.command_text.dg_lab_device_join}
🕹️查看当前玩家：{fist_command_start}{config.command_text.show_players}
🚪退出游戏：{fist_command_start}{config.command_text.exit_game}

🔺增加玩家通道强度：{fist_command_start}{config.command_text.increase_strength} <At用户> <百分比>
🔻减小玩家通道强度：{fist_command_start}{config.command_text.decrease_strength} <At用户> <百分比>
🎚️查看当前通道强度：{fist_command_start}{config.command_text.current_strength} <At用户>
🎲随机通道强度：{fist_command_start}{config.command_text.random_strength} <At用户>

🏷️列出可用波形：{fist_command_start}{config.command_text.show_pulses}
⤴️添加波形到循环：{fist_command_start}{config.command_text.append_pulse} <At用户> <波形名称>
🔄️重设为某波形：{fist_command_start}{config.command_text.reset_pulse} <At用户> <波形名称>
📈显示当前波形：{fist_command_start}{config.command_text.current_pulse} <At用户>
🎲重设为随机波形：{fist_command_start}{config.command_text.random_pulse} <At用户>

🎲开始骰子玩法：{fist_command_start}{config.command_text.start_dice}
🚪停止骰子玩法：{fist_command_start}{config.command_text.stop_dice}
注：骰子玩法至少需要两个玩家

🔗项目链接：https://github.com/Ljzd-PRO/nonebot-plugin-dg-lab-play
"""

usage = on_alconna(
    Alconna(get_command_start_list(), config.command_text.usage),
    block=True
)


@usage.handle()
async def handle_usage():
    await MessageFactory(
        USAGE_TEXT
    ).finish(at_sender=True)

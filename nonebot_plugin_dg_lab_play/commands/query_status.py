from arclet.alconna import Alconna, Args
from nonebot.plugin import get_plugin_config
from nonebot_plugin_alconna import on_alconna, At, Match
from nonebot_plugin_saa import MessageFactory

from ..client_manager import client_manager
from ..config import Config
from ..utils import get_command_start_list

__all__ = ["current_strength", "current_pulse"]

config = get_plugin_config(Config).dg_lab_play

current_strength = on_alconna(
    Alconna(
        get_command_start_list(),
        config.command_text.current_strength,
        Args["at?", At]
    ),
    block=True
)


@current_strength.handle()
async def handle_current_strength(at: Match[At]):
    if not at.available:
        await MessageFactory(
            config.reply_text.please_at_target
        ).finish(at_sender=True)
    target_user_id = at.result.target
    if play_client := client_manager.user_id_to_client.get(target_user_id):
        if play_client.last_strength:
            await MessageFactory(
                config.reply_text.current_strength.format(
                    play_client.last_strength.a,
                    play_client.last_strength.a_limit,
                    play_client.last_strength.b,
                    play_client.last_strength.b_limit,
                )
            ).finish(at_sender=True)
        else:
            await MessageFactory(
                config.reply_text.failed_to_fetch_strength_info
            ).finish(at_sender=True)
    else:
        await MessageFactory(
            config.reply_text.invalid_target
        ).finish(at_sender=True)


current_pulse = on_alconna(
    Alconna(
        get_command_start_list(),
        config.command_text.current_pulse,
        Args["at?", At]
    ),
    block=True
)


@current_pulse.handle()
async def handle_current_pulse(at: Match[At]):
    if not at.available:
        await MessageFactory(
            config.reply_text.please_at_target
        ).finish(at_sender=True)
    target_user_id = at.result.target
    if play_client := client_manager.user_id_to_client.get(target_user_id):
        if play_client.pulse_names:
            await MessageFactory(
                config.reply_text.current_pulse.format(
                    "-".join(play_client.pulse_names)
                )
            ).finish(at_sender=True)
        else:
            await MessageFactory(
                config.reply_text.pulses_empty
            ).finish(at_sender=True)
    else:
        await MessageFactory(
            config.reply_text.invalid_target
        ).finish(at_sender=True)

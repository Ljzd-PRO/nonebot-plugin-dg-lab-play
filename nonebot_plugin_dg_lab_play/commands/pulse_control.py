import random
from typing import Literal

from arclet.alconna import Alconna, Args
from loguru import logger
from nonebot.plugin import get_plugin_config
from nonebot_plugin_alconna import on_alconna, At, Match
from nonebot_plugin_saa import MessageFactory
from pydglab_ws import Channel

from ..client_manager import client_manager
from ..config import Config
from ..model import custom_pulse_data
from ..utils import get_command_start_list

__all__ = ["append_pulse", "reset_pulse", "random_pulse"]

config = get_plugin_config(Config).dg_lab_play


async def pulse_control(
        mode: Literal["reset", "append"],
        at: Match[At],
        pulse_name: Match[str]
):
    if not at.available:
        await MessageFactory(
            config.reply_text.please_at_target
        ).finish(at_sender=True)
    elif pulse_name.available:
        if pulse_data := custom_pulse_data.root.get(pulse_name.result):
            target_user_id = at.result.target
            if play_client := client_manager.user_id_to_client.get(target_user_id):
                if mode == "reset":
                    play_client.setup_pulse_job([pulse_name.result], pulse_data, Channel.A, Channel.B)
                elif mode == "append":
                    play_client.setup_pulse_job(
                        play_client.pulse_names + [pulse_name.result],
                        play_client.pulse_data + pulse_data,
                        Channel.A,
                        Channel.B
                    )
                else:
                    logger.error("strength_control - mode 参数不正确")
                    return
                await MessageFactory(
                    config.reply_text.successfully_set_pulse.format(
                        "-".join(play_client.pulse_names)
                    )
                ).finish(at_sender=True)
            else:
                await MessageFactory(
                    config.reply_text.invalid_target
                ).finish(at_sender=True)
        else:
            await MessageFactory(
                config.reply_text.invalid_pulse_param
            ).finish(at_sender=True)
    else:
        await MessageFactory(
            config.reply_text.invalid_pulse_param
        ).finish(at_sender=True)


append_pulse = on_alconna(
    Alconna(
        get_command_start_list(),
        config.command_text.append_pulse,
        Args["at?", At],
        Args["pulse_name?", str]
    ),
    block=True
)


@append_pulse.handle()
async def handle_append_pulse(at: Match[At], pulse_name: Match[str]):
    await pulse_control("append", at, pulse_name)


reset_pulse = on_alconna(
    Alconna(
        get_command_start_list(),
        config.command_text.reset_pulse,
        Args["at?", At],
        Args["pulse_name?", str]
    ),
    block=True
)


@reset_pulse.handle()
async def handle_reset_pulse(at: Match[At], pulse_name: Match[str]):
    await pulse_control("reset", at, pulse_name)


random_pulse = on_alconna(
    Alconna(
        get_command_start_list(),
        config.command_text.random_pulse,
        Args["at?", At]
    ),
    block=True
)


@random_pulse.handle()
async def handle_random_pulse(at: Match[At]):
    available_pulse_names = list(custom_pulse_data.root.keys())
    if not available_pulse_names:
        await MessageFactory(
            config.reply_text.no_available_pulse
        ).finish(at_sender=True)
    pulse_name_index = random.randint(0, len(available_pulse_names) - 1)
    pulse_name = available_pulse_names[pulse_name_index]
    await pulse_control("reset", at, Match(pulse_name, True))

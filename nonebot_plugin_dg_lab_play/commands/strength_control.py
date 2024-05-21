import random

from arclet.alconna import Alconna, Args
from loguru import logger
from nonebot.plugin import get_plugin_config
from nonebot_plugin_alconna import on_alconna, At, Match
from nonebot_plugin_saa import MessageFactory
from pydglab_ws import Channel, StrengthOperationType

from ..client_manager import client_manager
from ..config import Config
from ..utils import get_command_start_list

__all__ = ["increase_strength", "decrease_strength", "random_strength"]

config = get_plugin_config(Config).dg_lab_play


async def strength_control(
        mode: StrengthOperationType,
        at: Match[At],
        percentage_value: Match[float]
):
    if not at.available:
        await MessageFactory(
            config.reply_text.please_at_target
        ).finish(at_sender=True)
    elif not percentage_value.available or not 0 < percentage_value.result <= 100:
        await MessageFactory(
            config.reply_text.invalid_strength_param
        ).finish(at_sender=True)
    target_user_id = at.result.target
    if play_client := client_manager.user_id_to_client.get(target_user_id):
        if not play_client.pulse_data:
            await MessageFactory(
                config.reply_text.please_set_pulse_first.format(
                    f"{get_command_start_list()[0]}{config.command_text.random_pulse}"
                )
            ).finish(at_sender=True)
        elif play_client.last_strength:
            a_value = round(play_client.last_strength.a_limit * (percentage_value.result / 100))
            b_value = round(play_client.last_strength.b_limit * (percentage_value.result / 100))
            await play_client.client.set_strength(
                Channel.A,
                mode,
                a_value
            )
            await play_client.client.set_strength(
                Channel.B,
                mode,
                b_value
            )
            if mode == StrengthOperationType.INCREASE:
                success_text = config.reply_text.successfully_increased.format(round(percentage_value.result))
            elif mode == StrengthOperationType.DECREASE:
                success_text = config.reply_text.successfully_decreased.format(round(percentage_value.result))
            elif mode == StrengthOperationType.SET_TO:
                success_text = config.reply_text.successfully_set_to_strength.format(round(percentage_value.result))
            else:
                logger.error("strength_control - mode 参数不正确")
                return
            await MessageFactory(success_text).finish(at_sender=True)
        else:
            await MessageFactory(
                config.reply_text.failed_to_fetch_strength_limit
            ).finish(at_sender=True)
    else:
        await MessageFactory(
            config.reply_text.invalid_target
        ).finish(at_sender=True)


increase_strength = on_alconna(
    Alconna(
        get_command_start_list(),
        config.command_text.increase_strength,
        Args["at?", At],
        Args["percentage_value?", float]
    ),
    block=True
)


@increase_strength.handle()
async def handle_increase_strength(at: Match[At], percentage_value: Match[float]):
    await strength_control(StrengthOperationType.INCREASE, at, percentage_value)


decrease_strength = on_alconna(
    Alconna(
        get_command_start_list(),
        config.command_text.decrease_strength,
        Args["at?", At],
        Args["percentage_value?", float]
    ),
    block=True
)


@decrease_strength.handle()
async def handle_decrease_strength(at: Match[At], percentage_value: Match[float]):
    await strength_control(StrengthOperationType.DECREASE, at, percentage_value)


random_strength = on_alconna(
    Alconna(
        get_command_start_list(),
        config.command_text.random_strength,
        Args["at?", At]
    ),
    block=True
)


@random_strength.handle()
async def handle_random_strength(at: Match[At]):
    random_strength_value = float(random.randint(0, 100))
    await strength_control(
        StrengthOperationType.SET_TO,
        at,
        Match(random_strength_value, True)
    )

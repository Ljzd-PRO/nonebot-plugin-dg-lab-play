from arclet.alconna import Alconna, Args
from nonebot.plugin import get_plugin_config
from nonebot_plugin_alconna import on_alconna, At, Match
from nonebot_plugin_saa import MessageFactory
from pydglab_ws import Channel, StrengthOperationType

from ..client_manager import client_manager
from ..config import Config

__all__ = ["increase_strength"]

config = get_plugin_config(Config)


async def strength_control(
        mode: StrengthOperationType,
        at: Match[At],
        percentage_value: Match[float]
):
    if not at.available:
        await MessageFactory(
            config.dg_lab_play.reply_text.please_at_target
        ).finish(at_sender=True)
    elif not percentage_value.available or not 0 < percentage_value.result <= 100:
        await MessageFactory(
            config.dg_lab_play.reply_text.invalid_strength_param
        ).finish(at_sender=True)
    target_user_id = at.result.target
    if play_client := client_manager.user_id_to_client.get(target_user_id):
        if play_client.last_strength:
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
            await MessageFactory(
                config.dg_lab_play.reply_text.successfully_increased if mode == StrengthOperationType.INCREASE
                else config.dg_lab_play.reply_text.successfully_decreased
            ).finish(at_sender=True)
        else:
            await MessageFactory(
                config.dg_lab_play.reply_text.failed_to_fetch_strength_limit
            ).finish(at_sender=True)
    else:
        await MessageFactory(
            config.dg_lab_play.reply_text.invalid_target
        ).finish(at_sender=True)


increase_strength = on_alconna(
    Alconna(
        config.dg_lab_play.command_text.increase_strength,
        Args["at?", At],
        Args["percentage_value?", float]
    ),
    block=True
)


@increase_strength.handle()
async def _(at: Match[At], percentage_value: Match[float]):
    await strength_control(StrengthOperationType.INCREASE, at, percentage_value)


decrease_strength = on_alconna(
    Alconna(
        config.dg_lab_play.command_text.decrease_strength,
        Args["at?", At],
        Args["percentage_value?", float]
    ),
    block=True
)


@decrease_strength.handle()
async def __(at: Match[At], percentage_value: Match[float]):
    await strength_control(StrengthOperationType.DECREASE, at, percentage_value)

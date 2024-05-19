from typing import Annotated

from nonebot.params import CommandArg
from nonebot.plugin import on_command, get_plugin_config
from nonebot_plugin_saa import MessageFactory, Text, Mention
from pydglab_ws import Channel, StrengthOperationType

from ..client_manager import client_manager
from ..config import Config

__all__ = ["increase_strength"]

config = get_plugin_config(Config)

increase_strength = on_command(
    config.dg_lab_play.command_text.increase_strength[0],
    aliases=config.dg_lab_play.command_text.increase_strength[1],
    block=True
)


@increase_strength.handle()
async def handle_function(arg: Annotated[MessageFactory, CommandArg()]):
    if mention_msg := arg[Mention]:
        target_user_ids = map(lambda x: x.data.user_id, mention_msg)
        if text_msg := arg[Text]:
            channel_strength = str(text_msg).split()
            try:
                if len(channel_strength) == 1:
                    channel, strength = Channel, int(channel_strength[0])
                else:
                    channel, strength = [Channel[channel_strength[0].upper()]], int(channel_strength[1])
            except (ValueError, KeyError):
                await MessageFactory(
                    config.dg_lab_play.reply_text.invalid_strength_param
                ).finish(at_sender=True)
            else:
                for user_id in target_user_ids:
                    if play_client := client_manager.user_id_to_client.get(user_id):
                        for target_channel in channel:
                            await play_client.client.set_strength(
                                target_channel,
                                StrengthOperationType.INCREASE,
                                strength
                            )
                    else:
                        await MessageFactory(
                            config.dg_lab_play.reply_text.invalid_target
                        ).finish(at_sender=True)
                await MessageFactory(
                    config.dg_lab_play.reply_text.successfully_increased
                ).finish(at_sender=True)
        else:
            await MessageFactory(
                config.dg_lab_play.reply_text.invalid_strength_param
            ).finish(at_sender=True)
    else:
        await MessageFactory(
            config.dg_lab_play.reply_text.please_at_target
        ).finish(at_sender=True)

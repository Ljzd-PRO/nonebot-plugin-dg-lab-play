import io

import qrcode
from arclet.alconna import Alconna
from nonebot.internal.adapter import Event
from nonebot.plugin import get_plugin_config
from nonebot_plugin_alconna import on_alconna
from nonebot_plugin_saa import MessageFactory, Image, Text, Mention

from ..client_manager import client_manager
from ..config import Config
from ..utils import get_command_start_list, is_onebot_group

__all__ = ["dg_lab_device_join", "show_players", "exit_game"]

config = get_plugin_config(Config).dg_lab_play

dg_lab_device_join = on_alconna(
    Alconna(get_command_start_list(), config.command_text.dg_lab_device_join),
    block=True
)


@dg_lab_device_join.handle()
async def handle_dg_lab_device_join(event: Event):
    play_client = client_manager.user_id_to_client.get(event.get_user_id()) or await client_manager.new_client(
        event.get_user_id()
    )
    if not play_client:
        await MessageFactory(
            config.reply_text.failed_to_create_client
        ).finish(at_sender=True)
    qrcode_data = play_client.qrcode
    qrcode_img_bytes_io = io.BytesIO()
    qrcode.make(qrcode_data).save(qrcode_img_bytes_io, "JPEG")
    msg_builder = MessageFactory([
        Image(qrcode_img_bytes_io),
        Text(config.reply_text.please_scan_qrcode)
    ])
    await msg_builder.send(at_sender=True)
    async with play_client.bind_finished_lock:
        pass
    if not play_client.is_destroyed:
        if is_onebot_group(event):
            play_client.set_group(event.group_id)
        await MessageFactory(
            config.reply_text.successfully_bind
        ).finish(at_sender=True)
    else:
        await MessageFactory(
            config.reply_text.bind_timeout
        ).finish(at_sender=True)


show_players = on_alconna(
    Alconna(get_command_start_list(), config.command_text.show_players),
    block=True
)


@show_players.handle()
async def handle_show_players():
    if client_manager.user_id_to_client:
        await MessageFactory(
            [config.reply_text.current_players]
            + [Mention(user_id) for user_id in client_manager.user_id_to_client.keys()]
        ).finish(at_sender=True)
    else:
        await MessageFactory(
            config.reply_text.no_player
        ).finish(at_sender=True)


exit_game = on_alconna(
    Alconna(get_command_start_list(), config.command_text.exit_game),
    block=True
)


@exit_game.handle()
async def handle_exit_game(event: Event):
    if play_client := client_manager.user_id_to_client.get(event.get_user_id()):
        await play_client.destroy()
        await MessageFactory(
            config.reply_text.game_exited
        ).finish(at_sender=True)
    else:
        await MessageFactory(
            config.reply_text.not_bind_yet
        ).finish(at_sender=True)

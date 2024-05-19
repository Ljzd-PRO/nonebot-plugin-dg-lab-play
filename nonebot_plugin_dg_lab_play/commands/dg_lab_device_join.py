import io

import qrcode
from arclet.alconna import Alconna
from nonebot.internal.adapter import Event
from nonebot.plugin import get_plugin_config
from nonebot_plugin_alconna import on_alconna
from nonebot_plugin_saa import MessageFactory, Image, Text

from ..client_manager import client_manager
from ..config import Config

__all__ = ["dg_lab_device_join"]

config = get_plugin_config(Config)

dg_lab_device_join = on_alconna(
    Alconna(config.dg_lab_play.command_text.dg_lab_device_join),
    block=True
)


@dg_lab_device_join.handle()
async def handle_function(event: Event):
    play_client = client_manager.user_id_to_client.get(event.get_user_id()) or await client_manager.new_client(
        event.get_user_id()
    )
    if not play_client:
        await MessageFactory(
            config.dg_lab_play.reply_text.failed_to_create_client
        ).finish(at_sender=True)
    qrcode_data = play_client.qrcode
    qrcode_img_bytes_io = io.BytesIO()
    qrcode.make(qrcode_data).save(qrcode_img_bytes_io, "JPEG")
    msg_builder = MessageFactory([
        Image(qrcode_img_bytes_io),
        Text(config.dg_lab_play.reply_text.please_scan_qrcode)
    ])
    await msg_builder.send(at_sender=True)
    async with play_client.bind_finished_lock:
        pass
    if not play_client.is_destroyed:
        await MessageFactory(
            config.dg_lab_play.reply_text.successfully_bind
        ).finish(at_sender=True)
    else:
        await MessageFactory(
            config.dg_lab_play.reply_text.bind_timeout
        ).finish(at_sender=True)

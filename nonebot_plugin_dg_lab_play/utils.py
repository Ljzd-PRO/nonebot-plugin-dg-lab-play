import ssl
from typing import List

import nonebot

__all__ = ["get_command_start_list", "get_client_ssl_context"]

nonebot_config = nonebot.get_driver().config


def get_command_start_list() -> List[str]:
    return list(nonebot_config.command_start)


def get_client_ssl_context() -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_default_certs(ssl.Purpose.CLIENT_AUTH)
    return context

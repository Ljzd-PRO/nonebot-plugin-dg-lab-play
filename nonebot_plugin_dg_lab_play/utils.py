from typing import List

import nonebot
from nonebot.internal.adapter import Event

__all__ = ["get_command_start_list", "is_onebot_group"]

nonebot_config = nonebot.get_driver().config


def get_command_start_list() -> List[str]:
    return list(nonebot_config.command_start)


def is_onebot_group(event: Event) -> bool:
    # 判断Event是不是一个QQ群消息
    return event.__class__.__module__.startswith("nonebot.adapters.onebot") and event.message_type == 'group'


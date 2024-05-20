from typing import List

import nonebot

__all__ = ["get_command_start_list"]

nonebot_config = nonebot.get_driver().config


def get_command_start_list() -> List[str]:
    return list(nonebot_config.command_start)

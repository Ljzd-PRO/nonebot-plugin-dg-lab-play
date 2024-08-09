import asyncio
import random
from typing import Dict, List

from nonebot import on_message
from nonebot.internal.adapter import Event
from nonebot.plugin import get_plugin_config
from nonebot_plugin_alconna import on_alconna, Alconna
from nonebot_plugin_saa import MessageFactory, Text, Mention
from pydglab_ws import StrengthOperationType, Channel

from .virtual import VirtualPlayer
from ..client_manager import client_manager, DGLabPlayClient
from ..config import Config
from ..model import custom_pulse_data
from ..utils import get_command_start_list
from ..utils import is_onebot_group

__all__ = ["start_dice_play", "stop_dice_play", "on_dices"]
config = get_plugin_config(Config).dg_lab_play
dice_config = get_plugin_config(Config).dice_play


class Dice:
    """
    骰子类，用于存储骰子点数
    :param user_id: 投掷骰子的玩家QQ号
    :param dice_point: 骰子点数
    """

    def __init__(self, user_id: str, dice_point: int):
        self.user_id = user_id
        self.dice_point = dice_point
        self.player = None

    def __lt__(self, other):
        return self.dice_point < other.dice_point


class DiceProcessManager:
    def __init__(self, group_id: str):
        self.group_id = group_id
        self.players: List[DGLabPlayClient] = client_manager.group_id_to_group.get(group_id)
        random.shuffle(self.players)

        self.round = 1  # 游戏当前轮数，可修改DicePlayConfig.max_round
        self.task = None  # 存储处理游戏逻辑的asyncio任务
        self.dice_buffer: List[Dice] = []  # 骰子缓冲区，存储已记录的骰子
        self.dice_receive_event = asyncio.Event()  # 这个事件表明骰子处理Handler是否已接收到骰子
        self.dice_checked_event = asyncio.Event()  # 这个事件表明游戏逻辑任务是否空闲以处理骰子
        self.dice_checked_event.set()  # 当然，默认空闲
        processing_dice_play[group_id] = self  # 加入进行中的游戏列表

    async def start(self):
        """
        开始骰子游戏
        """
        if self.task is not None:
            await MessageFactory(config.reply_text.dice_already_started).finish(at_sender=True)
            return
        else:
            mentions = [Mention(user_id=player.user_id) for player in self.players]
            await MessageFactory(Text(config.reply_text.dice_ready_start) + mentions).send()
            self.task = asyncio.create_task(self.__game())
            return

    async def stop(self):
        """
        停止骰子游戏
        """
        if self.task is not None:
            self.task.cancel()
        await MessageFactory(config.reply_text.dice_stopped).finish(at_sender=True)

    async def __game(self):
        while self.round <= dice_config.max_round:
            if len(self.players) < 2 or len(client_manager.group_id_to_group.get(self.group_id) or []) < 2:
                # 检查是否有足够的玩家
                break
            for player in client_manager.group_id_to_group.get(self.group_id):
                # 检查是否有新加入玩家
                if player not in self.players:
                    self.players = client_manager.group_id_to_group.get(self.group_id)
                    random.shuffle(self.players)
                    mentions = [Mention(user_id=player.user_id) for player in self.players]
                    await MessageFactory(Text(config.reply_text.dice_new_player) + mentions).send()
                    break

            self.dice_buffer.clear()
            await asyncio.sleep(1)
            await MessageFactory(
                config.reply_text.dice_round_start.format(round=self.round, max_round=dice_config.max_round)).send()
            await asyncio.sleep(1)

            for player in self.players:
                if client_manager.user_id_to_client.get(player.user_id) is None:
                    # 检查玩家是否存活
                    self.players.pop(self.players.index(player))
                    await MessageFactory(Mention(player.user_id) + Text(config.reply_text.dice_player_lost)).send()
                    await asyncio.sleep(1)
                    continue  # 跳过已失去连接的玩家，重新进入for循环
                try:
                    # 等待骰子
                    await asyncio.wait_for(self.__wait_dice(player), timeout=dice_config.timeout)
                except asyncio.TimeoutError:
                    # 超时则判定本轮为负， 本轮结束
                    await MessageFactory(Mention(player.user_id) + Text(config.reply_text.dice_timeout)).send()
                    self.dice_buffer.append(Dice(player.user_id, 0))
                    self.dice_buffer[-1].player = player
                    break  # 结束本轮的for循环

            self.dice_buffer.sort()
            await MessageFactory(Text(config.reply_text.dice_defeat) + Mention(self.dice_buffer[0].user_id)).send()
            await asyncio.sleep(1)
            await self.__punish(self.dice_buffer[0].player)
        del processing_dice_play[self.group_id]
        await MessageFactory(config.reply_text.dice_stopped).send()

    async def __punish(self, player: DGLabPlayClient):
        if isinstance(player, VirtualPlayer):
            await MessageFactory(Mention(player.user_id) + Text("是一个虚拟玩家")).send()
        elif client_manager.user_id_to_client.get(player.user_id) is None:
            await MessageFactory(Mention(player.user_id) + Text(config.reply_text.dice_player_lost)).send()
        else:
            available_pulse_names = list(custom_pulse_data.root.keys())
            if not available_pulse_names:
                await MessageFactory(
                    config.reply_text.no_available_pulse
                ).finish()
                return
            pulse_name_index = random.randint(0, len(available_pulse_names) - 1)
            pulse_name = available_pulse_names[pulse_name_index]
            pulse_data = custom_pulse_data.root.get(pulse_name)
            await player.setup_pulse_job([pulse_name], pulse_data, Channel.A, Channel.B)
            await player.client.set_strength(Channel.A, StrengthOperationType.INCREASE, dice_config.punish)
            await player.client.set_strength(Channel.B, StrengthOperationType.INCREASE, dice_config.punish)
        self.round += 1

    async def __wait_dice(self, player: DGLabPlayClient):
        await MessageFactory(
            Text(config.reply_text.dice_require.format(second=dice_config.timeout)) + Mention(player.user_id)).send()
        while True:
            await self.dice_receive_event.wait()  # 等待骰子处理Handler将骰子放入缓冲区
            self.dice_receive_event.clear()  # 标记处理器已收到
            self.dice_checked_event.clear()  # 标记处理器正忙

            if self.dice_buffer[-1].user_id != player.user_id:  # 非本轮玩家投出的骰子
                self.dice_buffer.pop(-1)
                self.dice_checked_event.set()
            else:
                self.dice_buffer[-1].player = player
                self.dice_checked_event.set()  # 标记处理器空闲
                return


processing_dice_play: Dict[str, DiceProcessManager] = {}

start_dice_play = on_alconna(
    Alconna(
        get_command_start_list(),
        config.command_text.start_dice), block=True
)


@start_dice_play.handle()
async def handle_start_dice_play(event: Event):
    """
    开始骰子游戏
    命令配置：start_dice: str = "开始骰子玩法"
    """
    if not is_onebot_group(event):
        # 判断来源是不是QQ群
        await MessageFactory(config.reply_text.dice_not_support).finish(at_sender=True)
        return
    if len(client_manager.group_id_to_group.get(event.group_id) or []) < 2:
        # 判断是否有足够的玩家
        await MessageFactory(config.reply_text.dice_no_enough_players).finish(at_sender=True)
        return
    processing = processing_dice_play.get(event.group_id) or DiceProcessManager(event.group_id)
    await processing.start()


stop_dice_play = on_alconna(
    Alconna(
        get_command_start_list(),
        config.command_text.stop_dice), block=True
)


@stop_dice_play.handle()
async def handle_stop_dice_play(event: Event):
    """
    停止骰子游戏
    命令配置：stop_dice: str = "停止骰子玩法"
    """
    if not is_onebot_group(event):
        # 判断来源是不是QQ群
        MessageFactory(config.reply_text.dice_not_support).finish(at_sender=True)
        return
    processing = processing_dice_play.get(event.group_id)
    if processing is not None:
        del processing_dice_play[processing.group_id]
        await processing.stop()


on_dices = on_message()


@on_dices.handle()
async def handle_dices(event: Event):
    """
    处理骰子的投掷事件
    Note:Alconna无法处理骰子事件，因此使用on_message
    """
    if not is_onebot_group(event) or event.message[0].type != 'dice':
        return
    processing = processing_dice_play.get(event.group_id)
    if processing is not None:
        await processing.dice_checked_event.wait()
        point = int(event.message[0].data['result'])
        processing.dice_buffer.append(Dice(event.get_user_id(), point))
        processing.dice_receive_event.set()

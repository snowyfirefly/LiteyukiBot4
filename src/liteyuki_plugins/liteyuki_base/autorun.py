import time
import uuid

from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.exception import IgnoredException
from nonebot.internal.matcher import Matcher
from nonebot.message import run_preprocessor, event_preprocessor
from nonebot import get_driver, get_bots
from nonebot import get_bot
from nonebot.typing import T_State

from ...liteyuki_api.data import *

driver = get_driver()


# 保存启动时间
@driver.on_startup
async def _():
    Data(Data.globals, "liteyuki").set_data("start_time", list(time.localtime())[0:6])
    if Data(Data.globals, "liteyuki").get_data("liteyuki_id") is None:
        Data(Data.globals, "liteyuki").set_data("liteyuki_id", str(uuid.uuid4()))


@driver.on_bot_connect
async def _(bot: Bot):
    for superuser_id in bot.config.superusers:
        await bot.send_private_msg(user_id=int(superuser_id), message=f"LiteyukiBot:{bot.self_id}已连接")


@run_preprocessor
async def _(matcher: Matcher, event: Union[GroupMessageEvent]):
    white_list = [
        "liteyuki_base"
    ]
    if matcher.plugin_name not in white_list:
        if Data(Data.groups, event.group_id).get_data("enable", True):
            pass
        else:
            raise IgnoredException("会话未启用Bot")
    else:
        pass


@run_preprocessor
async def _(event: MessageEvent):
    banned_user_list = Data(Data.globals, "liteyuki").get_data("banned_users", [])
    if event.user_id in banned_user_list:
        raise IgnoredException("用户已被屏蔽")

from typing import Tuple

from nonebot.internal.rule import Rule

from ...liteyuki_api.utils import Command

weather_lang_names = ("天气", "weather", "天気", "날씨")

def format_location_show_name(level_list: list) -> str:
    """
    格式化可读地名，例如：["中国", "北京市", "北京", "北京"] -> "中国 北京市 北京"

    :param level_list: 行政区列表
    :return: 格式化后的名字
    """
    new_list = []
    for loc in level_list:
        if loc not in new_list:
            new_list.append(loc)
    return " ".join(new_list)


def format_location_show_name_2(level_list: list) -> Tuple[str, str]:
    """
    天气卡片专用版1

    :param level_list:
    :return:
    """
    new_list = level_list
    for loc in level_list:
        if loc not in new_list:
            new_list.append(loc)
    return " ".join(new_list[0:-1]), new_list[-1]


@Rule
async def WEATHER_NOW(bot, event, state):
    args, kwargs = Command.formatToCommand(str(event.message))
    args = " ".join(args)
    if args.endswith(("逐天天气", "小时天气")):
        return False
    else:
        if args.endswith(weather_lang_names):
            return True
        else:
            return False

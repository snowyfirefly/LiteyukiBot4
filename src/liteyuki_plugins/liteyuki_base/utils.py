from nonebot import require

from ...liteyuki_api.canvas import Color
from ...liteyuki_api.reloader import Reloader


# 可选参数 5秒后触发重启


def restart_bot():
    Reloader.reload()


def get_usage_percent_color(percent):
    if percent < 40:
        arc_color = (0, 255, 0, 255)
    elif percent < 60:
        arc_color = (255, 255, 255, 255)
    elif percent < 80:
        arc_color = arc_color = Color.hex2dec("FFFFEE00")
    else:
        arc_color = (255, 0, 0, 255)
    return arc_color

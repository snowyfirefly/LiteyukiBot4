from nonebot import require

from ...liteyuki_api.canvas import Color
from ...liteyuki_api.reloader import Reloader


# 可选参数 5秒后触发重启


def restart_bot():
    Reloader.reload()


def get_usage_percent_color(percent):
    if percent < 40:
        arc_color = Color.hex2dec("FF55AF7B")
    elif percent < 60:
        arc_color = Color.hex2dec("FFFAC230")
    elif percent < 80:
        arc_color = Color.hex2dec("FFFA9D5A")
    else:
        arc_color = Color.hex2dec("FFEB4537")
    return arc_color

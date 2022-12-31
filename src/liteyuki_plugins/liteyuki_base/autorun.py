import time

from nonebot import get_driver

from ...liteyuki_api.data import *
driver = get_driver()
# 保存启动时间
@driver.on_startup
async def _():
    Data(Data.globals, "liteyuki").set_data("start_time", list(time.localtime())[0:6])

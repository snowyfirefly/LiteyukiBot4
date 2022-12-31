import time

from bot import driver
from ...liteyuki_api.data import *

# 保存启动时间
@driver.on_startup
async def _():
    Data(Data.globals, "liteyuki").set_data("start_time", list(time.localtime())[0:6])

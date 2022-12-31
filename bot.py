#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from src.liteyuki_api.config import init

# 初始化轻雪
from src.liteyuki_api.data import Data

init()
# 初始化Nonebot
nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)
for plugin_name in Data(Data.globals, "liteyuki").get_data("installed_plugin", []):
    nonebot.load_plugin(plugin_name)
if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")

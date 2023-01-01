#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import traceback

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
nonebot.load_from_toml("pyproject.toml")
for plugin_name in Data(Data.globals, "liteyuki").get_data("installed_plugin", []):
    try:
        nonebot.load_plugin(plugin_name)
    except BaseException as e:
        nonebot.logger.info("插件：%s导入时出现错误:%s" % (plugin_name,traceback.format_exception(e)))

if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")

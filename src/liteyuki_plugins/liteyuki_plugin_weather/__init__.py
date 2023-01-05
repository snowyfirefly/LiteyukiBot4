from nonebot.adapters.onebot.v11 import MessageEvent, Bot, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot import on_command
from nonebot.utils import run_sync
from .weather_api import *
from ...liteyuki_api.data import Data
from ...liteyuki_api.utils import *

set_key = on_command("配置天气key", permission=SUPERUSER)
bind_location = on_command("绑定天气城市")


@set_key.handle()
async def _(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
    key = str(arg)
    resp = await run_sync(simple_request_get)("https://api.qweather.com/v7/weather/now?location=101040300&key=%s" % key)
    code = (resp.json())["code"]
    if code == "200":
        key_type = "com"
    else:
        resp = await run_sync(simple_request_get)("https://devapi.qweather.com/v7/weather/now?location=101040300&key=%s" % key)
        code = (resp.json())["code"]
        if code == "200":
            key_type = "dev"
        else:
            key_type = None
            await set_key.finish("key无效")
    Data(Data.globals, "qweather").set_many_data({"key": key, "key_type": key_type})
    await set_key.send("和风天气key设置成功：%s" % ("商业版" if key_type == "com" else "开发版"))

@bind_location.handle()
async def _(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
    args, kwargs = Command.formatToCommand(str(arg))
    # 输入内容
    args_2 = Command.formatToString(args)
    location_list = await run_sync(get_location(args_2, **kwargs))
    print(location_list)


__plugin_meta__ = PluginMetadata(
    name="轻雪天气",
    description="轻雪内置和风天气插件",
    usage='•配置天气key\n\n'
          '•<地名>天气\n\n'
          '•绑定天气城市<地名>\n\n',
    extra={
        "liteyuki_plugin": True,
        "liteyuki_resource_git": {

        }
    }
)

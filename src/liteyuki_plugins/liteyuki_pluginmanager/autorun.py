import traceback

import nonebot
from nonebot.adapters.onebot.v11 import Bot
from nonebot.exception import IgnoredException
from nonebot.matcher import Matcher
from nonebot.message import run_preprocessor
from nonebot.typing import T_State
from nonebot.utils import run_sync

from bot import driver
from .plugin_api import *
from ...liteyuki_api.utils import download_file


@run_preprocessor
async def _(matcher: Matcher, bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], state: T_State):
    """
    检查插件是否启用，未启用则进行阻断

    :param matcher:
    :param bot:
    :param event:
    :param state:
    :return:
    """
    white_list = [
        "liteyuki_pluginmanager"
    ]
    if matcher.plugin_name not in white_list:
        if check_enabled_stats(event, matcher.plugin_name):
            pass
        else:
            raise IgnoredException
    else:
        pass

@driver.on_bot_connect
async def detect_liteyuki_resource():
    """
    检测轻雪插件的资源，不存在就下载
    :return:
    """
    mirror = "https://ghproxy.com/https://github.com/"
    for _plugin in get_loaded_plugins():
        if _plugin.metadata is not None and _plugin.metadata.extra.get("liteyuki_plugin", False):
            git_resource = _plugin.metadata.extra.get("liteyuki_resource_git", {})
            for root_path, url in git_resource.items():
                if not os.path.exists(os.path.join(Path.root, root_path)):
                    await run_sync(download_file)(file=os.path.join(Path.root, root_path), url=mirror + url)
            normal_resource = _plugin.metadata.extra.get("liteyuki_resource", {})
            for root_path, url in git_resource.items():
                if not os.path.exists(os.path.join(Path.root, root_path)):
                    await run_sync(download_file)(file=os.path.join(Path.root, root_path), url=url)


@driver.on_bot_connect
async def update_metadata():
    """
    联网在nb商店中获取插件元数据

    :return:
    """
    for p in get_loaded_plugins():
        try:
            if p.metadata is None and metadata_db.get_data(p.name) is None:
                plugin_data = await run_sync(search_plugin_info_online)(p.name)
                if plugin_data is not None:
                    plugin_data = plugin_data[0]
                    metadata_db.set_data(p.name, {"name": plugin_data["name"], "description": plugin_data["description"], "usage": ""})
                    nonebot.logger.info("已从Nonebot插件商店中更新本地插件%s（%s）的信息" % (plugin_data["name"], p.name))
        except BaseException as e:
            nonebot.logger.info("更新插件%s信息时出现错误:%s" % (p.name, traceback.format_exception(e)))
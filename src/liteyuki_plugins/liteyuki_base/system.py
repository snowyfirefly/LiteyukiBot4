import datetime
import json
import os
import random
import shutil
import time
import traceback
from typing import Union

from PIL import Image
from nonebot.params import CommandArg
from nonebot.typing import T_State
from nonebot.utils import run_sync
from .utils import *
from ...liteyuki_api.canvas import *
from ...liteyuki_api.config import *
from ...liteyuki_api.data import LiteyukiDB
from ...liteyuki_api.utils import *
from nonebot import *
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent, Message, NoticeEvent, Bot, MessageSegment
from nonebot.permission import SUPERUSER
import pickle

check_update = on_command("检查更新", permission=SUPERUSER)
set_auto_update = on_command("启用自动更新", aliases={"停用自动更新"}, permission=SUPERUSER)
update = on_command("#update", aliases={"#轻雪更新"}, permission=SUPERUSER)
restart = on_command("#restart", aliases={"#轻雪重启"}, permission=SUPERUSER)
export_database = on_command("#export", aliases={"#导出数据"}, permission=SUPERUSER)
liteyuki_bot_info = on_command("#info", aliases={"#轻雪信息", "#轻雪状态"}, permission=SUPERUSER)
clear_cache = on_command("#清除缓存", permission=SUPERUSER)
self_destroy = on_command("#轻雪自毁", permission=SUPERUSER)

data_importer = on_notice()


@check_update.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    check_url = "https://gitee.com/snowykami/liteyuki-bot/raw/master/src/config/config.json"
    local_version_id: int = config_data.get("version_id", None)
    local_version_name: str = config_data.get("version_name", None)
    resp = await run_sync(simple_request)(check_url)
    resp_data = resp.json()
    msg = "当前版本：%s(%s)\n仓库版本：%s(%s)" % (local_version_name, local_version_id, resp_data.get("version_name"), resp_data.get("version_id"))
    if resp_data.get("version_id") > local_version_id:
        msg += "\n检测到新版本：\n请使用「#update BotQQ号」命令手动更新"
    await check_update.send(msg)


@update.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], arg: Message = CommandArg()):
    check_url = "https://gitee.com/snowykami/liteyuki-bot/raw/master/src/config/config.json"
    local_version_id: int = config_data.get("version_id", None)
    local_version_name: str = config_data.get("version_name", None)
    resp = await run_sync(simple_request)(check_url)
    resp_data = resp.json()
    await update.send("开始更新:\n当前：%s(%s)\n更新：%s(%s)" % (local_version_name, local_version_id, resp_data.get("version_name"), resp_data.get("version_id")), at_sender=True)
    await run_sync(os.system)("git pull --force https://gitee.com/snowykami/liteyuki-bot.git")
    await update.send("更新完成，正在重启", at_sender=True)
    restart_bot()


@restart.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], arg: Message = CommandArg()):
    await restart.send("正在重启", at_sender=True)
    restart_bot()


@export_database.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    export_db = {"export_time": tuple(time.localtime())[0:6]}
    for collection_name in LiteyukiDB.list_collection_names():
        export_db[collection_name] = []
        for document in LiteyukiDB[collection_name].find():
            export_db[collection_name].append(document)
    f_path = os.path.join(Path.cache, "liteyuki.db")

    def export():
        f = open(f_path, "wb")
        pickle.dump(export_db, f)
        f.close()

    await run_sync(export)()
    datetime = "%s-%s-%s-%s-%s-%s" % tuple(time.localtime())[0:6]
    await bot.call_api("upload_private_file", user_id=event.user_id, file=f_path, name="liteyuki_%s.db" % datetime)


@data_importer.handle()
async def _(bot: Bot, event: NoticeEvent, state: T_State):
    eventData = event.dict()
    if str(eventData.get("user_id", None)) in bot.config.superusers:
        if event.notice_type == "offline_file":
            file = eventData["file"]
            name: str = file.get("name", "")
            if name.startswith("liteyuki") and name.endswith(".db"):
                url = file.get("url", "")
                path = os.path.join(Path.cache, name)
                await run_sync(download_file)(url, path)
                liteyuki_db = pickle.load(open(path, "rb"))
                for collection_name, collection_data in liteyuki_db.items():
                    collection = LiteyukiDB[collection_name]
                    if collection_name == "export_time":
                        continue
                    for document in collection_data:
                        for key, value in document.items():
                            collection.update_one(filter={"_id": document.get("_id")}, update={"$set": {key: value}}, upsert=True)
                await bot.send_private_msg(user_id=eventData.get("user_id"), message="数据库合并完成")


# 轻雪状态
@liteyuki_bot_info.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    msg = "轻雪状态："
    stats = await bot.call_api("get_status")
    prop_list = [
        {
            "Bot昵称": "、".join(bot.config.nickname if len(bot.config.nickname) else ["Bot还没有名字哦"]),
            "状态": "在线" if stats.get("online") else "离线",
            "群聊数": len(await bot.get_group_list()),
            "好友数": len(await bot.get_friend_list()),
            "收/发消息数": "%s/%s" % (stats.get("stat").get("message_received"), stats.get("stat").get("message_sent")),
            "收/发数据包数": "%s/%s" % (stats.get("stat").get("packet_received"), stats.get("stat").get("packet_sent"))
        }
    ]
    drawing_path = os.path.join(Path.data, "liteyuki/drawing")
    head_high = 350
    hardware_high = 640
    width = 1080
    side = 20
    if len(drawing_path) > 0:
        base_img = await run_sync(Utils.central_clip_by_ratio)(Image.open(os.path.join(Path.data, "liteyuki/drawing/%s" % random.choice(os.listdir(drawing_path)))), (width, 2000))
    else:
        base_img = Image.new(mode="RGBA", size=(width, 2000), color=(255, 255, 255, 255))
    info_canvas = Canvas(base_img)
    info_canvas.content = Panel(
        uv_size=info_canvas.base_img.size,
        box_size=(info_canvas.base_img.size[0] - 2 * side, info_canvas.base_img.size[1] - 2 * side),
        parent_point=(0.5, 0.5), point=(0.5, 0.5)
    )
    content_size = info_canvas.get_actual_pixel_size("content")
    print(content_size)
    info_canvas.content.head = Rectangle(
        uv_size=(1, content_size[1]), box_size=(1, head_high),
        parent_point=(0.5, 0), point=(0.5, 0), fillet=0.05, color=(0, 0, 0, 80)
    )
    user_icon_path = os.path.join(Path.cache, "u%s.png" % bot.self_id)
    await run_sync(download_file)("http://q1.qlogo.cn/g?b=qq&nk=%s&s=640" % bot.self_id, user_icon_path)
    head_size = info_canvas.get_actual_pixel_size("content.head")
    info_canvas.content.head.icon = Img(
        uv_size=(1, 1), box_size=(0.75, 0.75), parent_point=(min(head_size) / 2 / max(head_size), 0.5), point=(0.5, 0.5),
        img=await run_sync(Utils.circular_clip)(Image.open(user_icon_path))
    )
    icon_pos = info_canvas.get_parent_box("content.head.icon")
    info_canvas.content.head.nickname = Text(
        uv_size=(1, 1), box_size=(0.75, 0.25), parent_point=(icon_pos[2] + 0.05, 0.45), point=(0, 1),
        text=list(bot.config.nickname)[0]
    )
    nickname_pos = info_canvas.get_parent_box("content.head.nickname")
    await run_sync(info_canvas.draw_line)("content.head", (nickname_pos[0], nickname_pos[3] + 0.05), (nickname_pos[2], nickname_pos[3] + 0.05), (80, 80, 80, 255), width=5)
    for prop in prop_list:
        for prop_name, prop_value in prop.items():
            msg += "\n%s: %s" % (prop_name, prop_value)
    await liteyuki_bot_info.send(MessageSegment.image(file="file:///%s" % await run_sync(info_canvas.export_cache)()))


# 清除缓存
@clear_cache.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    file_list = []

    def get_all_file(_dir: str):
        for _f in os.listdir(_dir):
            wp = os.path.join(_dir, _f)
            if os.path.isdir(wp):
                get_all_file(wp)
            else:
                file_list.append(wp)

    get_all_file(Path.cache)

    if len(file_list) > 0:
        size_int = 0
        for f in file_list:
            size_int += os.path.getsize(f)
        size = size_text(size_int)
        await run_sync(shutil.rmtree)(Path.cache)
        await run_sync(os.makedirs)(Path.cache)
        await clear_cache.send(message="缓存清除成功：%s" % size)
    else:
        if not os.path.exists(Path.cache):
            os.makedirs(Path.cache)
        await clear_cache.send(message="当前没有缓存")


# 你在尝试一种很新的玩法
@self_destroy.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    pass

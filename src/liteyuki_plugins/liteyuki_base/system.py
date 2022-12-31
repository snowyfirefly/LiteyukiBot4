import datetime
import json
import os
import platform
import random
import shutil
import time
import traceback
from typing import Union

import psutil
from PIL import Image
from nonebot.params import CommandArg
from nonebot.typing import T_State
from nonebot.utils import run_sync
from .utils import *
from ...liteyuki_api.canvas import *
from ...liteyuki_api.config import *
from ...liteyuki_api.data import LiteyukiDB, Data
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
    _datetime = "%s-%s-%s-%s-%s-%s" % tuple(time.localtime())[0:6]
    await bot.call_api("upload_private_file", user_id=event.user_id, file=f_path, name="liteyuki_%s.db" % _datetime)


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
    if len(bot.config.nickname) == 0:
        bot.config.nickname.add("轻雪")
    msg = "轻雪状态："
    stats = await bot.get_status()
    version_info = await bot.get_version_info()
    protocol_dict = {
        -1: "",
        0: "iPad",
        1: "Android",
        2: "手表",
        3: "MacOS",
        4: "企点",
        5: "iPad"
    }
    delta_time = datetime.datetime.now() - datetime.datetime.strptime("%s-%s-%s-%s-%s-%s" % tuple(Data(Data.globals, "liteyuki").get_data("start_time", tuple(time.localtime())[0:6])),
                                                                      "%Y-%m-%d-%H-%M-%S")
    delta_sec = delta_time.days * 24 * 60 * 60 + delta_time.seconds
    prop_list = [
        [
            "%s%s" % (protocol_dict.get(version_info["protocol"], ""), "在线" if stats.get("online") else "离线"),
            "群聊 %s" % len(await bot.get_group_list()),
            "好友 %s" % len(await bot.get_friend_list())

        ],
        [
            "接收 %s 发送 %s" % (stats.get("stat").get("message_received"), stats.get("stat").get("message_sent")),
            "运行时间 %s" % time_format_text_by_sec(delta_sec)
        ],
        [
            "轻雪版本 %s" % config_data["version_name"],
            "适配器 %s" % version_info["app_version"]
        ]
    ]
    part_3_prop = {
        "平台": platform.platform()
    }
    drawing_path = os.path.join(Path.data, "liteyuki/drawing")
    head_high = 350
    hardware_high = 640
    block_distance = 20
    block_alpha = 168
    single_disk_high = 60
    disk_distance = 10
    disk_count = len(psutil.disk_partitions())
    part_3_prop_high = 60
    part_3_high = disk_distance * (disk_count + 1) + single_disk_high * disk_count + len(part_3_prop) * part_3_prop_high
    width = 1080
    side = 20
    high = side * 2 + block_distance * 2 + head_high + hardware_high + part_3_high
    if len(os.listdir(drawing_path)) > 0:
        base_img = await run_sync(Utils.central_clip_by_ratio)(Image.open(os.path.join(Path.data, "liteyuki/drawing/%s" % random.choice(os.listdir(drawing_path)))), (width, high))
    else:
        base_img = Image.new(mode="RGBA", size=(width, high), color=(255, 255, 255, 255))
    info_canvas = Canvas(base_img)
    info_canvas.content = Panel(
        uv_size=info_canvas.base_img.size,
        box_size=(info_canvas.base_img.size[0] - 2 * side, info_canvas.base_img.size[1] - 2 * side),
        parent_point=(0.5, 0.5), point=(0.5, 0.5)
    )
    content_size = info_canvas.get_actual_pixel_size("content")
    """head block"""
    info_canvas.content.head = Rectangle(
        uv_size=(1, content_size[1]), box_size=(1, head_high),
        parent_point=(0.5, 0), point=(0.5, 0), fillet=20, color=(0, 0, 0, block_alpha)
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
        uv_size=(1, 1), box_size=(0.6, 0.25), parent_point=(icon_pos[2] + 0.05, 0.4), point=(0, 1),
        text=(await bot.get_login_info())["nickname"], font=Font.HYWH_85w, dp=1
    )
    nickname_pos = info_canvas.get_parent_box("content.head.nickname")
    await run_sync(info_canvas.draw_line)("content.head", (nickname_pos[0], nickname_pos[3] + 0.05), (nickname_pos[2], nickname_pos[3] + 0.05), (255, 255, 255, 255), width=5)
    for i, prop_sub_list in enumerate(prop_list):
        prop_text_list = []
        for prop_str in prop_sub_list:
            prop_text_list.append(TextSegment(prop_str, color=(240, 240, 240, 255)))
            prop_text_list.append(TextSegment(" | ", color=(168, 168, 168, 255)))
        del prop_text_list[-1]
        info_canvas.content.head.__dict__["label_%s" % i] = Text(
            uv_size=(1, 1), box_size=(0.6, 0.1), parent_point=(nickname_pos[0], nickname_pos[3] + 0.08 + 0.16 * i), point=(0, 0), text=prop_text_list, force_size=True, font=Font.HYWH_85w
        )
    """hardware block"""
    hardware = info_canvas.content.hardware = Rectangle(
        uv_size=(1, content_size[1]), box_size=(1, hardware_high),
        parent_point=(0.5, (head_high + block_distance) / content_size[1]), point=(0.5, 0), fillet=20, color=(0, 0, 0, block_alpha)
    )
    hardware_part = [
        {
            "name": "CPU",
            "percent": sum(psutil.cpu_percent(percpu=True)),
            "sub_prop": [
                "物理核心 %s" % psutil.cpu_count(logical=False),
                "逻辑处理器 %s" % psutil.cpu_count(),
                "%sMhz" % average(psutil.cpu_freq())
            ]
        },
        {
            "name": "RAM",
            "percent": psutil.virtual_memory().used / psutil.virtual_memory().total * 100,
            "percent2": psutil.Process(os.getpid()).memory_info().rss / psutil.virtual_memory().total * 100,
            "sub_prop": [
                "Bot %s" % size_text(psutil.Process(os.getpid()).memory_info().rss),
                "已用 %s" % size_text(psutil.virtual_memory().used),
                "剩余 %s" % size_text(psutil.virtual_memory().free),
                "总计 %s" % size_text(psutil.virtual_memory().total)
            ]
        }
    ]
    for part_i, sub_part in enumerate(hardware_part):
        if sub_part["percent"] < 40:
            arc_color = (0, 255, 0, 255)
        elif sub_part["percent"] < 60:
            arc_color = (255, 255, 255, 255)
        elif sub_part["percent"] < 80:
            arc_color = arc_color = Color.hex2dec("FFFFEE00")
        else:
            arc_color = (255, 0, 0, 255)
        point_x = (part_i * 2 + 1) / (len(hardware_part) * 2)
        arc_bg = Graphical.arc(160, 0, 360, width=40, color=(192, 192, 192, 192))
        arc_up = Graphical.arc(160, 0, 360 * sub_part["percent"] / 100, width=40, color=arc_color)

        part = hardware.__dict__["part_%s" % part_i] = Panel(
            uv_size=(1, 1), box_size=(1 / len(hardware_part), 1), parent_point=(point_x, 0.4), point=(0.5, 0.5)
        )
        part.arc_bg = Img(uv_size=(1, 1), box_size=(0.6, 0.5), parent_point=(0.5, 0.4), point=(0.5, 0.5), img=arc_bg)

        part.arc_bg.arc_up = Img(uv_size=(1, 1), box_size=(1, 1), parent_point=(0.5, 0.5), point=(0.5, 0.5), img=arc_up)
        part.arc_bg.percent_text = Text(
            uv_size=(1, 1), box_size=(0.4, 0.2), parent_point=(0.5, 0.5), point=(0.5, 0.5), text="%.1f" % sub_part["percent"] + "%", force_size=True, font=Font.HYWH_85w
        )
        arc_pos = info_canvas.get_parent_box("content.hardware.part_%s.arc_bg" % part_i)
        part.name = Text(uv_size=(1, 1), box_size=(1, 0.08), parent_point=(0.5, arc_pos[3] + 0.03), point=(0.5, 0), text=sub_part["name"], force_size=True, font=Font.HYWH_85w)
        last_pos = info_canvas.get_parent_box("content.hardware.part_%s.name" % part_i)
        for sub_prop_i, sub_prop in enumerate(sub_part["sub_prop"]):
            part.__dict__["sub_prop_%s" % sub_prop_i] = Text(
                uv_size=(1, 1), box_size=(1, 0.05), parent_point=(0.5, last_pos[3] + 0.02), point=(0.5, 0), text=sub_prop, force_size=True, color=(192, 192, 192, 255), font=Font.HYWH_85w
            )
            last_pos = info_canvas.get_parent_box("content.hardware.part_%s.sub_prop_%s" % (part_i, sub_prop_i))

    part_3 = info_canvas.content.part_3 = Rectangle(
        uv_size=(1, content_size[1]), box_size=(1, part_3_high),
        parent_point=(0.5, (head_high + hardware_high + block_distance * 2) / content_size[1]), point=(0.5, 0), fillet=20, color=(0, 0, 0, block_alpha)
    )

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

import datetime
import pickle
import platform
import random
import shutil
import time

import psutil
from nonebot import *
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent, Message, NoticeEvent, Bot, MessageSegment, MessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.utils import run_sync

from .utils import *
from ...liteyuki_api.canvas import *
from ...liteyuki_api.config import *
from ...liteyuki_api.data import LiteyukiDB, Data
from ...liteyuki_api.utils import *

check_update = on_command("#检查更新", permission=SUPERUSER)
set_auto_update = on_command("#启用自动更新", aliases={"#停用自动更新"}, permission=SUPERUSER)
update = on_command("#update", aliases={"#更新", "#轻雪更新"}, permission=SUPERUSER)
restart = on_command("#reboot", aliases={"#重启", "#轻雪重启"}, permission=SUPERUSER)
export_database = on_command("#export", aliases={"#导出数据"}, permission=SUPERUSER)
liteyuki_bot_info = on_command("#state", aliases={"#状态", "#轻雪状态"})
clear_cache = on_command("#清除缓存", permission=SUPERUSER)
self_destroy = on_command("#轻雪自毁", permission=SUPERUSER)
enable_group = on_command("#群聊启用", aliases={"#群聊停用"}, permission=SUPERUSER)
ban_user = on_command("#屏蔽用户", aliases={"#取消屏蔽"}, permission=SUPERUSER)
call_api = on_command("#api", permission=SUPERUSER)

data_importer = on_notice()


@check_update.handle()
async def _():
    check_url = "https://gitee.com/snowykami/liteyuki-bot/raw/master/src/config/config.json"
    local_version_id: int = config_data.get("version_id", None)
    local_version_name: str = config_data.get("version_name", None)
    resp = await run_sync(simple_request_get)(check_url)
    resp_data = resp.json()
    msg = "当前版本：%s(%s)\n仓库版本：%s(%s)" % (local_version_name, local_version_id, resp_data.get("version_name"), resp_data.get("version_id"))
    if resp_data.get("version_id") > local_version_id:
        msg += "\n检测到新版本：\n请使用「#更新」命令手动更新"
    await check_update.send(msg)


@update.handle()
async def _(event: PrivateMessageEvent):
    check_url = "https://gitee.com/snowykami/liteyuki-bot/raw/master/src/config/config.json"
    local_version_id: int = config_data.get("version_id", None)
    local_version_name: str = config_data.get("version_name", None)
    resp = await run_sync(simple_request_get)(check_url)
    resp_data = resp.json()
    await update.send("开始更新:\n当前：%s(%s)\n更新：%s(%s)" % (local_version_name, local_version_id, resp_data.get("version_name"), resp_data.get("version_id")), at_sender=True)
    await run_sync(os.system)("git pull --force https://gitee.com/snowykami/liteyuki-bot.git")
    await update.send("更新完成，正在重启", at_sender=True)
    restart_bot()


@restart.handle()
async def _():
    await restart.send("正在重启", at_sender=True)
    restart_bot()


@export_database.handle()
async def _(bot: Bot, event: PrivateMessageEvent):
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
    _datetime = "-".join([str(i) for i in list(time.localtime())[0:6]])
    await bot.call_api("upload_private_file", user_id=event.user_id, file=f_path, name=f"liteyuki_{_datetime}.db")


# 轻雪状态
@liteyuki_bot_info.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if len(bot.config.nickname) == 0:
        bot.config.nickname.add("轻雪")
    stats = await bot.get_status()
    version_info = await bot.get_version_info()
    protocol_dict = {
        -1: "",
        0: "iPad",
        1: "手机",
        2: "手表",
        3: "MacOS",
        4: "企点",
        5: "iPad"
    }
    time_list_6 = [str(i) for i in list(Data(Data.globals, "liteyuki").get_data("start_time", tuple(time.localtime())[0:6]))]
    protocol_name = protocol_dict.get(version_info.get("protocol", version_info.get("protocol_name", 0)), "")
    delta_time = datetime.datetime.now() - datetime.datetime.strptime("-".join(time_list_6),
                                                                      "%Y-%m-%d-%H-%M-%S")
    delta_sec = delta_time.days * 24 * 60 * 60 + delta_time.seconds
    prop_list = [
        [
            f"{protocol_name}在线"
            f"群 {len(await bot.get_group_list())}",
            f"好友 {len(await bot.get_friend_list())}",
            f"插件 {len(get_loaded_plugins())}"

        ],
        [
            f"收 {stats.get('stat').get('message_received')} 发 {stats.get('stat').get('message_sent')}",
            f"运行时长 {time_to_hms_by_sec(delta_sec)}"
        ],
        [
            f"版本 {config_data['version_name']}",
            f"适配器 {version_info['app_version']}"
        ]
    ]
    part_3_prop = {
        "OS": f"{platform.system()} {platform.version()}",
        "Python": f"{platform.python_implementation()} {platform.python_version()}",
        "Signature": generate_signature
    }
    drawing_path = os.path.join(Path.data, "liteyuki/drawing")
    head_high = 350
    hardware_high = 700
    block_distance = 20
    block_alpha = 168

    single_disk_high = 70
    disk_distance = 20
    disk_count = len(psutil.disk_partitions())
    part_3_prop_high = 70
    distance_of_part_3_sub_part = 20
    part_3_high = disk_distance * (disk_count + 1) + single_disk_high * disk_count + len(part_3_prop) * part_3_prop_high + (len(part_3_prop) + 1) * distance_of_part_3_sub_part

    width = 1080
    side_up = 20
    side_down = 20

    part_fillet = 20

    default_font = Font.HYWH_85w

    usage_base_color = (192, 192, 192, 192)

    high = side_up + side_down + block_distance * 2 + head_high + hardware_high + part_3_high
    if len(os.listdir(drawing_path)) > 0:
        base_img = await run_sync(Utils.central_clip_by_ratio)(Image.open(os.path.join(Path.data, f"liteyuki/drawing/{random.choice(os.listdir(drawing_path))}")), (width, high))
    else:
        base_img = Image.new(mode="RGBA", size=(width, high), color=(255, 255, 255, 255))
    info_canvas = Canvas(base_img)
    info_canvas.content = Panel(
        uv_size=info_canvas.base_img.size,
        box_size=(info_canvas.base_img.size[0] - 2 * side_up, info_canvas.base_img.size[1] - side_up - side_down),
        parent_point=(0.5, 0.5), point=(0.5, 0.5)
    )
    content_size = info_canvas.get_actual_pixel_size("content")
    """head block"""
    info_canvas.content.head = Rectangle(
        uv_size=(1, content_size[1]), box_size=(1, head_high),
        parent_point=(0.5, 0), point=(0.5, 0), fillet=part_fillet, color=(0, 0, 0, block_alpha)
    )
    user_icon_path = os.path.join(Path.cache, f"u{bot.self_id}.png")
    await run_sync(download_file)(f"http://q1.qlogo.cn/g?b=qq&nk={bot.self_id}&s=640", user_icon_path)
    head_size = info_canvas.get_actual_pixel_size("content.head")
    info_canvas.content.head.icon = Img(
        uv_size=(1, 1), box_size=(0.75, 0.75), parent_point=(min(head_size) / 2 / max(head_size), 0.5), point=(0.5, 0.5),
        img=await run_sync(Utils.circular_clip)(Image.open(user_icon_path))
    )
    icon_pos = info_canvas.get_parent_box("content.head.icon")
    info_canvas.content.head.nickname = Text(
        uv_size=(1, 1), box_size=(0.6, 0.18), parent_point=(icon_pos[2] + 0.05, 0.23), point=(0, 0.5),
        text=(await bot.get_stranger_info(user_id=event.self_id, no_cache=True))["nickname"], font=default_font, dp=1
    )
    nickname_pos = info_canvas.get_parent_box("content.head.nickname")
    await run_sync(info_canvas.draw_line)("content.head", (nickname_pos[0], nickname_pos[3] + 0.05), (nickname_pos[2], nickname_pos[3] + 0.05), (255, 255, 255, 255), width=5)
    for i, prop_sub_list in enumerate(prop_list):
        prop_text_list = []
        for prop_str in prop_sub_list:
            prop_text_list.append(TextSegment(prop_str, color=(240, 240, 240, 255)))
            prop_text_list.append(TextSegment(" | ", color=(168, 168, 168, 255)))
        del prop_text_list[-1]
        info_canvas.content.head.__dict__[f"label_{i}"] = Text(
            uv_size=(1, 1), box_size=(0.6, 0.1), parent_point=(nickname_pos[0], nickname_pos[3] + 0.08 + 0.16 * i), point=(0, 0), text=prop_text_list, force_size=True, font=default_font
        )
    """hardware block"""
    hardware = info_canvas.content.hardware = Rectangle(
        uv_size=(1, content_size[1]), box_size=(1, hardware_high),
        parent_point=(0.5, (head_high + block_distance) / content_size[1]), point=(0.5, 0), fillet=part_fillet, color=(0, 0, 0, block_alpha)
    )

    # percent为0-1的float
    hardware_part = [
        {
            "name": "CPU",
            "percent": psutil.cpu_percent(),
            "sub_prop": [
                "物理核心 {psutil.cpu_count(logical=False)}",
                "逻辑处理器 psutil.cpu_count()",
                f"{round(average([percpu.current for percpu in psutil.cpu_freq(percpu=True)]), 1)}MHz"
            ]
        },
        {
            "name": "RAM",
            "percent": psutil.virtual_memory().used / psutil.virtual_memory().total * 100,
            "percent2": psutil.Process(os.getpid()).memory_info().rss / psutil.virtual_memory().total * 100,
            "sub_prop": [
                f"Bot {size_text(psutil.Process(os.getpid()).memory_info().rss)}",
                f"已用 {size_text(psutil.virtual_memory().used)}",
                f"空闲 {size_text(psutil.virtual_memory().free)}",
                f"总计 {size_text(psutil.virtual_memory().total)}"
            ]
        }
    ]
    for part_i, sub_part in enumerate(hardware_part):
        arc_color = get_usage_percent_color(sub_part["percent"])
        point_x = (part_i * 2 + 1) / (len(hardware_part) * 2)
        arc_bg = Graphical.arc(160, 0, 360, width=40, color=usage_base_color)
        arc_up = Graphical.arc(160, 0, 360 * sub_part["percent"] / 100, width=40, color=arc_color)

        part = hardware.__dict__[f"part_{part_i}"] = Panel(
            uv_size=(1, 1), box_size=(1 / len(hardware_part), 1), parent_point=(point_x, 0.4), point=(0.5, 0.5)
        )
        part.arc_bg = Img(uv_size=(1, 1), box_size=(0.6, 0.5), parent_point=(0.5, 0.4), point=(0.5, 0.5), img=arc_bg)

        part.arc_bg.arc_up = Img(uv_size=(1, 1), box_size=(1, 1), parent_point=(0.5, 0.5), point=(0.5, 0.5), img=arc_up)
        part.arc_bg.percent_text = Text(
            uv_size=(1, 1), box_size=(0.55, 0.15), parent_point=(0.5, 0.5), point=(0.5, 0.5), text="%.1f" % sub_part["percent"] + "%", font=default_font, dp=1, force_size=True
        )
        arc_pos = info_canvas.get_parent_box(f"content.hardware.part_{part_i}.arc_bg")
        part.name = Text(uv_size=(1, 1), box_size=(1, 0.08), parent_point=(0.5, arc_pos[3] + 0.03), point=(0.5, 0), text=sub_part["name"], force_size=True, font=default_font)
        last_pos = info_canvas.get_parent_box(f"content.hardware.part_{part_i}.name")
        for sub_prop_i, sub_prop in enumerate(sub_part["sub_prop"]):
            part.__dict__[f"sub_prop_{sub_prop_i}"] = Text(
                uv_size=(1, 1), box_size=(1, 0.05), parent_point=(0.5, last_pos[3] + 0.02), point=(0.5, 0), text=sub_prop, force_size=True, color=(192, 192, 192, 255), font=default_font
            )
            last_pos = info_canvas.get_parent_box(f"content.hardware.part_{part_i}.sub_prop_{sub_prop_i}")

    part_3 = info_canvas.content.part_3 = Rectangle(
        uv_size=(1, content_size[1]), box_size=(1, part_3_high),
        parent_point=(0.5, (head_high + hardware_high + block_distance * 2) / content_size[1]), point=(0.5, 0), fillet=part_fillet, color=(0, 0, 0, block_alpha)
    )
    part_3_pixel_size = info_canvas.get_actual_pixel_size("content.part_3")
    point_y = distance_of_part_3_sub_part / part_3_pixel_size[1]
    for disk_i, disk in enumerate(psutil.disk_partitions()):
        disk_usage = psutil.disk_usage(disk.device)
        disk_panel = part_3.__dict__[f"disk_panel_{disk_i}"] = Panel(
            uv_size=(1, 1), box_size=(1, single_disk_high / part_3_pixel_size[1]), parent_point=(0.5, point_y + disk_i * (disk_distance + single_disk_high) / part_3_pixel_size[1]),
            point=(0.5, 0)
        )
        disk_panel.name = Text(
            uv_size=(1, 1), box_size=(0.2, 0.7), parent_point=(0.05, 0.5), point=(0, 0.5), text=disk.device, font=default_font, force_size=True
        )
        disk_panel.usage_bg = Rectangle(
            uv_size=(1, 1), box_size=(0.75, 0.9), parent_point=(0.2, 0.5), point=(0, 0.5), fillet=10, color=usage_base_color
        )
        disk_panel.usage_bg.usage_img = Rectangle(
            uv_size=(1, 1), box_size=(1 * disk_usage.used / disk_usage.total, 1), parent_point=(0, 0.5), point=(0, 0.5), fillet=10,
            color=get_usage_percent_color(disk_usage.used / disk_usage.total * 100)
        )

        disk_panel.usage_bg.usage_text = Text(
            uv_size=(1, 1), box_size=(1, 0.6), parent_point=(0.5, 0.5), point=(0.5, 0.5),
            text=f"{round(disk_usage.used / disk_usage.total * 100, 1)}% 可用{size_text(disk_usage.free, dec=1)} 共{size_text(disk_usage.total, dec=1)}", font=default_font
        )
    point_y += (len(psutil.disk_partitions()) * (single_disk_high + disk_distance) + distance_of_part_3_sub_part) / part_3_pixel_size[1]
    for prop_i, prop_dict in enumerate(part_3_prop.items()):
        prop_panel = part_3.__dict__[f"prop_panel_{prop_i}"] = Panel(
            uv_size=(1, 1), box_size=(1, part_3_prop_high / part_3_pixel_size[1]),
            parent_point=(0.5, point_y + prop_i * (part_3_prop_high + distance_of_part_3_sub_part) / part_3_pixel_size[1]),
            point=(0.5, 0)
        )
        prop_panel.name = Text(
            uv_size=(1, 1), box_size=(0.25, 0.6), parent_point=(0.05, 0.5), point=(0, 0.5), text=prop_dict[0], force_size=True, font=default_font
        )
        prop_panel.value = Text(
            uv_size=(1, 1), box_size=(0.25, 0.6), parent_point=(0.95, 0.5), point=(1, 0.5), text=prop_dict[1], force_size=True, font=default_font
        )
    await liteyuki_bot_info.send(MessageSegment.image(file=f"file:///{await run_sync(info_canvas.export_cache)()}"))
    await run_sync(info_canvas.delete)()


# 清除缓存
@clear_cache.handle()
async def _():
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
        await clear_cache.send(message=f"缓存清除成功：{size}")
    else:
        if not os.path.exists(Path.cache):
            os.makedirs(Path.cache)
        await clear_cache.send(message="当前没有缓存")


@call_api.handle()
async def _(bot: Bot, arg: Message = CommandArg()):
    try:
        args, kwargs = Command.formatToCommand(str(arg), exe=True)
        result = await bot.call_api(args[0], **kwargs)
        await call_api.send(str(result))
    except BaseException as e:
        await call_api.send(f"API调用时出错：{traceback.format_exception(e)}")


@ban_user.handle()
async def _(event: MessageEvent, bot: Bot, arg: Message = CommandArg()):
    user_id_list = [int(i) for i in str(arg).strip().split()]
    banned_user_list = Data(Data.globals, "liteyuki").get_data("banned_users", [])
    failed_list = []
    suc_list = []
    if "#屏蔽用户" in event.raw_message:
        ban = True
    else:
        ban = False
    info_dict = {}
    for ban_user_id in user_id_list:
        user_info = await bot.get_stranger_info(user_id=ban_user_id, no_cache=True)
        nickname = user_info["nickname"]
        info_dict[ban_user_id] = nickname
        if ban:
            if ban_user_id not in banned_user_list:
                banned_user_list.append(ban_user_id)
                suc_list.append(ban_user_id)
            else:
                failed_list.append(ban_user_id)
        else:
            if ban_user_id in banned_user_list:
                banned_user_list.remove(ban_user_id)
                suc_list.append(ban_user_id)
            else:
                failed_list.append(ban_user_id)

    msg = ""
    if len(suc_list) > 0:
        if ban:
            msg += "已屏蔽以下用户："
        else:
            msg += "已对以下用户取消屏蔽："
        for suc_id in suc_list:
            msg += f"\n- {info_dict[suc_id]}({suc_id})"

    if len(failed_list) > 0:
        if len(suc_list) > 0:
            msg += "\n\n"
        if ban:
            msg += "以下用户之前已被屏蔽："
        else:
            msg += "以下用户之前未被屏蔽："
        for failed_id in failed_list:
            msg += f"\n- {info_dict[failed_id]}({failed_id})"
    if len(user_id_list) > 0:
        Data(Data.globals, "liteyuki").set_data("banned_users", banned_user_list)
        await ban_user.send(msg)


@data_importer.handle()
async def _(bot: Bot, event: NoticeEvent):
    eventData = event.dict()
    if str(eventData.get("user_id", None)) in bot.config.superusers:
        # 超级用户判断
        if event.notice_type == "offline_file":
            # 判断为文件
            file = eventData["file"]
            name: str = file.get("name", "")
            if name.startswith("liteyuki") and name.endswith(".db"):
                # 导数据
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
            else:
                # 存文件
                url = file.get("url", "")
                path = os.path.join(Path.data, "file_receive", name)
                await run_sync(download_file)(url, path)
                await bot.send_private_msg(user_id=eventData.get("user_id"), message=f"文件已存为{path}")


# 你在尝试一种很新的玩法
@self_destroy.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    await self_destroy.send("启动自毁程序，将会随机删除70%的代码")

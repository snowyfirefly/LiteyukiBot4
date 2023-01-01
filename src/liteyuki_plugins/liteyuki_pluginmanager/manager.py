import asyncio
import traceback

import nonebot
from nonebot import get_driver
from nonebot import on_command
from nonebot import plugin
from nonebot.adapters.onebot.v11 import Bot, Message, GROUP_OWNER, GROUP_ADMIN, PRIVATE_FRIEND
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.utils import run_sync
from ...liteyuki_api.reloader import Reloader
from ...liteyuki_api.utils import download_file, Command

driver = get_driver()
from .plugin_api import *

bot_help = on_command(cmd="help", aliases={"#帮助", "#列出插件", "#插件列表", "#全部插件", "帮助"})
enable_plugin = on_command(cmd="#启用", aliases={"#停用"}, permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN | PRIVATE_FRIEND)
add_meta_data = on_command(cmd="#添加插件元数据", permission=SUPERUSER)
del_meta_data = on_command(cmd="#删除插件元数据", permission=SUPERUSER)
hidden_plugin = on_command(cmd="#隐藏插件", permission=SUPERUSER)
install_plugin = on_command("#install", aliases={"#安装插件"}, permission=SUPERUSER)
uninstall_plugin = on_command("#uninstall", aliases={"#卸载插件"}, permission=SUPERUSER)
update_metadata = on_command("#更新元数据", permission=SUPERUSER)
online_plugin = on_command("#插件商店")


# help菜单
@bot_help.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], arg: Message = CommandArg()):
    if str(arg).strip() == "":
        try:
            if "#全部插件" in event.raw_message:
                raise KeyError("全部插件")
            canvas = generate_plugin_image(event)
            file = canvas.export_cache()
            msg = MessageSegment.image(file="file:///%s" % file)
            await bot_help.send(message=msg)
            canvas.delete()
        except BaseException as e:
            print(e.__repr__())
            traceback.format_exception(e)
            _hidden_plugin = Data(Data.globals, "plugin_data").get_data(key="hidden_plugin", default=[])
            msg = "加载插件数：%s" % len(plugin.get_loaded_plugins())
            for _plugin in plugin.get_loaded_plugins():
                hidden_stats = "隐" if _plugin.name in _hidden_plugin else "显"
                enable_stats = "开" if check_enabled_stats(event, _plugin.name) else "关"
                if _plugin.metadata is not None:
                    p_name = _plugin.metadata.name
                else:
                    if metadata_db.get_data(_plugin.name) is not None:
                        p_name = PluginMetadata(**metadata_db.get_data(_plugin.name)).name
                    else:
                        p_name = _plugin.name
                msg += "\n[%s|%s]%s" % (enable_stats, hidden_stats, p_name)
            msg += "\n•使用「help插件名」来获取对应插件的使用方法\n"
            await bot_help.send(message=msg)
    else:
        plugin_name_input = str(arg).strip()
        plugin_ = search_for_plugin(plugin_name_input)
        if plugin_ is None:
            await bot_help.finish("插件不存在", at_sender=True)
        else:
            if plugin_.metadata is not None or metadata_db.get_data(plugin_.name) is not None:
                if metadata_db.get_data(plugin_.name) is not None:
                    plugin_.metadata = PluginMetadata(**metadata_db.get_data(plugin_.name))
                await bot_help.finish("•%s\n「%s」\n==========\n使用方法\n%s" % (plugin_.metadata.name, plugin_.metadata.description, str(plugin_.metadata.usage)))
            else:
                await bot_help.finish("%s还没有编写使用方法" % plugin_.name)


# 启用插件
@enable_plugin.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], arg: Message = CommandArg()):
    plugin_name_input = str(arg).strip()
    enable = True if "#启用" in event.raw_message.replace(plugin_name_input, "") else False
    searched_plugin = search_for_plugin(plugin_name_input)
    if searched_plugin is not None:
        if searched_plugin.metadata is None:
            show_name = searched_plugin.name
            force_enable = False
            if metadata_db.get_data(searched_plugin.name) is not None:
                custom_plugin_metadata = PluginMetadata(**metadata_db.get_data(searched_plugin.name))
                show_name = custom_plugin_metadata.name
                force_enable = custom_plugin_metadata.extra.get("force_enable", False)
        else:
            show_name = searched_plugin.metadata.name
            force_enable = searched_plugin.metadata.extra.get("force_enable", False)
        stats = check_enabled_stats(event, searched_plugin.name)
        if force_enable:
            await enable_plugin.finish("「%s」处于强制启用状态，无法更改" % show_name, at_sender=True)
        if stats == enable:
            await enable_plugin.finish("「%s」处于%s状态，无需重复操作" % (show_name, "启用" if stats else "停用"), at_sender=True)
        else:
            db = Data(*Data.get_type_id(event))
            enabled_plugin = db.get_data("enabled_plugin", [])
            disabled_plugin = db.get_data("disabled_plugin", [])
            default_stats = get_plugin_default_stats(searched_plugin.name)
            if default_stats:
                if enable:
                    disabled_plugin.remove(searched_plugin.name)
                else:
                    disabled_plugin.append(searched_plugin.name)
            else:
                if enable:
                    enabled_plugin.append(searched_plugin.name)
                else:
                    enabled_plugin.remove(searched_plugin.name)
            db.set_data(key="enabled_plugin", value=enabled_plugin)
            db.set_data(key="disabled_plugin", value=disabled_plugin)
            await enable_plugin.finish("「%s」%s成功" % (show_name, "启用" if enable else "停用"), at_sender=True)
    else:
        await enable_plugin.finish("插件不存在", at_sender=True)


# 添加元数据
@add_meta_data.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], arg: Message = CommandArg()):
    arg = Command.escape(str(arg))
    arg_line = arg.splitlines()
    plugin_name_input = arg_line[0]
    _plugin = search_for_plugin(plugin_name_input)
    if _plugin is None:
        await add_meta_data.send("插件不存在", at_sender=True)
    if _plugin.metadata is not None:
        await add_meta_data.send("插件源码中已存在元数据", at_sender=True)
    meta_data = {"name": arg_line[1], "description": arg_line[2], "usage": "\n".join(arg_line[3:])}
    Data(Data.globals, "plugin_metadata").set_data(_plugin.name, meta_data)
    await add_meta_data.send("「%s」元数据添加成功" % _plugin.name, at_sender=True)


# 删除元数据
@del_meta_data.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], arg: Message = CommandArg()):
    arg = Command.escape(str(arg))
    _plugin = search_for_plugin(arg)
    if _plugin is None:
        await del_meta_data.send("插件不存在", at_sender=True)
    elif _plugin.metadata is not None:
        await del_meta_data.send("插件源码中已存在元数据", at_sender=True)
    elif metadata_db.get_data(_plugin.name) is None:
        await del_meta_data.send("插件中不存在自定义元数据", at_sender=True)
    else:
        metadata_db.del_data(_plugin.name)
        await del_meta_data.send("「%s」元数据删除成功" % _plugin.name, at_sender=True)


# 隐藏插件
@hidden_plugin.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], arg: Message = CommandArg()):
    arg = Command.escape(str(arg))
    plugin_name_input = arg
    _plugin = search_for_plugin(plugin_name_input)
    if _plugin is None:
        await hidden_plugin.finish("插件不存在", at_sender=True)
    else:
        _hidden_plugin = Data(Data.globals, "plugin_data").get_data(key="hidden_plugin", default=[])
        _hidden_plugin.append(_plugin.name)
        _hidden_plugin = set(_hidden_plugin)
        Data(Data.globals, "plugin_data").set_data(key="hidden_plugin", value=list(_hidden_plugin))
        await hidden_plugin.send("插件：%s隐藏成功" % _plugin.name, at_sender=True)


# 安装插件
@install_plugin.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], arg: Message = CommandArg()):
    args = str(arg).strip().split()
    suc = False
    installed_plugin = Data(Data.globals, "liteyuki").get_data("installed_plugin", [])

    for plugin_name in args:
        try:
            _plugins = await run_sync(search_plugin_info_online)(plugin_name)
            if _plugins is None:
                await install_plugin.send("在Nonebot商店中找不到插件：%s" % plugin_name)
            else:
                _plugin = _plugins[0]
                await install_plugin.send("正在尝试安装插件：%s(%s)" % (_plugin["name"], _plugin["id"]))
                result = (await run_sync(os.popen)("pip install %s" % _plugin["id"])).read()
                if "Successfully installed" in result.splitlines()[-1]:
                    await install_plugin.send("插件：%s(%s)安装成功" % (_plugin["name"], _plugin["id"]))
                    suc = True
                    installed_plugin.append(_plugin["id"].replace("-", "_"))
                elif "Requirement already satisfied" in result.splitlines()[-1]:
                    await install_plugin.send("已安装过%s(%s)，无法重复安装" % (_plugin["name"], _plugin["id"]))
                    installed_plugin.append(_plugin["id"].replace("-", "_"))
                else:
                    await install_plugin.send("安装过程可能出现问题：%s" % result)
                installed_plugin = list(set(installed_plugin))
                Data(Data.globals, "liteyuki").set_data("installed_plugin", installed_plugin)
        except BaseException as e:
            await install_plugin.send("安装%s时出现错误:%s" % (plugin_name, traceback.format_exc()))
    if suc:
        await install_plugin.send("安装过程结束，正在重启...")
        Reloader.reload()


@online_plugin.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], arg: Message = CommandArg()):
    loaded_plugin_id_list = [_plugin.name for _plugin in get_loaded_plugins()]
    print(loaded_plugin_id_list)
    msg = "Nonebot插件商店内容：\n"
    times = 0
    if str(arg).strip() == "":
        searched_plugin_data_list = await run_sync(get_online_plugin_list)()
        sub_text = "插件商店总览"
    else:
        sub_text = "插件商店中“%s”搜索结果" % str(arg).strip()
        r1 = await run_sync(search_plugin_info_online)(str(arg).strip())
        if r1 is None:
            msg += "\n未搜索到任何内容"
            await online_plugin.finish(msg)
            searched_plugin_data_list = []
        else:
            searched_plugin_data_list = r1
    width = 1000
    line_high = 80
    head_high = 300
    side = 0.025
    bg = Canvas(base_img=Image.new(mode="RGBA", size=(width, head_high + line_high * len(searched_plugin_data_list) + int(side * width)), color=(80, 80, 80, 255)))
    bg.title = Panel(uv_size=(1, 1), box_size=(1, head_high / bg.base_img.size[1]), parent_point=(0.5, 0), point=(0.5, 0))
    bg.title.text = Text(uv_size=(1, 1), box_size=(0.618, 0.5), parent_point=(0.5, 0.3), point=(0.5, 0.5), text=[
        TextSegment("N", color=(255, 0, 0, 255)), TextSegment("one"), TextSegment("B", color=(255, 0, 0, 255)), TextSegment("ot")
    ])
    bg.title.text2 = Text(uv_size=(1, 1), box_size=(0.618, 0.3), parent_point=(0.5, 0.72), point=(0.5, 0.5), text=sub_text)
    bg.plugin_bg = Rectangle(
        uv_size=(1, 1), box_size=(1 - 2 * side, line_high * len(searched_plugin_data_list) / bg.base_img.size[1]),
        parent_point=(0.5, head_high / bg.base_img.size[1]), point=(0.5, 0),
        fillet=0, color=(0, 0, 0, 68)
    )
    plugin_bg_size = bg.get_actual_pixel_size("plugin_bg")
    for i, _plugin in enumerate(searched_plugin_data_list):
        rectangle = bg.plugin_bg.__dict__["plugin_bg_%s" % i] = Rectangle(uv_size=(1, 1), box_size=(1, line_high / plugin_bg_size[1]),
                                                                          parent_point=(0.5, i * line_high / plugin_bg_size[1]), point=(0.5, 0),
                                                                          fillet=0, color=(0, 0, 0, 128 if i % 2 == 0 else 0))
        installed = _plugin["id"].replace("-", "_") in loaded_plugin_id_list
        install_stats = "[已安装]" if installed else ""
        install_color = (0, 255, 0, 255) if installed else (255, 255, 255, 255)
        rectangle.show_name = Text(
            uv_size=(1, 1), box_size=(0.5, 0.45), parent_point=(0.05, 0.5), point=(0, 0.5), text=install_stats + _plugin["name"], dp=1, color=install_color
        )
        rectangle.id_name = Text(
            uv_size=(1, 1), box_size=(0.4, 0.45), parent_point=(0.5, 0.5), point=(0, 0.5), text=_plugin["id"], dp=1, color=install_color
        )

    await online_plugin.send(MessageSegment.image(file="file:///%s" % await run_sync(bg.export_cache)()))

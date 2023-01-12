import asyncio
import os
import traceback

import nonebot
from nonebot import get_driver
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message, GROUP_OWNER, GROUP_ADMIN, PRIVATE_FRIEND
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.utils import run_sync
from ...liteyuki_api.reloader import Reloader
from ...liteyuki_api.utils import download_file, Command

driver = get_driver()
from .autorun import *
from .plugin_api import *

bot_help = on_command(cmd="help", aliases={"帮助", "菜单", "插件列表", "全部插件"})
enable_plugin = on_command(cmd="#启用", aliases={"#停用"}, permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN | PRIVATE_FRIEND)
global_enable_plugin = on_command(cmd="#全局启用", aliases={"#全局停用"}, permission=SUPERUSER)  # 未完成
add_meta_data = on_command(cmd="#添加元数据", permission=SUPERUSER)
del_meta_data = on_command(cmd="#删除元数据", permission=SUPERUSER)  # 未完成
hidden_plugin = on_command(cmd="#隐藏插件", permission=SUPERUSER)
show_plugin = on_command(cmd="#显示插件", permission=SUPERUSER)
install_plugin = on_command("#install", aliases={"#安装插件"}, permission=SUPERUSER)
uninstall_plugin = on_command("#uninstall", aliases={"#卸载插件", "#删除插件"}, permission=SUPERUSER)
update_metadata = on_command("#更新元数据", permission=SUPERUSER)
online_plugin = on_command("#插件商店")
install_all_plugin = on_command("#安装全部", permission=SUPERUSER)


# help菜单
@bot_help.handle()
async def _(event: Union[GroupMessageEvent, PrivateMessageEvent], arg: Message = CommandArg()):
    if str(arg).strip() == "":
        try:
            if "全部插件" in event.raw_message:
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
            msg = "加载插件数：%s" % len(get_loaded_plugin_by_liteyuki())
            for _plugin in get_loaded_plugin_by_liteyuki():
                hidden_stats = "隐" if _plugin.name in _hidden_plugin else "显"
                enable_stats = "开" if check_enabled_stats(event, _plugin.name) else "关"
                p_name = _plugin.metadata.name
                msg += "\n[%s|%s]%s" % (enable_stats, hidden_stats, p_name)
            msg += "\n•使用「help插件名」来获取对应插件的使用方法\n"
            await bot_help.send(message=msg)
    else:
        "单插件帮助"
        plugin_name_input = str(arg).strip()
        plugin_ = search_for_plugin(plugin_name_input)
        if plugin_ is None:
            await bot_help.finish("插件不存在", at_sender=True)
        else:
            plugin_id = plugin_.name
            plugin_show_name = plugin_.metadata.name
            plugin_usage = plugin_.metadata.usage
            plugin_extra = plugin_.metadata.extra
            plugin_state = check_enabled_stats(event, plugin_id)
            await bot_help.finish("•%s\n「%s」\n==========\n使用方法\n%s" % (plugin_.metadata.name, plugin_.metadata.description, str(plugin_.metadata.usage)))


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
            await enable_plugin.finish(f"「{show_name}」处于强制启用状态，无法更改", at_sender=True)
        if stats == enable:
            await enable_plugin.finish(f"「{show_name}」处于{'启用' if stats else '停用'}状态，无需重复操作", at_sender=True)
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
            await enable_plugin.finish(f"「{show_name}」{'启用' if enable else '停用'}成功", at_sender=True)
    else:
        await enable_plugin.finish("插件不存在", at_sender=True)


# 添加元数据
@add_meta_data.handle()
async def _(arg: Message = CommandArg()):
    args, kwargs = Command.formatToCommand(Command.escape(str(arg)))
    if len(args) <= 1 or args[1] not in ["name", "description", "usage"]:
        await add_meta_data.finish("元数据参数有误", at_sender=True)
    plugin_name_input = args[0]
    key = args[1]
    value = args[2]
    _plugin = search_for_plugin(plugin_name_input)
    if _plugin is None:
        await add_meta_data.finish("插件不存在", at_sender=True)
    updated_data = {
        key: value
    }
    old_data: dict = metadata_db.get_data(_plugin.name, {})
    old_data.update(**updated_data)
    metadata_db.set_data(_plugin.name, old_data)
    await add_meta_data.finish(f"{_plugin.metadata.name}元数据更新成功：{key}:{value}")


# 删除元数据
@del_meta_data.handle()
async def _(arg: Message = CommandArg()):
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
async def _(arg: Message = CommandArg()):
    arg = Command.escape(str(arg))
    plugin_name_input = arg
    _plugin = search_for_plugin(plugin_name_input)
    if _plugin is None:
        await hidden_plugin.finish("插件不存在", at_sender=True)
    else:
        _hidden_plugin = Data(Data.globals, "plugin_data").get_data(key="hidden_plugin", default=[])
        if _plugin.name not in _hidden_plugin:
            _hidden_plugin.append(_plugin.name)
            Data(Data.globals, "plugin_data").set_data(key="hidden_plugin", value=list(_hidden_plugin))
            await hidden_plugin.send(f"{_plugin.metadata.name}隐藏成功", at_sender=True)
        else:
            await show_plugin.send(f"{_plugin.metadata.name}不在显示列表中", at_sender=True)

# 显示插件
@show_plugin.handle()
async def _(arg: Message = CommandArg()):
    arg = Command.escape(str(arg))
    plugin_name_input = arg
    _plugin = search_for_plugin(plugin_name_input)
    if _plugin is None:
        await show_plugin.finish("插件不存在", at_sender=True)
    else:
        _hidden_plugin = Data(Data.globals, "plugin_data").get_data(key="hidden_plugin", default=[])
        if _plugin.name in _hidden_plugin:
            _hidden_plugin.remove(_plugin.name)
            Data(Data.globals, "plugin_data").set_data(key="hidden_plugin", value=list(_hidden_plugin))
            await show_plugin.send(f"{_plugin.metadata.name}显示成功", at_sender=True)
        else:
            await show_plugin.send(f"{_plugin.metadata.name}不在隐藏插表中", at_sender=True)

# 安装插件
@install_plugin.handle()
async def _(arg: Message = CommandArg()):
    args = str(arg).strip().split()
    suc = False
    installed_plugin = Data(Data.globals, "liteyuki").get_data("installed_plugin", [])
    search_list = get_online_plugin_list()
    for plugin_name in args:
        try:
            _plugins = await run_sync(search_plugin_info_online)(plugin_name, search_list)
            if _plugins is None:
                await install_plugin.send(f"在Nonebot商店中找不到插件：{plugin_name}")
            else:
                _plugin = _plugins[0]
                await run_sync(os.system)(f"pip3 install {_plugin['id']}")
                module_name = _plugin["id"].replace("-", "_")
                loaded_list_before_load = [_plugin.name for _plugin in get_loaded_plugins()]
                if module_name in loaded_list_before_load:
                    await install_plugin.send(f"{_plugin['name']}({_plugin['id']})已装载，无需重复安装")
                else:
                    nonebot.load_plugin(module_name)
                    loaded_list_after_load = [_plugin.name for _plugin in get_loaded_plugins()]
                    if module_name in loaded_list_after_load:
                        installed_plugin.append(module_name)
                        await install_plugin.send(f"{_plugin['name']}({_plugin['id']})安装成功")
                        suc = True
                    else:
                        await install_plugin.send(f"{_plugin['name']}({_plugin['id']})本身存在问题，安装失败，请联系插件作者")
                if suc:
                    installed_plugin = list(set(installed_plugin))
                    Data(Data.globals, "liteyuki").set_data("installed_plugin", installed_plugin)
        except BaseException as e:
            await install_plugin.send("安装时出现错误:%s" % (traceback.format_exc()))


# 插件全装
@install_all_plugin.handle()
async def _():
    suc = []
    failed = []
    installed_plugin = Data(Data.globals, "liteyuki").get_data("installed_plugin", [])
    for plugin_data in get_online_plugin_list():
        module_name = plugin_data["id"].replace("-", "_")
        try:
            await run_sync(os.system)(f"pip3 install {plugin_data['id']}")
            nonebot.load_plugin(module_name)
            loaded_list = [_plugin.name for _plugin in get_loaded_plugins()]
            if module_name in loaded_list:
                installed_plugin.append(module_name)
                suc.append(plugin_data)
                Data(Data.globals, "liteyuki").set_data("installed_plugin", list(set(installed_plugin)))
        except BaseException:
            failed.append(plugin_data)
    msg = "安装成功："
    for suc_plug in suc:
        msg += f"\n- {suc_plug['name']}({suc_plug['id']})"
    msg += "\n安装失败:"
    for failed_plug in failed:
        msg += f"\n- {failed_plug['name']}({failed_plug['id']})"
    await install_all_plugin.send(msg + "\n正在重启...")
    Reloader.reload()


@uninstall_plugin.handle()
async def _(arg: Message = CommandArg()):
    args = str(arg).strip().split()
    suc = False
    installed_plugin: list = Data(Data.globals, "liteyuki").get_data("installed_plugin", [])
    loaded_list = [_plugin.name for _plugin in get_loaded_plugins()]
    for plugin_name in args:
        searched_plugin = search_for_plugin(plugin_name)
        if searched_plugin is not None:
            if searched_plugin.name in installed_plugin:
                installed_plugin.remove(searched_plugin.name)
                await run_sync(os.system)(f"pip uninstall {searched_plugin.name} -y")
                suc = True
                await uninstall_plugin.send(f"{searched_plugin.metadata.name}({searched_plugin.name})卸载成功")
            else:
                await uninstall_plugin.send(f"{searched_plugin.metadata.name}({searched_plugin.name})卸载失败：轻雪插件和手动安装的插件不可被卸载")
        else:
            await uninstall_plugin.send("未找到插件或插件未加载")
    Data(Data.globals, "liteyuki").set_data("installed_plugin", installed_plugin)
    if suc:
        await uninstall_plugin.send("卸载完成正在重启...")
    Reloader.reload()


@online_plugin.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], arg: Message = CommandArg()):
    loaded_plugin_id_list = [_plugin.name for _plugin in get_loaded_plugins()]
    msg = "Nonebot插件商店内容：\n"
    times = 0
    if str(arg).strip() == "":
        searched_plugin_data_list = await run_sync(get_online_plugin_list)()
        sub_text = "插件商店总览"
    else:
        sub_text = f"插件商店中“{str(arg).strip()}”搜索结果"
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
        rectangle = bg.plugin_bg.__dict__[f"plugin_bg_{i}"] = Rectangle(uv_size=(1, 1), box_size=(1, line_high / plugin_bg_size[1]),
                                                                        parent_point=(0.5, i * line_high / plugin_bg_size[1]), point=(0.5, 0),
                                                                        fillet=0, color=(0, 0, 0, 128 if i % 2 == 0 else 0))
        installed = _plugin["id"].replace("-", "_") in loaded_plugin_id_list
        install_stats = "[已装载]" if installed else ""
        install_color = (0, 255, 0, 255) if installed else (255, 255, 255, 255)
        rectangle.show_name = Text(
            uv_size=(1, 1), box_size=(0.5, 0.45), parent_point=(0.05, 0.5), point=(0, 0.5), text=install_stats + _plugin["name"], dp=1, color=install_color
        )
        rectangle.id_name = Text(
            uv_size=(1, 1), box_size=(0.4, 0.45), parent_point=(0.5, 0.5), point=(0, 0.5), text=_plugin["id"], dp=1, color=install_color
        )

    await online_plugin.send(MessageSegment.image(file=f"file:///{await run_sync(bg.export_cache)()}"))

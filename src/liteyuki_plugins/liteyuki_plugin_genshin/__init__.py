import traceback
from datetime import time

from PIL import ImageEnhance
from nonebot import on_command, on_message
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from .uid import set_uid_handle
from .user_card import *
from .character_info import *
from .utils import *
from .resource import *

set_uid = on_command(cmd="绑定uid", aliases={"#绑定uid", "绑定UID", "#绑定UID"}, block=True)
hid_uid = on_command(cmd="遮挡uid", block=True)
update_resource = on_command(cmd="原神资源更新", block=True, permission=SUPERUSER)
character_img = on_message(rule=args_end_with("立绘"), block=True)
add_aliases = on_command(cmd="添加别称", block=True, permission=SUPERUSER)
character_card = on_message(rule=args_end_with("面板"))


@character_card.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    await character_card_handle(bot, event, character_card)


@set_uid.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], args: Message = CommandArg()):
    await set_uid_handle(bot, event, set_uid, args)


@hid_uid.handle()
async def _(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    raw_stats = Data(Data.users, event.user_id).get_data(key="genshin.hid_uid", default=False)
    Data(Data.users, event.user_id).set_data(key="genshin.hid_uid", value=not raw_stats)
    await hid_uid.finish("已%suid遮挡" % ("关闭" if raw_stats else "开启"), at_sender=True)


@update_resource.handle()
async def _():

    for file, url in resource_pool.items():
        await update_resource.send("正在更新：%s" % file)
        await run_sync(download_file)(url, os.path.join(Path.root, file))
    await update_resource.finish("资源更新完成", at_sender=True)


@add_aliases.handle()
async def _(args: Message = CommandArg()):
    file_pool = await load_resource(add_aliases)
    args, kwargs = Command.formatToCommand(cmd=str(args))
    identify_name = args[0]
    if len(args) > 1:
        _break = False
        aliases = args[1:]
        hash_id = str()
        for lang, lang_data in file_pool["loc.json"].items():
            for hash_id, entry in lang_data.items():
                if identify_name == entry:
                    _break = True
                    break
            if _break:
                break
        else:
            await add_aliases.finish(data_lost, at_sender=True)
        character_hash_id = hash_id

        character_id = 0
        character = {}
        for character_id, character in file_pool["characters_enka.json"].items():
            if int(hash_id) == character["NameTextMapHash"]:
                character_id = character_id
                break
        else:
            await add_aliases.finish(data_lost, at_sender=True)

        data = Data(Data.globals, "genshin_game_data").get_data(key="character_aliases", default={})
        if hash_id in data:
            data[hash_id] += aliases
        else:
            data[hash_id] = aliases
        data[hash_id] = list(set(data[hash_id]))
        Data(Data.globals, "genshin_game_data").set_data(key="character_aliases", value=data)
        await add_aliases.finish("别称添加完成：%s(%s)：%s" % (identify_name, hash_id, aliases))

    else:
        await add_aliases.finish("请至少添加一个别称", at_sender=True)


@character_img.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    file_pool = await load_resource(character_img)
    args, kwargs = Command.formatToCommand(event.raw_message)
    character_name_input = args[0].strip().replace("立绘", "").replace("#", "")
    if character_name_input == "更新":
        raise IgnoredException
    _break = False
    lang = "zh-CN"
    hd = kwargs.get("hd", "false")
    hash_id = str()
    entry = str()

    """旅行者判定"""
    if character_name_input in ["荧", "空"]:
        character_name_input = "旅行者"

    """遍历loc.json从输入的角色名查询词条的hash_id"""
    for lang, lang_data in file_pool["loc.json"].items():
        for hash_id, entry in lang_data.items():
            if character_name_input == entry:
                chinese_name = file_pool["loc.json"]["zh-CN"].get(str(hash_id))
                _break = True
                break
        if _break:
            break
    else:
        """从别称数据中查找hash_id"""
        for hash_id, aliases_list in Data(Data.globals, "genshin_game_data").get_data(key="character_aliases", default={}).items():
            if character_name_input in aliases_list:
                chinese_name = file_pool["loc.json"]["zh-CN"].get(str(hash_id))
                break
        else:
            if os.path.exists(os.path.join(Path.res, "textures/genshin/%s.png" % character_name_input)):
                chinese_name = character_name_input
            else:
                await character_img.finish("角色名不存在或资源未更新", at_sender=True)

    await character_img.finish(MessageSegment.image(file="file:///%s" % os.path.join(Path.res, "textures/genshin/%s.png" % chinese_name)))


__plugin_meta__ = PluginMetadata(
    name="原神查询",
    description="原神角色面板查询",
    usage="命令：\n"
          "•「原神资源更新」更新本地的资源文件\n\n"
          "•「xx面板」查看角色面板\n"
          "•「原神数据|更新数据 [uid]」更新原神角色展示框中的数据,默认为绑定的uid\n"
          "•「绑定uid xxx」绑定自己的uid\n"
          "•「添加别称 角色名 别称1 别称2...」在查询面板时可以用别称查询\n"
          "•「xx立绘」获取角色立绘图\n"
          "•可以在「绑定uid」空格后接「lang=xx」来指定语言，可选的语言有：\n"
          "en ru vi th pt ko ja id fr es de zh-TW zh-CN it tr\n"
          "•可在「xx面板」、「xx角色数据]空格后接「hd=true」来生成高清面板\n"
          "•可在「xx面板」、「xx角色数据]空格后接「uid=000000000」来指定uid\n",
    extra={
        "default_enable": True,
        "liteyuki_resource_git": resource_git,
        "liteyuki_resource": resource,
        "liteyuki_plugin": True
    }
)

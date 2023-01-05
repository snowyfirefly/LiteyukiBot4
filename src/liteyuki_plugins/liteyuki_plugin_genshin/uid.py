import time
from nonebot.utils import run_sync

from .utils import uid_info_error, servers
from ...liteyuki_api.data import Data
from ...liteyuki_api.utils import Command, simple_request_get


async def set_uid_handle(bot, event, matcher, args):
    set_uid = matcher
    args, kwargs = Command.formatToCommand(str(args).strip())
    if not args[0].isdigit():
        await set_uid.finish("uid格式错误", at_sender=True)
    else:
        uid = int(args[0])
        player_data = (await run_sync(simple_request_get)(f"https://enka.network/u/{uid}/__data.json")).json()

        if "playerInfo" not in player_data:
            await set_uid.finish(uid_info_error, at_sender=True)
        else:
            playerInfo = player_data["playerInfo"]
            lang = kwargs.get("lang", "zh-CN")
            Data(Data.users, event.user_id).set_data(key="genshin.uid", value=uid)
            Data(Data.users, event.user_id).set_data(key="genshin.lang", value=lang)
            await set_uid.finish("绑定成功：%s（%s  Lv.%s）" % (playerInfo["nickname"], servers.get(str(uid)[0], "Unknown Server"), playerInfo["level"]), at_sender=True)
            if len(player_data.get("avatarInfoList", [])) > 0:
                player_data["time"] = tuple(list(time.localtime())[0:5])
                Data(Data.globals, "genshin_player_data").set_data(str(uid), player_data)

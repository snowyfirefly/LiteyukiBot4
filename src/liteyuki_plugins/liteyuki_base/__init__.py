from nonebot.plugin import PluginMetadata
from .autorun import *
from .resource import *
from .system import *

echo = on_command(cmd="echo", permission=SUPERUSER)
liteyuki = on_command(cmd="liteyuki", permission=SUPERUSER)
download_resource = on_command(cmd="下载资源", aliases={"更新资源"}, permission=SUPERUSER)


@echo.handle()
async def _(args: Message = CommandArg()):
    await echo.send(Message(Command.escape(str(args))))


@liteyuki.handle()
async def _(bot: Bot):
    await liteyuki.finish(f"轻雪测试成功：{bot.self_id}\n轻雪服务端id：{Data(Data.globals, 'liteyuki').get_data('liteyuki_id', '暂无')}")


@download_resource.handle()
async def _():
    pass


__plugin_meta__ = PluginMetadata(
    name="轻雪底层基础",
    description="以维持轻雪的正常运行，无法关闭",
    usage='•「liteyuki」测试Bot\n\n'
          '•「echo 消息」Bot复读，可转CQ码\n\n'
          '•「#更新/update/轻雪更新」手动更新（仅私聊）\n\n'
          '•「#重启/reboot/轻雪重启」手动重启\n\n'
          '•「#状态/state/轻雪状态」查看状态\n\n'
          '•「#下载资源/更新资源」解决自动资源下载失败的问题\n\n'
          '•「#检查更新」检查当前版本是否为最新\n\n'
          '•「#启用/停用自动更新」管理自动更新\n\n'
          '•「#清除缓存」清楚无关紧要的缓存文件\n\n'
          '•「#屏蔽用户/取消屏蔽 <id1> <id2>...」添加屏蔽用户，多个id空格\n\n'
          '•「#api api_name **params」直接调用gocqAPI并获取返回结果\n\n'
          '•「#导出数据」仅私聊生效，导出liteyuki.xxx.db的数据库文件（仅私聊）\n\n'
          '•「liteyuki.xxx.db」将此文件发送给Bot导入数据',
    extra={
        "liteyuki_plugin": True,
        "liteyuki_resource_git": resource_git
    }
)

from .manager import *
from .autorun import *
from .resource import resource_git
from nonebot.plugin.plugin import plugins, PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="轻雪插件管理",
    description="轻雪内置的插件管理",
    usage="命令：\n"
          "•「help」获取菜单/插件列表\n\n"
          "•「help <插件>」获取插件使用方法\n\n"
          "•「#启用/停用<插件>」当前会话中插件开关(仅群管/超级用户/私聊)\n\n"
          '•「#安装插件/卸载插件 <插件1> <插件2>...」从Nonebot商店搜索并安装/卸载插件（多个用空格分隔）\n\n'
          '•「#安装全部插件」把整个Nonebot商店搬到本地，不建议\n\n'
          "•「#更新元数据」从商店插件中更新本地插件的元数据\n\n"
          "•「#添加/删除元数据 <插件> <键> <值>」添加自定义元数据，详细请查看nb官网\n\n"
          "•「#隐藏插件/显示插件 <插件>」将部分后台插件隐藏起来，可使用「全部插件」查看所有插件\n\n"
          "•「#插件商店 [可选关键词]」查看/搜索商店中的插件\n\n"
          "•「#全局启用/停用 <插件>」全局插件开关\n\n",
    extra={
        "force_enable": True,
        "liteyuki_resource_git": resource_git,
        "liteyuki_plugin": True
    }
)

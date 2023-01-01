from .manager import *
from .autorun import *
from .resource import resource_git
from nonebot.plugin.plugin import plugins, PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="轻雪插件管理",
    description="轻雪内置的插件管理",
    usage="命令：\n"
          "•「help」获取插件列表\n\n"
          "•「help插件名」获取插件使用方法\n\n"
          "•「#启用/停用xxx」插件开关\n\n"
          '•「#安装插件 插件名...」从Nonebot商店搜索并安装插件（多个用空格分隔）\n\n'
          '•「#卸载插件 插件名...」卸载插件（空格分隔）\n\n'
          '•「#安装全部插件」把整个Nonebot商店搬到本地\n\n'
          "•「#添加插件元数据 name description usage extra」\n\n"
          "•「#隐藏插件xxx」将部分后台插件隐藏起来，可使用「全部插件」查看所有插件\n\n"
          "•「#插件商店 [可选关键词]」查看/搜索商店中的插件",
    extra={
        "force_enable": True,
        "liteyuki_resource_git": resource_git,
        "liteyuki_plugin": True
    }
)

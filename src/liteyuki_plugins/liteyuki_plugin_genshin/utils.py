import json
import os

from PIL import Image

from .resource import resource
from ...liteyuki_api.config import Path
from ...liteyuki_api.utils import clamp, download_file, generate_signature

liteyuki_sign = generate_signature + "    Powered by Enka.Network"
data_lost = "数据缺失，请先发送「原神资源更新」以更新资源"
uid_info_error = "UID信息不存在或Enka不稳定请求失败，请稍后再试"
resource_pool = resource

"""元素英文希腊语映射表"""
elements = {
    "Rock": "geo",  # 岩元素
    "Wind": "Anemo",  # 风元素
    "Water": "Hydro",  # 水元素
    "Electric": "Electro",  # 雷元素
    "Fire": "Pyro",  # 火元素
    "Ice": "Cryo",  # 冰元素
    "Grass": "Dendro",  # 草元素
    "Unknown": "Unknown"  # 万能元素
}
servers = {
    "1": "天空岛",
    "2": "天空岛",
    "5": "世界树",
    "6": "America",
    "7": "Europe",
    "8": "Asia",
    "9": "TW,HK,Mo"
}


def wish_img_crop(img: Image.Image):
    w, h = img.size
    if w > h:
        img = img.crop(((w - h) // 2, 0, (w + h) // 2, h))
    elif w < h:
        img = img.crop((0, (h - w) // 2, w, (h + w) // 2))
    img = img.convert("RGBA")
    img = img.resize((1000, 1000))
    x_size = 320
    up_size, down_size = 100, 150
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            if x in range(0, x_size) or x in range(img.size[0] - x_size, img.size[0]):
                p = list(img.getpixel((x, y)))
                """距离边缘的距离"""
                cd = min(abs(x), abs(x - img.size[0]))
                light = clamp(cd / x_size, 0, 1)
                p[3] = int(p[3] * light ** 2)
                img.putpixel((x, y), tuple(p))
            if y in range(0, up_size):
                p = list(img.getpixel((x, y)))
                """距离边缘的距离"""
                cd = y
                light = clamp(cd / up_size, 0, 1)
                p[3] = int(p[3] * light ** 2)
                img.putpixel((x, y), tuple(p))
            if y in range(img.size[1] - down_size, img.size[1]):
                p = list(img.getpixel((x, y)))
                """距离边缘的距离"""
                cd = abs(img.size[1] - y)
                light = clamp(cd / down_size, 0, 1)
                p[3] = int(p[3] * light ** 2)
                img.putpixel((x, y), tuple(p))

    return img


def get_lang_word(key: str, lang: str = "zh-CN", loc=None):
    if loc is None:
        loc = {}
    return loc.get(lang, loc["en"]).get(key, "Id not existing")


async def load_resource(matcher):
    file_pool = {}
    for f in resource_pool.keys():
        whole_path = os.path.join(Path.root, f)
        if os.path.exists(whole_path):
            file_pool[os.path.basename(f)] = json.load(open(whole_path, encoding="utf-8"))
        else:
            await matcher.finish(data_lost + whole_path, at_sender=True)
    return file_pool


def enka_resource_detect(texture: str):
    # 检测enka图片资源是否存在于本地，不存在就下载，无需带png
    if not os.path.exists(os.path.join(Path.cache, "genshin", "%s.png" % texture)):
        download_file(url="https://enka.network/ui/%s.png" % texture,
                      file=os.path.join(Path.cache, "genshin", "%s.png" % texture))
    else:
        pass

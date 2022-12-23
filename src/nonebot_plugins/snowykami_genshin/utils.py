import os

from PIL import Image

from ...liteyuki_api.config import Path
from ...liteyuki_api.utils import clamp, download_file

liteyuki_sign = "Generated by Liteyuki-Bot   Powered by Enka.Network"
data_lost = "数据缺失，请先发送'原神资源更新'以更新资源"
resource_pool = {
    "characters.json": "https://raw.kgithub.com/mrwan200/enkanetwork.py-data/master/exports/data/characters.json",
    "characters_enka.json": "https://raw.kgithub.com/EnkaNetwork/API-docs/master/store/characters.json",
    "loc.json": "https://raw.kgithub.com/EnkaNetwork/API-docs/master/store/loc.json",
    "AvatarExcelConfigData.json": "https://git.crepe.moe/grasscutters/Grasscutter_Resources/-/raw/3.3/Resources/ExcelBinOutput/AvatarExcelConfigData.json?inline=false",
    "AvatarSkillDepotExcelConfigData.json": "https://git.crepe.moe/grasscutters/Grasscutter_Resources/-/raw/3.3/Resources/ExcelBinOutput/AvatarSkillDepotExcelConfigData.json"
                                            "?inline=false",
}
elements = {
    "Rock": "geo",
    "Wind": "Anemo",
    "Water": "Hydro",
    "Electric": "Electro",
    "Fire": "Pyro",
    "Ice": "Cryo",
    "Grass": "Dendro",
    "Unknown": "Unknown"
}


def wish_img_crop(img: Image.Image):
    w, h = img.size
    if w > h:
        img = img.crop(((w - h) // 2, 0, (w + h) // 2, h))
    elif w < h:
        img = img.crop((0, (h - w) // 2, w, (h + w) // 2))
    img = img.resize((1000, 1000))
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            if x in range(0, 300) or x in range(700, 1000):
                p = list(img.getpixel((x, y)))
                pn = []
                k = clamp((1 - (abs(500 - x) - 200) / 330), 0, 1)
                for rgb in p[0:3]:
                    pn.append(int(rgb * k))
                pn.append(int(p[-1] * k))
                img.putpixel((x, y), tuple(pn))
            if y in range(0, 150) or y in range(850, 1000):
                p = list(img.getpixel((x, y)))
                pn = []
                k = clamp((1 - (abs(500 - y) - 350) / 160), 0, 1)
                for rgb in p[0:3]:
                    pn.append(int(rgb * k))
                pn.append(int(p[-1] * k))
                img.putpixel((x, y), tuple(pn))

    return img


def get_lang_word(key: str, lang: str = "zh-CN", loc=None):
    if loc is None:
        loc = {}
    return loc.get(lang, loc["zh-CN"]).get(key, "None")


def resource_detect(texture: str):
    # 检测enka图片资源是否存在于本地，不存在就下载，无需带png
    if not os.path.exists(os.path.join(Path.cache, "genshin", "%s.png" % texture)):
        download_file(url="https://enka.network/ui/%s.png" % texture,
                      file=os.path.join(Path.cache, "genshin", "%s.png" % texture))
    else:
        pass

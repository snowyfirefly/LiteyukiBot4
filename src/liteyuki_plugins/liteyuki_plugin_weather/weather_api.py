# 和风天气接口
from typing import Type

import jieba
from nonebot.internal.matcher import Matcher

from .model import *
from ...liteyuki_api.utils import *
from ...liteyuki_api.data import Data


def jieba_cut(word: str) -> list:
    """
    异步结巴分词，避免占用

    :param word:
    :return:
    """
    return jieba.lcut(word)


async def key_check(matcher: Type[Matcher]):
    if Data(Data.globals, "qweather").get_data("key") is None:
        await matcher.finish("未配置key，轻雪天气部分查询服务无法运行！")


def get_location(keyword: str, **kwargs) -> List[Location] | None:
    key, key_type = Data(Data.globals, "qweather").get_many_data({"key": None, "key_type": None})
    url = "https://geoapi.qweather.com/v2/city/lookup?"
    params = {"key": key, "location": keyword}
    params.update(kwargs)
    resp = simple_request_get(url, params=params)
    if resp.json()["code"] == "200":
        return [Location(**location) for location in resp.json()["location"]]

    word_list = keyword.split()
    if len(word_list) >= 2:
        params["location"] = word_list[-1]
        params["adm"] = word_list[0]
        resp = simple_request_get(url, params=params)
        if resp.json()["code"] == "200":
            return [Location(**location) for location in resp.json()["location"]]

    word_list = jieba_cut(keyword)
    if len(word_list) >= 2:
        params["location"] = word_list[-1]
        params["adm"] = word_list[0]
        resp = simple_request_get(url, params=params)
        if resp.json()["code"] == "200":
            return [Location(**location) for location in resp.json()["location"]]
    return None


def get_weather():
    pass

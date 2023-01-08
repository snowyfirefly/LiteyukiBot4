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


def city_lookup(keyword: str, **kwargs) -> CityLookup | None:
    """
    建议异步执行
    查询不到结果时返回None

    :param keyword:
    :param kwargs:
    :return:
    """
    key, key_type = Data(Data.globals, "qweather").get_many_data({"key": None, "key_type": None})
    url = "https://geoapi.qweather.com/v2/city/lookup?"
    params = {"key": key, "location": keyword}
    params.update(kwargs)
    resp = simple_request_get(url, params=params)
    if resp.json()["code"] == "200":
        return CityLookup(**resp.json())

    word_list = keyword.split()
    if len(word_list) >= 2:
        params["location"] = word_list[-1]
        params["adm"] = word_list[0]
        resp = simple_request_get(url, params=params)
        if resp.json()["code"] == "200":
            return CityLookup(**resp.json())

    word_list = jieba_cut(keyword)
    if len(word_list) >= 2:
        params["location"] = word_list[-1]
        params["adm"] = word_list[0]
        resp = simple_request_get(url, params=params)
        if resp.json()["code"] == "200":
            return CityLookup(**resp.json())
    return None


def weather_now(location: str, lang="zh-hans", unit="m") -> WeatherNow:
    """
    建议异步执行
    :param location: id或坐标
    :param lang:
    :param unit:
    :return:
    """
    key, key_type = Data(Data.globals, "qweather").get_many_data({"key": None, "key_type": None})
    url = f"https://{'dev' if key_type == 'dev' else ''}api.qweather.com/v7/weather/now?"
    resp = simple_request_get(url, params={"location": location, "lang": lang, "unit": unit, "key": key})
    if resp.json()["code"] == "200":
        return WeatherNow(**resp.json())

def weather_daily(location: str, lang="zh-hans", unit="m") -> WeatherDaily:
    key, key_type = Data(Data.globals, "qweather").get_many_data({"key": None, "key_type": None})
    url = f"https://{'dev' if key_type == 'dev' else ''}api.qweather.com/v7/weather/7d?"
    resp = simple_request_get(url, params={"location": location, "lang": lang, "unit": unit, "key": key})
    if resp.json()["code"] == "200":
        return WeatherDaily(**resp.json())

def air_now(location: str, lang="zh-hans", unit="m") -> AirNow:
    key, key_type = Data(Data.globals, "qweather").get_many_data({"key": None, "key_type": None})
    url = f"https://{'dev' if key_type == 'dev' else ''}api.qweather.com/v7/air/now?"
    resp = simple_request_get(url, params={"location": location, "lang": lang, "unit": unit, "key": key})
    if resp.json()["code"] == "200":
        return AirNow(**resp.json())

def weather_hourly(location: str, lang="zh-hans", unit="m") -> WeatherHourly:
    key, key_type = Data(Data.globals, "qweather").get_many_data({"key": None, "key_type": None})
    url = f"https://{'dev' if key_type == 'dev' else ''}api.qweather.com/v7/weather/24h?"
    resp = simple_request_get(url, params={"location": location, "lang": lang, "unit": unit, "key": key})
    if resp.json()["code"] == "200":
        return WeatherHourly(**resp.json())

from typing import List

from pydantic import BaseModel


class Location(BaseModel):
    name: str
    id: str
    lat: str
    lon: str
    adm2: str
    adm1: str
    country: str
    tz: str
    utcOffset: str
    isDst: str
    type: str
    rank: str
    fxLink: str
    sources: str = str()
    license: str = str()


class CityLookup(BaseModel):
    code: str
    location: List[Location]


# 实时天气
class Now(BaseModel):
    obsTime: str = str()
    temp: str = str()
    feelsLike: str = str()
    icon: str = str()
    text: str = str()
    wind360: str = str()
    windDir: str = str()
    windScale: str = str()
    windSpeed: str = str()
    humidity: str = str()
    precip: str = str()
    pressure: str = str()
    vis: str = str()
    cloud: str = str()
    dew: str = str()


class WeatherNow(BaseModel):
    code: str
    updateTime: str
    fxLink: str
    now: "Now"


# 逐天天气
class Daily(BaseModel):
    fxDate: str
    sunrise: str = str()
    sunset: str = str()
    moonrise: str = str()
    moonset: str = str()
    moonPhase: str
    moonPhaseIcon: str
    tempMax: str
    tempMin: str
    iconDay: str
    textDay: str
    iconNight: str
    textNight: str
    wind360Day: str
    windDirDay: str
    windScaleDay: str
    windSpeedDay: str
    wind360Night: str
    windDirNight: str
    windScaleNight: str
    windSpeedNight: str
    humidity: str
    precip: str
    vis: str
    cloud: str = str()
    uvIndex: str


class WeatherDaily(BaseModel):
    code: str
    updateTime: str
    fxLink: str
    daily: List[Daily]


# 逐小时天气
class Hourly(BaseModel):
    fxTime: str
    temp: str
    icon: str
    text: str
    wind360: str
    windDir: str
    windScale: str
    windSpeed: str
    humidity: str
    pop: str = str()
    precip: str
    pressure: str
    cloud: str = str()
    dew: str = str()


class WeatherHourly(BaseModel):
    code: str
    updateTime: str
    fxLink: str
    hourly: List[Hourly]


# 分钟级降水
class Minutely(BaseModel):
    fxTime: str
    precip: str
    type: str


class MinutelyPrecipitation(BaseModel):
    code: str
    updateTime: str
    fxLink: str
    summary: str
    minutely: List[Minutely]

# 格点天气
class GridWeather(BaseModel):
    code: str
    updateTime: str
    fxLink: str
    now: Now


class AirNowNow(BaseModel):
    pubTime: str
    aqi: str
    level: str
    category: str
    primary: str
    pm10: str
    pm2p5: str
    no2: str
    so2: str
    co: str
    o3: str

class AirNow(BaseModel):
    code: str = ""
    updateTime: str
    fxLink: str
    now: AirNowNow

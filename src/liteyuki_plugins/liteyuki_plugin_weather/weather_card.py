import random

from .model import *
from ...liteyuki_api.canvas import *
from .utils import *
from .text import *
from PIL import Image

from ...liteyuki_api.utils import download_file, generate_signature

default_font = Font.HYWH_85w


def generate_weather_now(location: Location, weather_now: WeatherNow, weather_hourly: WeatherHourly, air: AirNow, unit="℃", lang="zh-hans") -> Canvas:
    bg_size = (1080, 2400)
    side_width = 25
    down_width = 50
    distance_height = 25
    base_fillet = 15
    base_cover = (0, 0, 0, 128)
    drawing_path = os.path.join(Path.data, "liteyuki/drawing")

    distance_height_scale = distance_height / (bg_size[1] - 2 * side_width)
    part_now_height_scale = 0.27
    tag_part_height_scale = 0.13
    hourly_temp_part_height_scale = 0.2

    if len(os.listdir(drawing_path)) > 0:
        base_img = Utils.central_clip_by_ratio(Image.open(os.path.join(Path.data, "liteyuki/drawing/%s" % random.choice(os.listdir(drawing_path)))), bg_size)
    else:
        base_img = Image.new(mode="RGBA", size=bg_size, color=(255, 255, 255, 255))
    canvas = Canvas(base_img)
    canvas.content = Panel(
        uv_size=bg_size,
        box_size=(bg_size[0] - 2 * side_width, bg_size[1] - side_width - down_width),
        parent_point=(0.5, side_width / bg_size[1]),
        point=(0.5, 0)
    )
    # Part Now Weather
    canvas.content.now_part = Rectangle(
        uv_size=(1, 1), box_size=(1, part_now_height_scale), parent_point=(0.5, 0), point=(0.5, 0), color=base_cover, fillet=base_fillet
    )
    country_province_name, location_name = format_location_show_name_2([location.country, location.adm1, location.adm2, location.name])
    # 国家 中国 重庆市
    canvas.content.now_part.cp_name = Text(
        uv_size=(1, 1), box_size=(0.8, 0.085), parent_point=(0.025, 0.04), point=(0, 0),
        text=country_province_name, font=default_font, color=(220, 220, 220, 255), anchor="lt"
    )
    # 地点名 沙坪坝
    canvas.content.now_part.loc_name = Text(
        uv_size=(1, 1), box_size=(0.75, 0.15), parent_point=(0.5, 0.19), point=(0.5, 0),
        text=location_name, font=default_font, anchor="lt"
    )
    state_icon_path = os.path.join(Path.cache, f"weather/{weather_now.now.icon}.png")
    download_file(f"https://a.hecdn.net/img/common/icon/202106d/{weather_now.now.icon}.png", os.path.join(Path.cache, f"weather/{weather_now.now.icon}.png"), detect=True)
    # 状态区
    canvas.content.now_part.state_icon = Img(
        uv_size=(1, 1), box_size=(0.5, 0.5), parent_point=(0.5, 0.58), point=(1, 0.5),
        img=Image.open(state_icon_path)
    )
    canvas.content.now_part.temp = Text(
        uv_size=(1, 1), box_size=(0.5, 0.15), parent_point=(0.5, 0.48), point=(0, 0.5),
        text=f"{weather_now.now.temp}{unit}", font=default_font
    )
    canvas.content.now_part.state_text = Text(
        uv_size=(1, 1), box_size=(0.5, 0.12), parent_point=(0.5, 0.68), point=(0, 0.5),
        text=weather_now.now.text, font=default_font
    )

    canvas.content.tag_part = Rectangle(
        uv_size=(1, 1), box_size=(1, tag_part_height_scale), parent_point=(0.5, part_now_height_scale + distance_height_scale), point=(0.5, 0), color=base_cover, fillet=base_fillet
    )
    if air is not None:
        AQI = int(air.now.aqi)
        if AQI < 75:
            arc_color = Color.hex2dec("FF55AF7B")
        elif AQI < 150:
            arc_color = Color.hex2dec("FFFAC230")
        elif AQI < 300:
            arc_color = Color.hex2dec("FFFA9D5A")
        else:
            arc_color = Color.hex2dec("FFEB4537")
        canvas.content.now_part.aqi = Text(
            uv_size=(1, 1), box_size=(0.5, 0.1), parent_point=(0.5, 0.89), point=(0.5, 0.5),
            text=f" AQI {AQI} {air.now.category} ", font=default_font, fill=arc_color, fillet=8
        )

        props = [
            {
                "icon": os.path.join(Path.res, "textures/genshin/FIGHT_PROP_WIND_ADD_HURT.png"),
                "name": {
                    "zh-hans": f"{weather_now.now.windDir} {weather_now.now.windScale}级",
                    "en": f"{weather_now.now.windDir} Lv.{weather_now.now.windScale}"
                }
            },
            {
                "icon": os.path.join(Path.res, "textures/genshin/FIGHT_PROP_CHARGE_EFFICIENCY.png"),
                "name": {
                    "zh-hans": f"风向 {weather_now.now.wind360}° {weather_now.now.windSpeed}km/h",
                    "en": f"Wind {weather_now.now.wind360}° {weather_now.now.windSpeed}km/h",
                }
            },
            {
                "icon": os.path.join(Path.res, "textures/genshin/FIGHT_PROP_WATER_ADD_HURT.png"),
                "name": {
                    "zh-hans": f"相对湿度 {weather_now.now.humidity}%",
                    "en": f"Humidity {weather_now.now.humidity}%"
                }
            },
            {
                "icon": os.path.join(Path.res, "textures/genshin/FIGHT_PROP_HEAL_ADD.png"),
                "name": {
                    "zh-hans": f"体感温度 {weather_now.now.feelsLike}{unit}",
                    "en": f"FeelTemp {weather_now.now.feelsLike}{unit}"
                }
            },
            {
                "icon": os.path.join(Path.res, "textures/genshin/FIGHT_PROP_HP.png"),
                "name": {
                    "zh-hans": f"小时降水量 {weather_now.now.precip}mm",
                    "en": f"Precip {weather_now.now.precip}mm"
                }
            },
            {
                "icon": os.path.join(Path.res, "textures/genshin/FIGHT_PROP_CRITICAL_HURT.png"),
                "name": {
                    "zh-hans": f"大气压强 {weather_now.now.pressure}hPa",
                    "en": f"Atm {weather_now.now.pressure}hPa"
                }
            }
        ]
        count_for_each_row = 2
        prop_dx = 1 / count_for_each_row
        prop_dy = 1 / (len(props) // count_for_each_row)
        for prop_i, prop in enumerate(props):
            row = prop_i // count_for_each_row
            columns = prop_i % count_for_each_row
            prop_panel = canvas.content.tag_part.__dict__["prop_%s" % prop_i] = Panel(
                uv_size=(1, 1), box_size=(prop_dx, prop_dy), parent_point=(prop_dx * columns, prop_dy * row), point=(0, 0)
            )
            prop_panel.icon = Img(
                uv_size=(1, 1), box_size=(0.6, 0.5), parent_point=(0.11, 0.5), point=(0.5, 0.5), img=Image.open(prop["icon"])
            )
            prop_panel.text = Text(
                uv_size=(1, 1), box_size=(0.6, 0.45), parent_point=(0.19, 0.5), point=(0, 0.5), text=prop["name"].get(lang, prop["name"]["en"]), force_size=True, font=default_font
            )

    else:
        canvas.content.tag_part.text = Text(
            uv_size=(1, 1), box_size=(0.6, 0.5), parent_point=(0.5, 0.5), point=(0.5, 0.5), text=no_detailed_data, font=default_font
        )
        canvas.content.now_part.aqi = Text(
            uv_size=(1, 1), box_size=(0.5, 0.1), parent_point=(0.5, 0.89), point=(0.5, 0.5),
            text=f" No AQI data ", font=default_font, fill=Color.hex2dec("FF55AF7B"), fillet=8
        )

    # 小时温度区域
    canvas.content.hourly_temp_part = Rectangle(
        uv_size=(1, 1), box_size=(1, hourly_temp_part_height_scale), parent_point=(0.5, part_now_height_scale + tag_part_height_scale + distance_height_scale * 2), point=(0.5, 0),
        color=base_cover, fillet=base_fillet
    )
    if weather_hourly is not None:
        temp_list = [int(hour.temp) for hour in weather_hourly.hourly]
        min_temp = min(temp_list)
        max_temp = max(temp_list)
        hour_dx = 1 / len(temp_list)
        for hour_i, hour in enumerate(weather_hourly.hourly[0:13]):
            line_height = [0.2, 0.9]
            point_xy = (
                hour_dx / 2 + hour_dx * hour_i,

            )
            hour_panel = canvas.content.hourly_temp_part.__dict__["hour_%s" % hour_i] = Panel(
                uv_size=(1, 1), box_size=(hour_dx, 1), parent_point=(hour_dx*hour_i, 0), point=(0, 0)
            )
            if hour_i % 2 == 1:
                # 加时间
                add_or_sub = "+" if "+" in hour.fxTime else "-"
                time_text = hour.fxTime.split("T")[1].split(add_or_sub)[0]
    else:
        canvas.content.hourly_temp_part.text = Text(
            uv_size=(1, 1), box_size=(0.6, 0.5), parent_point=(0.5, 0.5), point=(0.5, 0.5), text=no_detailed_data, font=default_font
        )
    canvas.signature = Text(
        uv_size=(1, 1), box_size=(1, 0.018), parent_point=(0.5, 0.995), point=(0.5, 1), text=generate_signature, font=default_font, dp=1
    )
    return canvas

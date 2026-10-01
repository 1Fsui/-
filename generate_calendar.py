import datetime as dt
import json
import re
from pathlib import Path

import requests
from lunardate import LunarDate


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "public"
OUT.mkdir(exist_ok=True)

# 生成滚动 3 年日历：上一年、当前年、下一年
today = dt.date.today()
years = range(today.year - 1, today.year + 2)

events = []


def esc(s):
    return (
        str(s)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def add_event(day, name, desc):
    if day.year in years:
        events.append((day, name, desc))


# ============================================================
# 1. 中国法定节假日 + 调休/补班
# ============================================================

url = (
    "https://raw.githubusercontent.com/"
    "NateScarlet/holiday-cn/master/holiday-cn.ics"
)

try:
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    text = r.text
    blocks = re.findall(
        r"BEGIN:VEVENT(.*?)END:VEVENT",
        text,
        flags=re.S,
    )

    for b in blocks:
        dm = re.search(
            r"DTSTART(?:;VALUE=DATE)?:([0-9]{8})",
            b,
        )
        sm = re.search(r"SUMMARY:(.*)", b)

        if not dm or not sm:
            continue

        day = dt.datetime.strptime(
            dm.group(1),
            "%Y%m%d",
        ).date()

        name = sm.group(1).strip()

        add_event(
            day,
            name,
            "中国法定节假日及调休数据",
        )

except Exception as e:
    print("中国节假日数据源获取失败：", e)


# ============================================================
# 2. 中国传统节日
# ============================================================

for y in years:
    try:
        # 农历正月初一：春节
        spring_festival = LunarDate(
            y,
            1,
            1,
        ).toSolarDate()

        # 除夕：春节前一天
        new_year_eve = spring_festival - dt.timedelta(days=1)

        # 元宵节：正月十五
        lantern = LunarDate(
            y,
            1,
            15,
        ).toSolarDate()

        # 端午节：五月初五
        dragon_boat = LunarDate(
            y,
            5,
            5,
        ).toSolarDate()

        # 七夕：七月初七
        qixi = LunarDate(
            y,
            7,
            7,
        ).toSolarDate()

        # 中元节：七月十五
        ghost_festival = LunarDate(
            y,
            7,
            15,
        ).toSolarDate()

        # 中秋节：八月十五
        mid_autumn = LunarDate(
            y,
            8,
            15,
        ).toSolarDate()

        # 重阳节：九月初九
        double_ninth = LunarDate(
            y,
            9,
            9,
        ).toSolarDate()

        # 腊八节：腊月初八
        laba = LunarDate(
            y,
            12,
            8,
        ).toSolarDate()

        add_event(
            new_year_eve,
            "除夕",
            "中国传统节日",
        )

        add_event(
            spring_festival,
            "春节",
            "中国传统节日",
        )

        add_event(
            lantern,
            "元宵节",
            "中国传统节日",
        )

        add_event(
            dragon_boat,
            "端午节",
            "中国传统节日",
        )

        add_event(
            qixi,
            "七夕节",
            "中国传统节日",
        )

        add_event(
            ghost_festival,
            "中元节",
            "中国传统节日",
        )

        add_event(
            mid_autumn,
            "中秋节",
            "中国传统节日",
        )

        add_event(
            double_ninth,
            "重阳节",
            "中国传统节日",
        )

        add_event(
            laba,
            "腊八节",
            "中国传统节日",
        )

    except Exception as e:
        print(f"{y} 年中国传统节日计算失败：", e)


# ============================================================
# 3. 中国传统节日：小年
# ============================================================

for y in years:
    try:
        # 北方小年：腊月二十三
        xiaonian_north = LunarDate(
            y,
            12,
            23,
        ).toSolarDate()

        # 南方小年：腊月二十四
        xiaonian_south = LunarDate(
            y,
            12,
            24,
        ).toSolarDate()

        add_event(
            xiaonian_north,
            "小年（北方）",
            "中国传统节日",
        )

        add_event(
            xiaonian_south,
            "小年（南方）",
            "中国传统节日",
        )

    except Exception as e:
        print(f"{y} 年小年计算失败：", e)


# ============================================================
# 4. 全球普遍使用的固定节日
# ============================================================

fixed_global_days = {
    (1, 1): "元旦",
    (2, 14): "情人节",
    (3, 8): "国际妇女节",
    (4, 1): "愚人节",
    (4, 22): "世界地球日",
    (5, 1): "国际劳动节",
    (6, 1): "国际儿童节",
    (10, 31): "万圣节",
    (12, 24): "平安夜",
    (12, 25): "圣诞节",
    (12, 31): "跨年夜",
}

for y in years:
    for (month, day), name in fixed_global_days.items():
        add_event(
            dt.date(y, month, day),
            name,
            "全球普遍节日或纪念日",
        )


# ============================================================
# 5. 母亲节、父亲节
# ============================================================

def nth_weekday_of_month(year, month, weekday, n):
    first = dt.date(year, month, 1)

    offset = (weekday - first.weekday()) % 7

    return first + dt.timedelta(
        days=offset + (n - 1) * 7
    )


for y in years:
    # 母亲节：5 月第二个星期日
    mothers_day = nth_weekday_of_month(
        y,
        5,
        6,
        2,
    )

    # 父亲节：6 月第三个星期日
    fathers_day = nth_weekday_of_month(
        y,
        6,
        6,
        3,
    )

    add_event(
        mothers_day,
        "母亲节",
        "全球普遍节日",
    )

    add_event(
        fathers_day,
        "父亲节",
        "全球普遍节日",
    )


# ============================================================
# 6. 复活节
# ============================================================

def easter_sunday(year):
    """
    西方公历复活节计算。
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1

    return dt.date(year, month, day)


for y in years:
    easter = easter_sunday(y)

    add_event(
        easter - dt.timedelta(days=2),
        "耶稣受难日",
        "全球普遍节日",
    )

    add_event(
        easter,
        "复活节",
        "全球普遍节日",
    )

    add_event(
        easter + dt.timedelta(days=1),
        "复活节星期一",
        "全球普遍节日",
    )


# ============================================================
# 7. 联合国 / 国际组织纪念日
# ============================================================

obs_file = ROOT / "observances.json"

obs = json.loads(
    obs_file.read_text(
        encoding="utf-8"
    )
)

for y in years:
    for item in obs:
        try:
            day = dt.date.fromisoformat(
                f"{y}-{item['date']}"
            )
        except (KeyError, ValueError):
            continue

        # 只使用中文名称
        name_zh = str(
            item.get("name_zh", "")
        ).strip()

        if not name_zh:
            continue

        add_event(
            day,
            name_zh,
            "联合国及国际组织纪念日",
        )


# ============================================================
# 8. 去重
# ============================================================

seen = set()
unique = []

for day, name, desc in sorted(events):
    key = (day, name)

    if key in seen:
        continue

    seen.add(key)
    unique.append(
        (day, name, desc)
    )


# ============================================================
# 9. 生成 ICS
# ============================================================

def make_ics(items):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//中国国际节日日历//CN//",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:中国 + 国际节日日历",
        "X-WR-CALDESC:中国法定节假日、调休、中国传统节日、全球普遍节日、联合国及国际组织纪念日",
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]

    for i, (day, name, desc) in enumerate(items):
        uid = (
            f"{day:%Y%m%d}-{i}"
            "@china-international-calendar"
        )

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            (
                "DTSTAMP:"
                f"{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}"
            ),
            (
                "DTSTART;VALUE=DATE:"
                f"{day:%Y%m%d}"
            ),
            (
                "DTEND;VALUE=DATE:"
                f"{(day + dt.timedelta(days=1)):%Y%m%d}"
            ),
            f"SUMMARY:{esc(name)}",
            f"DESCRIPTION:{esc(desc)}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")

    return "\r\n".join(lines) + "\r\n"


(OUT / "holiday.ics").write_text(
    make_ics(unique),
    encoding="utf-8",
)


# ============================================================
# 10. GitHub Pages 首页
# ============================================================

html = """<!doctype html>
<meta charset="utf-8">
<title>中国 + 国际节日日历</title>

<h1>中国 + 国际节日日历</h1>

<p>
包含中国法定节假日、调休、中国传统节日、
全球普遍节日，以及联合国和国际组织纪念日。
</p>

<p>
不包含其他国家自己的公共假日，
不包含黄历、宜忌、每日农历、天干地支、二十四节气。
</p>

<p>
<a href="holiday.ics">订阅 / 下载 holiday.ics</a>
</p>
"""

(OUT / "index.html").write_text(
    html,
    encoding="utf-8",
)


print(
    f"已生成 {len(unique)} 个日历事件："
    f"{OUT / 'holiday.ics'}"
)

import datetime as dt
import json
import re
from pathlib import Path

import requests
from lunardate import LunarDate

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "public"
OUT.mkdir(exist_ok=True)

# 自动生成：上一年、当前年、下一年
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
# 1. 中国法定节假日、调休
# ============================================================

url = "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/holiday-cn.ics"

try:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    text = r.text

    blocks = re.findall(
        r"BEGIN:VEVENT(.*?)END:VEVENT",
        text,
        flags=re.S
    )

    for b in blocks:
        dm = re.search(
            r"DTSTART(?:;VALUE=DATE)?:([0-9]{8})",
            b
        )
        sm = re.search(
            r"SUMMARY:(.*)",
            b
        )

        if not dm or not sm:
            continue

        day = dt.datetime.strptime(
            dm.group(1),
            "%Y%m%d"
        ).date()

        if day.year not in years:
            continue

        name = sm.group(1).strip()

        add_event(
            day,
            name,
            "中国法定节假日及调休数据"
        )

except Exception as e:
    print("中国节假日数据源获取失败：", e)


# ============================================================
# 2. 中国传统节日
#    使用农历日期自动换算
# ============================================================

for year in years:

    start = dt.date(year, 1, 1)
    end = dt.date(year, 12, 31)

    day = start

    while day <= end:

        try:
            lunar = LunarDate.fromSolarDate(
                day.year,
                day.month,
                day.day
            )

            lunar_month = lunar.month
            lunar_day = lunar.day

            # 春节
            if lunar_month == 1 and lunar_day == 1:
                add_event(
                    day,
                    "春节",
                    "中国传统节日"
                )

            # 元宵节
            elif lunar_month == 1 and lunar_day == 15:
                add_event(
                    day,
                    "元宵节",
                    "中国传统节日"
                )

            # 端午节
            elif lunar_month == 5 and lunar_day == 5:
                add_event(
                    day,
                    "端午节",
                    "中国传统节日"
                )

            # 七夕
            elif lunar_month == 7 and lunar_day == 7:
                add_event(
                    day,
                    "七夕",
                    "中国传统节日"
                )

            # 中元节
            elif lunar_month == 7 and lunar_day == 15:
                add_event(
                    day,
                    "中元节",
                    "中国传统节日"
                )

            # 中秋节
            elif lunar_month == 8 and lunar_day == 15:
                add_event(
                    day,
                    "中秋节",
                    "中国传统节日"
                )

            # 重阳节
            elif lunar_month == 9 and lunar_day == 9:
                add_event(
                    day,
                    "重阳节",
                    "中国传统节日"
                )

            # 腊八节
            elif lunar_month == 12 and lunar_day == 8:
                add_event(
                    day,
                    "腊八节",
                    "中国传统节日"
                )

            # 除夕
            # 农历十二月最后一天可能是29日或30日
            next_day = day + dt.timedelta(days=1)

            if lunar_month == 12:
                try:
                    next_lunar = LunarDate.fromSolarDate(
                        next_day.year,
                        next_day.month,
                        next_day.day
                    )

                    if next_lunar.month == 1 and next_lunar.day == 1:
                        add_event(
                            day,
                            "除夕",
                            "中国传统节日"
                        )

                except Exception:
                    pass

        except Exception:
            pass

        day += dt.timedelta(days=1)


# ============================================================
# 3. 大众常见节日
#
# 注意：
# 这里只加入全球普遍认知的节日/纪念日，
# 不加入美国、日本、韩国、英国等国家自己的法定公共假日。
# ============================================================

for year in years:

    # 元旦
    # 中国法定节假日数据已经提供“元旦假期”，
    # 因此这里故意不再加入单独的“元旦”，避免重复。

    common_fixed = [
        (1, 4, "世界盲文日"),
        (2, 14, "情人节"),
        (3, 8, "国际妇女节"),
        (4, 1, "愚人节"),
        (4, 22, "世界地球日"),
        (5, 1, "国际劳动节"),
        (5, 31, "世界无烟日"),
        (6, 1, "国际儿童节"),
        (7, 30, "国际友谊日"),
        (10, 31, "万圣节"),
        (12, 25, "圣诞节"),
        (12, 31, "跨年夜"),
    ]

    for month, day_num, name in common_fixed:
        try:
            add_event(
                dt.date(year, month, day_num),
                name,
                "大众节日及国际纪念日"
            )
        except ValueError:
            pass

    # --------------------------------------------------------
    # 母亲节：5月第二个星期日
    # --------------------------------------------------------

    d = dt.date(year, 5, 1)

    while d.weekday() != 6:
        d += dt.timedelta(days=1)

    d += dt.timedelta(days=7)

    add_event(
        d,
        "母亲节",
        "大众节日"
    )

    # --------------------------------------------------------
    # 父亲节：6月第三个星期日
    # --------------------------------------------------------

    d = dt.date(year, 6, 1)

    while d.weekday() != 6:
        d += dt.timedelta(days=1)

    d += dt.timedelta(days=14)

    add_event(
        d,
        "父亲节",
        "大众节日"
    )


# ============================================================
# 4. 联合国 / 国际组织纪念日
# ============================================================

obs = json.loads(
    (ROOT / "observances.json").read_text(
        encoding="utf-8"
    )
)

for year in years:

    for item in obs:

        try:
            day = dt.date.fromisoformat(
                f"{year}-{item['date']}"
            )
        except (KeyError, ValueError):
            continue

        name_zh = str(
            item.get("name_zh", "")
        ).strip()

        # 没有中文名称的不加入
        if not name_zh:
            continue

        # 元旦已经由中国法定节假日数据提供
        # 不再重复添加
        if name_zh == "元旦":
            continue

        add_event(
            day,
            name_zh,
            "联合国及国际组织纪念日"
        )


# ============================================================
# 5. 去重
#
# 同一天 + 同一个名称只保留一次
# ============================================================

seen = set()
unique = []

for day, name, desc in sorted(events):

    key = (
        day,
        name
    )

    if key in seen:
        continue

    seen.add(key)

    unique.append(
        (day, name, desc)
    )


# ============================================================
# 6. 生成 ICS
# ============================================================

def make_ics(items):

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//中国国际节日日历//CN//",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:中国 + 国际节日日历",
        "X-WR-CALDESC:中国法定节假日、调休、中国传统节日、大众节日及联合国国际纪念日",
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]

    timestamp = dt.datetime.now(
        dt.timezone.utc
    )

    for i, (day, name, desc) in enumerate(items):

        uid = (
            f"{day:%Y%m%d}-"
            f"{i}@china-international-calendar"
        )

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{timestamp:%Y%m%dT%H%M%SZ}",
            f"DTSTART;VALUE=DATE:{day:%Y%m%d}",
            f"DTEND;VALUE=DATE:{(day + dt.timedelta(days=1)):%Y%m%d}",
            f"SUMMARY:{esc(name)}",
            f"DESCRIPTION:{esc(desc)}",
            "END:VEVENT",
        ]

    lines.append(
        "END:VCALENDAR"
    )

    return "\r\n".join(lines) + "\r\n"


# ============================================================
# 7. 输出日历
# ============================================================

(OUT / "holiday.ics").write_text(
    make_ics(unique),
    encoding="utf-8"
)


# ============================================================
# 8. GitHub Pages 首页
# ============================================================

html = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>中国 + 国际节日日历</title>
</head>
<body>
<h1>中国 + 国际节日日历</h1>

<p>
包含中国法定节假日、调休、中国传统节日、大众节日，以及联合国和国际组织纪念日。
</p>

<p>
不包含其他国家自己的法定公共假日。
</p>

<p>
不包含黄历、宜忌、每日农历、天干地支、二十四节气。
</p>

<p>
<a href="holiday.ics">订阅 / 下载日历</a>
</p>

</body>
</html>
"""

(OUT / "index.html").write_text(
    html,
    encoding="utf-8"
)


print(
    f"已生成 {len(unique)} 个日历事件："
    f"{OUT / 'holiday.ics'}"
)

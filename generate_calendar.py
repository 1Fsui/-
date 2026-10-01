import datetime as dt
import json
import re
from pathlib import Path

import requests
from lunardate import LunarDate


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "public"
OUT.mkdir(exist_ok=True)


# ============================================================
# 生成范围
# ============================================================
# 上一年 + 当前年 + 下一年
#
# 例如当前是 2026：
# 2025 / 2026 / 2027
#
# 不会把上一年的具体日期复制到下一年。
# ============================================================

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
    if not isinstance(day, dt.date):
        return

    if day.year not in years:
        return

    name = str(name).strip()

    if not name:
        return

    events.append((day, name, desc))


# ============================================================
# 1. 中国国务院官方节假日 / 调休
# ============================================================
#
# 数据源：
# https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{年份}.json
#
# 只使用对应年份自己的数据。
#
# 绝不会：
# - 把 2026 年调休复制到 2027 年
# - 把 2026 年春节日期复制到 2027 年
# - 猜测下一年的调休
#
# 如果某一年官方尚未公布，days 通常为空，
# 那么下面的“固定节日 + 农历节日”系统会负责生成节日。
# ============================================================

for year in years:

    url = (
        "https://raw.githubusercontent.com/"
        f"NateScarlet/holiday-cn/master/{year}.json"
    )

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        days = data.get("days", [])

        if days:

            for item in days:

                try:
                    day = dt.date.fromisoformat(
                        item["date"]
                    )
                except (
                    KeyError,
                    ValueError,
                    TypeError,
                ):
                    continue

                if day.year != year:
                    continue

                name = str(
                    item.get("name", "")
                ).strip()

                if not name:
                    continue

                is_off_day = bool(
                    item.get("isOffDay", False)
                )

                if is_off_day:

                    add_event(
                        day,
                        f"{name}假期",
                        "中国国务院节假日数据源",
                    )

                else:

                    add_event(
                        day,
                        f"上班(补{name}假期)",
                        "中国国务院节假日数据源",
                    )

            print(
                f"{year} 年：已读取国务院节假日安排"
            )

        else:

            print(
                f"{year} 年：官方完整节假日安排尚未发布，"
                "不猜测调休，只生成确定的节日。"
            )

    except Exception as e:

        print(
            f"{year} 年官方数据暂时无法获取：{e}"
        )

        # 注意：
        # 这里绝对不复制上一年的调休。
        # 后面的固定/农历节日系统仍然会继续生成。


# ============================================================
# 2. 中国固定公历节日 / 纪念日
# ============================================================
#
# 这些日期与上一年无关。
# 每一年直接按照公历固定日期计算。
#
# 依据现行《全国年节及纪念日放假办法》：
# 元旦 1月1日
# 妇女节 3月8日
# 青年节 5月4日
# 劳动节 5月1日、5月2日
# 儿童节 6月1日
# 建军节 8月1日
# 国庆节 10月1日-3日
#
# 教师节、护士节、记者节、植树节等也加入。
# ============================================================

FIXED_CHINA_DATES = {

    # 法定 / 部分公民节日
    "01-01": "元旦",
    "03-08": "妇女节",
    "03-12": "植树节",
    "05-01": "劳动节",
    "05-02": "劳动节",
    "05-04": "青年节",
    "06-01": "儿童节",
    "08-01": "建军节",

    # 纪念日
    "05-12": "护士节",
    "09-10": "教师节",
    "09-18": "九一八纪念日",
    "10-01": "国庆节",
    "10-02": "国庆节",
    "10-03": "国庆节",
    "11-08": "记者节",
    "12-13": "国家公祭日",
}


for year in years:

    for mmdd, name in FIXED_CHINA_DATES.items():

        month, day = map(
            int,
            mmdd.split("-")
        )

        add_event(
            dt.date(year, month, day),
            name,
            "中国固定节日及纪念日",
        )


# ============================================================
# 3. 中国农历传统节日
# ============================================================
#
# 每一年单独按照该年的农历计算。
#
# 因此：
#
# 2026 年春节 ≠ 2027 年春节
# 2027 年端午 ≠ 2026 年端午
# 2028 年中秋 ≠ 2027 年中秋
#
# 不存在复制上一年公历日期的问题。
# ============================================================

for year in years:

    # --------------------------------------------------------
    # 除夕
    # --------------------------------------------------------
    # 正月初一的前一天就是除夕。
    # 春节年份对应的农历年为 year。
    # --------------------------------------------------------

    try:

        lunar_new_year = LunarDate(
            year,
            1,
            1
        ).toSolarDate()

        chinese_new_year = dt.date(
            lunar_new_year.year,
            lunar_new_year.month,
            lunar_new_year.day,
        )

        new_year_eve = (
            chinese_new_year
            - dt.timedelta(days=1)
        )

        add_event(
            new_year_eve,
            "除夕",
            "中国传统节日（农历）",
        )

        # ----------------------------------------------------
        # 春节
        # ----------------------------------------------------

        add_event(
            chinese_new_year,
            "春节",
            "中国传统节日（农历）",
        )

        add_event(
            chinese_new_year
            + dt.timedelta(days=1),
            "春节",
            "中国传统节日（农历）",
        )

        add_event(
            chinese_new_year
            + dt.timedelta(days=2),
            "春节",
            "中国传统节日（农历）",
        )

        # 初四也作为传统春节期间保留
        add_event(
            chinese_new_year
            + dt.timedelta(days=3),
            "春节",
            "中国传统节日（农历）",
        )

    except Exception as e:

        print(
            f"{year} 年春节计算失败：{e}"
        )


    # --------------------------------------------------------
    # 元宵节：正月十五
    # --------------------------------------------------------

    try:

        day = LunarDate(
            year,
            1,
            15
        ).toSolarDate()

        add_event(
            dt.date(
                day.year,
                day.month,
                day.day,
            ),
            "元宵节",
            "中国传统节日（农历）",
        )

    except Exception:
        pass


    # --------------------------------------------------------
    # 端午节：五月初五
    # --------------------------------------------------------

    try:

        day = LunarDate(
            year,
            5,
            5
        ).toSolarDate()

        add_event(
            dt.date(
                day.year,
                day.month,
                day.day,
            ),
            "端午节",
            "中国传统节日（农历）",
        )

    except Exception:
        pass


    # --------------------------------------------------------
    # 七夕：七月初七
    # --------------------------------------------------------

    try:

        day = LunarDate(
            year,
            7,
            7
        ).toSolarDate()

        add_event(
            dt.date(
                day.year,
                day.month,
                day.day,
            ),
            "七夕",
            "中国传统节日（农历）",
        )

    except Exception:
        pass


    # --------------------------------------------------------
    # 中元节：七月十五
    # --------------------------------------------------------

    try:

        day = LunarDate(
            year,
            7,
            15
        ).toSolarDate()

        add_event(
            dt.date(
                day.year,
                day.month,
                day.day,
            ),
            "中元节",
            "中国传统节日（农历）",
        )

    except Exception:
        pass


    # --------------------------------------------------------
    # 中秋节：八月十五
    # --------------------------------------------------------

    try:

        day = LunarDate(
            year,
            8,
            15
        ).toSolarDate()

        add_event(
            dt.date(
                day.year,
                day.month,
                day.day,
            ),
            "中秋节",
            "中国传统节日（农历）",
        )

    except Exception:
        pass


    # --------------------------------------------------------
    # 重阳节：九月初九
    # --------------------------------------------------------

    try:

        day = LunarDate(
            year,
            9,
            9
        ).toSolarDate()

        add_event(
            dt.date(
                day.year,
                day.month,
                day.day,
            ),
            "重阳节",
            "中国传统节日（农历）",
        )

    except Exception:
        pass


    # --------------------------------------------------------
    # 腊八节：腊月初八
    # --------------------------------------------------------

    try:

        day = LunarDate(
            year,
            12,
            8
        ).toSolarDate()

        add_event(
            dt.date(
                day.year,
                day.month,
                day.day,
            ),
            "腊八节",
            "中国传统节日（农历）",
        )

    except Exception:
        pass


# ============================================================
# 4. 清明节
# ============================================================
#
# 清明不是固定公历日期。
# 因此不能简单写死成 4 月 4 日或 4 月 5 日。
#
# 这里使用按年份计算的常用清明算法。
#
# 该算法只负责“节日本身的日期”。
# 国务院公布的具体放假/调休仍然以官方年度数据为准。
# ============================================================

def qingming_date(year):

    # 2000-2099 年常用清明算法
    # 清明约在 4 月 4 日或 4 月 5 日。

    if year < 2000 or year > 2099:
        return None

    # 清明计算公式：
    # 4月5日附近，按世纪常数进行计算。
    #
    # 这里采用 2000-2099 年常用公式。
    y = year % 100

    day = int(
        y * 0.2422
        + 4.81
        - y // 4
    )

    # 特殊年份修正
    special = {
        2008: 4,
        2009: 4,
        2012: 4,
        2016: 4,
        2019: 5,
        2020: 4,
        2021: 4,
        2024: 4,
        2025: 4,
        2026: 5,
        2027: 5,
        2028: 4,
        2029: 4,
        2030: 5,
    }

    if year in special:
        day = special[year]

    return dt.date(
        year,
        4,
        day,
    )


for year in years:

    day = qingming_date(year)

    if day:

        add_event(
            day,
            "清明节",
            "中国传统节日及法定节日",
        )


# ============================================================
# 5. 全球普遍节日
# ============================================================
#
# 注意：
# 这里不是“各国公共假日”。
#
# 只加入全球范围内普遍认知的大众节日/文化节日。
#
# 不加入美国国庆、加拿大国庆、日本成人节、
# 韩国中秋公共假期等“某个国家自己的公共假日”。
# ============================================================

GLOBAL_FIXED = {

    "02-14": "情人节",
    "12-24": "平安夜",
    "12-25": "圣诞节",
    "10-31": "万圣节",
}

for year in years:

    for mmdd, name in GLOBAL_FIXED.items():

        month, day = map(
            int,
            mmdd.split("-")
        )

        add_event(
            dt.date(year, month, day),
            name,
            "全球普遍节日",
        )


# ============================================================
# 6. 母亲节
# ============================================================
# 每年 5 月第二个星期日
# 不使用上一年的日期。
# ============================================================

def nth_weekday(year, month, weekday, n):

    first = dt.date(
        year,
        month,
        1,
    )

    offset = (
        weekday
        - first.weekday()
    ) % 7

    return first + dt.timedelta(
        days=offset + (n - 1) * 7
    )


for year in years:

    add_event(
        nth_weekday(
            year,
            5,
            6,   # 星期日
            2,
        ),
        "母亲节",
        "全球普遍节日",
    )


# ============================================================
# 7. 父亲节
# ============================================================
# 每年 6 月第三个星期日
# ============================================================

for year in years:

    add_event(
        nth_weekday(
            year,
            6,
            6,
            3,
        ),
        "父亲节",
        "全球普遍节日",
    )


# ============================================================
# 8. 感恩节
# ============================================================
#
# 这里仅作为全球大众文化节日记录，
# 不代表中国法定假日。
#
# 每年 11 月第四个星期四。
# ============================================================

for year in years:

    add_event(
        nth_weekday(
            year,
            11,
            3,   # 星期四
            4,
        ),
        "感恩节",
        "全球普遍文化节日",
    )


# ============================================================
# 9. 联合国 / 国际组织纪念日
# ============================================================
#
# 使用你现有的 observances.json。
#
# 只写 name_zh。
# name_en 永远不会进入 ICS。
# ============================================================

obs_path = ROOT / "observances.json"

if obs_path.exists():

    try:

        obs = json.loads(
            obs_path.read_text(
                encoding="utf-8"
            )
        )

        for year in years:

            for item in obs:

                try:

                    day = dt.date.fromisoformat(
                        f"{year}-{item['date']}"
                    )

                except (
                    KeyError,
                    ValueError,
                    TypeError,
                ):
                    continue

                name_zh = str(
                    item.get(
                        "name_zh",
                        ""
                    )
                ).strip()

                if not name_zh:
                    continue

                add_event(
                    day,
                    name_zh,
                    "联合国及国际组织纪念日",
                )

    except Exception as e:

        print(
            f"observances.json 读取失败：{e}"
        )


# ============================================================
# 10. 去重
# ============================================================

seen = set()
unique = []

for day, name, desc in sorted(events):

    key = (
        day,
        name,
    )

    if key in seen:
        continue

    seen.add(key)

    unique.append(
        (
            day,
            name,
            desc,
        )
    )


# ============================================================
# 11. 生成 ICS
# ============================================================

def make_ics(items):

    lines = [

        "BEGIN:VCALENDAR",

        "VERSION:2.0",

        "PRODID:-//中国国际节日日历//CN//",

        "CALSCALE:GREGORIAN",

        "METHOD:PUBLISH",

        "X-WR-CALNAME:中国 + 国际节日日历",

        (
            "X-WR-CALDESC:"
            "中国法定节假日、调休、中国传统节日、"
            "全球普遍节日、联合国及国际组织纪念日"
        ),

        "X-WR-TIMEZONE:Asia/Shanghai",
    ]


    for i, (
        day,
        name,
        desc,
    ) in enumerate(items):

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


    lines.append(
        "END:VCALENDAR"
    )

    return (
        "\r\n".join(lines)
        + "\r\n"
    )


# ============================================================
# 12. 写入 holiday.ics
# ============================================================

ics_content = make_ics(
    unique
)

(OUT / "holiday.ics").write_text(
    ics_content,
    encoding="utf-8",
)


# ============================================================
# 13. 网页
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
包含中国法定节假日、调休、中国传统节日、
全球普遍节日、联合国及国际组织纪念日。
</p>

<p>
中国法定节假日及调休以当年国务院公布的安排为准。
</p>

<p>
不包含其他国家自己的公共假日。
</p>

<p>
不包含黄历、宜忌、每日农历、
天干地支、二十四节气。
</p>

<p>
<a href="holiday.ics">
订阅 / 下载 holiday.ics
</a>
</p>

</body>
</html>
"""

(OUT / "index.html").write_text(
    html,
    encoding="utf-8",
)


# ============================================================
# 14. 输出统计
# ============================================================

print(
    "========================================"
)

print(
    f"生成年份："
    f"{today.year - 1} / "
    f"{today.year} / "
    f"{today.year + 1}"
)

print(
    f"日历事件数量：{len(unique)}"
)

print(
    f"输出文件：{OUT / 'holiday.ics'}"
)

print(
    "========================================"
)

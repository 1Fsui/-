import datetime as dt
import json
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "public"
OUT.mkdir(exist_ok=True)

# 生成滚动 3 年日历：
# 上一年 + 当前年 + 下一年
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
    events.append((day, name, desc))


# ============================================================
# 1. 中国法定节假日、调休
# ============================================================
#
# 改为逐年读取 holiday-cn 的 JSON：
#
# https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{年份}.json
#
# 这样不会再受到 holiday-cn.ics 的年份范围限制。
#
# 数据结构：
# {
#   "year": 2026,
#   "days": [
#       {
#           "name": "元旦",
#           "date": "2026-01-01",
#           "isOffDay": true
#       }
#   ]
# }
#
# 如果未来年份还没有公布官方安排，
# holiday-cn 对应年份可能暂时为空。
# 这种情况下至少自动保留该年的 1 月 1 日“元旦”，
# 等官方数据公布后，GitHub Actions 会自动抓取完整安排。
# ============================================================

for year in years:
    url = (
        "https://raw.githubusercontent.com/"
        f"NateScarlet/holiday-cn/master/{year}.json"
    )

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()

        days = data.get("days", [])

        # --------------------------------------------------------
        # 官方数据已经存在
        # --------------------------------------------------------
        if days:
            for item in days:
                try:
                    day = dt.date.fromisoformat(item["date"])
                except (KeyError, ValueError, TypeError):
                    continue

                if day.year != year:
                    continue

                name = str(item.get("name", "")).strip()

                if not name:
                    continue

                is_off_day = bool(item.get("isOffDay", False))

                if is_off_day:
                    # 休假日
                    add_event(
                        day,
                        f"{name}假期",
                        "中国国务院节假日数据源",
                    )
                else:
                    # 调休上班日
                    add_event(
                        day,
                        f"上班(补{name}假期)",
                        "中国国务院节假日数据源",
                    )

        # --------------------------------------------------------
        # 未来年份官方数据暂未公布
        # --------------------------------------------------------
        else:
            # 元旦是固定法定节日，法律明确规定为 1 月 1 日。
            # 因此即使该年份官方完整安排尚未发布，
            # 也先确保元旦不会消失。
            add_event(
                dt.date(year, 1, 1),
                "元旦",
                "中国法定节日（固定日期）",
            )

            print(
                f"{year} 年官方节假日安排尚未发布，"
                "暂时加入固定节日：元旦"
            )

    except Exception as e:
        print(f"{year} 年中国节假日数据获取失败：{e}")

        # 数据源临时失败时，也不要让元旦完全消失。
        add_event(
            dt.date(year, 1, 1),
            "元旦",
            "中国法定节日（固定日期）",
        )


# ============================================================
# 2. 联合国 / 国际组织纪念日
# ============================================================

obs_path = ROOT / "observances.json"

if obs_path.exists():
    obs = json.loads(
        obs_path.read_text(encoding="utf-8")
    )

    for year in years:
        for item in obs:
            try:
                day = dt.date.fromisoformat(
                    f"{year}-{item['date']}"
                )
            except (KeyError, ValueError, TypeError):
                continue

            name_zh = str(
                item.get("name_zh", "")
            ).strip()

            # 没有中文名称的不加入，
            # 确保日历里不会出现英文。
            if not name_zh:
                continue

            add_event(
                day,
                name_zh,
                "联合国及国际组织纪念日",
            )


# ============================================================
# 3. 去重
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
# 4. 生成 ICS
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
            f"DTSTART;VALUE=DATE:{day:%Y%m%d}",
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


ics_content = make_ics(unique)

(OUT / "holiday.ics").write_text(
    ics_content,
    encoding="utf-8",
)


# ============================================================
# 5. 生成网页
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
不包含其他国家自己的公共假日，
不包含黄历、宜忌、每日农历、天干地支、二十四节气。
</p>

<p>
<a href="holiday.ics">订阅 / 下载 holiday.ics</a>
</p>

</body>
</html>
"""

(OUT / "index.html").write_text(
    html,
    encoding="utf-8",
)


print(
    f"已生成 {len(unique)} 个日历事件："
    f"{OUT / 'holiday.ics'}"
)

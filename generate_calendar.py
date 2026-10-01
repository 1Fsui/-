import datetime as dt
import json
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "public"
OUT.mkdir(exist_ok=True)

# 生成滚动 3 年日历：上一年、当前年、下一年。
today = dt.date.today()
years = range(today.year - 1, today.year + 2)


def esc(s):
    return (
        str(s)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


events = []

# 1) 中国法定节假日、调休及官方公布的节日数据。
# 数据源：holiday-cn，维护内容来自中国国务院节假日通知。
url = "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/holiday-cn.ics"

try:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    text = r.text

    # 解析简单的全天 VEVENT。
    blocks = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, flags=re.S)

    for b in blocks:
        dm = re.search(r"DTSTART(?:;VALUE=DATE)?:([0-9]{8})", b)
        sm = re.search(r"SUMMARY:(.*)", b)

        if not dm or not sm:
            continue

        day = dt.datetime.strptime(dm.group(1), "%Y%m%d").date()

        if day.year not in years:
            continue

        name = sm.group(1).strip()
        events.append(
            (day, f"中国：{name}", "中国国务院节假日数据源")
        )

except Exception as e:
    print("中国节假日数据源获取失败：", e)


# 2) 联合国 / 国际组织纪念日。
# 只使用中文名称，不把 name_en 写入日历。
obs = json.loads(
    (ROOT / "observances.json").read_text(encoding="utf-8")
)

for y in years:
    for item in obs:
        try:
            day = dt.date.fromisoformat(f"{y}-{item['date']}")
        except (KeyError, ValueError):
            continue

        name_zh = str(item.get("name_zh", "")).strip()

        # 没有中文名称的项目不加入，避免日历出现英文。
        if not name_zh:
            continue

        events.append(
            (day, name_zh, "联合国及国际组织纪念日")
        )


# 3) 去重：同一天 + 同名称只保留一次。
seen = set()
unique = []

for day, name, desc in sorted(events):
    key = (day, name)

    if key in seen:
        continue

    seen.add(key)
    unique.append((day, name, desc))


def make_ics(items):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//中国全球节日日历//CN//",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:中国 + 联合国国际节日",
        "X-WR-CALDESC:中国法定节假日、调休及联合国和国际组织纪念日",
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]

    for i, (day, name, desc) in enumerate(items):
        uid = f"{day:%Y%m%d}-{i}@china-world-calendar"

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}",
            f"DTSTART;VALUE=DATE:{day:%Y%m%d}",
            f"DTEND;VALUE=DATE:{(day + dt.timedelta(days=1)):%Y%m%d}",
            f"SUMMARY:{esc(name)}",
            f"DESCRIPTION:{esc(desc)}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


# 输出订阅日历。
(OUT / "holiday.ics").write_text(
    make_ics(unique),
    encoding="utf-8",
)


# GitHub Pages 首页。
html = """<!doctype html>
<meta charset="utf-8">
<title>中国 + 联合国国际节日订阅</title>
<h1>中国 + 联合国国际节日</h1>
<p>包含中国法定节假日、调休，以及联合国和国际组织纪念日。</p>
<p>不包含其他国家自己的公共假日，不包含黄历、宜忌、每日农历、二十四节气。</p>
<p><a href="holiday.ics">订阅 / 下载 holiday.ics</a></p>
"""

(OUT / "index.html").write_text(
    html,
    encoding="utf-8",
)

print(f"已生成 {len(unique)} 个日历事件：{OUT / 'holiday.ics'}")

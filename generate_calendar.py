import datetime as dt
import json
import os
import re
from pathlib import Path

import holidays
import requests

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "public"
OUT.mkdir(exist_ok=True)

# Generate a rolling 3-year calendar: previous, current and next year.
today = dt.date.today()
years = range(today.year - 1, today.year + 2)

# Countries whose public holidays are useful for a China + international calendar.
COUNTRIES = ["CN", "JP", "US", "GB", "CA", "AU", "KR", "SG", "IN", "FR", "DE", "IT", "ES", "BR", "MX"]

def esc(s):
    return str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

events = []

# 1) Public holidays from the maintained Python holidays database.
# China statutory holiday arrangements are supplemented below from the
# official-data-derived holiday-cn feed.
for country in COUNTRIES:
    try:
        cal = holidays.country_holidays(country, years=list(years))
        for day, name in sorted(cal.items()):
            events.append((day, f"{name} [{country}]", f"Public holiday • {country}"))
    except Exception as e:
        print(f"skip {country}: {e}")

# 2) China official-derived feed. This repository is maintained from
# State Council holiday notices and includes compensating workdays.
url = "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/holiday-cn.ics"
try:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    text = r.text
    # Parse simple all-day VEVENTs.
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
        events.append((day, f"中国：{name}", "中国国务院节假日数据源"))
except Exception as e:
    print("China feed unavailable:", e)

# 3) Broad international observances (no almanac / solar terms).
obs = json.loads((ROOT / "observances.json").read_text(encoding="utf-8"))
for y in years:
    for item in obs:
        day = dt.date.fromisoformat(f"{y}-{item['date']}")
        events.append((day, f"{item['name_zh']} / {item['name_en']}", "International observance"))

# 4) Common movable cultural days.
def nth_weekday(year, month, weekday, n):
    d = dt.date(year, month, 1)
    d += dt.timedelta(days=(weekday - d.weekday()) % 7)
    return d + dt.timedelta(days=7*(n-1))

def last_weekday(year, month, weekday):
    if month == 12:
        d = dt.date(year+1,1,1)-dt.timedelta(days=1)
    else:
        d = dt.date(year,month+1,1)-dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday()-weekday)%7)

for y in years:
    movable = [
        (nth_weekday(y,5,6,2), "母亲节 / Mother's Day"),
        (nth_weekday(y,6,6,3), "父亲节 / Father's Day"),
        (nth_weekday(y,11,3,4), "美国感恩节 / Thanksgiving Day"),
        (nth_weekday(y,9,0,1), "劳动节（美国/加拿大等） / Labour Day"),
    ]
    for day, name in movable:
        events.append((day, name, "Cultural observance"))

# Deduplicate by date + name.
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
        "PRODID:-//Global Holiday Calendar//CN+World//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:中国 + 全球节日",
        "X-WR-CALDESC:中国法定节假日、调休、传统节日及全球公共假日和国际纪念日（无黄历、无二十四节气）",
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]
    for i,(day,name,desc) in enumerate(items):
        uid = f"{day:%Y%m%d}-{i}@global-holiday-calendar"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}",
            f"DTSTART;VALUE=DATE:{day:%Y%m%d}",
            f"DTEND;VALUE=DATE:{(day+dt.timedelta(days=1)):%Y%m%d}",
            f"SUMMARY:{esc(name)}",
            f"DESCRIPTION:{esc(desc)}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

(OUT/"holiday.ics").write_text(make_ics(unique), encoding="utf-8")

# Also publish a simple landing page for GitHub Pages.
html = """<!doctype html><meta charset="utf-8">
<title>中国 + 全球节日订阅</title>
<h1>中国 + 全球节日</h1>
<p>不包含黄历、宜忌、每日农历、二十四节气。</p>
<p><a href="holiday.ics">订阅 / 下载 holiday.ics</a></p>
"""
(OUT/"index.html").write_text(html, encoding="utf-8")
print(f"Wrote {len(unique)} events to {OUT/'holiday.ics'}")

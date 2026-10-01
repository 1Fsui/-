# 中国 + 全球节日订阅日历

这个仓库通过 GitHub Actions 自动生成 `public/holiday.ics`。

包含：
- 中国法定节假日与调休数据
- 中国及主要国家/地区公共假日
- 联合国/国际组织体系中的大量国际日
- 常见和部分不常见的国际文化纪念日

明确不包含：
- 黄历
- 宜忌
- 每日农历
- 二十四节气

## GitHub Pages

仓库创建后，在 **Settings → Pages** 中选择：

- Source: GitHub Actions

部署完成后，订阅地址为：

`https://你的GitHub用户名.github.io/你的仓库名/holiday.ics`

例如仓库名为 `global-holiday-calendar`：

`https://你的用户名.github.io/global-holiday-calendar/holiday.ics`

## 自动更新

GitHub Actions 每月运行一次，也可以在 Actions 页面手动运行 `Update global holiday calendar`。

中国法定节假日最终以国务院当年正式发布的安排为准。本项目使用公开的官方数据衍生源来补充中国调休信息。

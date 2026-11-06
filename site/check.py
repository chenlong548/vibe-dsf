#!/usr/bin/env python3
"""site/check.py — 静态展示页的发布自检（CI 与 docs/23 发布清单都跑它）。

检查项：
  1. 零外部资源依赖（脚本/样式/图片/CSS @import 不得外链）；
  2. EN/中文 i18n key 成对且非空；
  3. 必需锚点存在、页内 #链接 都有落点；
  4. meta / 品牌色 / reduced-motion / 配套资产齐全；
  5. 页脚展示的版本与仓库根 VERSION 一致（防止发布时忘同步）。

用法：python site/check.py
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
HTML = HERE / "index.html"
REQUIRED_IDS = ("top", "how", "qa", "work", "engage", "faq")
REQUIRED_META = ("charset", "viewport", "theme-color", "description")


class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.anchors = []
        self.i18n = 0
        self.bad_i18n = []
        self.metas = set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids.add(d["id"])
        h = d.get("href", "")
        if h.startswith("#") and len(h) > 1:
            self.anchors.append(h[1:])
        if tag == "meta":
            if "charset" in d:
                self.metas.add("charset")
            if d.get("name"):
                self.metas.add(d["name"])
            if d.get("property", "").startswith("og:"):
                self.metas.add("og")
        en, zh = d.get("data-en"), d.get("data-zh")
        if en is not None or zh is not None:
            self.i18n += 1
            if not en or not zh:
                self.bad_i18n.append((tag, d.get("id") or d.get("class") or "?"))


def main():
    errors = []
    if not HTML.exists():
        print("[site] FAIL index.html 不存在")
        return 1
    text = HTML.read_text(encoding="utf-8")

    s = Scan()
    s.feed(text)

    # 1. 零外部资源依赖
    external = [
        (r"<script[^>]+src\s*=\s*[\"']https?://", "外部脚本"),
        (r"<link[^>]+href\s*=\s*[\"']https?://", "外部 link 资源"),
        (r"<img[^>]+src\s*=\s*[\"']https?://", "外部图片"),
        (r"@import\s+url\(", "CSS @import"),
        (r"url\(\s*[\"']?https?://", "CSS 外链 url"),
    ]
    for pat, label in external:
        if re.search(pat, text, re.I):
            errors.append(f"存在{label}（站点必须离线可开）")

    # 2. i18n
    if s.bad_i18n:
        errors.append(f"{len(s.bad_i18n)} 个元素的 data-en/data-zh 不成对或为空：{s.bad_i18n[:5]}")
    if s.i18n < 60:
        errors.append(f"i18n 覆盖过少（{s.i18n} 个），疑似漏标文案")

    # 3. 锚点
    for rid in REQUIRED_IDS:
        if rid not in s.ids:
            errors.append(f"缺少必需锚点 #{rid}")
    for a in set(s.anchors):
        if a not in s.ids:
            errors.append(f"页内链接 #{a} 没有落点")

    # 4. meta / 品牌 / 动效降级 / 资产
    for m in REQUIRED_META:
        if m not in s.metas:
            errors.append(f"缺少 meta: {m}")
    if "og" not in s.metas:
        errors.append("缺少 og:* 分享信息")
    if "#E8A87C" not in text.upper():
        errors.append("唯一强调色 #E8A87C 缺失（与 brand/BRAND.md 不一致）")
    if "prefers-reduced-motion" not in text:
        errors.append("缺少 prefers-reduced-motion 降级")
    for name in ("favicon.svg", "og-card.svg"):
        if not (HERE / name).exists():
            errors.append(f"缺少配套资产 {name}")

    # 5. 版本同步
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if f"v{version}" not in text:
        errors.append(f"页脚版本未同步到 v{version}")

    if errors:
        print(f"[site] FAIL · {len(errors)} 项：")
        for e in errors:
            print("  -", e)
        return 1
    print(f"[site] OK · {s.i18n} 组双语文案 · {len(s.ids)} 个锚点 · "
          f"零外部依赖 · v{version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

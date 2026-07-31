#!/usr/bin/env python3
"""news/*.md のフロントマターから news/index.json（日付マニフェスト）を再生成する。

ビューワーは index.json の dates[] を日付ナビの選択肢として使う。
手書き更新は日付の追加漏れ・件数ズレを招くため、必ず本スクリプトで生成する。

使い方:
    python3 scripts/build_manifest.py           # 生成して書き込む
    python3 scripts/build_manifest.py --check   # 差分の有無だけ確認する（CI用・書き込まない）
"""

import datetime
import glob
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS_DIR = os.path.join(REPO_ROOT, "news")
MANIFEST_PATH = os.path.join(NEWS_DIR, "index.json")

WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]


def parse_front_matter(text):
    """先頭の --- 〜 --- を key: value として解析する。"""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)

    if not match:
        return {}

    meta = {}

    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()

    return meta


def fallback_label(date):
    """label が無い場合に YYYYMMDD から日本語ラベルを組み立てる。"""
    try:
        d = datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8]))
    except ValueError:
        return date

    return "{}年{}月{}日（{}）".format(d.year, d.month, d.day, WEEKDAYS[d.weekday()])


def build():
    entries = []

    for path in sorted(glob.glob(os.path.join(NEWS_DIR, "*.md"))):
        name = os.path.splitext(os.path.basename(path))[0]

        if not re.fullmatch(r"\d{8}", name):
            print("  スキップ（日付形式でないファイル名）: {}".format(os.path.basename(path)))
            continue

        with open(path, encoding="utf-8") as f:
            text = f.read()

        meta = parse_front_matter(text)
        date = meta.get("date", name)
        label = meta.get("label") or fallback_label(date)

        try:
            count = int(meta.get("count", ""))
        except ValueError:
            count = len(re.findall(r"^### ", text, re.M))

        entries.append({"date": date, "label": label, "count": count})

    if not entries:
        print("エラー: news/ に YYYYMMDD.md が1件もありません", file=sys.stderr)
        sys.exit(1)

    # ビューワー側でも降順ソートするが、マニフェスト自体も降順で保存しておく
    entries.sort(key=lambda e: e["date"], reverse=True)

    return {"latest": entries[0]["date"], "dates": entries}


def serialize(manifest):
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def main():
    check_only = "--check" in sys.argv
    manifest = build()
    rendered = serialize(manifest)

    current = ""

    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            current = f.read()

    print("latest: {} / 全 {} 日分".format(manifest["latest"], len(manifest["dates"])))

    if rendered == current:
        print("マニフェストは最新です（変更なし）")
        return

    if check_only:
        print("マニフェストに差分があります（--check のため書き込みませんでした）")
        sys.exit(1)

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        f.write(rendered)

    print("news/index.json を更新しました")


if __name__ == "__main__":
    main()

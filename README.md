# Morning Brief — ニュースビューワー

毎朝、世界・日本の最新トピックニュースをスマホで一望するための単一HTMLビューワーと、その日次データを置くリポジトリ。

**公開URL:** （Cloudflare Pages 接続後に記載）

---

## 構成

```
index.html            ビューワー本体（CSS/JSインラインの単一HTML完結・外部依存はGoogle Fontsのみ）
news/
  index.json          日付マニフェスト（latest ＋ dates[]）※自動生成・手書き禁止
  YYYYMMDD.md         日次ニュース本体（毎晩23時の自動リサーチが追加する）
scripts/
  build_manifest.py   news/*.md から index.json を再生成する
.github/workflows/
  build-manifest.yml  md追加をトリガーにマニフェストを自動再生成する
```

このリポジトリは **ビューワーと公開データのみ** を置く。企画・仕様・検討経緯は社内ワークスペース側で管理する。

---

## 更新フロー

```
毎晩 23:03 JST  自動リサーチが news/YYYYMMDD.md を main に push
      ↓
GitHub Actions  news/index.json を md 群から再生成してコミット
      ↓
Cloudflare Pages  push を検知して自動デプロイ
      ↓
翌朝           スマホのホーム画面から閲覧
```

手動でニュースを追加した場合も、`news/YYYYMMDD.md` を置いて push すれば同じ経路で反映される。

ローカルでマニフェストを確認・更新したい場合:

```bash
python3 scripts/build_manifest.py           # 再生成する
python3 scripts/build_manifest.py --check   # 差分の有無だけ確認する
```

---

## データ書式

### `news/index.json`

```json
{
  "latest": "20260728",
  "dates": [
    { "date": "20260728", "label": "2026年7月28日（火）", "count": 17 }
  ]
}
```

- `latest` … 初期表示する日付。無ければ `dates[0].date` を採用
- `dates[]` … 日付ナビの選択肢。ビューワー側でも降順ソートするため順不同で可

### `news/YYYYMMDD.md`（UTF-8・区切りは全角パイプ `｜`）

```
---
date: 20260728
label: 2026年7月28日（火）
coverage: 2026年7月27日 23:00 〜 7月28日 23:00（JST）
updated: 2026-07-28T23:00:00+09:00
count: 17
---

## 政治

### [high｜日本] タイトル
概要：本文（3〜4文・1行）
視点：押さえる視点（1文）
出典：NHK ｜ 2026-07-27 ｜ https://...
```

- カテゴリは `## ` 見出し。固定順 `政治` → `経済・金融` → `テクノロジー・IT` → `スポーツ` → `国際`
- 各項目は `### [重要度｜地域] タイトル`。重要度は `high` / `mid` / `low`、地域は `日本` / `海外`
- `### ` の直後に `概要：` `視点：` `出典：` を各1行。キーは全角コロン
- `出典：` は `媒体名 ｜ 公開日(YYYY-MM-DD) ｜ URL`。URLは実在記事のみ
- 各カテゴリ3〜5件、合計15〜22件

書式から外れた項目はビューワー側が除外して描画を継続する（`title` 欠損項目・空カテゴリは非表示、未知のカテゴリ名は既定色で表示）。

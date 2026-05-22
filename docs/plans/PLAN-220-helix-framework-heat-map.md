---
plan_id: PLAN-220
title: "HELIX framework heat map (使用頻度可視化)"
kind: impl
layer: L4
drive: be
status: draft
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: tl-advisor
    slot_label: "TL adversarial check — heat map 集計設計 (helix.db join / index 妥当性) review"
  - role: se
    slot_label: "SE — heat_map_collector.py 実装・helix-heatmap CLI 実装・HTML テンプレート生成"
  - role: qa
    slot_label: "QA — pytest test 設計・集計境界テスト・HTML 出力検証"
  - role: pmo-sonnet
    slot_label: "PMO — 関連 PLAN (PLAN-134 / PLAN-179) との整合確認・Sprint review"
generates:
  - artifact_type: python_module
    path: cli/lib/heat_map_collector.py
  - artifact_type: cli_extension
    path: cli/helix-heatmap
  - artifact_type: test
    path: cli/lib/tests/test_heat_map_collector.py
dependencies:
  requires:
    - PLAN-134
  blocks: []
  parent: PLAN-MM-001
related_adr: []
related_docs:
  - cli/lib/helix_db.py
  - cli/helix-metrics
  - docs/plans/PLAN-134-helix-metrics-cli.md
  - docs/plans/PLAN-179-skill-recommender-accuracy-metrics.md
  - docs/plans/PLAN-160-helix-mkdocs-site.md
acceptance_criteria:
  - "helix heatmap --target skill --since 30d --format table が skill 別使用回数をテーブルで出力する"
  - "helix heatmap --target hook --format json が hook 別呼び出し回数を JSON で出力する"
  - "helix heatmap --target cli --format json が CLI サブコマンド別呼び出し回数を JSON で出力する"
  - "--target plan が PLAN ステータス遷移回数を集計して出力する"
  - "--format html が heat map 付き HTML を生成し mkdocs docs/ 配下に配置できる"
  - "python3 -m py_compile cli/lib/heat_map_collector.py PASS"
  - "pytest test_heat_map_collector.py 全 PASS"
  - "helix heatmap --help で usage が表示される"
---

# PLAN-220: HELIX framework heat map (使用頻度可視化)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 helix.db を参照する新規 CLI の追加** であり、
新規の大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:
- helix.db 集計クエリは既存 schema (skill_usage / hook_invocations /
  codex_invocations / plan_status_changes 等) への read-only SELECT のみ
- CLI 体系は既存 `cli/helix-*` パターンに準拠
- HTML 生成は標準 Python string.Template のみ使用、外部 SPA framework は不使用

## 背景

HELIX framework は skill / hook / CLI サブコマンド / PLAN が増加し続けているが、
「実際に使われているもの」と「全く使われていないもの」を定量的に把握する手段がない。

現状の問題:

1. **framework polish の優先順位が不明**: 107 skill / 30 CLI role / 19 subagent のうち
   どれが日常的に使われているかを数値で確認できず、改善対象の選定が属人的になっている
2. **デッドコード / 未使用 hook の検出**: helix.db に記録はあるが、
   集計・可視化する CLI が存在せず、未使用 component が放置されるリスクがある
3. **PLAN-134 metrics との連携不足**: session 別 metrics (PLAN-134) は時系列の
   変化量を集計するが、component 別のヒートマップは別の観点で必要
4. **PLAN-179 推薦精度改善への寄与**: skill 推薦 (PLAN-179) の改善には
   実使用頻度データが不可欠だが、集計基盤が未整備

`helix heatmap` CLI を導入し、framework の使用実態を可視化する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **HELIX 内部 CLI の新規追加** であり、外部ライブラリへの新規依存なし。
WebSearch **skip**。

skip 理由:
- helix.db からの SQLite SELECT 集計は標準 Python sqlite3 module のみ使用
- HTML 出力は標準 `string.Template` / f-string のみ、外部テンプレートエンジン不使用
- CLI 体系は既存 `cli/helix-*` (bash dispatch + Python helper) パターンと同型

## 設計方針

### 対象 target と集計元

| --target | 集計元テーブル | 集計キー | 説明 |
|---|---|---|---|
| `skill` | `skill_usage` | `skill_id` | skill 別呼び出し回数 |
| `hook` | `hook_invocations` | `hook_name` | hook 別呼び出し回数 |
| `cli` | `invocation` | `subcommand` | CLI サブコマンド別呼び出し |
| `plan` | `plan_status_changes` | `plan_id` | PLAN ステータス遷移回数 |

テーブルが helix.db に存在しない場合は graceful degradation (空結果を返す)。

### 出力形式

#### テーブル形式 (--format table、デフォルト)

```
$ helix heatmap --target skill --since 30d
Heat map: skill (past 30 days)

  Rank  Skill ID                          Count  Bar
     1  common/testing                       42  ████████████████████
     2  workflow/verification                38  ██████████████████
     3  workflow/design-doc                  21  ██████████
    ...
    85  advanced/i18n                         0  (unused)
```

#### JSON 形式 (--format json)

```json
{
  "generated_at": "2026-05-23T14:00:00Z",
  "target": "skill",
  "since": "2026-04-23",
  "entries": [
    {"id": "common/testing", "count": 42, "rank": 1},
    {"id": "workflow/verification", "count": 38, "rank": 2}
  ],
  "unused_count": 22
}
```

#### HTML 形式 (--format html)

- `string.Template` による静的 HTML 生成 (外部依存なし)
- 色付きセル (高頻度: 濃い青、未使用: 灰色) を CSS inline style で表現
- `--output PATH` で出力先を指定 (デフォルト: `docs/heatmap-{target}-{date}.html`)
- mkdocs site (PLAN-160) embed 用に `<div>` 単体としても出力可能 (`--embed`)

### CLI インターフェース

```
helix heatmap [OPTIONS]

Options:
  --target {skill,hook,cli,plan}  集計対象 (必須)
  --since DURATION                集計期間 (例: 30d / 7d / 90d, default: 30d)
  --format {table,json,html}      出力形式 (default: table)
  --output PATH                   出力ファイルパス (--format html 時のみ)
  --embed                         HTML を <div> 単体で出力 (mkdocs embed 用)
  --top N                         上位 N 件のみ表示 (default: 全件)
  --show-unused                   未使用 component を明示表示 (default: true)
  --help                          usage 表示
```

## 実装計画

### Sprint .1: heat_map_collector.py 実装 (Codex se 委譲)

実施内容:

1. `cli/lib/heat_map_collector.py` 新規作成:
   - `HeatMapEntry` dataclass (id / count / rank)
   - `collect_heatmap(db_path, target, since_days)` → list[HeatMapEntry]
   - target ごとの SELECT クエリ分岐 (skill / hook / cli / plan)
   - テーブル不在時は空リストを返す graceful degradation
   - `python3 -m py_compile` PASS を mandatory とする

2. 集計クエリ:
   - skill: `SELECT skill_id, COUNT(*) as cnt FROM skill_usage WHERE used_at >= ? GROUP BY skill_id ORDER BY cnt DESC`
   - hook: `SELECT hook_name, COUNT(*) as cnt FROM hook_invocations WHERE invoked_at >= ? GROUP BY hook_name ORDER BY cnt DESC`
   - cli: `SELECT subcommand, COUNT(*) as cnt FROM invocation WHERE invoked_at >= ? GROUP BY subcommand ORDER BY cnt DESC`
   - plan: `SELECT plan_id, COUNT(*) as cnt FROM plan_status_changes WHERE changed_at >= ? GROUP BY plan_id ORDER BY cnt DESC`

Sprint .1 完了条件:
- `py_compile` PASS
- `collect_heatmap` が 4 target すべてで空リストまたは正常結果を返す

### Sprint .2: helix-heatmap CLI + HTML 生成 (Codex se 委譲)

実施内容:

1. `cli/helix-heatmap` 新規作成 (bash):
   - `--target` / `--since` / `--format` / `--output` / `--embed` / `--top` 引数パース
   - `python3 cli/lib/heat_map_collector.py` への委譲
   - table / json / html 出力分岐

2. HTML 生成 (`string.Template` 使用):
   - 色付きヒートマップセルを CSS inline style で表現
   - `--embed` フラグで `<div>` 単体出力

3. `cli/helix` のルーターに `heatmap` サブコマンド登録

Sprint .2 完了条件:
- `helix heatmap --help` で usage 表示
- `helix heatmap --target skill --format json` で JSON 出力
- `helix heatmap --target skill --format html --output /tmp/test.html` でファイル生成

### Sprint .3: pytest test (Codex qa 委譲)

対象: `cli/lib/tests/test_heat_map_collector.py`

| ケース | 内容 |
|---|---|
| T1-001 | skill fixture DB → count 降順で rank 付与 |
| T1-002 | since_days 境界: 期間外レコードが除外される |
| T1-003 | テーブル不在 DB → 空リスト (例外なし) |
| T2-001 | hook target → hook_invocations 集計 |
| T3-001 | cli target → invocation.subcommand 集計 |
| T4-001 | plan target → plan_status_changes 集計 |
| T5-001 | unused_count: count=0 の component 数が正確 |
| T5-002 | JSON 出力スキーマ: generated_at / target / entries / unused_count 全項目存在 |

mandatory in sprint:
- `pytest test_heat_map_collector.py -v` 全 8 ケース PASS
- セルフレビュー (Codex qa 内)
- pmo-sonnet review (Sprint Exit、PLAN-134 / PLAN-179 整合確認含む)

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/heat_map_collector.py` PASS
- [ ] pytest `test_heat_map_collector.py` 全 PASS
- [ ] `helix heatmap --help` 表示確認
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)
- [ ] tl-advisor adversarial check (Sprint .1 完了後、集計 schema join 妥当性)
- [ ] commit message に `PLAN-220 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `cli/lib/heat_map_collector.py` 実装済、`py_compile` PASS
- [ ] `cli/helix-heatmap` 実装済、`helix heatmap --help` 表示
- [ ] `cli/helix` ルーターに `heatmap` サブコマンド登録済
- [ ] 4 target (skill / hook / cli / plan) すべてで集計が動作する
- [ ] `--format table / json / html` 3 形式すべてで出力が動作する
- [ ] pytest 全 8 ケース PASS
- [ ] graceful degradation: テーブル不在で例外なし
- [ ] helix doctor pass 数が現行以上

## carry / 学び (起票時記録)

- Sprint .1 着手前に `sqlite3 .helix/helix.db ".tables"` で `skill_usage` / `hook_invocations` /
  `plan_status_changes` の実在を確認し、テーブル名が異なる場合はクエリを調整する
- PLAN-160 embed 手順との整合は Sprint .2 実装時に確認する
- PLAN-179 との連携インターフェース (heat map データの渡し方) は PLAN-179 側で定義する

## 関連 reference

- PLAN-134 (helix metrics CLI、session 別集計との分業)
- PLAN-179 (skill recommender accuracy、heat map データの活用先)
- PLAN-160 (helix mkdocs site、HTML embed の展開先)
- cli/lib/helix_db.py (SQLite access layer、schema 定義の正本)

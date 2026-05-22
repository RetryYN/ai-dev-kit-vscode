---
plan_id: PLAN-121
title: "skill recommender improvement (gpt-5.4-mini prompt tuning + cache TTL 拡張)"
status: draft
kind: refactor
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — prompt template 更新・cache 戦略実装"
  - role: qa
    slot_label: "QA — precision/recall 測定 test set 構築・30 タスク検証"
  - role: pmo-sonnet
    slot_label: "PMO — agent 決定マッピング drift 確認・DoD 整合チェック"
generates:
  - artifact_type: template
    path: cli/templates/prompts/skill-search.md
  - artifact_type: python_module
    path: cli/lib/skill_recommender.py
  - artifact_type: test
    path: cli/lib/tests/test_skill_recommender_precision.py
dependencies:
  requires:
    - PLAN-022
  blocks: []
  parent: null
related_docs:
  - cli/templates/prompts/skill-search.md
  - cli/lib/skill_recommender.py
  - cli/lib/skill_dispatcher.py
  - SKILL_MAP.md §自動推挙システム
acceptance_criteria:
  - "prompt template の agent 決定マッピングが 9 種 → 13 種に更新されている"
  - "新 4 skill (doc-system-architect / requirements-deriver / god-writing / gpt-image) が recommender に反映される"
  - "cache TTL が 1h → 24h に延長、かつ task-hash + skill-catalog-hash の二段 cache が実装されている"
  - "30 タスク test set で recommend precision が baseline から +10% 以上改善されている"
  - "cache hit rate が +30% 以上改善されている (test set 再実行で計測)"
  - "python3 -m py_compile cli/lib/skill_recommender.py PASS"
  - "pytest cli/lib/tests/test_skill_recommender_precision.py 全 PASS"
---

# PLAN-121: skill recommender improvement (gpt-5.4-mini prompt tuning + cache TTL 拡張)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 PLAN-022 skill recommender framework の内部改善** であり、
新規の大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:

- skill recommender 基盤は PLAN-022 で確立済み (gpt-5.4-mini / cache / dispatcher)
- agent 決定マッピング更新は prompt template の追記のみ (framework 変更なし)
- cache 戦略改善は既存 `.helix/cache/recommendations/<sha256>.json` 構造の拡張
- precision 測定は新規 test file の追加 (既存 pytest infrastructure 利用)

## §1 背景・目的

### 1.1 PLAN-022 稼働後の改善余地

PLAN-022 (2026-05-06 完遂) により `helix skill chain "<task>"` の自動推挙 pipeline が稼働している。
実稼働から約 3 週間で以下の課題が顕在化した。

**課題 1: agent 決定マッピングの outdated**

`cli/templates/prompts/skill-search.md` に 9 種の agent 決定マッピングが定義されているが、
本 session (2026-05-23) で 4 skill が追加されている:

- `skills/writing/god-writing/` — 広告 LP / SEO 記事 / SNS の高密度ライティング
- `skills/advanced/doc-system-architect/` — ドキュメント体系設計
- `skills/advanced/requirements-deriver/` — 要件導出
- `skills/agent-skills/gpt-image/` — GPT-4o image 生成

これら 4 skill は prompt template に反映されていないため、
`helix skill chain "LP 起草"` 等で god-writing が選ばれない状態が発生する。

**課題 2: cache TTL 1 時間の非効率**

同一タスク (例: 毎朝の定型委譲) で 1 時間以上間隔が空くと cache miss が発生し、
毎回 gpt-5.4-mini 呼び出しが走る。skill catalog が変更されない限り結果は同一であるにもかかわらず、
コストと遅延が生じている。

**課題 3: LLM matching 精度の未計測**

PLAN-022 以降、precision/recall を定量測定していない。
description / triggers の重み調整効果を検証する test set がない。

### 1.2 解決ゴール

1. prompt template に 4 skill を追加し、agent 決定マッピングを 9 → 13 種に更新する
2. cache TTL を 24h に延長し、task-hash + skill-catalog-hash の二段 cache で staleness を管理する
3. 30 タスク test set で precision/recall baseline を計測し、改善幅を定量化する

## §2 WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **HELIX 内部 CLI の prompt tuning と cache 戦略** であり、
外部ライブラリ / 業界 standard への新規依存なし。WebSearch **skip**。

skip 理由:

- gpt-5.4-mini ベース推挙は PLAN-022 で確立済の内部 framework
- cache 戦略 (task-hash + catalog-hash) は Python hashlib 標準機能のみ
- precision 測定は pytest + json fixture のみで完結

## §3 設計方針

### Sprint .1 — prompt template 更新 (agent 決定マッピング 9 → 13 種)

**対象ファイル**: `cli/templates/prompts/skill-search.md`

現行 9 種マッピング (PLAN-022 起票時):

```
tl / se / pe / qa / security / dba / devops / docs / research
```

追加 4 skill の agent 割当方針:

| skill | agent | 理由 |
|---|---|---|
| god-writing | docs | ライティング成果物生成 → docs role |
| doc-system-architect | docs | ドキュメント体系設計 → docs role |
| requirements-deriver | tl | 要件導出は設計判断 → TL |
| gpt-image | docs | 画像生成 prompt 起草 → docs role |

prompt section 追記方針:
- 既存マッピング section の末尾に 4 エントリを追加
- 各エントリに `trigger_keywords` と `example_task` を付記
- 合計マッピング数を header で明示 (9 → 13)

### Sprint .2 — cache TTL + 二段 cache 実装

**対象ファイル**: `cli/lib/skill_recommender.py`

現行 cache 構造:

```python
cache_key = sha256(task_text).hexdigest()
cache_path = CACHE_DIR / f"{cache_key}.json"
# TTL: 3600秒 (1h)
```

改善後 cache 構造:

```python
catalog_hash = sha256(skill_catalog_json).hexdigest()[:8]
task_hash    = sha256(task_text).hexdigest()[:16]
cache_key    = f"{task_hash}_{catalog_hash}"
cache_path   = CACHE_DIR / f"{cache_key}.json"
# TTL: 86400秒 (24h)
```

二段 cache の利点:
- skill catalog が更新されると `catalog_hash` が変わり、古い推奨が自動 invalidate される
- task が同一で catalog が変わらなければ 24h 内は cache hit

catalog_hash 取得:

```python
from cli.lib.skill_catalog import load_catalog
catalog_hash = sha256(json.dumps(load_catalog(), sort_keys=True).encode()).hexdigest()[:8]
```

### Sprint .3 — precision 測定 test set 構築

**対象ファイル**: `cli/lib/tests/test_skill_recommender_precision.py`

30 タスク test set の設計方針:

| カテゴリ | タスク数 | 例 |
|---|---|---|
| ライティング系 | 8 | "LP 起草", "SEO 記事 3000 字", "SNS コピー 5 パターン" |
| 設計・要件系 | 8 | "API 設計", "要件定義", "ADR 起票", "ER 図設計" |
| 実装系 | 7 | "バグ修正", "単体テスト追加", "リファクタリング" |
| インフラ・セキュリティ系 | 4 | "CICD 設定", "脆弱性監査" |
| ドキュメント体系 | 3 | "ドキュメント構造設計", "技術仕様書" |

precision 計測方法:

```python
def test_recommend_precision():
    """30 タスク test set で top-1 precision を計測する"""
    results = []
    for task, expected_skills in TEST_SET:
        recommended = recommend(task, n=3)
        hit = any(s in recommended for s in expected_skills)
        results.append(hit)
    precision = sum(results) / len(results)
    # baseline 記録 (初回実行時に JSON で保存)
    assert precision >= BASELINE_PRECISION * 1.10  # +10% 改善必須
```

baseline は Sprint .3 初回実行時に `.helix/cache/recommender-baseline.json` に記録する。

## §4 実装 Sprint

### Sprint .1: prompt template 更新

- 担当: SE
- 対象: `cli/templates/prompts/skill-search.md`
- 作業: agent 決定マッピング 9 → 13 種追記 (4 新 skill + trigger_keywords)
- 検証: `bash -n` + 手動 `helix skill chain "LP 起草"` で god-writing が top-3 に出ることを確認
- 想定: 30 分

### Sprint .2: cache 戦略改善

- 担当: SE
- 対象: `cli/lib/skill_recommender.py`
- 作業: 二段 cache key 実装 + TTL 1h → 24h 変更
- 検証: `python3 -m py_compile` + pytest で cache hit/miss シナリオ確認
- 想定: 60 分

### Sprint .3: precision 測定 test set

- 担当: QA
- 対象: `cli/lib/tests/test_skill_recommender_precision.py`
- 作業: 30 タスク test set 作成 + precision 計測 + baseline JSON 記録
- 検証: pytest PASS + baseline ファイル生成確認
- 想定: 90 分

## §5 DoD (完了条件)

- [ ] Sprint .1: agent 決定マッピングが 13 種に更新され、4 新 skill が選択候補に入る
- [ ] Sprint .2: cache TTL 24h + 二段 cache が動作し、catalog 更新時に自動 invalidate される
- [ ] Sprint .3: 30 タスク test set で precision baseline が記録され、+10% 改善を定量確認
- [ ] python3 -m py_compile cli/lib/skill_recommender.py PASS
- [ ] pytest cli/lib/tests/test_skill_recommender_precision.py 全 PASS
- [ ] helix doctor warn 増加なし

## §6 関連

- PLAN-022: skill recommender pipeline 基盤 (本 PLAN の前提)
- PLAN-109: skill catalog rebuild hook (catalog 更新トリガと二段 cache invalidate の連携点)
- 本 session 統合 4 skill: god-writing / doc-system-architect / requirements-deriver / gpt-image

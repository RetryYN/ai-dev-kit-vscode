---
plan_id: PLAN-122
title: "helix skill chain auto-execution (skill use chaining)"
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
kind: impl
drive: be
layer: L4
size: S
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — chain_next field 実装・auto-execute CLI flag 実装"
  - role: qa
    slot_label: "QA — 3 シナリオ (LP / SEO / FE) chain 動作確認"
  - role: pmo-sonnet
    slot_label: "PMO — skill dependency graph 設計の整合確認・DoD チェック"
generates:
  - artifact_type: python_module
    path: cli/lib/skill_dispatcher.py
  - artifact_type: cli_extension
    path: cli/helix-skill
  - artifact_type: test
    path: cli/lib/tests/test_skill_chain_auto_execute.py
dependencies:
  requires:
    - PLAN-022
  blocks: []
  parent: null
related_docs:
  - cli/lib/skill_dispatcher.py
  - cli/lib/skill_catalog.py
  - cli/helix-skill
  - SKILL_MAP.md §自動推挙システム
acceptance_criteria:
  - "SKILL.md frontmatter に chain_next フィールドが定義できる"
  - "helix skill chain --auto-execute で chain_next を辿り最大 3 段自動実行される"
  - "LP 起草シナリオ: god-writing → gpt-image の 2 段 chain が動作する"
  - "SEO 記事シナリオ: god-writing 単独 (chain_next なし) が正常終了する"
  - "FE microcopy シナリオ: god-writing → frontend-ui-engineering の 2 段 chain が動作する"
  - "循環 chain (A → B → A) が安全に検出・中断される"
  - "python3 -m py_compile cli/lib/skill_dispatcher.py PASS"
  - "pytest cli/lib/tests/test_skill_chain_auto_execute.py 全 PASS"
---

# PLAN-122: helix skill chain auto-execution (skill use chaining)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 PLAN-022 skill chain framework の自動化拡張** であり、
新規の大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:

- skill dispatcher / catalog / chain 基盤は PLAN-022 で確立済み
- `chain_next` field は SKILL.md frontmatter の任意拡張であり、既存 field を破壊しない
- auto-execute は `--auto-execute` flag を追加するのみ (既存 `helix skill chain` は変更なし)
- 循環検出は DFS visited set で実装、既存 graph 構造への依存なし

## §1 背景・目的

### 1.1 手動 chain の限界

`helix skill chain "<task>"` は `search → use` の一気通貫を実現している (PLAN-022)。
しかし `use` の実行結果が次の skill への入力になるケースでは、手動で次の chain を起動する必要がある。

例: "LP ページを作る" タスクの理想 chain:

```
god-writing (LP コピー生成)
  → gpt-image (ヒーロー画像生成)
  → frontend-ui-engineering (FE 実装)
```

現状は各 skill を個別に `helix skill use` で呼び出す必要があり、
workflow として一貫した自動化ができていない。

### 1.2 解決ゴール

1. SKILL.md frontmatter に `chain_next` field を定義し、skill 間の連鎖関係を宣言できる
2. `helix skill chain --auto-execute` flag で chain_next を辿り、最大 N 段 (default 3) を自動実行する
3. 循環 chain を安全に検出して中断する
4. LP 起草 / SEO 記事 / FE microcopy の 3 シナリオで動作確認する

### 1.3 スコープ制限

本 PLAN のスコープは `chain_next` による **線形 chain** のみ。
分岐 (conditional chain) / 並列 (parallel chain) は対象外とし、必要時に別 PLAN で対応する。

## §2 WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **HELIX 内部 CLI の framework 拡張** であり、
外部ライブラリ / 業界 standard への新規依存なし。WebSearch **skip**。

skip 理由:

- skill dispatcher は PLAN-022 で確立済の内部 Python モジュール
- `chain_next` field は YAML frontmatter の optional field 追加のみ
- 循環検出アルゴリズム (DFS visited set) は標準 CS 知識の範囲

## §3 設計方針

### 3.1 SKILL.md frontmatter 拡張 (`chain_next` field)

SKILL.md の frontmatter に以下の optional field を追加する:

```yaml
chain_next:
  - skill_id: agent-skills/gpt-image
    condition: "画像が必要な場合"
    priority: 1
  - skill_id: common/visual-design
    condition: "デザイン調整が必要な場合"
    priority: 2
```

- `skill_id`: `skills/` 配下の相対パス (カテゴリ/スキル名)
- `condition`: chain を辿る条件の自然言語記述 (optional、ドキュメント目的)
- `priority`: 複数候補の優先順位 (1 が最優先)

既存 SKILL.md への後方互換性: `chain_next` がなければ chain は終了。既存 SKILL.md の変更は不要。

### 3.2 auto-execute 実装 (`cli/lib/skill_dispatcher.py`)

`dispatch_chain_auto()` 関数を追加する:

```python
def dispatch_chain_auto(
    task: str,
    initial_skill_id: str,
    max_depth: int = 3,
) -> list[str]:
    """
    skill を chain_next で辿り auto-execute する。
    循環は visited set で検出して中断。
    returns: 実行した skill_id のリスト
    """
    visited = set()
    executed = []
    current = initial_skill_id

    for depth in range(max_depth):
        if current in visited:
            # 循環 chain 検出: 中断
            break
        visited.add(current)
        _execute_skill(current, task)
        executed.append(current)

        skill_meta = load_skill_meta(current)
        chain_next = skill_meta.get("chain_next", [])
        if not chain_next:
            break
        # priority 昇順で最初の skill を選択
        chain_next_sorted = sorted(chain_next, key=lambda x: x.get("priority", 99))
        current = chain_next_sorted[0]["skill_id"]

    return executed
```

### 3.3 CLI flag 追加 (`cli/helix-skill`)

`helix skill chain` サブコマンドに `--auto-execute` flag を追加:

```bash
# 現行
helix skill chain "<task>" [-n 1]

# 拡張後
helix skill chain "<task>" [-n 1] [--auto-execute] [--max-depth 3]
```

`--auto-execute` なしの動作は既存と完全に同一 (後方互換)。

### 3.4 循環検出と安全性

- visited set に skill_id を記録
- 同一 skill_id が chain_next で再度出現した時点で `WARN: circular chain detected` を stderr に出力して中断
- max_depth (default 3) を超えた場合も `WARN: max chain depth reached` を出力して中断
- エラーで中断せず、ここまで実行した skill のリストを返す (fail-open)

### 3.5 3 シナリオ設計

| シナリオ | 初期 skill | chain_next | 検証観点 |
|---|---|---|---|
| LP 起草 | god-writing | → gpt-image | 2 段 chain、画像生成まで自動化 |
| SEO 記事 | god-writing | なし | chain_next 不在 = 1 段で正常終了 |
| FE microcopy | god-writing | → frontend-ui-engineering | 2 段 chain、FE 実装まで自動化 |

## §4 実装 Sprint

### Sprint .1: SKILL.md frontmatter 拡張 + catalog 対応

- 担当: SE
- 対象: `cli/lib/skill_catalog.py` (chain_next field の parse 追加)
- 作業: frontmatter parser に `chain_next` optional field を追加、catalog JSON に含める
- 検証: `python3 -m py_compile cli/lib/skill_catalog.py`
- 想定: 30 分

### Sprint .2: auto-execute 実装 + CLI flag

- 担当: SE
- 対象: `cli/lib/skill_dispatcher.py` + `cli/helix-skill`
- 作業: `dispatch_chain_auto()` 実装 + `--auto-execute` / `--max-depth` flag 追加
- 検証: `python3 -m py_compile` + `bash -n cli/helix-skill`
- 想定: 60 分

### Sprint .3: テスト + 3 シナリオ確認

- 担当: QA
- 対象: `cli/lib/tests/test_skill_chain_auto_execute.py`
- 作業: 3 シナリオ test + 循環検出 test + max_depth test 計 10 case
- 検証: pytest 全 PASS
- 想定: 60 分

## §5 DoD (完了条件)

- [ ] Sprint .1: skill_catalog が `chain_next` を parse して catalog JSON に含める
- [ ] Sprint .2: `helix skill chain --auto-execute` で chain_next を辿って最大 3 段実行される
- [ ] Sprint .2: 循環 chain が WARN で中断され、それ以前の実行は保持される
- [ ] Sprint .3: LP / SEO / FE の 3 シナリオが全て PASS
- [ ] python3 -m py_compile cli/lib/skill_dispatcher.py PASS
- [ ] pytest cli/lib/tests/test_skill_chain_auto_execute.py 全 PASS
- [ ] helix doctor warn 増加なし
- [ ] 既存 `helix skill chain` (--auto-execute なし) の動作が変わらない

## §6 関連

- PLAN-022: skill recommender pipeline 基盤 (chain 基盤の前提)
- PLAN-121: skill recommender improvement (precision 改善、chain 精度向上との相乗効果)
- god-writing SKILL.md: chain_next 最初の適用 skill として利用 (LP → gpt-image)
- gpt-image SKILL.md: god-writing の chain_next ターゲット

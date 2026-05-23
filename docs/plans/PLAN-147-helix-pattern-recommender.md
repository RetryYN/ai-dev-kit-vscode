---
plan_id: PLAN-147
title: "helix pattern recommender — recipe deprecated 後継 (session 横断 pattern 認識 + 再現提案)"
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
kind: design
drive: be
layer: L3
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: tl
    slot_label: "TL — 設計 ADR 凍結・helix.db schema 拡張方針決定"
  - role: se
    slot_label: "SE — pattern_extractor.py / pattern_recommender.py 実装・helix-pattern CLI 実装"
  - role: qa
    slot_label: "QA — パターン抽出精度テスト・推薦結果一貫性テスト構築"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 recipe CLI との互換性確認・DoD 整合チェック"
generates:
  - artifact_type: design_doc
    path: docs/plans/PLAN-147-helix-pattern-recommender.md
  - artifact_type: adr_snapshot
    path: docs/adr/ADR-051-helix-pattern-recommender-design.md
  - artifact_type: python_module
    path: cli/lib/pattern_extractor.py
  - artifact_type: python_module
    path: cli/lib/pattern_recommender.py
  - artifact_type: cli_extension
    path: cli/helix-pattern
  - artifact_type: test
    path: cli/lib/tests/test_pattern_extractor.py
  - artifact_type: test
    path: cli/lib/tests/test_pattern_recommender.py
dependencies:
  parent: null
  requires:
    - PLAN-022
  blocks: []
related_docs:
  - SKILL_MAP.md §自動推挙システム
  - cli/lib/skill_recommender.py
  - cli/lib/skill_dispatcher.py
acceptance_criteria:
  - "helix pattern learn --since 30d が skill_usage / commit_log / agent_dispatch テーブルからパターンを抽出し patterns テーブルに保存する"
  - "helix pattern recommend --task '...' が過去の成功パターン上位 3 件を返す"
  - "helix recipe (learn/promote/discover) が deprecated メッセージを表示し終了する (後方互換 shim)"
  - "python3 -m py_compile cli/lib/pattern_extractor.py PASS"
  - "python3 -m py_compile cli/lib/pattern_recommender.py PASS"
  - "pytest cli/lib/tests/test_pattern_extractor.py 全 PASS"
  - "pytest cli/lib/tests/test_pattern_recommender.py 全 PASS"
  - "helix doctor warn 増加なし"
---

# PLAN-147: helix pattern recommender — recipe deprecated 後継

## §1 背景・目的

### 1.1 recipe framework の経緯

PLAN-022 で `helix recipe` (learn/promote/discover) が deprecated 化された。
現状、CLI コマンドは dummy stub として残存しており、実際にはパターン蓄積・提案の機能を持たない。

`SKILL_MAP.md §自動推挙システム` の記述:

```
helix recipe <learn|promote|discover|list>  # learn/promote/discover は deprecated
```

deprecated の理由は、recipe が単発スキル推挙 (skill chain) と責務が重複し、
かつ session 横断のパターン学習という設計上の価値を実装していなかったためである。

### 1.2 新 framework の必要性

skill recommender (PLAN-022) が「タスク記述 → スキル推薦」を担う一方、
**「過去の成功パターンを横断的に抽出し、類似タスクへ再現提案する」** 機能は未実装のままである。

具体的な課題:

- 同種の委譲タスク (例: "Codex se に BE 実装委譲後 pmo-sonnet で review") が
  繰り返されるが、パターンとして認識・提案する仕組みがない
- commit pattern / Codex 委譲 pattern が helix.db に蓄積されているにもかかわらず活用されていない
- skill_usage テーブル統計 (`helix skill stats`) は存在するが、
  「どの組み合わせが成功したか」を抽出する推薦 pipeline がない

### 1.3 解決ゴール

1. `helix recipe` を正式 deprecated し、後継 `helix pattern` サブコマンド群を実装する
2. helix.db の skill_usage / commit 履歴 / agent_dispatch 記録から成功パターンを抽出する
3. gpt-5.4-mini ベースの推薦 pipeline で類似タスクへパターンを再現提案する

## §2 L2 凍結 (ADR snapshot)

本 PLAN tree は **新規 pattern recommender framework の設計判断** を含む。
ADR-051 snapshot を別途起票する。

対象判断:

- パターン抽出の単位定義 (skill chain 単位 vs commit 単位 vs セッション単位)
- gpt-5.4-mini ベース推薦 vs ルールベース推薦の選択
- helix.db schema 拡張方針 (patterns テーブル新設 vs skill_usage 拡張)
- `helix recipe` shim の後方互換期間

ADR-051 は PLAN-147 §3 設計方針確定後に TL 承認を経て凍結する。

## §3 設計方針

### 3.1 パターンの定義

本 framework における「パターン」は以下の 3 種を扱う:

| パターン種別 | 抽出元 | 説明 |
|---|---|---|
| skill_chain_pattern | skill_usage テーブル | 同一セッション内で連続して使用されたスキル列 |
| dispatch_pattern | agent_dispatch / handover | role 組み合わせ (例: se → pmo-sonnet review) が成功したシーケンス |
| commit_pattern | git log (optional) | 特定ファイル群への変更が特定スキル使用と相関するパターン |

### 3.2 CLI サブコマンド設計

```bash
# パターン抽出 (helix.db から --since N 日内を集計)
helix pattern learn [--since 30d] [--min-count 2]

# 過去パターンに基づく推薦
helix pattern recommend --task "..." [-n 3] [--json]

# 蓄積パターン一覧
helix pattern list [--kind skill_chain|dispatch|commit] [--json]

# パターン削除
helix pattern remove <pattern_id>
```

deprecated shim (後方互換):

```bash
helix recipe learn    # → "DEPRECATED: use 'helix pattern learn'" + exit 0
helix recipe promote  # → "DEPRECATED: recipe promote is no longer available" + exit 0
helix recipe discover # → "DEPRECATED: use 'helix skill chain' or 'helix pattern recommend'" + exit 0
```

### 3.3 helix.db schema 拡張 (patterns テーブル)

```sql
CREATE TABLE IF NOT EXISTS patterns (
    pattern_id   TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,  -- skill_chain | dispatch | commit
    pattern_data TEXT NOT NULL,  -- JSON: 抽出したパターン本体
    task_context TEXT,           -- 関連タスク記述 (nullable)
    success_count INTEGER DEFAULT 1,
    last_seen    TEXT NOT NULL,  -- ISO8601
    created_at   TEXT NOT NULL
);
```

### 3.4 pattern_extractor.py の設計

```python
class PatternExtractor:
    """
    helix.db の skill_usage / agent_dispatch テーブルを読み取り、
    patterns テーブルへ集約・更新する
    """

    MIN_OCCURRENCE = 2   # N 回以上出現で pattern 認定

    def extract_skill_chains(self, db_path: str, since_days: int) -> list[dict]:
        """skill_usage テーブルから同一セッション内の連続使用スキル列を抽出"""

    def extract_dispatch_patterns(self, db_path: str, since_days: int) -> list[dict]:
        """agent_dispatch / handover テーブルから成功シーケンスを抽出"""

    def upsert_patterns(self, db_path: str, patterns: list[dict]) -> int:
        """patterns テーブルへ upsert、success_count を累積加算して返す"""
```

### 3.5 pattern_recommender.py の設計

```python
class PatternRecommender:
    """
    gpt-5.4-mini を使い、入力タスク記述と patterns テーブルを突合して
    類似パターンを上位 N 件推薦する
    """

    MODEL = "gpt-5.4-mini"
    CACHE_TTL_SECONDS = 3600  # 1h

    def recommend(self, task: str, db_path: str, n: int = 3) -> list[dict]:
        """
        task 記述を embed/classify し、patterns テーブルの
        task_context との類似度上位 N 件を返す
        """
```

## §4 実装 Sprint 計画

### Sprint .1: deprecated shim + CLI skeleton

- 担当: SE
- 対象: `cli/helix-pattern` (bash), `cli/helix` (routing 行追加)
- 作業: deprecated shim 3 件 + `helix pattern learn/recommend/list/remove` skeleton
- 検証: `bash -n cli/helix-pattern` + `helix pattern --help` 動作確認
- 想定: 45 分

### Sprint .2: helix.db schema 拡張 + pattern_extractor.py

- 担当: SE
- 対象: `cli/lib/helix_db.py` (migration 追加), `cli/lib/pattern_extractor.py`
- 作業: patterns テーブル migration + PatternExtractor 実装
- 検証: `python3 -m py_compile` + `pytest cli/lib/tests/test_pattern_extractor.py`
- 想定: 90 分

### Sprint .3: pattern_recommender.py + ADR-051 起票

- 担当: SE (実装) / TL (ADR-051 凍結)
- 対象: `cli/lib/pattern_recommender.py`, `docs/adr/ADR-051-*.md`
- 作業: PatternRecommender 実装 + gpt-5.4-mini 推薦 pipeline + ADR-051 起票
- 検証: `python3 -m py_compile` + `pytest cli/lib/tests/test_pattern_recommender.py`
- 想定: 120 分

### Sprint .4: 統合 + DoD 確認

- 担当: QA / PMO
- 対象: `helix pattern learn/recommend` の E2E 確認
- 作業: fake helix.db fixture を使った統合テスト + recipe shim 動作確認
- 検証: pytest 全 PASS + helix doctor warn 増加なし
- 想定: 60 分

## §5 テスト設計

### test_pattern_extractor.py

| テスト ID | シナリオ | 期待値 |
|---|---|---|
| U-147-001 | skill_usage 3 件同一セッション → chain 抽出 | skill_chain_pattern 1 件 |
| U-147-002 | skill_usage 1 件のみ (MIN_OCCURRENCE 未満) | patterns 空 |
| U-147-003 | upsert 後に同一 pattern が再度抽出 | success_count += 1 |
| U-147-004 | since_days=7 で 8 日前データを除外 | 対象外データ含まず |
| U-147-005 | agent_dispatch 成功シーケンス 2 件 → dispatch_pattern | dispatch_pattern 1 件 |

### test_pattern_recommender.py

| テスト ID | シナリオ | 期待値 |
|---|---|---|
| U-147-006 | patterns テーブル空 → recommend | 空リスト返却 (エラーなし) |
| U-147-007 | task_context 完全一致 → top-1 に一致 | pattern_id 一致 |
| U-147-008 | n=3 で patterns が 2 件のみ | 2 件返却 |
| U-147-009 | cache hit (同一 task を 2 回呼び出し) | LLM 呼び出し 1 回のみ |

## §6 DoD (完了条件)

- [ ] Sprint .1: `helix recipe learn/promote/discover` が deprecated メッセージ表示 + exit 0
- [ ] Sprint .1: `helix pattern learn/recommend/list/remove --help` が動作する
- [ ] Sprint .2: patterns テーブルが helix.db に追加される (migration idempotent)
- [ ] Sprint .2: `pattern_extractor.py` が skill_chain / dispatch パターンを抽出できる
- [ ] Sprint .3: `pattern_recommender.py` が gpt-5.4-mini で上位 N 件を推薦できる
- [ ] Sprint .3: ADR-051 が TL 承認で凍結される
- [ ] Sprint .4: `python3 -m py_compile` 対象 2 モジュール PASS
- [ ] Sprint .4: `pytest cli/lib/tests/test_pattern_extractor.py` 全 PASS (5 ケース)
- [ ] Sprint .4: `pytest cli/lib/tests/test_pattern_recommender.py` 全 PASS (4 ケース)
- [ ] helix doctor warn 増加なし

## §7 V-model 4 artifact trace

| Artifact | ファイル |
|---|---|
| ① 設計 (本 PLAN §3-§5) | docs/plans/PLAN-147-helix-pattern-recommender.md |
| ② 実装コード | cli/lib/pattern_extractor.py / cli/lib/pattern_recommender.py / cli/helix-pattern |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-147-test-design.md (Sprint .3 完了後に起票) |
| ④ テストコード | cli/lib/tests/test_pattern_extractor.py / test_pattern_recommender.py |

- 設計 → テスト設計: テスト設計ファイル `docs/v2/L4-test-design/PLAN-147-test-design.md`
- テスト設計 → 設計: 対象設計 `PLAN-147 §3-§5`
- 設計 → 実装コード: 実装ファイル `cli/lib/pattern_extractor.py` / `cli/lib/pattern_recommender.py`
- テストコード → テスト設計: DoD 検証 `PLAN-147 U-147-001〜009`

## §8 関連

- PLAN-022: skill recommender pipeline 基盤 (本 PLAN の前提 / requires)
- ADR-051: 本 PLAN の L2 大局判断 snapshot (Sprint .3 で起票)
- `SKILL_MAP.md §自動推挙システム`: deprecated recipe 記述の正本
- `cli/lib/skill_recommender.py`: 類似コンポーネント (推薦 pipeline の参考)

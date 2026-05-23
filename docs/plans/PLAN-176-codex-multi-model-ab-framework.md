---
plan_id: PLAN-176
title: "PLAN-176: helix-codex multi-model A/B framework (gpt-5.3 vs gpt-5.4 vs gpt-5.5 比較)"
kind: design
layer: L4
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
size: M
created: "2026-05-23"
revised: "2026-05-23"
owner: PM
agent_slots:
  - role: tl
    slot_label: "TL — A/B 実行制御設計・並列 model 呼び出し仕様・結果比較 schema 設計"
  - role: se
    slot_label: "SE — helix codex --ab-test flag 実装・helix.db codex_ab_results schema + migration"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 helix-codex / ROLE_MAP.md との整合確認・cost ガードレール観点"
  - role: qa
    slot_label: "QA — A/B 結果の比較メトリクス検証・統計有意性テスト設計"
generates:
  - artifact_path: docs/plans/PLAN-176-codex-multi-model-ab-framework.md
    artifact_type: design_doc
  - artifact_path: cli/lib/codex_ab_runner.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_codex_ab_runner.py
    artifact_type: test
  - artifact_path: docs/commands/codex-ab-test.md
    artifact_type: markdown_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr: []
related_docs:
  - cli/ROLE_MAP.md
  - helix/HELIX_CORE.md
  - docs/plans/PLAN-091-plan-framework-v5-core.md
  - cli/lib/helix_db.py
acceptance_criteria:
  - "helix codex --ab-test --role se --models 'gpt-5.4,gpt-5.5' --task '...' が 2 model に同 task を並列投入する"
  - "結果 (出力 / elapsed_ms / estimated_cost) が helix.db codex_ab_results に記録される"
  - "helix codex ab-report --plan-id PLAN-NNN で集計レポートを出力する"
  - "python3 -m py_compile cli/lib/codex_ab_runner.py PASS"
  - "unit test 7 case 全 PASS"
---

# PLAN-176: helix-codex multi-model A/B framework

## L2 凍結 (ADR snapshot)

本 PLAN は **helix.db への新テーブル追加 (`codex_ab_results`)** を含む。
schema 変更は PLAN-092 (PostToolUse 自動登録 + helix.db schema) の管轄であり、
既存 migration 体系内の拡張として扱う。

ADR snapshot 要否判定:
- 新規 framework 採用: A/B 比較機能は既存 `helix codex` への additive extension → **新方針なし**
- helix.db 新テーブル: PLAN-092 (ADR-026) の管轄下の schema 拡張 → **ADR-026 で既に凍結済**
- 外部 API 変更なし

→ 本 PLAN tree 内に L2 大局判断は含まない。ADR snapshot は不要。

## 背景

PE / SE / TL の model 選択は `cli/ROLE_MAP.md` で固定されている。
しかし実際のタスクでは、以下の状況が発生している。

### 問題

1. **model 選択の根拠が感覚的**: gpt-5.4 vs gpt-5.5 の精度差がタスク種別によって
   異なる可能性があるが、実測データがない。
2. **コスト最適化の機会損失**: gpt-5.5 high が必要ないタスクに gpt-5.5 を使い続けている
   可能性がある (コスト比: gpt-5.5 ≫ gpt-5.4 > gpt-5.3)。
3. **ROLE_MAP 固定の硬直**: 新 model (gpt-5.X) 登場時の評価フローが定義されていない。

### 解決方針

同一タスクを複数 model に並列投入し、出力品質 / 実行時間 / コストを定量比較する
A/B framework を実装する。蓄積データから ROLE_MAP の更新根拠を自動生成する。

## 設計方針

### CLI インタフェース

```bash
# 2 model A/B 比較
helix codex --ab-test --role se --models "gpt-5.4,gpt-5.5" --task "..."

# 3 model 比較
helix codex --ab-test --role pe --models "gpt-5.3,gpt-5.3-spark,gpt-5.4" --task "..."

# plan 単位での集計レポート
helix codex ab-report --plan-id PLAN-NNN
helix codex ab-report --role se --last 30d

# ROLE_MAP 更新提案
helix codex ab-recommend --role se
```

### 実行フロー

```
helix codex --ab-test
    ↓
codex_ab_runner.run_ab(task, models, role)
    ↓ 並列投入 (subprocess × N)
┌───────────────────────────────────────┐
│  model A: gpt-5.4  │  model B: gpt-5.5  │
│  elapsed_ms / cost  │  elapsed_ms / cost  │
└───────────────────────────────────────┘
    ↓ 結果を helix.db codex_ab_results に INSERT
    ↓ diff 表示 (unified diff + サマリ)
```

### helix.db schema 拡張

`codex_ab_results` テーブル (v36 migration):
主要カラム = `run_id (UUID) / plan_id / task_id / role / model / task_hash (SHA-256) /
elapsed_ms / estimated_cost_usd / output_length / output_sha256 / quality_score (nullable) / created_at`。
index = `run_id` + `(role, model)` の 2 件。migration は idempotent (T6 で検証)。

### 比較メトリクス

| メトリクス | 説明 | 収集方法 |
|---|---|---|
| `elapsed_ms` | model の応答時間 | subprocess タイマー |
| `estimated_cost_usd` | 推定コスト | ROLE_MAP の rate × token 数 |
| `output_length` | 出力文字数 | len(output) |
| `quality_score` | 品質スコア | 初版は null、将来 LLM judge |

初版は自動品質評価なし（quality_score は null）。人間が `helix codex ab-report` を見て
手動スコアを入力する運用。LLM judge は別 PLAN に委譲。

### cost ガードレール

A/B テストはコスト倍増リスクがあるため、以下を強制する:

- `--ab-test` 使用時に budget チェック (`helix budget status`) を先行実行
- 残 budget < 20% の場合は確認プロンプト (or `--force` で bypass)
- 1 回の A/B run の推定コスト上限: デフォルト 0.50 USD (`--max-cost` でオーバーライド可)

## 実装計画

### Sprint .1: Python module 実装 (SE 委譲、size M)

**Entry 条件**: helix.db migration 番号確認 (現行 v35)

`cli/lib/codex_ab_runner.py`: `ABResult` dataclass + `run_ab` (ThreadPoolExecutor 並列) +
`insert_ab_results` + `check_budget_before_run`。helix.db v36 migration 追加。
単体テスト 7 case (T1: dataclass / T2: mock subprocess / T3: DB round-trip / T4-T5: budget guard /
T6: idempotent migration / T7: task_hash deterministic)。

受入条件: `python3 -m py_compile` PASS / unit test 7 PASS / v36 idempotent 確認

### Sprint .2: CLI 統合 (SE 委譲、size S)

**Entry 条件**: Sprint .1 module PASS

実施内容:
1. `cli/helix-codex` に `--ab-test` / `--models` オプション追加
   - `--models "gpt-5.4,gpt-5.5"` をパースして `codex_ab_runner.run_ab` に渡す
   - `--max-cost 0.50` オプション追加
2. `cli/helix-codex` に `ab-report` サブコマンド追加
   - `--plan-id` / `--role` / `--last <days>` フィルタ
   - テーブル形式で集計出力 (model 別: avg elapsed / avg cost / run 数)
3. `bash -n cli/helix-codex` PASS (mandatory in sprint)
4. 既存 bats テスト影響なし確認

受入条件:
- `helix codex --ab-test --role se --models "gpt-5.4,gpt-5.5" --task "hello"` 動作確認
- `helix codex ab-report --role se` で集計テーブル出力確認
- bats 回帰テスト PASS

### Sprint .3: docs + QA メトリクス検証 (QA / Docs 委譲、size S)

**Entry 条件**: Sprint .2 CLI 動作確認済

実施内容:
1. `docs/commands/codex-ab-test.md` 起草
   - コマンドリファレンス・ユースケース例・ROLE_MAP 更新フロー
2. 実 task 3 種 × 2 model で A/B 試行
   - role=se: 小規模実装タスク
   - role=pe: 単機能速度重視タスク
   - role=tl: 設計レビュータスク
3. 統計的有意性チェック: 3 試行は少ないため P2 carry として結論留保

受入条件:
- `docs/commands/codex-ab-test.md` 作成済
- 3 種試行の raw data が helix.db に記録済
- `helix codex ab-report` で 3 試行の集計が確認できる

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/codex_ab_runner.py` PASS
- [ ] unit test 7 case PASS
- [ ] v36 migration idempotent 確認
- [ ] `bash -n cli/helix-codex` PASS
- [ ] bats 回帰テスト PASS (既存挙動影響なし)
- [ ] pmo-sonnet review (Sprint .2 完了後)

## DoD

- [ ] `cli/lib/codex_ab_runner.py` 実装・`python3 -m py_compile` PASS
- [ ] helix.db v36 migration 追加・idempotent 確認
- [ ] unit test 7 case PASS
- [ ] `helix codex --ab-test --models "..."` 動作確認
- [ ] `helix codex ab-report` で集計出力確認
- [ ] bats 回帰テスト PASS
- [ ] `docs/commands/codex-ab-test.md` 作成済
- [ ] helix doctor pass 数現行以上維持

## V-model 4 artifact trace

| artifact | パス |
|---|---|
| ① 設計 | docs/plans/PLAN-176-codex-multi-model-ab-framework.md |
| ② 実装コード | cli/lib/codex_ab_runner.py / cli/helix-codex (--ab-test 追加) |
| ③ テスト設計 | 本文 §Sprint .1 T1-T7 + §mandatory in sprint |
| ④ テストコード | cli/lib/tests/test_codex_ab_runner.py + bats smoke |

## carry / リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| A/B テストのコスト倍増 | budget 圧迫 | budget guard + --max-cost デフォルト 0.50 USD |
| 統計的有意性不足 (3 試行) | 結論が信頼できない | P2 carry として Sprint .3 は raw data 収集のみ |
| helix.db v36 と既存 v35 衝突 | migration 失敗 | idempotent migration + T6 で事前検証 |
| `--ab-test` と既存 `--task` の option 競合 | CLI 破壊 | bats 回帰テストで既存挙動保護 |

## 関連 reference

- cli/ROLE_MAP.md (model 割当の正本)
- cli/lib/helix_db.py (DB access パターン参考実装)
- PLAN-092 (helix.db schema v35、migration 体系の正本)
- PLAN-099 (自動走行 framework、task_queue 連携候補)
- helix/HELIX_CORE.md §モデル割当

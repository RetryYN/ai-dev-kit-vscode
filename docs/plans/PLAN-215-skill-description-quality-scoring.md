---
plan_id: PLAN-215
title: "PLAN-215: skill description quality scoring (LLM-as-judge で品質評価)"
kind: impl
layer: L4
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: S
created: "2026-05-23"
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — helix skill quality-score サブコマンド実装 + helix doctor 統合"
  - role: qa
    slot_label: "QA — quality score 算出ロジックのテスト + helix doctor WARN 閾値確認"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-194 description 最適化との整合確認 + score 基準が推挙精度に与える影響チェック"
generates:
  - artifact_path: docs/plans/PLAN-215-skill-description-quality-scoring.md
    artifact_type: design_doc
  - artifact_path: cli/helix-skill
    artifact_type: cli_extension
  - artifact_path: cli/lib/skill_quality_scorer.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_skill_quality_scorer.py
    artifact_type: test
dependencies:
  parent: null
  requires:
    - PLAN-194
  blocks: []
related_adr: []
related_plans:
  - PLAN-194
  - PLAN-022
  - PLAN-121
related_feedback:
  - feedback_codex_docs_enum_inline_prompt
---

# PLAN-215: skill description quality scoring (LLM-as-judge で品質評価)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 SKILL.md description の品質評価 framework 追加** であり、
新規 framework 採用 / fail-close 化 / 外部仕様採用の大局判断を含まない。
ADR snapshot は不要。

根拠:
- LLM judge 呼び出し経路は PLAN-194 `cli/lib/skill_description_optimizer.py` の
  gpt-5.4-mini 既存呼び出しを踏襲する
- `helix skill` サブコマンド追加は既存 `cli/helix-skill` Bash dispatcher の拡張
- `helix doctor` 統合は既存 warn 追加のみで、fail-close 化は本 PLAN スコープ外
- score 算出基準 (具体性 / 明示性 / triggers 整合の 3 軸) は SKILL_MAP.md
  §メンテナンス指針の既存ルールを評価軸に変換したもの

---

## §1. 背景・目的

### 1.1 問題

PLAN-194 (description LLM 自動生成) は description を 80-120 文字に最適化するが、
**品質の絶対値評価** は行わない。以下の問題が未解決:

- 既存 description が曖昧であっても score 0 件で検出不能
- description を改善したとき「どのくらい改善したか」の定量根拠がない
- helix doctor は description 長さ超過を検出しないため、god-writing 型の長文が蓄積する

### 1.2 解決ゴール

1. `helix skill quality-score --all` で全 111 skill の description を
   gpt-5.4 で品質スコア化 (1-10) し、スコアと改善提案を JSON / テキストで出力する
2. スコア < 6 の skill を `helix doctor` WARN として報告し、定期的な品質維持を促す
3. PLAN-194 との連携: 低スコア skill を `quality-score` で特定 →
   `description optimize` で改善 → 再スコア化で改善効果を定量確認する

### 1.3 評価 3 軸

| 軸 | 説明 | 高スコア例 |
|---|---|---|
| 具体性 | 「〇〇関連」禁止、動詞 + 対象物 + 用途 で記述 | 「Playwright 記録から E2E テストを生成し a11y 検証を統合」 |
| 明示性 | 「〇〇系」「〇〇周辺」のような曖昧語を使わない | triggers / task context と対応する具体語を含む |
| triggers 整合 | SKILL.md の triggers と description が矛盾しない | description に記載のない概念が triggers に大量出現しない |

---

## §2. WebSearch 履歴 (PLAN-087 ガード遵守)

外部ライブラリへの新規依存なし。WebSearch **skip**。LLM judge 経路は PLAN-194
gpt-5.4-mini 踏襲 (モデルは gpt-5.4 格上げ)、score 基準は SKILL_MAP.md §メンテ方針から直接導出。

---

## §3. 設計方針

### 3.1 サブコマンド設計

```bash
# 全 skill の quality score を一括評価
helix skill quality-score --all

# 特定 skill のみ評価
helix skill quality-score --skill common/testing

# JSON 出力 (CI / helix doctor 連携)
helix skill quality-score --all --json

# スコア閾値でフィルタ (低スコアのみ表示)
helix skill quality-score --all --below 6
```

### 3.2 スコア算出パイプライン

```
SKILL.md (description + triggers + 本文冒頭 300 文字)
    ↓
gpt-5.4 LLM-as-judge プロンプト (3 軸評価)
    ↓
score 1-10 (per axis) + overall score + 改善 suggestion
    ↓
JSON / テキスト出力
    ↓
helix doctor 統合 (overall < 6 → WARN 追加)
```

### 3.3 gpt-5.4 プロンプト設計

3 軸 (具体性 / 明示性 / triggers 整合) を 1-10 で評価し、以下の JSON を返す。

```json
{
  "skill_id": "<id>",
  "scores": {"specificity": N, "clarity": N, "triggers_alignment": N},
  "overall": N,
  "suggestion": "改善提案 (1-2 文)"
}
```

入力: skill_id / description / triggers / content_head (300 文字)。

### 3.4 helix doctor 統合

`cli/helix-doctor` に `check_skill_description_quality` を追加。
overall < 6 の skill を WARN として報告する (fail-close 化は本 PLAN スコープ外)。

```
WARN [skill:common/testing] description quality score 4/10
```

### 3.5 PLAN-194 連携フロー

低スコア特定 (`quality-score --all --below 6`) → 改善 (`description optimize`) →
catalog rebuild → 再スコア化の 4 ステップで改善効果を定量確認する。

---

## §4. 実装 Sprint

### Sprint .1: skill_quality_scorer.py 実装 (Codex se 委譲)

Entry 条件: PLAN-194 `cli/lib/skill_description_optimizer.py` 動作確認済。

実装: `score_description` (gpt-5.4 呼び出し) / `parse_score_response` (overall 1-10 検証) /
`format_score_report` (テキスト / JSON 整形)。`python3 -m py_compile` PASS で完了。

### Sprint .2: helix skill quality-score サブコマンド + helix doctor 統合 (Codex se 委譲)

Entry 条件: Sprint .1 完了。

`cli/helix-skill` に `quality-score` (--all / --skill / --json / --below) を追加。
`cli/helix-doctor` に `check_skill_description_quality` を追加し overall < 6 を WARN 報告。
`bash -n` 両ファイル PASS で完了。

### Sprint .3: テスト実装 (Codex qa 委譲)

Entry 条件: Sprint .2 完了。

`test_skill_quality_scorer.py` に mock gpt-5.4 レスポンス / 範囲外 score 拒否 /
--below フィルタ / helix doctor WARN の 4 ケースを作成。`pytest` 全 PASS で完了。

---

## §5. DoD (完了条件)

- [ ] `cli/lib/skill_quality_scorer.py` が `python3 -m py_compile` PASS
- [ ] `helix skill quality-score --skill <id> --json` が score JSON を出力する
- [ ] `helix skill quality-score --all --below 6` が低スコア skill のみ表示する
- [ ] `helix doctor` で overall < 6 の skill が WARN に出現する
- [ ] `test_skill_quality_scorer.py` 全 PASS
- [ ] `bash -n cli/helix-skill` + `bash -n cli/helix-doctor` PASS
- [ ] PLAN-194 連携フロー (低スコア特定 → optimize → 再スコア) が動作する
- [ ] helix doctor warn 数が低スコア skill 以外で増加しない

---

## §6. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-215-*.md |
| ② 実装コード | Sprint .1〜.2 で生成 | cli/lib/skill_quality_scorer.py / cli/helix-skill / cli/helix-doctor |
| ③ テスト設計 | Sprint .3 (QA) が担当 | docs/v2/L4-test-design/PLAN-215-test-design.md (Sprint .3 起票) |
| ④ テストコード | Sprint .3 実装 | cli/lib/tests/test_skill_quality_scorer.py |

**双方向 reference**:
- 本 PLAN (①) → 実装 (②): generates.artifact_path に列挙
- 実装 (②) → 本 PLAN (①): cli/lib/skill_quality_scorer.py 先頭 comment に `# PLAN-215` 明記
- 本 PLAN (①) → テスト設計 (③): Sprint .3 起票時に §6 に追記

---

## §7. リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| gpt-5.4 LLM judge が score 基準を安定再現しない | 同一 description で score がブレる | Sprint .1 で temperature=0 + seed 固定でブレを最小化 |
| 111 skill 一括 scoring で gpt-5.4 コスト増加 | budget 圧迫 | `--all` 実行前に推定 token 数を表示し確認を求める (--yes 未指定時) |
| helix doctor WARN 数が急増し既存 WARN が埋もれる | 重要 WARN が見逃される | 初回実行時のみ `--dry-run` で影響範囲確認を推奨する手順を doc 追加 |
| PLAN-194 未完了で連携フローが動作しない | Sprint .3 の連携確認ができない | Sprint .3 は PLAN-194 Sprint .2 (helix-skill description サブコマンド) 完了後に着手 |

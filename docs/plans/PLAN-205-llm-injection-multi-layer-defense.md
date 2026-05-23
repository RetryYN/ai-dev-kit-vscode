---
plan_id: PLAN-205
title: "PLAN-205: prompt injection 多層防御 (OWASP LLM01 全委譲経路対応)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
size: M
created: 2026-05-23
revised: 2026-05-23
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: tl-advisor
    slot_label: "TL — 全委譲経路 (helix-codex/helix-claude/skill chain) の sanitization 統合方針 adversarial check"
  - role: se
    slot_label: "SE — llm_guard.py 実装・helix-codex / helix-claude への sanitizer 統合・pydantic schema validation"
  - role: security
    slot_label: "Security — OWASP LLM01 injection pattern 網羅・LLM-as-judge 判定スキーマ設計"
  - role: qa
    slot_label: "QA — 全経路 injection シナリオ設計・output schema validation regression test"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-184 との重複境界確認・scope 整合・DoD チェック"
generates:
  - artifact_path: cli/lib/llm_guard.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_llm_guard.py
    artifact_type: test
  - artifact_path: cli/lib/output_validator.py
    artifact_type: python_module
  - artifact_path: docs/v2/L3-llm-injection-defense-design.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-184
    - PLAN-153
  blocks: []
related_plans:
  - PLAN-184
  - PLAN-153
  - PLAN-022
related_adr:
  - ADR-057 候補 (全 LLM 委譲経路 injection 防御方針 L2 snapshot、本 PLAN 起票後に起票)
related_docs:
  - cli/lib/skill_sanitizer.py
  - cli/lib/skill_recommender.py
  - cli/helix-codex
  - cli/helix-claude
acceptance_criteria:
  - "helix-codex / helix-claude / helix skill chain の全 3 経路で input sanitization が適用される"
  - "output pydantic schema validation が JSON 応答の型不正・unexpected field を reject する"
  - "LLM-as-judge が injection_score >= 0.8 の入力を block し WARN を出力する"
  - "injection シナリオ 15 case (経路別 5 case × 3) が全件 sanitize / reject される"
  - "正常入力の推奨精度が PLAN-184 baseline と比較して 5% 以上低下しない"
  - "python3 -m py_compile cli/lib/llm_guard.py PASS"
  - "pytest cli/lib/tests/test_llm_guard.py 全 PASS"
  - "sandbox 環境 (LLM-as-judge 呼び出し不可) でも Layer 1 / Layer 2 が機能する"
---

# PLAN-205: prompt injection 多層防御 (OWASP LLM01 全委譲経路対応)

## L2 凍結 (ADR snapshot)

本 PLAN tree は全 LLM 委譲経路への injection 防御拡張を含む。
PLAN-184 が skill recommender 単体に適用した三層防御を helix-codex / helix-claude にも横断適用するアーキテクチャ変更と、LLM-as-judge の採用は L2 大局判断に該当するため、ADR snapshot を併設する。

| ADR | 凍結対象 | Status |
|---|---|---|
| ADR-057 (起票予定) | 全 LLM 委譲経路 injection 防御方針 (llm_guard 共通層 + LLM-as-judge 統合) | Proposed |

双方向 trace:
- 本 PLAN → ADR-057: frontmatter `related_adr` + 本 section
- ADR-057 → 本 PLAN: `## Related` に「PLAN-205 (実装 PLAN、本 ADR が L2 凍結する)」を記載

> ADR-057 は本 PLAN の L4 着手前 (G3 通過後) に起票する。WebSearch 3 query 必須 (OWASP LLM Top 10 2025 全経路対策 / LLM-as-judge injection detection / pydantic LLM output validation)。

---

## 0. 背景

PLAN-184 は `helix skill chain` における prompt injection 防御 (sanitizer + boundary + output validation) を実装した。
しかし injection リスクは skill recommender 単体にとどまらない:

- `helix-codex`: ユーザータスク文字列を Codex CLI に渡す際に injection が混入しうる
- `helix-claude`: `--task` 引数がプロンプトに直接展開される
- `helix skill chain`: PLAN-184 で対応済 (本 PLAN は拡張のみ)

本 PLAN は共通 guard 層 (`cli/lib/llm_guard.py`) を新設し、全 3 経路に横断適用する。
また LLM-as-judge を第 4 層として追加し、高度な injection (indirect / multi-turn) を検出する。

## 1. 業界 standard 参照

| 参照 | source | 役割 |
|---|---|---|
| OWASP LLM Top 10 2025 (LLM01) | owasp.org/www-project-top-10-for-large-language-model-applications | 全委譲経路の Prompt Injection 対策パターン |
| NIST AI 100-1 §3.2 Adversarial ML | nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf | indirect injection の脅威モデル |
| LLM-as-Judge (Zheng et al. 2023) | arxiv.org/abs/2306.05685 | LLM による injection 判定の精度・コスト評価 |
| Pydantic v2 model validation | docs.pydantic.dev/latest/concepts/models | output schema strict validation の実装根拠 |

## 2. 攻撃経路分析 (PLAN-184 との境界)

| 経路 | PLAN-184 対応 | 本 PLAN の追加範囲 |
|---|---|---|
| helix skill chain (input/output) | sanitize + output validate 適用済 | LLM-as-judge 第 4 層追加 / pydantic strict 強化 |
| helix-codex (--task) | 未対応 | llm_guard.sanitize 適用 |
| helix-claude (--task) | 未対応 | llm_guard.sanitize 適用 |
| indirect injection (file 経由) | 未対応 | LLM-as-judge で検出 |

## 3. 設計方針

### 3.1 四層防御構成

```
[Layer 1] Input Sanitizer (PLAN-184 の skill_sanitizer を共通化)
     ↓ cli/lib/llm_guard.py で re-export
[Layer 2] Structured Prompt boundary (経路別 boundary marker)
     ↓
[Layer 3] Output Schema Validation (pydantic v2 strict model)
     ↓
[Layer 4] LLM-as-Judge (injection_score >= 0.8 で block)
```

Layer 1-3 は sandbox でも動作する。Layer 4 は LLM 呼び出しが必要なため fail-open (WARN のみ) とする。

### 3.2 `cli/lib/llm_guard.py` (共通 guard 層)

`guard_task_input(task, context)` が PLAN-184 の `sanitize_task_input` を re-export する (重複実装なし)。
`validate_llm_output(raw, schema_cls)` が pydantic `schema_cls.model_validate(raw)` で strict validation する。
context は `"codex"` / `"claude"` / `"skill_chain"` で経路ごとの将来拡張に備える。

### 3.3 経路別 integration point

| 経路 | integration 場所 | 変更内容 |
|---|---|---|
| helix-codex | cli/helix-codex (bash) → Python helper | `--task` を llm_guard.guard_task_input に通す |
| helix-claude | cli/helix-claude (bash) → Python helper | `--task` を llm_guard.guard_task_input に通す |
| helix skill chain | cli/lib/skill_recommender.py | 既存 sanitize_task_input を llm_guard 経由に変更 |

### 3.4 Layer 4: LLM-as-Judge

`llm_guard.judge_injection(task, threshold=0.8)` が gpt-5.4-mini で injection_score を 0.0〜1.0 で返す。
閾値 0.8 以上で block、呼び出し失敗時は fail-open (WARN + pass)。

### 3.5 output_validator.py (pydantic schema)

`CodexTaskOutput` / `SkillRecommendation` を `model_config = {"extra": "forbid"}` で strict 定義し、
unexpected field を含む LLM 出力を全 reject する。

## 4. テスト設計

### 4.1 injection シナリオ 15 case (経路別 5 case × 3)

| case | 経路 | カテゴリ | 期待結果 |
|---|---|---|---|
| T01-T03 | codex | "Ignore previous" / 制御文字 / "system: override" | Layer 1 除去 |
| T04 | codex | indirect injection_score=0.9 | Layer 4 block |
| T05 | codex | 正常タスク | pass |
| T06-T08 | claude | extraction / role override / delimiter | Layer 1 除去 |
| T09 | claude | indirect injection_score=0.85 | Layer 4 block |
| T10 | claude | 正常タスク | pass |
| T11-T12 | skill chain | catalog 外 ID / pydantic schema 外 field | Layer 3 reject |
| T13-T14 | skill chain | injection_score=0.95 / judge 呼び出し失敗 | block / fail-open |
| T15 | skill chain | 正常推奨 | pass |

### 4.2 精度 regression test

PLAN-184 で確立した 10 件の正常シナリオに対して推奨精度を測定し、baseline と比較する。

## 5. L4 実装 Sprint 計画

| Sprint | 実装内容 | Exit 条件 |
|---|---|---|
| .1 | `llm_guard.py` + helix-codex / helix-claude へ guard_task_input 挿入 | py_compile PASS / T01-T10 Layer 1 sanitize 確認 |
| .2 | `output_validator.py` pydantic strict model + skill_recommender.py integration | T11-T12 schema violation reject 確認 |
| .3 | `judge_injection()` LLM-as-judge (gpt-5.4-mini) + fail-open 実装 | T13-T14 Layer 4 期待動作確認 |
| .4 | `test_llm_guard.py` 15 case + 精度 regression (QA) | pytest 全 PASS / baseline 差 5% 以内 |
| .5 | Security review + `L3-llm-injection-defense-design.md` 起草 + ADR-057 起票 | DoD 全件 PASS |

## 6. リスクと緩和策

| リスク | 影響 | 緩和 |
|---|---|---|
| LLM-as-judge コスト増 | 委譲コスト上昇 | gpt-5.4-mini + injection_score 閾値 0.8 でコスト最小化 |
| Layer 1 過剰除去で helix-codex タスクが歪む | 実装品質低下 | regression test (Sprint .4) で 5% 閾値を設定 |
| pydantic strict mode で既存 output が reject | 委譲失敗多発 | Sprint .2 で既存 output をサンプリングしてスキーマを validate してから凍結 |
| PLAN-184 との scope 重複 | 実装競合 | Layer 1 は PLAN-184 の skill_sanitizer を re-export する (重複実装しない) |

## 7. DoD (Definition of Done)

- acceptance_criteria 全件 PASS
- injection シナリオ 15 case が pytest で全 PASS
- PLAN-184 精度 baseline との差が 5% 以内
- ADR-057 起票済 (L2 凍結)
- `docs/v2/L3-llm-injection-defense-design.md` 起草済 (V-model 設計 artifact)
- helix doctor warn 増加なし

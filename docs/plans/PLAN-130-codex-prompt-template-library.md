---
plan_id: PLAN-130
title: "Codex 委譲 prompt template library (各 role 標準 prompt 体系化)"
kind: impl
layer: L4
drive: be
status: draft
size: M
created: "2026-05-23"
owner: PM
phases: L3, L4
gates: G3, G4
agent_slots:
  - role: docs
    slot_label: "docs — 11 役 standard.md template 起草 + feedback memory 知見の反映"
  - role: se
    slot_label: "SE — helix codex --template flag 実装 + CLI integration"
  - role: pmo-sonnet
    slot_label: "PMO — feedback memory との整合確認・既存 prompt との drift チェック"
  - role: qa
    slot_label: "QA — 各 role 実 task 3 件試行 + SUMMARY 集約問題改善実証"
generates:
  - artifact_path: docs/plans/PLAN-130-codex-prompt-template-library.md
    artifact_type: design_doc
  - artifact_path: cli/templates/codex-prompts/se/standard.md
    artifact_type: template
  - artifact_path: cli/templates/codex-prompts/pg/standard.md
    artifact_type: template
  - artifact_path: cli/templates/codex-prompts/qa/standard.md
    artifact_type: template
  - artifact_path: cli/templates/codex-prompts/dba/standard.md
    artifact_type: template
  - artifact_path: cli/templates/codex-prompts/docs/standard.md
    artifact_type: template
  - artifact_path: cli/templates/codex-prompts/research/standard.md
    artifact_type: template
  - artifact_path: cli/templates/codex-prompts/security/standard.md
    artifact_type: template
  - artifact_path: cli/templates/codex-prompts/fe/standard.md
    artifact_type: template
  - artifact_path: cli/templates/codex-prompts/devops/standard.md
    artifact_type: template
  - artifact_path: cli/templates/codex-prompts/perf/standard.md
    artifact_type: template
  - artifact_path: cli/templates/codex-prompts/legacy/standard.md
    artifact_type: template
  - artifact_path: cli/lib/tests/test_codex_prompt_template.py
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr: []
related_plans:
  - PLAN-091 (V5 framework 本体 — kind / drive / agent_slots enum 正本)
  - PLAN-099 (自動走行 framework — task_queue からの prompt 参照経路)
related_feedback:
  - feedback_codex_report_section_loss
  - feedback_codex_docs_enum_inline_prompt
---

# PLAN-130: Codex 委譲 prompt template library

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 Codex 委譲経路 (helix codex --role X) の内部整理** であり、
新規 framework 採用 / fail-close 化 / 外部仕様採用の大局判断を含まない。
ADR snapshot は不要。

根拠:
- `helix codex --role X` の CLI 経路は ADR-015/PLAN-028 で凍結済
- template 追加は既存 `cli/templates/` ディレクトリへの拡張で新方針なし
- `--template` flag は既存 `--task` との組み合わせオプションであり破壊的変更なし

## 背景

Codex 委譲 (`helix codex --role X`) を多用する中で、以下の問題が蓄積している:

### 問題 1: feedback_codex_report_section_loss

Codex se (gpt-5.4) が task 完了時に **SUMMARY 形式に全セクションを圧縮** し、
「改善案」「詳細プロファイル数値」「carry candidates」等の重要セクションが欠落する事例が
本 session (2026-05-23 Wave 3) で確認された。

根本原因:
- 委譲 prompt に「全セクションを出力せよ」という明示指示が不在
- Codex はデフォルトで簡潔さを優先するため、詳細情報を SUMMARY に要約してしまう

### 問題 2: feedback_codex_docs_enum_inline_prompt

Codex docs (gpt-5.3-codex-spark) で template / placeholder doc 起草を委譲するとき、
**enum 正本を prompt 内に inline で再掲しないと placeholder で enum 違反値が生成される**。

2026-05-20 の PLAN-091 Sprint .2 で 11 template 全件違反が検出された。

### 問題 3: prompt 散在

各 role の prompt best practice が以下に散在している:
- `~/.claude/CLAUDE.md` (委譲ルール)
- `cli/templates/prompts/skill-search.md` (skill search 専用)
- feedback memory entries (暗黙知)
- 各 PLAN.md の「委譲先」セクション

役割別に **標準 prompt + 改善知見を 1 ファイルにまとめた template** が不在。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **HELIX 内部 prompt 整理** であり、外部ライブラリへの新規依存なし。
WebSearch **skip**。

skip 理由:
- prompt engineering の知見は feedback memory + PLAN 蓄積から抽出
- `cli/templates/` の既存パターン (skill-search.md) をベースに拡張
- enum 正本は PLAN-091 §5 + ROLE_MAP.md が正本で外部参照不要

## 設計方針

### template 構造

```
cli/templates/codex-prompts/
  <role>/
    standard.md       # 標準 prompt template
```

各 `standard.md` の構造:

```markdown
# <role> standard prompt

## role meta
role: <role>
model: <model>
thinking: <level>

## task injection point
{TASK}

## output requirements
(role 別の出力要件 — SUMMARY 集約問題への対策を含む)

## enum reference (docs role のみ)
(enum 一覧の inline 再掲 — feedback_codex_docs_enum_inline_prompt 対策)

## known issues
(feedback memory から抽出した注意事項)
```

### 対象 11 役と主な改善知見

| role | model | 主な改善ポイント |
|---|---|---|
| se | gpt-5.4 | SUMMARY 集約禁止・セクション別出力指示・carry candidates 必須出力 |
| pg | gpt-5.3-codex-spark | 軽量タスク向け・テスト必須指示・bash -n / py_compile 必須 |
| qa | gpt-5.4 | テスト scenario 明示・fixture 動的 timestamp 指示・4 scenario template |
| dba | gpt-5.3-codex | idempotent migration 必須・rollback テスト指示 |
| docs | gpt-5.3-codex-spark | enum inline 再掲必須・placeholder 禁止指示・spot check 手順 |
| research | gpt-5.4 | 一次ソース優先・出典付き出力・WebSearch query 3 件以上 |
| security | gpt-5.4 | OWASP 参照・severity 分類・修正提案セット出力 |
| fe | gpt-5.4 | mock 駆動設計準拠・state-events.md 更新指示 |
| devops | gpt-5.3-codex | idempotent script 必須・dry-run option 指示 |
| perf | gpt-5.4 | ベースライン比較必須・数値出力 (ms / MB) 指示 |
| legacy | gpt-5.4 | 変更範囲最小化・既存 test 保護・characterization test 追加指示 |

### helix codex --template flag

```bash
helix codex --role se --task "..." --template standard
helix codex --role docs --task "..." --template standard
```

- `--template <usage>` で `cli/templates/codex-prompts/<role>/<usage>.md` を読み込む
- `{TASK}` を `--task` 引数で置換して最終 prompt を構築
- 省略時は既存挙動 (template なし) を維持 (破壊的変更なし)

## 実装計画

### Sprint .1: template 設計・起草 (Codex docs 委譲、size M)

**Entry 条件**: feedback memory entries 精読完了

実施内容:

1. `cli/templates/codex-prompts/<role>/standard.md` × 11 ファイル 新規作成
   - feedback_codex_report_section_loss 対策: se / pg / qa に「全セクション出力必須」明示
   - feedback_codex_docs_enum_inline_prompt 対策: docs に enum 完全リスト inline 再掲
   - 各 role の thinking level / model を冒頭に明記
2. pmo-sonnet で既存 prompt / feedback memory との drift チェック

受入条件:
- 11 ファイルが `cli/templates/codex-prompts/<role>/standard.md` に存在
- docs/standard.md に VALID_KINDS / VALID_LAYERS / VALID_DRIVES / VALID_ARTIFACT_TYPES の
  完全 enum が inline 再掲されている
- se/standard.md に「SUMMARY 集約禁止・全セクション出力」の明示指示がある

### Sprint .2: --template flag 実装 (Codex se 委譲、size S)

**Entry 条件**: Sprint .1 template 全 11 ファイル PASS

実施内容:

1. `cli/helix-codex` に `--template <usage>` オプション追加
2. template ファイル読み込み + `{TASK}` 置換ロジック実装
3. `bash -n cli/helix-codex` PASS (mandatory in sprint)
4. 既存テスト (`helix test --bats-only`) に影響なし確認

受入条件:
- `helix codex --role se --task "テスト" --template standard` が動作する
- `--template` 省略時に既存挙動が維持される
- bats 回帰テスト PASS

### Sprint .3: 実 task 試行 + 改善実証 (Codex qa 委譲、size S)

**Entry 条件**: Sprint .2 --template flag 動作確認済

実施内容:

1. 各 role で実 task 3 件試行 (合計 33 件、role × 3)
2. se/standard.md 適用後に SUMMARY 集約問題が改善されているか確認
   (feedback_codex_report_section_loss 改善実証)
3. docs/standard.md 適用後に enum 違反 placeholder がゼロか確認
   (feedback_codex_docs_enum_inline_prompt 改善実証)
4. `cli/lib/tests/test_codex_prompt_template.py` 新規作成
   - template ファイル存在チェック (11 ファイル)
   - `{TASK}` 置換動作確認
   - docs/standard.md の enum 完全性チェック

受入条件:
- se: SUMMARY 集約なし・全セクション出力確認 (3/3 task)
- docs: enum 違反 placeholder ゼロ (3/3 task)
- `test_codex_prompt_template.py` 全 PASS

## DoD (Definition of Done)

- [ ] 11 役 `standard.md` 全ファイル存在
- [ ] docs/standard.md に VALID_* enum inline 再掲
- [ ] se/standard.md に SUMMARY 集約禁止指示
- [ ] `helix codex --template standard` 動作確認
- [ ] bats 回帰テスト PASS (既存挙動影響なし)
- [ ] `test_codex_prompt_template.py` 全 PASS
- [ ] SUMMARY 集約問題改善実証 (se 3 task)

## risks

| リスク | 影響 | 緩和策 |
|---|---|---|
| template が長大になり prompt token 超過 | Codex がエラー | 各 standard.md を 100 行以内に制限 |
| `--template` flag が既存 `--task` と競合 | 既存委譲が壊れる | 省略時は既存挙動維持、bats 回帰で確認 |
| docs role の enum が validator 更新で乖離 | 違反 placeholder 再発 | docs/standard.md に「validator から自動抽出」コメント追記 |
| Sprint .3 の 33 件試行がコスト大 | budget 圧迫 | 各 role 1 件の smoke test を先行、3 件は P2 carry も可 |

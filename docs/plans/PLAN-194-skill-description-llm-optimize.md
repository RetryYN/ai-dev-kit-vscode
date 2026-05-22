---
plan_id: PLAN-194
title: "skill description LLM 自動生成 (冗長 description を機械最適化)"
kind: impl
layer: L4
drive: be
status: draft
size: S
created: "2026-05-23"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: se
    slot_label: "SE — helix skill description optimize サブコマンド実装 + SKILL.md 書き戻しロジック"
  - role: qa
    slot_label: "QA — description 長さ制約・diff 確認フロー・承認ゲートの bats + pytest"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-121 recommender との整合確認・description 変更が推挙精度に与える影響チェック"
generates:
  - artifact_path: docs/plans/PLAN-194-skill-description-llm-optimize.md
    artifact_type: design_doc
  - artifact_path: cli/helix-skill
    artifact_type: cli_extension
  - artifact_path: cli/lib/skill_description_optimizer.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_skill_description_optimizer.py
    artifact_type: test
dependencies:
  parent: null
  requires:
    - PLAN-022
  blocks: []
related_adr: []
related_plans:
  - PLAN-121 (skill recommender improvement — description 最適化の推挙精度改善効果を計測)
  - PLAN-022 (skill recommender 基盤 — catalog と SKILL.md description の使われ方)
  - PLAN-091 (V5 framework — helix.db skill_usage テーブル参照)
related_feedback:
  - feedback_codex_docs_enum_inline_prompt
---

# PLAN-194: skill description LLM 自動生成 (冗長 description を機械最適化)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 SKILL.md description の品質改善** であり、
新規 framework 採用 / fail-close 化 / 外部仕様採用の大局判断を含まない。
ADR snapshot は不要。

根拠:
- skill catalog 基盤は PLAN-022 で確立済み (`cli/lib/skill_catalog.py`)
- LLM 呼び出し経路は `cli/lib/skill_recommender.py` の gpt-5.4-mini 既存利用を踏襲
- `helix skill` サブコマンド追加は既存 `cli/helix-skill` Bash dispatcher の拡張
- SKILL.md への書き戻しは frontmatter `description:` フィールドの上書きのみ

## §1 背景・目的

### 1.1 問題

SKILL_MAP.md §メンテナンス指針では description について:
> description は具体的用途を記載 (「〇〇関連」禁止)

しかし実態として、一部の SKILL.md description は:
- 200 文字超の長文 (god-writing 系で顕在化、2026-05-23 本 session で確認)
- skill catalog の推挙プロンプト (`cli/templates/prompts/skill-search.md`) は
  description を LLM context に含めるため、長文は token を圧迫しマッチング精度を低下させる

最適な description 長は **80-120 文字** (skill-search.md のプロンプト設計根拠)。

### 1.2 解決ゴール

1. `helix skill description optimize --all` で全 107 skill の description を
   gpt-5.4-mini で一括生成し、80-120 文字の最適版を提案する
2. diff 確認 + 手動承認後に SKILL.md の `description:` フィールドを書き戻す
3. 最適化後の推挙精度改善を PLAN-121 test set (30 タスク) で定量確認する

## §2 WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **HELIX 内部 CLI ツールの実装** であり、外部ライブラリへの新規依存なし。
WebSearch **skip**。

skip 理由:
- LLM による description 生成は PLAN-022 の gpt-5.4-mini 既存呼び出しを踏襲
- SKILL.md frontmatter 操作は PyYAML (`yaml.safe_load` / `yaml.dump`) を既存利用
- description 品質基準 (80-120 文字) は SKILL_MAP.md §メンテナンス指針から直接導出

## §3 設計方針

### 3.1 サブコマンド設計

```bash
# 全 skill の description を一括最適化 (diff 確認モード)
helix skill description optimize --all

# 特定 skill のみ最適化
helix skill description optimize --skill common/testing

# dry-run (diff のみ表示、SKILL.md 書き戻しなし)
helix skill description optimize --all --dry-run

# 承認フラグ付きで直接書き戻し (CI / 自動化向け)
helix skill description optimize --all --yes
```

### 3.2 最適化パイプライン

```
SKILL.md (description + 本文冒頭 500 文字)
    ↓
gpt-5.4-mini プロンプト
    ↓
最適 description 候補 (80-120 文字)
    ↓
diff 表示 (旧 description vs 新 description)
    ↓
ユーザー承認 (y/n/skip)
    ↓
SKILL.md の description フィールド書き戻し
```

### 3.3 gpt-5.4-mini プロンプト設計

```
以下の HELIX skill について、skill recommender の推挙精度を最大化する
description を 80〜120 文字で生成してください。

制約:
- 「〇〇関連」「〇〇系」等の曖昧表現は禁止
- 具体的な動詞 + 対象物 + 用途 で記述
- 日本語で記述
- 現行 description の核心語句を保持する

skill_id: {skill_id}
現行 description: {current_description}
SKILL.md 本文冒頭:
{skill_content_head}
```

### 3.4 SKILL.md 書き戻し

対象フィールド: frontmatter の `description:` のみ。
本文・他 frontmatter フィールドは変更しない。

書き戻し実装 (`cli/lib/skill_description_optimizer.py`):

```python
def rewrite_description(skill_path: Path, new_description: str) -> None:
    """SKILL.md の description フィールドのみ安全に書き戻す"""
    text = skill_path.read_text(encoding="utf-8")
    # frontmatter の description: 行のみ置換 (正規表現)
    updated = re.sub(
        r'^(description:\s*).*$',
        f'description: "{new_description}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    skill_path.write_text(updated, encoding="utf-8")
```

### 3.5 catalog 自動再構築

SKILL.md 書き戻し後に `helix skill catalog rebuild` を自動実行し、
推奨キャッシュを invalidate する (PLAN-121 Sprint .2 の二段 cache と連携)。

## §4 実装 Sprint

### Sprint .1: skill_description_optimizer.py 実装 (Codex se 委譲)

**Entry 条件**: PLAN-022 `cli/lib/skill_catalog.py` 動作確認済

実施内容:
1. `cli/lib/skill_description_optimizer.py` 新規作成
   - `optimize_description(skill_id, skill_path)` — gpt-5.4-mini 呼び出し
   - `rewrite_description(skill_path, new_description)` — frontmatter 書き戻し
   - `diff_display(old, new)` — unified diff 形式で表示
2. `python3 -m py_compile cli/lib/skill_description_optimizer.py` PASS

受入条件:
- `optimize_description` が 80-120 文字の description を返す
- `rewrite_description` が description フィールドのみ書き換え、本文を保護する
- `python3 -m py_compile` PASS

### Sprint .2: helix skill description サブコマンド追加 (Codex se 委譲)

**Entry 条件**: Sprint .1 完了

実施内容:
1. `cli/helix-skill` に `description` サブコマンド追加
   - `optimize --all / --skill <id> / --dry-run / --yes` オプション対応
2. インタラクティブ承認フロー実装 (y/n/skip + --yes bypass)
3. 承認後に `helix skill catalog rebuild` を自動呼び出し
4. `bash -n cli/helix-skill` PASS

受入条件:
- `helix skill description optimize --all --dry-run` が diff を表示して終了する
- `helix skill description optimize --skill common/testing --yes` が
  SKILL.md の description を書き戻し、catalog rebuild を実行する
- `bash -n cli/helix-skill` PASS

### Sprint .3: テスト + 推挙精度検証 (Codex qa 委譲)

**Entry 条件**: Sprint .2 完了 + PLAN-121 Sprint .3 test set 30 タスク準備済

実施内容:
1. `cli/lib/tests/test_skill_description_optimizer.py` 新規作成
   - `rewrite_description` 単体テスト (description のみ変更、本文保護)
   - 80-120 文字制約テスト (mock gpt-5.4-mini)
   - `--dry-run` フラグで SKILL.md が変更されないことの確認
2. PLAN-121 test set (30 タスク) を使い、description 最適化前後の精度比較
   - 最適化対象: 200 文字超の description を持つ skill (想定 10-15 件)
   - 計測: top-3 precision で最適化前後を比較
3. `pytest cli/lib/tests/test_skill_description_optimizer.py` 全 PASS

受入条件:
- `test_skill_description_optimizer.py` 全 PASS
- `--dry-run` で SKILL.md が変更されていないことを確認
- description 最適化後の推挙精度が最適化前と同等以上 (precision 低下なし)
- `helix doctor warn` 増加なし

## §5 DoD (完了条件)

- [ ] `cli/lib/skill_description_optimizer.py` が `python3 -m py_compile` PASS
- [ ] `helix skill description optimize --all --dry-run` が全 107 skill の diff を表示する
- [ ] `helix skill description optimize --skill <id> --yes` が SKILL.md description を書き戻す
- [ ] description 書き戻し後に `helix skill catalog rebuild` が自動実行される
- [ ] `test_skill_description_optimizer.py` 全 PASS
- [ ] `bash -n cli/helix-skill` PASS
- [ ] PLAN-121 test set で description 最適化後の精度低下なし
- [ ] helix doctor warn 増加なし

## §6 risks

| リスク | 影響 | 緩和策 |
|---|---|---|
| gpt-5.4-mini が制約 (80-120 文字) を超える description を生成 | 長文 description が混入し推挙精度が悪化 | Sprint .1 で `len(result) < 120` の assertion + 超過時は再生成 (最大 2 回) |
| `rewrite_description` が description 以外の frontmatter を破壊 | SKILL.md が validate エラー | Sprint .3 で全 107 SKILL.md の `helix skill catalog rebuild` PASS を受入条件に追加 |
| PLAN-121 未完了で precision 計測の比較基準が未定 | Sprint .3 の精度検証ができない | Sprint .3 は PLAN-121 Sprint .3 (baseline 記録) 完了後に着手、未完了時は defer |
| 107 skill 一括処理で gpt-5.4-mini コスト増加 | budget 圧迫 | `--all` 実行前に推定 token 数を表示してユーザー確認を求める (--yes flag がない場合) |

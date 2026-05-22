---
plan_id: PLAN-193
title: "helix-codex prompt versioning (template version control)"
kind: refactor
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
    slot_label: "SE — helix-codex に --template-version flag 追加 + template 冒頭 version フィールド読み取り実装"
  - role: qa
    slot_label: "QA — version pinning / upgrade / unknown version 各シナリオの bats + pytest"
  - role: pmo-sonnet
    slot_label: "PMO — helix.db codex_invocations schema との整合確認・PLAN-130/PLAN-154 依存チェック"
generates:
  - artifact_path: docs/plans/PLAN-193-codex-prompt-versioning.md
    artifact_type: design_doc
  - artifact_path: cli/helix-codex
    artifact_type: cli_extension
  - artifact_path: cli/lib/tests/test_codex_prompt_versioning.py
    artifact_type: test
dependencies:
  parent: PLAN-130
  requires:
    - PLAN-130
  blocks: []
related_adr: []
related_plans:
  - PLAN-130 (Codex 委譲 prompt template library — template ファイル管理の親 PLAN)
  - PLAN-154 (codex_invocations — template_version 記録先 DB テーブル)
  - PLAN-091 (V5 framework — helix.db schema 正本)
related_feedback:
  - feedback_codex_report_section_loss
---

# PLAN-193: helix-codex prompt versioning (template version control)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **PLAN-130 で確立した template 体系への version 管理付加** であり、
新規 framework 採用 / fail-close 化 / 外部仕様採用の大局判断を含まない。
ADR snapshot は不要。

根拠:
- template 管理基盤は PLAN-130 で確立済み (`cli/templates/codex-prompts/<role>/standard.md`)
- version フィールドの追加は YAML front-matter の拡張のみで既存 parse を破壊しない
- `--template-version` flag は `--template` flag (PLAN-130) への追加オプション
- helix.db への記録は PLAN-154 `codex_invocations` テーブルへのカラム追加で完結

## §1 背景・目的

### 1.1 問題

PLAN-130 で整備した Codex 委譲 prompt template (`cli/templates/codex-prompts/<role>/standard.md`) は、
継続的に改善される設計である。しかし現状では:

1. **再現性がない**: 過去の Codex 委譲がどの template で実行されたか追跡できない
2. **比較実験ができない**: template 改善前後の出力品質を定量比較できない
3. **ロールバックができない**: template を更新しても旧版への切り戻し経路がない

### 1.2 解決ゴール

- `cli/templates/codex-prompts/<role>/standard.md` の冒頭に `version: <semver>` フィールドを追加
- `helix codex --template-version <ver>` で特定 version の template に固定して実行できる
- `helix.db` の `codex_invocations` テーブルに `template_version` を記録し、実行履歴から追跡可能にする

## §2 WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **HELIX 内部 CLI の拡張** であり、外部ライブラリへの新規依存なし。
WebSearch **skip**。

skip 理由:
- template version 管理は semver 標準 (`MAJOR.MINOR.PATCH`) をそのまま採用
- CLI flag 追加は既存 `cli/helix-codex` Bash 実装の拡張のみ
- helix.db カラム追加は SQLite `ALTER TABLE ADD COLUMN` で完結 (外部 ORM 不要)

## §3 設計方針

### 3.1 template version フィールド

各 `cli/templates/codex-prompts/<role>/standard.md` の冒頭に以下を追加:

```markdown
<!-- version: 1.0.0 -->
```

HTML コメント形式を採用する理由:
- Markdown の表示に影響しない
- Bash/Python 両方から `grep` で容易に抽出可能
- 既存 template parser (PLAN-130 Sprint .2) が非 YAML 冒頭を想定している

version 抽出 (Bash):

```bash
template_version=$(grep -m1 '<!-- version:' "$template_file" | sed 's/.*version: *//;s/ *-->//')
```

### 3.2 --template-version flag

```bash
helix codex --role se --task "..." --template standard --template-version 1.0.0
helix codex --role se --task "..." --template standard --template-version latest
```

動作仕様:
- `--template-version` を指定すると、`cli/templates/codex-prompts/<role>/versions/<ver>/standard.md`
  が存在する場合はそちらを優先使用する
- 存在しない場合は `cli/templates/codex-prompts/<role>/standard.md` の version と照合し、
  一致しなければ警告を出して最新版を使用する (fail-open)
- `--template-version latest` または省略時は常に `standard.md` を使用する (既存挙動と同一)

### 3.3 helix.db への記録

PLAN-154 で定義された `codex_invocations` テーブルに `template_version TEXT` カラムを追加:

```sql
ALTER TABLE codex_invocations ADD COLUMN template_version TEXT;
```

記録タイミング: `helix codex` 実行時に template 読み込み直後
記録値: 抽出した version 文字列 (例: `"1.0.0"`)、template 未使用時は `NULL`

### 3.4 バージョン管理フロー

```
cli/templates/codex-prompts/<role>/
  standard.md              # 最新版 (常にここが正本)
  versions/
    1.0.0/
      standard.md          # 旧版アーカイブ (手動コピー)
    1.1.0/
      standard.md
```

バージョンアップ手順:
1. `standard.md` を更新
2. 旧版を `versions/<old-ver>/standard.md` にコピー
3. `standard.md` の `<!-- version: ... -->` を新バージョンに更新

## §4 実装 Sprint

### Sprint .1: template に version フィールド追加 (Codex se 委譲)

**Entry 条件**: PLAN-130 Sprint .1 完了 (11 role standard.md 存在)

実施内容:
1. 11 役 `standard.md` の冒頭に `<!-- version: 1.0.0 -->` を追加
2. `cli/templates/codex-prompts/<role>/versions/` ディレクトリ構造の skeleton 作成
3. `bash -n cli/helix-codex` PASS (変更前後で syntax エラーなし)

受入条件:
- 11 ファイル全てに `<!-- version: 1.0.0 -->` が存在する
- `grep -r 'version:' cli/templates/codex-prompts/` で 11 件ヒット

### Sprint .2: --template-version flag 実装 (Codex se 委譲)

**Entry 条件**: Sprint .1 完了

実施内容:
1. `cli/helix-codex` に `--template-version <ver>` オプション追加
2. version 抽出ロジック実装 (grep + sed)
3. `versions/<ver>/standard.md` へのフォールバック探索実装
4. `bash -n cli/helix-codex` PASS

受入条件:
- `helix codex --role se --task "テスト" --template standard --template-version 1.0.0` が正常動作する
- `--template-version` 省略時に既存挙動が維持される (破壊的変更なし)
- `--template-version 9.9.9` (存在しない version) 指定時に警告を出して最新版で続行する

### Sprint .3: helix.db 記録 + テスト (Codex qa 委譲)

**Entry 条件**: Sprint .2 完了 + PLAN-154 `codex_invocations` テーブル確認

実施内容:
1. `codex_invocations` テーブルへの `template_version` カラム追加 migration
2. `cli/lib/tests/test_codex_prompt_versioning.py` 新規作成:
   - `<!-- version: ... -->` 抽出ロジックの単体テスト
   - `--template-version` flag の bats シナリオ (pinning / latest / unknown)
   - DB 記録値の確認テスト
3. `python3 -m py_compile cli/helix-codex` 相当確認 + `bash -n`

受入条件:
- `pytest cli/lib/tests/test_codex_prompt_versioning.py` 全 PASS
- `helix codex` 実行後に `codex_invocations.template_version` が記録されている
- bats シナリオ 3 種 (pinning / latest / unknown) 全 PASS

## §5 DoD (完了条件)

- [ ] 11 役 `standard.md` 全てに `<!-- version: 1.0.0 -->` フィールドが存在する
- [ ] `helix codex --template standard --template-version 1.0.0` が正常動作する
- [ ] `--template-version` 省略時に既存挙動が維持される (PLAN-130 Sprint .2 bats 回帰 PASS)
- [ ] `codex_invocations.template_version` カラムが追加され、実行時に記録される
- [ ] `test_codex_prompt_versioning.py` 全 PASS
- [ ] `bash -n cli/helix-codex` PASS
- [ ] helix doctor warn 増加なし

## §6 risks

| リスク | 影響 | 緩和策 |
|---|---|---|
| PLAN-154 未完了で codex_invocations テーブル不在 | Sprint .3 の DB 記録実装がブロックされる | Sprint .3 は PLAN-154 完了依存を明示、未完了時は NULL 記録で fail-open |
| versions/ ディレクトリ肥大化 | repo サイズ増加 | 保持する旧版は最新 3 バージョンまで、古いものは `.gitignore` または削除 |
| --template-version と --template の組み合わせ不整合 | flag が衝突してエラー | `--template-version` は `--template` 指定時のみ有効とし、単独指定時は warning で無視 |
| 11 role 全件への version 付加漏れ | grep で検出できない role が発生 | Sprint .3 テストで全 11 ファイルの version フィールド存在を自動チェック |

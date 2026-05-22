---
plan_id: PLAN-199
title: "PLAN-199: HELIX framework semver version bumping framework"
kind: impl
layer: cross
drive: be
status: draft
size: M
created: 2026-05-23
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — helix/VERSION file + helix-version CLI 実装 (bump/show/changelog)"
  - role: pmo-sonnet
    slot_label: "PMO — CHANGELOG.md template 整合確認・既存 PLAN/ADR との drift チェック"
  - role: tl-advisor
    slot_label: "TL adversarial check — semver bump ルール + breaking change 判定基準設計"
  - role: docs
    slot_label: "Docs — CHANGELOG.md 初版起草・version history セクション整備"
generates:
  - artifact_path: helix/VERSION
    artifact_type: config
  - artifact_path: cli/helix-version
    artifact_type: cli_extension
  - artifact_path: CHANGELOG.md
    artifact_type: markdown_doc
  - artifact_path: cli/lib/tests/test_helix_version.py
    artifact_type: test
  - artifact_path: docs/adr/ADR-059-helix-semver-versioning.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-091
  blocks: []
---

# PLAN-199: HELIX framework semver version bumping framework

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-059** で凍結予定:
- semver (MAJOR.MINOR.PATCH) 採用理由と breaking change 定義
- `helix/VERSION` を single source of truth とする方針
- CHANGELOG.md 自動生成のコミットメッセージ規約適用範囲

## 背景

HELIX framework は CLAUDE.md / SKILL_MAP.md / 100+ PLAN / 50+ ADR で構成された複合ドキュメント体系であるが、**framework 自体の version が不明確**という状態が継続している。

現状の問題:
- CLAUDE.md に「v2.2」「v2.3」等の断片的 version 記述が混在するが、統一された version 管理が存在しない
- PLAN frontmatter schema 変更 / SKILL.md format 変更などの **breaking change** が commit log のみに埋没し、利用者が追跡できない
- `helix doctor` / `helix plan lint` の出力に framework version が表示されず、診断結果の再現性が低い
- 複数 session にまたがる V5 framework 移行 (PLAN-091〜099) でも version 識別子がなく、どの version の HELIX を使っているか不明

## 要件 (DoD)

1. `helix/VERSION` file が存在し、semver 文字列 (`X.Y.Z`) を単一行で保持する
2. `helix version show` が現在の version を標準出力する
3. `helix version bump --type major|minor|patch` が VERSION を更新し、CHANGELOG.md に entry を追記する
4. `helix version changelog --since vX.Y.Z` が指定 tag 以降の commit を集約して release notes を生成する
5. `helix doctor` の出力先頭に `HELIX vX.Y.Z` が表示される
6. breaking change 定義が ADR-059 で明文化されている

## 設計方針

### semver bump ルール

| bump type | トリガー条件 |
|---|---|
| **major** | PLAN frontmatter 必須フィールド追加 / VALID_KINDS 削除 / VALID_LAYERS 削除 / hook 出力 protocol 変更 |
| **minor** | 新 CLI subcommand 追加 / PLAN frontmatter オプションフィールド追加 / 新 VALID_KINDS 追加 |
| **patch** | bug fix / doc 更新 / test 追加 / 既存 CLI のメッセージ修正 |

### 初期 version

現状を観測したうえで ADR-059 で確定:
- V5 framework (PLAN-091〜099) 完遂 = minor 9 相当
- PLAN-100 retrofit = patch 相当
- 初期値案: `2.5.0` (V2 ベース + V5 minor bump × 5 相当)

### `helix/VERSION` file 規約

```
2.5.0
```

単一行、末尾改行あり、コメント不可。

### CLI 設計

```bash
helix version show                         # 現在 version を表示
helix version bump --type patch            # PATCH bump + CHANGELOG entry 追記
helix version bump --type minor            # MINOR bump + PATCH reset + CHANGELOG entry
helix version bump --type major            # MAJOR bump + MINOR/PATCH reset + CHANGELOG entry
helix version changelog [--since vX.Y.Z]  # release notes 生成 (git log ベース)
helix version tag                          # git tag vX.Y.Z を作成 (dry-run あり)
```

### CHANGELOG.md 自動生成

コミットメッセージ規約 (`feat / fix / chore / docs / test / refactor`) を parse して section 分類:
- `feat:` → Added
- `fix:` → Fixed
- `refactor:` / `chore:` → Changed
- breaking change 明示 (`BREAKING CHANGE:` footer) → Breaking Changes セクション

### helix doctor 統合

`helix doctor` 先頭行に `HELIX vX.Y.Z` を表示:
```
HELIX v2.5.0 — doctor check
```

## 実装ステップ (L4 Sprint)

### Sprint .1: helix/VERSION 初期化 + helix-version show

- `helix/VERSION` 作成 (初期値は TL と協議の上 ADR-059 で確定)
- `cli/helix-version` bash script 骨格 + `show` subcommand
- `cli/helix` router に `version` 登録
- test: `helix version show` が X.Y.Z 形式を出力することを確認

### Sprint .2: bump + CHANGELOG 生成

- `bump --type major|minor|patch` ロジック実装 (semver parse + increment + write)
- CHANGELOG.md 追記フォーマット設計 + git log parse
- test: bump 前後の VERSION 変化 + CHANGELOG entry 追記を確認

### Sprint .3: helix doctor 統合 + ADR-059 起票

- `helix doctor` 出力先頭 version 表示
- ADR-059 起票 (WebSearch 3 query 必須: semver.org / keep-a-changelog / SemVer for internal frameworks)
- 全回帰: `helix test --no-pytest --bats-only` + pytest

## 受入条件

- `helix/VERSION` が存在し `helix version show` が X.Y.Z を返す
- `helix version bump --type patch` 実行後に VERSION が更新され CHANGELOG.md に entry が追記される
- `helix doctor` 先頭に version 文字列が表示される
- ADR-059 が起票され breaking change 定義が明文化されている
- pytest + bats 全 PASS

## リスク

| リスク | 対応 |
|---|---|
| 初期 version 値の合意コスト | ADR-059 で TL adversarial check を通す |
| CHANGELOG.md が git commit 規約と乖離 | commit 規約 (CLAUDE.md §コミット規約) を正本とし parser を合わせる |
| helix doctor 出力形式変更による既存 test 破損 | bats test を先に更新してから実装 (TDD) |

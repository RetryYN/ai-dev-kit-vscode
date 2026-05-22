---
plan_id: PLAN-169
title: "PLAN-169: HELIX framework import tool (新規 repo への bulk import)"
layer: L4
kind: impl
status: draft
size: M
drive: be
created: 2026-05-23
owner: PM
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — 既存 helix init の import 対象資産棚卸し + 選択 import 仕様確認"
  - role: tl
    slot_label: "TL — import CLI 設計・dry-run / manifest / conflict 方針・ADR 起票判断"
  - role: se
    slot_label: "SE — cli/helix-import 実装 + cli/helix ルーター登録 + bats テスト"
  - role: qa
    slot_label: "QA — 実際の新規 repo を使った end-to-end 検証・dry-run 出力確認"
generates:
  - artifact_path: cli/helix-import
    artifact_type: cli_extension
  - artifact_path: cli/lib/import_manifest.py
    artifact_type: python_module
  - artifact_path: cli/tests/test_helix_import.bats
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_plans:
  - PLAN-006-upstream-meta-phase
related_docs:
  - cli/helix-init
  - helix/HELIX_CORE.md
  - skills/SKILL_MAP.md
  - cli/ROLE_MAP.md
---

# PLAN-169: HELIX framework import tool (新規 repo への bulk import)

> **kind**: impl (helix import CLI 新規実装)
> **layer**: L4
> **drive**: be (CLI 拡張が中心)
> **本 PLAN の役割**: 新規 project への HELIX framework 導入は現在 `helix init` のみが対応しているが、既存 repo に後から skill / PLAN template / hook / CLAUDE.md を **選択的に bulk import** する手段がない。本 PLAN で `helix import` CLI を実装し、任意の target repo へ framework 資産を安全にコピーできるようにする。

---

## §0. 背景・問題設定

### 現状の限界

`helix init` は **新規 project の初期化** を前提にしており、既存 repo への後付け導入には以下の問題がある。

| 問題 | 影響 |
|---|---|
| `helix init` は既存ファイルを上書きする安全策がない | 既存 CLAUDE.md / hook を誤って破壊するリスク |
| import 対象を選べない (skill のみ / hook のみ 等) | 不要な資産まで一括コピーされる |
| dry-run で事前確認できない | 実行前に影響範囲を把握できない |
| 新 repo に HELIX を導入したチームが手順を再現できない | オンボーディングコスト増大 |

### 解決アプローチ

`helix import --target <new-repo>` で framework 資産を安全に bulk copy し、`--include` フラグで対象カテゴリを絞り込める CLI を実装する。`--dry-run` で事前確認も可能とする。

---

## §1. 目的

1. `helix import --target <path>` で HELIX framework 資産 (skill / template / hook / CLAUDE.md / SKILL_MAP) を target repo へ bulk copy する
2. `--include <categories>` フラグで import 対象を選択できる (例: `--include skills,hooks`)
3. `--dry-run` で実際のコピーを行わず、コピー予定の全ファイル一覧と conflict 一覧を出力する
4. conflict (既存ファイルあり) はデフォルト skip、`--overwrite` で上書きを許可する

---

## §2. CLI 仕様

### コマンド形式

```bash
helix import --target <new-repo-path> \
  [--include skills,templates,hooks,claude,skill-map] \
  [--dry-run] \
  [--overwrite]
```

### オプション仕様

| オプション | 説明 | デフォルト |
|---|---|---|
| `--target <path>` | import 先 repo のルートパス (必須) | — |
| `--include <list>` | カンマ区切りのカテゴリ指定 | all (全カテゴリ) |
| `--dry-run` | ファイルコピーせず予定一覧を出力 | false |
| `--overwrite` | 既存ファイルを上書きする | false (デフォルト: skip) |

### カテゴリ一覧

| カテゴリ名 | コピー元 (HELIX_HOME 相対) | コピー先 (target 相対) |
|---|---|---|
| `skills` | `skills/` | `skills/` |
| `templates` | `cli/templates/` | `cli/templates/` |
| `hooks` | `.claude/hooks/` | `.claude/hooks/` |
| `agents` | `.claude/agents/` | `.claude/agents/` |
| `claude` | `CLAUDE.md` | `CLAUDE.md` |
| `skill-map` | `skills/SKILL_MAP.md` | `skills/SKILL_MAP.md` |

---

## §3. 実装方針

### Sprint .1: pmo-sonnet — 資産棚卸し + 仕様確認

担当: pmo-sonnet

```bash
# import 対象資産の確認
find skills/ -name "SKILL.md" | wc -l
ls .claude/hooks/ | wc -l
ls .claude/agents/ | wc -l
ls cli/templates/ | head -20
```

出力: 各カテゴリの file 数 + conflict 判定ロジックの仕様メモ

### Sprint .2: tl — CLI 設計 + import_manifest.py 設計

担当: tl

設計対象:
- `cli/lib/import_manifest.py`: カテゴリ → src/dst パスリスト生成、conflict 検出、dry-run 出力
- `cli/helix-import`: Bash 本体 (argparse 相当を getopts で実装、import_manifest.py を呼び出す)
- cli/helix への routing 登録

conflict 判定ルール:
1. dst に同名ファイルが存在 → skip + WARN 出力 (デフォルト)
2. `--overwrite` 指定時 → 上書きコピー + INFO 出力
3. `--dry-run` 時 → 実際のコピーなし、WOULD_COPY / WOULD_SKIP を stdout に出力

### Sprint .3: se — cli/helix-import 実装

担当: se

実装ファイル:
- `cli/helix-import` (Bash、メイン CLI)
- `cli/lib/import_manifest.py` (Python、manifest 生成・conflict 検出)

```bash
# cli/helix-import の骨格
#!/usr/bin/env bash
set -euo pipefail
HELIX_HOME="$(cd "$(dirname "$0")/.." && pwd)"
# getopts で --target / --include / --dry-run / --overwrite をパース
# python3 cli/lib/import_manifest.py --source "$HELIX_HOME" \
#   --target "$TARGET" --include "$INCLUDE" ${DRY_RUN:+--dry-run} \
#   ${OVERWRITE:+--overwrite}
```

cli/helix routing 登録 (2 行追加):

```bash
import) exec "$HELIX_CLI_DIR/helix-import" "$@" ;;
```

### Sprint .4: qa — end-to-end 検証

担当: qa

```bash
# テスト用の空 repo を作成して dry-run 確認
mkdir -p /tmp/test-target-repo
helix import --target /tmp/test-target-repo --dry-run
# WOULD_COPY が出力されることを確認

# 実際の import
helix import --target /tmp/test-target-repo --include skills
ls /tmp/test-target-repo/skills/

# conflict テスト
echo "existing" > /tmp/test-target-repo/CLAUDE.md
helix import --target /tmp/test-target-repo --include claude
# SKIP WARN が出力されることを確認

# overwrite テスト
helix import --target /tmp/test-target-repo --include claude --overwrite
grep -q "existing" /tmp/test-target-repo/CLAUDE.md && echo "FAIL: not overwritten" || echo "PASS"
```

---

## §4. Sprint 計画

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **Sprint .1** | 資産棚卸し + 仕様確認 | pmo-sonnet | カテゴリ別 file 数確認・conflict ルール仕様メモ |
| **Sprint .2** | CLI + import_manifest.py 設計 | tl | 設計書または本 §3 Sprint .2 メモ確定 |
| **Sprint .3** | cli/helix-import + import_manifest.py 実装 | se | `bash -n` + `python3 -m py_compile` PASS |
| **Sprint .4** | end-to-end 検証 + bats テスト | qa | `helix import --dry-run` 動作確認 + bats 全 PASS |

---

## §5. DoD (Definition of Done)

1. `helix import --target <path> --dry-run` が WOULD_COPY / WOULD_SKIP を出力する
2. `helix import --target <path> --include skills` が skills/ を target にコピーする
3. conflict (既存ファイル) はデフォルト skip、`--overwrite` で上書きが動作する
4. `helix commands` に `import` が表示される
5. `bash -n cli/helix-import` PASS
6. `python3 -m py_compile cli/lib/import_manifest.py` PASS
7. bats テスト (Sprint .4) が全 PASS
8. `python3 cli/lib/plan_validator.py docs/plans/PLAN-169-*.md` PASS

---

## §6. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-169-*.md |
| ② 実装コード | Sprint .3 で生成 | cli/helix-import / cli/lib/import_manifest.py |
| ③ テスト設計 | Sprint .4 で起票 | docs/v2/L4-test-design/PLAN-169-test-design.md |
| ④ テストコード | Sprint .4 実装 | cli/tests/test_helix_import.bats |

**双方向 reference**:
- 本 PLAN (①) → 実装 (②): `generates.artifact_path` に明記
- 実装 (②) → 本 PLAN (①): cli/helix-import 先頭 comment に `# PLAN-169` 明記
- 本 PLAN (①) → テスト設計 (③): Sprint .4 起票後に §6 に追記
- テスト設計 (③) → 本 PLAN (①): frontmatter `related_plans: [PLAN-169]` 明記

---

## §7. リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| target repo に同名ファイルが多数存在し全件 skip | import が実質無効化 | dry-run で事前確認を推奨、`--overwrite` オプションを提供 |
| symlink / 実行権限が target に正しくコピーされない | hook が動作しない | Sprint .4 で権限 + symlink テストを追加 |
| HELIX_HOME が未設定の環境で実行 | コピー元パスが解決できない | cli/helix-import の先頭で HELIX_HOME を自動 resolve (script の dirname から導出) |
| skills/ が大量ファイルで import に時間がかかる | UX 低下 | progress 表示 (`echo "Copying skills... (N files)"`) を追加 |

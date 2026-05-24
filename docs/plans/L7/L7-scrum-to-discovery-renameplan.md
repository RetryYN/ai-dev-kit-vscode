---
plan_id: L7-scrum-to-discovery-renameplan
title: "L7-scrum-to-discovery-renameplan: helix-scrum → helix-discovery 名称統一 (CLI / skill / runtime dir / doc / PLAN kind enum 全 6 範囲、backward compat 4 段階)"
kind: refactor
layer: L7
drive: be
status: draft
created: 2026-05-24
revised: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/discovery-workflow.md
pairs_test_design:
  - HELIX-workflows/helix-process/discovery-workflow.md
  - HELIX-workflows/helix-process/scrum-workflow.md
is_reference: false
agent_slots:
  - role: tl-advisor
    slot_label: "TL — CLI alias 設計・runtime dir migration 方式・backward compat timeline 妥当性検証 (R1 adversarial check)"
  - role: se
    slot_label: "SE — cli/helix-discovery 実装 + alias shim + runtime dir auto-migrate + テスト拡張"
  - role: pmo-sonnet
    slot_label: "PMO — doc 更新 4 件整合チェック + 4 artifact 双方向 trace review"
generates:
  - artifact_path: cli/helix-discovery
    artifact_type: cli_extension
  - artifact_path: cli/helix-scrum (deprecated alias shim)
    artifact_type: cli_extension
  - artifact_path: docs/v2/L7-design/L7-scrum-to-discovery-rename-design.md
    artifact_type: design
  - artifact_path: docs/v2/L7-test-design/L7-scrum-to-discovery-rename-test-design.md
    artifact_type: test_design
  - artifact_path: cli/lib/tests/test_helix_discovery_alias.py
    artifact_type: test
  - artifact_path: cli/tests/helix-discovery.bats
    artifact_type: test
dependencies:
  parent: L7-helix-workflows-parent-acceptedplan
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/discovery-workflow.md
  - HELIX-workflows/helix-process/scrum-workflow.md
  - skills/SKILL_MAP.md (§HELIX Scrum line 245-271)
  - skills/agent-skills/helix-scrum/SKILL.md
  - cli/helix-scrum
  - cli/helix
  - helix/HELIX_CORE.md
  - CLAUDE.md
  - AGENTS.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/discovery-workflow.md](../../../HELIX-workflows/helix-process/discovery-workflow.md)
> **本 PLAN の対象**: HELIX-workflows V2 完全移行で「Scrum (アジャイル)」と「Discovery (検証駆動)」が別概念に整理されたことに伴い、既存の `helix scrum` CLI・`skills/agent-skills/helix-scrum/` skill・`.helix/scrum/` runtime dir・各種 doc 4 件・PLAN kind enum を全て「discovery」名称に統一する。backward compat (alias / deprecated warning / migration / removal) を 4 段階で提供し、既存ユーザーのデータと操作手順を保全する。
> **位置づけ**: SKILL_MAP.md §HELIX Scrum line 247 に「将来の rename は別 PLAN carry」として明記された carry を消化する PLAN。SKILL_MAP.md:197 carry (integration-map §結論 carry 列) の消化にも対応する。

**kind: refactor の根拠 (deviation-plan-map.md §モード × 逸脱パターン)**:
Refactor モード = 「構造改善（振る舞い不変）」。`helix scrum` CLI の機能（D0-D4 フェーズ、
backlog/sprint/verify 操作）を変えずに名称構造 (scrum → discovery) を改善するため、
kind=refactor が deviation-plan-map の定義に合致する。
参照: `HELIX-workflows/helix-process/deviation-plan-map.md` §モード × 逸脱パターン

### SKILL_MAP.md:247 引用 (carry 根拠)

```
> 既存 `helix scrum` CLI / `agent-skills/helix-scrum` skill / S0-S4 phase / `.helix/scrum/` 配下は
> legacy 互換で維持されるが、概念的には Discovery として運用する。
> **将来の rename は別 PLAN carry**。
```

### 概念整理の前提

| 旧名称 | 新名称 | 意味 |
|---|---|---|
| HELIX Scrum / `helix scrum` CLI | Discovery / `helix discovery` CLI | 仮説検証・PoC・verify scripts による不確実性の潰し込み |
| `skills/agent-skills/helix-scrum/` | `skills/agent-skills/helix-discovery/` | 同上のスキル定義 |
| `.helix/scrum/` | `.helix/discovery/` | runtime state dir (backlog.yaml / sprint.yaml / verify/) |
| S0-S4 フェーズ記号 | D0-D4 フェーズ記号 | 段階名称 (Discovery フェーズ) |
| アジャイル Scrum (新概念) | 独立して Scrum ワークフロー | ユーザーと反復で要件を固める別モード |

---

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 影響範囲 inventory 確定 (CLI / skill / runtime dir / doc 4 件 / PLAN kind enum / 既存 PLAN retrofit 件数) | PM | ✅ done (§3) |
| 2 | backward compat 4 段階タイムライン設計 | PM | ✅ done (§2) |
| 3 | CLI alias 設計 + routing 契約確定 | PM | ✅ done (§8) |
| 4 | tl-advisor adversarial check R1 | PM → TL | □ pending |
| 5 | TL R1 指摘反映 (もしあれば) | PM | □ pending |
| 6 | tl-advisor adversarial check R2 (R1 で needs_revision の場合) | PM → TL | □ pending |
| 7 | SE 委譲: Sprint .2 CLI alias 実装 (`cli/helix-discovery` + `cli/helix-scrum` shim) | PM → SE | □ pending |
| 8 | SE 委譲: Sprint .3 skill rename (`skills/agent-skills/helix-scrum/` → `helix-discovery/`) | PM → SE | □ pending |
| 9 | SE 委譲: Sprint .4 runtime dir migration (`auto_migrate_scrum_to_discovery()`) | PM → SE | □ pending |
| 10 | SE 委譲: Sprint .5 doc 更新 4 件 (CLAUDE.md / AGENTS.md / SKILL_MAP.md / HELIX_CORE.md) | PM → SE | □ pending |
| 11 | SE 委譲: Sprint .6 既存 PLAN kind retrofit + smoke test | PM → SE | □ pending |
| 12 | bash -n / shellcheck / python3 -m py_compile 確認 | SE | □ pending |
| 13 | pytest test_helix_discovery_alias.py + bats helix-discovery.bats 全 PASS | SE | □ pending |
| 14 | cli/helix router 登録 (discovery) + `helix help` + `helix commands check` 確認 | SE | □ pending |
| 15 | pmo-sonnet で 4 artifact 双方向 trace 確認 + doc 更新整合チェック | PM → PMO | □ pending |
| 16 | commit + push | PM | □ pending |

---

## §2 設計判断: backward compat 4 段階タイムライン

### 4 段階の定義

```
Stage 1: Alias 段階 (本 PLAN 実装直後)
  - cli/helix-discovery が正本コマンドとして登録
  - cli/helix-scrum は deprecated alias shim として残存
  - helix router に両方を登録 (discovery → helix-discovery、scrum → helix-scrum shim)
  - ユーザーへの影響: なし (既存コマンドが動く)

Stage 2: Warning 段階 (本 PLAN コミット後、次の minor release で開始)
  - cli/helix-scrum shim を実行すると stderr に deprecated warning を出力
  - warning message: "[WARN] 'helix scrum' は非推奨です。'helix discovery' を使用してください。helix-scrum は L7-scrum-to-discovery-rename PLAN (removal: L7-helix-scrum-removal-YYYY) で削除予定。"
  - .helix/scrum/ dir 検出時に auto-migrate 提案 ("helix discovery migrate を実行してください") を表示
  - ユーザーへの影響: warning が出るが操作は継続可能

Stage 3: Migration 段階 (Warning 段階開始から 2 minor release 後)
  - .helix/scrum/ が存在する場合、helix discovery コマンド実行時に auto-migrate を自動実行
  - auto-migrate: .helix/scrum/ → .helix/discovery/ へ cp -r + .helix/scrum/ に README.deprecated を配置
  - helix scrum コマンドは warning を出した上で helix discovery にリダイレクト
  - ユーザーへの影響: 初回実行時にマイグレーション自動実行 (破壊的変更なし、旧 dir は保持)

Stage 4: Removal 段階 (Migration 段階開始から 3 minor release 後)
  - cli/helix-scrum shim を削除
  - helix router の scrum エントリを削除
  - .helix/scrum/ の旧 dir サポートを終了 (README.deprecated のみ残す)
  - 実施タイミング: 別 PLAN (L7-helix-scrum-removal-plan、本 PLAN §10 で carry 起票) で管理
```

### removal タイムライン (具体的 PLAN ID + 条件)

| Stage | 開始条件 | 終了条件 | 担当 PLAN |
|---|---|---|---|
| Stage 1 (Alias) | 本 PLAN commit | 次 minor release | 本 PLAN |
| Stage 2 (Warning) | 本 PLAN の次 minor release commit | Warning 開始から 2 minor release | 本 PLAN (warning 実装含む) |
| Stage 3 (Migration) | Warning 開始から 2 minor release 後の commit | Migration 開始から 3 minor release | 本 PLAN (auto-migrate 実装含む) |
| Stage 4 (Removal) | Migration 開始から 3 minor release 後 | — | **L7-helix-scrum-removal-plan** (§10 carry) |

**重要**: Stage 4 は別 PLAN (`L7-helix-scrum-removal-plan`) で管理する。本 PLAN の DoD は Stage 3 完了 (auto-migrate 実装 + warning 実装) まで。

---

## §3 影響範囲 inventory

> **責務分離 (cross-cutting-mechanisms との関係)**:
> 本 CLI (helix discovery / helix scrum) は横断機構 (helix interrupt / debt / drift-check / readiness) と別レイヤーである。
> rename 作業は横断機構に影響しない。cross-cutting-mechanisms.md で定義される機構は本 PLAN の影響範囲に含まない。

> **generates trace と deviation-plan-map の対応**:
> frontmatter `generates` の各 artifact は deviation-plan-map.md の kind=refactor 実装物分類に準拠する。
> `cli/helix-discovery` (cli_extension) は refactor 実装物、`docs/v2/L7-design/` 以下 (design) は refactor 設計書、
> テスト 2 件は refactor 検証物として trace される。

### 3.1 CLI

| 対象 | 変更内容 | priority |
|---|---|---|
| `cli/helix-scrum` (1028 行) | → deprecated alias shim に縮小、先頭に warning 追加して `helix-discovery "$@"` に転送 | P1 |
| `cli/helix-discovery` (新規) | helix-scrum の内容を helix-discovery としてコピー、内部変数名 `SCRUM_DIR` → `DISCOVERY_DIR` 等を置換 | P1 |
| `cli/helix` (router) | `discovery)` エントリを追加、`scrum)` を shim 経由で維持 | P1 |

**内部変数置換対象** (`cli/helix-scrum` → `cli/helix-discovery`):

| 旧 | 新 |
|---|---|
| `SCRUM_DIR="$HELIX_DIR/scrum"` | `DISCOVERY_DIR="$HELIX_DIR/discovery"` |
| `BACKLOG="$SCRUM_DIR/backlog.yaml"` | `BACKLOG="$DISCOVERY_DIR/backlog.yaml"` |
| `SPRINT_FILE="$SCRUM_DIR/sprint.yaml"` | `SPRINT_FILE="$DISCOVERY_DIR/sprint.yaml"` |
| `SCRUM_VERIFY_DIR="$SCRUM_DIR/verify"` | `DISCOVERY_VERIFY_DIR="$DISCOVERY_DIR/verify"` |
| `scrum_*` 関数名 | `discovery_*` 関数名 |

### 3.2 skill

| 対象 | 変更内容 | priority |
|---|---|---|
| `skills/agent-skills/helix-scrum/` (SKILL.md のみ) | ディレクトリを `skills/agent-skills/helix-discovery/` に rename + SKILL.md 内容更新 | P1 |
| SKILL.md name / description | `helix-scrum` → `helix-discovery`、「Scrum モード」→「Discovery モード」 | P1 |
| SKILL.md upstream | `cli/helix-scrum` → `cli/helix-discovery` | P1 |
| SKILL.md helix_layer | `[S0, S1, S2, S3, S4]` → `[D0, D1, D2, D3, D4]` | P1 |
| SKILL.md 内文章 | S0-S4 フェーズ記号を D0-D4 に置換、「Scrum モード」を「Discovery モード」に置換 | P1 |

### 3.3 runtime dir

| 対象 | 変更内容 | priority |
|---|---|---|
| `.helix/scrum/` | → `.helix/discovery/` へ auto-migrate (§5 Sprint .4 参照) | P0 (user data) |
| `.helix/scrum/backlog.yaml` | content はそのまま migrate、yaml key は変更なし | P0 |
| `.helix/scrum/sprint.yaml` | content はそのまま migrate | P0 |
| `.helix/scrum/verify/` | content はそのまま migrate | P0 |

**user data 保全原則**: `.helix/scrum/` は削除しない。`cp -r .helix/scrum/ .helix/discovery/` 後、`.helix/scrum/README.deprecated` を配置して「このディレクトリは廃止されています。.helix/discovery/ を参照してください。」を明示する。

### 3.4 doc 更新 4 件

| ファイル | 更新箇所 | 変更内容 |
|---|---|---|
| `CLAUDE.md` | §HELIX ワークフロー「helix scrum init」言及箇所 | `helix discovery init (旧: helix scrum init)` に更新 |
| `AGENTS.md` | Scrum 関連記述 | `Discovery (legacy: helix scrum)` 表記に更新 |
| `skills/SKILL_MAP.md` | §HELIX Scrum section (line 245-271) | section title を「§HELIX Discovery (旧: HELIX Scrum)」に変更、CLI コマンド例を `helix discovery` に更新、legacy 互換 note を保持 |
| `helix/HELIX_CORE.md` | §状態管理の二層構造 `.helix/scrum/` 言及箇所 | `.helix/discovery/ (旧: .helix/scrum/)` 表記に更新 |

### 3.5 PLAN kind enum

| 対象 | 変更内容 | priority |
|---|---|---|
| `plan_validator.py` VALID_KINDS | `"scrum"` を `"discovery"` に置換、legacy compat として `"scrum"` も一定期間 warn-only で許容 | P1 |
| 既存 PLAN の `kind: scrum` | → `kind: discovery` に retrofit (§5 Sprint .6 で実施) | P2 |

**既存 PLAN 調査結果**: `grep -rn "kind: scrum" docs/plans/` で 0 件 (既存 PLAN に `kind: scrum` を使用しているものは確認されず)。引き続き Sprint .1 で確認を実施する。

---

## §4 Sprint 分割

### Sprint .1 — inventory 確認 + 設計確定

**目的**: 影響範囲の最終確定 (§3 の grep 確認)、接続契約の最終合意

**タスク**:
1. `grep -rn "helix scrum\|helix-scrum\|helix_scrum\|HELIX Scrum\|\.helix/scrum"` で全影響箇所を最終 grep
2. `grep -rn "kind: scrum\|kind=scrum" docs/plans/` で既存 PLAN retrofit 件数を確定
3. 本 PLAN §2 タイムライン / §8 接続契約を tl-advisor R1 に提示
4. tl-advisor フィードバック反映

**受入条件**: tl-advisor R1 が `passed` または `passed_with_minor_changes` であること

---

### Sprint .2 — CLI alias 実装

**目的**: `cli/helix-discovery` 新規作成 + `cli/helix-scrum` → deprecated shim 変換 + helix router 登録

**実装手順**:
1. `cli/helix-scrum` を `cli/helix-discovery` にコピー
2. `cli/helix-discovery` の内部変数・関数名を §3.1 変換表に従い置換
3. `cli/helix-scrum` を deprecated alias shim に縮小:

```bash
#!/bin/bash
# helix-scrum: DEPRECATED — 'helix discovery' を使用してください
# このファイルは backward compat のために残されています
# Stage 4 removal: L7-helix-scrum-removal-plan で削除予定

>&2 echo "[DEPRECATED] 'helix scrum' は非推奨です。'helix discovery' を使用してください。"
>&2 echo "[DEPRECATED] L7-scrum-to-discovery-renameplan による名称統一。Stage 4 removal: L7-helix-scrum-removal-plan"
exec "$(dirname "$0")/helix-discovery" "$@"
```

4. `cli/helix` router に `discovery)` エントリを追加:

```bash
# 既存 scrum エントリの後に追加
discovery)  exec "$SCRIPT_DIR/helix-discovery" "$@" ;;
```

5. `cli/helix` の help/usage にも `discovery` を追記

**受入条件**:
- `bash -n cli/helix-discovery` PASS
- `shellcheck cli/helix-discovery` PASS (warnings 許容、errors 不可)
- `helix discovery help` が正常に動作する
- `helix scrum help` が deprecated warning を出力した上で `helix discovery help` と同等の出力を返す

---

### Sprint .3 — skill rename

**目的**: `skills/agent-skills/helix-scrum/` → `skills/agent-skills/helix-discovery/` への rename + SKILL.md 内容更新

**実装手順**:
1. `mv skills/agent-skills/helix-scrum/ skills/agent-skills/helix-discovery/`
2. `skills/agent-skills/helix-discovery/SKILL.md` の以下を更新:
   - frontmatter `name:` を `helix-discovery` に変更
   - frontmatter `description:` を Discovery モードの説明に更新
   - frontmatter `helix_layer:` を `[D0, D1, D2, D3, D4]` に変更
   - frontmatter `upstream:` を `cli/helix-discovery` に変更
   - 本文の「HELIX Scrum」→「HELIX Discovery」、「S0-S4」→「D0-D4」を置換
   - 本文の `helix scrum` コマンド例 → `helix discovery` に更新
   - legacy note: 「旧: helix scrum (S0-S4)。backward compat alias は L7-scrum-to-discovery-renameplan §2 参照」を Overview 末尾に追記
3. `docs/agent-skills/README.md` の `helix-scrum` 参照を `helix-discovery` に更新

**受入条件**:
- `skills/agent-skills/helix-discovery/SKILL.md` が存在する
- `skills/agent-skills/helix-scrum/` が存在しない (rename 完了)
- `grep -rn "helix-scrum" skills/agent-skills/` が 0 件

---

### Sprint .4 — runtime dir migration

**目的**: `.helix/scrum/` → `.helix/discovery/` への auto-migrate 実装

**実装手順**: `cli/helix-discovery` に `cmd_migrate()` サブコマンドを追加

```bash
cmd_migrate() {
  local src="$HELIX_DIR/scrum"
  local dst="$HELIX_DIR/discovery"

  if [[ ! -d "$src" ]]; then
    echo "[INFO] .helix/scrum/ は存在しません。migration 不要です。"
    return 0
  fi

  if [[ -d "$dst" ]]; then
    echo "[WARN] .helix/discovery/ は既に存在します。上書きしません。"
    echo "[INFO] 手動で確認してください: ls .helix/discovery/"
    return 1
  fi

  echo "[INFO] .helix/scrum/ → .helix/discovery/ に migration を開始します..."
  cp -r "$src" "$dst"
  cat > "$src/README.deprecated" << 'EOF'
# DEPRECATED

このディレクトリ (.helix/scrum/) は非推奨です。
データは .helix/discovery/ に migration されました。

このディレクトリは L7-helix-scrum-removal-plan (Stage 4) で削除される予定です。
それまでは参照用として残されます。
EOF
  echo "[OK] migration 完了: .helix/scrum/ → .helix/discovery/"
  echo "[INFO] 元のディレクトリ .helix/scrum/ は保持されています (README.deprecated を参照)。"
}
```

**auto-migrate トリガー** (Stage 3 Migration 段階で有効化):
- `helix discovery init` / `helix discovery backlog` 等の実行時に `.helix/scrum/` が存在し `.helix/discovery/` が存在しない場合、自動的に `cmd_migrate` を呼び出す
- Stage 2 (Warning 段階) では migrate 提案のみ (自動実行しない)

**受入条件**:
- `helix discovery migrate` が `.helix/scrum/` を `.helix/discovery/` に正常 cp する
- `.helix/scrum/README.deprecated` が生成される
- `.helix/scrum/` のデータが消えない (cp のみ)
- `.helix/discovery/` が既に存在する場合はエラーで中断する

---

### Sprint .5 — doc 更新 4 件

**目的**: §3.4 で定義した 4 ファイルの更新

**実装手順**:
1. `skills/SKILL_MAP.md` §HELIX Scrum section の更新:
   - section title: `### HELIX Scrum（検証駆動 / 要件未確定時）` → `### HELIX Discovery（検証駆動 / 要件未確定時、旧: HELIX Scrum）`
   - CLI コマンド例: `helix scrum init` → `helix discovery init (旧: helix scrum init)`
   - phase 記号: `S0` → `D0`、`S1` → `D1` ... `S4` → `D4`
   - 責務整理 note の「将来の rename は別 PLAN carry」を「rename 完了 (L7-scrum-to-discovery-renameplan)」に更新
2. `helix/HELIX_CORE.md` の `.helix/scrum/` 参照を `.helix/discovery/ (旧: .helix/scrum/)` に更新
3. `CLAUDE.md` の `helix scrum init` コマンド例を `helix discovery init` に更新 (§HELIX ワークフロー)
4. `AGENTS.md` の Scrum 関連記述を `Discovery (legacy: helix scrum)` 表記に更新

**受入条件**:
- 4 ファイルの更新が完了している
- `grep -rn "helix scrum init" CLAUDE.md AGENTS.md` が 0 件
- pmo-sonnet の doc 整合チェックが PASS

---

### Sprint .6 — 既存 PLAN kind retrofit + smoke test

**目的**: `plan_validator.py` の kind enum 更新 + 既存 PLAN retrofit + 全体 smoke test

**実装手順**:
1. `grep -rn "kind: scrum" docs/plans/` で retrofit 対象を確定
2. 対象 PLAN の `kind: scrum` → `kind: discovery` に Edit
3. `plan_validator.py` の `VALID_KINDS` に `"discovery"` を追加 (既存 `"scrum"` は warn-only で一定期間残す)
4. smoke test:
   - `helix discovery help` が正常動作
   - `helix scrum help` が deprecated warning + 正常動作
   - `helix discovery migrate` が dry-run 相当の動作
   - `python3 -m py_compile cli/lib/plan_validator.py` PASS
   - `helix doctor` に新規 FAIL が出ないこと

**受入条件**:
- `plan_validator.py` が `discovery` kind を PASS として扱う
- `helix doctor` の FAIL 件数が Sprint .6 開始前と同数以下
- smoke test 全項目 PASS

---

## §5 DoD (Definition of Done)

以下を全て満たすこと:

| # | 条件 | 検証方法 |
|---|---|---|
| D1 | `helix discovery <subcommand>` が全サブコマンド正常動作 | bats helix-discovery.bats 全 PASS |
| D2 | `helix scrum <subcommand>` が deprecated warning を出力した上で同等動作 | bats helix-discovery.bats + 手動 smoke |
| D3 | `skills/agent-skills/helix-discovery/SKILL.md` が存在し、内容が Discovery モードに更新されている | grep 確認 |
| D4 | `skills/agent-skills/helix-scrum/` が存在しない | ls 確認 |
| D5 | `helix discovery migrate` が `.helix/scrum/` → `.helix/discovery/` を安全に移行する | pytest test_helix_discovery_alias.py |
| D6 | doc 更新 4 件 (CLAUDE.md / AGENTS.md / SKILL_MAP.md / HELIX_CORE.md) が完了 | pmo-sonnet review PASS |
| D7 | `plan_validator.py` が `kind: discovery` を PASS として扱う | pytest PASS |
| D8 | `helix doctor` の FAIL 件数が本 PLAN 実施前と同数以下 | `helix doctor` 実行確認 |
| D9 | tl-advisor R1 (または R2) が `passed` または `passed_with_minor_changes` | tl-advisor 実行記録 |
| D10 | 4 artifact が別文書として存在し、双方向 reference が完備 | pmo-sonnet 4 artifact trace PASS |

> **automation-gate-map 適用範囲**: 本 CLI (helix discovery / helix scrum) は `gate-checks.yaml` の static チェック適用範囲外。Discovery モードは機械側だけで工程進行を完結できない除外モード (automation-gate-map.md より)。本 PLAN の DoD は workflow doc 固有の上記 D1-D10 で代替する。

---

## §6 受入条件と検証

### bats テスト (`cli/tests/helix-discovery.bats`)

```bash
# 基本動作確認
@test "helix discovery help が正常に表示される" { ... }
@test "helix discovery init が .helix/discovery/ を作成する" { ... }
@test "helix discovery backlog add が動作する" { ... }
@test "helix discovery plan が sprint.yaml を生成する" { ... }
@test "helix discovery status が現在の状態を表示する" { ... }

# deprecated alias 確認
@test "helix scrum が deprecated warning を stderr に出力する" {
  run helix scrum help
  [[ "${output}" =~ "DEPRECATED" ]] || [[ "${stderr}" =~ "DEPRECATED" ]]
}
@test "helix scrum が helix discovery と同等の結果を返す" { ... }

# migration 確認
@test "helix discovery migrate が .helix/scrum/ を .helix/discovery/ に migration する" { ... }
@test "helix discovery migrate は .helix/scrum/ を削除しない" { ... }
@test "helix discovery migrate は .helix/discovery/ が既存の場合エラーを返す" { ... }
@test ".helix/scrum/ が存在しない場合 migrate は success を返す" { ... }
```

### pytest テスト (`cli/lib/tests/test_helix_discovery_alias.py`)

```python
def test_plan_validator_accepts_discovery_kind():
    """kind: discovery が VALID_KINDS に含まれる"""
    ...

def test_plan_validator_warns_for_scrum_kind():
    """kind: scrum が warn-only で通過する"""
    ...

def test_scrum_dir_migration_copies_data():
    """migrate() が scrum dir の内容を discovery dir にコピーする"""
    ...

def test_scrum_dir_migration_preserves_original():
    """migrate() が元の scrum dir を削除しない"""
    ...

def test_scrum_dir_migration_skips_if_discovery_exists():
    """migrate() は discovery dir が既存の場合 exit 1"""
    ...

def test_scrum_dir_migration_noop_if_scrum_not_exists():
    """migrate() は scrum dir がない場合 success を返す"""
    ...
```

---

## §7 risk / mitigation

| リスク | 影響 | 可能性 | 緩和策 |
|---|---|---|---|
| R1: ユーザーの `.helix/scrum/` データ消失 | HIGH | LOW | `cp -r` (削除なし) + README.deprecated で保全。`helix discovery migrate` は `cp -r` のみ実行し `rm -rf` しない |
| R2: alias 永続化リスク (removal が never になる) | MEDIUM | MEDIUM | `L7-helix-scrum-removal-plan` を §10 で carry 起票し、removal を別 PLAN の DoD に明示する |
| R3: doc 更新漏れによる SKILL_MAP.md drift | MEDIUM | MEDIUM | pmo-sonnet review を Sprint .5 の exit 条件に組み込む。`grep -rn "helix scrum init"` で漏れ検出 |
| R4: skill 内 reference の rename 漏れ | MEDIUM | LOW | `grep -rn "helix-scrum" skills/` を Sprint .3 exit 前に実行して 0 件を確認 |
| R5: helix-discovery の CLI 動作互換性劣化 | HIGH | LOW | `helix scrum <cmd>` と `helix discovery <cmd>` の同等性を bats で全サブコマンドテスト |
| R6: plan_validator.py の `kind: scrum` 即 fail-close 化 | MEDIUM | LOW | warn-only 期間を Stage 3 まで維持し、Stage 4 の `L7-helix-scrum-removal-plan` で fail-close に昇格 |
| R7: docs/agent-skills/README.md など §3 外の参照漏れ | LOW | MEDIUM | Sprint .1 で `grep -rn "helix-scrum"` の全 output を確認し、§3 に追記 |

---

## §8 V3 接続契約: 旧 scrum 呼び出し → 新 discovery 実体への routing

本節は tl-advisor R1 のレビュー対象となる CLI 設計の核心部分。

**Discovery mode の機械進行除外根拠 (automation-gate-map.md より)**:
Discovery (旧 Scrum) は「Scrum を除く全モードは機械側だけで進行できる」条件の除外対象であり、
gate-checks.yaml の static チェックのみでは工程進行を完結できない。
`helix size --uncertain` の routing は「機械判定 (--uncertain フラグ)」だが、
モード内の進行 (D0-D4) は人間 + AI の協働判断が前提となる。
このため、本 CLI の routing 設計 (alias shim + exec 透過転送) は機械自動実行の対象外とし、
ユーザー操作の透過転送に特化した設計を採用する。

### 呼び出しフロー契約

```
ユーザー入力                  routing 層                   実体
-----------                  ----------                   ------
helix discovery <cmd>  →  cli/helix router               cli/helix-discovery (正本)
helix scrum <cmd>      →  cli/helix router               cli/helix-scrum (deprecated shim)
                                ↓
                         stderr: "[DEPRECATED] ..."
                                ↓
                         exec cli/helix-discovery "$@"   (透過転送)
```

### signal_to_condition マッピング (旧 scrum 信号 → 新 discovery 実体)

| 旧信号 (入力) | 条件 | 新実体 (出力) | stage |
|---|---|---|---|
| `helix scrum init` | 常に | `helix discovery init` + deprecated warning | Stage 1-3 |
| `helix scrum backlog add` | 常に | `helix discovery backlog add` + deprecated warning | Stage 1-3 |
| `helix scrum poc` | 常に | `helix discovery poc` + deprecated warning | Stage 1-3 |
| `helix scrum verify` | 常に | `helix discovery verify` + deprecated warning | Stage 1-3 |
| `helix scrum decide` | 常に | `helix discovery decide` + deprecated warning | Stage 1-3 |
| `helix size --uncertain` | 常に | `helix discovery init` を案内 (旧: `helix scrum init`) | Stage 1 以降 |
| `.helix/scrum/` 存在 + init | Stage 2 | migrate 提案のみ | Stage 2 |
| `.helix/scrum/` 存在 + init | Stage 3 | auto-migrate 実行 | Stage 3 |

### runtime dir 解決優先順位

```python
def resolve_discovery_dir(helix_dir: str) -> str:
    """
    .helix/discovery/ が存在すれば優先。
    なければ .helix/scrum/ を fallback (Stage 2 用)。
    どちらもなければ .helix/discovery/ を新規作成先として返す。
    """
    discovery = os.path.join(helix_dir, "discovery")
    scrum_legacy = os.path.join(helix_dir, "scrum")

    if os.path.isdir(discovery):
        return discovery
    if os.path.isdir(scrum_legacy):
        # Stage 2: legacy fallback + migration 提案
        warn_legacy_dir(scrum_legacy)
        return scrum_legacy  # Stage 2 は読み取りのみ、書き込みは migration 後
    return discovery  # 新規作成先
```

### deprecated shim の実装契約

```bash
# cli/helix-scrum (deprecated shim)
# - exec で helix-discovery に転送することで、exit code も含めて透過
# - "$@" を変更せずに転送 (サブコマンド・引数はそのまま)
# - stderr に warning を出力 (stdout を汚染しない)
# - warning は 1 回のみ (loop しない)
>&2 printf '[DEPRECATED] helix scrum は非推奨です。\n'
>&2 printf '[DEPRECATED] "helix discovery %s" を使用してください。\n' "$*"
>&2 printf '[DEPRECATED] removal: L7-helix-scrum-removal-plan を参照\n'
exec "$(dirname "$0")/helix-discovery" "$@"
```

**制約**:
- deprecated warning は stderr のみ (stdout に混入しない)
- exit code は helix-discovery のものをそのまま返す (`exec` により透過)
- `"$@"` を変更しない (サブコマンドの透過転送)

---

## §9 関連 doc / 関連 PLAN

### 関連 doc

| doc | 関係 |
|---|---|
| `HELIX-workflows/helix-process/discovery-workflow.md` | parent_design (正本設計) |
| `HELIX-workflows/helix-process/scrum-workflow.md` | 新 Scrum (アジャイル) の定義 — 本 PLAN の rename 対象とは別概念 |
| `HELIX-workflows/helix-process/automation-gate-map.md` | Discovery が機械進行除外モードである根拠 (§8 V3 接続契約の前提) |
| `HELIX-workflows/helix-process/deviation-plan-map.md` | kind=refactor 根拠 (§モード × 逸脱パターン、§0 に引用済) |
| `HELIX-workflows/helix-process/cross-cutting-mechanisms.md` | 横断機構 (helix interrupt/debt/drift-check/readiness) との非重複確認。本 CLI は横断機構と別レイヤーのため、rename 作業は横断機構に影響しない |
| `skills/SKILL_MAP.md` §HELIX Scrum (line 245-271) | carry 根拠の記載箇所 |
| `skills/agent-skills/helix-scrum/SKILL.md` | rename 対象 skill |
| `cli/helix-scrum` | rename 対象 CLI |
| `docs/agent-skills/README.md` | `helix-scrum` 参照箇所 — Sprint .3 で更新 |
| `docs/design/L2-cli-architecture.md` | `helix scrum` 記述 — §3 外 carry 候補 |
| `docs/v2/V5-plan-outlines.md` | `helix scrum` 参照 — is_reference: true のため低優先 |

### 関連 PLAN

| PLAN | 関係 |
|---|---|
| `L7-helix-workflows-parent-acceptedplan` | parent (HELIX-workflows 正本化の親 PLAN) |
| `L7-helix-scrum-removal-plan` (未起票) | Stage 4 Removal 実施 PLAN (§10 carry) |

---

## §10 carry / 残課題

### Carry C1 (P1 — 本 PLAN 完了後に起票必須)

**L7-helix-scrum-removal-plan**: Stage 4 (cli/helix-scrum shim 完全削除 + helix router scrum エントリ削除 + .helix/scrum/ 完全サポート終了) を実施する PLAN。本 PLAN が Stage 3 (auto-migrate 実装) まで完了した後に起票する。

起票タイミング: Stage 3 の Migration 段階開始から 3 minor release 後の時点で起票を確認する。

### Carry C2 (P3 — 任意)

`docs/design/L2-cli-architecture.md` の `helix scrum` 記述 (line 89, 281) を `helix discovery` に更新する。is_reference の V1 doc であるため低優先。

### Carry C3 (P3 — 任意)

`docs/v2/V5-plan-outlines.md` の `helix scrum` 参照 (複数箇所) を更新する。is_reference の docs であるため低優先。

### Carry C4 (P2 — Sprint .1 で件数確定後に判断)

既存 PLAN の `kind: scrum` retrofit 件数が 5 件以上になる場合、Sprint .6 を Codex se に委譲して batch 処理する。現在の grep 結果では 0 件のため、Sprint .1 で再確認後に判断する。

### Carry C5 (P2 — 本 PLAN commit 後に実施)

`HELIX-workflows/helix-process/integration-map.md` の「コマンドの穴」リスト更新。現時点で `helix-discover` / `helix-discovery` が穴リストに未記載であるため、本 PLAN の rename 完了後に integration-map 側を update し、`helix discovery` が正式コマンドとして登録済みであることを反映する。更新箇所: integration-map.md §コマンドの穴 (または相当 section) に `helix-scrum → helix-discovery rename 完了 (L7-scrum-to-discovery-renameplan)` を記載する。

---

## §11 4 artifact 双方向 trace

| Artifact | ファイル | trace 先 |
|---|---|---|
| **① 設計** | 本 PLAN §2/§3/§8 | → ③ テスト設計 (`docs/v2/L7-test-design/L7-scrum-to-discovery-rename-test-design.md`) |
| **② 実装コード** | `cli/helix-discovery` + shim | → ① 設計 §8 接続契約。→ ④ テストコード |
| **③ テスト設計** | `docs/v2/L7-test-design/L7-scrum-to-discovery-rename-test-design.md` | → ① 設計 (本 PLAN §5 DoD) |
| **④ テストコード** | `cli/lib/tests/test_helix_discovery_alias.py` + `cli/tests/helix-discovery.bats` | → ③ テスト設計 DoD D1-D10 |

**注記**: `docs/v2/L7-test-design/L7-scrum-to-discovery-rename-test-design.md` は Sprint .1 で別途起草する (generates に記載済み)。本 PLAN §6 のテスト仕様が同ファイルの雛型となる。

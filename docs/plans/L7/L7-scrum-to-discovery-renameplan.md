---
plan_id: L7-scrum-to-discovery-renameplan
title: "L7-scrum-to-discovery-renameplan (A1): helix-scrum → helix-discovery CLI/skill/doc alias + Stage 1 deprecated warning (backward compat Stage 1 のみ)"
kind: refactor
layer: L7
drive: be
status: draft
created: 2026-05-24
revised: "2026-05-24 (R2 revision: P0-1 state-path legacy / P1-1 docs/commands / P1-2 enum-contract / P1-3 4-property-test / P2-1 trace / P2-2 no-dollar-star / P2-3 env-form)"
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
    slot_label: "TL — CLI alias 設計・Stage 1 backward compat 設計妥当性検証 (R1 adversarial check)"
  - role: se
    slot_label: "SE — cli/helix-discovery 実装 (全 12 subcommand) + alias shim (全 12 subcommand) + doc 更新 + テスト"
  - role: pmo-sonnet
    slot_label: "PMO — doc 更新 整合チェック + 4 artifact 双方向 trace review"
generates:
  - artifact_path: cli/helix-discovery
    artifact_type: cli_extension
  - artifact_path: cli/helix-scrum (deprecated alias shim、Stage 1)
    artifact_type: cli_extension
  - artifact_path: docs/v2/L7-design/L7-scrum-to-discovery-rename-design.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L7-test-design/L7-scrum-to-discovery-rename-test-design.md
    artifact_type: design_doc
  - artifact_path: cli/lib/tests/test_helix_discovery_alias.py
    artifact_type: test
  - artifact_path: cli/tests/helix-discovery.bats
    artifact_type: test
dependencies:
  parent: L7-helix-workflows-parent-acceptedplan
  requires: []
  blocks:
    - L7-scrum-to-discovery-migration-enumplan
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
  - docs/commands/index.md (P1-1: Sprint .4 で discovery エントリ追加)
  - docs/commands/scrum.md (P1-1: alias doc として残存 + discovery.md への誘導注記追加)
  - docs/commands/discovery.md (P1-1: 新規作成 — Sprint .4 で実施)
  - "(本 PLAN は ADR-041/042/043 の影響範囲外: drift_type / recommended_command / Mode enum は本 PLAN scope に含まれない)"
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/discovery-workflow.md](../../../HELIX-workflows/helix-process/discovery-workflow.md)
> **本 PLAN (A1) の scope**: HELIX-workflows V2 完全移行で「Scrum (アジャイル)」と「Discovery (検証駆動)」が別概念に整理されたことに伴い、**CLI/skill/doc の外部表示名を alias で統一し、Stage 1 (deprecated warning あり alias) を実装する**。内部 symbol/DB table の rename は一切行わない (legacy 名維持)。
> **enum 契約 (P1-2 反映)**: 本 PLAN は `plan_validator.py` の `VALID_KINDS`/`VALID_DRIVES` を **変更しない**。`kind: discovery` の追加・`VALID_DRIVES` への discovery 追加・`kind: scrum` の warn-only 化は全て A2 scope。PLAN frontmatter の `kind:` は既存 enum 値 (`poc` 等) を使用し続ける。本 PLAN は **CLI/skill/doc alias のみ**を担う。
> **位置づけ**: SKILL_MAP.md §HELIX Scrum line 247 に「将来の rename は別 PLAN carry」として明記された carry を消化する PLAN (A1)。A1 完遂後に後段 PLAN A2 (`L7-scrum-to-discovery-migration-enumplan`) が runtime dir migration + drive/kind enum 正規化 + Stage 2-4 を担う。

> **A2 移管事項 (本 PLAN の scope 外)**:
> - runtime dir (`.helix/scrum/` → `.helix/discovery/`) migration、atomicity / manifest 検証 → **A2 scope**
> - `plan_validator.py` の `VALID_DRIVES`/`VALID_KINDS` 修正、`kind: discovery` 追加 → **A2 scope**
> - `HELIX_DISCOVERY_COMPAT_STAGE` env による Stage activation → **A2 scope**
> - Stage 2/3/4 の有効化・切替手順 → **A2 scope**
> - S0-S4 → D0-D4 state machine 分離 (DB layer) → **A2 scope**
> - `helix size`/`helix mode`/`current_mode`/`phase.yaml`/`command_mapper` の互換設計 → **A2 scope**
> - `L7-helix-scrum-removal-plan` stub 起票 → **A2 scope (A2 §10 carry)**

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

### 概念整理の前提 (A1 scope 内のみ)

| 旧名称 | A1 での扱い | 意味 |
|---|---|---|
| HELIX Scrum / `helix scrum` CLI | `helix scrum` → Stage 1 alias shim (warning あり)、`helix discovery` が正本 | 仮説検証・PoC・verify scripts による不確実性の潰し込み |
| `skills/agent-skills/helix-scrum/` | alias skill stub として維持 (削除しない)、`helix-discovery/` SKILL.md を新規作成 | 同上のスキル定義 |
| `.helix/scrum/` | **A1 では触れない**。migration は A2 scope | runtime state dir (backlog.yaml / sprint.yaml / verify/) |
| S0-S4 フェーズ記号 | doc 上は D0-D4 に更新 (SKILL.md 等)。DB state は legacy 名維持 | 段階名称 (Discovery フェーズ)。DB layer の分離は A2 scope |
| アジャイル Scrum (新概念) | 独立して Scrum ワークフロー — 本 PLAN の rename 対象とは別概念 | ユーザーと反復で要件を固める別モード |

**内部 symbol 維持 (A1 では rename しない)**:
- `cli/lib/scrum_local.py`、`scrum_trigger.py`、`scrum_to_reverse_routing.py`、`scrum_reverse_matrix.py` — 内部モジュール名は legacy 維持
- DB table: `scrum_trigger`、`scrum_local_loops` — table 名は legacy 維持
- `cli/helix-scrum` 内部変数 (`SCRUM_DIR` 等) — shim 内では legacy 変数名でよい (exec で転送するのみ)
- templates 配置パス、handoff path、dashboard/doctor/mode/size 内部参照 — A2 scope

---

## §1 工程表 (作業手順 + 進捗) — A1 scope

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 影響範囲 inventory 確定 (CLI 全 12 subcommand / skill / doc 件数) | PM | ✅ done (§3) |
| 2 | Stage 1 alias + warning 設計確定 | PM | ✅ done (§2) |
| 3 | CLI alias routing 契約確定 (全 12 subcommand) | PM | ✅ done (§8) |
| 4 | tl-advisor adversarial check R1 | PM → TL | ✅ done (needs_revision → revision 完了) |
| 5 | TL R1 指摘反映 (P0/P1 反映、scope 縮小) | PM | ✅ done (本 revision) |
| 6 | tl-advisor adversarial check R2 反映 (P0-1 / P1-1/-2/-3 / P2-1/-2/-3 全反映) | PM → PMO | ✅ done (本 revision) |
| 7 | SE 委譲: Sprint .2 CLI alias 実装 (`cli/helix-discovery` 全 12 subcommand + `cli/helix-scrum` shim) | PM → SE | □ pending |
| 8 | SE 委譲: Sprint .3 skill alias 対応 (`helix-discovery/` 新規 + `helix-scrum/` alias stub 維持) | PM → SE | □ pending |
| 9 | SE 委譲: Sprint .4 doc 更新 (CLAUDE.md / AGENTS.md / SKILL_MAP.md / HELIX_CORE.md / docs/agent-skills/README.md 等) | PM → SE | □ pending |
| 10 | bash -n / shellcheck 確認 (cli/helix-discovery + cli/helix-scrum shim) | SE | □ pending |
| 11 | pytest test_helix_discovery_alias.py + bats helix-discovery.bats 全 PASS | SE | □ pending |
| 12 | cli/helix router 登録 (discovery) + `helix help` + `helix commands check` (route/help/docs 三者同期確認) | SE | □ pending |
| 13 | pmo-sonnet で 4 artifact 双方向 trace 確認 + doc 更新整合チェック | PM → PMO | □ pending |
| 14 | commit + push | PM | □ pending |

---

## §2 設計判断: Stage 1 (Alias + Warning) — A1 scope

### Stage 1 の定義 (本 PLAN が担当する唯一の Stage)

```
Stage 1: Alias + Warning 段階 (本 PLAN 実装直後、default activation)
  - cli/helix-discovery が正本コマンドとして登録 (全 12 subcommand)
  - cli/helix-scrum は deprecated alias shim として残存 (全 12 subcommand を透過転送)
  - helix router に両方を登録 (discovery → helix-discovery、scrum → helix-scrum shim)
  - helix-scrum shim 実行時は stderr に deprecated warning を出力 (stdout を汚染しない)
  - exit code は helix-discovery の値を透過 (exec による)
  - ユーザーへの影響: なし (既存コマンドが動く)、warning のみ出力
  - HELIX_SUPPRESS_LEGACY_WARN=1 で warning を抑止可能
```

### Stage 2-4 は A2 scope

| Stage | 担当 PLAN | 内容 |
|---|---|---|
| Stage 1 (Alias + Warning) | **本 PLAN (A1)** | CLI/skill alias + deprecated warning (default 有効) |
| Stage 2 (Migration 提案) | **A2** (`L7-scrum-to-discovery-migration-enumplan`) | runtime dir migration 提案 + Stage activation 仕組み |
| Stage 3 (Auto-migrate) | **A2** | auto-migrate 実行 + atomicity 保全 |
| Stage 4 (Removal) | **`L7-helix-scrum-removal-plan`** (A2 §10 carry で stub 起票) | cli/helix-scrum 完全削除 |

**本 PLAN の DoD**: Stage 1 完了 (CLI alias 実装 + deprecated warning + doc 更新) のみ。

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
| `cli/helix-scrum` (1028 行) | → deprecated alias shim に縮小。先頭に warning 追加して `helix-discovery "$@"` に exec 転送 (全 12 subcommand 透過) | P1 |
| `cli/helix-discovery` (新規) | helix-scrum の内容をコピーして helix-discovery として作成。**外部表示名のみ変更** (内部 symbol は §0 内部 symbol 維持を参照) | P1 |
| `cli/helix` (router) | `discovery)` エントリを追加、`scrum)` を shim 経由で維持。`helix help` / `helix commands check` に `discovery` を追記 | P1 |

**現行 helix-scrum の全 12 subcommand** (全て helix-discovery + alias shim でカバー):

| subcommand | 説明 |
|---|---|
| `init` | Discovery ワークスペース初期化 |
| `backlog` | backlog 管理 (add / list 等) |
| `local` | local loop 管理 |
| `plan` | Sprint 計画 |
| `poc` | PoC 実装委譲 |
| `verify` | 検証スクリプト実行 |
| `decide` | 仮説確認/否定/pivot |
| `review` | レビュー |
| `status` | 現在状態表示 |
| `trigger` | trigger 管理 |
| `web-search` | Web 検索統合 |
| `acceptance-design` | 受入設計 |

**外部表示名の変更対象** (`cli/helix-discovery` 内で変更する箇所):

| 旧 | 新 |
|---|---|
| usage/help 表示 `helix scrum` | `helix discovery` |

> **重要 (P0-1 反映)**: `cli/helix-discovery` の **runtime state path は `.helix/scrum/` を引き続き使用する** (backward compat 維持)。`SCRUM_DIR`、`BACKLOG`、`SPRINT_FILE`、`SCRUM_VERIFY_DIR` 等の変数名・パス定義は変更しない。`.helix/discovery/` への切替・fallback・migration は A2 (`L7-scrum-to-discovery-migration-enumplan`) scope。A1 では外部表示名 (CLI usage / help 文字列 / skill doc / user-facing doc) のみ変更する。

**内部維持 (変更しない)**: `scrum_*` 変数名・関数名・内部 module import・DB table 名・runtime dir パス — 全て A2 scope

### 3.2 skill

| 対象 | 変更内容 | priority |
|---|---|---|
| `skills/agent-skills/helix-scrum/` | **削除しない**。Stage 1 では alias skill stub として維持 (SKILL.md に legacy note 追記) | P2 (削除は A2/removal PLAN) |
| `skills/agent-skills/helix-discovery/` (新規) | 新規ディレクトリ + SKILL.md を作成。`helix-scrum` が alias である旨を明記 | P1 |
| helix-discovery/SKILL.md name / description | `helix-discovery`、「Discovery モード」として定義 | P1 |
| helix-discovery/SKILL.md upstream | `cli/helix-discovery` | P1 |
| helix-discovery/SKILL.md helix_layer | `[D0, D1, D2, D3, D4]` | P1 |
| helix-scrum/SKILL.md | legacy note 追記: 「backward compat alias。`helix-discovery` を使用してください (L7-scrum-to-discovery-renameplan)」 | P1 |
| `docs/agent-skills/README.md` | `helix-scrum` 参照に legacy 注記追加 + `helix-discovery` エントリ追加 | P1 |

### 3.3 runtime dir — A2 移管

> **A1 では runtime dir を一切変更しない。** `.helix/scrum/` の migration は A2 (`L7-scrum-to-discovery-migration-enumplan`) が担当する。
> atomicity / manifest 検証 / lock / 再実行安全性の設計は A2 scope。
> **`cli/helix-discovery` は `.helix/scrum/` を runtime storage として使用する** (backward compat Stage 1)。`.helix/discovery/` への切替は A2 で実施する。A1 では `.helix/discovery/` に関する記述・実装を一切含まない。

### 3.4 doc 更新対象 (A1 scope で全件実施)

ユーザー向け doc (user-facing) と内部 reference を分類して更新する。

**user-facing doc (primary 更新対象)**:

| ファイル | 更新箇所 | 変更内容 |
|---|---|---|
| `CLAUDE.md` | §HELIX ワークフロー「helix scrum init」言及箇所 | `helix discovery init (旧: helix scrum init)` に更新 |
| `AGENTS.md` | Scrum 関連記述 | `Discovery (legacy: helix scrum)` 表記に更新 |
| `skills/SKILL_MAP.md` | §HELIX Scrum section (line 245-271) | section title を「§HELIX Discovery (旧: HELIX Scrum)」に変更、CLI コマンド例を `helix discovery` に更新、legacy 互換 note を保持。carry 明記「rename 完了 (L7-scrum-to-discovery-renameplan)」 |
| `helix/HELIX_CORE.md` | §状態管理の二層構造 `.helix/scrum/` 言及箇所 | `.helix/discovery/ (旧: .helix/scrum/)` 表記に更新 |
| `docs/agent-skills/README.md` | `helix-scrum` 参照箇所 | `helix-discovery` を正本として追加 + `helix-scrum` を legacy alias として注記 |
| `docs/commands/index.md` | コマンド一覧 | `discovery` エントリ追加 (P1-1 追加) |
| `docs/commands/scrum.md` | doc 全体 | alias doc として残存。冒頭に「**[DEPRECATED]** `helix scrum` は非推奨です。`helix discovery` を使用してください → `docs/commands/discovery.md` 参照」を追記 (P1-1 追加) |
| `docs/commands/discovery.md` | 新規作成 | `helix discovery` の正本コマンドリファレンス (全 12 subcommand 記載)。`helix scrum` は deprecated alias である旨を冒頭に明記 (P1-1 追加、Sprint .4 で作成) |

**内部 reference (accepted workflow / runtime doc — 更新対象)**:

| ファイル | 更新箇所 | 変更内容 |
|---|---|---|
| `HELIX-workflows/helix-process/db-integration.md` | scrum CLI 言及箇所 | `helix discovery (旧: helix scrum)` に更新 |
| `cli/lib/command_mapper.py` | `helix scrum` routing エントリ | `helix discovery` を正本エントリとして追加、`helix scrum` を alias エントリとして維持 |
| `cli/helix-mode` | scrum mode 言及箇所 | `discovery (旧: scrum)` 表記に更新 |
| `cli/helix-size` | `--uncertain → helix scrum init` 案内箇所 | `helix discovery init (旧: helix scrum init)` に更新 |
| `cli/helix-dashboard` | scrum mode 表示箇所 | `discovery (旧: scrum)` 表記に更新 |
| `cli/helix-doctor` | scrum 関連チェック箇所 | `discovery` チェック追加 (scrum alias チェックは legacy 維持) |

**legacy reference (is_reference: true 等 — 低優先、carry)**:

| ファイル | 対応方針 |
|---|---|
| `docs/design/L2-cli-architecture.md` | P3 carry (§10 Carry C2) |
| `docs/v2/V5-plan-outlines.md` | P3 carry (§10 Carry C3) |

### 3.5 PLAN kind enum — A2 移管

> **A1 では `plan_validator.py` の `VALID_KINDS`/`VALID_DRIVES` を変更しない。** `kind: discovery` 追加・`kind: scrum` warn-only 化・`VALID_DRIVES` 修正・`helix size`/`helix mode` 互換設計は全て A2 scope。
>
> 既存 PLAN の `kind: scrum` retrofit も A2 scope (調査結果: `grep -rn "kind: scrum" docs/plans/` で 0 件、Sprint .1 で最終確認)。

---

## §4 Sprint 分割 — A1 scope

### Sprint .1 — inventory 確認 + 設計確定

**目的**: 影響範囲の最終確定 (§3 の grep 確認)、接続契約の最終合意

**タスク**:
1. `grep -rn "helix scrum\|helix-scrum\|helix_scrum\|HELIX Scrum"` で全影響箇所を最終 grep (user-facing vs internal 分類)
2. `cli/helix-scrum` の全 subcommand 一覧を確定 (現行 12 件の最終確認)
3. doc 更新対象 §3.4 全件の grep で影響箇所を確定
4. tl-advisor R2 が必要な場合は本 PLAN revision 後に実施

**受入条件**: tl-advisor R1 needs_revision 反映完了 (本 revision で完了)。R2 が必要な場合は R2 `passed`

---

### Sprint .2 — CLI alias 実装 (全 12 subcommand)

**目的**: `cli/helix-discovery` 新規作成 (全 12 subcommand) + `cli/helix-scrum` → deprecated shim 変換 + helix router 登録

**実装手順**:
1. `cli/helix-scrum` を `cli/helix-discovery` にコピー
2. `cli/helix-discovery` の外部表示名を §3.1 変換表に従い置換 (dir パス変数・usage 表示、内部 symbol は維持)
3. `cli/helix-scrum` を deprecated alias shim に縮小 (全 12 subcommand を透過転送):

```bash
#!/bin/bash
# helix-scrum: DEPRECATED — 'helix discovery' を使用してください
# このファイルは backward compat (Stage 1) のために残されています
# Removal: L7-helix-scrum-removal-plan (A2 §10 carry で stub 起票) で削除予定
# HELIX_SUPPRESS_LEGACY_WARN=1 で warning を抑止できます

if [[ -z "${HELIX_SUPPRESS_LEGACY_WARN:-}" ]]; then
  >&2 printf '[DEPRECATED] '\''helix scrum'\'' は非推奨です。'\''helix discovery'\'' を使用してください。\n'
  >&2 printf '[DEPRECATED] removal: L7-helix-scrum-removal-plan を参照\n'
fi
exec "$(dirname "$0")/helix-discovery" "$@"
```

4. `cli/helix` router に `discovery)` エントリを追加:

```bash
# 既存 scrum エントリの後に追加
discovery)  exec "$SCRIPT_DIR/helix-discovery" "$@" ;;
```

5. `cli/helix` の help/usage にも `discovery` を追記
6. `helix commands check` で route/help/docs 三者同期を確認

**受入条件**:
- `bash -n cli/helix-discovery` PASS
- `shellcheck cli/helix-discovery` PASS (warnings 許容、errors 不可)
- 全 12 subcommand で `helix discovery <subcmd>` が正常動作する
- 全 12 subcommand で `helix scrum <subcmd>` が deprecated warning を stderr に出力した上で `helix discovery <subcmd>` と同等の stdout を返す
- `stdout not contains DEPRECATED` (stdout 汚染なし)
- `stderr contains DEPRECATED` (warning は stderr のみ)
- exit code が `helix discovery <subcmd>` と一致する

---

### Sprint .3 — skill alias 対応

**目的**: `skills/agent-skills/helix-discovery/` 新規作成 + `helix-scrum/` legacy note 追記 + docs/agent-skills/README.md 更新

**実装手順**:
1. `skills/agent-skills/helix-discovery/` ディレクトリ + SKILL.md を新規作成:
   - frontmatter `name:` を `helix-discovery`
   - frontmatter `description:` を Discovery モードの説明
   - frontmatter `helix_layer:` を `[D0, D1, D2, D3, D4]`
   - frontmatter `upstream:` を `cli/helix-discovery`
   - 本文の「HELIX Discovery (旧: HELIX Scrum / helix scrum)」として記述
   - legacy note: 「旧: helix-scrum (S0-S4)。backward compat alias は L7-scrum-to-discovery-renameplan §2 参照」を Overview 末尾に追記
2. `skills/agent-skills/helix-scrum/SKILL.md` に legacy note を追記 (**ディレクトリは削除しない**):
   - 先頭に「> **[DEPRECATED]** このスキルは backward compat alias です。`skills/agent-skills/helix-discovery/` を使用してください (L7-scrum-to-discovery-renameplan)。」を追記
3. `docs/agent-skills/README.md` に `helix-discovery` エントリを追加、`helix-scrum` を legacy alias として注記

**受入条件**:
- `skills/agent-skills/helix-discovery/SKILL.md` が存在する
- `skills/agent-skills/helix-scrum/` が存在する (削除しない)
- `helix-scrum/SKILL.md` に legacy note が追記されている
- `docs/agent-skills/README.md` に `helix-discovery` エントリが存在する

---

### Sprint .4 — doc 更新 (全件)

**目的**: §3.4 で定義した user-facing doc + 内部 reference の更新

**実装手順**:
1. `skills/SKILL_MAP.md` §HELIX Scrum section の更新:
   - section title: `### HELIX Scrum（検証駆動 / 要件未確定時）` → `### HELIX Discovery（検証駆動 / 要件未確定時、旧: HELIX Scrum）`
   - CLI コマンド例: `helix scrum init` → `helix discovery init (旧: helix scrum init)`
   - phase 記号: `S0` → `D0`、`S1` → `D1` ... `S4` → `D4`
   - carry 注記: 「将来の rename は別 PLAN carry」を「rename 完了 (L7-scrum-to-discovery-renameplan)」に更新
2. `helix/HELIX_CORE.md` の `.helix/scrum/` 参照を `.helix/discovery/ (旧: .helix/scrum/)` に更新
3. `CLAUDE.md` の `helix scrum init` コマンド例を `helix discovery init` に更新
4. `AGENTS.md` の Scrum 関連記述を `Discovery (legacy: helix scrum)` 表記に更新
5. `docs/agent-skills/README.md` 更新 (Sprint .3 で実施済の場合はスキップ)
6. `HELIX-workflows/helix-process/db-integration.md`、`cli/lib/command_mapper.py`、`cli/helix-mode`、`cli/helix-size`、`cli/helix-dashboard`、`cli/helix-doctor` の §3.4 内部 reference 更新

**受入条件**:
- `grep -rn "helix scrum init" CLAUDE.md AGENTS.md` が 0 件
- pmo-sonnet の doc 整合チェックが PASS
- `helix commands check` PASS (route/help/docs 三者同期)

---

### Sprint .5 — smoke test + 最終確認

**目的**: 全体 smoke test + helix doctor + 4 artifact 確認

**実装手順**:
1. smoke test:
   - 全 12 subcommand で `helix discovery <subcmd> --help` が正常動作
   - 全 12 subcommand で `helix scrum <subcmd> --help` が deprecated warning + 正常動作
   - `helix commands check` PASS (route/help/docs 三者同期)
   - `helix doctor` に新規 FAIL が出ないこと
2. pmo-sonnet で 4 artifact 双方向 trace 確認

**受入条件**:
- smoke test 全項目 PASS
- `helix doctor` の FAIL 件数が Sprint .1 開始前と同数以下
- pmo-sonnet 4 artifact trace PASS

---

## §5 DoD (Definition of Done) — A1 scope

以下を全て満たすこと:

| # | 条件 | 検証方法 |
|---|---|---|
| D1 | `helix discovery <subcommand>` が全 12 subcommand 正常動作 | bats helix-discovery.bats 全 PASS |
| D2 | `helix scrum <subcommand>` が deprecated warning を stderr に出力した上で `helix discovery <subcommand>` と同等動作 (全 12 subcommand)。具体的には: **stdout equality** (scrum stdout == discovery stdout)、**stderr contains DEPRECATED**、**stdout not contains DEPRECATED**、**exit code equality** の 4 property 全て成立すること (P1-3 反映) | bats helix-discovery.bats `_assert_alias_equivalence` helper で 12 subcommand × 4 property 全 PASS |
| D3 | `stdout not contains DEPRECATED` (stdout 汚染なし) かつ `stderr contains DEPRECATED` | bats run --separate-stderr 確認 |
| D4 | exit code が `helix discovery <subcmd>` と `helix scrum <subcmd>` で一致する | bats 確認 |
| D5 | `HELIX_SUPPRESS_LEGACY_WARN=1` 時に stderr warning が出力されない | bats 確認 |
| D6 | `skills/agent-skills/helix-discovery/SKILL.md` が存在し、内容が Discovery モードを示している | grep 確認 |
| D7 | `skills/agent-skills/helix-scrum/` が存在する (削除しない) かつ legacy note が追記されている | ls + grep 確認 |
| D8 | doc 更新 (CLAUDE.md / AGENTS.md / SKILL_MAP.md / HELIX_CORE.md 等 §3.4 全件) が完了 | pmo-sonnet review PASS |
| D9 | `helix doctor` の FAIL 件数が本 PLAN 実施前と同数以下 | `helix doctor` 実行確認 |
| D10 | `helix commands check` PASS (route/help/docs 三者同期) | `helix commands check` 実行確認 |
| D11 | tl-advisor R1 needs_revision 反映完了 (R2 が必要な場合は R2 `passed`) | tl-advisor 実行記録 |
| D12 | 4 artifact が別文書として存在し、双方向 reference が完備 | pmo-sonnet 4 artifact trace PASS |

> **automation-gate-map 適用範囲**: 本 CLI (helix discovery / helix scrum) は `gate-checks.yaml` の static チェック適用範囲外。Discovery モードは機械側だけで工程進行を完結できない除外モード (automation-gate-map.md より)。本 PLAN の DoD は workflow doc 固有の上記 D1-D12 で代替する。

---

## §6 受入条件と検証 — A1 scope

### bats テスト (`cli/tests/helix-discovery.bats`)

全 12 subcommand を対象にした alias 同等性テストと、stdout/stderr 分離テストを実施する。

```bash
# --- helix discovery 基本動作確認 (全 12 subcommand) ---
@test "helix discovery init が正常に動作する" { ... }
@test "helix discovery backlog add が動作する" { ... }
@test "helix discovery local が動作する" { ... }
@test "helix discovery plan が動作する" { ... }
@test "helix discovery poc が動作する" { ... }
@test "helix discovery verify が動作する" { ... }
@test "helix discovery decide が動作する" { ... }
@test "helix discovery review が動作する" { ... }
@test "helix discovery status が動作する" { ... }
@test "helix discovery trigger が動作する" { ... }
@test "helix discovery web-search が動作する" { ... }
@test "helix discovery acceptance-design が動作する" { ... }

# --- deprecated alias 確認 (全 12 subcommand × 4 property) ---
# P1-3 反映: 全 12 subcommand で以下 4 property を --separate-stderr で assertion する:
#   property 1: stdout == helix discovery <subcmd> stdout  (alias 同等性)
#   property 2: stderr contains DEPRECATED               (warning 出力確認)
#   property 3: stdout not contains DEPRECATED           (stdout 汚染なし)
#   property 4: exit code == helix discovery <subcmd> exit code (透過)

# helper: subcmd alias 同等性 + 4 property を一括検証
_assert_alias_equivalence() {
  local subcmd="$1"; shift
  # helix discovery の stdout / exit code を取得 (warning なし)
  run helix discovery "$subcmd" "$@"; local disc_out="$output"; local disc_status="$status"
  # helix scrum の stdout / stderr / exit code を取得
  run --separate-stderr env HELIX_SUPPRESS_LEGACY_WARN=0 helix scrum "$subcmd" "$@"
  # property 1: stdout 同等性
  [[ "$output" == "$disc_out" ]]
  # property 2: stderr に DEPRECATED
  [[ "$stderr" =~ "DEPRECATED" ]]
  # property 3: stdout に DEPRECATED なし
  [[ ! "$output" =~ "DEPRECATED" ]]
  # property 4: exit code 一致
  [[ "$status" -eq "$disc_status" ]]
}

@test "alias 4-property: helix scrum init" {
  _assert_alias_equivalence init --help
}
@test "alias 4-property: helix scrum backlog" {
  _assert_alias_equivalence backlog --help
}
@test "alias 4-property: helix scrum local" {
  _assert_alias_equivalence local --help
}
@test "alias 4-property: helix scrum plan" {
  _assert_alias_equivalence plan --help
}
@test "alias 4-property: helix scrum poc" {
  _assert_alias_equivalence poc --help
}
@test "alias 4-property: helix scrum verify" {
  _assert_alias_equivalence verify --help
}
@test "alias 4-property: helix scrum decide" {
  _assert_alias_equivalence decide --help
}
@test "alias 4-property: helix scrum review" {
  _assert_alias_equivalence review --help
}
@test "alias 4-property: helix scrum status" {
  _assert_alias_equivalence status --help
}
@test "alias 4-property: helix scrum trigger" {
  _assert_alias_equivalence trigger --help
}
@test "alias 4-property: helix scrum web-search" {
  _assert_alias_equivalence web-search --help
}
@test "alias 4-property: helix scrum acceptance-design" {
  _assert_alias_equivalence acceptance-design --help
}

# --- warning 抑止 (P2-3 反映: env 形式統一) ---
@test "HELIX_SUPPRESS_LEGACY_WARN=1 時に helix scrum は warning を出力しない" {
  run --separate-stderr env HELIX_SUPPRESS_LEGACY_WARN=1 helix scrum init --help
  [[ ! "$stderr" =~ "DEPRECATED" ]]
}

# --- alias 同等性 (stdout が helix discovery と一致する、HELIX_SUPPRESS_LEGACY_WARN=1 で warning 除外) ---
@test "helix scrum help と helix discovery help の stdout が一致する" {
  run helix discovery help; discovery_out="$output"
  run env HELIX_SUPPRESS_LEGACY_WARN=1 helix scrum help; scrum_out="$output"
  [[ "$discovery_out" == "$scrum_out" ]]
}
```

### pytest テスト (`cli/lib/tests/test_helix_discovery_alias.py`)

A1 scope では migration/plan_validator テストは含まない。

```python
def test_helix_discovery_script_exists():
    """cli/helix-discovery が存在し実行可能"""
    ...

def test_helix_scrum_shim_exists():
    """cli/helix-scrum が存在する (削除されていない)"""
    ...

def test_helix_scrum_shim_is_small():
    """cli/helix-scrum が deprecated shim (exec 転送のみ) に縮小されている"""
    # shim は exec helix-discovery を含む
    ...

def test_helix_discovery_skill_exists():
    """skills/agent-skills/helix-discovery/SKILL.md が存在する"""
    ...

def test_helix_scrum_skill_still_exists():
    """skills/agent-skills/helix-scrum/ が削除されていない"""
    ...

def test_helix_scrum_skill_has_legacy_note():
    """helix-scrum/SKILL.md に DEPRECATED 注記が含まれる"""
    ...
```

---

## §7 risk / mitigation — A1 scope

| リスク | 影響 | 可能性 | 緩和策 |
|---|---|---|---|
| R1: `helix-scrum/` skill ディレクトリを誤って削除する | HIGH | LOW | A1 では削除しない (§3.2 / Sprint .3 / DoD D7 で明示)。削除は A2/removal PLAN の DoD でのみ許可 |
| R2: alias 永続化リスク (removal が never になる) | MEDIUM | MEDIUM | `L7-helix-scrum-removal-plan` stub 起票を A2 §10 carry に明示。A2 の DoD に stub 起票を組み込む |
| R3: doc 更新漏れによる drift | MEDIUM | MEDIUM | pmo-sonnet review を Sprint .4/.5 の exit 条件に組み込む。`grep -rn "helix scrum init" CLAUDE.md AGENTS.md` で漏れ検出 |
| R4: helix-discovery の CLI 動作互換性劣化 | HIGH | LOW | 全 12 subcommand の alias 同等性を bats で固定。stdout not contains DEPRECATED を必須検証 |
| R5: stdout 汚染 (deprecated warning が stdout に混入) | HIGH | LOW | shim は `>&2 printf` で stderr のみに出力。bats で `--separate-stderr` を使い stdout/stderr を分離検証 |
| R6: doc 更新対象の漏れ (§3.4 内部 reference) | LOW | MEDIUM | Sprint .1 で `grep -rn "helix-scrum\|helix scrum"` の全 output を確認し §3.4 に追記 |
| R7: `helix commands check` の route/help/docs 不整合 | MEDIUM | LOW | Sprint .2/.5 で `helix commands check` を exit 条件に組み込む |

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

### signal_to_condition マッピング (旧 scrum 信号 → 新 discovery 実体) — Stage 1 のみ

| 旧信号 (入力) | 新実体 (出力) | Stage | 備考 |
|---|---|---|---|
| `helix scrum init` | `helix discovery init` + deprecated warning (stderr) | Stage 1 | 全 12 subcommand に適用 |
| `helix scrum backlog add` | `helix discovery backlog add` + deprecated warning | Stage 1 | |
| `helix scrum poc` | `helix discovery poc` + deprecated warning | Stage 1 | |
| `helix scrum verify` | `helix discovery verify` + deprecated warning | Stage 1 | |
| `helix scrum decide` | `helix discovery decide` + deprecated warning | Stage 1 | |
| `helix scrum local` | `helix discovery local` + deprecated warning | Stage 1 | |
| `helix scrum plan` | `helix discovery plan` + deprecated warning | Stage 1 | |
| `helix scrum review` | `helix discovery review` + deprecated warning | Stage 1 | |
| `helix scrum status` | `helix discovery status` + deprecated warning | Stage 1 | |
| `helix scrum trigger` | `helix discovery trigger` + deprecated warning | Stage 1 | |
| `helix scrum web-search` | `helix discovery web-search` + deprecated warning | Stage 1 | |
| `helix scrum acceptance-design` | `helix discovery acceptance-design` + deprecated warning | Stage 1 | |
| `helix size --uncertain` | `helix discovery init` を案内 (旧: `helix scrum init`) | Stage 1 以降 | cli/helix-size の doc update |

> **Stage 2/3 の migrate 提案・auto-migrate は A2 scope。** A1 では `.helix/scrum/` 存在チェックを行わない。

### runtime dir — A1 scope の扱い

> **P0-1 反映**: A1 では `cli/helix-discovery` の runtime storage path を **`.helix/scrum/` のまま維持する**。`helix discovery` コマンドが参照するデータは `.helix/scrum/` に置かれ続けるため、既存ユーザーへの影響はない。`.helix/discovery/` への切替・fallback・drive enum 追加は A2 scope。runtime dir 解決ロジック (fallback / migration 提案 / auto-migrate) は A2 scope。

### deprecated shim の実装契約

```bash
# cli/helix-scrum (deprecated shim)
# - exec で helix-discovery に転送することで、exit code も含めて透過
# - "$@" を変更せずに転送 (サブコマンド・引数はそのまま)
# - stderr に warning を出力 (stdout を汚染しない)
# - warning は 1 回のみ (loop しない)
# - "$*" を warning message に含めない (引数の log 化を避ける — P2-2 反映)
>&2 printf '[DEPRECATED] helix scrum は非推奨です。'\''helix discovery'\'' を使用してください。\n'
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
| `HELIX-workflows/helix-process/db-integration.md` | scrum CLI 言及 — Sprint .4 で更新 |
| `skills/SKILL_MAP.md` §HELIX Scrum (line 245-271) | carry 根拠の記載箇所 — Sprint .4 で更新 |
| `skills/agent-skills/helix-scrum/SKILL.md` | alias skill stub として維持 (legacy note 追記対象) |
| `cli/helix-scrum` | deprecated alias shim 化対象 |
| `cli/lib/command_mapper.py` | `helix scrum` routing エントリ — Sprint .4 で更新 |
| `cli/helix-mode` / `cli/helix-size` / `cli/helix-dashboard` / `cli/helix-doctor` | 内部 reference — Sprint .4 で更新 |
| `docs/agent-skills/README.md` | `helix-scrum` 参照箇所 — Sprint .3/.4 で更新 |
| `docs/design/L2-cli-architecture.md` | `helix scrum` 記述 — P3 carry (§10 Carry C2) |
| `docs/v2/V5-plan-outlines.md` | `helix scrum` 参照 — P3 carry (§10 Carry C3) |
| `docs/commands/index.md` | コマンド一覧 — Sprint .4 で `discovery` エントリ追加 (P1-1) |
| `docs/commands/scrum.md` | alias doc として残存 — Sprint .4 で deprecated 誘導注記追加 (P1-1) |
| `docs/commands/discovery.md` | 新規作成 — Sprint .4 で `helix discovery` 正本リファレンス作成 (P1-1) |

> **ADR scope 外の明示**: 本 PLAN (A1) は **ADR-041/042/043 の影響範囲外** である。ADR-041/042/043 が扱う `drift_type`・`recommended_command`・`Mode enum` (route_engine 関連) は本 PLAN scope に含まれない。

### 関連 PLAN

| PLAN | 関係 |
|---|---|
| `L7-helix-workflows-parent-acceptedplan` | parent (HELIX-workflows 正本化の親 PLAN) |
| `L7-scrum-to-discovery-migration-enumplan` (A2) | 本 PLAN が blocks (A1 完遂後に起動)。runtime dir migration + drive/kind enum + Stage 2-4 を担う |
| `L7-helix-scrum-removal-plan` (未起票) | Stage 4 Removal 実施 PLAN。A2 §10 carry で stub 起票 |

---

## §10 carry / 残課題 — A1 scope

### Carry C1 (P1 — A2 scope、`L7-scrum-to-discovery-migration-enumplan` §10 carry として移管済)

**A2 移管事項**: runtime dir migration / drive・kind enum 正規化 / Stage activation / S0-S4→D0-D4 state machine 分離 / `L7-helix-scrum-removal-plan` stub 起票は全て A2 PLAN が担当する。A1 完遂後に A2 を起動すること。

**tl-advisor 指摘 → A2 該当節 trace (P2-1 反映)**:

| tl-advisor 指摘 ID | 指摘内容 | A2 対応節 |
|---|---|---|
| R1-P0: runtime dir 切替が Stage 1 backward compat を破壊 | A1 で `.helix/discovery/` を使い始める設計 → A1 は `.helix/scrum/` 維持に変更 | A2 §3.3 runtime dir migration |
| R2-P0-1 (本 revision で解消) | A1 §3.1 / §8 の `.helix/discovery/` 記述削除 → 解消済 | — |
| R1-P1: drive enum 不整合 | A1 に `kind: discovery` / VALID_DRIVES 追加あり → A1 からは削除、A2 へ移管 | A2 §3.5 PLAN kind enum |
| R2-P1-2 (本 revision で解消) | A2 の enum 契約説明 (VALID_KINDS 変更しない) に統一 → 解消済 | — |
| R2-P1-3 (本 revision で解消) | alias 同等性テスト 4 property × 12 subcommand 強化 → §6 / DoD D2 に反映済 | — |

**state path migration は A2 carry** (`L7-scrum-to-discovery-migration-enumplan` §3.3 runtime dir migration が担当)。

### Carry C2 (P3 — 任意)

`docs/design/L2-cli-architecture.md` の `helix scrum` 記述 (line 89, 281) を `helix discovery` に更新する。is_reference の V1 doc であるため低優先。

### Carry C3 (P3 — 任意)

`docs/v2/V5-plan-outlines.md` の `helix scrum` 参照 (複数箇所) を更新する。is_reference の docs であるため低優先。

### Carry C4 (P2 — A1 commit 後に実施)

`HELIX-workflows/helix-process/integration-map.md` の「コマンドの穴」リスト更新。`helix-discovery` が正式コマンドとして登録済みであることを反映する。更新箇所: integration-map.md §コマンドの穴 (または相当 section) に `helix-scrum → helix-discovery rename 完了 (L7-scrum-to-discovery-renameplan)` を記載する。

---

## §11 4 artifact 双方向 trace

本 PLAN では 4 artifact を別文書として分離し、双方向 reference を完備する。

| Artifact | ファイル | artifact_type | trace 先 |
|---|---|---|---|
| **① 設計** | `docs/v2/L7-design/L7-scrum-to-discovery-rename-design.md` | design_doc | → ③ テスト設計。→ ② 実装コード |
| **② 実装コード** | `cli/helix-discovery` + `cli/helix-scrum` shim | cli_extension | → ① 設計 §8 接続契約。→ ④ テストコード |
| **③ テスト設計** | `docs/v2/L7-test-design/L7-scrum-to-discovery-rename-test-design.md` | design_doc | → ① 設計 §5 DoD。→ ④ テストコード |
| **④ テストコード** | `cli/lib/tests/test_helix_discovery_alias.py` + `cli/tests/helix-discovery.bats` | test | → ③ テスト設計 DoD D1-D12 |

**本 PLAN (設計 PLAN) と ① 設計の関係**: 本 PLAN §2/§3/§8 が設計 doc の雛型となる。Sprint .2 着手前に `docs/v2/L7-design/L7-scrum-to-discovery-rename-design.md` を別途起草し、本 PLAN から参照する。

**③ テスト設計の起草タイミング**: Sprint .2 着手前に `docs/v2/L7-test-design/L7-scrum-to-discovery-rename-test-design.md` を起草する (generates に記載済み)。本 PLAN §6 のテスト仕様が同ファイルの雛型となる。

**双方向 reference ルール**:
- ① 設計 doc には「テスト設計: docs/v2/L7-test-design/L7-scrum-to-discovery-rename-test-design.md」を明示
- ② 実装コード (cli/helix-discovery) の docstring/header には「契約: docs/v2/L7-design/L7-scrum-to-discovery-rename-design.md §接続契約」を明示
- ③ テスト設計には「対象設計: docs/v2/L7-design/L7-scrum-to-discovery-rename-design.md」を明示
- ④ テストコードの docstring には「DoD 検証: L7-scrum-to-discovery-rename-test-design.md D1-D12」を明示

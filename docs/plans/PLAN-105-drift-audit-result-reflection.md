---
plan_id: PLAN-105
title: "drift audit 結果反映 (CLAUDE.md / SKILL_MAP / HELIX_CORE / CODEX_TL_MODE)"
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
kind: retrofit
drive: be
layer: cross
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (claude-sonnet-4-6)
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — drift finding 抽出・4 doc 変更箇所特定・Edit 実施"
  - role: pm-advisor
    slot_label: "PM — P0 変更承認・破壊的変更フラグ確認"
generates:
  - artifact_type: doc_update
    path: CLAUDE.md
  - artifact_type: doc_update
    path: skills/SKILL_MAP.md
  - artifact_type: doc_update
    path: helix/HELIX_CORE.md
  - artifact_type: doc_update
    path: helix/CODEX_TL_MODE.md
  - artifact_type: doc_update
    path: docs/commands/index.md
dependencies:
  requires:
    - PLAN-100
  blocks: []
  parent: null
related_adr: []
related_docs:
  - CLAUDE.md §subagent 工程マッピング
  - CLAUDE.md §セッション開始チェック
  - skills/SKILL_MAP.md §自動推挙システム
  - helix/HELIX_CORE.md §工程別 subagent 起動マップ
  - docs/commands/index.md
acceptance_criteria:
  - "helix agent slots release / release-stale subcommand が CLAUDE.md §コマンド / SKILL_MAP §自動推挙システム / docs/commands/index.md に記載されている"
  - "helix agent top-level router 登録 (commit 90b4a4d) が CLAUDE.md / docs/commands/index.md に反映されている"
  - "SessionStart hook 案内 3 段階構成 (commit e3c658d) が HELIX_CORE.md / CLAUDE.md 相当箇所に反映されている"
  - "PLAN-100 status: complete が CLAUDE.md §次 session 最優先 carry の carry 記述から除外されている"
  - "4 doc の drift finding P0/P1 全件が反映され、helix doctor warn 数が増加していない"
  - "4 doc それぞれのセルフレビューが実施され、enum 違反 / broken reference がない"
---

# PLAN-105: drift audit 結果反映 (CLAUDE.md / SKILL_MAP / HELIX_CORE / CODEX_TL_MODE)

## L2 凍結 (ADR snapshot)

本 PLAN は **既存 doc への実装反映 (retrofit)** であり、新規アーキテクチャ採用を含まない。L2 大局判断なし、ADR snapshot 不要。

## 背景

2026-05-23 session (commits 90b4a4d / 898295e / 0d5eb6a / e3c658d / 9cca9bc) で複数の実装変更が landing したが、CLAUDE.md / SKILL_MAP.md / HELIX_CORE.md / CODEX_TL_MODE.md / docs/commands/index.md への drift 反映が未実施。

本 PLAN は landing 済み実装の **doc 追いつき** として 4 doc + index.md を対象に drift を解消する。

## WebSearch 履歴

本 PLAN は既存 doc への実装反映 (retrofit) が目的であり、外部新仕様採用を含まない。PLAN-087 ガードレール判定: WebSearch 3 query 不要 (設計 doc ではなく doc 反映文書)。

## drift finding 一覧

### 1. CLAUDE.md

| Finding ID | P 区分 | 対象箇所 | 現状 | 是正内容 |
|---|---|---|---|---|
| D-CLAUDE-01 | P1 | §コマンド / agent コマンド一覧 | `helix agent` コマンドが subagent 工程マッピングとして記載されているが、`slots release` / `slots release-stale` subcommand の追加 (commit 898295e) が未記載 | `helix agent slots release [SLOT_ID]` / `helix agent slots release-stale` を記載追加 |
| D-CLAUDE-02 | P1 | §コマンド / docs/commands/index.md 参照 | `helix agent` の top-level router 登録 (commit 90b4a4d) 後の subcommand 一覧が現行 docs/commands/index.md と不整合の可能性 | docs/commands/index.md と CLAUDE.md の helix agent 記述を整合 |
| D-CLAUDE-03 | P1 | §セッション開始チェック (または SessionStart 言及箇所) | SessionStart hook の案内メッセージ 3 段階構成 (commit e3c658d: helix agent slots release-stale 二段化) が CLAUDE.md に未記載 | commit e3c658d の変更内容を CLAUDE.md の SessionStart 関連記述に反映 |
| D-CLAUDE-04 | P2 | §次 session 最優先 carry | PLAN-100 が 2026-05-23 session で status: complete になった (commit 9cca9bc) が、carry 記述に残存している可能性 | PLAN-100 完遂を明示、carry から除外 |
| D-CLAUDE-05 | P3 | §V5 framework 9 PLAN 起票案 | PLAN-103 / PLAN-105 (本 PLAN) 起票が反映されていない | 起票済みとして PLAN 一覧を更新 |

### 2. skills/SKILL_MAP.md

| Finding ID | P 区分 | 対象箇所 | 現状 | 是正内容 |
|---|---|---|---|---|
| D-SKILL-01 | P1 | §自動推挙システム (コマンド一覧) | `helix agent` 系の CLI 一覧に `slots release` / `slots release-stale` が未記載 | コマンド一覧に 2 subcommand 追記 |
| D-SKILL-02 | P2 | §工程別 subagent 起動マップ (要点) | `helix agent fire-mandatory --phase Lx` の記述はあるが、slots 管理 subcommand が欠落 | slots 管理コマンドへの簡易言及追加 |
| D-SKILL-03 | P3 | §PLAN 参考正本 | PLAN-103 / PLAN-105 が起票されたが一覧に未記載 (SKILL_MAP は PLAN 一覧の exhaustive list を目的としないため P3) | 必要に応じて追記 |

### 3. helix/HELIX_CORE.md

| Finding ID | P 区分 | 対象箇所 | 現状 | 是正内容 |
|---|---|---|---|---|
| D-CORE-01 | P1 | §工程別 subagent 起動マップ | CLI 欄に `helix agent fire-mandatory --phase Lx` / `helix agent suggest --task "..."` が記載されているが、`helix agent slots release-stale` (stale slot 管理) が欠落 | Sprint Plan 標準構造などの slot 管理文脈で release-stale を言及追加 |
| D-CORE-02 | P2 | §Sprint Plan 標準構造 Step 7 (commit + carry note) | stale slot の自動 release が SessionStart hook に組み込まれた (commit e3c658d) が、Sprint 手順に記載なし | commit 後の stale slot 確認 / release を Step 7 or Step 8 に追記 (任意注記レベル) |
| D-CORE-03 | P3 | §状態管理の二層構造 | helix.db の table 一覧が PLAN-091/092/099 実装後の schema と drift している可能性 | 別途 helix.db schema audit 実施後に反映 (本 PLAN スコープ外、P3 として記録) |

### 4. helix/CODEX_TL_MODE.md

| Finding ID | P 区分 | 対象箇所 | 現状 | 是正内容 |
|---|---|---|---|---|
| D-TL-01 | P2 | §委譲・コマンド利用ゲート | Codex TL の利用可能コマンド一覧に `helix agent slots release-stale` が未記載 | sprint 完了後の stale slot cleanup として追記 (sprint workflow のクリーンアップ手順) |
| D-TL-02 | P3 | §Codex 非交渉ルール | PLAN-100 完遂後の進捗状況を反映する必要がある場合、参照 PLAN 番号を更新 | PLAN-100 完遂を確認した場合のみ記述更新 |

### 5. docs/commands/index.md

| Finding ID | P 区分 | 対象箇所 | 現状 | 是正内容 |
|---|---|---|---|---|
| D-IDX-01 | P1 | helix agent row | `helix agent` の description が "agent slot 一覧/release/stats/fire-mandatory/audit (PLAN-082)" で、commit 90b4a4d で top-level router 登録した新 subcommand (`slots release` / `slots release-stale`) が欠落 | description を現行 8 subcommand (fire/release/slots/stats/fire-mandatory/suggest/audit + release-stale) に更新 |

## 実装 Sprint 構成

| Sprint | 内容 | 対象ファイル | role | 想定 size |
|---|---|---|---|---|
| Sprint .1 | P0/P1 finding 抽出 + 変更箇所確認 (Read 専用) | 4 doc + index.md | pmo-sonnet | XS |
| Sprint .2 | CLAUDE.md D-CLAUDE-01/02/03 反映 | CLAUDE.md | pmo-sonnet | S |
| Sprint .3 | SKILL_MAP.md D-SKILL-01 反映 + docs/commands/index.md D-IDX-01 反映 | SKILL_MAP.md + index.md | pmo-sonnet | S |
| Sprint .4 | HELIX_CORE.md D-CORE-01 + CODEX_TL_MODE.md D-TL-01 反映 | HELIX_CORE.md + CODEX_TL_MODE.md | pmo-sonnet | S |

### Sprint Exit 条件 (mandatory in sprint)

- 各 sprint で変更対象ファイルを Edit 前に Read
- Edit 後にセルフレビュー (enum 違反 / broken reference / markdown linter 相当)
- Sprint .4 完了後に `helix doctor` 実行し warn 数が増加していないことを確認

## DoD (Definition of Done)

- [ ] D-CLAUDE-01/02/03 が CLAUDE.md に反映
- [ ] D-SKILL-01 が SKILL_MAP.md に反映
- [ ] D-IDX-01 が docs/commands/index.md に反映
- [ ] D-CORE-01 が HELIX_CORE.md に反映
- [ ] D-TL-01 が CODEX_TL_MODE.md に反映
- [ ] P2/P3 finding は carry 記録またはスキップ判断を本 PLAN の carry section に明記
- [ ] 各 doc に markdown syntax エラーなし
- [ ] `helix doctor` warn 数が本 PLAN 着手前と比較して増加していない
- [ ] 本 PLAN frontmatter が `helix plan lint --v5` PASS

## carry / 学び

- **D-CORE-03 (helix.db schema drift)**: 別途 helix.db schema audit が必要。本 PLAN スコープ外として次 session carry に格上げ候補
- **CLAUDE.md の肥大化**: 現行 CLAUDE.md は 400 行超。drift 反映を続けると FR-V5-MK02 (Progressive disclosure) の必要性が増す。本 PLAN 完了後に肥大化状況を reporting する
- **drift 再発防止**: 今後は各実装 commit の PR description に「doc drift 対象: CLAUDE.md §XX」を明記する運用が有効 (PLAN-096 GitHub Actions workflow で自動チェック候補)

## 関連 reference

- commit 90b4a4d: feat(helix-cli): helix agent CLI を top-level router に登録 + docs 整合
- commit 898295e: feat(helix-agent): slots に release / release-stale subcommand 追加
- commit 0d5eb6a: fix(pytest-infra): conftest.py 追加で collection stop 偽 fail 解消
- commit e3c658d: chore(harness-cleanup): datetime.utcnow() 非推奨修正 + SessionStart hook 案内拡張
- commit 9cca9bc: docs(plan-100): status draft → complete + §14 完遂記録
- [[feedback_merge_settings_helix_hook_judge_bug]] (PLAN-103 / drift 再発パターン例)
- PLAN-100 (完遂済み retrofit、本 PLAN の carry 解消 baseline)
- PLAN-096 (GitHub Actions、drift 防止自動化の将来接続先)

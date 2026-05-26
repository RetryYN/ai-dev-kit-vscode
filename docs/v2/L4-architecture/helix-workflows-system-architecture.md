---
doc_id: l4-helix-workflows-system-architecture
title: "HELIX-workflows V2 方式設計 (system architecture)"
status: skeleton
created: 2026-05-27
owner: PM
process_layer: L4
parent_plan: L4-helix-workflows-方式設計plan
pairs_test_design: docs/v2/L9-test-design/helix-workflows-system-test-design.md
adr_snapshot: docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
industry_standards:
  - IEEE 42010:2022 (architecture description)
  - arc42 template
  - C4 model
related_l3_plans:
  - docs/plans/L3/L3-helix-workflows-業務要件plan.md
  - docs/plans/L3/L3-helix-workflows-機能要件plan.md
  - docs/plans/L3/L3-helix-workflows-非機能要件plan.md
---

# HELIX-workflows V2 方式設計 (system architecture)

## §0 概要

HELIX-workflows V2 dogfooding の L4 方式設計は、L3 の確定要件を 4 つの観点（工程、永続化、監査、pairing）で実装可能な設計断面へ落とし込むことを目的とします。L3 入力は実装判断より先にアーキテクチャ制約へ変換し、L9 テスト設計へ逆流可能な形で固定します。

本セクションでは、scope、pairing、業界標準整合（IEEE 42010 / arc42 / C4）を明文化し、Plan + ADR + Test 設計の 3 文書同時起票を前提にします。

## §1 システム構成

### 1.1 HELIX ワークフロー全体構造

HELIX-workflows は以下の 3 層で成立します。

| 層 | 役割 | 監査対象 |
|---|---|---|
| HELIX-workflows/ layer | 基本規約、mode/phase ルール、plan と audit の正本 | 規約変更履歴 |
| cli/ layer | bash/Python 実装、recommend/doctor/context、hooks と CLI entrypoint | 起動 trace と実行結果 |
| skills/ layer | 設計・レビューの知識資産、role 参照、外部調査の正本 | skill 設定の整合 |

### 1.2 永続化 4 種（本体化対象）

1. `helix.db`（SQLite）: PLAN/実行履歴、mode遷移、監査ログ。
2. `.helix/audit/*.yaml`: 実行証跡、失敗 trace、review evidence。
3. `git history`: 監査ログ不変性、変更追跡（ID 増分・diff）。
4. `.helix/handover/`: 受け渡しと ownership。

### 1.3 Git hook 配線

本設計では以下の hook が方式設計と監査を接続します。

| Hook | 役割 | 起点 |
|---|---|---|
| pre-commit | fast lint/doctor 基本検査（0.5-2s） | ローカル開発体験維持 |
| pre-push | CI 判定の軽量ゲート補助 | 追加の失敗早期検知 |
| SessionStart / PreCompact / UserPromptSubmit | コンテキスト注入・履歴圧縮・手動監査通知 | セッション回遊 |

L4では hook の fast/CI split を Step 2-3 で本文化し、`help` / `doctor` / `changeprop` の呼出し順を明文化します。

## §2 アーキテクチャ

### 2.1 PLAN ⊃ ADR レイヤー併存

PLAN は実装計画である一方、L2 の大局設計を越える意思決定は ADR snapshot で凍結し、同時に plan_validator の pairing 判定を経て trace します。L4 では本 PLAN を起点に ADR を同時起票することで、後追い freeze を回避します。

### 2.2 V-model 4 artifact 双方向 trace

V-model は設計⇔テスト設計、実装⇔テストコードの 2 対 2 で維持し、L4-L9 は設計・総合テストで pair します。L4 の方式設計は L9 総合テスト設計への `pairs_test_design` を固定し、逆方向 trace を ST-*.table で戻します。

### 2.3 工程の左右腕構造

L0-L14 左右 4 対 4 の接続として、L4 は L9 へ、L7 は L8 と連携しつつ、各工程が 2 方向の trace を持つことを前提にします。工程外れは L4 carry で切断不能な状態として扱います。

### 2.4 9 mode → Forward 回帰

9 mode 入口は discovery/research/recovery の判定を経て、最終的に Forward の L1-L9-L14 経路へ収束します。mode closure は `helix.db.mode_transition` のイベントとして永続化し、pair freeze の再実行に耐える構造とします。

## §3 技術スタック

### 3.1 CLI / 実装基盤

- **Python 3** (`cli/lib/`): doctor / db / plan validator / catalog 構築。
- **Bash** (`cli/`): 主要 entrypoint と hook 実装。
- **SQLite** (`helix.db`): 変更 trace と状態遷移の正規レイヤ。

### 3.2 監査・実行基盤

- **Git hooks**: pre-commit / pre-push / session events。
- **GitHub Actions**: CI-only lint/test/doctor の慢性監視。
- **Codex CLI + Claude Code subagent**: pm/ tl / pmo / doc-reviewer / advisors。
- **許可モデル**: PMO Sonnet/Haiku + PdM Opus 系 12 種 role を必要時起動（実行と監査を分離）。

## §4 BR-12 ratchet 機構の方式

### 4.1 baseline と update policy

`balance-ratio-baseline.yaml` を起点に `changeprop` 前提の最低値を管理し、`check_balance_ratio_regression` / `check_upstream_downstream_alignment` / `check_id_reference_completeness` を ratchet 条件で常時確認します。新規追加 ID は下流反映と同一 commit または近傍 commit 内で吸収します。

### 4.2 機能分離

`helix doctor --check-changeprop` (read-only) は検査専用で実行し、`--check-changeprop --update` (write) は baseline 更新の独立 path で実行します。これにより pre-commit fast lane と CI deep check を分離し、ローカル速度と統治精度を両立します。表記は `--check-changeprop` で統一し、L3/L12/L14 の旧表記 `check_changeprop` は retrofit carry として PLAN §4.2 P1-A3 で扱います。

### 4.3 hook 分割

- pre-commit: fast check（0.5-2 秒）
- CI: deep check（20-120 秒、失敗時 fail-close）
- 違反は `.helix/audit/changeprop-violations.yaml` に時系列保存し、再試行基準を保持

## §5 mandatory subagent 起動方式

### 5.1 entry hook と制御表

L3-L9 各工程の entry hook は `vmodel-semantics.yaml` を参照し、mandatory subagent を明示します。`agent_slots` は PLAN frontmatter と対応し、起動漏れは audit carry として扱います。

| 分類 | subagent | 起動契機 |
|---|---|---|
| `mandatory_by_phase` | pmo-sonnet / pmo-helix-explorer / pmo-project-explorer / doc-reviewer | 工程 entry で必須発火 (`helix agent fire-mandatory --phase Lx`) |
| `on_demand` | pm-advisor / tl-advisor / pmo-haiku / pmo-tech-news | PM/TL 判断時に任意召喚 (大局判断 / adversarial check / 軽 web 検索) |

`agent_slots` frontmatter には両カテゴリ混在可とし、`mandatory_by_phase` 不在は G2/G4 audit で fail-close、`on_demand` 不在は advisory note 扱い。詳細 mapping は Step 2 で `vmodel-semantics.yaml` schema 表として本体化します。

### 5.2 実行プロトコル

1. `helix agent fire-mandatory --phase Lx` を起点に mandatory を起動。
2. `helix.db` の helix event log に実行証跡を保存。
3. 返却 evidence を PLAN 本体（carry note）へ反映。

### 5.3 監査連動

subagent 起動は `helix.db` と `.helix/audit/*.yaml` の双方向参照で同一ソース化し、召喚証跡が欠けないことを DoD に含めます。

## §6 二重/三重 audit pattern の方式

### 6.1 監査レイヤ構成

TL / PMO / doc-reviewer の 3 重監査を採用し、adversarial check・整合監査・文書品質監査を分離します。必要時に rollout JSONL bypass を使い、要約損失を回避します。

### 6.2 監査 evidence フロー

`doc-review evidence` と `audit trace` を交差チェックし、欠落時は Step 6 を pending 停止します。

## §7 採用 project への配布

### 7.1 配布範囲

`helix init` で `.helix/` / `CLAUDE.md` / `.gitignore` を採用 project へ配布し、必要最小限でドッグフーディング起動できる状態を作ります。`docs/v2/` の要件設計は project 側採用に合わせてシンボリック参照にします。

### 7.2 配布後の更新方針

portable package 化し、更新時は Plan/ADR を再解釈して採用 project 側へ反映します。運用負荷は hook split と監査証跡で吸収します。

### 7.3 既存資産整理 / 移行経路の取り込み (BR-09 / BR-10 carry)

採用 project 配布は **BR-09 (既存資産整理)** と **BR-10 (Strangler Fig 移行経路)** を内包します。本 skeleton では明示ラベルのみ宣言し、本体化は Step 2-3 で実施します:

- **BR-09 既存資産整理**: HELIX-workflows portable package に同梱する対象 (`HELIX-workflows/` 正本 doc + `cli/` 主要 entrypoint + `skills/` 必須 skill) と除外対象 (`.helix/audit/*` 等の runtime state) の manifest 化。
- **BR-10 Strangler Fig 移行**: 採用 project 既存 framework と HELIX-workflows の段階的並走 → 切替 → 旧 framework 廃止の 3-stage migration path、各 stage の rollback 条件と完了 evidence。

## §8 残課題 (skeleton 段階)

以下は本 skeleton の carry note です。`SECTION` ごとに Step 2-3 で本体化を行う (詳細は [L4 PLAN §4.2/§4.3](../../plans/L4/L4-helix-workflows-方式設計plan.md) を参照)。

### §8.1 構造的 carry (Step 2-3 で本体化)

- **§0 / §1**: 3 層構成について、既存ドキュメント（PLAN/ADR/技能）との重複削除ルール追加 + IEEE 42010 viewpoint / arc42 12 章 / C4 4 階層 への対応表 (P1-A7)。
- **§1-§7**: 各 § に対応 ST-ID / 観測コマンド / evidence path 表を追加 (P1-A2、L4→L9 双方向 trace 強化)。
- **§4.4**: baseline path / source / update policy の SSoT 確定 (P1-A3、L3/L12/L14 横断 retrofit と統合)。
- **§5.2**: `vmodel-semantics.yaml` と mandatory skill map の完全 schema を table 化 (P1-A5 と統合)。
- **§6.3**: doc-reviewer evidence YAML schema (fields / retention / helix.db key / 欠落時 fail 条件) を明文化 (P1-A5)。

### §8.2 実在主張表 retrofit (BR-RULE-09 違反対応、Step 2 必須)

本 doc が CLI / file / schema を主張する箇所 (§1.3 hook 表 / §3 技術スタック表 / §4.2 CLI コマンド / §5.1 subagent 表 / §7.1 配布範囲) には **`implementation_status` 列** を追加し、実装済 / 設計のみ / carry を機械検出可能にする (P1-A8、BR-RULE-09)。

### §8.3 採用 project 配布 carry

- **BR-09**: portable package manifest 化 (§7.3 で明示ラベル済、本体化は Step 2)。
- **BR-10**: Strangler Fig 3-stage migration path (§7.3 で明示ラベル済、本体化は Step 2)。

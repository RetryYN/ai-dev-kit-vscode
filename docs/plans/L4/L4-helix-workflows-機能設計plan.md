---
plan_id: L4-helix-workflows-機能設計plan
title: "L4-helix-workflows-機能設計plan: HELIX-workflows V2 機能設計 (skeleton)"
kind: design
layer: L4
drive: be
status: draft
created: 2026-05-27
owner: PM
process_layer: L4
parent_process: HELIX-workflows/helix-process/L4-basic-design.md
pairs_test_design:
  - docs/v2/L9-test-design/helix-workflows-functional-test-design.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G4 evidence)"
  - role: doc-reviewer
    slot_label: "doc-reviewer — ドキュメント品質レビュー"
generates:
  - artifact_path: docs/v2/L4-architecture/helix-workflows-functional-design.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L9-test-design/helix-workflows-functional-test-design.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md
    artifact_type: design_doc
dependencies:
  parent: L4-helix-workflows-方式設計plan
  requires:
    - L0-helix-workflows-conceptplan
    - L1-helix-workflows-業務要求plan
    - L1-helix-workflows-機能要求plan
    - L1-helix-workflows-技術要求plan
    - L1-helix-workflows-非機能要求plan
    - L3-helix-workflows-業務要件plan
    - L3-helix-workflows-機能要件plan
    - L3-helix-workflows-非機能要件plan
    - L4-helix-workflows-方式設計plan
  blocks:
    - L4-helix-workflows-データ設計plan
    - L4-helix-workflows-外部IF設計plan
    - L5-helix-workflows-詳細設計plan
related_docs:
  - HELIX-workflows/helix-process/L4-basic-design.md
  - HELIX-workflows/helix-process/L9-system-test.md
  - docs/v2/L4-architecture/helix-workflows-system-architecture.md
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
  - docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md
  - skills/SKILL_MAP.md
  - helix/HELIX_CORE.md
  - CLAUDE.md
---

## §0 PLAN concept

本 PLAN は L4 方式設計と pair で運用する **機能設計** であり、CLI / DB / hook の物理設計とは切り分ける。
機能設計は「機能構成 + 機能間連携」の記述を凍結し、L5 詳細設計 / L7 実装で helix doctor check_*、hook、skill chain、dispatcher の具体契約を決定する。

本 PLAN は 5 機能領域を起点に、各機能の機械処理 mapping を同じ粒度で定義する。これにより `L4↔L9` の pair freeze が実装前に可観測化される。

### §0.1 5 機能領域

1. ドキュメント体系（F1）
2. PLAN テンプレート規約（F2）
3. skill 体系 + 推挙 framework（F3）
4. ワークフロー / 9 mode 入口分岐（F4）
5. オーケストレーションルール（F5）

これらを本 PLAN の中で固定し、Step 2-3 の本体化で各章に展開する。対象は `docs/v2/L4-architecture/helix-workflows-functional-design.md`（F1〜F5）と `docs/v2/L9-test-design/helix-workflows-functional-test-design.md`（ST-F1〜ST-F5）。

### §0.2 生物遺伝子工学 metaphor と対応

本 framework は「生物遺伝子工学を V モデルにはめ込んだ AI 時代の再編集モデル」を思想コアとする。
README 正本の DNA/染色体/ゲノム/細胞核 などの層構造を、5 機能領域の抽象レイヤに対応づける（§0.1.1 で凍結）。

1. ドキュメント体系 = DNA + 塩基配列 + 染色体 + ゲノム + 細胞核（設計情報の配列化）
2. PLAN 規約 = 遺伝子 + 遺伝子座 + 遺伝子発現（工程 ID の決定論）
3. skill 体系 = 細胞器官 + 細胞分化（役割分担による専門分化）
4. ワークフロー = 9 細胞応答経路 + 分裂サイクル（mode 入口と L0-L14 進行）
5. オーケストレーション = 中枢神経 + シナプス + 免疫系（自動化と AI 委譲の協働）

### §0.2.1 詳細対応表

| 機能領域 | 生物学 metaphor | 役割 |
|---|---|---|
| F1 ドキュメント体系 | DNA + 染色体 + ゲノム + 細胞核 | PLAN/ADR/docs の保存と参照規約。SSoT 制御 |
| F2 PLAN テンプレート規約 | 遺伝子 + 遺伝子座 + 発現 | 工程別 PLAN スキーマと進捗表現の統一 |
| F3 skill 体系 + 推挙 | 細胞器官 + 分化 | role 別責務分離と委譲スケジューラ |
| F4 ワークフロー入口 | 応答経路 + 分裂サイクル | 9 mode と Forward 回帰の入口制御 |
| F5 オーケストレーション | 中枢神経 + シナプス + 免疫 | 実行自動化、審査委譲、異常回収の 3 軸 |

## §1 工程表 (Step 1-6)

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 参考調査（L4 方式設計 + ADR-044 + CLAUDE.md + SKILL_MAP.md + HELIX_CORE.md + commit cd598d2 の思想原文） | ☑ completed (2026-05-27、本 wave で実施) |
| 2 | 機能設計 doc 起草 (`docs/v2/L4-architecture/helix-workflows-functional-design.md`) | ☑ completed (2026-05-27、574 行本体化、F1-F5 + §6 統合表) |
| 3 | L9 機能テスト設計 doc 起草 (`docs/v2/L9-test-design/helix-workflows-functional-test-design.md`) | ☑ completed (2026-05-27、357 行本体化、ST-F1〜F5 + fixture 契約) |
| 4 | tl-advisor adversarial check（G4 evidence） | ☑ completed (2026-05-27、conditional_approve P0=0/P1=5/P2=5/P3=2) |
| 5 | pmo-sonnet + doc-reviewer 二重 audit | ☑ completed (2026-05-27、pmo-sonnet=no→修正後 yes、doc-reviewer は次 session carry) |
| 6 | 修正反映 → G4 ゲート判定 → L5 詳細設計 / L4 残 PLAN へ展開 | ☑ in_progress (P1 修正反映済、conditional_approve 取得、L5 carry: planned CLI sweep + fixture path 実体化) |

Step 間の前提:

- Step1 が `required_docs` の欠損を洗い出し、残課題は §7 carry note へ集約。
- Step2/3 は本体化で `implementation_status` を `partial` とし、欠損行を `pairs trace` で明示。
- Step6 は pmo-sonnet と doc-reviewer の承認状態を carry し、G4 evidence として L9 側へ展開。

## §2 実装計画

### §2.1 必須記載項目

機能設計 doc と L9 機能テスト設計 doc は、各 F1〜F5 を「1-2 段落 + table 骨子 + 機械処理 mapping」で凍結する。

- F1〜F5 の章タイトル
- 機械処理 mapping（check 名 / hook / CLI / DB）
- `→ pair: L9 ST-Fn` の行
- 失敗時の `implementation_status`（partial/planned）

### §2.2 5 機能領域 ↔ 機械処理 mapping

| 機能領域 | 主契約 | 主要 check | 主 hook | DB / state |
|---|---|---|---|---|
| F1 | ドキュメント体系 | `check_doc_lifecycle`, `check_4_domain_separation`, `check_ssot_sync` | `SessionStart`, `pre-commit`, `pre-push` | `.helix/audit/*.yaml` + `helix.db` |
| F2 | PLAN 規約 | `check_plan_frontmatter_completeness`, `check_plan_naming_convention`, `check_plan_template_usage` | `pre-commit`, `helix plan validate` | `helix.db` event_log |
| F3 | skill / 推挙 | `check_skill_catalog`（再構築時）, `check_skill_chain_invocation` | `pre-tool-use` + `agent-guard` | `helix.db` agent_events |
| F4 | ワークフロー | `check_mode_routing`, `check_reentry_gate`, `check_vmodel_trace` | `helix mode`, `helix route` | mode_transition + readiness |
| F5 | オーケストレーション | `check_advisor_usage`, `check_agent_slot_coverage`, `check_parallel_safety` | `helix skill chain`, `helix agent` | delegation ledger + handover |

### §2.3 方式設計 pair 整合性

- 本 PLAN は `L4-helix-workflows-方式設計plan` の `generates` と同一運用で pair freeze する。
- 機能設計 doc: `docs/v2/L4-architecture/helix-workflows-functional-design.md`
- テスト設計 doc: `docs/v2/L9-test-design/helix-workflows-functional-test-design.md`
- 仕様変更は L9 DoD に連動し、片側のみ更新しない。

### §2.4 L4 接続規約

`driver` は `be` を基本とし、`docs/README`・`docs/v2`・`docs/plans/L4`・`docs/adr` の 4 参照面で相互参照を保つ。
`plan_validator` は Step6 まで `error 0` を満たす。`warn` は未起票 artifact への期待（blocks）については運用 carry として許容。

## §3 成果物

- 起票 1: 本 PLAN（本ファイル）
- 起票 2: 機能設計 doc
  - `docs/v2/L4-architecture/helix-workflows-functional-design.md`
- 起票 3: 機能テスト設計 doc
  - `docs/v2/L9-test-design/helix-workflows-functional-test-design.md`

## §4 残 carry

Step 2-3 に本体化される carry として以下を明示。

1. F 各節の観点・観測コマンドを 1 章 1 テーブルまで充実
2. 生物 metaphor の詳細対応（README 正本の該当条項）を表形式で 5 層連携化
3. skill 件数（既存 116+）の最新化と role count 検証
4. 9 mode 図、Forward 回帰図、V-model trace 図の mermaid 完成
5. 機械処理 mapping の table を ST-Fx へ完全整備

## §5 L4 完遂条件 (DoD)

1. F1〜F5 全部（§1-§5）の本体化対象が明示され、carry と実装方針が分離されている
2. L9 ST-F1〜ST-F5 が §7 対応表で 1:1 になっている
3. tl-advisor PASS と pmo-sonnet + doc-reviewer 並列 audit が完了
4. `plan_validator` error 0（warn は carry の場合のみ）
5. balance_ratio は BR/FR/NFR/AC/OT の再集計で 1.0 以上維持
6. 5 機能領域の機械処理 mapping が `check_*` と hook と DB 状態まで含む
7. 本 PLAN 自体の frontmatter が V2 正本スキーマ準拠

### §5.1 pair trace 完了監査（required）

- F1 → ST-F1
- F2 → ST-F2
- F3 → ST-F3
- F4 → ST-F4
- F5 → ST-F5

### §5.2 次 Wave 受け入れ条件

- 本 PLAN の Step6 通過時に、機能設計 doc と L9 test design が以下を満たしていること。
- §1 5 機能領域の本文化率 100%
- §2-§2.4 の必須 mapping 記述がすべて埋まっていること
- §4 carry が next action として L5 / L4 副 PLAN に受け渡されていること

### §5.3 検証証跡（skeleton 判定）

| 種別 | 判定方法 | 期待値 |
|---|---|---|
| frontmatter parse | YAML parse | OK |
| plan_validator | `python3 cli/lib/plan_validator.py ...` | error 0 |
| F-L9 trace | 5 行固定 | 1:1 対応 |
| L4 line count | wc | 200〜300 |

## §6 参考ガードライン

### §6.1 変更原則

1. 機能設計は構造・関係を固定し、実装契約は Step2 以降へ先出ししない。
2. L4 で固定しない値を後続へ持ち越す場合、必ず `carry` に記載する。
3. pair trace 欠損は次工程禁止条件として明示する。

### §6.2 監査前提

- 変更は 3 行レベルで監査可能な形式（check 名・hook・CLI・DB）を付与。
- 5 機能は 1 つの PLAN のみで定義し、機能間の重複記述は避ける。
- `implementation_status` は `partial`/`planned` を優先し、`implemented` は L4 本体化完了時に更新。

### §6.3 参照リンク

- `docs/v2/L4-architecture/helix-workflows-system-architecture.md`
- `docs/v2/L9-test-design/helix-workflows-system-test-design.md`
- `docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md`
- `HELIX-workflows/helix-process/L4-basic-design.md`

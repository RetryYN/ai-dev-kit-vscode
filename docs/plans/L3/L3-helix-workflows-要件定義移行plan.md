---
plan_id: L3-helix-workflows-要件定義移行plan
title: "L3-helix-workflows-要件定義移行plan: L1 要求 → L3 要件への移行 (L1 carry 採択判断)"
kind: requirements
layer: L3
drive: be
status: finalized
created: 2026-05-29
owner: PM
process_layer: L3
parent_process: HELIX-workflows/helix-process/L3-requirements-definition.md
pairs_test_design: []
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 採択判断・移行 finalize"
  - role: tl-advisor
    slot_label: "TL — FR-13 PLAN レビュー (ユーザー確認の前)"
  - role: pmo-sonnet
    slot_label: "PMO — L1 carry trace 整合チェック"
generates:
  - artifact_path: docs/plans/L3/L3-helix-workflows-要件定義移行plan.md
    artifact_type: doc_update
dependencies:
  parent: L1-helix-workflows-要求定義移行plan
  requires:
    - L0-helix-workflows-conceptplan
    - L1-helix-workflows-要求定義移行plan
    - L1-helix-workflows-業務要求plan
    - L1-helix-workflows-機能要求plan
    - L1-helix-workflows-技術要求plan
    - L1-helix-workflows-非機能要求plan
  blocks:
    - L3-helix-workflows-業務要件plan
    - L3-helix-workflows-機能要件plan
    - L3-helix-workflows-非機能要件plan
related_docs:
  - docs/plans/L1/L1-helix-workflows-要求定義移行plan.md
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - docs/v2/L1-requirements/helix-workflows-functional-requirements.md
  - docs/v2/L1-requirements/helix-workflows-technical-requirements.md
  - docs/v2/L1-requirements/helix-workflows-nfr.md
  - docs/v2/L3-requirements/helix-workflows-business-requirements-detail.md
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
  - docs/v2/L3-requirements/helix-workflows-nfr-detail.md
  - HELIX-workflows/helix-process/L3-requirements-definition.md
---

# L3-helix-workflows-要件定義移行plan: L1 要求 → L3 要件への移行

> **工程**: L1 → L3 移行 (工程間移行 PLAN)
> **正本**: HELIX-workflows/helix-process/L3-requirements-definition.md
> **本 PLAN の対象**: L1 4 doc (業務 / 機能 / 技術 / 非機能要求) の **carry / 残課題 / L3 で詰めるべき項目** を採択 / 保留 / 見送り判断し、採択分を L3 3 doc (業務 / 機能 / 非機能要件) に振り分ける**進め方 + 採択判断の軌跡**。
>
> **起票理由 (2026-05-29)**:
> 1. 範例 [L1-要求定義移行plan §5](../L1/L1-helix-workflows-要求定義移行plan.md): 「L0→L1 だけでなく **L1→L3 / L3→L4 ... 各工程移行に同様の採択 / 詰め判断 PLAN が要る**」
> 2. 既存 L3 3 PLAN (2026-05-26 起票) は各 PLAN が独立に L1 → L3 mapping を持つが、**L1 4 doc の carry を一覧化して採択判断を集約した trace が散在**。grep 差分だけで「L1 carry がクリア漏れ」と早合点する事故 ([[feedback_vmodel_pair_judge_by_trace_not_file]]) を再発させない。
> 3. FR-13 PLAN 起票レビュールール (L1 機能要求 FR-13、2026-05-28 確立) の**適用第 1 号**として、本 PLAN 起票後にユーザー確認の前に tl-advisor へ正当性レビューを通す。
>
> **scope 厳守**: 本 PLAN は L1→L3 migration boundary のみ扱う。L3 doc 本体 (-detail.md 3 件) の中身は既存 L3 3 PLAN が正本。L4 以降には踏み込まない ([[feedback_stay_in_requested_phase_scope]] / [[feedback_plan_doc_adr_layer_vmodel_order]])。

## §1 工程表 (進め方)

| Step | 作業 | 進捗 |
|---|---|---|
| 1 | L1 4 doc の carry / 残課題 / L3 へ持ち越し項目を一覧化 | ☑ completed (本 PLAN §2、機能 §5/§6 + 業務 §9/§9.1 + 技術 §8 + 非機能 §8 から抽出) |
| 2 | 各項目を採択 (L3 で確定) / 保留 (L4 へ繰り越し) / 見送り判断 | ☑ completed (本 PLAN §2) |
| 3 | 採択分を L3 3 PLAN / L3 3 doc に振り分け | ☑ completed (本 PLAN §2 table) |
| 4 | 保留分 (L4 へ持ち越し) を §3 ヒアリングシートに整理 | ☑ completed (§3) |
| 5 | L3 3 PLAN (既存) へ blocks でバトン | ☑ completed (frontmatter dependencies.blocks) |
| 6 | FR-13: tl-advisor PLAN レビュー → 修正反映 | □ pending (本 PLAN 起票直後) |
| 7 | ユーザー要点報告 → 承認後 commit | □ pending |

## §2 要点書 (L1 carry → L3 採択判断の軌跡)

> **正本宣言**: 詳細振り分けは L3 3 PLAN / L3 3 doc が正本 (本 PLAN は判断軌跡の集約であり、要件内容を重複記載しない)。本 §2 は L1 4 doc の **carry section を 1 ヶ所に集約** することで「どの L1 carry が L3 で確定し、どの carry が L4 へ繰り越されるか」の trace を担保する。

### §2.1 L1 機能要求 carry → L3 採択 (L1 doc §4/§5/§6 由来)

| L1 carry source | 内容 | 判断 | 主振り分け先 |
|---|---|---|---|
| L1 §5 FR-01 carry | NSM 集計の計測対象・入出力・受入基準 (物理 SQL / schema / view 名は L4/L5 carry) | **採択 (L3 で確定)** | L3 機能要件 (FR-NSM-01)。tl-advisor P2 反映: L3 では仕様レベルまで、物理 schema は L4/L5 |
| L1 §5 FR-02 carry | Guardrail 逸脱時の gate 連動ルール | **採択 (L3 で確定)** | L3 機能要件 (FR-GR-01) + `gate-policy.yaml` (実体化は L4 carry) |
| L1 §5 FR-03 carry | TDD detector / sprint state machine | **採択 (L3 で確定)** | L3 機能要件 (FR-TDD-01) |
| L1 §4 carry L1-IN-09 | PLAN template 手順書化 (`agent_slot` / `workflow_ref` field 組込み + step ごとの machine-enforced workflow ref) | **保留 → L4 へ** | L1 技術要求 §8 carry + L4 基本設計 PLAN 起票時に template lint 機能化 |
| L1 §1 FR-13 carry | FR-13 PLAN 起票レビューの適用範囲 (mandatory / recommended / skip 閾値、risk / size / trace-impact ベース) | **採択 (L3 で確定)** | L3 機能要件 (FR-13 詳細化) |

### §2.2 L1 業務要求 carry → L3 採択 (L1 doc §9 / §9.1 / §10 由来)

| L1 carry source | 内容 | 判断 | 主振り分け先 |
|---|---|---|---|
| L1 §9 carry | 8 BR 優先度配分 (P0/P1/P2) の Phase α/β/γ 数値閾値 (L1-IN-13 連動) | **採択 (L3 で確定)** | L3 業務要件 (BR 優先度配分の数値化) |
| L1 §9 carry | §3.1 業務フローの「G ゲート」合成式 (static_subchecks + AI 判定、L0 §6.5.4 由来) | **採択 (L3 で確定)** | L3 業務要件 (合成式定義) + `gate-policy.yaml` 実体化は L4 carry |
| L1 §9 carry | BR-09〜BR-12 の L14 OT-09〜12 実体定義 | **保留 → L14 へ** | L14 運用テスト設計 doc (L1↔L14 pair freeze は L14 工程で完成) |
| L1 §9.1 L1-IN-13 | Phase α/β/γ 境界 KGI 確定 (must / should / later 3 段分割 + kill criteria) | **採択 (L3 で確定)** | L3 業務要件 + L3 非機能要件 |
| L1 §9.1 L1-IN-14 | 専門エージェント / team 構造の Phase 配分 (チームアルゴリズム設計 / セキュリティ監査 / ドメインチェック自動化 / コーディングルール自動化等) | **保留 → L4 へ** | L4 基本設計 (team 構造 + 各 team の使用フェーズ + ROI 評価) |
| L1 §9.1 L1-IN-15 | 逆引き audit 11 穴の段階対応 | **段階対応** (P1 = L3/L4、P2 = L7/L9、P3 = L13/L14) | L3 採択分 (P1 進化 / 繁殖 / 老化 / 共生 / 代謝) を L3 業務 + L3 非機能に差分化、P2/P3 は L4/L7-L9/L13-L14 へ |
| L1 §10 carry | 業務 entity の属性 / 集約境界 / ライフサイクル詳細 (DDD) | **保留 → L4 へ** | L4 基本設計 (arc42 §5 Building Block View) |

### §2.3 L1 技術要求 carry → L3 採択 (L1 doc §6 / §7 / §8 由来)

| L1 carry source | 内容 | 判断 | 主振り分け先 |
|---|---|---|---|
| L1 TR-01〜TR-08 | 採用技術詳細 / 制約 (helix.db schema 二層 / skill 注入 / 9 mode 共通基盤 / drift 解消) | **採択 (L3 で確定済)** | L3 機能要件 (FR-NSM-01 〜 FR-MIGR-01 に統合済、既存 L3 機能要件 PLAN §2.2 mapping 参照) |
| L1 §6 (L1-IN-08) | 9 mode 完了 event の helix.db schema (mode closure event) | **採択 (L3 で確定)** | L3 機能要件 (FR-EVT-01) + L3 業務要件 (mode 業務フロー) |
| L1 §8 carry | 技術要求 doc は L1↔L14 ではなく **L4↔L9 でペア凍結** (`next_pair_freeze: L4`) | **保留 → L4 へ** | L4 基本設計起票時に L9 総合テスト設計を pair artifact 化 |

### §2.4 L1 非機能要求 carry → L3 採択 (L1 doc §1〜§8 由来)

| L1 carry source | 内容 | 判断 | 主振り分け先 |
|---|---|---|---|
| L1 §7 NFR-OP-05 | session 跨ぎ memory carry の verify-before-act 機械強制 ([[feedback_memory_verify_before_act]]) | **採択 (L3 で確定)** | L3 非機能要件 (NFR-OP-05 詳細化、判定式・違反検出契約を確定) |
| L1 §8 carry | `pairs_test_design: []` は L1 で許容、L4 で L9/L13/L14 検証設計 artifact 追加 | **保留 → L4 へ** | L4 基本設計起票時に pair artifact 追加 (`pairs_test_design` 更新) |
| L1 §8 L1-IN-15 carry | 逆引き 11 穴は §3 運用保守 / §4 移行性 / §5 セキュリティで段階吸収、未実装分は L3/L4 で明示差分化 | **採択 (L3 で差分化、§2.2 と整合)** | L3 非機能要件 (§3 NFR-OP-* / §4 NFR-MIG-* / §5 NFR-SEC-* に P1 5 系統を吸収) |
| L1 §1 (使用性 skip) | 機能適合性は L3 機能要求 + L4-L6 設計で凍結、使用性は HELIX-workflows が UI を持たないため L2/L10 skip | **採択 (skip 方針を L3 でも維持)** | L3 非機能要件 (使用性 skip の根拠記録 + docs site / visual workflow 追加時の unskip 条件) |
| L1 §2/§3 carry | IPA × ISO 25010 二軸タグの数値閾値 (可用性 / 性能 / 運用保守) | **採択 (L3 で確定)** | L3 非機能要件 (IPA グレード値を明示化、L12 受入テスト pair に AC-NFR-* として降下) |

### §2.5 集計 (tl-advisor P1 反映、2026-05-29)

| 区分 | 件数 | 主振り分け先 |
|---|---:|---|
| 採択 (L3 で確定) | 13 件 | L3 3 doc (-detail.md) / L3 3 PLAN |
| 保留 (L4 へ繰り越し) | 5 件 | §3.1 (L1 carry row 由来、下流 action は別ラベル) |
| 保留 (L14 へ繰り越し) | 1 件 | L14 運用テスト設計 doc |
| 段階対応 | 1 件 (L1-IN-15) | L1 carry row 1 件、派生 action は §3.1/§3.3 へ展開 |
| **合計** | **20 件** | 機能 5 + 業務 7 + 技術 3 + 非機能 5 (§2.1〜§2.4 row 計と一致) |

> **件数定義**: 本 §2.5 は **L1 carry row** (§2.1〜§2.4 の row 数) を集計する。§3 ヒアリングシートに記載される **下流 action** とは別軸 (1 つの carry row が複数の下流 action に展開される / 段階対応 row から派生 action が複数発生する) のため、§3 の bullet 数とは一致しない。

## §3 ヒアリングシート (L4 / L14 へ持ち越し / 保留事項)

下流工程 (主に L4 基本設計) で確定すべき事項を蓄積。auto mode で都度チャットせず、ここで保留:

### §3.1 L4 基本設計へ持ち越し (L1 carry row 5 件 + 関連下流 action 2 件 = 7 bullet)

> tl-advisor P2 反映 (2026-05-29): 本 §3.1 の bullet 数 (7) は §2.5 「保留 L4 5 件」と直接一致しない。**§2.5 = L1 carry row 集計** (本 PLAN 工程の集約軸) / **§3.1 = 下流 action 列挙** (L4 工程の入口リスト) の二軸。`gate-policy.yaml 実体化` と `逆引き 11 穴 P2` は L1 carry row として §2.5 で重複計上せず、§2.2/§2.4 の row が L4 で展開する派生 action として §3.1 に列挙する。

- [ ] **L1-IN-09 PLAN template 手順書化**: 各工程 template (`cli/templates/plan/v2/L00-L14-*-template.md` 全 15 件) に `agent_slot` + `workflow_ref` field を組込み、step ごとに担当 agent / workflow ref を機械強制する (L4 基本設計で template lint 機能として詳細化、tl-advisor / pmo-sonnet 2026-05-26 Phase C audit 指摘反映)
- [ ] **L1-IN-14 team 構造**: 専門エージェント / team scaling をどの Phase に配分するか (チームアルゴリズム設計 / セキュリティ監査 / ドメインチェック自動化 / コーディングルール自動化等の team 編成、memory carry §9 P1.5)。各 team の使用フェーズ + ROI 評価
- [ ] **業務 entity 詳細**: 属性 / 集約境界 / ライフサイクル (L4 arc42 §5 Building Block View)
- [ ] **技術要求 L4↔L9 pair freeze**: L4 基本設計起票時に L9 総合テスト設計を pair artifact 化 (`next_pair_freeze: L4` 反映)
- [ ] **NFR `pairs_test_design` 追加**: L1 NFR doc の `pairs_test_design: []` を L4 起票時に L9 / L13 / L14 検証設計 artifact で更新
- [ ] **`gate-policy.yaml` 実体化**: G ゲート合成式 (static_subchecks + AI 判定) を YAML 化 (L4 carry、複数 §2 carry の合流先)
- [ ] **逆引き 11 穴 P2 (L7-L9)**: 内分泌 / 循環 / 消化 / 性差 (L7-L9 工程の検証対象)

### §3.2 L14 へ持ち越し

- [ ] **BR-09〜BR-12 ↔ OT-09〜12 実体定義**: L1↔L14 pair freeze の balance_ratio 実測完成 (L14 運用テスト設計 doc 起票時)

### §3.3 L13-L14 へ持ち越し

- [ ] **逆引き 11 穴 P3 (L13-L14)**: 多細胞化 / 神経変性 (L13 デプロイ後検証 / L14 運用検証で吸収)

## §4 DoD (移行完了条件)

- ☑ L1 4 doc の carry / 残課題が本 PLAN §2 に集約されている (機能 5 + 業務 7 + 技術 3 + 非機能 5 = **20 件** 1:1 trace、tl-advisor P1 反映)
- ☑ 採択 **13 件** の主振り分け先が L3 3 doc / L3 3 PLAN として示されている
- ☑ 保留 **5 件** (L4) + 1 件 (L14) + 段階対応 1 件 (L1-IN-15) が §3 ヒアリングシートに整理されている
- ☑ L3 3 PLAN (既存) へ blocks でバトンが渡されている (frontmatter dependencies.blocks)
- □ **FR-13 適用**: tl-advisor PLAN レビュー → 指摘 (P0/P1/P2) 反映済 (本 turn)
- □ plan_validator / plan_lint で errors なし (本 turn)
- □ ユーザー要点報告 → 承認後 commit

## §5 関連 / 再発防止

- **範例 PLAN**: [L1-helix-workflows-要求定義移行plan](../L1/L1-helix-workflows-要求定義移行plan.md) §5「L0→L1 だけでなく **L1→L3 / L3→L4 ... 各工程移行に同様の採択 / 詰め判断 PLAN が要る**」
- **FR-13 適用第 1 号**: 本 PLAN 起票後、ユーザー確認の前に tl-advisor へレビュー依頼 (L1 機能要求 FR-13 / L0 §8 L1-IN-22)
- **既存 L3 3 PLAN (業務 / 機能 / 非機能要件)**: 本 PLAN の blocks で繋ぐ。各 PLAN の Step 5 (TL レビュー) / Step 6 (pmo audit) は本 PLAN とは別の作業として進める (scope 厳守)
- **工程間移行 PLAN チェーン (確立)**:
  - L0→L1 (完了、commit 9ae52c7 / 5082eb2)
  - **L1→L3 (本 PLAN、2026-05-29)**
  - L3→L4 (将来、本 PLAN §3.1 の L4 carry を入口に起票)
  - L4→L5 / L5→L6 / L6→L7 / ... (将来)
- **scope 違反防止**: [[feedback_stay_in_requested_phase_scope]] (依頼 = L1→L3 移行) / [[feedback_plan_doc_adr_layer_vmodel_order]] (PLAN = 進め方、設計内容は doc 側) / [[feedback_vmodel_pair_judge_by_trace_not_file]] (grep 差分でなく採択判断の集約 trace で確認)
- **plan_validator WARN 3 件は範例同型で運用上 accepted** (tl-advisor P3 反映、2026-05-29): 本 PLAN の `dependencies.blocks` 3 件 (L3 業務/機能/非機能要件 PLAN) に対し、被 block 側 PLAN が `requires` に本 PLAN を列挙していないため WARN が出る。範例 [L1-要求定義移行plan](../L1/L1-helix-workflows-要求定義移行plan.md) も同型 WARN 4 件で運用中 (L0→L1 完遂 commit `5082eb2` 時点)。移行 PLAN は工程間 trace 用途で被 block 側の編集を最小化する設計、後続レビューで誤検出と誤認しないこと。

---
plan_id: R-helix-workflows-existing-assets-fullbackplan
title: "R-helix-workflows-existing-assets-fullbackplan: HELIX framework 既存資産 548 件 × L1/L3 要件 56 ID の双方向 trace + 機能一覧 SSoT 起草 (Reverse fullback)"
kind: reverse
layer: cross
drive: reverse
reverse_type: fullback
workflow_phase: R4
status: draft
created: 2026-05-29
owner: PM
size: M
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・PO 確認 (R3)・最終 finalize"
  - role: tl-advisor
    slot_label: "TL — adversarial check (RG0-RG3 ゲート判定)"
  - role: pmo-sonnet
    slot_label: "PMO — inventory / audit / 起草支援 (Wave A-fix-E)"
generates:
  # 注: artifact_type は cli/lib/plan_validator.py の VALID_ARTIFACT_TYPES に従う。
  # yaml_* type が enum 未対応の場合は markdown_doc に fallback、PLAN body §3 で yaml 形式と明記
  - artifact_path: docs/v2/reverse/fullback/helix-workflows-existing-assets/F0-fullback-evidence.yaml
    artifact_type: markdown_doc  # 実 yaml (plan_validator enum 制約)
  - artifact_path: docs/v2/reverse/fullback/helix-workflows-existing-assets/F1-fullback-contracts.yaml
    artifact_type: markdown_doc  # 実 yaml
  - artifact_path: docs/v2/reverse/fullback/helix-workflows-existing-assets/F2-fullback-as-is-review.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/reverse/fullback/helix-workflows-existing-assets/F3-fullback-handover-checklist.yaml
    artifact_type: markdown_doc  # 実 yaml
  - artifact_path: docs/v2/reverse/fullback/helix-workflows-existing-assets/F4-fullback-routing.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/L3-requirements/helix-workflows-functional-registry.md
    artifact_type: design_doc
pairs_test_design: []
dependencies:
  parent: null
  requires: []
  blocks: []
related_l1:
  - docs/v2/L1-requirements/helix-workflows-functional-requirements.md
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - docs/v2/L1-requirements/helix-workflows-nfr.md
  - docs/v2/L1-requirements/helix-workflows-technical-requirements.md
related_l3:
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
  - docs/v2/L3-requirements/helix-workflows-business-requirements-detail.md
  - docs/v2/L3-requirements/helix-workflows-nfr-detail.md
related_adr: []
related_docs:
  - HELIX-workflows/helix-process/reverse-workflow.md
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
audit_history:
  - "2026-05-29: pmo-sonnet — PLAN draft 起票 (R0-R4 完了状態を retrofit)"
  - "2026-05-29: pmo-sonnet (Wave fix-E) — tl-advisor R1 P1 反映 (HO-01〜08 F3 SSoT 同期 + frontmatter 型/related update + 件数 548 / path docs/v2/reverse/ 同期 + RGC 条件付き表現)"
---

## §0 PLAN

HELIX framework の 548 既存資産 (CLI 80 / lib 139 / hook 17 / agent 19 / skill 130 / workflow doc 49 / templates 114) を機能一覧 SSoT として体系化し、L1 要求 13 FR / L3 要件 18 FR を含む 56 ID との双方向 trace を完成させる。実装完遂後の文書整合 = Reverse fullback workflow R0-R4 を正式実施する。

本 PLAN は **後追い retrofit**: 本 session の作業 (ad hoc に進行) を fullback workflow に整理して PLAN 化することで、今後の類似作業の標準化に資する。

---

## §1 目的

1. HELIX framework 既存資産 548 件の機能一覧 SSoT を確立する (FR-FNREG-01 部分実体化)
2. L1 要求 ↔ L3 要件 ↔ 実装資産の双方向 trace を機械検証可能にする
3. 漏れ (順方向: 要件→実装 / 逆方向: 実装→要件) を整理し、Forward HELIX (L1 back-port / L4 carry / Wave 内実体化) へ routing する
4. Reverse fullback workflow の dogfooding 事例として標準化し、今後の類似 fullback PLAN の雛形とする

---

## §2 背景

本 session 開始時、ユーザー指示「HELIX-workflows を確認して要件定義からの漏れはないかチェックして」と「既存資産を機能一覧にして漏れをなくす」を受けて、ad hoc に inventory + audit + 機能一覧 doc 起草を進行した。

途中でユーザーから「これがリバースフルバックの導線だな」との指摘があり、本作業が正式に Reverse fullback workflow R0-R4 に該当することが確認された。

Reverse fullback type (SKILL_MAP.md §Reverse type matrix) の定義:

> fullback: 実装完遂後の文書整合が起点。R0 で実装証拠、R1 で文書 gap、R2 で alignment 設計、R3 で文書 PO 確認、R4 で closure routing を行う。

本 PLAN は事後 retrofit として、Wave A-G の成果物を fullback workflow 成果物 (F0-F4) に整形し、正式 PLAN として登録する。

---

## §3 実装計画

### R0: Evidence Acquisition (完了済 ✓)

目的: 既存資産の全件収集と機械的列挙。

- **Wave A** (2026-05-29 実施): CLI / lib / hook / agent / template の inventory を取得 (初期計上 CLI 94 / template 108、後の verify で canonical 80 / 114 と判明)
- **Wave B** (2026-05-29 実施): skill / workflow doc の inventory を取得 (初期計上 skill 132 / workflow 50、後の verify で canonical 130 / 49 と判明)
- **F0 retrofit**: 上記 inventory を `docs/v2/reverse/fullback/helix-workflows-existing-assets/F0-fullback-evidence.yaml` に整形 (canonical 件数 548)

資産内訳 (合計 548 件、`find -type f -executable` 等で re-verify):

| カテゴリ | 件数 | 備考 |
|---|---|---|
| CLI binaries | 80 | regular file + executable (`cli/helix-plan-cmds/` 配下 12 sub-script + dir entry 2 件は内部構成要素のため除外) |
| lib (Python モジュール) | 139 | `cli/lib/*.py` |
| hook | 17 | `.claude/hooks/*.sh` |
| agent (.claude/agents/) | 19 | |
| skill (SKILL.md) | 130 | `skills/**/SKILL.md` |
| workflow doc (HELIX-workflows/) | 49 | `helix-process/*.md` (48) + root `HELIX-process-L0-L14.md` (1) |
| template | 114 | `cli/templates/**` 全 file |
| **合計** | **548** |

RG0 ゲート: 証拠網羅ゲート [TL] — 全カテゴリ列挙完了を確認。

### R1: Observed Contracts (完了済 ✓)

目的: L1 要求 56 ID × L3 detail の双方向 trace を機械的に抽出。

- **pmo-sonnet audit** (2026-05-29 実施): L1 56 ID × L3 detail trace 表を生成
- **F1 retrofit**: 上記 audit を `docs/v2/reverse/fullback/helix-workflows-existing-assets/F1-fullback-contracts.yaml` に整形

観測契約 結果:

| 採録種別 | 件数 |
|---|---|
| L3 採択 (そのまま反映) | 47 |
| L4 carry (基本設計で実体化) | 5 |
| L14 carry (運用検証工程) | 1 |
| 段階対応 (条件付き実体化) | 1 |
| L3 新規拡張 (Wave D 候補) | 2 |
| **合計** | **56 (100% 採録)** |

RG1 ゲート: 契約検証ゲート [TL] — L1 56 ID 全件の trace 完了を確認。

### R2: As-Is Review (完了済 ✓)

目的: 観測契約から現状設計の alignment 設計を起草。

- **Wave C** (2026-05-29 実施): 機能一覧 SSoT `docs/v2/L3-requirements/helix-workflows-functional-registry.md` (848 行) を起草
- **Wave E** (2026-05-29 実施): L3 FR doc に back-port 親 trace 追記 (FR-FNREG-01 / FR-GLOSSARY-01 / BR-RULE-13 / FR-13 横断)
- **F2 retrofit**: `docs/v2/reverse/fullback/helix-workflows-existing-assets/F2-fullback-as-is-review.md` (summary wrapper)

alignment 起草 scope:

- FR-FNREG-01: 機能一覧 SSoT 初版 (functional-registry.md、全 548 資産 × FR/BR 双方向 link)
- FR-GLOSSARY-01: 用語一覧 SSoT 候補 (Wave D 別 fullback での実体化を routing)
- BR-RULE-13: V2 PLAN 命名規則 × 既存 223 件 V1 PLAN の is_reference 整合確認

RG2 ゲート: 設計検証ゲート [TL + adversarial-review] — alignment 設計の妥当性確認。

### R3: Intent Hypotheses + PO Checklist (完了済 ✓)

目的: 実装意図の仮説 + PO 確認事項を列挙。

- **Wave R3** (2026-05-29 実施): `docs/v2/reverse/fullback/helix-workflows-existing-assets/F3-fullback-handover-checklist.yaml` (HO-01〜HO-08 = 8 item) を起草

PO 確認事項 一覧 (urgency × routing_candidate):

| ID | カテゴリ | 内容 | urgency | routing_candidate |
|---|---|---|---|---|
| HO-01 | important_forward_gap | FR-FNREG-01 の L1 back-port 欠落 — FR-14 (機能一覧管理) を L1 doc に back-port するか | medium | L4 carry または L3 trace 追記で closure |
| HO-02 | important_forward_gap | FR-GLOSSARY-01 の L1 back-port 欠落 かつ実装未実体化 — glossary-registry.md 起草 + FR-15 back-port するか | high | Wave D (本 session) または L4 carry |
| HO-03 | important_reverse_gap | BR-RULE-13 の L1 back-port 欠落 — BR-13 (PdM 提案統合業務) を L1 doc に back-port するか | low | L4 carry または L3 trace 追記で closure |
| HO-04 | reverse_gap_deprecated | DEPRECATED shim 4 件 (helix-check-claudemd / helix-gate-api-check / helix-hook / helix-session-start) の廃止 milestone 不明 | medium | L4 carry (NFR-OP-01 拡張) または warn 残置 |
| HO-05 | reverse_gap_legacy_alias | helix-scrum alias の廃止 milestone 不明 | low | L4 carry または indefinite alias 維持 |
| HO-06 | confirmation_resolved | 本 R2 で trace 追記済 5 件 (helix-test / helix-test-debug / helix-bats-cleanup / assets 7 file / folder-structure-review.md) の closure 確認 | low | RG3 pass → R4 で 5 件まとめて closure |
| HO-07 | structural_observation | L3 FR mapping coverage 78% 未達 (FR-GLOSSARY-01 未実装) — Wave D で glossary-registry.md 起草するか | high | Wave D (本 session) または L4 carry |
| HO-08 | methodology_retrofit | 本 session 作業が ad hoc で進行 — helix reverse fullback CLI 標準化推奨 | low | L4 carry (reverse-workflow.md §fullback section 追加) |

urgency 集計: high 2 件 (HO-02 / HO-07) / medium 2 件 (HO-01 / HO-04) / low 4 件 (HO-03 / HO-05 / HO-06 / HO-08)

詳細: [F3-fullback-handover-checklist.yaml](../v2/reverse/fullback/helix-workflows-existing-assets/F3-fullback-handover-checklist.yaml) を SSoT として参照。本 PLAN は F3 の概要のみ記載、HO-ID 詳細 (finding / hypothesis / po_question / decision_required) は F3 yaml 正本。

RG3 ゲート: 仮説検証ゲート [PM + PO + TL] — PO 確認と意図仮説の妥当性確認。

### R4: Gap & Routing (完了済 ✓)

目的: Gap を Forward HELIX の具体的な routing 先に変換。

- **Wave R4** (2026-05-29 実施): `docs/v2/reverse/fullback/helix-workflows-existing-assets/F4-fullback-routing.md` (Forward 戻し先別 routing 表) を起草

Forward routing 件数:

| routing 先 | 件数 | 主な内容 |
|---|---|---|
| L1 doc 改訂 (back-port) | 3 | HO-01 (FR-14) / HO-02 (FR-15) / HO-03 (BR-13) |
| L3 拡張 (Wave 内追加) | 1 | HO-02/07 連動 Wave D 候補 (glossary-registry) |
| L4 carry (基本設計) | 4 | HO-04 (deprecated shim) / HO-05 (helix-scrum alias) / HO-07 (coverage 不達) / HO-08 (fullback CLI doc) |
| L8-L11 closure (RG3 pass) | 1 | HO-06 (resolved 5 件まとめ確認) |
| RGC closure (closed) | 5 | FR-FNREG-01 / F0-F4 全件 / functional-registry.md 起草 |
| RGC open | 7 | L4 carry 4 / L1 back-port 3 |

invalidate-forward 判定:

- G1 (要求完了ゲート): 再実施候補 — back-port 3 件確定後に再確認要
- G3 (要件凍結ゲート): **条件付き** — Wave D で新 FR/AC 追加なら再判定候補、catalog 実体化のみなら不要
- G4 (基本設計凍結ゲート): 不要 — L4 carry 4 件は次 L4 PLAN で individual 処理

---

## §4 受入条件 / DoD

- [x] R0 evidence: 548 資産が機械的に列挙されており F0 yaml に整形されている
- [x] R1 contracts: L1 56 ID 全件が L3 detail と trace されている (採録率 100%)
- [x] R2 as-is review: 機能一覧 SSoT (functional-registry.md 848 行) が起草されている
- [x] R3 handover checklist: 8 item × PO 質問 + urgency + routing_candidate が明示されている (F3 SSoT)
- [x] R4 routing: Forward 戻し先別 routing 表 + invalidate 判定 + 条件付き RGC pass が確定されている
- [ ] tl-advisor R2 adversarial check passed (本 PLAN 修正後実施)
- [ ] PO 承認 (本 PLAN の commit 前 + HO-01〜08 actual_route 確定)
- [ ] L4 carry 4 件 / L1 back-port 3 件 / Wave D 1 件の Forward route 反映 (別 PLAN または本 session 内)

---

## §5 関連 PLAN / ADR / docs

### 関連 PLAN

| PLAN | 関係 |
|---|---|
| L1-helix-workflows-要求定義移行plan | related (L1 要求 56 ID の起点) |
| L1-helix-workflows-機能要求plan | related (FR 13 件 trace 対象) |
| L1-helix-workflows-業務要求plan | related (BR 13 件 trace 対象) |
| L3-helix-workflows-要件定義移行plan | related (L3 56 ID への展開) |
| L3-helix-workflows-機能要件plan | related (FR 18 件 trace 対象) |
| L3-helix-workflows-業務要件plan | related (BR trace 対象) |

### 後続 PLAN 候補

| PLAN 候補 | 内容 | 優先度 |
|---|---|---|
| L1-helix-workflows-back-portplan | FR-14 / FR-15 / BR-13 back-port | 低-中 |
| L4-helix-workflows-基本設計plan §carry 追加 | L4 carry 4 件追加 | 中 |
| R-helix-workflows-glossary-registry-fullbackplan | Wave D 別 fullback (用語一覧 SSoT) | 中 |

### 関連 docs

- `HELIX-workflows/helix-process/reverse-workflow.md` — fullback workflow 正本
- `docs/v2/L3-requirements/helix-workflows-functional-registry.md` — R2 成果物 (main artifact)
- `docs/v2/reverse/fullback/helix-workflows-existing-assets/F0-F4` — R0-R4 成果物群

### 関連 skill

- `skills/workflow/reverse-analysis/` (R0-R4 + RGC routing 統合)
- `skills/workflow/reverse-r0` 〜 `skills/workflow/reverse-r4` (各 phase 専門)
- `skills/workflow/reverse-rgc` (closure 確認)
- `skills/workflow/verification` (Spec 駆動検証、L1↔L14 突合)

---

## §6 R0-R4 連動 CLI コマンド (運用記録 + 今後の標準化 reference)

本 PLAN は ad hoc retrofit のため CLI 経由なしで進行したが、今後類似作業の標準化のため CLI 起動シーケンスを記録する。

```bash
# 標準フロー (今後の reference)
helix reverse fullback R0 --target HELIX-workflows  # F0-fullback-evidence.yaml
helix reverse fullback R1                            # F1-fullback-contracts.yaml
helix reverse fullback R2                            # F2-fullback-as-is-review.md
helix reverse fullback R3                            # F3-fullback-handover-checklist.yaml
helix reverse fullback R4                            # F4-fullback-routing.md
helix reverse fullback rgc                           # RGC closure 確認
```

本 PLAN の実際の進行: Wave A-G + pmo-sonnet 並列で ad hoc 実施し、後付けで成果物を `docs/v2/reverse/fullback/helix-workflows-existing-assets/` に retrofit した。

---

## §7 RGC (Reverse Gap Closure) 状態

| 項目 | 状態 |
|---|---|
| F0 evidence yaml | closed ✓ |
| F1 contracts yaml | closed ✓ |
| F2 as-is review | closed ✓ |
| F3 handover checklist | closed ✓ |
| F4 routing | closed ✓ |
| functional-registry.md 起草 | closed ✓ |
| tl-advisor adversarial check | open (次アクション) |
| PO 承認 (HO-01〜HO-08) | open (次アクション) |
| L1 back-port 3 件 | open (別 PLAN) |
| L4 carry 4 件 | open (別 PLAN) |
| Wave D (glossary-registry) | open (別 fullback PLAN) |
| L14 carry 1 件 | open (別 PLAN) |
| 段階対応 1 件 | open (条件待ち) |

closed: 6 件 / open: 7 件

**RGC 判定**: 条件付き pass — R4 routing pass 済。完全 closure は PO 承認 + 後続 PLAN/debt ID 採番後に確定。
完了条件: 全 open item の actual_route 確定 + `helix reverse fullback rgc` 起動時に open 残数 0。

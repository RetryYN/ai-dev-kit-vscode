---
plan_id: L3-helix-workflows-非機能要件plan
title: "L3-helix-workflows-非機能要件plan: HELIX-workflows V2 非機能要件 (IPA グレード値確定版)"
kind: requirements
layer: L3
drive: be
status: draft
created: 2026-05-26
owner: PM
process_layer: L3
parent_process: HELIX-workflows/helix-process/L3-requirements-definition.md
pairs_test_design:
  - docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 非機能要件の優先度・carry 判定"
  - role: pmo-sonnet
    slot_label: "PMO — IPA × ISO 25010 整合チェック"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G3 evidence)"
generates:
  - artifact_path: docs/v2/L3-requirements/helix-workflows-nfr-detail.md
    artifact_type: design_doc
dependencies:
  parent: L1-helix-workflows-非機能要求plan
  requires:
    - L0-helix-workflows-conceptplan
    - L1-helix-workflows-業務要求plan
    - L1-helix-workflows-機能要求plan
    - L1-helix-workflows-技術要求plan
    - L1-helix-workflows-非機能要求plan
    - L3-helix-workflows-業務要件plan
    - L3-helix-workflows-機能要件plan
  blocks:
    - L4-helix-workflows-基本設計plan
related_docs:
  - HELIX-workflows/helix-process/L3-requirements-definition.md
  - docs/v2/process/L03-requirements-definition-and-acceptance-test-design.md
  - docs/v2/L0-helix-workflows/concept.md
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - docs/v2/L1-requirements/helix-workflows-functional-requirements.md
  - docs/v2/L1-requirements/helix-workflows-technical-requirements.md
  - docs/v2/L1-requirements/helix-workflows-nfr.md
  - docs/plans/L3/L3-helix-workflows-業務要件plan.md
  - docs/plans/L3/L3-helix-workflows-機能要件plan.md
  - docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md
  - cli/templates/plan/v2/L03-requirements-definition-template.md
---

## §0 PLAN concept

> **工程**: L3 (L3↔L12 pair freeze)
> **正本**: HELIX-workflows/helix-process/L3-requirements-definition.md
> **本 PLAN の対象**: L1 [`helix-workflows-nfr.md`](../../v2/L1-requirements/helix-workflows-nfr.md) の NFR-AV/PF/OP/MG/SC/SE 計 23 件 + **L3 拡張 4 件** (BR-09〜12 由来: NFR-OP-06/07/08 + NFR-MG-04、2026-05-26 追加) = **計 27 件** を、**IPA 非機能要求グレード 2018 の 6 大項目ごとのグレード値 (レベル 0-5)** で確定し、L12 受入テスト設計の NFR 系 AC-NFR-* 30 件 とペア凍結 (balance_ratio = 30/27 = 1.11 ≥ 1.0、2026-05-30 PLAN-226 で ISO 25010:2023 移行 + Safety AC-NFR-SF-01 追加により 29→30) できる状態にする。L3 では target 値と測定境界を固定し、L4 で監視・実装方式を凍結する。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 参考調査: L0 concept / L1 NFR doc / L1 NFR PLAN / L3 業務要件 PLAN・製本 doc / L12 pair skeleton / requirements-deriver を読み、27 件 (L1 23 + L3 拡張 4) の確定対象と下流接続条件を整理する | ☑ completed (2026-05-26) |
| 2 | NFR-AV/PF/OP/MG/SC/SE 27 件 (L1 23 + L3 拡張 BR-09〜12 由来 4) について IPA グレード値 (0-5)・数値 target・L4/L12/L13/L14 検証境界を定義する | ☑ completed (2026-05-26、本 PLAN §2.1 / 製本 doc §1-§6) |
| 3 | ISO/IEC 25010:2023 9 特性を二軸で再掲し、L1 未掲示の 2 特性 (相互作用能力 / 機能適合性) を L3 で再導出し、安全性は網羅注記のみ追加する | ☑ completed (2026-05-26、本 PLAN §2.2 / 製本 doc §7) |
| 4 | `L1-IN-15` 逆引き audit 11 穴を L3-L4 / L7-L9 / L13-L14 の段階対応へ割り付ける | ☑ completed (2026-05-26、本 PLAN §2.3 / 製本 doc §8) |
| 5 | 製本 doc `docs/v2/L3-requirements/helix-workflows-nfr-detail.md` を起票し、Codex SE は L12 pair 編集禁止 → AC-NFR-* propose を別出力 (Opus PM が後段 Phase E.B.1 で L12 §3 に一括反映) | ☑ completed (2026-05-26、Codex SE propose → Opus L12 §3 に 29 件 detail 反映済、L3 拡張 4 件含む) |
| 6 | validator / grep / review で自己検証し、G3 evidence を残して L4 基本設計へ引き渡す | ☑ completed (2026-05-29、tl-advisor adversarial check verdict = changes_required → P1×2 (件数 23→27 / §7.1 二軸タグ表) + P2×2 (L12 §6 carry + doc 冒頭 BR-09〜12 由来明示) すべて反映、11 edit。pmo-sonnet 再 audit verdict = **approved** (D3 任意のみ)、NFR 27 件 / AC-NFR 29 件 / balance_ratio = 1.07、3 箇所 trace 成立) |

## §2 実装計画 (記載項目をどう埋めるか)

### §2.1 6 領域の IPA グレード値確定

| 領域 | 対象 NFR | L3 で確定する内容 | 下流接続 |
|---|---|---|---|
| 可用性 | NFR-AV-01〜03 | 起動成功率 / DB 整合性 / handover 復旧起点の target を **可用性レベル 3-4** で確定 | L12 受入でしきい値確認、L13/L14 で実運用観測 |
| 性能・拡張性 | NFR-PF-01〜04 | doctor / impact-range / 並列 Codex / PLAN 起票速度を **性能レベル 2-3** で確定 | L12 で初期性能確認、L13 で負荷安定性確認 |
| 運用・保守性 | NFR-OP-01〜08 (L1: 01-05 + L3 拡張 BR-09/11/12 由来: 06 inventory drift / 07 doc-reviewer 召喚 / 08 デグレ禁止 ratchet) | auto-deprecation / audit / warn 上限 / lineage / verify-before-act + inventory drift 監査 / doc-reviewer coverage / ratchet 機械強制 を **運用保守レベル 2-4** で確定 | L12 で機能有無、L14 で継続運用値を確認 |
| 移行性 | NFR-MG-01〜04 (L1: 01-03 + L3 拡張 BR-10 由来: 04 Strangler Fig 段階置換) | V1→V2 retrofit / schema migration / portable package + Strangler Fig Pattern 段階置換進捗 を **移行性レベル 2-3** で確定 | L12 で移行手順を受入、L13 で採用 project 展開性を確認 |
| セキュリティ | NFR-SC-01〜05 | secret 排除 / regen guard / tool guard / commit guard / human approval を **セキュリティレベル 3-4** で確定 | L12 で guard 有効性、L14 で逸脱 0 を継続監視 |
| システム環境 | NFR-SE-01〜03 | OS / toolchain / runtime 下限を **環境レベル 2** で確定 | L12 で matrix 確認、L13 で運用継続性を確認 |

### §2.2 IPA × ISO/IEC 25010:2023 9 特性網羅

- **現行 27 件に直接現れる特性**: 信頼性 / 性能効率性 / 保守性 / 柔軟性 / セキュリティ / 互換性
- **L3 で再導出する特性**:
  - **相互作用能力 (Interaction Capability、旧 Usability)**: HELIX-workflows は UI を持たないため「CLI usability」として再定義する。`helix help` 完備率、初回セットアップ完了時間、エラー文言の自己解決可能性を L3 の補助観点として固定し、docs site / TUI 追加時は L2/L10 unskip を trigger とする。
  - **機能適合性**: FR-* と AC-FR-* の 1:1 対応、契約逸脱の fail-close、L3 機能要件 doc と L12 機能系 AC の `balance_ratio ≥ 1.0` を機能適合性の品質観点として固定する。
- **安全性 (Safety)**: 本ドメインは該当薄、本番影響・破壊的操作シグナル時のみ現れる。
- **L3 での扱い**: 上記 2 特性は今回の 27 件へ強引に再採番せず、製本 doc §7 の **ISO 再導出観点** として記載し、AC-NFR propose で補助検証観点を追加する。

### §2.3 `L1-IN-15` 逆引き audit 11 穴の段階対応

| 段階 | 対応対象 | L3 での扱い |
|---|---|---|
| L3-L4 で確定 | 進化 / 繁殖 / 老化 / 共生 / 代謝 | `NFR-OP-04` / `NFR-MG-03` / `NFR-OP-01` / `NFR-SE-02` / `NFR-PF-04` を中心に target を確定し、L4 で監視・実装方式を凍結 |
| L7-L9 へ carry | 内分泌 / 循環 / 消化 / 性差 | 実装 telemetry、cross-mode trace、外部 OSS intake、multi-model routing として carry し、L7 実装・L8/L9 検証で受ける |
| L13-L14 へ carry | 多細胞化 / 神経変性 | team scaling と AI/hook 劣化検知の運用契約として carry し、安定性・運用検証で扱う |

## §3 成果物

- **PLAN file (本 PLAN)**: [`docs/plans/L3/L3-helix-workflows-非機能要件plan.md`](L3-helix-workflows-%E9%9D%9E%E6%A9%9F%E8%83%BD%E8%A6%81%E4%BB%B6plan.md)
- **製本 doc**: [`docs/v2/L3-requirements/helix-workflows-nfr-detail.md`](../../v2/L3-requirements/helix-workflows-nfr-detail.md)
- ~~**L12 pair propose**~~: **解消済 (2026-05-26)** — Codex SE 起票時の制約 (非編集 + propose 別出力) は完了、Opus PM が後段 Phase E.B.1 で L12 §3 に AC-NFR 29 件 (L1 25 + L3 拡張 4 由来 AC) を一括反映済。
- **ペア凍結**: L3↔L12 (非機能系 AC-NFR-* と 1:N 対応、`balance_ratio ≥ 1.0`)

## §4 DoD

- [x] L1 NFR 23 件 + L3 拡張 4 件 = 計 27 件すべてが L3 製本 doc で IPA グレード値を持つ
- [x] 6 領域 (AV / PF / OP / MG / SC / SE) すべてに target 値と検証境界がある
- [x] ISO/IEC 25010:2023 9 特性を棚卸しし、未掲示 2 特性 (相互作用能力 / 機能適合性) を再導出し、安全性は網羅注記を追加した
- [x] `L1-IN-15` 11 穴の段階対応を明示した
- [x] pair artifact path を frontmatter に固定し、L12 pair file 非編集を守った
- [x] `plan_validator.validate_plan(...)` pass (2026-05-29、WARN 1 件 = L4 PLAN 未起票は将来案件で許容)
- [x] tl-advisor / pmo-sonnet / review による最終レビュー (2026-05-29、tl-advisor: changes_required → 修正 / pmo-sonnet: **approved** with D3 任意のみ)
- [x] G3 要件凍結ゲート evidence を追記して L4 基本設計へ引き渡し (2026-05-29、NFR 27 件 / AC-NFR 29 件 / balance_ratio 1.07 / L3↔L12 pair freeze 成立) → **2026-05-30 PLAN-226 再検証**: ISO 25010:2023 移行 (8→9 特性、使用性→相互作用能力 / 移植性→柔軟性) + Safety AC-NFR-SF-01 追加 + AC-NFR-US-01 強化、tl-advisor changes_required → 反映後 NFR 27 / AC-NFR 30 / balance_ratio 1.11

## §5 関連

- **上流 PLAN**: [L1-helix-workflows-非機能要求plan](../L1/L1-helix-workflows-%E9%9D%9E%E6%A9%9F%E8%83%BD%E8%A6%81%E6%B1%82plan.md)
- **並走 L3 PLAN**: [L3-helix-workflows-業務要件plan](./L3-helix-workflows-%E6%A5%AD%E5%8B%99%E8%A6%81%E4%BB%B6plan.md)
- **製本済み L1 NFR**: [helix-workflows-nfr.md](../../v2/L1-requirements/helix-workflows-nfr.md)
- **L12 pair artifact**: [helix-workflows-acceptance-test-design.md](../../v2/L12-test-design/helix-workflows-acceptance-test-design.md)
- **HELIX-workflows 正本**: [HELIX-workflows/helix-process/L3-requirements-definition.md](../../../HELIX-workflows/helix-process/L3-requirements-definition.md)
- **template**: [cli/templates/plan/v2/L03-requirements-definition-template.md](../../../cli/templates/plan/v2/L03-requirements-definition-template.md)
- **下流 PLAN**: L4-helix-workflows-基本設計plan
- **並走 L3 PLAN 追加**: [L3-helix-workflows-機能要件plan](./L3-helix-workflows-%E6%A9%9F%E8%83%BD%E8%A6%81%E4%BB%B6plan.md) (sibling reciprocal)

## §6 L4 接続規約 (2026-05-26 tl-advisor G3 P1 #4 反映、L3 3 PLAN 共通)

- **L4 PLAN 起票時の dependencies.requires**: `L4-helix-workflows-基本設計plan` は L3 3 PLAN 全件 (業務要件 / 機能要件 / 非機能要件) を `dependencies.requires` に列挙する
- **L4↔L9 pair freeze**: L4 起票時に `docs/v2/L9-test-design/helix-workflows-system-test-design.md` (総合テスト設計) を pair artifact として同時起票し、L4 基本設計 (アーキテクチャ / ADR) と L9 総合テスト設計を pair freeze する
- **NFR 多層検証**: 本 L3 非機能要件 doc の NFR-* は L4↔L9 (総合) + L13 安定性 + L14 運用検証の **多層検証** で担保 (本 doc §8 末尾「L4/L9/L13/L14 接続方針」と整合)
- **L1-IN-14 team 構造確定**: L0 §8 L1-IN-14 (専門エージェント / team 構造) は L4 基本設計で ROI 評価 + Phase 配分確定 (本 doc の L4 carry として後段 L4 で実体化)

---
doc_id: F2-fullback-as-is-review-helix-workflows-existing-assets
title: F2 As-Is Review — HELIX framework 既存資産 548 件
type: fullback_as_is_review
reverse_type: fullback
workflow_phase: R2
plan_id: R-helix-workflows-existing-assets-fullbackplan
created: 2026-05-29
owner: PM
related_artifact:
  - docs/v2/reverse/fullback/helix-workflows-existing-assets/F0-fullback-evidence.yaml
  - docs/v2/reverse/fullback/helix-workflows-existing-assets/F1-fullback-contracts.yaml
  - docs/v2/reverse/fullback/helix-workflows-existing-assets/F3-fullback-handover-checklist.yaml
  - docs/v2/reverse/fullback/helix-workflows-existing-assets/F4-fullback-routing.md
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
audit_history:
  - 2026-05-29: PM (Opus) — F2 軽量 wrapper として起草 (本体は functional-registry.md 848 行)
  - 2026-05-29: pmo-sonnet (Wave fix-F) — tl-advisor R1 P1 反映 (件数 548 canonical 同期 + path docs/v2/reverse/ 反映)
---

# F2 As-Is Review — HELIX framework 既存資産

## §1 本 doc の位置付け

Reverse fullback workflow R2 (As-Is Design / Review) の正式成果物。本体は L3 要件定義 doc 配下の機能一覧 SSoT (`docs/v2/L3-requirements/helix-workflows-functional-registry.md`、848 行) に集約済み。本 doc は fullback workflow ファイル契約を満たすための軽量 wrapper + R2 summary を提供する。

## §2 R2 As-Is Review summary

### §2.1 対象資産 (548 件)

| カテゴリ | 件数 | path |
|---|---|---|
| CLI binaries | 80 | `cli/helix-*` (regular file + executable、`find -type f -executable` で verify) |
| CLI lib modules | 139 | `cli/lib/*.py` |
| Hooks | 17 | `.claude/hooks/*.sh` |
| Subagents | 19 | `.claude/agents/*.md` |
| Skills | 130 | `skills/**/SKILL.md` |
| HELIX-workflows doc | 49 | `HELIX-workflows/helix-process/*.md` (48) + root `HELIX-process-L0-L14.md` (1) |
| Templates | 114 | `cli/templates/**` |
| **合計** | **548** | |

> **件数訂正 note**: 初期 inventory (Wave A/B、559 件) では `ls cli/helix-*` で 94 件と数えていたが、`cli/helix-plan-cmds/` ディレクトリ配下の 12 sub-script + dir entry 2 件混入による誤計上。`find -type f -executable` で再 verify した結果、独立 CLI は 80 件 (skill 130 / workflow doc 49 / templates 114 も同様に再 verify)。

### §2.2 L1/L3 FR mapping coverage

- L1 FR 13 件 → 実装資産 mapping coverage: **100%** (13/13)
- L3 FR 18 件 → 実装資産 mapping coverage: **94% (17/18)** = 完全実装 13 件 + 部分実装 3 件 + 本 doc で部分実体化 1 件、未実装は FR-GLOSSARY-01 のみ (Wave D 候補)

### §2.3 漏れ整理 (R1 観測契約 → R2 alignment)

| 方向 | 件数 | 解消状態 |
|---|---|---|
| 逆方向 (実装あり要件なし) | 10 件 | resolved 5 / open 5 (deprecated shim 4 + helix-scrum alias 1) |
| 順方向 (要件あり実装なし) | 2 件 | 本 doc で部分実体化 1 (FR-FNREG-01) / open 1 (FR-GLOSSARY-01) |

### §2.4 As-Is 構造の特徴

- **plan / task / role / gate / handover** の 5 軸統制が CLI + hook + agent + skill すべての軸を貫通する設計
- **9 mode** (Forward / Scrum / Discovery / Reverse / Incident / Add-feature / Refactor / Retrofit / Research / Recovery) を入口判定で振り分け、すべて Forward の L0-L14 ドキュメント体系へ収束
- **V-model 4 artifact 双方向 trace** (設計 / 実装 / テスト設計 / テストコード) を 17 GA gate で機械検証
- **subagent 14 種** (PMO Sonnet 6 + PMO Haiku 3 + PdM 3 + その他 2) を許可リスト + model family 一致で fail-close
- **Codex 委譲** (TL / SE / PE / QA / Security / DBA / DevOps / Docs / Research / Legacy / Perf 等 30 ロール) と Opus PM 統制の責務分担

## §3 本体への reference

機能一覧の正本 (1 資産 = 1 行 × 548 行 + L1/L3 FR 逆引き表 + 漏れ整理表 + helix doctor 連携設計) は以下:

- **正本 doc**: [helix-workflows-functional-registry.md](../../../L3-requirements/helix-workflows-functional-registry.md)
- **L3 FR 親仕様**: FR-FNREG-01 (機能一覧 SSoT、[helix-workflows-functional-requirements-detail.md §1](../../../L3-requirements/helix-workflows-functional-requirements-detail.md))
- **L1 上位要求**: FR-09 (資産 inventory / density 可視化、[helix-workflows-functional-requirements.md](../../../L1-requirements/helix-workflows-functional-requirements.md))

## §4 R2 観点での結論

As-Is 構造は HELIX framework の宣言設計と整合しており、**重大な構造的欠陥は発見されなかった**。発見された漏れは以下の 3 カテゴリで、いずれも closure 可能:

1. **DEPRECATED shim 4 件 + legacy alias 1 件**: 廃止 milestone 未確定。R3 で PO 確認、R4 で NFR-OP-01 (auto-deprecation) へ routing。
2. **L3 FR-FNREG-01 / FR-GLOSSARY-01 の実装空き**: 本 R2 で FNREG は部分実体化、GLOSSARY は別 wave (Wave D) で実体化予定。R4 で routing。
3. **L1 FR-13 / FR-14 / FR-15 / BR-13 の back-port 候補**: L3 から L1 への補完が必要。R4 で L1 doc 改訂 PLAN へ routing。

## §5 R3 / R4 への引き継ぎ事項

- R3 PO 確認 checklist ([F3-fullback-handover-checklist.yaml](F3-fullback-handover-checklist.yaml)): 上記 3 カテゴリ × 件別 PO 質問、HO-01〜08 = 8 item
- R4 Forward routing ([F4-fullback-routing.md](F4-fullback-routing.md)): L1/L3/L4/L8-L11 のどこへ戻すかの routing 表、RGC 条件付き pass

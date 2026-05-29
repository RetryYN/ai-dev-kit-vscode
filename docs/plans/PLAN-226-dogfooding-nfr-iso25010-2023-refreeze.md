---
plan_id: PLAN-226
title: "PLAN-226: HELIX-workflows V2 dogfooding L0-L14 NFR 成果物の ISO/IEC 25010:2023 移行 + 再凍結 (frozen doc retrofit)"
layer: cross
kind: retrofit
status: completed
size: M
drive: be
created: 2026-05-30
completed_at: 2026-05-30
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — L3↔L12 pair 再検証 (balance_ratio / US→相互作用能力 再導出の妥当性) adversarial check"
  - role: docs
    slot_label: "Docs/SE — frozen NFR doc の 25010:2023 移行編集"
  - role: pmo-sonnet
    slot_label: "PMO — 移行後の数値整合・freeze metadata 確認"
generates:
  - artifact_path: docs/v2/L0-helix-workflows/concept.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L1-requirements/helix-workflows-nfr.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L3-requirements/helix-workflows-nfr-detail.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md
    artifact_type: doc_update
dependencies:
  parent: null
  requires:
    - PLAN-225
  blocks: []
related_adr: []
related_docs:
  - HELIX-workflows/helix-process/retrofit-workflow.md
  - docs/plans/recovery/recovery-2026-05-30-standards-fix-overreachplan.md
  - docs/plans/PLAN-225-iso25010-2023-standard-migration.md
related_memory:
  - reference_nfr_quality_standards_2026
  - feedback_stay_in_requested_phase_scope
---

## §0 PLAN

> **frozen doc retrofit**: HELIX-workflows V2 dogfooding の L0-L14 NFR 成果物 (L0 concept / L1-nfr / L3-nfr-detail / L12-acceptance + L1/L3 PLAN) は ISO/IEC 25010:2011 (8 特性) で凍結済。PLAN-225 で framework skill 側を 2023 版へ移行したため、dogfooding 成果物側にもドリフトが顕在化した (特に concept.md:863/865 の「25010:2023 8 特性」= バージョンと特性数の矛盾)。本 PLAN は frozen 成果物を 2023 版 9 特性へ移行し、L3↔L12 pair freeze を再検証の上で再凍結する。
> **起票根拠**: recovery-2026-05-30-standards-fix-overreach §4 + ユーザー判断「別 retrofit PLAN で再凍結を伴って移行」(2026-05-30)。

## §1 目的

frozen dogfooding NFR 成果物の ISO 25010 参照を 2011 版 8 特性 → 2023 版 9 特性へ統一し、PLAN-225 (framework skill) との整合を取る。L3↔L12 の pair freeze (balance_ratio) を移行後も成立させ、再凍結する。

## §2 背景

- PLAN-225 で skill 側 (requirements-deriver 等) を 25010:2023 へ移行 → dogfooding 成果物が 2011 版のまま取り残された
- `concept.md:863/865` は前 session が migration 途中で「25010:2023」とラベルだけ更新し「8 特性」を残した half-state (事実矛盾)
- L1-nfr / L3-nfr-detail / L12-acceptance は 2011 の 8 特性・旧名 (使用性/移植性) で一貫凍結 → 内部矛盾はないが現行標準と乖離

## §3 実装計画 (kind=retrofit、frozen → 移行 → 再凍結)

### 対象 doc 一覧
| doc | 凍結状態 | 移行内容 |
|---|---|---|
| `docs/v2/L0-helix-workflows/concept.md` (863/865) | frozen | 「25010:2023 8 特性」→「25010:2023 9 特性」+ 移行注記 (矛盾解消) |
| `docs/v2/L1-requirements/helix-workflows-nfr.md` | frozen | NFR タグ列の旧名更新 + §7 二軸タグ表 + 8→9 特性 + Safety 該当薄注記 |
| `docs/v2/L3-requirements/helix-workflows-nfr-detail.md` | frozen | 同上 + §7 + US→相互作用能力 再導出 (L3↔L12 pair) |
| `docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` | frozen | ISO 25010 再導出 (US/FS) の US→相互作用能力 + balance_ratio 再確認 |
| `docs/plans/L1/L1-helix-workflows-非機能要求plan.md` | finalized | 8→9 特性記述 |
| `docs/plans/L3/L3-helix-workflows-非機能要件plan.md` | finalized | 8→9 特性 + 旧名更新 |

**対象外**: docs/adr/ADR-035 (immutable historical citation、触らない) / process template (L01/L03) は generic 参照のため secondary (本 PLAN では触らない or 最小)

### 移行ルール (PLAN-225 と同一の正本に準拠)
- 8 特性 → 9 特性 (count)
- 使用性 → 相互作用能力 (Interaction Capability、旧 Usability)
- 移植性 → 柔軟性 (Flexibility、旧 Portability)
- 安全性 (Safety) は新規特性。dogfooding ドメイン (開発フレームワーク CLI) では「該当薄」とし、本番影響・破壊的操作シグナル時のみ「現れる」と注記 (新規 NFR は作らない)
- 日本語訳は暫定 + 英語正式名併記 (JIS X 25010:2025 未発行)
- 既存 NFR-ID / グレード値 / target は変更しない (特性名ラベルの更新のみ)

### pair 再検証 (★重要、再凍結の核心、2026-05-30 tl-advisor 実施済)
tl-advisor verdict = **changes_required** → P1×3 を反映:
- **P1-1 相互作用能力の網羅不足**: AC-NFR-US-01 を強化 (helix help 完備率 + TTFSP に加え、自己記述性=外部マニュアル無しで次アクション判明 / unknown command・error の next-step 提示 / 包摂性=NO_COLOR・--no-color 対応)
- **P1-2 Safety「該当薄」は楽観的**: HELIX は rollback/DB rollback/workspace drop の破壊的操作を持つ → 「該当薄」を撤回し「低頻度だが高影響」へ。**AC-NFR-SF-01 を ISO 再導出として追加** (fail-safe / reversibility / risk identification)。これにより **balance_ratio = AC-NFR 30 / NFR 27 = 1.11** (≥ 1.0、改善)。skill (requirements-deriver) の「破壊的操作シグナル時のみ Safety が現れる」rule に照らすと dogfooding は「現れる」ケースで、当初の該当薄判断が誤りだった
- **P1-3 status 不整合 → 再凍結で解消**: 対象 L3/L12 doc は `status: draft` だが、(a) L3 3 PLAN すべてが G3 要件凍結ゲート 2026-05-29 で「L3↔L12 pair freeze 成立」と記録、(b) 下流 L4-L6 設計 doc は既に `frozen`。**下流が frozen で上流が draft は論理破綻**であり、draft は凍結時に frontmatter を更新し忘れた clerical drift だった。「別 gate 判断で carry」は誤り (ユーザー指摘「フリーズしたから修正しない？ロジックがおかしい」)。tl-advisor の re-freeze 条件 (AC 補強) も満たしたため、**L3↔L12 pair artifact 4 doc (business/functional/nfr-detail + L12 acceptance) を `status: frozen` へ reconcile + freeze_evidence 追加**。L1 docs は L1↔L14 pair が L14 で完成する前提のため draft 維持が正しい

### 段階 rollout
1. concept 矛盾 2 行を先行修正 (最小・低リスク)
2. L1-nfr / L3-nfr-detail / L12-acceptance を移行 (Codex 委譲 + 機械 verify)
3. tl-advisor で L3↔L12 pair 再検証 (balance_ratio / US/FS)
4. L1/L3 PLAN の記述更新
5. 再凍結 evidence + commit + push

## §4 受入条件 / DoD
- [x] 対象 4 doc + 2 PLAN で 8 特性 → 9 特性、使用性→相互作用能力 / 移植性→柔軟性 (Codex SE bbz1c248b、機械 verify 済)
- [x] concept.md:863/865 の矛盾解消
- [x] L3↔L12 balance_ratio 移行後も ≥ 1.0 を tl-advisor が確認 (changes_required → 反映後 30/27 = 1.11)
- [x] Safety は「低頻度高影響」として AC-NFR-SF-01 を追加 (当初の該当薄判断を tl-advisor 指摘で撤回)
- [x] 相互作用能力の概念拡張 (自己記述性/包摂性) を AC-NFR-US-01 に反映
- [x] **再凍結実施**: L3↔L12 pair artifact 4 doc (business/functional/nfr-detail + L12 acceptance) を `status: frozen` + freeze_evidence へ reconcile (G3 2026-05-29 gate + 下流 L4-L6 frozen に整合)。L1 は L1↔L14 pair 未完成のため draft 維持が正しい
- [x] 日本語暫定訳 + 英語正式名併記

## §6 carry (本 PLAN scope 外)
- **L3↔L12 status drift は本 PLAN で解消済** (4 doc を frozen へ reconcile)。ただし他工程に同種 drift が残る可能性: L4-L6 は frozen だが、それらの pair (L9/L8/L7-test) や他 L3 doc (technical-requirements / functional-registry 等) の frozen/draft 整合は未確認 → **別途 status hygiene audit** (全 L0-L14 doc の status が gate evidence + pair freeze 記録と一致するか機械監査) を carry
- process template (docs/v2/process/L01/L03 / HELIX-workflows L1/L3) の generic「IPA 非機能要求グレード 2018 / ISO 25010」参照は総称で事実誤りなし → 任意 polish
- ADR-035 の IPA citation は immutable historical、触らない

## §5 関連 PLAN / ADR / docs
- requires: PLAN-225 (framework skill 側移行、本 PLAN は dogfooding 成果物側)
- recovery: docs/plans/recovery/recovery-2026-05-30-standards-fix-overreachplan.md
- memory: [[reference_nfr_quality_standards_2026]]

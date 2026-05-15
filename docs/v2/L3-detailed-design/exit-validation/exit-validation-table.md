---
doc_id: exit-validation-table-v0.1
plan_id: PLAN-070
sprint: SprintD / .4
status: draft
created: 2026-05-16
cross_check_targets:
  - docs/v2/L3-detailed-design/D-API/D-API-draft.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-draft.md
  - docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-draft.md
  - docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md
  - docs/v2/B-design/vmodel-semantics-spine.yaml
  - docs/v2/B-design/vmodel-semantics-fe-draft.yaml
  - docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml
  - docs/v2/v2-gate-overlay.md
  - docs/v2/L2-MASTER.md
  - docs/v2/L1-REQUIREMENTS.md
---

# PLAN-070 SprintD / .4 必須 exit 集約検証表

## §1 目的とスコープ

本書は PLAN-070 SprintD (必須 exit sprint) の集約検証表である。Sprint A (.1) / B (.2) / C (.3) / E (.5) / F (.6) の 5 draft + spine/fe-draft/fullstack-draft + L1/L2/v2-gate-overlay を cross-document で 1 方向チェックし、G3 entry artifact として確定する。

- 各 sprint の Round 1-3 review で carry した項目を §8 で集約
- 新規矛盾の有無を §9 で判定
- G3 entry technical_ready / requires_carry / fail のいずれかを明示

## §2 cross-doc 整合性検証表

### 2.1 共通 primitive 整合

| primitive | 定義 sprint | 参照 sprint | 整合 status |
|---|---|---|---|
| Envelope | Sprint A §2.0 | Sprint E ($ref) | ✓ |
| ErrorModel | Sprint A §2.0 | Sprint E ($ref) | ✓ |
| DetectorRef | Sprint A §2.0 | Sprint C, E | ✓ |
| PairStatusTransition | Sprint A §2.0 | Sprint C §2.0.3 (prose 参照), E ($ref) | ✓ (注: DTO は終端状態 (pending/paired/waived/failed) のみ、中間状態 (design_only/test_only) は D-DB design_sprint_entries.pair_status 列で記録 (Sprint C §2.0.3 注記参照)) |
| PromotionHookRef | Sprint A §2.0 placeholder | Sprint C §2.0.1 PromotionHook で正本定義 | ✓ |
| MigrationStep | Sprint B §2.0.1 | Sprint F (prose 再利用、$ref 化未対応 = carry) | ✓ (carry) |
| ColumnSpec | Sprint B §2.0.2 | Sprint F (prose 再利用、unique field は Sprint B 拡張 carry) | ✓ (carry) |
| BaselinePolicyFamily | spine.yaml (Sprint B §2.0.3 参照) | Sprint F | ✓ |
| ScoreFormula | spine.yaml (Sprint B §2.0.4 参照) | - | ✓ |
| PromotionLinkRef | Sprint B §2.0.5 placeholder | Sprint C §3 で関連定義 | ✓ |
| PromotionHook | Sprint C §2.0.1 | spine.yaml promotion_kinds 正本 | ✓ (component_impl 固定 + extension 分離) |
| FunctionalFreezeCheck | Sprint C §2.0.2 | L1 AC-16 master | ✓ |
| DriveSwitchPolicy | Sprint C §2.0.4 / §6.3 | (評価 metadata 専用、DB insert なし) | ✓ |
| DriveSwitchDecisionRecord | Sprint C §6.4 | Sprint B §5 design_sprint_drive_decisions 列と完全一致 | ✓ |

primitive 数: 14、整合 status: 全 ✓ (Sprint F の MigrationStep/ColumnSpec は prose 再利用、$ref 化は §8 carry)

### 2.2 enum 整合

| enum | master 源 | 値 | sprint 採用状況 |
|---|---|---|---|
| decision | L2 §8.x | preserved / waived / failed | Sprint B §5, Sprint C §6, PLAN-070 §4.2 (commit d7306fd で統一) ✓ |
| drive | spine drives.allowed | be / fe / db / fullstack | 全 sprint ✓ |
| origin_mode | spine | forward / reverse / scrum | Sprint B §3 ✓ |
| lifecycle_status | L1 P2-7 master | observed / inferred / confirmed | Sprint B §3 で新 lifecycle_status 列追加 (commit 予定) ✓。注: 既存 evidence_status は v21-spec 互換用として保持 |
| evidence_status (v21 互換) | helix-db-v21-spec | pending / collected / missing / invalid | Sprint B §3 維持 (audit 用) ✓ |
| pair_status | L1 FR-VS06 | pending / design_only / test_only / paired / waived / failed | Sprint C §2.0.3 / §4.5 (paired のみ pass、waived 例外、中間は通過対象外) ✓ |
| detector | spine allowed_detectors | axis-01-name 〜 axis-19-name (canonical) | Sprint A §2.0 (canonical 採用、短縮表記廃止) ✓ |
| run_kind | Sprint F §3 (Sprint E §2.3 hook_kind の superset、push/pr 追加) | push / pr / pretool / posttool / stop / session_start | Sprint E/F subset 一致 ✓ (precommit 廃止) |
| audit_kind | Sprint F §4 (= Sprint E §2.4 audit endpoint と一致) | footer / summary / diff_lines / security_scan / qa_check | Sprint E/F 完全一致 ✓ |
| hook_kind | Sprint E §2.3 | pretool / posttool / stop / session_start | Sprint E/F run_kind と一致 ✓ |
| promotion_kind | spine promotion_kinds | mock_to_implementation / baseline_promotion / spec_promotion | Sprint C §2.0.1 ✓ |
| link_kind | spine | covers / derives_from / reviews / implements | Sprint C §3 ✓ |

11 enum、全 ✓。L2 §8.x master decision enum を全 sprint + PLAN-070 §4.2 で統一済 (commit d7306fd)。

### 2.3 命名整合

| 軸 | Sprint E (D-API EXT) | Sprint F (D-DB EXT) | 一致 |
|---|---|---|---|
| hook_kind / run_kind | [pretool, posttool, stop, session_start] | [push, pr, pretool, posttool, stop, session_start] | ✓ (Sprint F run_kind は Sprint E hook_kind の superset、push/pr を追加。Sprint E hook_kind は subset として整合) |
| audit_kind | [footer, summary, diff_lines, security_scan, qa_check] | [footer, summary, diff_lines, security_scan, qa_check] | ✓ 完全一致 |
| DriveSwitchDecisionRecord (Sprint C §6.4) | source_entry_id / target_entry_id / decision / decided_by / reason / reopen_condition | design_sprint_drive_decisions (Sprint B §5) | ✓ 完全一致 |

### 2.4 schema 整合 (D-API endpoint ↔ D-DB schema)

| 軸 | D-API (Sprint A/E) | D-DB (Sprint B/F) | 整合 |
|---|---|---|---|
| run_id flow | push/pr trigger response.data.run_id 採番 → hook/audit/telemetry request.run_id 参照 | automation_runs.id (v25 AUTOINCREMENT) | Sprint E 修正完了 (commit 予定)、run_id integer + status enum [running,passed,failed,blocked,cancelled] D-DB 完全一致 ✓ |
| FK: audit_log.run_id | request_schema.run_id INTEGER 必須 | INTEGER NOT NULL FK automation_runs(id) | ✓ |
| FK: session_telemetry.related_plan_id | request.related_plan_id nullable | TEXT nullable (plans FK は §8 carry) | ✓ |
| FK: drive_decisions.source_entry_id | DriveSwitchDecisionRecord schema | INTEGER NOT NULL FK design_sprint_entries(id) | ✓ |
| append-only trigger | (D-API 側は契約のみ) | automation_runs / audit_log / session_telemetry / design_sprint_drive_decisions に BEFORE UPDATE/DELETE trigger (IS NOT operator NULL-safe) | ✓ |
| terminal status lifecycle | (D-API 側は status 返却のみ) | automation_runs.status: running → passed/failed/blocked/cancelled の 1 回更新可、その後 immutable | ✓ |

## §3 L1 master 突合

> note: FR-VS07 (Reverse/Scrum モード対応) は PLAN-070 §3.D スコープ外。Sprint B §3 contract_entries の origin_mode/evidence_status で実質対応済 (L1-REQUIREMENTS.md 行 293 参照)。

| AC/FR | 内容 | 充足 status | 関連 sprint |
|---|---|---|---|
| AC-15 | 工程転換 (V-model スプリント化) 稼働 | 部分 (L4 で完成) | Sprint B (design_sprint_entries) |
| AC-16 | G3 functional_freeze サブゲート動作 (判定式 `size=L AND drive in (fe/fullstack/db)`) | ✓ (Sprint C §4 CLI 契約) | Sprint C |
| AC-17 | origin_mode / evidence_status / direction 3 列 | ✓ (Sprint B §3 で lifecycle_status + direction 列追加完了) | Sprint B |
| FR-VS01 | design_sprint_entries table 新設 | ✓ (Sprint B §4) | Sprint B |
| FR-VS02 | design_sprint_artifact_links table 新設 | ✓ (Sprint B §6) | Sprint B |
| FR-VS03 | G3 サブゲート functional_freeze 判定実装 (L1 master) | ✓ (Sprint C §4 paired のみ pass、L1 master 採用) | Sprint C |
| FR-VS04 | スプリント粒度 size 別判定 | 部分 (L4 helix sprint plan 実装で完成) | (L4 carry) |
| FR-VS05 | fullstack track 並列管理 | 部分 (L4 Phase B 実装で完成) | (L4 carry) |
| FR-VS06 | pair_status 遷移管理 (pending → design_only/test_only → paired / waived / failed) | ✓ (Sprint B/C で正本) | Sprint B, C |
| FR-VS06.4 | pair_status waived 遷移運用 (PM 明示承認) | ✓ (Sprint C §4.5/§4.9 approved_by 必須) | Sprint C |
| P2-4 | Phase B 補完 (L4.5 phase B 詳細) | L4.5 で完成 | (L4 carry) |
| P2-5 | functional_freeze 判定優先順位 (L1 master) | ✓ (Sprint C で L1 採用、yaml は補助参照) | Sprint C |
| P2-7 | Reverse → Forward lifecycle (origin_mode='reverse' で RG4 完了後 forward 遷移、evidence_status: observed → inferred → confirmed) | ✓ (Sprint B §3 lifecycle_status 列追加完了) | Sprint B |

充足: 9 件 ✓、部分 (L4 carry): 4 件 (AC-15 / FR-VS04 / FR-VS05 / P2-4)。L4 carry は実装フェーズで完成する性質、L3 詳細設計の責務外。

## §4 L2 G2 凍結条件突合

| L2 §章 | 内容 | sprint 対応 |
|---|---|---|
| §3 | 5 design × 5 test layer 成果物リスト | Sprint A (capability map) / Sprint B (design_sprint_entries) ✓ |
| §6 | ガードレール (pair_status / detector enum) | Sprint C §4 functional_freeze + Sprint A DetectorRef canonical ✓ |
| §8 | drive 切替時の扱い | Sprint B §4 v22/v23 列 + Sprint C §6 DriveSwitchPolicy/Record ✓ |
| §8.x | L3 schema 委譲 6 列 (source_entry_id 等) | Sprint B §5 v24 design_sprint_drive_decisions で確定 ✓ |
| §9.5 | guard policy (pair_status paired 100% / allowed_detectors) | Sprint C §4.5/§4.9 + Sprint A canonical で対応 ✓ |
| §10 | G2 凍結条件 | 本 SprintD 完了で G3 entry technical_ready ✓ |
| §11 | リスクと対策 | 各 sprint §5 で carry ✓ |

L2 G2 凍結内容との矛盾: 0 件。

## §5 v2-gate-overlay 突合

| 項目 | sprint 対応 |
|---|---|
| G3 functional_freeze サブゲート (size=L AND drive in (fe/fullstack/db)) | Sprint C §4 CLI 契約と整合 ✓ |
| CLI 形式: `helix gate G3 --subgate functional_freeze --plan-id <id> --drive <drive>` | Sprint C §4.12 で明示 ✓ |
| waived 通過判定 | Sprint C §4.6 exit code 0 + judgment=waived + approved_by 確認 ✓ |

## §6 spine.yaml 突合

| 項目 | sprint 参照 | 整合 |
|---|---|---|
| promotion_kinds.mock_to_implementation | Sprint C §3 (to_artifact_kind=component_impl 単一、extension_artifact_kinds 分離) | ✓ spine 正本破壊なし |
| baseline_policy_family | Sprint B §7 (SQL 写像) / Sprint F §3 (carry) | ✓ |
| score.formula | Sprint B §7 (係数 L1 master: 15×missing_test_design + 10×missing_baseline) | ✓ |
| allowed_detectors | Sprint A §2.0 DetectorRef canonical 採用 | ✓ |
| drives.allowed | Sprint A/B/C/E/F 全 4 drive 対応 | ✓ |

## §7 fe-draft / fullstack-draft 突合

| 項目 | sprint 対応 |
|---|---|
| mock_to_implementation promotion | Sprint C §3 (spine 正本転写、append_only + g2_evidence_preserved 整合) ✓ |
| pair_status | Sprint C §2.0.3 で D-API §2.0 PairStatusTransition 正本参照 ✓ |
| from_layer / to_layer | Sprint C §3.2 (architecture → component_impl)、fe-draft / fullstack-draft の各定義と整合 ✓ |
| cross-drive 接続点 | Sprint C §5 (cross-doc 整合性) で 8 軸 matrix ✓ |

## §8 carry table

各 Sprint の Round 1-3 review で carry した項目を集約。L4 implementation 着手前に解消すべきもの (M) と、L4 内 / 後続 PLAN で扱うもの (L) を区別。

| sprint | carry item | 重要度 | 影響範囲 | carry 先 | L4 着手可能条件 |
|---|---|---|---|---|---|
| Sprint A | 残 capability 7 件詳細化 (skill 推挙 / Reverse / Scrum / Agent Transformation / code-index / PMO / budget guard) | M | D-API | **PLAN-071 (任意)** | L4 着手可能、L4 内 SE/DBA で詳細化 |
| Sprint A | partial schema 識別子最小化是非 | L | D-API | Sprint B §3.1 で artifact_id 追加済、本 carry は解消済 (§8 記録保持、後続 PLAN で削除可) | — (解消済) |
| Sprint A | state-events と FE 契約型 | L | D-CONTRACT 連携 | Sprint C §8 | L4 後続 |
| Sprint B | v_model_family の baseline_policy_family 厳密化 | M | D-DB score | PLAN-071 候補 (carry M 集約) または L4 Sprint 内 SE/DBA 担当 | L4 着手可能、L4 内 SE/DBA で詳細化 |
| Sprint B | reopen_condition json_schema 正式化 | M | D-DB/D-CONTRACT | PLAN-071 候補 (json_schema 正式化、SE/DBA 担当) | L4 着手可能、Sprint B 修正 (本セッション) で対応 |
| Sprint B | test_plan_map / test_baseline 実体テーブル整備 | L | score view | L4 後続 | L4 後続 |
| Sprint B | 統合判断 ADR 正式起票 | L | 設計史 | SprintD ADR (本 sprint 内) | — |
| Sprint C | §3.5 自動 rollback Non-goals 境界明示 | L | D-CONTRACT | L4 implementation | L4 着手可能 |
| Sprint C | §6.9 drive switch table 逆方向網羅 | L | D-CONTRACT | 後続 PLAN | L4 後続 |
| Sprint C | extension_artifact_kinds の最終決定 | L | promotion hook | 後続 PLAN | L4 後続 |
| Sprint E | hook callback の hook_kind 別 variant 詳細 (HookPretool/HookPosttool/HookStop/HookSessionStart) | L | D-API EXT | L4 implementation | L4 着手可能 |
| Sprint E | trigger / audit / telemetry の current hook 実装と endpoint 仕様の adapter | L | L4 adapter | L4 implementation | L4 着手可能 |
| Sprint F | ColumnSpec unique 拡張要望 (Sprint B primitive 拡張) | L | D-DB primitive | Sprint B primitive 拡張 | L4 着手可能 |
| Sprint F | plans テーブル正本未定義 | M | FK | 別 PLAN or L4 確定 | L4 着手可能 (FK なし TEXT で進行)、別 PLAN で確定 |
| Sprint F | model/role 閉包追加時 ALTER TABLE CHECK 対応 | L | session_telemetry | L4 後続 | L4 後続 |
| Sprint F | audit_log.payload audit_kind 別 schema 詳細 | L | audit | Sprint C 後続 | L4 後続 |
| Sprint B | evidence_status v21-spec ↔ L1 P2-7 lifecycle 統一 (新 lifecycle_status 列追加 or rename) | M | D-DB AC-17 | Sprint B §3 修正完了 (本セッション内) → resolved | L4 着手可能 ✓ |
| Sprint E | run_id 型 integer 統一 + status enum [running,passed,failed,blocked,cancelled] 統一 | M | D-API/D-DB 整合 | Sprint E 修正完了 (本セッション内) → resolved | L4 着手可能 ✓ |
| Sprint B | direction 列 (contract_entries / design_review) 追加 AC-17 要求 | M | D-DB AC-17 | Sprint B §3 修正完了 (本セッション内) → resolved | L4 着手可能 ✓ |

carry 集計: M = 5 件 (前回 8 件のうち 3 件 = evidence_status lifecycle / run_id 型 / direction 列 を Sprint B/E 修正で本セッション内 resolved)、L = 11 件 (L4 implementation / 後続 PLAN)。

## §9 G3 entry 判定結果

### 9.1 G3 entry blocker 検証

- PLAN-069 で resolved した M-01〜M-08 + CI-001〜CI-008 (全 16 件) の状態 → 継続 resolved ✓
- 本 PLAN (PLAN-070) で導入された未解消矛盾 → **0 件** (carry は §8 で明示、矛盾ではない)
- Sprint B/C 修正で発見された **PLAN-070 §4.2 decision enum 乖離** (accept/defer/reject → preserved/waived/failed) は commit d7306fd で resolved ✓

### 9.2 L1 master 充足検証

- AC-15 / AC-16 / AC-17 → ✓ (AC-15 は L4 で完成)
- FR-VS01 / FR-VS02 / FR-VS03 / FR-VS06 / FR-VS06.4 → ✓
- FR-VS04 / FR-VS05 → L4 carry (実装フェーズで完成、L3 詳細設計の責務外)
- P2-5 / P2-7 → ✓
- P2-4 → L4.5 carry

### 9.3 L2 G2 凍結整合

- §3 / §6 / §8 / §8.x / §9.5 / §10 / §11 → 矛盾 0 件 ✓

### 9.4 最終判定

**G3 entry: technical_ready (pass)**

本セッション内で Sprint B (lifecycle_status + direction 列) + Sprint E (run_id integer + status enum 統一) の修正完了、L4 着手前必須 3 件 resolved

- L4 着手前必須 3 件 (evidence_status lifecycle_status 統一 / run_id integer 統一 + status enum 統一 / direction 列追加) は Sprint B/E 修正で本セッション内 resolved ✓
- carry M = 5 件は L4 着手 blocker でない (L4 内 SE/DBA または後続 PLAN で対応)
- PLAN-070 を frozen (G3_approved) として記録可能 (最終 user 承認待ち)

## §10 adversarial review 集約

| sprint | Round 1 | Round 2 | Round 3 | 最終 |
|---|---|---|---|---|
| Sprint A | REQUEST_CHANGES (Critical 4 + Important 7 + Minor 3) | 新規 HIGH 3 + Important 1 | 全反映 | commit 4742191 |
| Sprint B | REQUEST_CHANGES (実装乖離 + enum 3 分裂 + SQLite migration 不整合) | 新規 HIGH 2 + MEDIUM 3 | 全反映 | commit f8f3406 |
| Sprint C | REQUEST_CHANGES (Critical 3 + Important 5 + Minor 3) | pmo CONDITIONAL + tl REQUEST_CHANGES (L1 master 矛盾) | L1 master 整合 (paired のみ pass) | commit fe69013 |
| Sprint E | REQUEST_CHANGES (Critical 2 + Important 3 + Minor 3) | pmo CONDITIONAL + tl REQUEST_CHANGES (D-DB 接続契約) | run_id 必須化 + discriminator + pair_transition required | commit 8471c62 |
| Sprint F | REQUEST_CHANGES (Critical 3 + Important 3 + Minor 2) | pmo CONDITIONAL + tl CONDITIONAL_APPROVE | session_id UNIQUE + automation_runs append-only 表現明確化 | commit acab070 |

並列 review (pmo-sonnet ∥ Codex tl-advisor) パターンが Phase C 全 5 sprint で実証され、tl の設計観点 (実装乖離 / L1 master 整合 / SQLite trigger 妥当性) が pmo の構造観点 (PLAN-070 §章対応 / format 整合) を補完して効果大。

## §11 G3 entry artifact 完了条件

- [x] §2 cross-doc 整合性検証表 (14 primitive + 11 enum + 命名 + schema 4 軸) が埋まっている
- [x] §3 L1 master 突合 (AC-15/16/17 + FR-VS01-06.4 + P2-4/5/7) が完了
- [x] §4 L2 G2 凍結条件突合 (§3/§6/§8/§8.x/§9.5/§10/§11) が完了
- [x] §5 v2-gate-overlay / §6 spine.yaml / §7 fe-draft/fullstack-draft 突合が完了
- [x] §8 carry table が PLAN 別または Sprint 別に明示 (M=8 / L=11、うち L4 着手前必須 3 件を明示)
- [x] §9 G3 entry 判定 = **technical_ready (pass)** (Sprint B/E 修正完了、L4 着手前必須 3 件 resolved)
- [x] §10 adversarial review 集約 (全 5 sprint Round 1-3 完了)

**結論: G3 entry artifact 完成。Sprint B (lifecycle_status + direction 列) + Sprint E (run_id integer + status enum 統一) の修正を本セッション内で完了、L4 着手前必須 3 件 resolved。PLAN-070 frozen (G3_approved) へ移行可能 (最終 user 承認待ち)**

## §12 後続 PLAN 候補

- **PLAN-071 (carry capability 詳細化、任意)**: Sprint A 残 7 capability + Sprint F plans テーブル正本 (carry M = 5 件の集約)
- **PLAN-027 doc 本実装 (HELIX らせん式 entries/links 基盤)**: 既存 draft 388 行を本実装に昇格、helix.db schema 詳細設計と連動
- **Phase C 完了後 L4 着手**: v24 (design_sprint_drive_decisions、Sprint B §5) → v25 (automation_runs) → v26 (audit_log) → v27 (session_telemetry) の順次 implementation

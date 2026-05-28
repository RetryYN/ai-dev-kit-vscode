---
doc_id: F4-fullback-routing-helix-workflows-existing-assets
title: F4 Forward Routing — HELIX framework 既存資産 fullback
type: fullback_routing
reverse_type: fullback
workflow_phase: R4
plan_id: R-helix-workflows-existing-assets-fullbackplan
created: 2026-05-29
owner: PM
forward_connection_target:
  - L1 要求定義: BR-13 / FR-14 / FR-15 back-port
  - L3 要件定義: FR-FNREG-01 部分実体化 + FR-GLOSSARY-01 実体化
  - L4 基本設計: 4 carry (deprecated shim milestone / helix-scrum 廃止 / NFR-OP-01 拡張 / CLI doc 補強)
  - L8-L11 fullback 統合: closure 確認のみ
related_artifact:
  - docs/v2/reverse/fullback/helix-workflows-existing-assets/F0-fullback-evidence.yaml
  - docs/v2/reverse/fullback/helix-workflows-existing-assets/F1-fullback-contracts.yaml
  - docs/v2/reverse/fullback/helix-workflows-existing-assets/F2-fullback-as-is-review.md
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
audit_history:
  - 2026-05-29: pmo-sonnet (Wave R4) — Forward routing 起草。F3 未生成につき R2 §4/§5 引き継ぎ事項を HO-ID に展開して代替
  - 2026-05-29: pmo-sonnet (Wave fix-D) — tl-advisor R1 P1-4/P1-5/P2-1/P2-2 反映 + path update (related_artifact)
---

# F4 Forward Routing — HELIX framework 既存資産 fullback

## §1 routing summary

R2 §4 結論 + §5 引き継ぎ事項 (F3 代替) から抽出した 8 HO-item を Forward HELIX の戻し先別に分類する。

| Forward 戻し先 | HO item 数 | 含まれる asset 数 | 例 |
|---|---|---|---|
| L1 doc 改訂 (back-port) | 3 | 3 (FR-FNREG / FR-GLOSSARY / BR-RULE-13) | HO-01 / HO-02 / HO-03 |
| L3 拡張 (Wave 内追加実体化) | 1 | 1 (glossary-registry.md) | HO-02 / HO-07 (重複) |
| L4 carry (基本設計 / framework 拡張) | 4 | 7+ (helix doctor 3 check + deprecated 4 shim + helix-scrum alias + workflow doc 補強) | HO-04 / HO-05 / HO-07 / HO-08 |
| L8-L11 fullback closure (RG3 pass) | 1 | 5 (resolved 5 件まとめ) | HO-06 |
| **合計** | **8 HO item** | **16+ asset** | |

注: HO-02 / HO-07 は L1 back-port と L3 拡張の両方に跨るため重複カウント。

---

## §2 routing 詳細表

### §2.1 L1 doc 改訂 (back-port) — 3 件

R2 §4 カテゴリ 3「L1 FR-13/FR-14/FR-15/BR-13 back-port 候補」の内、実作業が必要な 3 件。

| HO-ID | 対象 L1 ID | back-port 内容 | 推奨 PLAN | 優先度 |
|---|---|---|---|---|
| HO-01 | FR-14 | 機能一覧管理 SSoT (本 R2 で実体化済の functional-registry.md を L1 側に明示) | L1-helix-workflows-機能要求plan 改訂 sprint で消化 | medium |
| HO-02 | FR-15 | 用語一覧管理 SSoT (glossary-registry.md 起草後に L1 側に明示) | 同上 + Wave D glossary 起草 (本 session 内) | high |
| HO-03 | BR-13 | PdM 提案統合業務 (PdM subagent 3 種の統制設計を L1 BR 側に明示) | L1-helix-workflows-業務要求plan 改訂 | low |

back-port の性質: いずれも L3 以降で機能が実体化されているが L1 doc に対応記述が薄い。PO 判断で「L3 trace 追記のみで closure」を選べば L1 改訂不要 (→ G1 invalidate 不要)。

### §2.2 L3 拡張 (Wave 内追加実体化) — 1 件

R2 §4 カテゴリ 2「FR-GLOSSARY-01 の実装空き」の解消。

| HO-ID | 対象 FR | 実体化作業 | 推奨タイミング | 優先度 |
|---|---|---|---|---|
| HO-02 / HO-07 | FR-GLOSSARY-01 | `docs/v2/L3-requirements/helix-workflows-glossary-registry.md` 新規起草 (800-1000 行想定)。L0 §12 Glossary skeleton 19 用語の昇格 + 関連用語追加 + helix doctor `check_glossary_coverage` 設計 | 本 session 内 (Wave D) または次 session 最優先 | high (mapping coverage 80% 未達、FR 実装空き) |

### §2.3 L4 carry (基本設計 / framework 拡張) — 4 件

R2 §4 カテゴリ 1「DEPRECATED shim + legacy alias」と R2 §5 引き継ぎのうち設計判断を要する 4 件。

| HO-ID | 対象 NFR / 資産 | carry 内容 | 推奨 PLAN | 優先度 |
|---|---|---|---|---|
| HO-04 | NFR-OP-01 (auto-deprecation) | DEPRECATED shim 4 件 **(helix-check-claudemd / helix-gate-api-check / helix-hook / helix-session-start)** の廃止 milestone (リリース番号) 確定 + `helix doctor check_deprecated_shim_milestone` 実装 | L4-helix-workflows-基本設計plan §carry に追記 | medium |
| HO-05 | helix-scrum alias | `helix scrum` → `helix discovery` 完全移行の廃止リリース番号確定 + SKILL_MAP §6 / CLI ヘッダー明記 | 同上 | low |
| HO-07 | helix doctor 拡張 | `check_functional_registry` / `check_fr_sot_alignment` / `check_glossary_coverage` の 3 check 関数を helix-doctor に追加 (functional-registry.md + glossary.md との突合機構) | L4 carry (基本設計 + L7 実装 Sprint) | high |
| HO-08 | reverse-workflow.md | `HELIX-workflows/helix-process/reverse-workflow.md` §基本フロー に fullback type 起動シーケンス追加 (`helix reverse fullback R0 → R1 → R2 → R3 → R4` 例コマンド列) | L4 carry: workflow doc 拡張 (docs/v2 または HELIX-workflows 更新) | low |

### §2.4 L8-L11 fullback closure (RG3 pass) — 1 件 (5 件まとめ)

R2 の trace 追記により already-resolved となった資産群。PO 承認をもって closure 確定。

| HO-ID | 対象資産 | closure 内容 | 確認方法 | 優先度 |
|---|---|---|---|---|
| HO-06 | helix-test / helix-test-debug / helix-bats-cleanup / assets 7 file (`.helix/` 管理) / folder-structure-review.md | 本 R2 で functional-registry.md §12.1 に trace 追記済。PO 承認のみ残 | functional-registry.md §12.1 の `resolved: true` 列確認 | low (resolved 確認のみ) |

---

## §3 Forward 接続マッピング

`reverse-workflow.md §Forward 接続` 表との対応:

| Reverse の結論 | Forward 側戻し先 | 本 fullback の該当 item |
|---|---|---|
| 要件そのものが曖昧 | L1 要求 / L3 要件 (helix plan 前に再定義) | HO-01 / HO-02 / HO-03 (back-port) |
| 設計判断が不足 | L4 基本設計 (ADR / design-doc) | HO-04 / HO-05 / HO-07 / HO-08 |
| API / DB / contract が不明 | L5 詳細設計 | (該当なし、本 fullback では出現せず) |
| 実装だけで閉じる | L7 実装 (sprint) | (該当なし) |
| 運用・受入・文書整合 | L8-L11 (fullback) | HO-06 (RG3 closure) |

---

## §4 invalidate-forward 判定

本 fullback の結果が Forward の既存 gate 前提を崩すかを評価する。

| Gate | 判定 | 根拠 |
|---|---|---|
| **G1 (L1 要求完了ゲート)** | **invalidate 候補** | HO-01 / HO-02 / HO-03 の back-port を確定するなら L1 doc 改訂が必要 → G1 再判定。PO 判断で「L3 trace のみ closure」を選べば invalidate 不要 |
| **G3 (L3 要件凍結ゲート)** | **条件付き invalidate** | (a) 本 R2 で FR-FNREG-01 / FR-GLOSSARY-01 は L3 既採択、trace 補完のみなら G3 不要 / (b) Wave D で `helix-workflows-glossary-registry.md` 起草時、新規 FR / AC / 判定基準を追加するなら G3 再判定候補 |
| **G4 (L4 基本設計凍結ゲート)** | **invalidate 不要** | L4 doc 未起票のため G4 判定前。carry 4 件を取り込んだ後に G4 判定する正順を維持 |

**判定まとめ**: G1 のみ PO 判断次第で invalidate 候補。G3 は Wave D の追加内容次第 (catalog 実体化のみなら不要、新 FR/AC 追加なら再判定)。G4 は不要。

---

## §5 RGC (Reverse Gap Closure) 判定

R4 で routing した item の closure 状態:

| 状態 | 件数 | item |
|---|---|---|
| closed (本 R2 で resolved) | 5 | HO-06 まとめ (helix-test / helix-test-debug / helix-bats-cleanup / assets 7 file / folder-structure-review.md) |
| open (Forward L4 carry へ) | 4 | HO-04 / HO-05 / HO-07 / HO-08 |
| open (Forward L1 back-port へ) | 3 | HO-01 / HO-02 / HO-03 |
| open (Wave D 別実体化へ) | 1 | HO-02 / HO-07 重複 |

合計 closed 5 / open 7。

**RGC pass 状態**: **条件付き pass (R4 routing pass、RGC closure は PO 承認 + 後続 PLAN / debt ID 採番後に確定)**

reverse-workflow.md §85 の規定:「open / partial を Forward の debt / readiness defer / 新規 plan に戻す」を遵守。本 R4 で全 open item に Forward route 候補は紐付いたが、以下が確定するまで RGC pass は **条件付き**:

| 残作業 | 完了条件 |
|---|---|
| PO 承認 (8 HO item) | 各 HO の actual_route 確定 |
| L1 back-port PLAN 採番 | HO-01 / HO-02 / HO-03 を含む後続 PLAN ID 採番 |
| L4 carry 採番 | HO-04 / HO-05 / HO-07 / HO-08 を `L4-helix-workflows-基本設計plan` §carry に取り込み |
| Wave D 起票 (任意) | HO-02 / HO-07 を `R-helix-workflows-glossary-registry-fullbackplan.md` として別 fullback 起票 (代替: L4 carry に統合) |

**条件未充足の場合**: 該当 open item は debt registry へ追加し、`helix reverse fullback rgc` 起動時に open 残数で fail-close する。

---

## §6 次アクション

### §6.1 本 session 内で完遂したいアクション

| 優先 | アクション | 担当 |
|---|---|---|
| 1 | Wave D: `docs/v2/L3-requirements/helix-workflows-glossary-registry.md` 起草 (HO-02 / HO-07 解消、FR-GLOSSARY-01 実体化) | PM → Codex docs |
| 2 | `R-helix-workflows-existing-assets-fullbackplan.md` PLAN doc 起票完了 | PM |
| 3 | tl-advisor R1 adversarial check + pmo-sonnet audit (本 R4 + PLAN doc) | PM |
| 4 | commit chain (F4 + PLAN doc + Wave D 成果) + push | PM |

### §6.2 別 PLAN として起票推奨

| PLAN 候補 | scope | 優先度 |
|---|---|---|
| `L1-helix-workflows-back-portplan` | HO-01 / HO-02 / HO-03 まとめ (FR-14 / FR-15 / BR-13 back-port、L1 doc 改訂) | medium (PO 判断待ち) |
| `L4-helix-workflows-基本設計plan` §carry 追記 | HO-04 / HO-05 / HO-07 / HO-08 (deprecated milestone / helix doctor 3 check / workflow doc 拡張) | high (HO-07) / low (HO-05 / HO-08) |

### §6.3 helix doctor 連携 carry (L4 後段 L7 で実装)

- `check_functional_registry`: `docs/v2/L3-requirements/helix-workflows-functional-registry.md` SSoT と実コードの突合 (HO-07)
- `check_fr_sot_alignment`: L1/L3 FR mapping coverage 検証 (HO-07)
- `check_glossary_coverage`: `helix-workflows-glossary-registry.md` と doc 内用語の突合 (HO-07)
- `check_deprecated_shim_milestone`: deprecated 資産の廃止 milestone 明記検証 (HO-04)
- `check_legacy_alias_milestone`: legacy alias 廃止リリース明記検証 (HO-05)

---

## §7 Forward HELIX への戻し方 (実務手順)

1. 本 R4 routing 表を読み、PO 判断で各 HO-item の `actual_route` を確定
2. **L4 carry 4 件** は既存 L4 plan (または新規 `L4-helix-workflows-基本設計plan`) の §carry section に追記
3. **L1 back-port 3 件** は PO 判断で要否確定 → 必要なら `L1-helix-workflows-back-portplan` を新規起票 (別 session 可)
4. **Wave D** は本 session 内で起草可能なら実施 (FR-GLOSSARY-01 実体化、HO-02 / HO-07 両方を解消)
5. `R-helix-workflows-existing-assets-fullbackplan.md` を commit + push
6. `helix reverse fullback rgc` (または相当コマンド) で closure 確認 → RGC pass 記録

---

## §8 closure note

本 fullback workflow は HELIX framework 548 資産 × L1/L3 要件 56 ID の双方向 trace を完成させた。

**総括**:
- 構造的欠陥: **0 件** (As-Is 構造は宣言設計と整合)
- back-port 候補: **3 件** (HO-01/02/03、PO 判断で L1 改訂 or L3 trace closure を選択)
- L4 carry: **4 件** (HO-04/05/07/08、うち HO-07 が最優先)
- Wave 内実体化: **1 件** (HO-02/07 重複、glossary-registry.md)
- L8-L11 closure (resolved): **5 件** (HO-06 まとめ)

Forward HELIX の次ステップは **Wave D (glossary-registry.md 起草)** または **L4 carry 反映 (`L4-helix-workflows-基本設計plan` §carry 追記)** のいずれか (PO 判断)。G1 invalidate については back-port 方針確定を待つ。

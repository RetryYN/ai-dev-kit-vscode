# HELIX V3 — FE/UI 設計（FE ガバナンスを harness から盗む）

> **status: 再構築中**（charter D7 訂正反映） / base SSoT = [capture §5/§6](../audit/2026-06-26-new-base-comprehensive-capture.md)。
> **訂正（2026-06-26）**: 旧「fork は src/web 空 = FE は HELIX 最大の優位」は**誤り**。最新 clean harness は FE 設計**ガバナンス**を機械契約済で保有（document-system-map §1c per-layer / frontend-design-coverage / screen-impl-pair-freeze / tokens.yaml SSoT / screens table / design-bottomup）。**空なのは実 UI 描画（src/web）だけ** = そこのみ greenfield。
> 接続: [L5 §1 screens/screen_trace](../L0-L14/L5-detailed-design.md) / [L6 FN-DET-13](../L0-L14/L6-functional-design.md) / [engine C6 駆動 mode](../engine/doc-workflow-rules.md)。

## 0. 方針

FE は HELIX 独自優位でなく、**harness の FE ガバナンスを忠実に盗む**（Python 化）。HELIX が後乗せできる追加優位（state-events 駆動の BE/FE 契約・axis-15〜19 の視覚/a11y/visual detector）は **capture 後の HELIX 独自強化フェーズ**で上乗せ（§6）。

## 1. FE 設計 doc の per-layer 降下（document-system-map §1c — 左腕を機械担保）

harness §1c が per-layer FE 設計 doc を定義し、`frontend-design-coverage` detector が schema VALID_SUB_DOCS + §1c doc + 実ファイルの **3 者整合**で fail-close する。

```
L1 screen-requirements → L2 screen設計(screen-list/flow/ui-element/wireframe, G2)
  → L3 screen-functional → L4 ui-standard + tokens.yaml(デザイントークン SSoT)
  → L5 ui-detail(FE内部設計) → L6 screen-spec(per-screen 機能設計)
  → L7 src/web 実装（★唯一の greenfield） → L10 visual-design(UX 磨き/WCAG)
```

- **slot 登録 ≠ body 完成**（coverage ≠ substance）。`frontend-design-coverage` は「定義 + slot 整合」まで担保（schema から slug 消失 / 既存 FE doc 消失 / §1c から descent 鎖消失を absence-blindness させない、anchor marker = §1c / src/web）。
- **VALID_SUB_DOCS FE slug**: L1 `screen` / L2 `screen-list,screen-flow,ui-element,wireframe` / L3 `screen-functional` / L4 `ui-standard` / L5 `ui-detail` / L6 `screen-spec`。
- **tokens.yaml = L4 デザイントークン SSoT**（hex/px 実値、`data`(DB 設計標準)の FE 対応物）。impl 前に必要な FE 設計標準のため L4 配置（L10 でない）。src/web は token を唯一の出典に参照（ハードコード色/寸法禁止）。

## 2. V-model 位置づけ（L2 ↔ L10 pair）

| | L2（左腕・設計） | L10（右腕・検証） |
|---|---|---|
| 成果物 | screen-list / screen-flow / ui-element / **wireframe**(Low-Fi) | visual-design（実装済 UI の UX 磨き / WCAG 2.2 AA） |
| pair | `wireframe.md` の `pair_artifact: self`（L2↔L10 ③ペアを兼ねる、docs/test-design に L10 独立 doc を作らない） | 同左 |
| 凍結 | G2 mock 凍結（PO） | G10 UX 磨き通過 |
| 段階順 | **screen-impl-pair-freeze**: `next_pair_freeze` 未到達で `implemented_screens` 宣言を block（L10 すっ飛ばし「実装済」詐称防止） | 同 |
| skip | `drive=be`（UI なし）は `not_applicable(ui_absent)` 明示宣言で skip | L2 N/A → L10 N/A（cascade） |

## 3. 駆動: design-bottomup（harness net-new、capture §3）

確立 backend に後から UI を足す**第3の向き**（Forward / Add-feature と入口が違う）。`design-elicitation`: backend 実体（data_entity/projection/cli_command）+ screen_trace → FE 要件 derive（各画面×L3/L5/L6 slot）→ gap 検出（has_body=false を SLOT_SIGNAL、coverage≠substance）→ Discovery(entry=design_uncertain)合成 → Forward L3-L6 降下。新 mode を作らず既存 routing に乗る。

## 4. C1/C2/C3 への FE 増分

- **C1 table**: `screens`(screen_id, category, url, l1_ref, status, implemented) / `screen_trace`(screen_id, requirement_id, requirement_kind, relation) は L5 §1 / [C1 §5](../engine/schema-registry.md)（ともに projection）で確定。
- **C2 projection**: screen 設計 → `screens`/`screen_trace`（logical_key=screen_id、deletion/stale は §1.5 共通則）。PLAN-L7-96 screen-db-projection 相当。
- **C3 detector**: `frontend-design-coverage`（source_kind=file_snapshot、§1c×schema×実ファイル 3 者 AND）/ `screen-impl-pair-freeze`（source_kind=file_snapshot、next_pair_freeze 段階順）。FN-DET-13 = screen↔trace 片肺（drive-gated）。

## 5. gate / drive

- **drive=fe/fullstack で発火**（drive-gated）。`drive=be`（UI なし）は core gate を阻害しない（明示 waiver）。
- `fullstack` は twin-track（be/fe を独立 pair_status）。FE 設計カバレッジは frontend-design-coverage が fail-close（「後で磨けばいい」を許さない）。

## 6. HELIX 独自強化（capture 後に上乗せ — §0）

harness の FE ガバナンスを base にした上で、HELIX が追加できる優位（後フェーズ）:
- **実 UI 描画（src/web）**: harness も空＝全員 greenfield。HELIX が中央 Web UI（ADR-005、配布 §）として実装。
- **state-events 駆動 BE/FE 契約**（screen→requirement→API contract 縦断 trace）+ axis-15〜19（mock-promotion / token-drift / a11y / visual-regression / state-transition-drift）detector。visual-regression baseline は C5 ratchet と同型。
- `not_applicable(ui_absent)` 明示 waiver 制度 + drive 切替時 preserved/waived/failed 三分類。

## 7. 検証（V-model pair）

- L2↔L10: wireframe 凍結（G2）→ UX 磨き（G10）が pair で閉じる（片肺 = FN-DET-13 / screen-impl-pair-freeze）。
- 受入（L3↔L12）: AT-FE-01 drive=fe で screen 登録 trace 無し → FN-DET-13 / AT-FE-02 §1c slug 消失 → frontend-design-coverage / AT-FE-03 next_pair_freeze 未到達で implemented 宣言 → screen-impl-pair-freeze。
- 単体（L6↔L7）: 各 FN に UT 1:1。DB fixture（screens/screen_trace）+ file snapshot（§1c doc）で境界。

## 8. 未確定（L6/L7）

- `screen_trace` / `screens` 物理 column 型（[C1 §5](../engine/schema-registry.md) / L7 で確定）。a11y/visual 閾値（C5 ADR）。src/web 実装（HELIX 独自強化フェーズ、中央 UI = ADR-005）。

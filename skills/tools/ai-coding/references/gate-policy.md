# ゲートポリシー（手順正本）
> 目的: ゲートポリシー（手順正本） の要点を把握し、設計・実装判断を行う際のクイックリファレンスとして参照

> CLAUDE.md / SKILL_MAP.md から参照される手順の正本。
> 所有: ゲート定義、セキュリティチェック、フェーズ遷移、IIP、CC、V分類、LPR、ミニレトロ、adversarial-review、リファクタリング運用、Reverse ゲート。

## Status 共通語彙

| カテゴリ | 値 | 意味 |
|---------|-----|------|
| task_status | `pending` / `in_progress` / `completed` / `blocked` / `partial` | 工程表タスク |
| gate_status | `passed` / `failed` / `blocked` / `interrupted` / `invalidated` | ゲート単位。`invalidated` は freeze-break による無効化 |
| verification_status | `pass` / `fail` | 検証レポート |
| sprint_status | `active` / `interrupted` / `completed` | L4 スプリント状態 |
| track_status | `active` / `completed` / `blocked` / `waiting` | Twin Track 状態（BE/FE 個別） |
| deliverable_status | `pending` / `in_progress` / `done` / `waived` / `not_applicable` / `partial` | 成果物状態（ADR-001） |

- task_status と gate_status を混同しない（`ai-coding/SKILL.md §4` 参照）
- `interrupted` は gate_status（IIP 発動時）と sprint_status（中断時）の両方で使用する
- `blocked` は両カテゴリに存在するが意味が異なる: task は「前提タスク未完了」、gate は「前提不足/仕様不明」

## フェーズ遷移ルール

- 各フェーズ完了前に次フェーズに進まない
- ゲート不合格 → ゲート内リトライ（3回）→ 層内ループ（5回）→ 上位層エスカレ → 人間
- **freeze-break/change control**: 凍結後に API/Schema/権限境界/運用前提が変わったら、その層と下流ゲートを自動失効。G4 pass 後の要件修正は CC（§CC）で影響度を分類し返却先を決定
- **自動通過 = 会議省略であり証跡省略ではない**。証跡がなければ常に fail

## ゲート一覧

### G0.5 企画突合ゲート（L1 内）

| 項目 | 内容 |
|------|------|
| 挿入位置 | L1 完了後 → G1 前 |
| 通過条件 | 企画書の全項目が D-REQ-F/D-REQ-NF/D-ACC に対応付けられている、企画書にあって要件定義にない項目が 0、要件定義にあって企画書にない項目は「追加提案」として明示 |
| accuracy_weight | 0.4 |
| 根拠 | 企画突合は方向性の整合確認が主で、詳細の正確性はまだ確定前のため高精度要求は抑えめ。 |
| 判定者 | PM |
| 判定形式 | チェックリスト（自動 + 手動） |
| Fail | L1 差戻し。漏れた項目を追加 |

**担当スキル**:
- gate-planning（企画突合、2026-04-17 追加）

### G1 要件完了ゲート（L1 出口）

| 項目 | 内容 |
|------|------|
| 通過条件 | REQ/NFR/受入条件 100% 定義、in/out scope 確定、未解決 blocker 0 |
| accuracy_weight | 0.5 |
| 根拠 | 要件完了は方向性の確度が中心で、実装決定までの精密検証は次フェーズで加速する。 |
| 判定者 | PM（最終）、PO（スコープ承認） |
| 判定形式 | 明示 |
| 中規模 skip | 不可 |
| Fail | L1 差戻し。文言修正なら差分再審、scope/NFR 変更なら全再審 |

### G1.5 PoC ゲート（条件付き）

| 項目 | 内容 |
|------|------|
| 発火条件 | 技術不確実性がある場合のみ |
| accuracy_weight | 0.7 |
| 根拠 | PoC は仮説検証の再現性が重要。方向性を保ちながら、検証結果の精度を高める。 |
| 通過条件 | 仮説 + kill criteria 定義、成功指標達成 or 代替案決定、主要不確実性 0 or 受容 |
| 判定者 | TL + PM、PO は予算/納期影響時 |
| 判定形式 | 明示 |
| 中規模 skip | 可（不確実性なし） |
| Fail | L1 差戻し or L2 案再設計。仮説更新後に再 PoC |

**担当スキル**:
- poc（PoC 設計/実行、2026-04-17 追加）
- gate-planning（企画整合、2026-04-17 追加）

### G1R 事前調査ゲート

| 項目 | 内容 |
|------|------|
| 挿入位置 | G1 通過後 → L2 前 / G3 通過後 → L4 前 |
| accuracy_weight | 0.6 |
| 根拠 | 事前調査は採否判断に関わるためある程度の精度が必要。一次情報反映の誤りを抑える。 |
| 通過条件 | research_report 存在、公式/一次ソース優先、採用/不採用理由記録、open blocker 0 |
| 判定者 | 自動（外部 API/認証/法令/新 FW は TL spot check） |
| 判定形式 | 自動通過可 |
| 中規模 skip | 可（非トリガ案件） |
| Fail | 次層着手禁止 |
| 強制条件 | `ai-coding/SKILL.md §7`（単一ソース） |

**担当スキル**:
- research（事前調査、2026-04-17 追加）

### G2 設計凍結ゲート（L2 出口）

| 項目 | 内容 |
|------|------|
| 通過条件 | 要件トレース 100%、ADR/データフロー/権限/エラー/運用方針確定、threat model 完了、adversarial-review 完了（該当時）、ミニレトロ記録。**fe/fullstack 追加条件**: モック（`.helix/mock/<feature>/mock.html` + `state-events.md`）完成、UX 承認済み。通過時に `MOCK-DERIVED-CONTRACT` / `MOCK-HARDCODE` / `MOCK-CODE-LEAK` の 3 項目が debt-register に auto-enqueue される |
| accuracy_weight | 0.6 |
| 根拠 | 設計凍結は方向性と主要技術判断を固定し、実装時の前提ブレを防ぐ。 |
| 判定者 | PM（最終）、TL（必須）、PO（条件付き） |
| 判定形式 | 明示 |
| 中規模 skip | 不可 |
| Fail | L2 差戻し、要件曖昧なら L1。ADR/境界変更が入ったら G3 以降無効 |
| レビュー | `codex exec "レビュー"` — Codex 5.4 |

**担当スキル**:
- adversarial-review（批判レビュー）
- threat-model（脅威モデル、2026-04-17 追加）
- security（セキュリティ設計）

### G3 実装着手ゲート（L3 出口）

| 項目 | 内容 |
|------|------|
| 通過条件 | 詳細設計完了、API/Schema Freeze、テスト設計完了、WBS/担当/依存/環境/feature flag/migration/rollback 準備完了、reference_docs 空でない。**fe 追加条件**: TL が `state-events.md` から API 契約導出完了、モック凍結済み。fullstack 追加条件: D-CONTRACT 凍結、契約テスト設計完了、モック API 仕様確定、型生成手順固定 |
| accuracy_weight | 0.9 |
| 根拠 | Schema/API Freeze が成立するため、実装前検証として高精度の一致判定を求める。 |
| 判定者 | TL（主）、PM（共同）、自動チェック補助 |
| 判定形式 | ハイブリッド（API/DB 変更なしなら明示会議省略可） |
| 中規模 skip | 会議省略可 |
| Fail | L3 差戻し、設計矛盾なら L2。契約/スキーマ変更時は G4 以降無効 |
| レビュー | `codex exec "レビュー"` — Codex 5.4 |

**担当スキル**:
- schedule-wbs（工程表/WBS、2026-04-17 追加）

### G4 実装凍結ゲート（L4 出口）

| 項目 | 内容 |
|------|------|
| 通過条件 | 全スプリント完了、実装.1-.5 通過、CI/回帰/スモーク green、Critical/High defect 0、セキュリティ閉塞完了、未解決 debt は台帳化、ミニレトロ記録。**fe/fullstack 追加条件**: `MOCK-HARDCODE`（モックのハードコード残存 grep）+ `MOCK-CODE-LEAK`（`.helix/mock/` の本実装 import 禁止）が resolved（`helix-gate` が自動 fail-close）。fullstack 追加条件: BE Sprint .5 + FE Sprint .5 + Contract CI green + L4.5 結合テスト pass（片側完了のみは不通過） |
| accuracy_weight | 0.95 |
| 根拠 | 実装凍結直前の最終合意点であり、実装品質を確実に担保するため精度を最重要とする。 |
| 判定者 | TL（最終）、PM（確認）、自動 CI 必須 |
| 判定形式 | ハイブリッド（M/L では実質明示） |
| 中規模 skip | 不可 |
| Fail | L4 差戻し、IIP P2/P3 なら L3/L2/L1 へ逆流。コード局所修正なら G4 再審、契約変更なら G3 から |
| レビュー | `codex review --uncommitted` — Codex 5.4 |

**担当スキル**:
- debt-register（負債台帳、2026-04-17 追加）

### G5 デザイン凍結ゲート（L5 出口）

| 項目 | 内容 |
|------|------|
| 通過条件 | V0/V1/V2 分類完了、契約変更なし、UI レビュー/アクセシビリティ/性能許容内 |
| accuracy_weight | 0.7 |
| 根拠 | デザイン凍結は UI 検証が主で、実装詳細の精度より体験妥当性の担保が中心。 |
| 判定者 | TL + PM、PO は UX 期待変更時のみ |
| 判定形式 | V0 のみなら自動、V1/V2 は明示 |
| 中規模 skip | UI なしは skip 可 |
| Fail | V0: L5 内修正 / V1: L4 差戻し / V2: L2 から再走（→L3→L4→L5） |
| レビュー | `codex review --uncommitted` — Codex 5.4 |

### G6 RC 判定ゲート（L6 出口）

| 項目 | 内容 |
|------|------|
| 通過条件 | E2E/性能/セキュリティ/運用準備 pass、migration rehearsal pass、rollback 実証済み、既知 Sev1/2 0、release note/runbook 完了。**fe/fullstack 追加条件**: `MOCK-DERIVED-CONTRACT`（モック由来 API 契約のドメイン整合性 TL レビュー）が resolved（`helix-gate` が自動 fail-close） |
| accuracy_weight | 0.95 |
| 根拠 | RC 判定は最終品質ゲートであり、重大欠陥を防ぐため高精度な判断が求められる。 |
| 判定者 | PM（Go/No-Go）、TL（技術推奨）、PO（条件付き） |
| 判定形式 | 明示 |
| 中規模 skip | 不可 |
| Fail | L6 が基本、原因次第で L5/L4/L3/L2。成果物/設定が変わったら新 RC 振り直し |

**担当スキル**:
- runbook（運用手順、2026-04-17 追加）

### G7 安定性ゲート（L7 出口）

| 項目 | 内容 |
|------|------|
| 通過条件 | デプロイ成功、health/smoke pass、watch window 完了、SLO 逸脱なし or low 1件以下で owner+ETA あり、rollback 不要 |
| accuracy_weight | 0.7 |
| 根拠 | 安定性フェーズは運用監視中心であり、方向性より回帰防止の精度を重視。 |
| 判定者 | 自動が基本、条件付き pass は PM/TL |
| 判定形式 | 自動通過可（顧客向け/高リスクは watch skip 不可） |
| 中規模 skip | 不可 |
| Fail | 即 rollback → 原因に応じ L6/L4/L3 差戻し。ビルド/設定/infra 変更なら G6 から |
| 人間承認条件 | 初回デプロイ / 認証・決済・PII / 破壊的 DB マイグレ / 外部 API 変更 / エラーバジェット 75%超 / インフラ構成変更 |

### G9 デプロイ安定性ゲート（L9 出口）

| 項目 | 内容 |
|------|------|
| 発火条件 | L9 完了時 |
| 通過条件 | L9（デプロイ検証）完了、ロールバック手順検証、smoke test pass |
| 判定者 | 自動/PM |
| 判定形式 | 自動＋明示 |
| Fail | 即 rollback、次 L 差戻し |
| 人間承認条件 | 本番影響が高い場合は PM 最終確認 |
| accuracy_weight | 0.9 |

### G10 観測完了ゲート（L10 出口）

| 項目 | 内容 |
|------|------|
| 発火条件 | L10 完了時 |
| 通過条件 | SLO/SLI 監視結果レビュー、異常検知 0 件 or すべて解消 |
| 判定者 | PM |
| 判定形式 | 明示 |
| Fail | L10 再実行または差戻し |
| accuracy_weight | 0.8 |

### G11 運用学習完了ゲート（L11 出口）

| 項目 | 内容 |
|------|------|
| 発火条件 | L11 完了時 |
| 通過条件 | postmortem 作成、改善提案、次サイクル feedback 記載完了 |
| 判定者 | PM |
| 判定形式 | 明示 |
| Fail | L10 差戻し |
| accuracy_weight | 0.6 |

## readiness exit と carry rule

PLAN-004 v5 連動:

- P0: gate stop（即修正）
- P1: gate stop OR carry（PM 承認）
- P2: 次 L 開始まで or debt として `.helix/audit/deferred-findings.yaml` に carry
- P3: 任意 carry

readiness exit は L1-L11 の entry/exit 条件に適用し、deferred-finding 数で accuracy_score を加減算する。  
（deferred 1件につき accuracy_score から減点。減点式は共通設定を参照）

### PLAN レビュー（gate ではない）

> PLAN レビューは gate ではないが、accuracy_score テーブル上は `gate='PLAN_REVIEW'` で記録される。

| 項目 | 内容 |
|------|------|
| accuracy_weight | 0.5 |
| 根拠 | 方向性凍結を確認するレビューであるため、G3/G4 のような実装凍結精度は不要。 |

### L8 受入（終端判定）

| 項目 | 内容 |
|------|------|
| 通過条件 | L1 受入条件 100% 充足、残余リスクを PO が明示受容、運用引継ぎ完了 |
| 判定者 | PO |
| 判定形式 | 明示 |
| skip | 不可 |
| Fail | 不足のある層へ差戻し |

## セキュリティ 4 点チェック

| # | ゲート | 内容 |
|---|--------|------|
| ① | G2 | 脅威分析（threat model） |
| ② | G4 | 実装閉塞確認（セキュリティ実装の完了） |
| ③ | G6 | RC 時の攻撃/権限/負荷検証 |
| ④ | G7 直前 | config/secret/vuln scan |

## セキュリティゲート強制条件

サイズに関わらず該当ゲートのスキップ不可:

| 条件 | 強制ゲート |
|------|----------|
| 外部 API 連携（新規/変更） | G1R 事前調査必須 + G3 API 契約レビュー必須 |
| 認証・認可ロジックの変更 | G2 セキュリティ設計レビュー必須 + L4 実装.3 セキュリティチェック必須 |
| 課金・決済関連 | G2 設計承認（PO）必須 + L4 実装.3 セキュリティチェック必須 |
| 個人情報の取り扱い変更 | G2 設計承認（PO）必須 |
| 複数リポジトリ / チームに影響 | L3 接続設計必須 |
| Phase 4 Run（L9-L11） | G6/G7 相当の監査要求（config/secret/権限/脆弱性）を満たすこと |

## Codex レビュー義務化

| 遷移 | 手段 | 担当 |
|------|------|------|
| G2（設計凍結） | `codex exec "レビュー"` | Codex 5.4 |
| G3（実装着手） | `codex exec "レビュー"` | Codex 5.4 |
| L4 実装.2（軽量） | `codex review --uncommitted` | Codex 5.4（Critical/High のみ） |
| L4 実装.5（フル品質） | `codex review --uncommitted` | Codex 5.4（全 severity） |
| G4（実装凍結） | `codex review --uncommitted` | Codex 5.4 |
| G5（デザイン凍結） | `codex review --uncommitted` | Codex 5.4 |

**5.4 ボトルネック緩和**: 低リスク案件（サイジング S + セキュリティゲート非該当）は Codex 5.3 SE が一次レビュー可。高リスク案件は 5.4 TL 必須。

## L5 Visual Refinement 分岐

| 分類 | 内容 | 差し戻し |
|------|------|---------|
| V0（見た目のみ） | 色・余白・タイポ・トークン変更 | L5 内で修正 → G5 へ |
| V1（UI構造変更） | コンポーネント追加・レイアウト変更 | L4 に差し戻し → L5 再実行 |
| V2（契約影響） | API/DB 変更を伴う UI 変更 | L2 から再走（→L3→L4→L5） |

詳細: `layer-interface.md §L5 Visual Refinement`

## 作業前コード調査（実装.1a 必須）

実装.1 を .1a（コード調査）+ .1b（変更計画）に内部分割:

- .1a: 変更対象ファイルの Read / 依存関係列挙 / テスト現状確認 / 規約把握
- .1a の `impact_analysis` を .1b の必須入力とする（未読のまま計画を立てない）
- 詳細: `implementation-gate.md §実装.1`

## IIP（実装内割り込みプロトコル）

**適用範囲: L4 実装フェーズ内のみ。**

実装中の前提崩壊・想定外トラブル対応:

- `interrupted` ステータスで `failed`（既知前提内ミス）と分離。リトライカウント外
- 影響度: P0（ゲート内修正）/ P1（実装.1差戻し）/ P2（逆流ループ移送）/ P3（人間エスカレ直行）
- 詳細: `implementation-gate.md §IIP` / `layer-interface.md §IIP`

## CC（凍結後変更管理 — Change Control）

**適用範囲: G4 pass 後〜L8 受入完了まで。**
**発火条件: 凍結済み成果物に対して要件修正・仕様追加が発生した時。**

IIP（L4 内の前提崩壊）や V 分類（L5 の visual 差戻し）とは異なり、**PO 起点の要件変更**を影響度で分類する。

| 分類 | 影響 | 判定基準 | 返却先 | 再通過 | 承認 |
|------|------|---------|--------|--------|------|
| CC-S | 局所変更 | L1 受入条件・L2/L3 成果物・API/Schema/権限境界 すべて不変、**変更差分が** サイジング S 範囲 | L4 | G4 → 影響下流ゲートのみ | TL |
| CC-M | 設計差分 | L1 scope/NFR 不変だが、画面構造・導線・詳細設計・テスト設計・内部契約に変更 | L3 | G3 → L4 → L5 → … | TL+PM |
| CC-L | 要件変更 | L1 受入条件・scope・NFR・業務ルール・優先順位が変わる | L1 | フル再通過 | PO |

**自動昇格（3段階）**:
- CC-M で **API/Schema のみ**変更 → freeze-break により **L3** へ差戻し（G3 → L4 → … 再通過）。G3 が API/Schema Freeze の所有ゲート
- CC-M で **権限境界/ADR/運用前提**に触れた場合 → freeze-break により **L2** へ差戻し（G2 → G3 → L4 → … 再通過）。G2 が設計凍結の所有ゲート
- **L1 受入条件/scope/NFR** が変わる場合 → CC-L に昇格（L1 差戻し → フル再通過）

**累積カウント**: CC 発動回数は LPR（R1/R2/R3）と合算。同一 `cause_id`（変更要因の識別子）で 2 回発動 → 上位エスカレ。

## LPR（後半差戻しプロトコル）

**適用範囲: G5 pass 後（または G5 skip 決定後）〜 L8 受入完了まで。**
**発火条件: 後続フェーズが pass 済み成果物の再工事を要求した時。**

| 分類 | 原因 | 返却先 | 承認 |
|------|------|--------|------|
| R0 | Defect（不具合） | 該当実装 → 影響検証 | TL |
| R1 | Assumption Gap（前提乖離） | CC-S/M/L に準じた返却先（CC 分類で深度決定） | TL + PM |
| R2 | Quality Polish（体験品質） | L5 内で対応（**1回上限**） | TL |
| R3 | Scope Change（要件変更） | CC-L 相当（L1 差戻し → PO 承認） | PO |

**R2 diff 制約**: CSS/文言/既存要素の順序/a11y 属性まで。状態遷移・条件分岐・ルーティング・API 呼び出し・権限判定・計測イベント変更が入ったら R1 or R3 に昇格。

**L7 デプロイ後の再入**: 修正 → 再検証 → 再デプロイ → G7 再通過（watch リセット）→ PO 再承認。

**累積カウント**: R1/R2/R3 全て加算、CC 発動回数も合算。同一 `cause_id` で 2 回発動 → 上位エスカレ。R0（Defect）は通常のバグ修正であり累積対象外（品質改善を萎縮させないため）。

## プロトコル棲み分け

| プロトコル | 適用範囲 | 用途 |
|-----------|---------|------|
| 通常ゲート判定 | L1〜L3（凍結前） | ゲート fail → 差戻し。プロトコル不要 |
| IIP（P0-P3） | L4 実装中 | 前提崩壊・想定外トラブルの割り込み |
| CC（CC-S/M/L） | G4 pass 後〜L8 | 凍結後の要件修正（影響度で返却先を決定） |
| V 分類（V0/V1/V2） | L5 フェーズ全体 | Visual Refinement の変更分類と差戻し判定 |
| LPR（R0-R3） | G5 pass/skip 後〜L8 | 後半フェーズの差戻し分類（R1 は CC 深度参照） |

**L4 実装中の PO 起点要件変更**: G3 凍結済み成果物が変わるため freeze-break に該当。freeze-break で下流ゲート（G3 以降）を自動失効させ、影響に応じて L3/L2/L1 へ差戻す。IIP ではなく通常の freeze-break ルートで処理する。

**CC と LPR の使い分け**: CC は「PO 起点の要件修正」、LPR は「開発側が発見した再工事要因」。G5 pass/skip 後に PO から要件修正が入った場合は CC で分類し、開発側の検証で前提乖離が判明した場合は LPR R1 を使う（返却深度は CC-S/M/L を参照）。

**L5 フェーズ中の前提乖離**: visual 問題は V 分類（V0/V1/V2）で判定。V2（契約影響）は L2 差戻しとなるため CC-M 相当の扱い。L5 中に発見された非 visual 問題（defect, assumption gap 等）は CC で分類する（V 分類の対象外）。

## ミニレトロ（マイルストーン基準）

| マイルストーン | 発火タイミング | 目的 |
|--------------|--------------|------|
| 設計凍結後 | G2 通過後 | 設計判断の妥当性振り返り |
| 実装凍結後 | G4 通過後 | 実装の学び・工数乖離記録 |
| 終端フェーズ後 | L8 受入完了後 / G7 でロールバック発生時 | プロジェクト全体振り返り |

- Try は owner + due 必須（空文化防止）。重大リスク発見時のみ blocking Issue 化
- Sonnet に委譲
- CC/LPR 発動時に原因を記録 → Problem に反映
- 詳細: `layer-interface.md §ミニレトロ`

## adversarial-review（対立的レビュー）

- 自動発火: セキュリティゲート条件該当時 / ADR 作成時
- 任意発火: PM が「後戻りコストが高い」と判断した設計判断
- スキップ: サイジング S / 既存ルールの機械的適用 / 同一テーマ実施済み
- 責務分離: TL壁打ち（1案・低コスト）< codex review（品質・中コスト）< adversarial-review（反証・高コスト）
- 詳細: `workflow/adversarial-review/SKILL.md`

## L1 スキップ時の最小要件メモ

フェーズスキップ決定木で L1 を飛ばす場合（S案件のバグ修正・リファクタ・設定変更等）でも、以下の**最小要件メモ**を作成する:

- **目的**: 1行（何をなぜ変更するか）
- **受入条件**: 1-3項目（何が満たされたら完了か）
- **スコープ外**: 明示的に対象外とする事項（任意）

これにより、L8 受入時に突合する対象が常に存在する。S案件で L8 自体をスキップする場合は、完了報告に受入条件の充足を含めることで代替する。

## リファクタリング・共通化の実施タイミング

| タイミング | 内容 | 制約 |
|-----------|------|------|
| L4 着手前（準備リファクタ） | 機能を安全に触るための小整理。S サイズ・挙動不変 → L4 のみフローに収める | テスト全通過必須。公開 API/契約は変えない |
| G4 直後（台帳化のみ） | 実装せず負債を台帳化 + 優先度決定。G4 通過条件の debt 台帳化 + ミニレトロで洗い出す | この時点で共通化の実装着手は非推奨（実装凍結後のため下流ゲート無効化を招く） |
| L8 後の次イテレーション | 独立タスクとして共通化・リファクタ実施。**再サイジング**して該当フローに従う（S なら L4 のみ、M/L なら通常フロー） | 挙動変更を伴う場合は必ず再サイジング |

**負債蓄積の防止**:

1. G4 で `debt_register` 必須（未解決 debt は台帳化が G4 通過条件）。保存先: `docs/debt/YYYY-MM-DD-debt-register.md`
2. 毎イテレーション **20%** を改善枠に予約（ガイドライン。実績はミニレトロで振り返り）
3. 重複コード **3 回** で共通化を**検討**（ヒューリスティック。dev-policy / refactoring スキル準拠）

## Reverse ゲート（HELIX Reverse）

Forward ゲートが「定義の完全性 / 凍結可否」を判定するのに対し、Reverse ゲートは「**証拠の十分性 / 仮説の反証可能性**」を判定する。詳細フロー: `workflow/reverse-analysis/SKILL.md`

### 共通指標（全 Reverse ゲート）

| 指標 | 意味 |
|------|------|
| **coverage** | 対象モジュール/契約/設計のうち分析済みの割合 |
| **confidence** | 各仮説の確度（high / medium / low） |
| **contradictions** | 仮説間の矛盾数（未解決） |
| **unknowns** | 分類不能な項目数 |

### RG0 証拠網羅ゲート（R0 出口）

| 項目 | 内容 |
|------|------|
| 通過条件 | 対象モジュール coverage 100%、依存グラフ完成、DB スキーマ取得済み、unknowns が全て cataloged |
| 判定者 | TL |
| Fail | 未スキャン領域の追加調査 |

**生成スキル**:
- reverse-r0（Evidence Acquisition、2026-04-17 追加）

### RG1 契約検証ゲート（R1 出口）

| 項目 | 内容 |
|------|------|
| 通過条件 | API/DB/型の抽出 coverage ≥ 90%、confidence high ≥ 80%、characterization tests で主要パス検証済み、contradictions 0（未解決） |
| 判定者 | TL（Codex 5.4） |
| Fail | confidence low の契約に追加テスト / 再抽出 |

**生成スキル**:
- reverse-r1（Observed Contracts、2026-04-17 追加）

### RG2 設計検証ゲート（R2 出口）

| 項目 | 内容 |
|------|------|
| 通過条件 | アーキテクチャ復元完了、ADR 仮説の confidence high ≥ 70%、contradictions 0（未解決）、adversarial-review 実施済み（M/L） |
| 判定者 | TL（Codex 5.4）+ adversarial-review |
| Fail | 矛盾する ADR の追加調査 / 仮説修正 |

**生成スキル**:
- reverse-r2（As-Is Design、2026-04-17 追加）

### RG3 仮説検証ゲート（R3 出口）

| 項目 | 内容 |
|------|------|
| 通過条件 | PO 検証済み仮説率 ≥ 80%、unknown 分類の全項目に調査タスク割当済み、accidental/deprecated の全項目に対応方針決定済み |
| 判定者 | PM + PO + TL |
| Fail | PO 追加ヒアリング / unknown の調査タスク実行 |

**生成スキル**:
- reverse-r3（Intent Hypotheses、2026-04-17 追加）

### RG4 は独立ゲートではない

R4（Gap & Routing）の出力は Forward HELIX の入力となる。R4 完了 = gap_register の全項目に routing 割当 + 優先順位合意で、Forward フローの該当レイヤー（L1/L2/L3/L4）に直接接続する。

**生成スキル**:
- reverse-r4（Gap & Routing、2026-04-17 追加）

### RGC Gap Closure（Reverse Gap Closure — Forward 完了後）

> Forward の「G6 RC 判定ゲート」（RC = Release Candidate）とは別概念。RGC = Reverse Gap Closure。
> ※ CLI 未実装。将来バージョンで `helix reverse rgc` として実装予定。
> ※ 2026-04-17 更新: Python 実装済み（`helix reverse rgc` サブコマンド）。

| 項目 | 内容 |
|------|------|
| 実行タイミング | Forward HELIX 完了（L6/L8 pass）後 |
| 通過条件 | gap_register 全項目に closed/partial/open ステータス付与、closed 項目に evidence 記録済み、仮説成果物の昇格判定完了（intent_hypotheses は PO 承認必須） |
| 判定者 | TL（技術検証）+ PM（昇格判定）+ PO（intent_hypotheses 承認） |
| Fail | 未閉塞 gap の追加修正 → Forward 再実行 → RGC 再判定 |

**生成スキル**:
- reverse-rgc（Gap Closure、2026-04-17 追加）

**RGC 3 段階:**

| 段階 | 内容 |
|------|------|
| RGC-1 | Gap 閉塞検証（gap 種別ごとの検証手段で確認） |
| RGC-2 | 成果物昇格（observed_contracts → L3 正本、as_is_design → L2 正本、intent_hypotheses → L1 正本） |
| RGC-3 | 残存 Gap 判定（closed → 完了 / partial → debt_register 移管 / 新規 → 次イテレーション routing） |

詳細フロー: `workflow/reverse-analysis/SKILL.md §RGC`
検証チェックリスト: `workflow/verification/SKILL.md §15.3`

## 再入規則（横断）

| 条件 | アクション |
|------|---------|
| ゲート内リトライ | 最大 3 回 |
| 層内ループ | 最大 5 回 |
| 同一起点からの差し戻しが 2 回目 | 1 つ上位のフェーズへエスカレ |
| L2 まで到達して再度 5 回不合格 | 人間エスカレ（PO へスコープ判断を委譲） |
| IIP interrupted | リトライカウント外だが、逆流回数には含める |

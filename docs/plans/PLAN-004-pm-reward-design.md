# PLAN-004: PM 報奨設計 + Implementation Readiness Framework + Deliverable Abstraction + Research/Review Embed (v4)

## §1 目的

本 PLAN は `PLAN-004`（v3）を v4 へ改訂し、既存の「速度優先」から「正確・精度志向」への設計判断を実装前提まで拡張する。

### 1.1 本計画の中心方針

- 哲学 shift: `速度 → 正確・精度志向`
- 実装着手前の `Readiness` を明示し、フェーズ間の混線をなくす。
- `HELIX` の内製 Deliverable（`D-PLAN`, `D-API`, `D-DB`, `D-ARCH`, `D-CONTRACT` など）と外部形式（OpenAPI, ADR, Prisma, threat-model など）を同一抽象で扱う。
- 各 L で `Research` と `Review` を組み込み、評価と意思決定の再現性を上げる。
- v3 の報奨設計（既存 A）を維持し、L1-L3 の実行構造と CLI/アダプタ基盤を新規追加する。

### 1.2 v4 で達成する結果

- PLAN-004 の本文を以下で更新する。
  - `§1-§10` の v4 フォーマット確定
  - `§3` で A/B/C/D の 4 軸を明示
  - `§4.2-4.5` で Readiness/Deliverable/Research+Review を新規設計
  - `§7` で Sprint 7-10 を追加
  - `§10` に v4 改訂履歴を追加
- `README`, `ADR`, `API仕様`, `データモデル`, `Threat modeling` を含むドキュメント品質管理を、Sprint/Task 自己評価へ接続する。
- `helix-readiness` CLI（L4）を前提とした、readiness 評価の最短コマンド化（実装は sprint で進める）を前提化する。
- 実装はしない（PLAN 更新のみ）。コミット禁止を維持する。

### 1.3 継続条件（本 PLAN 内）

- 本 PLAN は計画と設計原則を確定する。実装粒度の最終確定は PLAN の後続または L4 実装スプリントへ委譲。
- L8 受入では `deferred` と `再開条件` を維持し、未解決の再現可能性を担保。

## §2 背景

### 2.1 現行 v3 での限界

- `PLAN-002/003` の運用経験では、`L1-L3` と `G3/G4` の判断基準が、レビューの粒度差を吸収しきれず停滞/浅薄レビューを招いた。
- v3 は価値観とレビュー精度を定義したが、実装・検証前の `readiness` が不足しており、進行判断に揺れが残る。
- 研究とレビューを各 L に明示埋め込みせず、`レビューの品質` が実装段階で後付け化していた。
- Deliverable は HELIX 内部の表現に寄りすぎ、外部形式連携（OpenAPI や ADR）までの接続ルールが未整備。

### 2.2 追加要件の背景

- 2026-04-30 ユーザー要望で、以下を同時に導入する必要が生まれた。
  - L-level Readiness Matrix（全 L）
  - L1-L3 詳細 sprint 構造
  - Deliverable Adapter Pattern（HELIX template 非依存）
  - Research/Review の各 L embedded 化
- これらを PLAN-004 に取り込まないと、PLAN-006/007/009 にまたがる前提不整合が発生する。

### 2.3 v4 で追加する文脈

- `helix-plan review` は方向性、`helix-gate` は実装性、`helix-readiness` は実装可否という 3 つを分離。
- Plan と実装を同時に書かず、L-level ごとの「入る条件」「出る条件」「継続条件」を可視化する。
- `accuracy_score` は記録だけでなく、readiness とレビューの接続点として再定義する。

## §3 スコープ（A/B/C/D）

本 PLAN は `1 ファイル`（`docs/plans/PLAN-004-pm-reward-design.md`）のみ更新対象。

### 3.1 含むもの

#### A. 報奨設計（既存 v3 継続）

1. 5 軸（情報の密度 / 深さ / 広さ / 実装の正確性 / 保守性）でのレビュー基準。
2. 精度向上を阻害しない再現的な review loop 制御。
3. 心理メカニズム逆手（反復率・改善率を可視化し、無駄な厳密化ループを防ぐ設計）。
4. `accuracy_score` 連動の記録方針。
5. PM 主体の報奨設計としての意思決定責務を保持。

#### B. Implementation Readiness Framework（新規）

1. L-level Readiness Matrix（L1-L8）を追加。
2. Layer 0〜3 の準備条件・達成条件を定義。
3. `HELIX_CORE.md` と `skills/tools/ai-coding/references/gate-policy.md` を正本として定義更新。
4. `L1-L8` の `entry/exit` 条件に readiness を入れ、G1-G7 の通過条件と連動。

#### C. Deliverable Adapter Pattern（新規）

1. Deliverable 抽象をHELIX内製 5 軸/8 成果物に限定せず一般化。
2. `cli/lib/deliverable_registry.py` と `cli/lib/adapters/` での実装方針を定義。
3. HELIX D-*（`D-API`, `D-DB`, `D-ARCH`, `D-CONTRACT`, `D-REVIEW` 等）と外部形式（OpenAPI / ADR / Prisma / threat-model）を同一型で扱う。
4. `.helix/deliverable-config.yaml` を型→アダプタのマッピング定義として導入。

#### D. Research + Review embedded（新規）

1. 各 L.0 sprint を research entry として正式化（`web-search` 経由）。
2. 各 L.X sprint exit を review exit として `workflow/adversarial-review` + 5軸で必須化。
3. Sprint 内の挿し込みルール（Mid-sprint）を定義し、PLAN-007 の 5 種 Scrum トリガー（research/UI/unit/sprint/post-deploy）と接続。

### 3.2 含まないもの

- `L-1, L9-L11` のフェーズ拡張: PLAN-006/009 で実施（本 PLAN v4 では未収載）。
- Scrum 挿し込み機構の全体実装: PLAN-007 で実施。
- 実装ロジックの最終コード、DB migration 本体、CLI 実装の本体コードは本 PLAN の対象外（対象は方針と実装分解まで）。
- 大量のアダプタ実装（20 種全部）の同時導入はしない。MVP で HELIX default + OpenAPI 程度に限定し、段階追加。

### 3.3 成果物

- 本 PLAN 本文（本書）にて、以下を最終化する。
  - L-level matrix
  - sprint 7-10 追加
  - Deliverable 抽象 + 実装配線
  - Research/review 例外条件・再挿入条件
- 各種実装ファイル（`cli/...`, `.helix/...`）は実装 PLAN（L4）で反映。

### 3.4 非機能境界

- 文書の主語は「方針」。
- コード/SQL の実装詳細値は L4 Sprint の本体に委譲。
- 追加作業を v4 に同梱しない。`想定外作業` は `§9` に限定。

## §4 採用方針

### 4.1 報奨設計（既存）

#### 4.1.1 既存要素の維持方針

- v3 で確立した 5 軸評価は維持する。
- 対象: `PLAN review`, `G3`, `G4`, `L8 受入`
- 5 軸の定義
  - density（必要事項の密度）
  - depth（掘り下げの有効性）
  - breadth（関連領域への目配り）
  - accuracy（仕様・契約・型の適合）
  - maintainability（変更耐性）

#### 4.1.2 5 軸 Lv1-5 テンプレ（再掲）

1. Lv1 (poor): 欠落、論点誤認、再現不能。
2. Lv2 (insufficient): 情報はあるが偏在し、検証不能領域が多い。
3. Lv3 (acceptable): 標準実務的に実行できる密度。
4. Lv4 (good): 根拠を含み、観点間整合が取れている。
5. Lv5 (excellent): 他 PLAN へ転用可能な汎用知見がある。

#### 4.1.3 review フォーマットとの整合

- ロール横断の報告は `findings` に `severity` とともに `dimension_scores` を併記する。  
  例（構造）:
  - `severity: medium`
  - `title: L1 entry 条件が未確認`
  - `dimension_scores`: `accuracy:2`, `density:2` など
- 5 軸は `overall_scores` でも常に要求される（`approve` でも要点不足なら `needs-attention`）。

#### 4.1.4 Accuracy Score と心理メカニズム逆手

- `accuracy_score` は「評価」だけでなく、改善サイクルのガードとして扱う。
- 1 回ごとに `deferred` が増えるだけの方向性に偏らず、次アクション付きで score を更新。
- `accuracy_score` を導入する理由:
  - 再レビュー時の判断基準を機械可読に保つ
  - 過去 PLAN の比較を plan_id × gate × dimension でトレースする
  - L8 で未解決項目の残存を「再発条件付き」へ明示する

### 4.2 Implementation Readiness Framework（新規）

#### 4.2.1 Layer 0: L-level Matrix（L1-L8）

各 L は `entry`（着手条件）/`exit`（完了条件）を満たさなければ次 gate に進まない。  
最終正本は `helix/HELIX_CORE.md` へ反映し、本 PLANで準拠仕様を定義する。

| L | entry 条件（抜粋） | exit 条件（抜粋） |
|---|---|---|
| L1 | 要件トレーサビリティ、目的の承認、主要制約の明文化 | 報奨設計 A の準拠確認、L1 readiness checklist 合格 |
| L2 | 設計方針の競合解消、ADR 方針の素案、攻めるべきレビュー観点の確定 | 主要要件の ADR 化、主要 API/データ定義の方針確定、L2 readiness 合格 |
| L3 | L2 成果物レビュー、依存関係の固定、実装リスクの初期評価 | L3 readiness 合格、主要実装タスク分解と実験設計 |
| L4 | L0-L3 readiness と gate-policy 前提が満たされること | L4 readiness 合格、実装受入の準備完了 |
| L5 | L4 レビュー根拠、UI 受入観点、運用条件の初期定義 | L5 readiness 合格 |
| L6 | テスト設計・計測設計・品質基準の準備 | 主要検証観点網羅とレビュー結果への反映 |
| L7 | デプロイ前提の整備、切り戻し手順 | 実デプロイ条件の明示、インシデント対応フロー準拠 |
| L8 | RC 判定結果・受入観点の確定 | `deferred` 追跡可能、次 PLAN 引き継ぎ完了 |

#### 4.2.2 Layer 1: PLAN-level Foundation

- `PLAN-004` 全体で共通する固定条件を定義:
  - 哲学変更の継続条件（v3 の評価軸は有効）
  - L-level に対する readiness 接続ルール
  - 失敗回避ルール（deferred を次アクション化）
  - Gate の pass 条件に readiness exit の紐付け

#### 4.2.3 Layer 2: Sprint-level Preconditions

- 各 Sprint は開始前に「S00」チェックを持つ。
  - 依存条件の解決
  - 関連 Deliverable の状態
  - 直近の research/review 反映可否
- Sprint 終了時は `exit` チェックを満たすことを `Sprint Retrospective` で明記。

#### 4.2.4 Layer 3: Task-level Self-check

- Task 開始時:
  - `owner`, `risk`, `exit条件`, `evidence`、`deferred` を明記。
- Task 完了時:
  - L-level readiness matrix に対する更新有無
  - review ループの再発条件確認

#### 4.2.5 正本文書化

- `helix/HELIX_CORE.md`: L-level matrix と Layer 判定ルールを追記。
- `skills/tools/ai-coding/references/gate-policy.md`: gate pass 条件に readiness を追加。
- 参考資料として `workflow-core`, `implementation-gate` への参照を明記。

### 4.3 L1-L3 詳細 sprint 構造（新規）

#### 4.3.1 L1/L2/L3 の sprint 分割

- 各 L は以下テンプレートで構造化。

| L | Sprint 内構成 |
|---|---|
| L1 | 1.0 research + 1.1-1.5 主要 + 1.6 review |
| L2 | 2.0 research + 2.1-2.5 主要 + 2.6 review |
| L3 | 3.0 research + 3.1-3.8 主要 + 3.9 review |

- `1.0 / 2.0 / 3.0` は新規条件確認 + 情報更新 + risk 再評価。
- `*.1-*` で実装/設計の主作業を行う。
- `*.6/*.6/*.9` は adversarial-review + 5軸評価を満たして終了。

#### 4.3.2 駆動タイプ別 skip/include rule

| 駆動タイプ | L1 research | L2 research | L3 research | review rule |
|---|---|---|---|---|
| be | 必須 | 必須 | 必須 | 例外なく実施 |
| fe | 必要時のみ | 必須（設計接続のため） | 必須 | `adversarial-review` で API/画面接続を検証 |
| db | 省略可 | 必須 | 必須 | schema/drift 監査を追加 |
| fullstack | 必須 | 必須 | 必須 | 連携証跡をレビュー時に必須化 |
| research | 深掘り必須 | 深掘り必須 | 必須 | 再現手順を research ノート化 |

### 4.4 Deliverable Adapter Pattern（新規）

#### 4.4.1 Deliverable 抽象型（MVP）

`type` は少なくとも以下を想定し、拡張可能な型階層を採用する（目安 ~20 種）。

```
api-spec, data-model, contract, threat-model, architecture, test-plan,
deployment, handover, ADR, policy, schema, config, observability,
review-report, roadmap, acceptance-criteria, runbook, db-migration,
risk-register, glossary, benchmark, release-note
```

#### 4.4.2 実装配置

- 登録は `cli/lib/deliverable_registry.py` で集中管理。
- 各型の変換器は `cli/lib/adapters/` 下で実装。
- MVP では以下を必須とする。
  - HELIX default adapter（D-* の基本型）
  - OpenAPI adapter（外部 API 形式）
  - `schema`/`config` の最小検証

#### 4.4.3 外部互換（HELIX template を超えて）

- HELIX D-* は `domain_type` により内製表現に維持。
- 外部 artifact との接続は adapter で変換。
- output は `deliverable` 共通 JSON（type, scope, source_ref, generated_by, schema_version, evidence）へ正規化。

#### 4.4.4 `.helix/deliverable-config.yaml`（スキーマ）

```yaml
version: "v1"
default_adapter: helix_default
types:
  api-spec:
    adapter: openapi
    required_fields: [version, title, paths]
    owner: docs
  threat-model:
    adapter: helix_default
    required_fields: [scope, threats, mitigations]
  data-model:
    adapter: helix_default
    required_fields: [entities, relations]
```

※ 詳細仕様は Sprint8 実装時に拡張する。

### 4.5 Research + Review embed（新規）

#### 4.5.1 全 L.0 / L.X の埋め込みルール

- L.0（research entry）  
  - `tools/web-search` skill 経由の公式/一次情報調査。
  - 1 L 当たり最大 1 営業日。
  - 調査結果は `.helix/research/` 配下に保存（保存前 redaction を実施）。
- L.X（review exit）  
  - `workflow/adversarial-review`（レビュー対抗的観点）を実行。
  - 5 軸で Lv3 以上を基本合格ラインとする。
  - `severity` と `dimension_scores` を併記。

#### 4.5.2 Mid-sprint insertion と PLAN-007 連携

- Sprint 中でも必要に応じて以下トリガーで挿入可能とする。
  - research-trigger（依存更新、仕様変更）
  - UI-trigger（ユーザー価値の齟齬）
  - unit-trigger（エラーパターン増加）
  - sprint-trigger（未解決 finding 増大）
  - post-deploy-trigger（本番観測不一致）
- 挿入時は該当 L sprint の「現状把握→軽量調査→review-exit の mini loop」を追加し、主 task 進行を停止しない。

#### 4.5.3 研究結果の再利用

- `.helix/research/` と `.helix/review/` の参照整合性を次 PLAN でも読み直せるよう、`source_ref` を一意キーで管理。
- 2 回目以降は差分だけを追記し、過去結果の重複を避ける。

## §5 ゲート（gate-policy + readiness）

### 5.1 ゲート適用原則

- 本 PLAN は G1-G7 の既存基準を維持し、`readiness exit` を追加条件として必須化する。
- 各 Gate は通常 pass 条件に加え、該当 L の readiness exit を満たしていることを要求。
- readiness が満たされない場合、評価コメントは「needs-attention」に寄せる。

### 5.2 G1-G7 追加条件

#### G1 PM
- 変更の目的・スコープが一致。
- L-level matrix 設計が本文に反映されている。

#### G2 設計凍結前レビュー
- 既存 gate-policy 準拠。
- §4.5 の research/review が L2 起点で埋め込まれていること。

#### G3 Schema Freeze
- L-level matrix の entry/exit を満たした上で、readiness exit を達成。
- `accuracy_score` スキーマ拡張条件（dimension と evidence の最小仕様）を満たす。

#### G4 Implementation Freeze
- Sprint 7-10（本 PLAN v4）で CLI 準備済みの前提を確認。
- `Deliverable Adapter` の最小構成（HELIX default + OpenAPI）方針を固定。

#### G5 デザイン凍結
- UI 依存でなければ適用外項目を明示し、readiness を L4 へ伝播。

#### G6 RC
- readiness 失敗履歴の再発防止条件があること。
- review loop が P1/P2 過多で終端しない運用ルールを明示。

#### G7 安定性
- deferred の引継ぎルール確認。
- Plan-level 監査観点と L8 受入条件が一致していること。

### 5.3 gate-pass 条件の判定式（簡易）

```text
pass(Gx, L) =
  gate_condition(Gx) AND readiness_exit(L, phase="entry|work|exit")
  AND findability(evidence, review, research)
```

※ gate_condition は既存 gate-policy に準拠。

## §6 主要リスク

### 6.1 v3 既存（R-01〜R-06）

#### R-01 逆流リスク
- 過剰な厳しさ/甘さどちらもループを増やす。
- 対処: readiness と review 深さを固定閾値に寄せる。

#### R-02 重み設定バイアス
- accuracy_weight が恣意化する危険。
- 対処: 変更理由を gate-policy に履歴記録。

#### R-03 migration 競合
- v2 系と新系の同時更新で衝突。
- 対処: 実装順序を PLAN 依存で固定。

#### R-04 PII/secret 混入
- accuracy/evidence 保存時の情報漏えい。
- 対処: 保存前 redaction と L8 検査を義務化。

#### R-05 5 軸の画一化
- 形骸化した review。
- 対処: gate 毎の weighting 分岐と再現条件の分離。

#### R-06 目的逸脱
- スコープ外改善の増殖。
- 対処: 対応しない項目は `想定外作業` として明示。

### 6.2 v4 追加（R-07〜R-09）

#### R-07 Adapter registry の over-engineering
- 対処: MVP のみに限定（HELIX default + OpenAPI）し、追加型は段階導入。

#### R-08 Research sprint の無限拡大
- 対処: 1 L.0 は最大 1 営業日、結果は redaction 後保存、追加は中断条件を明示。

#### R-09 Review ループ過剰深掘り
- 対処: review は原則 P0 をゼロ化し、5 軸全体で Lv3 以上が exit。  
  P1/P2 は次フェーズへの carry 仕様とする。

## §7 L4 Sprint 構成（PLAN-004 実装計画）

### 7.1 Sprint 1: Shared（既存）

- `helix.db v8`（既存）を前提に readiness YAML スキーマ定義を確定。
- DoD: readiness schema, phase linkage の最小仕様化。

### 7.2 Sprint 2: TL prompt（既存）

- 方向性凍結前後の観点切り分けを維持。
- DoD: TL レイヤ定義の分離条件を本文化。

### 7.3 Sprint 3: Codex prompt（既存）

- role 横断観点と 5 軸評価観点の整合。
- DoD: role prompt の最小要件を本文レベルで固定。

### 7.4 Sprint 4: gate-policy 重み（既存）

- readiness 追加条件と既存 weight 方針の接続。
- DoD: `gate-policy` への反映対象を明確化。

### 7.5 Sprint 5: helix accuracy report（既存）

- 精度レポート入力/出力粒度定義。
- DoD: 監査観点に必要な最小フィールドを明記。

### 7.6 Sprint 6: 実証（既存）

- 既存 PLAN の retro evidence を v4 条件へ反映。
- DoD: v3 実績の再評価結果を v4 テンプレへ反映。

### 7.7 Sprint 7（新）: Implementation Readiness CLI 実装

- `cli/helix-readiness check --phase L4 --plan PLAN-X` を前提にする CLI 観点設計。
- `.helix/phase.yaml` に readiness section を追加する方針を定義。
- Layer 0-3 の check ロジックを設計段階で記述。
- DoD:
  - 実行コマンド草案
  - L-level entry/exit 評価ルール
  - 失敗時リカバリ観点の記録

### 7.8 Sprint 8（新）: Deliverable Adapter Pattern

- `cli/lib/deliverable_registry.py` を新規追加対象として明記。
- `cli/lib/adapters/` に HELIX default + OpenAPI adapter の最小実装計画を定義。
- `.helix/deliverable-config.yaml` schema を固定。
- DoD:
  - adapter type map
  - HELIX D-* ↔ 外部形式の対応表
  - 新規型追加手順

### 7.9 Sprint 9（新）: L1-L3 詳細 sprint structure

- `HELIX_CORE.md`, `gate-policy.md`, `SKILL_MAP.md` の改訂を前提化。
- `cli/helix-sprint --phase L1-L8 全 phase` の仕様を追加。
- DoD:
  - L1-L3 スプリント構造（x.0/x.x）確定
  - 駆動タイプ別 skip/include ルール

### 7.10 Sprint 10（新）: Research + Review embed

- L.0/L.X sprint テンプレートを整備。
- `tools/web-search` と `workflow/adversarial-review` 連携フローの最小実装方針を追加。
- Mid-sprint insertion trigger と PLAN-007 5 種 Scrum を接続。
- DoD:
  - research 実行上限（最大1営業日）
  - review exit の 5軸要件（Lv3 以上）
  - redaction 保存ルール

### 7.11 Sprint 依存と順序

- 既存 1-6 は順序前提を維持。  
- Sprint7-10 は `L4 readiness` の前提として並行可能な項目を可視化しつつ、実装時は 7→8→9→10 の順で整列。

## §8 関連 PLAN

- PLAN-002: `docs/plans/PLAN-002-helix-inventory-foundation.md`  
  本 PLAN の v4 readiness を retroactive 適用し、既存 sprint に readiness section を追加。
- PLAN-003: `docs/plans/PLAN-003-auto-restart-foundation.md`  
  review evidence の再解釈と loop 制御を再評価。
- PLAN-005: `docs/plans/PLAN-005-ops-automation-skills.md`  
  Deliverable Adapter を介した API spec / schema 表現の受け渡しを前提化。
- PLAN-006: 参照先上流フェーズ（L-level matrix 共有）
- PLAN-007: Scrum 5 種との mid-sprint insertion 統合
- PLAN-009: Run 工程の L9-L11 へ readiness matrix 拡張

## §9 想定外作業（v4 追加）

- 外部形式アダプタの全域実装（OpenAPI 以外の広範連携）
- L9-L11（Run 工程）への一括反映
- 本 PLAN で未確定の PM-承認を要する組織方針変更
- 追加のライセンス審査を伴う外部ツール採用

## §10 改訂履歴

| 日付 | バージョン | 変更内容 | 変更者 |
| --- | --- | --- | --- |
| 2026-04-30 | v4 | `PLAN-004` を §1-§10 で再構成。§3 を A/B/C/D 4 軸化（v3報奨設計維持＋Implementation Readiness, Deliverable Adapter, Research/Review embed 追加）。§4 に Layer0-3 と L1-L3 sprint 構造、§5 に readiness exit 条件付き gate 方針、§7 に Sprint7-10 追加、関連 PLAN・リスク更新を反映。 | Docs (Codex) |
| 2026-04-30 | v3 | TL レビュー P1×1 + P2×2 + P3×1 を反映し、報奨設計の方針統一と G2-G7 hook、`accuracy_score` 精度検証、redaction 方針、R-05/R-06 追加、改訂履歴追記。 | Docs (Codex) |
| 2026-04-30 | v2 | `accuracy_weight` 単調増加表現を撤回し、根拠ベース化。`PLAN-004` と `G3` 境界統一、secret/PII 対応の基本方針を追加。 | Docs (Codex) |
| 2026-04-30 | v1 | 初版。`HELIX` 評価哲学を速度から正確・精度志向へ再定義し、TL/Codex 観点、gate 重み、`helix accuracy report`、L8 組込条件を確定。 | Docs (Codex) |

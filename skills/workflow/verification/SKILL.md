---
name: verification
description: L1〜V-L6の各検証レイヤーに加え、Spec駆動検証とL8仕様突合チェックを提供（V-L3〜V-L6は本スキル固有番号）。Reverse モード（RG0-RG3 + RGC）の検証基盤を含む
metadata:
  helix_layer: all
  triggers:
    - 設計レビュー時
    - 実装完了時
    - デプロイ前
    - 品質ゲート通過時
    - Reverse ゲート（RG0-RG3）通過時
    - RGC Gap 閉塞検証時
  verification:
    - "L1-L2, L3_api, V-L3〜V-L6 全レイヤー status: pass"
    - "L1: 要件カバレッジ 100% (functional/non-functional)"
    - "L2: 画面-API-DBマッピング 未対応 0件"
    - "L3_api: 型一致率 100% (FE-BE-DB)"
    - "V-L3: API仕様カバレッジ ≥95%"
    - "V-L4: 脆弱性 0件 (critical/high)"
    - "V-L5: カバレッジ ≥70% (unit), クリティカルパス 100%"
    - "V-L6: SLO定義 3種以上, アラートルール ≥1件"
    - "RG0: モジュール coverage 100%, unknowns cataloged"
    - "RG1: 契約 coverage ≥90%, confidence high ≥80%, contradictions 0"
    - "RG2: ADR confidence high ≥70%, contradictions 0, adversarial-review 済"
    - "RG3: PO 検証済み仮説率 ≥80%, unknown 全件タスク割当済み"
    - "RGC: gap_register 全件 status 付与, 昇格判定完了"
compatibility:
  claude: true
  codex: true
---

# 検証スキル（L1-L2, L3_api, V-L3〜V-L6）

## 適用タイミング

このスキルは以下の場合に読み込む：
- 各開発フェーズの品質ゲート通過時
- 設計・実装・テスト・デプロイの検証時
- HELIXフレームワークのL検証実行時

**accuracy_weight**: 各 gate の重み付けは [gate-policy.md §accuracy_weight](../../tools/ai-coding/references/gate-policy.md) を参照 (PLAN-004 で導入)

---

## フェーズ別判断チェックリスト

各フェーズで Go/No-Go を判断する際の最小チェック項目。

### L1（要件）

- スコープ確定（対象/対象外が明示）
- NFR 基準（性能・可用性・セキュリティ等）
- PoC 要否（不確実性が高い領域の有無）
- 事前調査要否（技術・法務・運用）

### L2（設計）

- ADR 作成（意思決定の記録）
- 技術選定理由（比較根拠と採否）
- 脅威モデル（STRIDE/OWASP 観点）
- adversarial-review 要否（反証レビュー実施判断）

### L3（詳細設計・契約）

- API 凍結（エンドポイント/型/エラー）
- DB 凍結（スキーマ/制約/マイグレーション方針）
- 契約凍結（FE-BE-DB 整合）
- テスト方針（Unit/Integration/E2E の配分）

### L4（実装）

- リファクタ vs 突進（負債返済か機能優先か）
- 共通化（重複 3 箇所以上の扱い）
- 外部化（プロジェクト横断で使うか）
- interrupt 発動（前提崩壊・設計差戻し要否）
- ship or fix（出荷可能性の判断）

### L5（Visual）

- V0/V1/V2 分類（品質段階の判定）
- a11y 合格（最低基準クリア）
- デザイン完了（仕様との一致）

### L6（統合検証）

- テスト十分性（網羅性・安定性）
- 性能合格（目標 SLO/指標達成）
- セキュリティ合格（Critical/High なし）
- RC 判定（リリース候補可否）

### L7（デプロイ）

- ロールバック判断基準（切戻し条件）
- 安定判定（監視・アラート正常）
- 人間承認（本番影響の承認）

### L8（受入）

- 受入/差戻し（要件突合結果）
- 残余リスク受容（受容可否の明示）
- 運用引継ぎ完了（Runbook/SLO/連絡経路）

---

## 1. 検証レイヤー概要

```
L1:    要件検証      ← 企画書・要件定義
L2:    設計検証      ← 基本設計・詳細設計
L3_api: API整合性   ← Frontend/Backend/DB間の型・スキーマ一致（★Helix中核、Helix L3内）
V-L3:  コントラクト  ← API仕様・インターフェース定義
V-L4:  依存関係      ← パッケージ・外部サービス
V-L5:  テスト検証    ← 単体・結合・E2E
V-L6:  運用検証      ← 監視・アラート・SRE

※ V-L3〜V-L6 は本スキル固有の検証レイヤー番号。
  HELIXフェーズ番号（L3=詳細設計+API契約、L4=実装、L5=Visual Refinement、L6=統合検証、L7=デプロイ、L8=受入）とは別体系。
```

---

## 2. L1: 要件検証

### 検証項目

```
□ 要件の完全性
  - 全機能要件が定義されている
  - 非機能要件が明確
  - 受け入れ条件が具体的

□ 要件の一貫性
  - 矛盾する要件がない
  - 優先順位が明確
  - スコープが定義されている

□ 要件の追跡可能性
  - 要件IDが付与されている
  - ビジネス目標との紐付け
  - テストケースへの対応
```

### 出力

```yaml
l1_verification:
  status: pass/fail
  coverage:
    functional: 100%
    non_functional: 100%
  issues: []
  timestamp: "ISO8601"
```

---

## 3. L2: 設計検証

### 検証項目

```
□ 設計の妥当性
  - 要件を満たす設計か
  - 技術選定の根拠
  - スケーラビリティ考慮

□ 設計の整合性
  - 画面設計とAPI設計の整合
  - データモデルとビジネスロジックの整合
  - コンポーネント間の依存関係

□ 設計の実現可能性
  - 期間内に実装可能か
  - チームスキルとのマッチ
  - 技術的リスクの評価
```

### L2 補足: 設計深掘り検証

```
□ エッジケースの考慮
  - 境界値での動作
  - 異常系の処理
  - 同時実行の考慮

□ パフォーマンス設計
  - ボトルネックの特定
  - キャッシュ戦略
  - インデックス設計
```

---

## 4. L3: API整合性検証（API契約検証）★

→ 詳細は `skills/workflow/api-contract/SKILL.md` を参照（Helix L3 API契約）

### 検証項目

```
□ Frontend/Backend/DB間の型一致
  - リクエスト/レスポンスの型定義がFE/BE間で一致
  - DBスキーマとバックエンド型の整合
  - 列挙型・定数値の同期

□ スキーマ整合性
  - OpenAPI仕様と実装の一致
  - 契約テスト（Consumer-Driven Contract）の通過

□ 自動検証
  - Codex による型一致率の数値判定
  - 不合格時はL3 API契約検証内でループ（契約再定義 or 各層の実装修正）
```

### 出力

```yaml
l3_api_verification:
  status: pass/fail
  type_match_rate: "100%"  # Frontend ↔ Backend ↔ DB
  schema_coverage: "100%"
  issues: []
  timestamp: "ISO8601"
```

---

## 5. V-L3: コントラクト検証

→ 詳細は `skills/workflow/api-contract/SKILL.md` を参照

### 検証項目

```
□ API仕様定義の完全性
□ エラーコード網羅
□ 後方互換性
□ バージョニング戦略
```

---

## 6. V-L4: 依存関係検証

→ 詳細は `skills/workflow/dependency-map/SKILL.md` を参照

### 検証項目

```
□ 依存パッケージの脆弱性
□ ライセンス互換性
□ バージョン互換性
□ 循環依存の検出
```

---

## 7. V-L5: テスト検証

→ 詳細は `skills/workflow/quality-lv5/SKILL.md` を参照

### 検証項目

```
□ テストカバレッジ
□ テストピラミッド比率
□ クリティカルパスの網羅
□ 回帰テストの実行
```

---

## 8. V-L6: 運用検証

> **V-L6 と L7 の責務境界**: V-L6 は「運用体制の充足性」（可観測性設計・アラート設定・運用手順の存在）を検証する。
> 「デプロイ後の SLO 達成」は L7.3（本番安定性ゲート＝G7）の責務。
> V-L6 は統合検証フェーズ（L5 → L6）で実施され、L7 の開始前提として pass が必要。

### 検証項目

```
□ 可観測性
  - ログ出力の網羅
  - メトリクス収集
  - トレーシング設定

□ アラート設定
  - SLO/SLI定義
  - アラートしきい値
  - エスカレーションパス

□ 運用手順
  - デプロイ手順書
  - ロールバック手順
  - 障害対応フロー
```

---

## 8.5. フェーズ証跡 vs L6 集約再検証

| 検証項目 | 証跡作成フェーズ | L6 で再検証するか | 備考 |
|---------|----------------|-----------------|------|
| 要件カバレッジ | L1（G1 通過時） | ○ 突合のみ | 実装結果と要件の対応確認 |
| 設計整合性 | L2（G2 通過時） | ○ 差分検証 | 実装が設計から逸脱していないか |
| API/型一致率 | L3（G3 通過時） | ○ 再計測 | FE↔BE↔DB の型一致を実コードで再検証 |
| 実装品質 | L4（各ゲート） | △ サンプル | codex review 結果の確認（全件再実行はしない） |
| ビジュアル適合 | L5（G5 通過時） | △ スクリーンショット | UI変更時のみ |
| 依存関係・脆弱性 | L3/L4 | ○ 再スキャン | npm audit / pip-audit を最新状態で実行 |
| テストカバレッジ | L4（実装.4） | ○ 再実行 | 全テストスイート実行 |
| 運用体制 | L6 で新規作成 | — | SLO定義・アラート・運用手順の存在確認 |

- ○: L6 で必ず再検証（最新状態で確認）
- △: L6 で確認するが、問題なければ証跡流用可
- —: 該当フェーズの成果物

---

## 9. 検証実行フロー

```
開始
  │
  ├─→ L1検証 ──→ fail → 要件修正 → 再検証
  │     │
  │     pass
  │     ↓
  ├─→ L2検証 ──→ fail → 設計修正 → 再検証
  │     │
  │     pass
  │     ↓
  ├─→ L3 API整合性検証 → fail → 型/スキーマ修正 → 再検証 ★API整合性
  │     │
  │     pass
  │     ↓
  ├─→ V-L3検証 ──→ fail → API仕様修正 → 再検証
  │     │
  │     pass
  │     ↓
  ├─→ V-L4検証 ──→ fail → 依存修正 → 再検証
  │     │
  │     pass
  │     ↓
  ├─→ V-L5検証 ──→ fail → テスト追加 → 再検証
  │     │
  │     pass
  │     ↓
  └─→ V-L6検証 ──→ fail → 運用設定修正 → 再検証
        │
        pass
        ↓
      完了（デプロイ可能）
```

---

## 10. 検証結果の記録

### 検証レポートテンプレート

```yaml
verification_report:
  project: "project-name"
  version: "1.0.0"
  timestamp: "ISO8601"

  layers:
    L1:
      status: "pass"
      coverage: "100%"
      issues: []
    L2:
      status: "pass"
      coverage: "100%"
      issues: []
    L3_api:
      status: "pass"
      type_match_rate: "100%"
      schema_coverage: "100%"
      issues: []
    V-L3:
      status: "pass"
      coverage: "95%"
      issues:
        - id: "VL3-001"
          severity: "low"
          description: "Optional field not documented"
    V-L4:
      status: "pass"
      vulnerabilities: 0
      outdated: 2
    V-L5:
      status: "pass"
      unit_coverage: "85%"
      integration_coverage: "70%"
      e2e_coverage: "critical_paths"
    V-L6:
      status: "pass"
      observability: "complete"
      alerts: "configured"

  # Reverse モード（該当時のみ追加）
  reverse_layers:
    RG0:
      status: "pass"
      coverage: "100%"
      unknowns_cataloged: true
      issues: []
    RG1:
      status: "pass"
      api_coverage: "92%"
      db_coverage: "95%"
      type_coverage: "88%"
      confidence_high_rate: "83%"
      contradictions: 0
      issues: []
    RG2:
      status: "pass"
      adr_confidence_high_rate: "75%"
      contradictions: 0
      adversarial_review: "completed"
      issues: []
    RG3:
      status: "pass"
      po_verified_rate: "85%"
      unknown_tasks_assigned: true
      issues: []
    RGC:
      status: "pass"
      gap_closed: 38
      gap_partial: 3
      gap_open: 1
      po_approval: "PO-approved"
      issues: []

  overall: "pass"
  notes: "Ready for production deployment"
```

---

## 11. 自動化ツール

### CI/CDパイプライン統合

```yaml
# GitHub Actions例
verify:
  jobs:
    l1-requirements:
      # 要件追跡ツール連携
    l2-design:
      # 設計ドキュメント検証
    l3-api-integrity:
      # Frontend/Backend/DB型一致検証（Codex）
    vl3-contract:
      # OpenAPI検証
    vl4-dependencies:
      - run: npm audit
      - run: npx license-checker
    vl5-testing:
      - run: npm run test:coverage
      - run: npm run test:e2e
    vl6-operations:
      # 監視設定検証
```

---

## 12. 監査の責任者・対応SLA（Helix Policy）

> 出典: docs/archive/v-model-reference-cycle-v2.md §運用ポリシー4

### RACI定義

| 役割 | 担当 |
|------|------|
| Accountable | PM（Opus） |
| Responsible | SE（Codex 5.3）／担当エージェント |
| Consulted | TL（Codex 5.4） |
| Informed | PO（人間） |

### 対応SLA（回数ベース）

> 時間ベースの SLA は現行環境で計測手段がないため、回数ベースに置換（アーカイブの時間値は参考のみ）。

| 重大度 | 対応基準 | エスカレーション閾値 |
|--------|----------|---------------------|
| critical | 次ゲート到達前に対応必須 | 未対応のまま次フェーズ進行 → 人間通知 + 停止必須 |
| high | 同一フェーズ内で対応 | 2回未対応 → 人間通知 |
| medium | 次マイルストーンまでに対応 | 3回未対応 → 人間通知 |
| low | 終端レトロまでに対応 | ミニレトロで記録のみ |

### SLAトリガー

```
以下のイベントでSLAカウント開始:
  - decision_conflict: 決定事項の矛盾検出
  - critical_degradation: 品質の重大劣化
  - provisional_expiry: 暫定決定の期限到達
```

---

## 13. 人間エスカレーション条件（Helix Policy）

> 出典: docs/archive/v-model-reference-cycle-v2.md §人間エスカレーション条件

以下の条件に該当する場合、エージェントは**必ず**人間にエスカレーションする。

### 即時エスカレーション（Critical）

| 条件 | エスカレーション形式 |
|------|---------------------|
| 本番環境への影響 | 実行前に承認を得る |
| 外部API連携の新規追加/既存変更 | API選定・変更の承認を得る |
| 認証・認可ロジックの変更 | 設計承認を得る |
| 課金・決済関連 | 実装前に承認を得る |
| 個人情報の取り扱い変更 | 方針決定を仰ぐ |
| ライセンス・著作権関連 | 判断を仰ぐ |
| **IIP P3（実装内割り込み: 人間エスカレ）** | スコープ/前提の根本変更が必要。状況報告+選択肢提示 |

Critical条件は人間が無応答でも「推奨選択肢で続行」してはならない。明示的な承認を待機する。

### 判断エスカレーション（Decision Required）

| 条件 | エスカレーション形式 |
|------|---------------------|
| MVPスコープの縮小 | 選択肢を提示し承認を得る |
| 期限延長の必要性 | 状況報告と選択肢提示 |
| 技術選定のトレードオフ | 比較表を提示し判断を仰ぐ |
| 要件の解釈が曖昧 | 解釈案を提示し確認（※技術詳細補完は自律判断可） |
| スコープ曖昧な要件 | 対応方針を確認（※暗黙の前提は自律判断可） |
| コスト超過の見込み | 見積もりと代替案を提示 |

### 進捗エスカレーション（Progress Alert）

| 条件 | 閾値 |
|------|------|
| 同一タスクでのリトライ回数（合計試行: ゲート内+タスク通算） | 5回以上 |
| レイヤー間エスカレーション | L1まで到達 |
| 想定外エラーの継続 | 3回連続 |
| 進捗停滞 | 1タスク2時間以上 |
| **IIP `interrupted` 発生** | P2 以上は即通知（P0/P1 は進捗報告に含める） |

**`interrupted` と `failed` の扱い:**
- `failed`（既知前提内ミス）→ リトライカウントに加算。上記「5回以上」の閾値に含める
- `interrupted`（IIP: 前提崩壊）→ リトライカウントに**含めない**。影響度分類に従い差し戻し

---

## 14. V字モデル検証サイクル

各レイヤーは独立した検証ループを持ち、左（計画）と右（検証）の対比で品質を確認する。

```
L1  要件定義 ←──────────────────→ 受入検証（L8）
L2    設計書 ←────────────────→ 設計整合性検証
L3      詳細設計+API契約 ←──→ API整合性検証+依存関係検証+テスト検証
             L4 実装（底）
             L5 Visual Refinement
L6        統合検証 ←────────→ E2E・性能・セキュリティ検証
L7             デプロイ ←──→ 本番検証
```

### レイヤー内検証ループ

```
設計書 → 契約/仕様作成 → 実装突合 → 一致率判定
  ↑                                    │
  │                    100%? ──No──→ 修正指示
  │                      │
  └──────────────────── Yes → 次レイヤーへ

ループ上限: 各レイヤー最大5回
超過時: 上位レイヤーにエスカレーション
最上位(L1)超過時: 人間にエスカレーション
```

→ 詳細は `references/verification-cycle.md` を参照

---

## 15. Reverse モード検証（HELIX Reverse 対応）

Forward 検証が「**仕様に対する実装の適合**」を判定するのに対し、Reverse 検証は「**証拠に対する仮説の十分性**」を判定する。

→ Reverse フロー詳細: `workflow/reverse-analysis/SKILL.md`
→ Reverse ゲート定義: `skills/tools/ai-coding/references/gate-policy.md §Reverse ゲート`

### 15.1 Forward ↔ Reverse 検証の対比

| | Forward 検証 | Reverse 検証 |
|--|-------------|-------------|
| 問い | 「実装は仕様を満たすか？」 | 「証拠は仮説を支持するか？」 |
| 判定基準 | 一致率・カバレッジ・pass/fail | **coverage, confidence, contradictions, unknowns** |
| 不合格時 | 実装修正 → 再検証 | 追加証拠収集 or 仮説修正 → 再検証 |
| 完了条件 | 全レイヤー pass | 仮説の反証可能性が確保され、unknowns が管理下 |

### 15.2 Reverse ゲート検証項目

#### RG0 証拠網羅検証

```
□ evidence_map にスコープ内全モジュール含有
□ 依存グラフ（内部 + 外部）完成
□ DB スキーマ取得済み（テーブル・インデックス・制約）
□ unknowns が全て cataloged（未分析でも記録済み）
□ ファイルツリーで未スキャン領域 = 0
```

```yaml
rg0_verification:
  status: pass/fail
  timestamp: "ISO8601"
  coverage: "100%"  # モジュール coverage
  unknowns_cataloged: true
  issues: []
```

#### RG1 契約検証

```
□ API エンドポイント抽出 coverage ≥ 90%
□ DB スキーマ抽出 coverage ≥ 90%
□ 型マッピング（FE↔BE↔DB）抽出 coverage ≥ 90%
□ confidence high の契約 ≥ 80%
□ characterization tests で主要パス検証済み
□ contradictions 0（未解決）
□ 契約抽出と検証設計が分離されている（混在禁止）
```

```yaml
rg1_verification:
  status: pass/fail
  timestamp: "ISO8601"
  api_coverage: "92%"
  db_coverage: "95%"
  type_coverage: "88%"
  confidence_high_rate: "83%"
  contradictions: 0
  issues: []
```

#### RG2 設計検証

```
□ アーキテクチャスタイル特定済み
□ コンポーネント境界・依存関係グラフ完成
□ ADR 仮説の confidence high ≥ 70%
□ contradictions 0（未解決）
□ adversarial-review 実施済み（M/L サイジング時）
□ パターン一貫性分析完了（consistent / inconsistent 分類）
```

```yaml
rg2_verification:
  status: pass/fail
  timestamp: "ISO8601"
  architecture_identified: true
  adr_confidence_high_rate: "75%"
  contradictions: 0
  adversarial_review: completed  # or skipped_s_sizing
  issues: []
```

#### RG3 仮説検証

```
□ PO 検証済み仮説率 ≥ 80%
□ 全仮説に Intended / Accidental / Unknown / Deprecated 分類済み
□ unknown 分類の全項目に調査タスク割当済み
□ accidental / deprecated の全項目に対応方針決定済み
□ PO が判断できない項目はエスカレーション済み
```

```yaml
rg3_verification:
  status: pass/fail
  timestamp: "ISO8601"
  po_verified_rate: "85%"
  classification:
    intended: 28
    accidental: 3
    unknown: 2
    deprecated: 2
  unknown_tasks_assigned: true
  issues: []
```

### 15.3 RGC Gap 閉塞検証

Forward HELIX 完了後に実施する。gap_register の各項目が閉じたことを検証する。

```
□ gap_register 全項目に closed / partial / open ステータス付与
□ closed 項目に evidence（テスト結果、コード差分等）記録済み
□ Behavioral Defect: テスト追加 + pass
□ Contract Drift: R1 characterization tests 再実行で差分 0
□ Architectural Debt: R2 パターン分析再実行で violation 0
□ Requirements Gap: R3 PO 検証で intended 確認
□ Security/Compliance: セキュリティゲート準拠
□ 仮説成果物の昇格判定完了（intent_hypotheses は PO 承認必須）
□ 残存 gap → debt_register に移管済み
□ 新規発見 gap → gap_register に追記 + routing 済み
```

```yaml
rgc_verification:
  status: pass/fail
  timestamp: "ISO8601"
  gap_summary:
    total: 42
    closed: 38
    partial: 3
    open: 1
  artifact_promotion:
    observed_contracts: promoted  # → L3 API 契約正本（RG1 pass + gap 閉塞）
    as_is_design: promoted        # → L2 設計書正本（RG2 pass + gap 閉塞）
    intent_hypotheses: promoted   # → L1 要件リスト正本（RG3 pass + PO 承認）
    po_approval: "PO-approved"    # intent_hypotheses 昇格の必須承認
  remaining_gaps:
    debt_register: 3
    next_iteration: 1
  issues: []
```

### 15.4 Reverse 検証フロー

> **フェーズスキップ時**: Reverse サイジングにより R2/R3 を skip する場合、対応する RG2/RG3 検証も N/A となる。
> 詳細: `workflow/reverse-analysis/SKILL.md §フェーズスキップ決定木`

```
R0 完了（フルフロー時。skip 時は該当ゲートを N/A で記録）
  ├─→ RG0 検証 ──→ fail → 未スキャン領域の追加調査
  │     │
  │     pass
  │     ↓
  ├─→ RG1 検証 ──→ fail → confidence low の追加テスト / 再抽出
  │     │
  │     pass
  │     ↓
  ├─→ RG2 検証 ──→ fail → 矛盾 ADR の追加調査 / 仮説修正
  │     │
  │     pass
  │     ↓
  └─→ RG3 検証 ──→ fail → PO 追加ヒアリング / unknown 調査
        │
        pass
        ↓
      R4 Gap & Routing → Forward HELIX → RGC 検証
```

---

## 形式検証（Formal Verification）入門

### コンセプト

テストはサンプル入力の検証であり、形式検証は全入力空間に対する性質の証明を目指す。

### 実践的な適用範囲

全コードへの適用は非現実的なため、検証価値の高い境界に限定して適用する。

- 契約検証: D-CONTRACT の型レベル整合性
- 状態機械: 画面遷移の到達可能性証明
- プロトコル: API リクエスト/レスポンスの不変条件検証

### ツール

- TypeScript: `ts-morph` を使った型レベル検証
- Python: `mypy --strict` + `beartype`
- 軽量形式検証: Alloy / TLA+（ドメインモデル検証の入門用途）

### HELIX 統合

- D-CONTRACT の状態境界を形式的に検証する手法を採用する
- fullstack G3 で型整合チェックを強制し、通過条件に含める

---

## Spec 駆動検証

仕様成果物（`D-API` / `D-CONTRACT` / `D-DB`）を起点に、実装後テストを自動導出する。
実装コードから逆算してテストを作るのではなく、仕様を正として不足を検出する。

### 仕様 → テスト自動導出の基本手順

1. `D-API`: エンドポイント、メソッド、期待ステータスを抽出
2. `D-CONTRACT`: Consumer/Provider の契約条件を抽出
3. `D-DB`: テーブル、制約、NULL可否、境界値条件を抽出
4. テンプレートに流し込み、`pytest` / `Jest` のテスト雛形を生成
5. G4 で自動実行し、L8 で仕様突合レポートに統合

### API 仕様 → マトリクステスト

最小単位は `endpoint × method × status_code`。

| endpoint | method | status | 目的 |
|----------|--------|--------|------|
| `/api/v1/users` | `GET` | `200` | 正常系 |
| `/api/v1/users` | `POST` | `201` | 作成成功 |
| `/api/v1/users/{id}` | `GET` | `404` | 存在しないID |
| `/api/v1/users` | `POST` | `422` | バリデーション違反 |

### DB スキーマ → CRUD / 制約 / 境界値テスト

`テーブル × CRUD × 制約違反 × NULL/境界値` を最低セットにする。

- CRUD: create/read/update/delete の往復整合
- 制約違反: UNIQUE / FK / CHECK / NOT NULL の失敗確認
- NULL/境界値: 最小値、最大値、空文字、長さ超過

### 契約仕様 → Consumer / Provider 契約テスト

- Consumer 視点: 期待レスポンス構造・必須フィールド・型
- Provider 視点: 実際の応答が契約を満たすか
- 双方向差分: Consumer 期待にない項目、Provider 未実装項目を検出

### HELIX Deliverable Matrix 統合

| Deliverable | 生成タイミング | 自動化内容 |
|------------|----------------|------------|
| `D-API` | G4 | API テスト自動生成・実行 |
| `D-CONTRACT` | G4 | 契約テスト自動生成 |
| `D-DB` | G4 | マイグレーションテスト自動生成 |

### テスト生成テンプレート（`pytest` / `Jest`）

#### `pytest`

```python
import pytest

@pytest.mark.parametrize(
    "method,path,expected_status",
    [
        ("GET", "/api/v1/users", 200),
        ("POST", "/api/v1/users", 201),
        ("POST", "/api/v1/users", 422),
    ],
)
def test_api_spec_matrix(client, method, path, expected_status):
    response = client.request(method, path)
    assert response.status_code == expected_status
```

#### `Jest`

```typescript
describe('D-API matrix', () => {
  const cases = [
    { method: 'get', path: '/api/v1/users', status: 200 },
    { method: 'post', path: '/api/v1/users', status: 201 },
    { method: 'post', path: '/api/v1/users', status: 422 },
  ] as const

  test.each(cases)('$method $path => $status', async ({ method, path, status }) => {
    const res = await request(app)[method](path)
    expect(res.status).toBe(status)
  })
})
```

---

## 仕様突合チェック

L8 受入時に `D-*` 成果物と実装コードを自動突合し、仕様差分を検出する。

### 検出対象

- 仕様に書いてあるが実装に存在しない項目（spec-only）
- 実装に存在するが仕様に書いていない項目（impl-only）

### `rg` ベースの突合パターン

```bash
# 例1: D-API と実装ルータ突合（spec-only / impl-only）
rg -n "^(GET|POST|PUT|PATCH|DELETE)\\s+/api" docs/features/**/D-API/*.md | sort > /tmp/spec_api.txt
rg -n "@(router\\.|app\\.|bp\\.)?(get|post|put|patch|delete)\\(" src/ backend/ | sort > /tmp/impl_api.txt
comm -23 /tmp/spec_api.txt /tmp/impl_api.txt   # spec-only
comm -13 /tmp/spec_api.txt /tmp/impl_api.txt   # impl-only

# 例2: D-DB と migration 突合
rg -n "CREATE TABLE|ALTER TABLE|CONSTRAINT" docs/features/**/D-DB/*.md | sort > /tmp/spec_db.txt
rg -n "CREATE TABLE|ALTER TABLE|CONSTRAINT" migrations/ db/ | sort > /tmp/impl_db.txt
comm -23 /tmp/spec_db.txt /tmp/impl_db.txt
comm -13 /tmp/spec_db.txt /tmp/impl_db.txt

# 例3: D-CONTRACT と契約テスト突合
rg -n "consumer|provider|contract|schema" docs/features/**/D-CONTRACT/*.md | sort > /tmp/spec_contract.txt
rg -n "contract|consumer|provider|pact|schema" tests/ contracts/ | sort > /tmp/impl_contract.txt
comm -23 /tmp/spec_contract.txt /tmp/impl_contract.txt
comm -13 /tmp/spec_contract.txt /tmp/impl_contract.txt
```

### 出力フォーマット（L8 添付）

```yaml
spec_reconciliation:
  d_api:
    spec_only: []
    impl_only: []
  d_contract:
    spec_only: []
    impl_only: []
  d_db:
    spec_only: []
    impl_only: []
  verdict: pass/fail
```

---

## チェックリスト

### 検証開始前

```
□ 検証対象の範囲を確認
□ 前提条件を確認
□ 必要なツール・環境を準備
```

### 検証実行中

```
□ 各レイヤーを順次実行
□ 発見した問題を記録
□ ブロッカーは即座にエスカレーション
```

### 検証完了後

```
□ 検証レポートを作成
□ 未解決の問題をトラッキング
□ 次フェーズへの申し送り
```

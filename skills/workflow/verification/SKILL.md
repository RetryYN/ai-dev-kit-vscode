---
name: verification
description: L1〜L6の各検証レイヤーのチェック項目と結果記録フォーマットを提供
metadata:
  helix_layer: all
  triggers:
    - 設計レビュー時
    - 実装完了時
    - デプロイ前
    - 品質ゲート通過時
  verification:
    - "L1-L6の全レイヤー status: pass"
    - "L1: 要件カバレッジ 100% (functional/non-functional)"
    - "L2: 画面-API-DBマッピング 未対応 0件"
    - "L2.5: 型一致率 100% (FE-BE-DB)"
    - "V-L3: API仕様カバレッジ ≥95%"
    - "V-L4: 脆弱性 0件 (critical/high)"
    - "V-L5: カバレッジ ≥70% (unit), クリティカルパス 100%"
    - "V-L6: SLO定義 3種以上, アラートルール ≥1件"
compatibility:
  claude: true
  codex: true
---

# 検証スキル（L1-L6）

## 適用タイミング

このスキルは以下の場合に読み込む：
- 各開発フェーズの品質ゲート通過時
- 設計・実装・テスト・デプロイの検証時
- HELIXフレームワークのL検証実行時

---

## 1. 検証レイヤー概要

```
L1:    要件検証      ← 企画書・要件定義
L2:    設計検証      ← 基本設計・詳細設計
L2.5:  API整合性    ← Frontend/Backend/DB間の型・スキーマ一致（★Helix中核）
V-L3:  コントラクト  ← API仕様・インターフェース定義
V-L4:  依存関係      ← パッケージ・外部サービス
V-L5:  テスト検証    ← 単体・結合・E2E
V-L6:  運用検証      ← 監視・アラート・SRE

※ V-L3〜V-L6 は本スキル固有の検証レイヤー番号。
  HELIXフェーズ番号（L3=依存関係、L4=工程表、L5=デプロイ、L6=受入）とは別体系。
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

## 4. L2.5: API整合性検証 ★

→ 詳細は `skills/workflow/api-contract/SKILL.md` を参照（Helix L2.5相当）

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
  - 不合格時はL2.5内でループ（契約再定義 or 各層の実装修正）
```

### 出力

```yaml
l2_5_verification:
  status: pass/fail
  type_match_rate: "100%"  # Frontend ↔ Backend ↔ DB
  schema_coverage: "100%"
  issues: []
  timestamp: "ISO8601"
```

---

## 5. L3: コントラクト検証

→ 詳細は `skills/workflow/api-contract/SKILL.md` を参照

### 検証項目

```
□ API仕様定義の完全性
□ エラーコード網羅
□ 後方互換性
□ バージョニング戦略
```

---

## 6. L4: 依存関係検証

→ 詳細は `skills/workflow/dependency-map/SKILL.md` を参照

### 検証項目

```
□ 依存パッケージの脆弱性
□ ライセンス互換性
□ バージョン互換性
□ 循環依存の検出
```

---

## 7. L5: テスト検証

→ 詳細は `skills/workflow/quality-lv5/SKILL.md` を参照

### 検証項目

```
□ テストカバレッジ
□ テストピラミッド比率
□ クリティカルパスの網羅
□ 回帰テストの実行
```

---

## 8. L6: 運用検証

> **V-L6 と L5 の責務境界**: V-L6 は「運用体制の充足性」（可観測性設計・アラート設定・運用手順の存在）を検証する。
> 「デプロイ後の SLO 達成」は L5.3（本番安定性ゲート）の責務。
> V-L6 は検証フェーズ（L4.7 → 検証）で実施され、L5 の開始前提として pass が必要。

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
  ├─→ L2.5検証 → fail → 型/スキーマ修正 → 再検証 ★API整合性
  │     │
  │     pass
  │     ↓
  ├─→ L3検証 ──→ fail → API仕様修正 → 再検証
  │     │
  │     pass
  │     ↓
  ├─→ L4検証 ──→ fail → 依存修正 → 再検証
  │     │
  │     pass
  │     ↓
  ├─→ L5検証 ──→ fail → テスト追加 → 再検証
  │     │
  │     pass
  │     ↓
  └─→ L6検証 ──→ fail → 運用設定修正 → 再検証
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
    L2.5:
      status: "pass"
      type_match_rate: "100%"
      schema_coverage: "100%"
      issues: []
    L3:
      status: "pass"
      coverage: "95%"
      issues:
        - id: "L3-001"
          severity: "low"
          description: "Optional field not documented"
    L4:
      status: "pass"
      vulnerabilities: 0
      outdated: 2
    L5:
      status: "pass"
      unit_coverage: "85%"
      integration_coverage: "70%"
      e2e_coverage: "critical_paths"
    L6:
      status: "pass"
      observability: "complete"
      alerts: "configured"

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
    l2_5-api-integrity:
      # Frontend/Backend/DB型一致検証（Codex）
    l3-contract:
      # OpenAPI検証
    l4-dependencies:
      - run: npm audit
      - run: npx license-checker
    l5-testing:
      - run: npm run test:coverage
      - run: npm run test:e2e
    l6-operations:
      # 監視設定検証
```

---

## 12. 監査の責任者・対応SLA（Helix Policy）

> 出典: docs/archive/v-model-reference-cycle-v2.md §運用ポリシー4

### RACI定義

| 役割 | 担当 |
|------|------|
| Accountable | helix-auditor（監査エージェント）[現行: PM（Opus）が代替] |
| Responsible | task-owner（タスク担当エージェント） |
| Consulted | secondary-reviewer |
| Informed | human:project-owner |

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
L1  要件定義 ←──────────────────→ 受入検証（L6）
L2    設計書 ←────────────────→ 設計整合性検証
L2.5    API契約 ←──────────→ API整合性検証
L3       依存関係 ←──────→ 依存関係検証
L4         工程表 ←────→ テスト検証
             L4.5 実装（底）
             L4.7 ビジュアル適用
L5             デプロイ ←→ 本番検証
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

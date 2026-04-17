---
name: schedule-wbs
description: L3 工程表 (WBS + feature flag + rollback) 生成スキル。G3 通過条件を直接充足
metadata:
  helix_layer: L3
  triggers:
    - L3 工程表生成時
    - API Freeze 後の実装計画時
    - feature flag 設定時
    - rollback 計画時
  verification:
    - "工程表が docs/ または .helix/ に存在"
    - "各タスクに feature flag と rollback が記載 (不要な場合は N/A 明記)"
    - "L4 Sprint 番号が割り当てられている"
compatibility:
  claude: true
  codex: true
---

# L3 工程表スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- L3 で実装着手前の工程表を確定する時
- G3 の通過条件（WBS/担当/依存/環境/feature flag/rollback）を満たす時
- API/Schema Freeze 後に実装順序を固定する時

---

## 1. 目的と位置づけ

- 本スキルは **L3 実装計画の確定** を目的とする
- 出力は `docs/` または `.helix/` 配下の工程表ファイル
- G3 通過に必要な計画証跡を直接作成する

### project-management との差分

- `project-management`: L1 中心の全体進捗管理（ダッシュボード・報告・運用）
- `schedule-wbs`: L3 中心の実装直前計画（WBS、feature flag、rollback、環境切替）
- 進捗可視化よりも **実装順序の凍結とリスク封じ込め** を優先する

---

## 2. L3 工程表テンプレート

```markdown
# L3 実装工程表

## 0. 前提
- API Freeze: YYYY-MM-DD
- Schema Freeze: YYYY-MM-DD
- 対象リリース: vX.Y.Z
- 作成日: YYYY-MM-DD

## 1. WBS
| WBS ID | タスク | 担当 | 依存 | 期間 | 環境 | L4 Sprint | feature flag | rollback |
|--------|--------|------|------|------|------|-----------|--------------|----------|
| WBS-01 | 例: API実装 | @se-a | WBS-00 | 1.0d | dev | .1b-.2 | ff_api_v2 | db migration down + flag off |
| WBS-02 | 例: UI接続 | @fe-a | WBS-01 | 0.5d | dev/stg | .3 | ff_ui_v2 | route切替 + build rollback |
| WBS-03 | 例: 統合テスト | @qa-a | WBS-01,WBS-02 | 0.5d | stg | .4-.5 | N/A | test baseline へ戻す |

## 2. マイルストーン
- MS1: L4 .2 完了（主要機能の骨格）
- MS2: L4 .4 完了（回帰テスト pass）
- MS3: L4 .5 完了（最終レビュー pass）

## 3. クリティカルパス
- WBS-01 -> WBS-02 -> WBS-03

## 4. リスクと緩和
| リスク | 影響 | 緩和策 | 所有者 |
|--------|------|--------|--------|
| API応答仕様差分 | 高 | contract test 先行 | @se-a |
```

テンプレート必須列:
- `タスク` / `担当` / `依存` / `期間` / `環境`
- `feature flag` / `rollback`
- `L4 Sprint`

---

## 3. feature flag 設計指針

### 基本方針

- 新機能は原則 flag で保護する
- flag 名は機能とスコープが識別可能であること
- 環境別の ON/OFF 方針を事前定義する

### 命名規則

```text
ff_<domain>_<feature>_<version>
例: ff_billing_invoice_v2
```

### 設計チェック

- デフォルト値を明記（`false` 推奨）
- 有効範囲（全体/テナント/ユーザー群）を明記
- 切替手順と監視指標を明記
- 廃止期限（cleanup date）を明記

### 反映テンプレート

```markdown
#### feature flag 定義
- flag: ff_xxx
- default: false
- rollout: internal -> beta -> all
- owner: @担当
- metrics: error_rate, latency_p95
- cleanup_deadline: YYYY-MM-DD
```

---

## 4. rollback 計画テンプレート

```markdown
## Rollback Plan

### 1) 発火条件
- エラーレート > 2%
- p95 レイテンシ > 既存比 30% 悪化
- 重大不具合 (Sev1/Sev2) 発生

### 2) 手順
1. feature flag を OFF
2. 新規ルーティングを旧経路へ戻す
3. 必要に応じて DB migration を down
4. smoke test を再実行
5. 監視値が復帰したことを確認

### 3) 体制
- 実行者: @oncall
- 承認者: @tl
- 連絡先: #incident-xxx

### 4) 復旧判定
- health check green
- 主要 API 成功率 >= 99%
- 既知クリティカル障害 0
```

ルール:
- rollback が不要なタスクでも `N/A` を明記する
- DB 変更を含む場合は down 可否とデータ整合方針を記載する

---

## 5. マイクロスプリント (.1a〜.5) との紐付け

| L4 Sprint | 目的 | WBSでの記載ルール |
|-----------|------|-------------------|
| .1a | コード調査 | 影響範囲、既存テスト、依存調査タスクを明示 |
| .1b | 変更計画 | 実装順、担当、前提条件、受入条件を明示 |
| .2 | 骨格実装 | 最小動作と flag 配下実装を明示 |
| .3 | 強化実装 | エラーハンドリング、セキュリティ、互換性対策を明示 |
| .4 | 検証固定 | テスト項目、実施環境、合否基準を明示 |
| .5 | 仕上げ | レビュー修正、ドキュメント同期、残課題管理を明示 |

記載形式例:
- `L4 Sprint: .1a-.2`
- `L4 Sprint: .3`

---

## 6. G3 通過のための最終チェック

```text
□ 工程表ファイルが docs/ または .helix/ に存在
□ 全タスクに担当・依存・期間・環境がある
□ 全タスクに feature flag と rollback がある（不要時 N/A）
□ L4 Sprint 番号が全タスクにある
□ API/Schema Freeze 日付が明記されている
□ クリティカルパスと高リスク対策が記載されている
```

---

## 7. 出力先の推奨

- `docs/plan/l3-schedule-wbs.md`
- `.helix/plans/l3-schedule-wbs.md`

どちらを採用してもよいが、同一プロジェクト内で統一する。

---

## 8. 失敗パターン

- WBS に feature flag/rollback 列が存在しない
- 実装順はあるが依存関係が明示されていない
- Sprint 番号が無く、L4 実装.1〜.5 への接続ができない
- rollback が「必要時対応」など曖昧記述のみ

上記がある場合、G3 は `failed` または `blocked` とする。

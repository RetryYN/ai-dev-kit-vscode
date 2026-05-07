# HELIX 拡張性 × 制約性両軸設計

## 1. 概要

本ドキュメントは PLAN-029 W-10 の成果として、**拡張性（多様性）** と
**制約性（品質劣化防止）** の両軸を1つの運用指標へ集約する。

想定読者: TL / SE / PE / PMO / Opus / QA  
対象リリース: PLAN-029 W-10  
反映範囲: 文書化のみ（実装は W-11 で追加）

目的:

- 代理実行の多様性と役割偏在を定量化し、単一点依存を防ぐ
- テスト・設計・運用の制約を「数値で監視」し、速度と品質のトレードを明示する
- Sprint 運用・レビュー運用に載せる KPI を先に統一し、W-11 以降の schema 実装と整合させる

## 2. 拡張性軸（多様性 KPI）

### 2.1 Skill / Plugin 多様性

### 2.1.1 スキル推奨精度
- KPI: **Skill 推奨 hit_rate**
  - 定義: gpt-5.4-mini 推奨 Skill と Opus/セッション実運用採択結果の一致率
  - 目標値: **≥ 80%**
  - 観測元: Opus 承認ログ、helix session log
  - 監視周期: 週次
- KPI: **Skill 多様性指数**
  - 定義: 推奨された skill ID の Shannon entropy
  - 目標値: **≥ 3.0**
  - 監視周期: 月次

### 2.1.2 プラグイン採用の幅
- KPI: **Plugin 採用数**
  - 定義: helix.db.plugins テーブルの件数（実体テーブルは W-11）
  - 現時点: 「W-11 schema 化対象」扱い、PLAN-029 時点では観測未対応
  - 目標: 新規 PLAN 発行時に 0.1/sprint 以上の純増
- KPI: **Plugin 更新率**
  - 定義: 対象 sprint 内で新規追加・更新された Plugin 数 / 全 Plugin 稼働数
  - 目標: **前月比 +5%以上** の改善を目標（偏在回避の補助指標）

### 2.2 Role 多様性

### 2.2.1 役割利用分散
- KPI: **Role 利用分布**
  - 定義: TL/SE/PE/PMO/recommender の委譲実行比率を sprint_metrics に記録
  - 目標: 主要4ロール（TL/SE/PE/PMO）で偏在比率が均衡すること
  - 最低限監視: 各ロールに0回ゼロリスクの最低運用（0.0% 連続禁止）

### 2.2.2 偏在リスク
- KPI: **Role 偏在 KPI**
  - 定義: 1 role の委譲比率が 80%を超える状態
  - しきい値: **80%超時 warning（運用上の集中リスク）**
  - 対応: W-11 の報告で sprint 参加ロールの再配分アラートを発火

### 2.3 PLAN 多様性

### 2.3.1 計画方式の偏り
- KPI: **PLAN 種類数**
  - 定義: forward / reverse / scrum / mini-PLAN の実施比率
  - 目標: 3カテゴリ以上を3スプリント継続期間で利用
  - 監視周期: 月次

### 2.3.2 企画創発速度
- KPI: **新規 PLAN 種類比**
  - 定義: 月別に新規に作成された PLAN 数 / 既存 PLAN 数
  - 目標: **月次 0.2〜1.0 のレンジ（0.05未満は停滞兆候）**
  - 注意: W-10 段階では trend 収集のみ、閾値は暫定

## 3. 制約性軸（品質 KPI）

### 3.1 Test / Build 健全性

### 3.1.1 回帰耐性
- KPI: **regress 0 維持**
  - 定義: `pytest + bats` の失敗件数が前 commit から増加しない
  - 目標値: **増加 0**（`helix gate G4` fail-close 条件と連動）
- KPI: **回帰検知時間**
  - 定義: 回帰検知から当該 commit までの平均修正時間
  - 目標: **≤ 2 時間**（ローカル開発時）

### 3.1.2 設計整合性
- KPI: **drift 0 件**
  - 定義: D-shard / 実装 / test の整合違反件数
  - 目標値: **0 件**
  - 観測: `helix drift-check`
- KPI: **ドキュメント整合率**
  - 定義: 主要要件項目に対するドキュメント反映率
  - 目標値: **100%**
  - 例外: 既知遅延は `deferred-finding` として明示

### 3.1.3 テスト観測性
- KPI: **bats coverage**
  - 定義: 主要 `cli/helix-*` CLI に対して `test-helix-*.bats` が存在する比率
  - 目標値: **80%以上（主要コマンド）**
- KPI: **テスト実行再現性**
  - 定義: 同一実行シナリオで PASS 率にばらつきがないか
  - 目標値: **100%**

### 3.2 Sprint 完遂 KPI

### 3.2.1 速度と完遂率
- KPI: **Sprint 完遂時間**
  - 定義: `sprint_metrics.duration_minutes` の平均
  - 目標値: **< 4 セッション / Sprint**
  - 監視周期: 月次
- KPI: **Sprint failure rate**
  - 定義: blocked / interrupted の比率
  - 目標値: **< 10%**

### 3.2.2 監査・運用
- KPI: **PM 違反検出**
  - 定義: Opus セッションでの Edit/Write/Agent 呼び出し発生時の警告件数
  - しきい値: **月次アラート 1件以上で要対応**
- KPI: **Review approve rate**
  - 定義: TL レビューでの1ラウンド approve 率
  - 目標値: **≥ 60%**

## 4. 集約ゲート運用

| 軸 | KPI | 評価周期 | 対応 G ゲート |
|---|---|---|---|
| 拡張性（Skill）| Skill 推奨 hit_rate ≥ 80% | 週次 | G7（安定性） |
| 拡張性（Role）| 偏在率 < 80% | 月次 | G11（運用学習） |
| 制約性（回帰）| regress 増加 0 件 | commit 毎 | G4（実装凍結） |
| 制約性（drift）| drift-check 0 件 | sprint 毎 | G2（設計凍結） |
| 制約性（Sprint）| 失敗率 < 10% | 月次 | G11（運用学習） |

## 5. KPI 観測の DB schema（W-11 実装）

W-11 で `helix.db v18 → v19` migration 時に、以下テーブルを追加する想定。

### 5.1 テーブル: `sprint_metrics`

- `test_pass_rate`（数値）
- `drift_count`（数値）
- `duration_minutes`（数値）
- `role_distribution_json`（JSON: Role 利用比率）
- `kpi_metadata_json`（JSON: 追加補助指標）

### 5.2 テーブル: `phase_gate_runs`

- `gate_id`（文字列）
- `phase`（文字列）
- `result`（文字列）
- `run_at`（日時）
- `notes`（文字列）

## 6. ダッシュボード（将来）

- W-10 では文書化のみで、暫定的に `helix budget status` の CLI 表示ベースで運用する。
- TUI / Web UI は PLAN-030 候補で検討する。
- W-11 以降は本ドキュメントの KPI を `sprint_metrics` / `phase_gate_runs` から集約表示へ接続する。

## 7. 受入条件（PLAN-029 §5.10）

### 7.1 文書成果物
- `docs/architecture/helix-flexibility-constraint.md` が存在すること
- 拡張性軸 / 制約性軸ごとに最低 2 件以上の KPI 定義があること
- 各 KPI の観測対象、周期、閾値、責務が明記されていること

### 7.2 テスト成果物（任意）
- `cli/tests/test-helix-flexibility.bats` が存在し、該当セクションの見出し確認が含まれること
- 各 KPI 規約は `1 +` ケースの smoke テストとして満たすことができる


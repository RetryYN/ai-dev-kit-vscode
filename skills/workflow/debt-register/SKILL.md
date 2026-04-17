---
name: debt-register
description: G4 通過条件の負債台帳生成・更新スキル
metadata:
  helix_layer: L4
  triggers:
    - G4 負債台帳必須時
    - 負債棚卸し時
    - debt_register 更新時
    - 技術負債の優先順位付け時
  verification:
    - "debt_register が docs/debt/ に .md で存在"
    - "各負債に impact (high/medium/low) と effort (high/medium/low) が記載"
    - "high impact 負債に owner と target_sprint が明記"
compatibility:
  claude: true
  codex: true
---

# 負債台帳（debt_register）スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- G4 判定前に未解決 debt を整理する時
- 既存負債を棚卸しして優先度を再評価する時
- Sprint 計画へリファクタ作業を取り込む時

---

## 1. 目的

- 目的: G4 通過条件の「未解決 debt は台帳化」を満たす
- 目的: 暗黙知の負債を見える化し、返済計画に接続する
- 目的: `high impact` の放置を防ぎ、リリースリスクを明示する

---

## 2. 保存先（正本準拠）

**重要**: 保存先は必ず以下にする。

- ディレクトリ: `docs/debt/`
- 命名規則: `YYYY-MM-DD-debt-register.md`
- 例: `docs/debt/2026-04-17-debt-register.md`

`layer-interface.md:445` の正本定義に準拠し、他パスへの保存はしない。

---

## 3. debt_register テンプレート

以下テンプレートを使用する。

```markdown
# Debt Register

## メタ情報
- 作成日: YYYY-MM-DD
- 更新日: YYYY-MM-DD
- 対象リリース: vX.Y.Z
- 作成者: TL/SE
- 関連:
  - docs/schedules/YYYY-MM-DD-schedule.md
  - docs/verification/YYYY-MM-DD-L4-verification.md

## 負債一覧

| debt_id | category | impact | effort | priority | owner | target_sprint | status |
|---------|----------|--------|--------|----------|-------|---------------|--------|
| DEBT-001 | architecture | high | medium | P1 | @team-a | Sprint 24.3 | open |
| DEBT-002 | test | medium | low | P2 | @team-b | Sprint 24.4 | open |
| DEBT-003 | performance | low | medium | P3 | @team-c | backlog | triaged |

## 判定メモ
- high impact 残存:
- blocker 判定:
- justification:

## Sprint .5 連携
- リファクタタスク化:
- 見積:
- 受入条件:
```

---

## 4. 各カラムの定義

- `debt_id`: 一意識別子（`DEBT-001` 形式）
- `category`: 代表カテゴリ
  - `architecture`
  - `code-quality`
  - `test`
  - `security`
  - `performance`
  - `observability`
  - `documentation`
- `impact`: 影響度（`high` / `medium` / `low`）
- `effort`: 対応工数（`high` / `medium` / `low`）
- `priority`: 優先度（`P1` / `P2` / `P3`）
- `owner`: 担当者または担当チーム
- `target_sprint`: 返済予定スプリント
- `status`: `open` / `triaged` / `in_progress` / `done` / `accepted_risk`

---

## 5. 優先順位評価軸

優先順位は次の軸で評価する。

- 基本式: `(影響度 × 発火確率) / 対応コスト`
- 影響度:
  - high: 顧客影響・障害化・セキュリティ事故につながる
  - medium: 品質低下や開発速度低下を継続発生させる
  - low: 局所的で直近リスクが小さい
- 発火確率:
  - high: 既に再発傾向あり
  - medium: 条件依存で発生
  - low: まれ
- 対応コスト:
  - high: 複数モジュール横断、回帰影響大
  - medium: 1 モジュール内で完結
  - low: 局所変更で対応可能

---

## 6. G4 通過判定基準

G4 では以下を確認する。

- debt_register が `docs/debt/` に存在
- 全項目に `impact` と `effort` が記載
- `high impact` 項目に `owner` と `target_sprint` がある
- `high impact` 残存時の扱い:
  - `blocker` として扱う
  - もしくは、明示的な `justification` を残す

### 判定ルール

- `high impact` が未割当（owner なし）: G4 fail
- `high impact` が期限未設定（target_sprint なし）: G4 fail
- `high impact` が存在し blocker 解除理由なし: G4 blocked

---

## 7. L4 Sprint .5 連携

L4 Sprint .5（仕上げ）で次を実施する。

- debt_register の open 項目を棚卸し
- 返済対象をリファクタタスクへ分解
- 各タスクに受入条件と検証方法を紐付け
- 次スプリント計画へ投入（`target_sprint` を確定）

### 連携の実務ルール

- 実装 fix が完了した負債は `status=done` へ更新
- 今回スコープ外は `accepted_risk` か `open` を明確化
- `accepted_risk` には期限と再評価日を必ず入れる

---

## 8. 作成手順

1. 未解決課題を収集（レビュー指摘、障害学習、未解決メモ由来）
2. 類似項目を統合し `debt_id` を付与
3. impact / effort / priority を採点
4. owner / target_sprint / status を埋める
5. G4 判定メモ（blocker or justification）を記載
6. Sprint .5 のリファクタタスクへ接続

---

## 9. 完了判定チェックリスト

- [ ] `docs/debt/YYYY-MM-DD-debt-register.md` が存在する
- [ ] 全 debt に impact と effort がある
- [ ] high impact の owner と target_sprint が埋まっている
- [ ] G4 判定メモ（blocker/justification）が記録されている
- [ ] Sprint .5 連携欄にタスク化結果が記載されている

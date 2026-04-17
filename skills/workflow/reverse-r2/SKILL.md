---
name: reverse-r2
description: HELIX Reverse R2 As-Is Design 復元スキル。観測契約から内部構造を再構成 + ADR 推定
metadata:
  helix_layer: R2
  triggers:
    - R2 As-Is Design 時
    - アーキテクチャ復元時
    - ADR 推定時
  verification:
    - "As-Is Design 書が docs/reverse/as-is-design.md に存在"
    - "推定 ADR が adr/ 下に存在 (status: draft-reverse)"
compatibility:
  claude: true
  codex: true
---

# Reverse R2: As-Is Design

> 目的: R1 で観測した契約を根拠に、現行システムの内部設計を復元し、設計判断を ADR 仮説として記録する。

## 適用タイミング
- Reverse フローで R1 を通過し R2 に進む時
- モジュール境界・依存関係・責務分担を可視化したい時
- 「なぜこの構造か」を ADR 仮説として文書化したい時

---

## R2 の目的
R2 は設計の「再定義」ではなく「復元」である。
- R1 観測契約に整合したアーキテクチャを再構成
- 設計上の一貫性/不整合を明文化
- 暗黙判断を ADR 仮説として管理
- R3 の要件仮説化に必要な設計コンテキストを提供

---

## RG2 通過条件
`gate-policy.md §Reverse ゲート` 準拠。
- アーキテクチャ復元が完了している
- ADR 仮説の confidence `high` が 70% 以上
- 未解決 contradictions が 0
- M/L 案件では `adversarial-review` 実施済み

Fail 時の標準対応。
- 矛盾する設計仮説の再観測（R1 契約へ戻って根拠再確認）
- ADR 仮説の confidence 再評価
- `adversarial-review` で反証された仮説の破棄/修正

---

## 入力（R1 引き継ぎ）
R2 は次の R1 成果物を入力とする。
- `observed_contracts`（API/DB/型）
- `r1_gaps`
- characterization tests 実行結果

入力検証。
- RG1 が pass している
- 契約 coverage と confidence 指標が記録済み
- 契約矛盾の状態が明示されている（未解決 0 が原則）

---

## アーキテクチャ復元手順
### 1. コンポーネント境界の再構成

対象モジュールを以下で分類する。
- Interface 層（API, Controller, Handler）
- Application 層（UseCase, Service）
- Domain/Data 層（Entity, Repository, Query）
- Platform 層（Infra, External API, Queue, Batch）

成果物。
- `docs/reverse/as-is-design.md` に境界図と責務表を作成

### 2. 依存関係グラフの構築

依存の方向と循環を明示する。
- 許容依存と違反依存を分離
- runtime 依存（env, feature flag, job scheduler）も併記
- 境界横断の副作用（直 DB 参照など）を列挙

### 3. データフロー・制御フローの復元

主要ユースケースごとに流れを記述する。
- 入力点 → 検証 → ドメイン処理 → 永続化 → 応答
- エラー経路、再試行、補償処理を明示
- 監査ログ・認証認可チェック位置を明示

---

## ADR 推定テンプレート

`adr/` 配下に `status: draft-reverse` で記録する。

```markdown
# ADR-RXXX: <推定タイトル>

- status: draft-reverse
- confidence: high|medium|low
- related_contracts: [contract_id...]
- evidence:
  - <file/path:line>
  - <runtime/log/ref>

## Context
現行の制約、依存、運用背景。

## Estimated Decision
推定される設計判断（断定しない）。

## Rationale (Observed)
推定根拠。コード/設定/運用証拠を列挙。

## Risks
推定誤り時の影響と確認方針。
```

記録対象の設計判断。
- 認証/認可方式
- トランザクション境界
- 非同期処理方式
- 外部API統合方式
- データ整合性戦略

---

## R1 契約との整合確認

確認観点。
- API endpoint が設計上の責務分割と一致するか
- DB 制約とアプリ層バリデーションの責務が矛盾しないか
- 型境界（DTO/Entity）が層を越えて漏れていないか

不一致時の扱い。
- 契約誤抽出の疑い: R1 に差し戻し
- 設計逸脱の疑い: R2 gap として保持
- 意図不明: R3 で PO 検証対象へ昇格

---

## adversarial-review の組み込み

M/L 案件では必須。
- 復元設計に対する反証シナリオを作成
- 「別解の方が説明力が高い」仮説を比較
- 反証後に残る仮説のみ ADR draft として確定

記録。
- 反証ログを `docs/reverse/review-notes.md` に保存（任意）
- RG2 判定時に実施有無を明示

---

## 出力フォーマット

```yaml
as_is_design:
  architecture: {}
  dependencies: {}
  data_flows: {}
  contradictions: []
adr_hypotheses:
  - id: ADR-RXXX
    status: draft-reverse
    confidence: high
```

必須ドキュメント。
- `docs/reverse/as-is-design.md`
- `adr/ADR-R*.md`（`status: draft-reverse`）

---

## R3 への引き渡し

R3 に渡す最小セット。
- `as_is_design` 一式
- `adr_hypotheses`
- 設計上 unresolved な unknown/contradictions（あれば）

引き渡し契約。
- R3 は R2 の設計復元を前提に意図仮説を生成する
- R3 で業務意図と矛盾が出た場合、R2 の ADR 仮説更新を許容

---

## チェックリスト

```text
[ ] As-Is Design 書が docs/reverse/as-is-design.md に存在
[ ] コンポーネント境界と依存関係が可視化済み
[ ] 主要データフロー/制御フローが記述済み
[ ] 推定 ADR が adr/ 下に存在（status: draft-reverse）
[ ] R1 契約との整合確認を実施済み
[ ] M/L の場合 adversarial-review 実施済み
[ ] RG2 判定結果を記録済み
[ ] R3 へ引き渡し済み
```

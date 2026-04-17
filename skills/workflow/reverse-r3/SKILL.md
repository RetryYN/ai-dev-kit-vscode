---
name: reverse-r3
description: HELIX Reverse R3 Intent Hypotheses スキル。要件仮説生成 + PO 検証 + Session Hypothesis Log
metadata:
  helix_layer: R3
  triggers:
    - R3 Intent Hypotheses 時
    - 要件仮説生成時
    - PO 検証時
    - Session Hypothesis Log 作成時
  verification:
    - "Session Hypothesis Log が docs/reverse/ に存在"
    - "各仮説に confidence (high/medium/low) と PO 検証結果が記載"
compatibility:
  claude: true
  codex: true
---

# Reverse R3: Intent Hypotheses

> 目的: R0-R2 の観測結果から要件仮説を生成し、PO 検証で Intended/Accidental/Unknown/Deprecated を確定する。

## 適用タイミング

このスキルは以下の場合に適用する。
- Reverse フローで R2 完了後に業務意図を復元する時
- 現行挙動の「仕様か偶発か」を PO と合意する時
- Session Hypothesis Log を作成し、R4 へ渡す判断材料を作る時

---

## R3 の目的

R3 は「コードに現れない意図」を仮説として扱う。
- 観測挙動を要件仮説へ変換
- PO との対話で仮説を検証
- confidence と検証状態を記録
- R4 の gap routing に使える粒度へ整形

原則。
- コードだけで要件を断定しない
- 不確実性は `unknown` として明示する
- PO 未確認の項目を「確定仕様」に昇格させない

---

## RG3 通過条件

`gate-policy.md §Reverse ゲート` 準拠。
- PO 検証済み仮説率が 80% 以上
- unknown 全項目に調査タスクが割当済み
- accidental/deprecated 全項目に対応方針がある
- PM + PO + TL の合意が記録されている

Fail 時の標準対応。
- PO 追加ヒアリングを実施
- unknown の観測証拠追加（R0-R2 再参照）
- 仮説粒度を分割して再判定

---

## 入力（R2 引き継ぎ）

R3 は次を入力として受け取る。
- `as_is_design`
- `adr_hypotheses`
- R1/R2 の gaps（要件起因が疑われる項目）

入力検証。
- R2 の RG2 判定結果が明示されている
- ADR 仮説に confidence と evidence が付与されている
- PO と検証セッション日程が確保されている

---

## Session Hypothesis Log テンプレート

保存先。
- `docs/reverse/session-hypothesis-log.md`（推奨）

表形式テンプレート（必須列）。

| hypothesis_id | 仮説（要件） | 観測証拠 | confidence | 検証方法 | PO 検証結果 | 次アクション |
|---|---|---|---|---|---|---|
| H-001 | 例: 注文金額は正数のみ許可 | API `POST /orders` とDB制約不一致 | medium | POヒアリング + 振る舞い再現 | accidental | L4 バグ修正へ routing |

列定義。
- `confidence`: `high` / `medium` / `low`
- `PO 検証結果`: `intended` / `accidental` / `unknown` / `deprecated`
- `次アクション`: R4 routing 先または追加調査

---

## 要件仮説生成手順

### 1. 仮説候補の作成

観測起点から仮説を生成する。
- 主要ユースケース（売上、課金、通知、承認）
- 例外パス（権限不足、重複登録、期限切れ）
- 運用系要件（監査、リトライ、アラート）

### 2. tools/ai-search 連携

AI 推論で候補を拡張する。
- ドメイン語彙と既存実装パターンから仮説候補を列挙
- 候補は必ず evidence 紐付け後に log へ記録
- AI 生成候補は初期 confidence を `low` に設定

### 3. 仮説の正規化

重複・曖昧表現を解消する。
- 1 仮説 = 1 判定可能命題
- 業務ルールと実装制約を分離記述
- 受入条件に転用可能な文章へ整形

---

## PO インタビュー手順

1. 事前準備
- 仮説一覧と証拠を先に共有
- 判定カテゴリ（intended/accidental/unknown/deprecated）を説明

2. セッション進行
- 高リスク仮説（セキュリティ、課金、法令）を先に確認
- 「現在の正解」と「将来の変更希望」を分けて聞く
- 判断不能な項目は unknown として保留

3. 記録
- 判定理由を1行で残す
- 追加確認先（業務担当、法務、運用）を明記
- 合意者（PM/PO/TL）と日時を記録

---

## 出力フォーマット

```yaml
intent_hypotheses:
  verified_ratio: 0
  hypotheses:
    - id: H-001
      confidence: medium
      po_verdict: accidental
      action: route-L4
  unknown_tasks: []
consensus:
  pm: true
  po: true
  tl: true
```

必須ドキュメント。
- `docs/reverse/session-hypothesis-log.md`

---

## R4 への引き渡し契約

R3 から R4 に渡す最小セット。
- Session Hypothesis Log（全仮説の判定付き）
- accidental/deprecated の対応方針
- unknown の調査タスクと担当

引き渡し規約。
- R4 は各仮説を gap 種別に再分類して routing する
- R4 完了時に Forward HELIX（L1/L2/L3/L4）へ接続する
- R3 未検証の仮説は R4 で「未確定」として優先度を下げる

---

## チェックリスト

```text
[ ] Session Hypothesis Log が docs/reverse/ に存在
[ ] 各仮説に confidence (high/medium/low) が記載
[ ] 各仮説に PO 検証結果が記載
[ ] unknown 項目に調査タスクを割当済み
[ ] accidental/deprecated 項目に対応方針あり
[ ] PM+PO+TL 合意の記録あり
[ ] RG3 判定結果を記録済み
[ ] R4 引き渡しパッケージを作成済み
```

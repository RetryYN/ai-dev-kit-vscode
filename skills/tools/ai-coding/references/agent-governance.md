# HELIX Agent Governance Policy
> 目的: HELIX Agent Governance Policy の要点を把握し、設計・実装判断を行う際のクイックリファレンスとして参照

## 目的

HELIX におけるエージェント実行を、宣言的ポリシーと多層ガードで統制する。
基本方針はゼロトラスト（default deny）で、明示許可された操作のみ実行する。

## ポリシー定義

- `.helix/rules/` で宣言的にポリシーを定義する（既存 rules YAML を拡張）
- 役割、ツール、実行条件、承認要件を機械可読で管理する
- 本番影響・認証・決済・PII は必ず人間承認を要求する

## ポリシー強制（3層）

- gate: フェーズ・成果物・安全条件の通過を必須化
- hook: 実行時の危険パターンを検知し advisory/block を返す
- guard: 実行可否を最終判定し、逸脱を停止する

## 監査ログ

- `helix.db`（SQLite）へエージェント操作を記録する
- 記録対象: 実行者、時刻、入力要約、実行コマンド、判定結果、承認情報
- レトロ時にログを参照し、再発防止策を更新する

## ゼロトラスト運用

- すべてのエージェント操作をデフォルト不信として扱う
- 権限昇格、外部通信、破壊的操作は明示許可がない限り拒否する
- 許可根拠は rules / gate / 承認記録で追跡可能にする

## エスカレーション境界

以下は必ず人間承認:

- 本番影響
- 認証・認可
- 決済
- 個人情報（PII）
- ライセンス判断

## ガバナンス 4 層

```text
ガバナンス 4 層:
  Layer 1: サンドボックス（実行環境分離）
    → Codex: sandbox: workspace-write
    → Claude: allowed-tools 制限
  Layer 2: ガードレール（事前認可）
    → Phase Guard: フェーズ違反ブロック
    → Deliverable Gate: 成果物不足ブロック
    → Plan Review: TL レビュー必須
  Layer 3: モニタリング（可観測性）
    → Advisory Hook: 3段階検知
    → Freeze-break: 凍結違反検知
    → Builder Store: 実行記録
  Layer 4: 監査（コンプライアンス）
    → SQLite ログ: 全操作記録
    → Retro: ミニレトロで振り返り
    → Learning Engine: パターン分析
```

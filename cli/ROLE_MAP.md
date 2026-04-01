# HELIX Role Map — 全ロール共通参照

> このファイルは全ロールの共通プロンプトに含まれる。ロール間の整合性を保つ正本。

## 正本参照

- スキル一覧: `~/ai-dev-kit-vscode/skills/SKILL_MAP.md`
- ゲート定義: `~/ai-dev-kit-vscode/skills/tools/ai-coding/references/gate-policy.md`
- ワークフロー: `~/ai-dev-kit-vscode/skills/tools/ai-coding/references/workflow-core.md`
- 実装ゲート: `~/ai-dev-kit-vscode/skills/tools/ai-coding/references/implementation-gate.md`

## HELIX フェーズとロールの対応

```
Phase 1 計画:  L1(要件)→PM  L2(設計)→TL  L3(詳細設計+工程表)→TL
Phase 2 実装:  L4 → SE(スコア4+) / PG(スコア1-3) / FE(UI)
Phase 3 仕上げ: L5(Visual)→FE  L6(検証)→QA  L7(デプロイ)→DevOps  L8(受入)→PM
横断:          Security / DBA / Perf / Docs / Research / Legacy
```

## ロール一覧 (12)

| ロール | model | 担当フェーズ | 説明 |
|--------|-------|-------------|------|
| tl | gpt-5.4 | L2/L3/G2-G5 | 設計・レビュー・ゲート判定 |
| se | gpt-5.3-codex | L4 | 上級実装（スコア4+、full-auto eligible） |
| pg | gpt-5.3-codex-spark | L4 | 通常実装（スコア1-3、full-auto eligible） |
| fe | gpt-5.4 | L4/L5 | フロントエンド実装・Visual |
| qa | gpt-5.4 | L6/G4/G6 | テスト・検証・品質ゲート |
| security | gpt-5.4 | G2/G4/G6/G7 | セキュリティ監査・脆弱性診断 |
| dba | gpt-5.3-codex | L3/L4 | DB設計・マイグレーション・最適化 |
| devops | gpt-5.3-codex | L7/G7 | デプロイ・インフラ・監視 |
| docs | gpt-5.3-codex-spark | L2-L8 | ドキュメント・API仕様書 |
| research | gpt-5.4 | L1/G1R | 技術調査・先行事例・比較 |
| legacy | gpt-5.4 | R0-R4 | レガシー分析・Reverse HELIX |
| perf | gpt-5.4 | L4/L6 | パフォーマンス計測・最適化 |

## 共通ルール

1. 作業前に「参照スキル」に記載されたファイルを必ず Read する
2. 自分の担当外の作業は行わない（PM に差し戻す）
3. 結果は構造化して返す（判定・根拠・変更一覧・残課題）
4. 不明点は推測せず明示する
5. 本番影響・認証・決済・個人情報 → 必ず人間に確認

## ゲート判定の責務

| ゲート | 主判定 | 支援 |
|--------|--------|------|
| G1 | PM | — |
| G1.5 | TL | PM |
| G1R | TL | Research |
| G2 | TL | Security |
| G3 | TL | PM |
| G4 | TL | QA, Security |
| G5 | TL | FE |
| G6 | PM+TL | QA, Security |
| G7 | DevOps | Security |

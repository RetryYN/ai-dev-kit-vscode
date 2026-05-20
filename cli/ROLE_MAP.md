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
Phase 2 実装:  L4 → SE(スコア4+) / PE(スコア1-3)
Phase 3 仕上げ: L5(Visual)→PE  L6(検証)→QA  L7(デプロイ)→DevOps  L8(受入)→PM
横断:          Security / DBA / Perf / Docs / Research / Legacy / PMO
```

## ロール一覧 (30)

> CLI 引数 (`--role`) は本表の「ロール」列に従う。team naming で「PE」と表記される責務は CLI 上では `pg` を使う (PE = `--role pg`)。

| ロール | model | 担当フェーズ | 説明 |
|--------|-------|-------------|------|
| tl | gpt-5.5 | L2/L3/G2-G5 | 設計・レビュー・ゲート判定 |
| se | gpt-5.4 | L4 | 上級実装・契約・リファクタリング |
| pg | gpt-5.3-codex-spark / gpt-5.3-codex | L4/L5 | 単機能・速度重視実装 (team naming: PE) |
| fe | gpt-5.4 | L5 | UI実装・スタイリング・アクセシビリティ対応 |
| qa | gpt-5.4 | L6/G4/G6 | テスト・検証・品質ゲート |
| security | gpt-5.4 | G2/G4/G6/G7 | セキュリティ監査・脆弱性診断 |
| dba | gpt-5.3-codex | L3/L4 | DB設計・マイグレーション・最適化 |
| devops | gpt-5.3-codex | L7/G7 | デプロイ・インフラ・監視 |
| docs | gpt-5.3-codex-spark | L2-L8 | ドキュメント・API仕様書 |
| research | gpt-5.4 | L1/G1R | 技術調査・先行事例・比較 |
| legacy | gpt-5.4 | R0-R4 | レガシー分析・Reverse HELIX |
| perf | gpt-5.4 | L4/L6 | パフォーマンス計測・最適化 |
| classifier | gpt-5.4-mini | 全フェーズ | タスク分類・ロール判定 |
| recommender | gpt-5.4-mini | 全フェーズ | スキル自動推挙（`helix skill search` 専用） |
| effort-classifier | gpt-5.4-mini | 全フェーズ | 工数・難易度・規模の分類補助 |
| pmo-sonnet | claude-sonnet-4-6 | 横断 | PMO 状況把握・判定サポート |
| pmo-haiku | claude-haiku-4-5-20251001 | 横断 | PMO 軽作業（docs 系、Web 検索） |
| pdm-tech-innovation | claude-opus-4-7 | 横断 | 海外技術思想翻案 |
| pdm-marketing-innovation | claude-opus-4-7 | 横断 | 海外マーケ思想翻案 |
| pdm-innovation-manager | claude-opus-4-7 | 横断 | 統合・意思決定 |
| impl-sonnet | claude-sonnet-4-6 | L4 | Sonnet write-enabled 実装（Codex 上限時の代替経路） |
| pm-advisor | claude-opus-4-7 | 全フェーズ | PM 級難判断のアドバイザー（read-only、Opus）。チャット PM (Opus / Sonnet 問わず) が大局判断で迷ったとき召喚 |
| tl-advisor | gpt-5.5 | 全フェーズ | TL 級難判断のアドバイザー（read-only）。チャット PM / 実装担当が設計・契約・技術選択で迷ったとき召喚 |
| pmo-helix-explorer | claude-sonnet-4-6 | 横断 | HELIX framework 内資産詳細探索 (skills/templates/cli/docs) |
| pmo-helix-scout | claude-haiku-4-5-20251001 | 横断 | HELIX 内軽量検索・候補列挙 (1 hop 目) |
| pmo-project-explorer | claude-sonnet-4-6 | 横断 | プロジェクト内資産詳細探索 (code/docs/config) |
| pmo-project-scout | claude-haiku-4-5-20251001 | 横断 | プロジェクト内軽量検索・候補列挙 (1 hop 目) |
| pmo-tech-docs | claude-sonnet-4-6 | 横断 | 設計手法・概念の外部精読 |
| pmo-tech-fork | claude-sonnet-4-6 | 横断 | OSS/plugin 探索・転用判断 |
| pmo-tech-news | claude-sonnet-4-6 | 横断 | 最新 Tech 動向 sweep（週次想定） |

## 共通ルール

> 注記: `helix codex --auto-thinking` は **opt-in flag**。default は role conf の `codex_thinking` を参照。`--auto-thinking` は task description から effort を動的推定する option（明示時のみ有効）。
> role effort map: tl/high, se/high, pg/medium, fe/high, qa/high, security/xhigh, dba/medium, devops/medium, docs/low, research/low, legacy/xhigh, perf/high, classifier/low, recommender/low, effort-classifier/low, impl-sonnet/medium, pdm-innovation-manager/high, pdm-marketing-innovation/high, pdm-tech-innovation/high, pm-advisor/high, pmo-haiku/low, pmo-helix-explorer/medium, pmo-helix-scout/low, pmo-project-explorer/medium, pmo-project-scout/low, pmo-sonnet/medium, pmo-tech-docs/medium, pmo-tech-fork/medium, pmo-tech-news/medium, tl-advisor/high.

1. 作業前に「参照スキル」に記載されたファイルを必ず Read する
2. 自分の担当外の作業は行わない（PM に差し戻す）
3. 結果は構造化して返す（判定・根拠・変更一覧・残課題）
4. 不明点は推測せず明示する
5. 本番影響・認証・決済・個人情報・ライセンス → 必ず人間に確認

## ゲート判定の責務

> 詳細条件: gate-policy.md §ゲート一覧 参照

| ゲート | 主判定 | 支援 |
|--------|--------|------|
| G1 | PM | — |
| G1.5 | TL | PM |
| G1R | TL | Research |
| G2 | TL | Security |
| G3 | TL | PM |
| G4 | TL | QA, Security |
| G5 | TL | PE |
| G6 | PM+TL | QA, Security |
| G7 | DevOps | Security |

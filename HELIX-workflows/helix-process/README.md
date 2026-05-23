---
doc_id: workflows-index
title: "HELIX ワークフロー索引"
status: draft
created: 2026-05-24
owner: PM
---

# HELIX ワークフロー索引

中核の Forward（Vモデル L0–L14）、入口に応じた9モード、FE/UX 工程の専門2、そして管理・自動化ドキュメント群で構成される。すべてのモードは最終的に Forward のドキュメント体系へ収束・昇華する。

## 1. Forward HELIX（Vモデル L0–L14）

正本は [HELIX-process-L0-L14.md](../HELIX-process-L0-L14.md)。工程別15ファイル（L0-concept 〜 L14-operation-verification）。

## 2. 入口モード（9）

| モード | ファイル | 入口 | 起票 kind |
|---|---|---|---|
| Scrum | scrum-workflow.md | 要件をユーザーと合わせ反復開発 | fullback |
| Discovery | discovery-workflow.md | 計画上の不明点を検証 | poc |
| Reverse | reverse-workflow.md | 既存資産を逆引き | reverse |
| Incident | incident-workflow.md | 本番障害に緊急対応 | troubleshoot / recovery |
| Add-feature | add-feature-workflow.md | 既存に機能追加 | add-design / add-impl |
| Refactor | refactor-workflow.md | 振る舞い不変の構造改善 | refactor |
| Retrofit | retrofit-workflow.md | 既存の改修・移行 | retrofit |
| Research | research-workflow.md | 事前調査・意思決定 | research |
| Recovery | recovery-workflow.md | AI 暴走のガード＋収束 | recovery |

## 3. 工程専門ワークフロー（FE / UX、2）

| ワークフロー | ファイル | 対応工程 |
|---|---|---|
| 画面設計（UI / ワイヤーフレーム） | screen-design-workflow.md | L2 |
| フロントデザイン（UX / ビジュアル） | frontend-design-workflow.md | L10 |

## 4. 管理・自動化ドキュメント

| ドキュメント | ファイル | 役割 |
|---|---|---|
| 自動化・ゲートマップ | automation-gate-map.md | Vモデル全工程の detector / ゲート |
| 逸脱 PLAN 起票マップ | deviation-plan-map.md | モード × kind × generates |
| 本線 DB 収束 | db-integration.md | 個別モードデータ → 本線 DB |
| DB 自動登録 | db-auto-registration.md | イベント駆動で helix_db へ登録 |
| 検出 → モード連携 | detection-routing.md | drift / 劣化 / 暴走 / 障害 → モード発動 |
| FE detector 仕様 | fe-detector-spec.md | FE 5種の決定論的判定仕様 |
| 横断機構 | cross-cutting-mechanisms.md | interrupt / debt / drift-check / readiness の位置づけ |
| テスト観点ゲート | test-perspective-gate.md | W字補強（テスト重複・抜け漏れ検出） |
| CI / GitHub 運用 | ci-pr-workflow.md | ブランチ pipeline ＋ 証跡検証 ＋ PR 許可 |
| L 単位 文脈注入 | layer-context-injection.md | 各 L にスキル/ワークフロー/agent/command/orchestration を注入 |
| Learning Engine | learning-engine.md | スキル発火・トラブル・成功ログから recipe を学習 |
| 観測・計測 | observability-metrics.md | 発火・トラブル計測と AI 実行ログの自動取得 |
| 自動走行・コンテキスト管理 | continuous-run-context-management.md | 指定時間の自動走行と、Codex セッションクリーナーによるコンテキスト管理（PoC）|
| 横断検出 | cross-detection.md | 依存漏れ・契約漏れ・接続欠損・デグレを横断検出 |
| 基盤整備状況 | infra-readiness.md | 検証・テスト・検出基盤の実装済み／設計済みの一覧 |
| スキル・コマンドの穴 | integration-map.md | スキル/コマンドの欠落と未統合項目の一覧 |
| フォルダ構成レビュー | folder-structure-review.md | 点検漏れ領域と docs/ への再構成方針 |
| 既存資産マッピング | asset-mapping.md | 既存資産の棚卸しと設計との対応・充足度 |
| HELIX W（2段V合流） | two-stage-agent-design.md | V字を2回（一般システム＋エージェント昇華）通し L10 で合流。エージェントシステム時のみ |

## ファイル構成

```
HELIX-process-L0-L14.md            # Forward 全体インデックス（正本）
helix-process/
├── L0-concept.md … L14-operation-verification.md   # Forward 工程別（15）
├── scrum / discovery / reverse / incident / add-feature-workflow.md   # 入口モード
├── refactor / retrofit / research / recovery-workflow.md              # 入口モード
├── screen-design / frontend-design-workflow.md                        # 工程専門
├── automation-gate-map.md / deviation-plan-map.md                     # 管理
├── db-integration.md / db-auto-registration.md / detection-routing.md # DB
├── fe-detector-spec.md                                                # FE 仕様
└── README.md                                                          # 本索引
```

## 設計思想

HELIX は TDD（テストファースト）を基本とする。コードを書く前に合格基準となるテストを先に書く順序を、全工程・全モードで厳守する（詳細は [HELIX-process-L0-L14.md](../HELIX-process-L0-L14.md) の基本原則）。


多様な入口（新規 / 反復 / 探索 / 逆引き / 緊急 / 追加 / 構造改善 / 移行 / 調査 / 暴走対応）から始めても、最終的に Forward の単一ドキュメント体系へ収束する。逸脱は kind 付き PLAN の起票として記録され、自動登録で本線 DB に取り込まれ、検出（drift / 劣化 / 暴走 / 障害）が再びモードを起動する。入口の柔軟さと Vモデルの厳格さ（双方向 trace・ゲート）が、単一 DB の上で両立する。

---
doc_id: process-overview-v2
title: "HELIX 工程定義 L0–L14 — V-model 構造"
status: draft
created: 2026-05-24
owner: PM
note: "ユーザー提示の工程定義を正本として整備。本ファイルは記述の忠実な構造化であり、工程の追加・削除・解釈変更は行わない。"
---

# HELIX 工程定義 L0–L14

## 基本原則：TDD（テストファースト）

HELIX は TDD（テスト駆動開発）を基本とする。**コードを書く前に、必ず合格基準となるテストを先に書く。** この順序は、いかなる工程・いかなるモードでも厳守し、決して破らない。

- 設計フェーズ（L1〜L6）で、各レベルのテスト設計（運用 / 受入 / 総合 / 結合 / 単体）を設計と同時に凍結する。
- L7 実装の直前に、L6 単体テスト設計に基づく合格基準テスト（コード）を書き、赤（fail）であることを確認してから実装し、緑（pass）にする。
- 「テスト（合格基準）→ 実装」の順序を固定する。実装してからテストを書く（テストアフター）ことは許さない。
- この原則は全モード（Forward / Scrum / Discovery / Reverse / Incident / Add-feature / Refactor / Retrofit / Research / Recovery）および HELIX W に共通する。Refactor では、変更前に保護網のテスト（既存テストまたはゴールデンマスター）があることを前提とする。

## 基本構造

工程 (process) を起点とする。設計フェーズ (左腕) で設計と同時に対応するテスト設計を凍結し、L7 (谷) で実装、検証フェーズ (右腕) で左腕のテスト設計を実行・検証する。

L7 (実装工程) は PLAN の上位概念であり、全体の進捗を管理する。PLAN は機能単位で起票し、ある工程から次の工程へ進む (例: L0 → L1) ために、どのドキュメントを・どの順番で・どんな手順を踏んで作るかを工程表として定義する。PLAN は工程表 (進捗) と実装計画の両方を内蔵し、作業が途中で中断してもどこまで進んだかを再開可能にする。

```
                                                       L0 企画書
                                                          │
[左腕：設計＋テスト設計ペア凍結]              [右腕：検証・運用]
  L1 要求定義 / 運用テスト設計  ───────────────  L14 運用検証 / 機能改善
   L2 画面設計・フロントUI / ワイヤーモック作成 ──  L10 フロントUX・ビジネスデザイン磨き上げ
    L3 要件定義 / 受け入れテスト設計 ────────────  L12 デプロイ / 受入テスト / 環境差異巻き取り
     L4 基本設計 / 総合テスト設計 ──────────────  L9 総合テスト / 依存関係解消
      L5 詳細設計 / 結合テスト設計 ─────────────  L8 結合テスト / 依存関係解消
       L6 機能設計 / 単体テスト設計 ───────────  （単体テストは L7 内で実施）
                          \                    /
                       [谷] L7 テスト実装 → 本体実装 → 3点レビュー
                            → テストパターン追加 → テスト実施 → 修正 / 実装完了
```

---

## 工程一覧（L0–L14）

| 層 | 区分 | 設計フェーズ | 対応するテスト設計 / テスト |
|---|---|---|---|
| **L0** | 起点 | 企画書 | — |
| **L1** | 左腕 | 要求定義 | 運用テスト設計 |
| **L2** | 左腕 | 画面設計・フロントUI | ワイヤーモック作成 |
| **L3** | 左腕 | 要件定義 | 受け入れテスト設計 |
| **L4** | 左腕 | 基本設計 | 総合テスト設計 |
| **L5** | 左腕 | 詳細設計 | 結合テスト設計 |
| **L6** | 左腕 | 機能設計 | 単体テスト設計 |
| **L7** | 谷 | テスト実装 → 本体実装 → 設計・テスト・実装3点レビュー → テストパターン追加 → テスト実施 → 修正 / 実装完了 | （単体テストの実行を内包） |
| **L8** | 右腕 | 結合テスト | 依存関係解消 |
| **L9** | 右腕 | 総合テスト | 依存関係解消 |
| **L10** | 右腕 | フロントデザインUX・ビジネスデザイン磨き上げ | — |
| **L11** | 右腕 | 総合レビュー | ユーザー検証 / 要件巻き取り |
| **L12** | 右腕 | デプロイ | 受入テスト / 環境差異巻き取り |
| **L13** | 右腕 | デプロイ後検証 | 実環境運用 |
| **L14** | 右腕 | 運用検証 | 機能改善 |

---

## V字の水平対応（左腕のテスト設計 ⇔ 右腕のテスト実行）

設計層で凍結したテスト設計を、対応する検証層で実行する。名称が一致する対応は以下の通り。

| 左腕（テスト設計を作る） | 右腕（そのテストを実行する） |
|---|---|
| L6 単体テスト設計 | L7 単体テスト実施（谷の中で実行） |
| L5 結合テスト設計 | L8 結合テスト |
| L4 総合テスト設計 | L9 総合テスト |
| L3 受け入れテスト設計 | L12 受入テスト |
| L1 運用テスト設計 | L14 運用検証 |
| L2 ワイヤーモック作成 | L10 フロントUX・ビジネスデザイン磨き上げ |

L11（総合レビュー / ユーザー検証 / 要件巻き取り）は、左腕 L1 要求定義・L3 要件定義に対する最終突合の位置にある。

---

## 各層の記述（提示内容の保全）

- **L0 企画書**
- **L1** 要求定義 / 運用テスト設計
- **L2** 画面設計・フロントUI / ワイヤーモック作成
- **L3** 要件定義 / 受け入れテスト設計
- **L4** 基本設計 / 総合テスト設計
- **L5** 詳細設計 / 結合テスト設計
- **L6** 機能設計 / 単体テスト設計
- **L7** テスト実装 ⇒ 本体実装 ⇒ 設計・テスト・実装3点レビュー ⇒ テストパターン追加 ⇒ テスト実施 ⇒ 修正 / 実装完了
- **L8** 結合テスト / 依存関係解消
- **L9** 総合テスト / 依存関係解消
- **L10** フロントデザインUX・ビジネスデザイン磨き上げ
- **L11** 総合レビュー / ユーザー検証 / 要件巻き取り
- **L12** デプロイ / 受入テスト / 環境差異巻き取り
- **L13** デプロイ後検証 / 実環境運用
- **L14** 運用検証 / 機能改善

---

## PLAN の位置づけ

### 役割

- PLAN は **機能単位** で起票する。
- PLAN は、ある工程から次の工程へ進む (例: L0 → L1) ために、**どのドキュメントを・どの順番で・どんな手順を踏んで作るか** を工程表として定義する。
- 各ステップには作業の種類を含められる。例: Web 検索を挟む / GitHub を調査してから書く / TL レビューを入れる。
- PLAN は **工程表（進捗）と実装計画の両方を内蔵** する。ドキュメント作成が途中で中断しても、どこまで進んだかを追跡し再開できる。

### L7 との関係

- **L7（実装工程）は PLAN の上位概念**。個々の PLAN の進捗を束ね、全体の進捗を管理する。
- **L7 の工程表** は、実装する機能の順番を定義する。
- **L7 における PLAN** は、機能の中身の実装手順書として起票する。

### 命名規則

- PLAN 名称は工程プレフィックスを付ける。形式: `L<工程番号>-○○○plan`。
- `○○○` はその PLAN が進める対象を表し、**工程によって変わる**。
  - **L7（実装工程）**: 機能名。
  - **L7 以外（ドキュメント作成工程）**: その工程で作成・遂行する対象（機能名とは限らない）。
- プレフィックスと `○○○` により、その PLAN が「どの工程の何を進めるものか」を識別する。

### 配置

- PLAN 起票のフォルダは分離する。

---

## 工程別詳細ドキュメント

各工程の PLAN とその記載項目は工程別ファイル（`helix-process/`）に分離。

- [L0 企画書](helix-process/L0-concept.md)
- [L1 要求定義](helix-process/L1-requirements.md)
- [L2 画面設計・フロントUI](helix-process/L2-ui-design.md)
- [L3 要件定義](helix-process/L3-requirements-definition.md)
- [L4 基本設計（外部設計）](helix-process/L4-basic-design.md)
- [L5 詳細設計（内部設計）](helix-process/L5-detailed-design.md)
- [L6 機能設計](helix-process/L6-functional-design.md)
- [L7 実装（谷）](helix-process/L7-implementation.md)
- [L8 結合テスト](helix-process/L8-integration-test.md)
- [L9 総合テスト](helix-process/L9-system-test.md)
- [L10 フロントUX・ビジネスデザイン磨き上げ](helix-process/L10-ux-refinement.md)
- [L11 総合レビュー・ユーザー検証・要件巻き取り](helix-process/L11-final-review.md)
- [L12 デプロイ・受入テスト・環境差異巻き取り](helix-process/L12-deployment.md)
- [L13 デプロイ後検証・実環境運用](helix-process/L13-post-deployment-verification.md)
- [L14 運用検証・機能改善](helix-process/L14-operation-verification.md)

---

## 他モード（Forward 以外）

Forward HELIX（上記 L0–L14）に加え、入口に応じて 9 モードを使い分ける。いずれも最終的に Forward（Vモデル）のドキュメント体系へ昇華・接続する。

- [Scrum HELIX ワークフロー](helix-process/scrum-workflow.md) — ユーザーと要件をすり合わせて反復開発し、完成機能を Vモデル体系へ昇華するモード
- [Discovery ワークフロー](helix-process/discovery-workflow.md) — 計画上の不明点を仮説・PoC・検証で潰す探索モード（Reverse と組み合わせ可）
- [Reverse HELIX ワークフロー](helix-process/reverse-workflow.md) — 既存コード・設計から逆引きし Forward に接続するモード
- [Incident HELIX ワークフロー](helix-process/incident-workflow.md) — 本番稼働中の障害に hotfix で即応し、恒久対策を Vモデル体系へ昇華するモード
- [Add-feature HELIX ワークフロー](helix-process/add-feature-workflow.md) — 既存システムに新機能を追加する差分ワークフロー（add-design / add-impl）
- [Refactor HELIX ワークフロー](helix-process/refactor-workflow.md) — 振る舞いを変えず内部構造を改善するモード（refactor）
- [Retrofit HELIX ワークフロー](helix-process/retrofit-workflow.md) — 既存システムを段階的に改修・移行するモード（retrofit）
- [Research HELIX ワークフロー](helix-process/research-workflow.md) — 実装前に調査し ADR で意思決定するモード（research）
- [Recovery HELIX ワークフロー](helix-process/recovery-workflow.md) — AI エージェントの暴走・独断専行をガード（警告）し収束（リカバリー）するモード（recovery）

| 入口 | 使うモード | Forward への昇華 |
|---|---|---|
| 要件・設計・契約が明確 | Forward HELIX（L0–L14） | — |
| 作るものは明確、要件をユーザーと合わせたい | Scrum HELIX（反復開発） | 完成機能を Reverse fullback で文書化 → L0–L14 |
| 計画上の不明点・実現性が未確定 | Discovery（Reverse と組み合わせ可） | confirmed → L1/L3/L4–L6 へ昇格 |
| 既存コード・設計資産を逆引きしたい | Reverse HELIX | R4 routing → L1/L3/L4/L7/L8–L11 |
| 本番稼働中に障害が発生した | Incident HELIX（hotfix 即応） | 暫定収束後、恒久対策を L1/L3/L4–L6、postmortem を L14 |
| 既存システムに新機能を追加したい | Add-feature（差分追補） | add-design / add-impl を L4–L7 に追補 → L0–L14 体系へ統合 |
| 振る舞いを変えず構造改善したい | Refactor | refactor を L7 実装の内部改善に閉じる |
| 既存を改修・移行したい | Retrofit | retrofit-matrix + config を L4–L9 に追補 |
| 実装前に調査・意思決定したい | Research | ADR を L1 / L4 の判断材料へ接続 |
| AI が暴走・独断専行した | Recovery（ガード＋収束） | 再開ポイントから L0–L14 へ復帰、認識訂正を L14 へ |

---

## 工程専門ワークフロー（FE / UX）

FE / UX は HELIX の弱点領域（FE 専用 detector が定義先行で未実装）のため、該当工程を専門ワークフローとして補強する。入口判定モードではなく、特定工程（L2 / L10）の進め方を専門化したもの。

- [画面設計ワークフロー（UI / ワイヤーフレーム）](helix-process/screen-design-workflow.md) — L2 画面設計の専門化
- [フロントデザインワークフロー（UX / ビジュアルデザイン）](helix-process/frontend-design-workflow.md) — L10 UX・ビジネスデザイン磨き上げの専門化

| 工程 | 専門ワークフロー | 補強する FE detector |
|---|---|---|
| L2 画面設計 | 画面設計（UI / ワイヤーフレーム） | state-transition-drift / mock-promotion |
| L10 UX 磨き上げ | フロントデザイン（UX / ビジュアル） | design-token-drift / a11y-regression / visual-regression |

L2（左腕）でワイヤーフレームを設計し、L10（右腕）でビジュアル・UX として磨き上げる、というVモデル上のペア関係になる。

---

## 管理・自動化ドキュメント

- [自動化・ゲートマップ](helix-process/automation-gate-map.md) — Vモデル全工程の detector / ゲート（FE 含む）
- [逸脱 PLAN 起票マップ](helix-process/deviation-plan-map.md) — 各モードの逸脱 kind と generates
- [本線 DB 収束](helix-process/db-integration.md) — 個別モードデータを本線 Vモデル DB へ収束
- [DB 自動登録機構](helix-process/db-auto-registration.md) — イベント駆動で helix_db へ自動登録
- [検出 → モード連携](helix-process/detection-routing.md) — drift / 劣化 / 暴走 / 障害を Recovery / Incident / Reverse へ
- [FE detector 仕様](helix-process/fe-detector-spec.md) — FE 5種の決定論的判定仕様
- [横断機構](helix-process/cross-cutting-mechanisms.md) — interrupt / debt / drift-check / readiness の位置づけ
- [テスト観点ゲート](helix-process/test-perspective-gate.md) — W字補強（テスト重複・抜け漏れ検出）
- [CI / GitHub 運用](helix-process/ci-pr-workflow.md) — ブランチ pipeline ＋ ゲート証跡検証 ＋ PR 許可
- [L 単位 文脈注入](helix-process/layer-context-injection.md) — 各 L にスキル / ワークフロー / agent / command / orchestration を注入し迷いを消す
- [Learning Engine](helix-process/learning-engine.md) — スキル発火・トラブル・成功ログから recipe を学習し予防ルール化
- [観測・計測](helix-process/observability-metrics.md) — 発火・トラブル計測と AI 実行ログの自動取得（hook → helix_db）
- [自動走行・コンテキスト管理](helix-process/continuous-run-context-management.md) — 指定時間の自動走行と、Codex がセッションを fresh 再起動してコンテキストを溜めない設計（PoC）
- [横断検出](helix-process/cross-detection.md) — 依存漏れ・契約漏れ・接続欠損・デグレを DB 横断で検出
- [基盤整備状況](helix-process/infra-readiness.md) — 検証・テスト・検出基盤の実装済み／設計済みの一覧
- [スキル・コマンドの穴](helix-process/integration-map.md) — スキル/コマンドの欠落と未統合項目の一覧
- [フォルダ構成レビュー](helix-process/folder-structure-review.md) — 点検漏れ領域と docs/ への再構成方針
- [既存資産マッピング](helix-process/asset-mapping.md) — 既存資産の棚卸しと設計との対応・充足度
- [HELIX W（2段V合流）](helix-process/two-stage-agent-design.md) — V字を2回（一般システム＋エージェント昇華）通し L10 で合流（AI エージェントシステム時のみ）

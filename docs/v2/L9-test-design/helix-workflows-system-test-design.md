---
doc_id: l9-helix-workflows-system-test-design
title: "HELIX-workflows V2 総合テスト設計 (system test design)"
status: skeleton
created: 2026-05-27
owner: PM
process_layer: L9
pairs_design: docs/v2/L4-architecture/helix-workflows-system-architecture.md
parent_plan: L4-helix-workflows-方式設計plan
industry_standards:
  - IEEE 829-2008 (test documentation)
  - ISO/IEC/IEEE 29119-3 (test design)
---

# HELIX-workflows V2 総合テスト設計 (system test design)

## §0 概要

本 doc は L4 方式設計 `docs/v2/L4-architecture/helix-workflows-system-architecture.md` と 1 対 1 で結びつく総合テスト設計の skeleton です。HELIX-workflows V2 の dogfooding を対象に、要件からシステム検証までの統制を L4-L9 pair として凍結し、G4 で評価可能な trace を起票時点から保持します。

対象は L9 工程で実行される E2E・性能・監査・回復の 4 視点で、本文では L4 セクションとの ST-* trace を先に明確化し、実行手順は Step 3 で展開します。

## §1 総合テスト方針

L9 は PLAN を最終的に運用可能へ繋ぐ工程であり、L8 依存解消完了後に前提条件として起動します。テストはシステム横断を基本軸とし、BR-01〜BR-12 を対象シナリオとして扱います。

方針は以下の通りです。

- **E2E**: L4→L9 の構成と mode 回帰を含む end-to-end で検証。
- **機能横断**: PLAN/HOOK/DB/audit/agent 配線を単一シナリオで検証。
- **システム全体**: L12 の受入結果を起点とした安定性と再現性を確認。
- **L8 前提**: 結合テスト完了後、L9 でシステム全体一貫性を確認。

## §2 テスト項目 ST-***

| Test ID | 対象 L4 セクション | 目的 |
|---|---|---|
| ST-1 | §1 システム構成 | 三層構造（workflow / cli / skills）が連携することを確認 |
| ST-2 | §2 アーキテクチャ | PLAN↔ADR 併存と 4 artifact trace の機械検出 |
| ST-3 | §3 技術スタック | 技術選定と実行環境（Python/Bash/SQLite/GHA）が整合 |
| ST-4 | §4 BR-12 ratchet 機構 | baseline / check / hook 分割の E2E 検証 |
| ST-5 | §5 mandatory subagent | entry hook + `vmodel-semantics.yaml` で mandatory 起動 |
| ST-6 | §6 二重/三重 audit pattern | tl / pmo / doc-reviewer の証跡 3 重起動 |
| ST-7 | §7 採用 project 配布 | `helix init` 経由の portable 化が成立 |

## §3 機能横断テスト

### BR-01 シナリオ

新規 PLAN 起票 → V-model 整合 check fail → 自動差戻し → 修正 → G ゲート通過 → L7 接続の流れを 1 シナリオとして検証します。`helix doctor` の check 失敗と手動差戻しの観測可能性を保証し、回復ルートが再現可能か確認します。

### BR-02〜BR-12 シナリオ

- **BR-02**: 既存 PLAN scan + retrofit 自動起票 + 修正。
- **BR-03**: drift 解消フローと recovery / normalization 切替。
- **BR-04**: 9 mode 入口判定と Forward 回帰 event。
- **BR-05**: ペア凍結監査の pair freeze coverage。
- **BR-06**: 影響範囲 query の応答品質。
- **BR-07**: mandatory subagent 注入成功率。
- **BR-08**: 採用 project 展開の dogfooding 稼働率。
- **BR-09〜BR-12**: 既存資産整理 / migration / doc-review / ratchet 構成の fail-close。

シナリオは E2E で1系統化し、BR 単位テストと system test 全体指標の突合を行います。

## §4 非機能テスト

### 性能

`helix doctor` と検出パイプラインの完了時間を計測し、L9 の実用目標（現時点では skeleton で carry note）を満たすかを判定します。fast local / CI ルートを分離し、性能回帰が local 起票時点で検知できることを確認します。

### セキュリティ

PII / secret / credential 取り扱いに対する監査項目と、セキュリティ fail-close の実装トリガを確認します。CI とローカル両方で lint と doctor の分岐を再現し、回避ルートの欠如を検出します。

### 信頼性

hook fail-close（pre-commit/CI）、mode close、handover 受け渡しの復旧力を検証します。失敗ケースを含む replay テストで、再試行可能性と evidence 追跡が成立するか確認します。

### 保守性

フレームワーク drift 検知時の recoverability を確認します。`cicd`, `doctor`, `auditors`、`schema` の変更が trace 不能にならないかを重点点検します。

## §5 依存関係解消テスト

本節は L4 配線の依存 integrity を担保します。`PLAN dependencies graph` の欠落、`parent_design` 欠如、`pairs_test_design` 欠如、V-model pair freeze coverage 欠如を検出します。

- 依存解消 test で、依存 DAG の欠落リンクが 0 であること。
- `parent_design` が L4 plan で定義され、pair 先を保持していること。
- pair coverage が 1.0 へ近接していること。

## §6 V-model pair freeze 双方向 trace

### テーブル（L4 §X ↔ ST-X）

| L4 セクション | L9 テスト項目 |
|---|---|
| §1 システム構成 | ST-1 |
| §2 アーキテクチャ | ST-2 |
| §3 技術スタック | ST-3 |
| §4 BR-12 ratchet 機構 | ST-4 |
| §5 mandatory subagent 起動方式 | ST-5 |
| §6 二重/三重 audit pattern | ST-6 |
| §7 採用 project 配布 | ST-7 |

### 運用ルール

この trace 表は本 skeleton では最小版とし、Step 3 の本体化時に ST-ID への詳細 test case ID、観測コマンド、合否判定とエビデンス保存先を追加します。

## §7 残課題

- ST-7 以外の ST を自動再現可能な形式（script/fixture）へ変換する。
- 依存解消テストの具体的コマンド（graph 構築、pair check）を Step 3 で本文化する。
- 非機能テスト項目（性能・信頼性）を既存監査コマンドに紐づける。

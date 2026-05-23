---
doc_id: infra-readiness
title: "検証・テスト・検出基盤の整備状況"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# 検証・テスト・検出基盤の整備状況

## 概要

検証・テスト・検出の3基盤と、その上に乗る統合機構の整備状況を、実装済み / 設計済み・実装未 の区分で示す。

## 検証基盤

| 機構 | 状態 |
|---|---|
| gate（fail-close, gate-checks.yaml） | 実装済み |
| verify-all（全レイヤー検証） | 実装済み |
| verify-agent（harvest / design / cross-check） | 実装済み |
| harness / bench | 実装済み |
| 双方向 trace（vmodel lint） | 実装済み |
| 証跡検証 CI（ci-pr-workflow） | 設計済み・実装未 |

## テスト基盤

| 機構 | 状態 |
|---|---|
| test 212本（detector / plan / scrum / gate / reverse） | 実装済み |
| coverage（axis-02 coverage-erosion） | 実装済み |
| デグレ baseline（axis-11 regression / test_baseline） | 実装済み |
| W字観点ゲート（test-perspective-gate） | 設計済み・実装未 |

## 検出機構

| 機構 | 状態 |
|---|---|
| detector axis-01〜14 | 実装済み |
| doctor 横断チェック（document_drift / plan_cycle / drift_count 他 10種以上） | 実装済み |
| drift-check（D-API / D-CONTRACT / D-DB） | 実装済み |
| FE detector axis-15〜19 | 仕様済み（fe-detector-spec）・実装未 |
| 横断検出統合（cross-detection） | 設計済み・実装未 |
| 検出 → モード（detection-routing） | 設計済み・一部実装 |

## 上位統合機構（本セッションで設計）

| 機構 | 状態 |
|---|---|
| db-integration（本線 DB 収束） | 設計済み |
| db-auto-registration（自動登録） | 設計済み（hook 一部実装） |
| detection-routing（検出 → モード） | 設計済み |
| learning-engine（学習） | 設計済み（learning_engine 一部実装） |
| layer-context-injection（L 単位注入） | 設計済み（部品実装済み） |

## 結論

3基盤の骨格（gate / verify-all / verify-agent / test 212 / detector 14 / doctor / drift-check）は実装済みで、検証・テスト・検出の土台は整っている。

明確な実装の穴は FE detector の axis-15〜19（5軸）で、これは仕様（fe-detector-spec.md）が確定済みのため、実装すれば埋まる。

本セッションで設計した統合層（収束・自動登録・検出ルーティング・学習・L 単位注入・W字観点ゲート）は、いずれも既存部品の上に乗せる形で設計が完了しており、残るはリポジトリ上の実装作業。設計と仕様はすべて揃っているため、新たな設計判断を要する空白はない。

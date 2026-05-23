---
doc_id: db-integration
title: "Vモデル本線 DB への収束・接続"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# Vモデル本線 DB への収束・接続

## 概要

Vモデルの成果物（ドキュメント・工程表・PLAN・テスト・コード・テストカバレッジ）を本線 DB で一元管理し、相互の一致を保証する。Reverse / Discovery などモード別の個別データ管理を、本線 Vモデルの DB に戻して接続する構想。

## 本線 DB が管理する対象

helix_db を中心に、catalog / registry 群で構成される。

| registry / catalog | 管理対象 |
|---|---|
| plan_registry | PLAN（kind / generates / requires / 工程・ゲート） |
| code_catalog | コード（AST 抽出 → FTS5 インデックス） |
| command_catalog | コマンド |
| contract_registry | API / DB 契約 |
| model_registry | モデル |
| skill_catalog | スキル |

## Vモデル成果物の一致

本線 DB は次の対応を一致（整合）させる。

| 一致対象 | 突き合わせ |
|---|---|
| PLAN.generates ⇔ ドキュメント | 起票した成果物が docs/ に存在するか |
| PLAN ⇔ コード | generates のコードが code_catalog に存在するか |
| コード ⇔ テスト ⇔ カバレッジ | 実装・テスト・カバレッジの対応 |
| 実装 ⇔ ドキュメント | drift_db_diff で乖離（drift）を検出 |
| 設計 ⇔ テスト設計 | 双方向 trace（4 artifact） |

## 個別モードデータ → 本線収束

### 現状

- Reverse は docs/reverse/（R0–R4）、Discovery は .helix/scrum/（backlog / hypotheses）等、モード別の個別領域に実行時生成される。
- モードごとにデータが分散し、本線 DB と切り離れている。

### 構想（収束接続）

1. 逸脱モードの成果物も、対応する PLAN kind（reverse / poc / troubleshoot / recovery / add-design / add-impl）で起票する（deviation-plan-map.md）。
2. 起票した PLAN を plan_registry.bulk_import で本線 DB に取り込む。
3. モード別の個別 DB 管理を廃し、本線 Vモデルの DB に一元化する。
4. drift_db_diff で、取り込んだ成果物と実装・ドキュメントの一致を検証する。

### 効果

- どのモードがどこで逸脱し、どの成果物を生み、どこで標準フローに戻ったかを、本線 DB で機械的に追える。
- ドキュメント・工程表・PLAN・テスト・コード・カバレッジが、単一の DB で一致管理される。

## 接続フロー

```
モード作業（Reverse / Discovery / Incident / Add-feature）
   → 逸脱 kind の PLAN 起票（generates 定義）
   → plan_registry.bulk_import で本線 DB へ取り込み
   → 本線 DB で一致管理（generates ⇔ doc ⇔ code ⇔ test ⇔ coverage）
   → drift_db_diff で乖離検出
```

個別 DB の分散管理から、本線 Vモデル DB への収束接続が成立する。逸脱は「個別領域への書き込み」ではなく「kind 付き PLAN の起票 → 本線 DB 取り込み」という定型操作になり、Vモデル全成果物の一致管理が単一 DB で完結する。

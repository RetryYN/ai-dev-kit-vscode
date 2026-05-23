---
doc_id: db-auto-registration
title: "HELIX DB 自動登録機構"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# HELIX DB 自動登録機構

## 概要

PLAN・成果物・コード・テスト・スコアを、イベント駆動で helix_db に自動登録する仕組み。手動登録を排し、Vモデル成果物の一致管理（db-integration.md）の前提を自動で満たす。

## 登録イベントと hook

既存の hook を、登録イベントとして体系化する。

| イベント | hook | 登録対象 |
|---|---|---|
| PLAN 起票 | plan_registry.bulk_import | PLAN（kind / generates / requires） |
| コード変更 | code_catalog | AST → FTS5 インデックス |
| Codex 実行後 | codex_post_hook | 精度スコア（accuracy dimensions） |
| ゲート通過後 | feedback_hook | 5軸フィードバック（Lv1–5） |
| セッション停止 | stop-hook | handover dump（状態保全） |

## 自動登録フロー

```
イベント発火（起票 / commit / gate pass / Codex 実行 / stop）
   → hook 起動
   → helix_db へ登録（plan_registry / code_catalog / contract_registry / skill_catalog）
   → catalog / registry 更新
```

## 設計方針

- 登録は「人が DB に書く」のではなく「イベントが hook を起動して書く」形に統一する。
- 各モードの逸脱 PLAN（reverse / poc / recovery 等）も、起票時に plan_registry へ自動取り込みする（deviation-plan-map.md）。
- generates で宣言した成果物が生成されたら、code_catalog / doc に自動反映する。

## 効果

- 手動登録漏れを排除し、DB が常に最新の成果物・スコアを保持する。
- db-integration の一致管理（doc ⇔ code ⇔ test ⇔ coverage）と drift 検出の前提が、追加作業なしで揃う。
- 自動登録で充実した DB が、次の「検出 → モード連携」（detection-routing.md）の入力になる。

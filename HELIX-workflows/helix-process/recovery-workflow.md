---
doc_id: workflow-recovery
title: "Recovery HELIX ワークフロー（AI 暴走対応）"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# Recovery HELIX ワークフロー（AI 暴走対応）

## 概要

AI エージェント（Claude Code / Codex）が独断専行・暴走したときに、ガード（事前警告）と収束（事後リカバリー）で対応するモード。kind=recovery。「これ大丈夫？」と止めるガードと、暴走状態を再開ポイントへ戻す収束の二段構え。

## 二段構えの機構

### ガード機構（事前警告「これ大丈夫？」）

危険な操作・逸脱を検出して警告・停止する。

| 機構 | 検出・警告 |
|---|---|
| agent_mandatory（audit_phase / fire_mandatory_audit） | 必須エージェント役割からの逸脱を監査 |
| budget | トークン・操作の過剰消費を上限で警告 |
| gate（fail-close） | 危険操作を関所で停止 |
| codex_post_validation | Codex（AI）出力の検証 |
| lock（file + DB metadata） | 競合・並行暴走の防止 |

### 収束機構（事後リカバリー）

暴走した状態を、再開ポイントへ戻す。

| 機構 | 収束 |
|---|---|
| recovery kind PLAN | 再開ポイント確定・認識訂正履歴・recovery-log |
| stop-hook | 停止時の状態 dump ＋ compact 推奨 |
| cutover_orchestrator | ロールバック・切替 |

## 入口判定

| 状況 | Recovery を使う理由 |
|---|---|
| AI が想定外の大規模変更をした | 停止して再開ポイントへ戻す |
| 独断専行で工程・設計から逸脱した | agent_mandatory 監査で逸脱を捕捉 |
| 認識のズレが蓄積し収拾がつかない | 認識訂正履歴を整理して収束 |
| 予算・操作が過剰に消費されている | budget 上限で警告・停止 |

## 基本フロー

```
ガード検出（逸脱・過剰消費）→ 警告／停止（gate・stop-hook）→ 状態把握
   → 再開ポイント確定（recovery PLAN）→ 認識訂正 → ロールバック／再開
```

1. ガード検出: agent_mandatory・budget・gate が逸脱や過剰を検出
2. 警告／停止: 「これ大丈夫？」を出し、stop-hook で状態を dump
3. 状態把握: どこから逸脱したかを特定
4. 再開ポイント確定: recovery PLAN で戻す地点を決める
5. 認識訂正: 認識訂正履歴を recovery-log に残す
6. ロールバック／再開: cutover_orchestrator で戻し、標準フローへ復帰

## 起票する PLAN kind

- kind=recovery、generates=recovery-log（再開ポイント・認識訂正履歴）
- 逸脱と kind の対応は deviation-plan-map.md を参照。

## 位置づけ（似た機構との違い）

| モード | 対象 |
|---|---|
| interrupt（IIP / CC） | 開発中の設計ギャップ・要件変更の割り込み |
| Incident | 本番稼働中の障害（hotfix） |
| Recovery | AI エージェントの暴走・独断専行（ガード＋収束） |

## Forward 接続

収束後、確定した再開ポイントから標準フロー（L0–L14）へ復帰する。認識訂正履歴と再発防止策は L14 運用検証へフィードバックする。

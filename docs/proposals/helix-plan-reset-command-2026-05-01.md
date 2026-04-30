# helix-plan reset コマンド追加提案

> 日付: 2026-05-01
> 起点: HELIX-V3-FOLLOWUP — handover Next Action #5「helix-plan の finalize 後 re-review 制約調査」
> 関連: PLAN-008 v2 改訂の差し戻し時に発覚

## 調査結果

| 項目 | 結果 |
|---|---|
| `helix plan review` 受付 status | `draft / reviewed / rejected` のみ（[cli/helix-plan:408](../../cli/helix-plan#L408)） |
| `helix plan finalize` 受付条件 | `review.status == approve`（[cli/helix-plan:487](../../cli/helix-plan#L487)） |
| **finalize 後の公式 status 戻し CLI** | **未実装** |
| `.helix/plans/*.yaml` の git 追跡 | 未追跡（直編集の痕跡が辿れない） |

## PLAN-004 v5 が通った推定経緯

`.helix/plans/PLAN-004.yaml` は git 未追跡のため `git log -- .helix/plans/PLAN-004.yaml` で履歴 0 件。
review.json mtime と finalized_at のタイムスタンプから、`status: finalized` を **手動で `draft` ないし `reviewed` に書き戻して** review→finalize を再実行した可能性が最有力。CLI を介した正規操作ではない。

## 提案: `helix plan reset` 追加

```
helix plan reset --id PLAN-XXX [--to draft|reviewed] [--reason "v2 改訂に伴う差し戻し"]
```

### 仕様骨子
- 受付 status: `finalized / reviewed / approve` (rejected は既に review 受付なので不要)
- 既存 `review.*` を `revision_history[]` に append-push（元の reviewed_at / verdict / review_file を保存）
- `status` を `--to` で指定（既定: `draft`）
- `finalized_at` を null にリセット（finalized → draft の場合）
- audit ログに `plan_reset` イベントを emit (helix.db `events` 表があれば)

### スコープ外
- review.json 自体の上書き（履歴は revision_history のポインタで参照）
- finalize 済みファイルの content rollback（content は手動編集を許容、CLI は status マシンのみ管理）

## 適用先

- PLAN-006 / PLAN-007 / PLAN-008 / PLAN-009 / PLAN-010 の今後の改訂時
- HELIX-V3-FOLLOWUP の派生実装 8 系統に **9 番目として追加候補**

## 優先度判定

**P1** — 後続 PLAN 改訂のたびに yaml 手動編集が必要な状態は audit 性が低く、再現性も損なう。派生実装の足場 (A) と並行で実装すべき。

---
doc_id: continuous-run-context-management
title: "自動走行とコンテキスト管理"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# 自動走行とコンテキスト管理

## 結論

- 本命: PoC「Claude オーケストレーション ＋ Codex セッションクリーナー」。Claude が指揮し、Codex が Claude の対話セッションを context 閾値で fresh 再起動する。対話セッション扱いでサブスク内、毎回 fresh で drift なし。
- フォールバック: 延命型（対話 + tmux で /compact 送信）。サブスク内だが /compact 要約のため drift が残る。
- 不採用: headless（claude -p）使い捨て型。2026/6/15 から Agent SDK クレジット課金（サブスク外）になるため。

## 問題

セッション単位で止まり、対話を続けるとコンテキストが溜まる。コンテキストが実際に減る契機は /compact・/clear・セッション terminate→fresh・auto-compact（満杯任せ）の4つだけ。handover を書くこと（メモ）はコンテキストを減らさない。Claude は自分の履歴を消して走り続けられないため、必ず外部刺激（別プロセスによる再起動、または /compact 送信）が要る。

## 本命: Claude オーケストレーション ＋ Codex セッションクリーナー（kind=poc）

役割を固定する。Claude は自分を再起動できないが、Codex が外から対話セッションを起こす。

| 役割 | 担当 |
|---|---|
| オーケストレーション（判断・作業・handover 記録） | Claude Code |
| セッションのクリーンアップ（context 監視・新 Claude 起動・旧終了・handover 渡し） | Codex |

仕組み:

```
Claude（対話）作業 → context 0.70 到達 → handover 記録
   → Codex が新 Claude セッションを起動（tmux new-session 'claude'）← fresh・サブスク内
   → 新 Claude が handover を読んで再開 → Codex が旧 Claude を終了
```

利点: 各セッションが起動ごとに完全 fresh（/compact の要約 drift も起きない）。対話セッション扱いなのでサブスク内に留まり、headless の課金分離を回避できる。Claude は指揮に専念し、コンテキスト管理の手間を持たない。

検証項目（PoC）:

1. Codex が Claude 対話セッションを外部から起動・終了できるか（tmux / CLI 制御）。
2. handover で状態が引き継がれ、fresh Claude が前作業を継続できるか。
3. 起動される Claude が対話セッション扱いでサブスク内に留まるか（4/4 の third-party harness 判定の影響）。
4. context が実際にリセットされ、drift が解消するか。
5. 中断・再開を跨いでオーケストレーション（判断進行）が一貫するか。

成功基準: ユーザー指定時間のあいだ、サブスク内で、毎回 fresh、handover を介して一貫した作業継続ができること。3（課金）と4（drift 解消）の両立が要。

位置づけ: Discovery モード（kind=poc）で起票し、verify script で実現性を確認。confirmed なら本実装へ昇格。generates: docs/research/<slug>-poc-findings.md ＋ verify script。

## フォールバック: 延命型（tmux + /compact）

対話セッションを保ったまま、外部から /compact を送ってコンテキストを縮める。本命 PoC が未達のときの代替。

```bash
tmux new-session -d -s helix 'claude'
while true; do
  pct="$(python3 -m cli.lib.handover_auto_dump context-pct --json 2>/dev/null | jq -r '.context_pct_estimate // 0')"
  awk "BEGIN{exit !($pct >= 0.70)}" && tmux send-keys -t helix '/compact' Enter
  sleep 60
done
```

サブスク内で回るが、/compact は要約のため情報が劣化し、drift は完全には消えない。

## 課金の制約（2026）

2026/6/15 から claude -p / Agent SDK / GitHub Actions / third-party のプログラマティック使用は、Claude プランのサブスク上限から外れ、別の月次 Agent SDK クレジット（$20 Pro / $100 Max 5x / $200 Max 20x、フル API レート、繰り越しなし）に課金される。対話的な claude（ターミナル / IDE）はサブスク内のまま。4/4 から third-party harness のサブスクアクセスはブロック済み。

このため headless 使い捨て型は不採用とし、本命・フォールバックとも「対話セッション」を使ってサブスク内に留める。

## 自動走行の制御

| 機構 | 役割 |
|---|---|
| heartbeat-scheduler | time window で ScheduleWakeup（次の wake 判定） |
| budget | ユーザー指定時間を time cap に設定（runaway 防止） |
| PLAN（工程表） | 各 wake の fresh セッションが再開する状態 |
| harness_monitor | 実行監視 |

発火条件は handover 記録後。Stop hook（helix-stop-hook）が handover_auto_dump で .helix/handover/CURRENT.md に Next Action を記録し、heartbeat-scheduler が `should_schedule = carry_count > 0 and within_time_window` で ScheduleWakeup を予約する。carry_count > 0（引き継ぎ記録あり）が条件なので、記録が残ってからしか次が起きない。

## 不足（穴）

- handover 記録後に Codex が Claude セッションを terminate → fresh 起動する制御（PoC の本体）。
- ユーザー指定時間を budget の time window へ渡す配線。
- 対話セッションを自動起動する仕組みが third-party harness と判定されないかの規約確認。

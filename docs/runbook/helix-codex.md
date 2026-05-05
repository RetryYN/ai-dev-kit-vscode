# Runbook: helix codex (Codex 委譲)

## 概要

`helix codex --role <role> --task "..."` で Codex CLI に実装・レビューを委譲するための shim。`cli/helix-codex` 本体。

## 正常系の動作確認

```bash
helix codex --role pg --task "echo test" --dry-run
```

dry-run で生成されるプロンプトに以下が含まれること:
- system prompt (ロール定義)
- CODEX_DISCIPLINE_PROMPT §1〜§5 (Plan Consent / WBS First / HELIX Commands / Output Evidence / **No Commit**)
- TASK_INPUT セクション

## よくある障害パターン

### 1. CPU 0% で hang

**症状**: ps で見ると `pcpu 0.0` が 5 分以上続く、output ファイルサイズが伸びない。

**一次対応**:
```bash
ps -eo pid,etime,pcpu,args | grep helix-codex
kill -TERM <pid>
sleep 2
kill -KILL <pid>   # 必要なら
```

ファイル編集が途中まで完了している可能性が高いので、`git diff` で確認後、Opus 側で pytest / bats を直接走らせて代替検証する。

**根因**: 過去の `--full-auto` 未指定 hang は 2026-04-30 commit 8d0274c で解消済み。再発時は Codex CLI 側の sandbox 待機状態を疑う。

### 2. plan-only guard で write できない

**症状**: 出力に `plan_only_guard=true / sandbox=read-only` が出て実装.1 で停止。

**対応**: `--approved --plan-id PLAN-NNN --task-id Sprint-N` を付けて再投入。タスク文に「即実装」「ファイル編集を実行」を明示。

### 3. 委譲先が勝手に commit した

**対応**: `git reset --soft HEAD~1` で巻き戻して呼び出し元 (Opus / TL モード Codex) で commit し直す。CODEX_DISCIPLINE_PROMPT §5 で禁止されているが念のため確認。

## エスカレーション基準

- Codex セッションが TIMEOUT (1800s) に達して落ちた → 範囲を分割して再投入
- 委譲先が D-API / D-DB / D-CONTRACT 変更を要求してきた → Opus 判断、勝手に確定しない
- secret / 認証 / 決済 / PII を扱うタスク → 人間確認必須

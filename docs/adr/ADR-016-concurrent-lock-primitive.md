# ADR-016: concurrent lock primitive を standalone module として導入する

## Status

Accepted (2026-05-10)

## 業界 standard 参照 (Web 検索 retrofit 2026-05-19)

### 参照ハイライト
- Google SRE 書籍のチーム構成では、`tech lead (TL)`、`manager (SRM)`、`project manager (PM/TPM/PgM)` が明記され、TL はチームの技術方向性を担う責務を持つことが示される（2026-05-19時点）。
- Spotify Engineering の公開資料では、`squad`（小規模自律チーム）・`tribe`・`chapter`・`guild` の構造と、squad 自律・知識共有・レビュー文化が言及される。
- LangGraph は「エージェントオーケストレーション」を前提とした低レベルの実行基盤として、durable execution / streaming / human-in-the-loop を強調する。一方 CrewAI はロール付きエージェントを `Crew` として組成する multi-agent フレームとして説明される（2026-05-19時点）。
- OpenAI Codex CLI の公式ページは、ローカル端末でリポジトリを検査・変更・実行できるコーディングエージェントとしての説明と、`open source` である公開情報を明示する。

### 参照先
- Google SRE: <https://sre.google/sre-book/communication-and-collaboration/>
- Spotify squad model: <https://engineering.atspotify.com/2014/09/squad-health-check-model>
- LangGraph overview: <https://docs.langchain.com/oss/python/langgraph/overview>
- CrewAI (Crews): <https://docs.crewai.com/en/concepts/crews>
- CrewAI Introduction: <https://docs.crewai.com/introduction>
- OpenAI Codex CLI: <https://developers.openai.com/codex/cli>
- OpenAI Codex Repo: <https://github.com/openai/codex>

## Deciders

PO (ユーザー), PM (Opus), TL

---

## Context

`cli/lib/handover.py` では、`lock_open` / `lock_close` が `fcntl.flock(LOCK_EX)` / `LOCK_UN` を ad-hoc に使っている
（`cli/lib/handover.py` lines 277-288）。加えて、`archive_current` と
`atomic_write_json_with_revision` は `os.replace` を使って atomic write を行っている
（`cli/lib/handover.py` lines 493, 500, 531）。

この実装は handover の単一 critical path には一定の保護を与える一方、次の未保証点を残している。

- lock path が handover 内ローカル実装に閉じており、`.helix/locks/<key>.lock` の統一規約がない
- timeout / retry がなく、待ち合わせ戦略が呼び出し側から制御できない
- 共通 primitive がないため、`helix.db` や `.helix/phase.yaml` へ同じ規律を適用できない
- ad-hoc 実装のままでは critical path ごとに race window や待機ポリシーがばらつく

PLAN-042 W-4 の責務は、この問題を critical path 全面展開ではなく
**standalone PoC + ADR** に限定して切り出し、PLAN-043 以降での適用優先度と運用原則を固定することにある。
本 PLAN では `cli/lib/handover.py` を編集しない。

## Decision

option A を採用する。`cli/lib/concurrent_lock.py` を新設し、
`fcntl.flock(LOCK_EX | LOCK_NB)` を共通 primitive 化する。
lock file は `.helix/locks/<key>.lock` に統一し、name は英数字と `-` / `_` のみ許可する。

PoC module の API は次の 3 点とする。

- `acquire(name: str, timeout: float = 5.0) -> int`
- `release(fd: int) -> None`
- `file_lock(name: str, timeout: float = 5.0)`

wait policy は retry interval 0.1s、default timeout 5s とする。
timeout 超過時は `TimeoutError` を送出し、呼び出し側が fail-close できるようにする。

critical path への適用優先度は PLAN-043+ で次の順とする。

1. `.helix/handover/CURRENT.json`
2. `helix.db` SQLite write
3. `.helix/phase.yaml`

deadlock 回避方針として、複数 lock が必要な場合は alphabetical lock name 順で acquire する。

## Considered Alternatives

### A: `cli/lib/concurrent_lock.py` 共通 module 化（採用）

- 利点: 既存 `flock` の知識を再利用でき、handover / SQLite / phase へ段階展開しやすい
- 利点: lock path、timeout、retry、入力検証を 1 箇所で統一できる
- 欠点: Linux/Unix 系の `fcntl` 前提であり、cross-platform primitive ではない

### B: SQLite transaction に寄せる（不採用）

- 利点: `helix.db` には自然に適用できる
- 欠点: `.helix/handover/CURRENT.json` や `.helix/phase.yaml` の file critical path を直接保護できない
- 欠点: PLAN-042 W-4 の scope を超え、schema / transaction policy 判断に広がりやすい

### C: ad-hoc 実装を維持する（不採用）

- 利点: 今回の write は最小で済む
- 欠点: timeout / retry / path 不統一が残り、critical path ごとの再実装が続く
- 欠点: PLAN-038 由来の concurrent reader 問題に対する再利用可能な改善にならない

## Consequences

1. PLAN-042 W-4 で standalone PoC と race regression test を先に確立できる。
2. `cli/lib/handover.py` は現時点では非変更のまま維持し、接続は PLAN-043 に carry する。
3. 以後の critical path 導入では、timeout default 5s と alphabetical acquisition order を前提条件にできる。
4. lock name validation により path traversal を防ぎ、`.helix/locks/` 配下への閉域化を維持する。

## Scope

本 PLAN scope は ADR 起票と standalone PoC のみである。
`cli/lib/handover.py` への接続、`helix.db` / `.helix/phase.yaml` への実適用、本番影響を伴う全面展開は
PLAN-043 で扱う。

## Related

- PLAN-042 W-4
- PLAN-038 W-1 P3 debt
- ADR-014
- ADR-015

## References

- `cli/lib/handover.py`
- `cli/lib/concurrent_lock.py`
- `cli/lib/tests/test_concurrent_lock.py`

## Revision History

| Date | Description |
|---|---|
| 2026-05-19 | 業界 standard 引用 retrofit (W5c-4、PLAN-087 ガードレール準拠) |

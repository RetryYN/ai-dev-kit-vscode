---
plan_id: PLAN-106
title: datetime.utcnow() Python 3.13 removal 対応 完全 sweep
status: completed
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
kind: refactor
drive: be
layer: L4
size: S
created_at: 2026-05-23
completed_at: 2026-05-23
completion_note: "起票後の全 repo sweep で datetime.utcnow() / datetime.utcfromtimestamp() の hit は 0 件 (cli/scripts/.claude/verify/ 全 dir 確認済)。実体は本 session commit e3c658d で cli/lib/agent_mandatory.py:101 修正時に既に解消済だった。本 PLAN は status=completed として close、追加修正不要。"
authors:
  - PM (Opus)
  - PMO (Sonnet)
  - PE (Codex gpt-5.3-codex-spark)
agent_slots:
  - role: pg
    slot_label: "PE (pg role、Codex gpt-5.3-codex-spark) — grep scan + 一括置換実装"
  - role: pmo-sonnet
    slot_label: "PMO — scan 結果確認・修正範囲レビュー (on-demand)"
generates:
  - artifact_type: python_module
    path: cli/lib/agent_mandatory.py
dependencies:
  requires:
    - PLAN-100
  blocks: []
  parent: null
related_docs:
  - cli/lib/agent_mandatory.py
  - cli/lib/tests/
acceptance_criteria:
  - "grep -rn 'datetime\\.utcnow\\|datetime\\.utcfromtimestamp' --include='*.py' . で 0 hit"
  - "python3 -W error::DeprecationWarning -m pytest cli/lib/tests/ -q で全 PASS (DeprecationWarning 0 件)"
  - "bash/shell script で date コマンド使用箇所が UTC 明示 (date -u) であること確認"
  - "helix doctor 24 pass / 0 fail / warn 維持"
  - "既存 test 全件 PASS (regression なし)"
---

# PLAN-106: datetime.utcnow() Python 3.13 removal 対応 完全 sweep

## L2 凍結 (ADR snapshot)

本 PLAN tree 内に L2 大局判断なし (Python 公式 deprecation への対応、代替 API は `datetime.now(timezone.utc)` に確定済)。ADR snapshot 不要。

## 背景

Python 3.12 で `datetime.datetime.utcnow()` および `datetime.datetime.utcfromtimestamp()` に DeprecationWarning が追加され、Python 3.13+ での removal が予定されている ([PEP 696 / bpo-16499](https://docs.python.org/3/whatsnew/3.12.html#datetime))。

**本 session (2026-05-23) の対応状況**:

- `cli/lib/agent_mandatory.py:101` の `datetime.utcnow()` を `datetime.now(timezone.utc)` に修正済 (commit e3c658d)
- `cli/lib/tests/` 配下の全 test が `-W error::DeprecationWarning` 付きで 24/24 PASS 確認済
- ただし `scripts/` / `.claude/hooks/` / `cli/templates/` / `verify/` / プロジェクト root 等は **未確認**

残留 hit がある場合、Python 3.13 移行時に `AttributeError: module 'datetime' has no attribute 'utcnow'` で実行時エラーになる。HELIX framework の安定性保証のため完全 sweep を実施する。

## WebSearch 履歴

Python 公式 deprecation 対応のため外部 standard 調査は不要 (PLAN-087 ガード: 内部 refactor は除外対象)。参照: [Python 3.12 What's New §datetime](https://docs.python.org/3/whatsnew/3.12.html#datetime)。

## 設計方針

### 置換ルール (Python)

| 旧 API | 新 API |
|---|---|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| `datetime.datetime.utcnow()` | `datetime.datetime.now(datetime.timezone.utc)` |
| `datetime.utcfromtimestamp(ts)` | `datetime.fromtimestamp(ts, tz=timezone.utc)` |
| `datetime.datetime.utcfromtimestamp(ts)` | `datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)` |

import 追加 (各 file の既存 import に合わせる):

```python
# 既存: from datetime import datetime
# 追加: from datetime import datetime, timezone

# 既存: import datetime
# そのまま: datetime.datetime.now(datetime.timezone.utc)
```

### 置換ルール (Bash / Shell)

`date -u` で UTC 出力が標準。`$(date +"%Y-%m-%dT%H:%M:%S")` (timezone 指定なし) を確認し、必要なら `$(date -u +"%Y-%m-%dT%H:%M:%SZ")` に変更。

### 確認スコープ

```
全 .py ファイル: cli/ scripts/ .claude/ verify/ helix/ docs/ (*.py のみ)
全 .sh ファイル: cli/ scripts/ .claude/hooks/ (date コマンド使用箇所)
```

## 実装計画 (Sprint .1 - .3)

### Sprint .1: scan + hit 列挙 (PE 委譲または Opus 直接)

scan コマンド:

```bash
# Python: utcnow / utcfromtimestamp の hit 列挙
grep -rn "datetime\.utcnow\|datetime\.utcfromtimestamp" \
  --include="*.py" \
  cli/ scripts/ .claude/ verify/ helix/ docs/ 2>/dev/null

# Bash: timezone 未指定の date コマンド (参考確認)
grep -rn 'date +"%Y-%m-%d' \
  --include="*.sh" \
  cli/ scripts/ .claude/hooks/ 2>/dev/null | grep -v "date -u"
```

期待結果:

- cli/lib/agent_mandatory.py は commit e3c658d で修正済 → hit なし
- その他の hit 件数を記録し Sprint .2 修正対象リストを作成

Sprint Exit 条件:

- Python hit 件数を確定
- hit 0 → Sprint .2 skip、Sprint .3 で検証のみ
- hit 1+ → Sprint .2 修正へ

### Sprint .2: 修正実装 (PE 委譲、hit ありの場合のみ)

**前提**: Sprint .1 で hit 1+ 件の場合のみ実施。

実装方針:

1. 各 hit file を Read して import 構造を確認
2. 置換ルール表に従い `datetime.utcnow()` → `datetime.now(timezone.utc)` に変更
3. import 行に `timezone` を追加 (既に含まれる場合はスキップ)
4. `utcfromtimestamp` は `fromtimestamp(ts, tz=timezone.utc)` に変更
5. Bash の `date` コマンドは UTC 明示が必要な箇所のみ `-u` 追加

mandatory in sprint:

- [ ] 各修正 file の `python3 -m py_compile <file>` PASS
- [ ] `bash -n <file.sh>` PASS (shell script 変更時)
- [ ] 直接関連 test が存在する場合は単体実行 PASS

Sprint Exit 条件:

- 全修正 file の `py_compile` PASS
- 修正 file リストと変更内容をまとめて Sprint .3 へ引き渡し

### Sprint .3: 検証 + commit (Opus 直接または PE 委譲)

検証手順:

```bash
# 1. Python DeprecationWarning 全 sweep
python3 -W error::DeprecationWarning -m pytest cli/lib/tests/ -q --tb=short

# 2. grep で 0 hit 確認
grep -rn "datetime\.utcnow\|datetime\.utcfromtimestamp" \
  --include="*.py" \
  cli/ scripts/ .claude/ verify/ helix/ docs/ 2>/dev/null

# 3. helix doctor
cli/helix doctor

# 4. 全体回帰 (bats)
cli/helix test --no-pytest --bats-only
```

mandatory in sprint:

- [ ] `python3 -W error::DeprecationWarning -m pytest cli/lib/tests/ -q` PASS (0 DeprecationWarning)
- [ ] grep 0 hit 確認
- [ ] helix doctor 24 pass / 0 fail 維持
- [ ] セルフレビュー (Opus)

Sprint Exit 条件:

- 全検証 PASS で DoD 達成
- commit message: `refactor(datetime): utcnow() → now(timezone.utc) 完全 sweep (Python 3.13 対応)`

## DoD (Definition of Done)

- [ ] `grep -rn "datetime\.utcnow\|datetime\.utcfromtimestamp" --include="*.py" .` で 0 hit
- [ ] `python3 -W error::DeprecationWarning -m pytest cli/lib/tests/ -q` で全 PASS
- [ ] helix doctor 24 pass / 0 fail / warn 維持
- [ ] 既存 test 全件 regression なし
- [ ] commit 済

## carry / 学び (起票時記録)

- **本 PLAN の難度は hit 件数次第**: Sprint .1 scan で 0 hit なら本 PLAN は close に近い (Sprint .3 検証のみ)。多数 hit の場合でも置換は機械的で S size 想定内。
- **timezone-aware datetime への統一**: `datetime.now(timezone.utc)` は timezone-aware object を返す。既存テストの `datetime == expected_datetime` 比較が naive datetime と比較している場合は assert を更新する必要がある ([[feedback_pytest_fixture_time_dependent_flake]] 参照)。
- **Python 3.13 移行タイムライン**: 2025-10 リリースの Python 3.13 で removal が確定。本 PLAN は予防的 sweep であり blocking 優先度は P2。

## 関連 reference

- [[feedback_pytest_fixture_time_dependent_flake]] (datetime 動的化の先行実装、本 PLAN の背景)
- commit e3c658d (cli/lib/agent_mandatory.py:101 の先行修正)
- PLAN-100 (V5 framework retrofit、parent chain)
- [Python 3.12 What's New §datetime](https://docs.python.org/3/whatsnew/3.12.html#datetime)

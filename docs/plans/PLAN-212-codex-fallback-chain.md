---
plan_id: PLAN-212
title: "PLAN-212: Codex 委譲 fallback chain (sandbox fail 時の Opus 直接 fallback)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
size: M
created: "2026-05-23"
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — sandbox fail signature 検出ロジック + fallback chain 実装 + helix.db 記録"
  - role: pmo-sonnet
    slot_label: "PMO — fallback 発火条件・signature 正確性レビュー・PLAN-137 との境界確認"
  - role: tl-advisor
    slot_label: "TL adversarial check — fallback が誤発火した場合の安全性リスク評価 (Sprint .2 前)"
generates:
  - artifact_path: cli/lib/codex_fallback_detector.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_codex_fallback_detector.py
    artifact_type: test
  - artifact_path: cli/helix-codex
    artifact_type: cli_extension
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-137-codex-approved-auto-flag
  blocks: []
related_adr: []
related_plans:
  - PLAN-137
  - PLAN-156
related_docs:
  - helix/CODEX_TL_MODE.md §helix codex hard guard
  - CLAUDE.md §委譲 Codex のコミット禁止
---

# PLAN-212: Codex 委譲 fallback chain (sandbox fail 時の Opus 直接 fallback)

## L2 凍結 (ADR snapshot)

既存 helix-codex hard guard (CODEX_TL_MODE.md) および PLAN-137 (classify framework) の延長実装であり、
新規 L2 大局判断 (fail-close 化方針変更 / 新 framework 採用) は発生しないため ADR snapshot は不要。

---

## §0. 背景・位置付け

2026-05-23 session にて `helix codex --role se` 委譲が sandbox read-only 制約で fail する事例が多発した。
主な失敗パターン:

- SQLite `.helix/helix.db` open 時の `SQLITE_READONLY` エラー
- `__pycache__` 生成時の permission denied
- pytest tmp dir (`/tmp/pytest-*`) 生成不可

現状、この fail は Codex 出力に混在するエラーメッセージとしてのみ現れ、Opus 側が手動で検出して
対処方針を決める必要がある。自動的に fallback 提示まで持っていく仕組みが存在しない。

**PLAN-137 との関係**: PLAN-137 = 事前 classify で --approved 付与、本 PLAN = 事後 fallback chain。補完的に機能する。

**WebSearch skip 根拠**: 内部 CLI 拡張。外部ライブラリ採用なし。

---

## §1. 設計方針

### fallback chain 概要

```
helix codex --role se --task "..." 実行
        ↓
  [Codex 出力取得]
        ↓
  signature 検出 (codex_fallback_detector.py)
        ↓ 検出あり
  fallback 提示出力 + helix.db 記録
  "sandbox fail を検出しました。以下の代替経路を試してください:
   1. helix codex --role se --approved --task '...'  (write sandbox)
   2. 直接 Codex exec + HELIX_ALLOW_RAW_CODEX=1      (raw exec)"
```

### sandbox fail signature 一覧

| ID | パターン | 説明 |
|---|---|---|
| SF-001 | `SQLITE_READONLY` / `unable to open database file` | SQLite write 不可 |
| SF-002 | `Permission denied.*__pycache__` | Python キャッシュ生成不可 |
| SF-003 | `Permission denied.*tmp` / `OSError.*tmp` | tmp dir 生成不可 |
| SF-004 | `Read-only file system` | sandbox 全体の read-only |
| SF-005 | `cannot write to.*sandbox` | Codex 自己報告 sandbox fail |

signature は正規表現で OR マッチ。誤検知防止のため `PermissionError` の文脈が Codex 出力
(stderr / stdout 含む) の先頭 50 行以内に存在することを条件とする。

### codex_fallback_detector.py インタフェース

```python
def detect_sandbox_fail(output: str) -> list[str]:
    """output: Codex の stdout + stderr 結合。戻値: 検出した signature ID リスト (空 = 正常)"""

def build_fallback_message(task: str, role: str, signatures: list[str]) -> str:
    """fallback 提示文字列を生成する"""

def record_fallback(
    task: str, role: str, signatures: list[str], db_path: str | None = None
) -> None:
    """helix.db の codex_fallback_history に記録する"""
```

### helix.db スキーマ追加

```sql
CREATE TABLE IF NOT EXISTS codex_fallback_history (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT    NOT NULL DEFAULT (datetime('now','utc')),
    role      TEXT    NOT NULL,
    task_hash TEXT    NOT NULL,  -- sha256(task)[:16]
    signatures TEXT  NOT NULL,  -- JSON list of SF-* IDs
    resolved  INTEGER NOT NULL DEFAULT 0  -- 0: unresolved / 1: resolved
);
```

---

## §2. 実装計画

### Sprint .1: fallback detector Python helper (se、size S)

1. `cli/lib/codex_fallback_detector.py` 新規作成
   - `detect_sandbox_fail` / `build_fallback_message` / `record_fallback` の 3 関数
   - helix.db migration は既存 `helix_db.py` の migration chain に v-next として追加
2. `python3 -m py_compile cli/lib/codex_fallback_detector.py` PASS

受入条件: SF-001〜SF-005 パターン検出 PASS / 正常出力での false positive なし

### Sprint .2: helix-codex 統合 + CLI flag (se、size S / tl-advisor review 前)

1. `cli/helix-codex` に `--fallback` / `--fallback-mode` flag 追加
2. Codex 出力取得後に `detect_sandbox_fail` を呼び、signature あれば fallback メッセージ出力
3. `bash -n cli/helix-codex` PASS

受入条件: `helix codex --role se --task "実装" --fallback opus-direct` が fallback 提示出力 /
`--no-fallback` 指定時は fallback 検出をスキップする

tl-advisor review を Sprint .2 着手前に実施 (誤検知リスク・fallback メッセージの安全性評価)。

### Sprint .3: テスト + pmo-sonnet review (qa、size S)

1. `cli/lib/tests/test_codex_fallback_detector.py` 新規作成 (10 case)
   - SF-001〜SF-005 各検出 / 正常出力での false positive / `build_fallback_message` フォーマット /
     `record_fallback` DB 書き込み / 既存 helix codex 回帰
2. `pytest cli/lib/tests/test_codex_fallback_detector.py -v` 全 PASS
3. pmo-sonnet review (PLAN-137 boundary / signature 誤検知評価)

---

## §3. DoD

- [ ] `detect_sandbox_fail` が SF-001〜SF-005 全 signature を検出できる
- [ ] 正常な Codex 出力 (3 種) で false positive が発生しない
- [ ] `helix codex --fallback opus-direct` が fallback 提示メッセージを出力する
- [ ] fallback 履歴が `codex_fallback_history` テーブルに記録される
- [ ] `python3 -m py_compile cli/lib/codex_fallback_detector.py` PASS
- [ ] `bash -n cli/helix-codex` PASS
- [ ] unit test 10 case 全 PASS
- [ ] tl-advisor review 完了 (Sprint .2 着手前)
- [ ] pmo-sonnet review 完了 (Sprint .3)
- [ ] 既存 helix codex 動作回帰なし
- [ ] `python3 cli/lib/plan_validator.py docs/plans/PLAN-212-codex-fallback-chain.md` PASS

---

## §4. デグレ禁止

- 既存の `helix codex --approved` / `--force-plan-only` の挙動を変更しない
- `--no-fallback` flag で fallback 検出を完全無効化できる
- DB migration は idempotent (既存テーブルが存在する場合は skip)
- signature 検出は出力の先頭 50 行のみを対象とし、大量出力でのパフォーマンス劣化を防ぐ

---

## §5. V-model trace

- ① 設計: `docs/plans/PLAN-212-codex-fallback-chain.md` (本 file)
- ② 実装: `cli/lib/codex_fallback_detector.py` / `cli/helix-codex` → docstring に「設計: PLAN-212」
- ③ テスト設計: Sprint .3 entry で §2 Sprint .3 を正本とする
- ④ テストコード: `cli/lib/tests/test_codex_fallback_detector.py` → docstring に「DoD 検証: PLAN-212 §3」

---

## §6. リスク

| リスク | 緩和策 |
|---|---|
| false positive | 先頭 50 行制限 + 文脈正規表現。`--no-fallback` で無効化可 |
| signature 網羅性不足 | SF-001〜SF-005 は主要パターン。新 signature は実運用で追記 |
| DB migration 失敗 | fail-open。記録不可なら WARN のみで fallback 提示は続行 |
| PLAN-137 との二重適用 | PLAN-137 = 事前 classify、本 PLAN = 事後 fallback。役割分離で競合なし |

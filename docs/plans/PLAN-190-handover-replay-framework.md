---
plan_id: PLAN-190
title: "handover replay framework (過去 session の再現・post-mortem 用途)"
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — archive ロジック実装 (cli/lib/handover.py + cli/helix-handover) + pytest 起草"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 handover 状態管理精読・replay dry-run 設計レビュー・HELIX_CORE.md 整合確認"
generates:
  - artifact_type: python_module
    path: cli/lib/handover.py
  - artifact_type: script
    path: cli/helix-handover
  - artifact_type: test
    path: cli/lib/tests/test_handover_replay.py
dependencies:
  requires:
    - PLAN-128
  blocks: []
  parent: PLAN-MM-001
related_adr: []
related_docs:
  - cli/lib/handover.py
  - cli/helix-handover
  - helix/HELIX_CORE.md
  - CLAUDE.md §BE 実装時の Handover ファイル維持
acceptance_criteria:
  - "helix handover が clear 実行時に .helix/handover/history/<timestamp>.json へ自動 archive する"
  - "helix handover replay --list が archive 一覧を降順で表示する"
  - "helix handover replay <timestamp> --dry-run が archive を読み込み state を標準出力に表示する (副作用なし)"
  - "helix handover replay <timestamp> が .helix/handover/CURRENT.json を archive から復元する (default = dry-run)"
  - "ESCALATION.md が archive 時点に存在した場合、.helix/handover/history/<timestamp>-escalation.json として同時 archive される"
  - "python3 -m py_compile cli/lib/handover.py PASS"
  - "pytest cli/lib/tests/test_handover_replay.py -q 全 PASS (7 scenario)"
  - "bash -n cli/helix-handover PASS"
---

# PLAN-190: handover replay framework (過去 session の再現・post-mortem 用途)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 handover 機構への archive / replay 機能追加** であり、
新規の大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:
- handover の状態管理は HELIX_CORE.md §状態管理の二層構造で凍結済
- archive は JSON ファイルのコピーという既存 HELIX 内パターンの延長
- dry-run default は HELIX の「副作用を抑制する read-only 優先」原則の適用
- 外部ライブラリ新規導入なし (Python stdlib shutil / json のみ)

## 背景

`helix handover clear` は `CURRENT.json` を削除して状態を失う。
post-mortem 分析・debug 再現・session audit で過去 state を参照したいユースケースがあるが、
現状 `.helix/handover/` は過去 state の保持機構を持たない。
`history/` への自動 archive と `helix handover replay` コマンドで解消する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は HELIX 内部 CLI の archive / replay 機能追加。外部ライブラリ新規依存なし。WebSearch **skip**。
JSON copy/restore は Python stdlib (shutil.copy2 / json) で完結。dry-run default は既存 `helix plan draft --dry-run` と同一パターン。

## 設計方針

### 1. archive ディレクトリ構造

```
.helix/handover/
  CURRENT.json                         # 現在の handover state
  history/
    20260523T120000Z.json              # archive (CURRENT.json のスナップショット)
    20260523T120000Z-escalation.json   # archive 時点の ESCALATION.md (存在した場合)
    20260521T090000Z.json
    ...
```

timestamp フォーマット: `%Y%m%dT%H%M%SZ` (UTC、ファイル名として安全な文字のみ)

### 2. 自動 archive トリガー

`helix handover clear` 実行時に CURRENT.json を `history/<timestamp>.json` へコピーしてから削除する。
ESCALATION.md が存在する場合は `history/<timestamp>-escalation.json` に同時コピーする。

```python
def archive_current(handover_dir: Path) -> Path | None:
    """Copy CURRENT.json to history/ before clear. Returns archive path or None."""
    current = handover_dir / "CURRENT.json"
    if not current.exists():
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    history_dir = handover_dir / "history"
    history_dir.mkdir(exist_ok=True)
    archive_path = history_dir / f"{ts}.json"
    shutil.copy2(current, archive_path)
    escalation = handover_dir / "ESCALATION.md"
    if escalation.exists():
        shutil.copy2(escalation, history_dir / f"{ts}-escalation.json")
    return archive_path
```

### 3. helix handover replay サブコマンド

| コマンド | 動作 |
|---|---|
| `helix handover replay --list` | history/ 一覧を降順で表示 (timestamp / task_id / status) |
| `helix handover replay <timestamp>` | dry-run: archive の state を標準出力に表示 (副作用なし) |
| `helix handover replay <timestamp> --restore` | CURRENT.json を archive から復元 (既存 CURRENT があれば abort) |
| `helix handover replay <timestamp> --restore --force` | 既存 CURRENT を上書きして復元 |

**dry-run default**: `--restore` を明示しない限り副作用は発生しない。
HELIX の「承認なし状態変更禁止」原則を遵守する。

### 4. replay --list 出力フォーマット

```
timestamp              task_id          status        owner
20260523T120000Z       PHASE4-CARRY-2B  completed     opus
20260521T090000Z       PLAN-100-REG...  escalated     codex
```

escalation archive が存在する場合は `[ESCALATION]` マーカーを付与する。

### 5. archive 保持上限

デフォルト 30 件保持。超過分は古い順に自動削除。
`HELIX_HANDOVER_HISTORY_MAX` 環境変数でオーバーライド可能。

## 実装計画

### Sprint .1: archive ロジック実装 (se 委譲)

Entry 条件: `cli/lib/handover.py` の `clear()` 実装と `CURRENT.json` 生成フローを Read して確認

1. `archive_current(handover_dir)` を `cli/lib/handover.py` に追加
2. `clear()` 先頭で `archive_current()` を呼ぶよう修正
3. `history/` ディレクトリ自動作成 + ESCALATION.md 同時 archive
4. 保持上限 30 件ローテーション (`_rotate_history(history_dir, max_count=30)`)
5. `python3 -m py_compile cli/lib/handover.py` PASS

### Sprint .2: replay サブコマンド実装 (se 委譲)

1. `cli/helix-handover` に `replay` サブコマンド追加
2. `replay --list`: `history/` JSON を走査して降順一覧を出力
3. `replay <timestamp>`: archive を pretty-print (dry-run default、副作用なし)
4. `replay <timestamp> --restore [--force]`: CURRENT.json 復元
5. `bash -n cli/helix-handover` PASS

### Sprint .3: pytest + 動作実証 (se 委譲)

`cli/lib/tests/test_handover_replay.py` 新規作成 (7 scenario):
- archive_created_on_clear / escalation_archived / no_archive_when_absent
- replay_list_descending / dry_run_no_side_effect / restore_overwrites / rotation_max_30

`pytest cli/lib/tests/test_handover_replay.py -q` 全 PASS

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/handover.py` PASS
- [ ] `bash -n cli/helix-handover` PASS
- [ ] pytest 全 7 scenario PASS
- [ ] `helix handover clear` 後に `history/<timestamp>.json` が生成されること
- [ ] 既存 `helix handover clear` / `resume` / `status` の動作が regression しないこと
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)

## DoD (Definition of Done)

- [ ] `helix handover clear` が `history/<timestamp>.json` に archive し、ESCALATION.md も同時 archive される
- [ ] `helix handover replay --list` が archive 一覧を降順で表示する
- [ ] `helix handover replay <timestamp>` (dry-run) が副作用なく state を表示する
- [ ] `helix handover replay <timestamp> --restore` が CURRENT.json を復元する
- [ ] history は最大 30 件でローテーションされる
- [ ] pytest 7 scenario 全 PASS / `python3 -m py_compile` + `bash -n` 全 PASS
- [ ] 既存 handover コマンド (clear / resume / status / update / dump) が regression しない

## V-model 4 artifact trace

| Artifact | ファイル |
|---|---|
| ① 設計 (本 PLAN) | docs/plans/PLAN-190-handover-replay-framework.md |
| ② 実装コード | cli/lib/handover.py / cli/helix-handover |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-190-replay-test-design.md (予定) |
| ④ テストコード | cli/lib/tests/test_handover_replay.py |

双方向 reference: 実装コード docstring に「設計: PLAN-190」/ テストコード docstring に「DoD 検証: PLAN-190 §DoD」を追記。

## リスク

| リスク | 緩和策 |
|---|---|
| `clear` が archive により遅延 | `shutil.copy2` は数 KB コピーのみ。<10ms で影響なし |
| `--restore` で既存 CURRENT を誤上書き | dry-run default。上書きは `--restore --force` の二段承認を必須化 |
| history/ がディスク圧迫 | 30 件ローテーション。`HELIX_HANDOVER_HISTORY_MAX` でオーバーライド可能 |
| PLAN-128 依存関係 | PLAN-128 先行確定後に Sprint .1 着手。新フィールドも archive 対象として後方互換テストで確認 |

## 関連 reference

- PLAN-128 (依存元: handover schema 強化)
- HELIX_CORE.md §状態管理の二層構造 / CLAUDE.md §Handover 維持 / cli/lib/handover.py

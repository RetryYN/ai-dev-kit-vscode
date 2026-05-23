---
plan_id: PLAN-157
title: "helix skill catalog incremental update (full rebuild 回避)"
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
kind: refactor
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — incremental update ロジック実装 (cli/lib/skill_catalog.py + cli/helix-skill) + bats/pytest 起草"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 rebuild ロジック精読・設計整合レビュー・SKILL_MAP.md との drift 確認"
generates:
  - artifact_type: python_module
    path: cli/lib/skill_catalog.py
  - artifact_type: script
    path: cli/helix-skill
  - artifact_type: test
    path: cli/lib/tests/test_skill_catalog_incremental.py
dependencies:
  requires:
    - PLAN-109
  blocks: []
  parent: PLAN-MM-001
related_adr: []
related_docs:
  - cli/lib/skill_catalog.py
  - cli/helix-skill
  - SKILL_MAP.md §自動推挙システム
acceptance_criteria:
  - "helix skill catalog rebuild --incremental が変更 SKILL.md のみを re-parse し、非変更 entry は cache を維持する"
  - "1 SKILL.md 変更時のターンアラウンドが 0.5 秒以下 (full rebuild 5-10 秒比)"
  - "helix skill catalog rebuild --force-full が従来と同一の full rebuild を実行する"
  - "default (flag なし) が --incremental と同等に動作する"
  - "cache 破損・不在時は自動 full rebuild へ fallback する"
  - "python3 -m py_compile cli/lib/skill_catalog.py PASS"
  - "pytest cli/lib/tests/test_skill_catalog_incremental.py -q 全 PASS (6 scenario)"
  - "bash -n cli/helix-skill PASS"
---

# PLAN-157: helix skill catalog incremental update (full rebuild 回避)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 skill catalog framework の性能改善** であり、
新規の大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:
- skill catalog 機構は SKILL_MAP.md §自動推挙システムで凍結済
- incremental update は mtime 比較 + 部分 cache merge という既存 HELIX 内パターンの延長
- 外部ライブラリ新規導入なし (Python stdlib pathlib.Path.stat() のみ)

## 背景

`helix skill catalog rebuild` は全 SKILL.md (111 件) + references (230 件) を full re-parse する。
1 skill を変更した場合も full rebuild が走り、5-10 秒のレイテンシが発生する。

PLAN-109 (PostToolUse hook) との組み合わせで SKILL.md Edit 毎に自動 rebuild が発火するため、
full rebuild コストが体感遅延として顕在化する。

incremental update (変更 file のみ re-parse + cache merge) により 0.5 秒以下を実現し、
連続 skill 統合作業・自動 rebuild 双方でのレスポンスを改善する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **HELIX 内部 CLI の性能改善** であり、外部ライブラリ / 業界 standard への
新規依存なし。WebSearch **skip**。

skip 理由:
- mtime 比較による incremental update は Python stdlib + POSIX 標準の範囲内
- 参照実装: `helix code build` (cli/lib/skill_catalog.py 内の既存 catalog 生成 loop) を応用
- 外部 OSS (watchdog 等) は非採用。PLAN-109 の bg 実行モデルで十分

## 設計方針

### 1. mtime diff 検出

cache JSON (`skill-catalog.json`) に各 entry の `source_mtime` を記録し、
rebuild 時に実 file の mtime と比較する。

```python
def _is_stale(entry: dict, file_path: Path) -> bool:
    cached_mtime = entry.get("source_mtime", 0.0)
    try:
        return file_path.stat().st_mtime > cached_mtime
    except FileNotFoundError:
        return True
```

### 2. incremental update フロー

```
load_cache() →
  for each SKILL.md in skills/:
    if cache[skill_id] exists AND not _is_stale(...):
      keep existing entry       # re-parse skip
    else:
      entry = parse_skill_md()  # re-parse + update source_mtime
  save_cache()
```

1 file 変更時のコストは `N_total × stat() + 1 × parse()` に抑えられる。

### 3. CLI flag 設計

```bash
helix skill catalog rebuild              # default = incremental
helix skill catalog rebuild --force-full # full rebuild (cache 無視)
```

`skill_catalog.py` の `rebuild(incremental: bool = True)` に引数追加。

### 4. cache 破損・不在 fallback

cache JSON 読み込み失敗 / `source_mtime` key 不在時は full rebuild へ自動 fallback し、
`[WARN] catalog cache corrupt, falling back to full rebuild` を STDERR に出力する。

### 5. 後方互換

既存 cache に `source_mtime` が存在しない場合は初回のみ full rebuild、2 回目以降から incremental が有効化。

## 実装計画

### Sprint .1: skill_catalog.py 改修 (se 委譲、size M)

Entry 条件: `cli/lib/skill_catalog.py` を Read して既存 rebuild() 実装を確認

実施内容:
1. `rebuild(incremental: bool = True)` 関数に分岐追加
2. `_is_stale(entry, file_path)` helper 追加
3. catalog entry に `source_mtime` field を追加
4. cache 破損時の full rebuild fallback (WARN to STDERR)
5. `python3 -m py_compile cli/lib/skill_catalog.py` PASS (mandatory in sprint)

完了条件: `rebuild(incremental=False)` が既存 full rebuild と同一出力を返すこと

### Sprint .2: helix-skill CLI flag 追加 (se 委譲、size S)

実施内容:
1. `cli/helix-skill` の `catalog rebuild` 節に `--force-full` flag 追加
2. flag なし / `--incremental` 指定時に `incremental=True` で呼び出し
3. `bash -n cli/helix-skill` PASS (mandatory in sprint)

### Sprint .3: pytest + 動作実証 (se 委譲、size S)

実施内容:
1. `cli/lib/tests/test_skill_catalog_incremental.py` 新規作成 (6 scenario):
   - `test_incremental_skips_unchanged` / `test_incremental_reparses_changed`
   - `test_force_full_reparses_all`
   - `test_fallback_on_missing_cache` / `test_fallback_on_corrupt_cache`
   - `test_source_mtime_written`
2. `pytest cli/lib/tests/test_skill_catalog_incremental.py -q` 全 PASS
3. 手動計測: 1 SKILL.md 変更で 0.5 秒以内に完了すること確認

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/skill_catalog.py` PASS
- [ ] `bash -n cli/helix-skill` PASS
- [ ] pytest 全 6 scenario PASS
- [ ] `helix skill catalog rebuild` (incremental) の動作確認
- [ ] `helix skill catalog rebuild --force-full` (full rebuild) の regression なし確認
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)

## DoD (Definition of Done)

- [ ] `cli/lib/skill_catalog.py` に `_is_stale()` + `incremental` 分岐実装済
- [ ] catalog entry に `source_mtime` field が記録される
- [ ] cache 破損時に WARN + full rebuild fallback が動作する
- [ ] `cli/helix-skill` に `--incremental` / `--force-full` flag 追加済
- [ ] default (flag なし) が incremental と同等に動作する
- [ ] pytest 6 scenario 全 PASS
- [ ] `python3 -m py_compile` + `bash -n` 全 PASS
- [ ] full rebuild (`--force-full`) の出力が既存実装と等価 (regression なし)
- [ ] helix doctor pass 数が現行以上

## リスク

| リスク | 緩和策 |
|---|---|
| stat() の clock 精度が低く mtime 一致でも内容変更を見逃す | mtime は 1 秒精度 (FAT32 は 2 秒)。HFS+ / ext4 では ns 精度で問題なし。将来的に hash fallback を検討 (P3 carry) |
| 大量 skill 削除時に stale entry が cache に残る | rebuild 時に `skills/` を walk して存在しない skill_id を cache から除去するクリーンアップ追加 |
| PLAN-109 debounce と incremental の組み合わせ | debounce は rebuild 呼び出し頻度を制御、incremental は rebuild 内部コスト削減。直交するため干渉なし |
| 既存 skill-catalog.json に source_mtime 不在 | fallback ロジックで初回のみ full rebuild、2 回目以降から incremental が有効化 (§設計方針 5 参照) |

## 関連 reference

- PLAN-109 (PostToolUse hook で rebuild 自動化、本 PLAN の依存元)
- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は skip 適用)
- [[feedback_adr_before_plan_violation]] (ADR snapshot 要否判定、本 PLAN は不要と確認)
- SKILL_MAP.md §自動推挙システム (skill catalog の仕組みと rebuild 手順)
- cli/lib/skill_catalog.py (catalog 生成実装の正本)
- cli/helix-skill (rebuild コマンドの dispatch)

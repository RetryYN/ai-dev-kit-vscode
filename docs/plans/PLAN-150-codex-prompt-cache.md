---
plan_id: PLAN-150
title: "PLAN-150: helix-codex prompt cache framework (cache TTL + invalidation)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-130-codex-prompt-template-library.md   # from dependencies.parent
size: M
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: se
    slot_label: "SE — cache framework 実装 (cli/lib/codex_prompt_cache.py + cli/helix-codex 拡張)"
  - role: qa
    slot_label: "QA — cache hit/miss/invalidation シナリオテスト設計・実装"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-130 との設計整合確認・mtime 検出ロジックレビュー・G4 review"
generates:
  - artifact_path: cli/lib/codex_prompt_cache.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_codex_prompt_cache.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-150-codex-prompt-cache.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-053-codex-prompt-cache-design.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-130
  requires:
    - PLAN-130
  blocks: []
related_plans:
  - PLAN-130-codex-prompt-template-library
  - PLAN-091-v5-framework-core
related_adr:
  - ADR-053-codex-prompt-cache-design
related_docs:
  - cli/helix-codex
  - cli/lib/skill_recommender.py
  - docs/commands/ai-harness.md
---

# PLAN-150: helix-codex prompt cache framework (cache TTL + invalidation)

> **kind**: impl (prompt cache 新規実装)
> **layer**: L4
> **drive**: be (bash + Python 実装中心)
> **L2 凍結**: ADR-053 (cache key 設計 + invalidation 方針 snapshot)

---

## §0. 本 PLAN の位置付け

`helix codex` は呼び出しごとに role conf / task description / allowed_files を結合して
prompt を生成し、Codex API に送信する。同 role × 同 task description で 1 時間以内の
再呼び出しがある場合、prompt 生成と API call を cache 経由でスキップできる。

本 PLAN は PLAN-130 (Codex prompt template library) を parent とし、
**cache key 設計 + TTL + allowed_files mtime 変動による自動 invalidation** の
cache framework を実装する。

---

## §1. 目的

1. `helix codex` の同一入力再呼び出し時に cache hit させ、Codex API call コストと
   レイテンシを削減する
2. cache key を `SHA256(role + task_description + allowed_files)` で構成し、
   入力が異なれば必ず別 cache エントリになるようにする
3. `--no-cache` flag で cache を強制 bypass する経路を提供する
4. allowed_files に含まれるファイルの mtime 変更を検出し、stale cache を自動 invalidate する

---

## §2. 背景

### 2.1 現状の課題

`helix codex` は毎回以下の処理を実行している:

1. role conf (`cli/roles/<role>.conf`) の読み込み
2. prompt template の組み立て (`cli/templates/prompts/`)
3. allowed_files の内容埋め込み
4. Codex API への送信と応答待ち

工程中に `helix codex --role pmo-sonnet --task "PLAN 整合確認"` のように同一入力で
複数回呼ばれるケース (Sprint Plan 標準構造 §Step 6、G4 review など) では、
毎回 API call が発生し コストと時間が無駄になる。

`helix skill chain` は PLAN-121 で 24h 二段 cache が実装済みであり、同様の仕組みを
`helix codex` にも導入するのが自然な拡張である。

### 2.2 Anthropic prompt cache との区別

Anthropic の server-side prompt cache (5 分 TTL、キャッシュトークン割引) とは別物。
本 PLAN は **client-side prompt response cache** であり、同一入力に対する response JSON
全体を `.helix/cache/codex-prompts/` に保存・再利用する。

### 2.3 WebSearch skip 理由 (PLAN-087 ガードレール遵守)

本 PLAN は HELIX 内部の bash/Python cache 実装であり、外部ライブラリの新規採用なし。
`hashlib.sha256` (Python 標準) + `os.stat().st_mtime` (POSIX 標準) のみ使用。
WebSearch **skip**。

---

## §3. 設計方針 (L2 凍結 → ADR-053)

### 3.1 cache key 設計

```python
import hashlib, json, os

def build_cache_key(
    role: str,
    task_description: str,
    allowed_files: list[str],
) -> str:
    """cache key = SHA256(role + task_description + sorted allowed_files)"""
    payload = json.dumps(
        {"role": role, "task": task_description, "files": sorted(allowed_files)},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

**設計選択の根拠 (ADR-053 で凍結)**:
- `sorted(allowed_files)` で順序を正規化し、渡し順の違いを無視する
- `ensure_ascii=False` でタスク記述の日本語を正確にハッシュする
- key の truncation なし (collision リスク回避のため full 64 hex chars)

### 3.2 cache ファイル構造

```
.helix/cache/codex-prompts/
  <sha256_key>.json
```

cache エントリの JSON 構造:

```json
{
  "cache_key": "<sha256>",
  "role": "se",
  "task_description": "...",
  "allowed_files": ["path/to/file.py"],
  "file_mtimes": {"path/to/file.py": 1716441600.0},
  "completion_time": "2026-05-23T10:00:00Z",
  "ttl_seconds": 3600,
  "response": { ... }
}
```

`file_mtimes` は invalidation 判定に使用する。

### 3.3 TTL + invalidation ルール

| 条件 | 動作 |
|---|---|
| `completion_time` から `ttl_seconds` 以内 + mtime 変化なし | cache hit: response を返す |
| TTL 超過 | cache miss: API call + cache 更新 |
| allowed_files のいずれかの mtime が `file_mtimes` と異なる | cache miss: stale invalidate + API call |
| `--no-cache` flag | cache 完全 bypass: 常に API call |

default TTL: **3600 秒 (1 時間)**。`--cache-ttl <秒>` でオーバーライド可能。

### 3.4 cli/helix-codex への統合

```bash
# cache check (Python helper 呼び出し)
_cache_key=$(python3 -c "
from cli.lib.codex_prompt_cache import build_cache_key, check_cache
key = build_cache_key('$role', '''$task''', $(echo "$allowed_files" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().split()))'))
result = check_cache(key)
if result:
    print('HIT:' + key)
else:
    print('MISS:' + key)
")

if [[ "$_cache_key" == HIT:* ]]; then
    # cache から response を出力して終了
    python3 -c "from cli.lib.codex_prompt_cache import get_cached_response; ..."
    exit 0
fi
# ... 通常の Codex API call ...
# API call 完了後に cache 保存
python3 -c "from cli.lib.codex_prompt_cache import save_cache; ..."
```

---

## §4. DoD (Definition of Done)

- [ ] `cli/lib/codex_prompt_cache.py` が `build_cache_key` / `check_cache` /
  `get_cached_response` / `save_cache` / `invalidate_cache` を実装している
- [ ] `cli/helix-codex` が cache check → hit 時 return / miss 時 API call → save の
  フローで動作する
- [ ] `--no-cache` flag で cache を完全 bypass できる
- [ ] allowed_files の mtime 変更を検出して stale cache を invalidate できる
- [ ] `--cache-ttl <秒>` で TTL をオーバーライドできる
- [ ] ADR-053 を L2 大局判断 snapshot として起票
- [ ] `cli/lib/tests/test_codex_prompt_cache.py` で T1〜T6 全件 PASS
- [ ] `python3 -m py_compile cli/lib/codex_prompt_cache.py` PASS
- [ ] `python3 -m pytest cli/lib/tests/test_codex_prompt_cache.py -v` 全件 PASS
- [ ] `helix doctor` warn 増加なし

---

## §5. 実装計画

### Sprint .1 — codex_prompt_cache.py 実装

**担当**: SE

**作業**:
1. `cli/lib/codex_prompt_cache.py` 新規作成:
   - `build_cache_key(role, task_description, allowed_files) -> str`
   - `check_cache(key) -> bool` (TTL + mtime 検証)
   - `get_cached_response(key) -> dict`
   - `save_cache(key, role, task, files, response) -> None`
   - `invalidate_cache(key) -> None`
   - `CACHE_DIR = Path(".helix/cache/codex-prompts")`
2. `py_compile` PASS 確認

**受入条件**:
- 全 5 関数が定義されている
- `check_cache` が TTL 超過時に False を返す
- `check_cache` が mtime 変更時に False を返し stale file を削除する
- `py_compile` PASS

### Sprint .2 — cli/helix-codex 統合

**担当**: SE

**作業**:
1. `cli/helix-codex` に cache check フローを追加:
   - `--no-cache` flag のパース
   - `--cache-ttl <秒>` flag のパース (default=3600)
   - cache hit 時は response を stdout 出力して早期 exit
   - API call 完了後に `save_cache` 呼び出し
2. cache 統計ログ: `HELIX_CACHE_DEBUG=1` 設定時に hit/miss/invalidate を stderr 出力
3. `bash -n cli/helix-codex` PASS 確認

**受入条件**:
- `helix codex --role se --task "test" --no-cache` で cache を bypass する
- 同一入力の 2 回目呼び出しで cache hit する (手動確認)
- `.helix/cache/codex-prompts/` に JSON ファイルが生成される

### Sprint .3 — テスト実装

**担当**: QA

**テストシナリオ**:

| ID | テスト内容 | 期待値 |
|---|---|---|
| T1 | TTL 内で同一 key の check_cache | True (hit) |
| T2 | TTL 超過後の check_cache | False (miss) |
| T3 | allowed_files の mtime 変更後の check_cache | False (stale invalidate) |
| T4 | allowed_files なし (空 list) の build_cache_key | 決定論的 key が返る |
| T5 | --no-cache フロー (cache 存在しても bypass) | API call が実行される |
| T6 | 並列呼び出し時の cache ファイル競合 (atomic write) | データ破損なし |

**受入条件**:
- `pytest cli/lib/tests/test_codex_prompt_cache.py -v` T1〜T6 全件 PASS

---

## §6. リスクと緩和策

| リスク | 影響 | 緩和策 |
|---|---|---|
| cache の stale response が誤った結果を返す | Codex 委譲の品質低下 | `--no-cache` flag を常に使える経路を確保。task description に timestamp を含む呼び出しは cache 無効化が自然に発生 |
| allowed_files が大量 (100 件以上) の場合の mtime チェックコスト | helix-codex 起動遅延 | Sprint .1 で mtime check を batch で実行 (os.stat × 100 は 数ms で許容範囲) |
| `.helix/cache/codex-prompts/` が肥大化 | disk 圧迫 | TTL 超過 entry は check_cache 時に削除 + `helix cache clear --codex-prompts` cleanup コマンド追加 (Sprint .2 optional) |
| parallel 書き込みによる JSON 破損 | cache 読み取りエラー | atomic write (tmp file → rename) で T6 を担保 |

---

## §7. 完了記録 (実装後記入)

- completion_commits: (TBD)
- 実際の Sprint 所要: (TBD)
- 残 carry / debt: (TBD)

---
plan_id: PLAN-164
title: skill recommender LLM prompt result cache (gpt-5.4-mini client-side 24h TTL)
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-121-skill-recommender-improvement.md   # from dependencies.parent
kind: impl
drive: be
layer: L4
size: S
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — Sprint .1-.2 skill_recommender_cache.py 実装 + skill_recommender.py 統合"
  - role: qa
    slot_label: "QA — Sprint .3 cache hit/miss/invalidation テスト設計・実装"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-121 設計整合確認・cache key 設計レビュー・G4 review"
generates:
  - artifact_type: python_module
    path: cli/lib/skill_recommender_cache.py
  - artifact_type: test
    path: cli/lib/tests/test_skill_recommender_cache.py
  - artifact_type: doc_update
    path: cli/lib/skill_recommender.py
dependencies:
  parent: PLAN-121
  requires:
    - PLAN-121
  blocks: []
related_adr: []
related_docs:
  - docs/plans/PLAN-121-skill-recommender-improvement.md
  - cli/lib/skill_recommender.py
  - cli/helix-skill
  - docs/commands/ai-harness.md
acceptance_criteria:
  - "cache key = SHA256(task_description + skill_catalog_hash) で決定論的 key が生成される"
  - "同一入力の 2 回目呼び出しで cache hit し gpt-5.4-mini API call が発生しない"
  - "skill catalog が更新 (catalog hash 変化) された場合に cache が invalidate される"
  - "TTL 24h 超過後に cache miss となり API call が再実行される"
  - "python3 -m py_compile cli/lib/skill_recommender_cache.py PASS"
  - "pytest cli/lib/tests/test_skill_recommender_cache.py -v 全件 PASS"
  - "既存 helix skill chain の動作が変化しない (回帰なし)"
---

# PLAN-164: skill recommender LLM prompt result cache (gpt-5.4-mini client-side 24h TTL)

## L2 凍結 (ADR snapshot)

本 PLAN は HELIX 内部の Python cache 実装であり、外部ライブラリ新規採用なし。
`hashlib.sha256` (Python 標準) + `time.time()` (POSIX 標準) のみ使用する。
新規 L2 大局判断なし → **ADR snapshot 不要**。

## 背景

### 現状の課題

`helix skill chain` は `cli/lib/skill_recommender.py` を経由して gpt-5.4-mini に
推奨スキルを問い合わせる。PLAN-121 では 1 時間 TTL の cache 実装が提案されたが、
以下の問題が未解決のまま残っている:

1. **cache key に skill catalog hash が含まれていない**: catalog が更新されても
   古い推奨結果が返り続ける stale cache のリスクがある
2. **TTL が 1 時間**: スプリント間でスキル推奨が変わらない場合でも毎時 API call が発生し、
   コストが最適でない
3. **cache 実装の所在が不明確**: skill_recommender.py 内に埋め込まれているか、
   独立モジュールになっているか、PLAN-121 時点で明確化されていない

本 PLAN は PLAN-121 の子 PLAN として、**skill catalog hash を cache key に組み込んだ 24h TTL**
の client-side cache を独立モジュール `cli/lib/skill_recommender_cache.py` として実装する。

### Anthropic prompt cache との区別

Anthropic の server-side prompt cache (5 分 TTL、キャッシュトークン割引) とは別物。
本 PLAN は **gpt-5.4-mini (Codex 側) の API response を client-side に保存する** 実装であり、
Anthropic API とは独立している。

### WebSearch skip 理由 (PLAN-087 ガードレール遵守)

本 PLAN は HELIX 内部の Python 標準ライブラリのみを使用する cache 実装。
新規外部ライブラリ採用なし、新規 framework 採用なし。WebSearch **skip**。
PLAN-150 (helix-codex prompt cache) が同様の設計パターンで WebSearch skip の前例を持つ
(PLAN-150 §2.3 参照)。

## 設計方針

### cache key 設計

```python
import hashlib, json

def build_cache_key(task_description: str, catalog_hash: str) -> str:
    """
    cache key = SHA256(task_description + skill_catalog_hash)
    catalog_hash: .helix/cache/skill-catalog.json の SHA256 (呼び出し元で計算)
    """
    payload = json.dumps(
        {"task": task_description, "catalog": catalog_hash},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

**設計選択の根拠**:

- `task_description` が異なれば必ず別 key: 誤 hit を防ぐ
- `catalog_hash` が変わればすべての cache が自動 invalidate: stale 防止
- `ensure_ascii=False` で日本語タスク記述を正確にハッシュ
- key truncation なし (full 64 hex chars、collision 回避)

### skill catalog hash の計算

```python
import hashlib
from pathlib import Path

def compute_catalog_hash(catalog_path: Path) -> str:
    """skill-catalog.json のファイル内容の SHA256 を返す"""
    content = catalog_path.read_bytes()
    return hashlib.sha256(content).hexdigest()
```

`catalog_path` = `.helix/cache/skill-catalog.json`。
catalog が `helix skill catalog rebuild` で再生成されると hash が変わり、
既存 cache が自動 invalidate される。

### cache ファイル構造

```
.helix/cache/skill-recommendations/
  <sha256_key>.json
```

既存の `.helix/cache/recommendations/` との関係:
PLAN-121 以前に `.helix/cache/recommendations/` が使われていた場合、
本 PLAN の実装後は `.helix/cache/skill-recommendations/` を正本とする。
旧 directory は `helix cache clear --skill-recommendations` で削除候補。

cache エントリの JSON 構造:

```json
{
  "cache_key": "<sha256>",
  "task_description": "...",
  "catalog_hash": "<sha256>",
  "created_at": 1716441600.0,
  "ttl_seconds": 86400,
  "recommendations": [ ... ]
}
```

### TTL + invalidation ルール

| 条件 | 動作 |
|---|---|
| `created_at` から `ttl_seconds` (86400s = 24h) 以内 + catalog hash 一致 | cache hit: recommendations を返す |
| TTL 超過 | cache miss: API call + cache 更新 |
| catalog hash が cache entry と異なる | cache miss: stale invalidate + API call |
| `HELIX_SKILL_NO_CACHE=1` 環境変数 | cache 完全 bypass |

default TTL: **86400 秒 (24 時間)**。`HELIX_SKILL_CACHE_TTL` 環境変数でオーバーライド可。

### skill_recommender.py への統合

```python
# cli/lib/skill_recommender.py の recommend() メソッド冒頭に挿入

from cli.lib.skill_recommender_cache import (
    build_cache_key, compute_catalog_hash,
    check_cache, get_cached_recommendations, save_cache,
)

catalog_hash = compute_catalog_hash(CATALOG_PATH)
cache_key = build_cache_key(task_description, catalog_hash)

if not os.getenv("HELIX_SKILL_NO_CACHE"):
    cached = get_cached_recommendations(cache_key)
    if cached is not None:
        return cached

# ... 既存の gpt-5.4-mini API call ...

save_cache(cache_key, task_description, catalog_hash, result)
return result
```

既存の 1 時間 TTL cache が skill_recommender.py 内に存在する場合、本実装で置き換える。

## 実装計画

### Sprint .1: skill_recommender_cache.py 実装

**担当**: SE

**作業**:

1. `cli/lib/skill_recommender_cache.py` 新規作成:
   - `build_cache_key(task_description, catalog_hash) -> str`
   - `compute_catalog_hash(catalog_path) -> str`
   - `check_cache(key) -> bool` (TTL + catalog hash 検証)
   - `get_cached_recommendations(key) -> list | None`
   - `save_cache(key, task, catalog_hash, recommendations) -> None`
   - `CACHE_DIR = Path(".helix/cache/skill-recommendations")`
   - `DEFAULT_TTL = 86400`
2. `python3 -m py_compile cli/lib/skill_recommender_cache.py` PASS

**受入条件**:

- 全 5 関数が定義されている
- `check_cache` が TTL 超過時に False を返す
- `check_cache` が catalog hash 不一致時に False を返し stale entry を削除する
- `python3 -m py_compile` PASS

### Sprint .2: skill_recommender.py 統合

**担当**: SE

**作業**:

1. `cli/lib/skill_recommender.py` を Read して既存 cache 実装の有無を確認
2. `recommend()` (または相当メソッド) の冒頭に cache check フローを挿入:
   - `HELIX_SKILL_NO_CACHE=1` 時は bypass
   - hit 時は早期 return
   - miss 時は API call 後に `save_cache` 呼び出し
3. 既存の 1 時間 TTL cache があれば本実装に置き換え
4. `python3 -m py_compile cli/lib/skill_recommender.py` PASS
5. `helix skill chain "テスト"` が動作することを手動確認

**受入条件**:

- 同一タスクの 2 回目呼び出しで `.helix/cache/skill-recommendations/` に JSON が生成される
- `HELIX_SKILL_NO_CACHE=1 helix skill chain "..."` が API call を実行する

### Sprint .3: テスト実装

**担当**: QA

**テストシナリオ**:

| ID | テスト内容 | 期待値 |
|---|---|---|
| T1 | TTL 24h 以内・catalog hash 一致の check_cache | True (hit) |
| T2 | TTL 超過後の check_cache | False (miss)、stale entry 削除 |
| T3 | catalog hash 不一致の check_cache | False (miss)、stale entry 削除 |
| T4 | HELIX_SKILL_NO_CACHE=1 で bypass | API call が実行される |
| T5 | catalog_path 不在時の compute_catalog_hash | FileNotFoundError または空 hash |
| T6 | build_cache_key の決定論的性質 | 同一入力 → 同一 key |
| T7 | 既存 skill_recommender 回帰 (cache あり) | 推奨結果が変化しない |

**受入条件**:

- `pytest cli/lib/tests/test_skill_recommender_cache.py -v` T1〜T7 全件 PASS
- `pytest cli/lib/tests/test_skill_recommender.py -v` (既存テストがある場合) 回帰なし

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/skill_recommender_cache.py` PASS
- [ ] `python3 -m py_compile cli/lib/skill_recommender.py` PASS
- [ ] `pytest cli/lib/tests/test_skill_recommender_cache.py -v` 全件 PASS
- [ ] 既存 skill_recommender テスト回帰なし
- [ ] セルフレビュー (SE)
- [ ] pmo-sonnet review (Sprint .3 完了時)
- [ ] commit message に `PLAN-164 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `cli/lib/skill_recommender_cache.py` が 5 関数を実装している
- [ ] `cli/lib/skill_recommender.py` が cache check フローを持つ
- [ ] TTL 24h + catalog hash 変更時の invalidation が動作する
- [ ] `HELIX_SKILL_NO_CACHE=1` で cache bypass できる
- [ ] `pytest cli/lib/tests/test_skill_recommender_cache.py -v` T1〜T7 全件 PASS
- [ ] 既存 helix skill chain の動作回帰なし
- [ ] `helix doctor` warn 増加なし

## リスクと緩和策

| リスク | 影響 | 緩和策 |
|---|---|---|
| stale cache が古い推奨スキルを返す | 委譲先ミスで工数増 | catalog hash を key に含めることで catalog 更新時に自動 invalidate |
| skill_recommender.py の既存 cache との二重化 | hit 率低下・disk 増加 | Sprint .2 着手前に既存 cache 実装を Read して一本化判定を Opus に返す |
| `.helix/cache/skill-recommendations/` の肥大化 | disk 圧迫 | TTL 超過 entry は check_cache 時に削除。`helix cache clear --skill-recommendations` cleanup 追加 (Sprint .2 optional) |

## 完了記録 (実装後記入)

- completion_commits: (TBD)
- 実際の Sprint 所要: (TBD)
- 残 carry / debt: (TBD)

## 関連 reference

- [[PLAN-121]] (parent PLAN、skill recommender improvement)
- [[PLAN-150]] (helix-codex prompt cache、同様の cache 設計パターン)
- [[feedback_codex_docs_enum_inline_prompt]] (enum 正本 inline prompt、Sprint 委譲時注意)
- cli/lib/skill_recommender.py (本 PLAN が統合する既存モジュール)
- `.helix/cache/skill-catalog.json` (catalog hash の参照元)

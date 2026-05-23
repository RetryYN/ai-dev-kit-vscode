---
plan_id: PLAN-141
title: "PLAN-141: agent_slots 実 model 解決 framework (role → model 自動 lookup)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: S
created: 2026-05-23
owner: PMO
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — 設計レビュー・ROLE_MAP.md 整合確認"
  - role: se
    slot_label: "SE — cli/lib/role_resolver.py 実装 + plan_validator 拡張 + テスト"
  - role: qa
    slot_label: "QA — pytest unit test 設計・実装"
generates:
  - artifact_path: cli/lib/role_resolver.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_role_resolver.py
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr: []
related_plans:
  - PLAN-091
related_docs:
  - cli/ROLE_MAP.md
  - cli/lib/plan_validator.py
  - helix/HELIX_CORE.md
---

# PLAN-141: agent_slots 実 model 解決 framework (role → model 自動 lookup)

> **kind**: impl (新規 Python module + plan_validator 拡張)
> **layer**: L4 (実装フェーズ。新規 helper module + CLI 拡張 + unit test)
> **drive**: be (CLI / Python helper 実装中心)
> **本 PLAN の役割**: PLAN frontmatter の `agent_slots[].role` 名 (se / pg / pmo-sonnet 等) から実 model 名 (gpt-5.4 / gpt-5.3-codex-spark / claude-sonnet-4-6 等) を自動 lookup する framework を実装する。`helix codex --role X` での委譲時に正しい model が適用されることを保証する。

---

## §0. 本 PLAN の位置付け

PLAN frontmatter の `agent_slots` フィールドには role 名を記載する設計だが (PLAN-091 V5 framework 確立)、実 model との対応は以下の問題を持つ:

1. **手動参照依存**: role → model の対応は `cli/ROLE_MAP.md` を手動で読む必要がある。委譲時の model 指定ミスが検出されない
2. **plan_validator の未対応**: plan_validator は role 名の妥当性検証 (ROLE_MAP.md 照合) は実装済だが、role → model lookup の API を提供していない
3. **委譲時の不整合リスク**: `helix codex --role tl` を投入する際、model 名を外部から参照する必要があり、ROLE_MAP.md との drift が生じやすい

本 PLAN で `cli/lib/role_resolver.py` を新規作成し、以下を提供する:

- role 名 → model 名の変換 API (`resolve_model(role: str) -> str`)
- role 名 → slot_label のデフォルト生成 (`default_slot_label(role: str) -> str`)
- `helix codex --role X` の実行前 fail-close (未定義 role で実行不可)
- plan_validator への統合 (resolve_model を利用した role 検証強化)

### WebSearch skip 根拠

本 PLAN は HELIX 内部の ROLE_MAP.md パースと Python module 追加。外部ライブラリへの新規依存なし。PLAN-087 ガードレール「設計 doc 新規起票・大幅 scope 変更時」に非該当。**WebSearch skip: 既存 framework 内の実装改善、新技術採用なし**。

---

## §1. 目的

1. `cli/lib/role_resolver.py` を新規作成し、ROLE_MAP.md をパースして role → model dict を提供する (Sprint .1)
2. `helix codex --role X` の実行時に role_resolver を呼び出し、未定義 role で fail-close する (Sprint .2)
3. plan_validator の agent_slots 検証に role_resolver を統合し、role 未定義を warn ではなく error として扱えるようにする (Sprint .2)
4. unit test を追加して role_resolver の動作を保証する (Sprint .3)

---

## §2. 背景・詳細

### 2.1 ROLE_MAP.md の現行形式

`cli/ROLE_MAP.md` の role テーブルは以下の形式:

```markdown
| ロール | model | 担当フェーズ | 説明 |
|--------|--------|------------|------|
| tl     | gpt-5.5 | L2/L3/G2-G5 | 設計・レビュー・ゲート判定 |
| se     | gpt-5.4 | L4          | 上級実装・契約・リファクタリング |
...
```

plan_validator.py の `load_valid_roles()` は既にこのテーブルをパースしている (role 名の set のみ抽出)。role_resolver はこれを拡張し、model 名も同時に抽出する。

### 2.2 role_resolver.py の設計

```python
# cli/lib/role_resolver.py

from __future__ import annotations
from pathlib import Path
from functools import lru_cache
from typing import NamedTuple


class RoleInfo(NamedTuple):
    role: str
    model: str
    phase: str
    description: str


@lru_cache(maxsize=1)
def load_role_map(role_map_path: Path | None = None) -> dict[str, RoleInfo]:
    """ROLE_MAP.md をパースして role → RoleInfo dict を返す。"""
    ...


def resolve_model(role: str, role_map_path: Path | None = None) -> str:
    """role 名から model 名を返す。未定義 role は ValueError を raise する。"""
    ...


def is_valid_role(role: str, role_map_path: Path | None = None) -> bool:
    """role が ROLE_MAP.md に定義されているか確認する。"""
    ...
```

### 2.3 fail-close 設計

`helix codex --role X` の実行フロー (bash shim `cli/helix-codex`) に以下を追加:

```bash
# role_resolver を呼び出し、未定義 role は exit 1 で fail-close
python3 -c "from cli.lib.role_resolver import resolve_model; resolve_model('$ROLE')" \
  || { echo "ERROR: role '$ROLE' is not defined in ROLE_MAP.md" >&2; exit 1; }
```

### 2.4 plan_validator 統合

既存の `validate_agent_slots()` は `load_valid_roles()` で role set を取得している。role_resolver を統合後:

- `load_valid_roles()` を `role_resolver.load_role_map()` で置き換え可能
- agent_slots の role 検証を同一コードパスで実施
- 将来的に model の override 検証 (frontmatter の model 明示時の整合性) に拡張可能

---

## §3. 実装計画

### Sprint .1: role_resolver.py 実装 (Codex se 委譲)

**Entry 条件**: `cli/lib/plan_validator.py` の `load_valid_roles()` と `cli/ROLE_MAP.md` のテーブル形式を Read して確認済

実施内容:

1. `cli/lib/role_resolver.py` 新規作成
   - `load_role_map()`: ROLE_MAP.md のテーブル行をパース、role → RoleInfo dict を構築、`@lru_cache` で 1 回のみ読み込み
   - `resolve_model(role)`: dict lookup、未定義は ValueError
   - `is_valid_role(role)`: bool wrapper
2. `python3 -m py_compile cli/lib/role_resolver.py` PASS 確認
3. `cli/lib/plan_validator.py` の `load_valid_roles()` が role_resolver の `load_role_map()` を利用するよう統合 (既存の role 検証は動作変更なし)

Sprint .1 完了条件:

- `cli/lib/role_resolver.py` が `resolve_model("se")` → `"gpt-5.4"` を返す
- `resolve_model("undefined-role")` が ValueError を raise する
- `cli/lib/plan_validator.py` の既存 role 検証が regression なし

### Sprint .2: helix-codex fail-close 統合 (Codex se 委譲)

**Entry 条件**: Sprint .1 完了 + `cli/helix-codex` の実行フローを Read 済

実施内容:

1. `cli/helix-codex` の `--role` 引数処理箇所に role_resolver 呼び出しを追加
2. 未定義 role の場合は error メッセージを stderr に出力して exit 1
3. `bash -n cli/helix-codex` PASS 確認

Sprint .2 完了条件:

- `helix codex --role undefined-role --task "test"` が `ERROR: role 'undefined-role' is not defined in ROLE_MAP.md` を出力して終了する
- 既存 role (`se` / `tl` / `pg` 等) では動作変更なし

### Sprint .3: unit test + regression 確認 (Codex qa 委譲)

**Entry 条件**: Sprint .1/.2 完了

実施内容:

1. `cli/lib/tests/test_role_resolver.py` 新規作成
   - `test_resolve_model_se`: `resolve_model("se")` → `"gpt-5.4"`
   - `test_resolve_model_pmo_sonnet`: `resolve_model("pmo-sonnet")` → `"claude-sonnet-4-6"`
   - `test_resolve_model_undefined`: `resolve_model("undefined")` → ValueError
   - `test_is_valid_role_true`: `is_valid_role("tl")` → True
   - `test_is_valid_role_false`: `is_valid_role("nonexistent")` → False
   - `test_load_role_map_all_roles`: 全 role が dict に含まれることを確認 (件数 ≥ 25)
2. `python3 -m pytest cli/lib/tests/test_role_resolver.py -q` 全 PASS
3. `python3 -m pytest cli/lib/tests/test_plan_validator.py -q` 全 PASS (regression なし)

Sprint .3 完了条件:

- test_role_resolver 6 件全 PASS
- test_plan_validator 全 PASS (sprint .1 の統合で regression なし)

---

## §4. 段階導入

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **Sprint .1** | role_resolver.py 実装 + plan_validator 統合 | se | `resolve_model("se")` → `"gpt-5.4"` / plan_validator regression なし |
| **Sprint .2** | helix-codex fail-close 統合 | se | 未定義 role で exit 1 / 既存 role 動作変更なし |
| **Sprint .3** | unit test + regression 確認 | qa | test 6 件 PASS / plan_validator test 全 PASS |

---

## §5. デグレ禁止項目

1. `cli/lib/plan_validator.py` の role 検証動作は変更しない (warn 出力の形式・内容を維持)
2. `cli/ROLE_MAP.md` は read-only (本 PLAN では編集しない)
3. `helix codex --role <既存 role>` の動作は変更しない (fail-close は未定義 role のみ)
4. plan_validator の `load_valid_roles()` 関数は外部互換のために残す (内部で role_resolver を呼び出す形に変更)

---

## §6. DoD (Definition of Done)

1. `cli/lib/role_resolver.py` が存在し、`resolve_model()` / `is_valid_role()` / `load_role_map()` を提供する
2. `resolve_model("se")` → `"gpt-5.4"` / `resolve_model("pmo-sonnet")` → `"claude-sonnet-4-6"` が正確に返る
3. `resolve_model("undefined")` が ValueError を raise する
4. `helix codex --role undefined-role` が exit 1 で終了する
5. `python3 -m pytest cli/lib/tests/test_role_resolver.py -q` 全 PASS (6 件)
6. `python3 -m pytest cli/lib/tests/test_plan_validator.py -q` 全 PASS (regression なし)
7. `python3 -m py_compile cli/lib/role_resolver.py` PASS
8. `bash -n cli/helix-codex` PASS
9. `python3 cli/lib/plan_validator.py docs/plans/PLAN-141-*.md` が PASS

---

## §7. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-141-agent-slots-role-model-resolver.md |
| ② 実装コード | Sprint .1〜.2 で実装 | cli/lib/role_resolver.py / cli/helix-codex |
| ③ テスト設計 | Sprint .3 entry で策定 | docs/v2/L4-test-design/PLAN-141-role-resolver-test-design.md (予定) |
| ④ テストコード | Sprint .3 で実装 | cli/lib/tests/test_role_resolver.py |

**双方向 reference**:

- 本 PLAN → 実装コード: `generates.artifact_path` に `cli/lib/role_resolver.py` を明記
- 実装コード → 本 PLAN: `role_resolver.py` の module docstring に「設計: PLAN-141」を追記
- 本 PLAN → テストコード: `generates.artifact_path` に `cli/lib/tests/test_role_resolver.py` を明記
- テストコード → 本 PLAN: test file docstring に「DoD 検証: PLAN-141 §6」を追記

---

## §8. 関連 PLAN / ADR

### 関連 PLAN

- PLAN-091: V5 framework 本体。agent_slots frontmatter の定義規約を確立したソース

### 関連 ADR

なし (既存 ROLE_MAP.md のパース改善。L2 大局判断なし)

---

## §9. リスク

| リスク | 緩和策 |
|---|---|
| ROLE_MAP.md のテーブル形式変更 | `load_role_map()` のパース処理に `# @helix:index` メタデータ行を skip する条件を追加。形式変更時は ValueError で即エラー化して気付きを促す |
| `@lru_cache` でテスト間に state が残る | テスト側で `load_role_map.cache_clear()` を pytest fixture の teardown で呼ぶ |
| plan_validator.py 統合で既存 test が落ちる | Sprint .1 で `test_plan_validator.py` を先に実行して baseline を確認し、統合後に再確認する 2 段階で進める |

---

## §10. mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/role_resolver.py` PASS
- [ ] `python3 -m pytest cli/lib/tests/test_role_resolver.py -q` 全 PASS
- [ ] `python3 -m pytest cli/lib/tests/test_plan_validator.py -q` 全 PASS (regression なし)
- [ ] `bash -n cli/helix-codex` PASS
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)

---
plan_id: PLAN-137
title: "PLAN-137: helix-codex --approved 自動付与 framework (実装 vs 計画 classify)"
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
    slot_label: "SE — helix-codex classify logic 実装 + opt-out flag 追加"
  - role: pmo-sonnet
    slot_label: "PMO — classify 仕様レビュー・既存 plan-only guard との整合確認"
  - role: qa
    slot_label: "QA — classify 判定テスト + sandbox writable 動作確認 fixture"
generates:
  - artifact_path: cli/helix-codex
    artifact_type: cli_extension
  - artifact_path: cli/lib/codex_task_classifier.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_codex_task_classifier.py
    artifact_type: test
dependencies:
  parent: PLAN-MM-001
  requires: []
  blocks: []
related_adr: []
related_plans:
  - PLAN-137
  - PLAN-138
related_docs:
  - CLAUDE.md §委譲 Codex のコミット禁止
  - helix/CODEX_TL_MODE.md §helix codex hard guard
---

# PLAN-137: helix-codex --approved 自動付与 framework

> **kind**: impl | **layer**: L4 | **drive**: be | **size**: M

---

## §0. 背景・位置付け

2026-05-23 session で `helix codex --role se` 委譲が sandbox read-only で実装 fail する事例が発生。
失敗操作: SQLite DB open / `__pycache__` 作成 / pytest tmp dir 生成。

`helix-codex` デフォルトは plan-only (sandbox read-only)。`--approved` で writable になるが、
呼び出し側が毎回明示する必要があり、classify 自動化がなく実装タスクが失敗し続ける。

本 PLAN は task description / allowed_files / role から「実装 vs 計画」を classify し、
実装スコープなら `--approved` を自動付与する framework を整備する。

**WebSearch skip**: 内部 CLI 拡張。既存 gpt-5.4-mini recommender 流用で新技術採用なし。

---

## §1. 設計方針

### classify 判定基準

| 判定軸 | 実装スコープ (→ approve) | 計画スコープ (→ plan-only) |
|---|---|---|
| role | se / pe / pg / qa / dba / devops / fe | tl / docs / research / pmo-sonnet |
| task キーワード | 「実装」「追加」「修正」「作成」「migrate」 | 「調査」「確認」「分析」「設計」「レビュー」 |
| allowed_files | `.py` / `.sh` write 指定あり | 未指定 or `.md` のみ |

classify 優先順位:
1. plan-only role (tl / docs / research 等) → 即 `"plan"` (LLM 不使用)
2. allowed_files に `.py` / `.sh` write 指定 → 即 `"impl"` (LLM 不使用)
3. 上記未確定 → gpt-5.4-mini classify (1 時間 TTL キャッシュ)
4. LLM timeout / error → `"plan"` フォールバック (安全側)

### `codex_task_classifier.py` インタフェース

```python
def classify_task(
    task: str,
    role: str,
    allowed_files: list[str] | None = None,
) -> Literal["impl", "plan"]:
    """返値: "impl" → --approved 自動付与、"plan" → plan-only 維持"""
```

### helix-codex 統合

```bash
CLASSIFY_RESULT=$(python3 "$HELIX_HOME/cli/lib/codex_task_classifier.py" \
  --task "$TASK" --role "$ROLE" --allowed-files "$ALLOWED_FILES")

if [[ "$CLASSIFY_RESULT" == "impl" && -z "$FORCE_PLAN_ONLY" ]]; then
  CODEX_FLAGS="$CODEX_FLAGS --approved"
fi
```

追加 flag: `--force-plan-only` (classify 無視で plan-only 強制) / `--auto-approve` (デフォルト ON)

---

## §2. 実装計画

### Sprint .1: classify module (se、size S)

1. `cli/lib/codex_task_classifier.py` 新規作成 (role 即判定 + gpt-5.4-mini fallback + TTL キャッシュ)
2. `python3 -m py_compile cli/lib/codex_task_classifier.py` PASS

受入条件: `classify_task("実装する","se")` → `"impl"` / `classify_task("調査","docs")` → `"plan"` / LLM timeout → `"plan"`

### Sprint .2: helix-codex 統合 (se、size S)

1. `cli/helix-codex` に classify 呼び出し + `--force-plan-only` flag 追加
2. `bash -n cli/helix-codex` PASS

受入条件: `helix codex --role se --task "test_module.py を実装する"` が `--approved` 相当で実行 / `--force-plan-only` 指定時 plan-only 維持

### Sprint .3: fixture 検証 (qa、size S)

1. `cli/lib/tests/test_codex_task_classifier.py` 新規作成 (8 scenario、gpt-5.4-mini mock)
2. `pytest cli/lib/tests/test_codex_task_classifier.py -v` 全 PASS

---

## §3. DoD

1. `classify_task` 3 pattern (impl / plan / LLM fallback) PASS
2. `helix codex --role se --task "実装する"` が writable sandbox で実行される
3. `--force-plan-only` 指定時に classify 結果に関わらず plan-only で実行される
4. `pytest test_codex_task_classifier.py -q` 全 PASS (8 scenario)
5. `bash -n cli/helix-codex` + `py_compile codex_task_classifier.py` PASS
6. `python3 cli/lib/plan_validator.py docs/plans/PLAN-137-*.md` PASS

---

## §4. デグレ禁止

- 既存の明示 `--approved` 呼び出しの動作を変更しない
- `--force-plan-only` は classify 結果より優先する
- LLM error / timeout 時は `"plan"` フォールバック (sandbox を write にしない)
- `HELIX_CODEX_REQUIRE_APPROVED=1` 環境下では auto classify を承認済みとみなす

---

## §5. V-model trace

- ① 設計: `docs/plans/PLAN-137-codex-approved-auto-flag.md` (本 file)
- ② 実装: `cli/lib/codex_task_classifier.py` / `cli/helix-codex` → docstring に「設計: PLAN-137」
- ③ テスト設計: Sprint .3 entry で §2 Sprint .3 を正本とする
- ④ テストコード: `cli/lib/tests/test_codex_task_classifier.py` → docstring に「DoD 検証: PLAN-137 §3」

---

## §6. リスク

| リスク | 緩和策 |
|---|---|
| 計画タスクを誤って impl classify → 意図しない write | role ベース即判定で plan-only role は確実に plan-only。`--force-plan-only` で opt-out 可 |
| gpt-5.4-mini API error | `"plan"` フォールバック (安全側)。WARN log + 明示 `--approved` での再実行案内 |
| TTL キャッシュと実タスク内容のずれ | キャッシュ key = sha256(task + role + allowed_files)。`--no-cache` flag で無効化可 |

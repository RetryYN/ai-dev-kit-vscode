---
plan_id: PLAN-144
title: "PLAN-144: SessionStart hook 拡張 (handover + carry status + PLAN open list auto-inject)"
layer: L4
kind: impl
status: draft
size: M
drive: be
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: se
    slot_label: "SE — sessionstart-context-inject.sh 実装 + context_injector.py + 既存 hook 共存確認"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・PLAN-081/099/115/139 との共存チェック・bundle サイズ検証"
  - role: qa
    slot_label: "QA — T5-001〜007 snapshot test 実装 + fake handover / fake carry fixture"
  - role: tl-advisor
    slot_label: "TL adversarial check — G4 凍結判定・bundle injection の secret/PII リスク review"
generates:
  - artifact_path: .claude/hooks/sessionstart-context-inject.sh
    artifact_type: hook
  - artifact_path: cli/lib/context_injector.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_context_injector.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-144-sessionstart-context-inject.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-051-sessionstart-context-inject-decision.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-099
  requires:
    - PLAN-099
    - PLAN-081
  blocks: []
related_adr:
  - ADR-051-sessionstart-context-inject-decision
related_plans:
  - PLAN-099 (親 PLAN、V5 Layer 4 定義。Layer 4 + SessionStart 注入設計の正本)
  - PLAN-081 (SessionStart 既存 hook。sessionstart-harness-summary.sh と共存必須)
  - PLAN-115 (claude-brain pattern 実装。sessionstart-history-injection.sh と共存)
  - PLAN-139 (runtime carry monitoring。carry-status コマンドを本 PLAN が呼ぶ)
  - PLAN-087 (WebSearch ガードレール。本 PLAN は L2 大局判断を含むため ADR-051 起票必須)
test_design: docs/v2/L4-test-design/PLAN-144-unit-test-design.md (別 session 起票予定)
---

# PLAN-144: SessionStart hook 拡張 (handover + carry status + PLAN open list auto-inject)

> **本 PLAN の位置付け**: PLAN-099 Layer 4 の子 PLAN (PLAN-115 と並列)。  
> 現状 SessionStart hook (PLAN-081) は stale slot 案内のみを出力する。  
> 本 PLAN は「handover summary」「carry status」「PLAN open list」を SessionStart 時に  
> 自動 inject することで、次 session 初期化を即座に可能にする。

---

## 1. 目的

SessionStart 時に以下 3 つの context を自動 inject し、セッション開始コストを削減する:

1. **handover summary** — `.helix/handover/CURRENT.json` が存在する場合、Next Action を要約して inject
2. **carry status** — `helix runtime carry-status` (PLAN-139) の出力を inject (carry 件数 / P0 明示)
3. **PLAN open list** — `status=draft` かつ `completed_at=null` の PLAN を最大 5 件 summary inject

---

## 2. 背景

### 2.1 現状の SessionStart hook 群

| hook | 役割 | 状態 |
|---|---|---|
| sessionstart-harness-summary.sh (PLAN-081) | stale slot 案内 + helix doctor 結果 | 実装済み |
| sessionstart-history-injection.sh (PLAN-115) | cleared/compacted 後の transcript 要約 bundle 注入 | 本 session 起票 |
| sessionstart-context-inject.sh (本 PLAN) | handover + carry + PLAN open list inject | **本 PLAN で追加** |

### 2.2 解決する問題

従来は session 開始直後に手動で以下を確認する必要があった:

```bash
helix handover status --json       # handover 確認
helix runtime carry-status         # carry 確認
helix plan list --status draft     # open PLAN 確認
```

3 コマンドの手動実行を SessionStart hook で自動化し、初手からコンテキストを持った状態で作業開始できる。

### 2.3 MEMORY.md との関係

MEMORY.md (`project_2026_05_23_session_handover.md`) は人手で更新する session 引き継ぎメモ。  
本 PLAN の auto-inject は MEMORY.md を **補完** するが、置き換えはしない:

| 情報源 | 役割 | 更新タイミング |
|---|---|---|
| MEMORY.md | 学び・feedback・プロジェクト状況の永続記録 | session 終了時に人手更新 |
| handover CURRENT.json | BE 実装継続の具体的 Next Action | Opus / Codex が随時更新 |
| carry-status | 未消化 carry の機械的集計 | コマンド実行時点の snapshot |
| PLAN open list | draft 状態の PLAN 一覧 | plan_registry から DB 抽出 (PLAN-116 前提) |

---

## 3. L2 凍結 (ADR snapshot 必須)

本 PLAN は以下の L2 大局判断を含む:

1. **handover + carry + PLAN open list を SessionStart inject に統合する採用決定**
   - 根拠: 3 情報源を 1 hook で集約することで、session 開始時の手動確認を撤廃
2. **inject bundle を ≤60 行 (≒750 token) に制限する採用決定**
   - 根拠: PLAN-115 の ≤500 token 制限と合計して ≤1250 token に抑え、context 圧迫を回避
3. **plan_registry 不在時の graceful fallback 採用決定**
   - 根拠: PLAN-116 (v36 schema) が未適用の環境でも hook が crash しないよう、file scan fallback を設ける

→ ADR-051-sessionstart-context-inject-decision.md を本 PLAN と同時起票すること。

> WebSearch は本 PLAN の scope 外。ただし inject パターンの設計根拠として  
> PLAN-115 §3 WebSearch 実績 (MemGPT / OWASP LLM06) を継承・参照する。

---

## 4. 設計方針

### 4.1 sessionstart-context-inject.sh の動作

```bash
# .claude/hooks/sessionstart-context-inject.sh
# SessionStart event hook (全 session_type に発火)
# Output: stdout JSON {systemMessage: "<bundle>"}

BUNDLE_MAX_LINES=60   # ~750 token 相当

bundle=$(python3 cli/lib/context_injector.py \
  --handover-path ".helix/handover/CURRENT.json" \
  --carry-cmd "helix runtime carry-status --json" \
  --plan-db ".helix/helix.db" \
  --plan-fallback-dir "docs/plans" \
  --max-lines "$BUNDLE_MAX_LINES")

if [ -n "$bundle" ]; then
  printf '{"systemMessage": %s}' "$(echo "$bundle" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
else
  exit 0
fi
```

### 4.2 context_injector.py の設計

```python
# cli/lib/context_injector.py
# 責務: handover / carry / PLAN open list を集約して bundle 文字列を生成する

PLAN_OPEN_LIST_MAX = 5       # inject する PLAN open list の最大件数
BUNDLE_MAX_LINES   = 60      # --max-lines デフォルト値

def build_bundle(
    handover_path: str,
    carry_cmd: str,
    plan_db: str,
    plan_fallback_dir: str,
    max_lines: int = BUNDLE_MAX_LINES,
) -> str:
    """
    3 情報源から bundle 文字列を生成する。
    空情報源はスキップする (部分失敗を許容)。
    合計行数が max_lines を超えたら末尾を truncate する。
    """
    sections: list[str] = []

    # 1. handover summary
    handover_section = _build_handover_section(handover_path)
    if handover_section:
        sections.append(handover_section)

    # 2. carry status
    carry_section = _build_carry_section(carry_cmd)
    if carry_section:
        sections.append(carry_section)

    # 3. PLAN open list
    plan_section = _build_plan_open_section(plan_db, plan_fallback_dir)
    if plan_section:
        sections.append(plan_section)

    bundle = "\n\n".join(sections)
    return _truncate_lines(bundle, max_lines)


def _build_handover_section(handover_path: str) -> str:
    """
    CURRENT.json が存在すれば Next Action 先頭 3 件 + status を返す。
    存在しない場合は空文字列を返す (graceful)。
    """
    ...


def _build_carry_section(carry_cmd: str) -> str:
    """
    helix runtime carry-status --json を subprocess で実行し、
    P0/P1 carry 件数 + 先頭 3 件のタイトルを返す。
    コマンド失敗時は空文字列 (graceful)。
    """
    ...


def _build_plan_open_section(plan_db: str, fallback_dir: str) -> str:
    """
    plan_registry (DB) から status=draft を最大 PLAN_OPEN_LIST_MAX 件取得。
    DB 不在 or v36 未適用の場合は docs/plans/ を grep fallback。
    """
    ...


def _truncate_lines(text: str, max_lines: int) -> str:
    """max_lines を超えたら末尾を切り捨て '...(truncated)' を付加する"""
    ...
```

### 4.3 既存 hook との共存

```
SessionStart 発火順序 (settings.json の hooks 配列順):
  1. sessionstart-harness-summary.sh (PLAN-081) — stale slot 案内
  2. sessionstart-history-injection.sh (PLAN-115) — transcript bundle 注入
  3. sessionstart-context-inject.sh (本 PLAN) — handover + carry + PLAN open list
```

3 hook は **独立した systemMessage** を出力する。Claude Code は複数 systemMessage を結合して注入する仕様 (PLAN-115 §3 Q2 確認済み)。

---

## 5. bundle 出力サンプル

```
## SessionStart Context (2026-05-23 UTC)

### Handover
- status: in_progress  owner: opus
- Next Action:
  1. pytest-xdist isolation PLAN 起票
  2. gate flake root cause 調査
  3. merge_settings.py _is_helix_hook bug 修正

### Carry Status
- P0: 0 件 / P1: 2 件 / P2: 3 件
- P1 carry:
  - pytest-xdist helix-db.lock isolation (PLAN 起票候補)
  - gate flake 1 件 (test_gate_design_doc_fail_close_passes_with_existing_web_and_oss_references)

### PLAN Open List (draft, 5 件)
- PLAN-116: helix.db v36 schema
- PLAN-134: helix metrics CLI
- PLAN-139: runtime carry monitoring
- PLAN-143: helix.db v37 schema (event_log + telemetry)
- PLAN-144: SessionStart hook 拡張 (本 PLAN)
```

---

## 6. 実装 Sprint

### Sprint .1: context_injector.py 実装

**担当**: se  
**scope**:
- `cli/lib/context_injector.py` 新規作成
  - `build_bundle()` + 3 private helper 実装
  - `_truncate_lines()` 実装
  - graceful fallback 確認 (handover 不在 / carry コマンド失敗 / DB 不在 でも crash しない)
- `cli/lib/tests/test_context_injector.py` 新規作成
  - fake handover json / fake carry json / fake plan list fixture
  - T5-001〜007 test case 実装

**Entry 条件**: PLAN-081 実装済み確認 + PLAN-139 carry-status コマンド動作確認  
**Exit 条件**: `python3 -m py_compile cli/lib/context_injector.py` PASS + pytest T5-001〜007 全 PASS

### Sprint .2: hook 実装 + settings.json 登録

**担当**: se  
**scope**:
- `.claude/hooks/sessionstart-context-inject.sh` 新規作成
  - §4.1 の設計に準拠
  - `bash -n` + `shellcheck` PASS
- `.claude/settings.json` の hooks 配列に追加 (PLAN-081 / PLAN-115 hook の後に挿入)
- smoke test: SessionStart をローカル発火して bundle が systemMessage に含まれることを確認

**Entry 条件**: Sprint .1 完遂  
**Exit 条件**: hook smoke test PASS + 既存 hook (PLAN-081 / PLAN-115) とのデグレなし確認

### Sprint .3: QA + pmo-sonnet review

**担当**: qa + pmo-sonnet  
**scope**:
- テスト設計 doc 起票 (docs/v2/L4-test-design/PLAN-144-unit-test-design.md)
- pmo-sonnet 設計整合確認
  - §4.3 共存設計 ↔ settings.json hook 順序の一致確認
  - bundle ≤60 行制限の実装確認
  - plan_registry fallback 動作確認
- tl-advisor adversarial check (inject 内容の secret/PII 漏洩リスク、G4 凍結判定)
- 全回帰 PASS

**Entry 条件**: Sprint .2 完遂  
**Exit 条件**: 全回帰 PASS + pmo-sonnet review 承認 + tl-advisor G4 passed

---

## 7. DoD (Definition of Done)

- [ ] `cli/lib/context_injector.py` 実装済み (build_bundle / 3 helper / _truncate_lines)
- [ ] graceful fallback 確認: handover 不在 / carry コマンド失敗 / DB 不在 で exit 0 (crash なし)
- [ ] `cli/lib/tests/test_context_injector.py` で T5-001〜T5-007 全 PASS:
  - T5-001: handover あり → Next Action 3 件含む bundle 生成
  - T5-002: handover なし → handover section スキップ、他 section 出力
  - T5-003: carry P1 あり → P1 件数 + タイトル含む bundle 生成
  - T5-004: carry コマンド失敗 → carry section スキップ (graceful)
  - T5-005: plan_registry あり → draft PLAN 5 件以内含む bundle 生成
  - T5-006: plan_registry なし → fallback dir から draft PLAN grep
  - T5-007: bundle max_lines 超過 → 末尾 truncate + '...(truncated)' 付加
- [ ] `.claude/hooks/sessionstart-context-inject.sh` 実装済み + settings.json 登録済み
- [ ] 既存 hook (PLAN-081 / PLAN-115) とのデグレなし確認
- [ ] `bash -n` + `shellcheck` PASS
- [ ] `python3 -m py_compile cli/lib/context_injector.py` PASS
- [ ] 全回帰 PASS (`helix test`)
- [ ] ADR-051 起票済み + 双方向 reference 確立
- [ ] pmo-sonnet review 承認
- [ ] tl-advisor G4 passed

---

## 8. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 | docs/plans/PLAN-144-sessionstart-context-inject.md |
| ② 実装コード | 未着手 (Sprint .1-.2) | cli/lib/context_injector.py / .claude/hooks/sessionstart-context-inject.sh |
| ③ テスト設計 | 未起票 (Sprint .3) | docs/v2/L4-test-design/PLAN-144-unit-test-design.md |
| ④ テストコード | 未着手 (Sprint .1) | cli/lib/tests/test_context_injector.py |

双方向 reference:
- 本 PLAN → ADR-051: `related_adr: [ADR-051-sessionstart-context-inject-decision]`
- ADR-051 → 本 PLAN: `Related: PLAN-144 (実装 tree)`
- 本 PLAN → PLAN-099: `dependencies.parent: PLAN-099`
- PLAN-099 §8 → 本 PLAN: Layer 4 SessionStart inject の子 PLAN として参照 (別 session 更新予定)
- 本 PLAN → PLAN-081: `dependencies.requires: [PLAN-081]`
- 実装コード → 本 PLAN: docstring に `# 契約: PLAN-144 §4 設計方針` を明示 (実装時)

---

## 9. 関連リンク

| 文書 | パス |
|---|---|
| PLAN-099 (親 PLAN、Layer 4 定義) | docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md |
| ADR-051 (本 PLAN の L2 snapshot、candidate) | docs/adr/ADR-051-sessionstart-context-inject-decision.md |
| PLAN-081 (SessionStart 既存 hook) | docs/plans/PLAN-081-stop-hook-auto-handover.md |
| PLAN-115 (claude-brain pattern、共存) | docs/plans/PLAN-115-claude-brain-pattern-helix-implementation.md |
| PLAN-139 (carry monitoring、carry-status コマンド) | docs/plans/PLAN-139-runtime-carry-monitoring.md |
| PLAN-116 (v36 schema、plan_registry 依存) | docs/plans/PLAN-116-helix-db-v36-schema.md |
| PLAN-087 (WebSearch ガードレール) | docs/plans/PLAN-087-design-doc-web-search-guardrail.md |

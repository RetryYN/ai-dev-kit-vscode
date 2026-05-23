---
plan_id: PLAN-146
title: "agent slot timeout 段階遷移 (5min advisory → 10min WARN → 15min auto-release)"
kind: refactor
layer: L4
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
size: S
created: "2026-05-23"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: se
    slot_label: "SE — agent_slot timeout 段階遷移 logic + advisory/WARN/auto-release 実装"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-129 stuck 検出との設計整合確認・重複ロジック drift チェック"
  - role: qa
    slot_label: "QA — 3 段階 threshold fake fixture テスト全ケース検証"
generates:
  - artifact_path: docs/plans/PLAN-146-agent-slot-timeout-graduation.md
    artifact_type: design_doc
  - artifact_path: cli/lib/helix_db.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_agent_slot_timeout_graduation.py
    artifact_type: test
dependencies:
  parent: null
  requires:
    - PLAN-129
  blocks: []
related_plans:
  - PLAN-129 (pmo-sonnet stuck 検出 + auto-recovery hook — 単一閾値 10min の正本)
  - PLAN-088 (TodoWrite × agent slot framework — agent_slots テーブル lifecycle 正本)
---

# PLAN-146: agent slot timeout 段階遷移

## 背景

PLAN-129 で確立した stuck 検出 framework では timeout 閾値が単一 (10 分) であり、
「stuck 候補」と「明確な stuck」の区別なく同一ポリシーが適用される。

具体的な問題:

1. 10 分超過で即 WARN が発火するため、やや重い処理 (pmo-sonnet の長文解析等) でも
   誤検出が発生し PM の注意を引きすぎる
2. auto-release (15 分) までの間に「候補である」という advisory 段階が存在しないため、
   PM が状況を把握してから介入する余地が少ない
3. helix doctor の WARN 増加を「ノイズ」と感じさせるリスクがある

PLAN-129 の `STUCK_THRESHOLD_MIN=10` を 3 段階に分割し、
段階的に緩やかに対応を強化することで誤検出ノイズを低減しつつ stuck を確実に回収する。

## WebSearch skip

本 PLAN は HELIX 内部の閾値ロジック変更 (refactor) であり、既存 PLAN-129 の実装範囲に収まる。
外部ライブラリ / 新規 framework の採用なし。

WebSearch **skip**。

## PLAN-129 との関係

本 PLAN は PLAN-129 の **後継実装** として位置づける。

| 側面 | PLAN-129 | 本 PLAN (PLAN-146) |
|---|---|---|
| 閾値 | 単一 (10 min stuck / 60 min stale) | 3 段階 (5 / 10 / 15 min) |
| スコープ | stuck 検出 + auto-recovery hook 新規作成 | 既存 threshold logic の refactor |
| DB schema | `last_activity_timestamp` 追加 (migration v36) | 追加変更なし (PLAN-129 schema を継承) |

**依存**: 本 PLAN の実装前提として PLAN-129 の Sprint .1 (migration v36 + `get_stuck_slots`) が完了していること。

## 設計方針

### 3 段階 threshold 定義

| 段階 | 経過時間 | 名称 | アクション |
|---|---|---|---|
| **advisory** | 5 min 超 | stuck 候補 | `helix doctor` INFO ログのみ (stderr に表示なし) |
| **WARN** | 10 min 超 | stuck 疑い | `helix doctor` WARN に積む + SessionStart hook で通知 |
| **auto-release** | 15 min 超 | stuck 確定 | `agent_slots.release_slot(status='stuck')` 自動実行 |

#### 既存 PLAN-129 との段階対応

```
PLAN-129 (単一閾値 10 min WARN + detect → 15 min release)
       ↓ refactor
PLAN-146 (5 min advisory → 10 min WARN → 15 min release)
```

`STUCK_THRESHOLD_MIN` (10 min) は WARN 段階に対応し、意味的な互換性を保つ。

### threshold パラメータ外部化

全閾値を環境変数で外部化する。固定値埋め込みを禁止する。

```bash
HELIX_SLOT_ADVISORY_MIN="${HELIX_SLOT_ADVISORY_MIN:-5}"
HELIX_SLOT_WARN_MIN="${HELIX_SLOT_WARN_MIN:-10}"
HELIX_SLOT_RELEASE_MIN="${HELIX_SLOT_RELEASE_MIN:-15}"
```

### 判定 SQL (3 段階)

```sql
SELECT
  slot_id,
  agent_id,
  role,
  last_activity_timestamp,
  started_at,
  CAST(
    (strftime('%s', 'now') - strftime('%s',
      COALESCE(last_activity_timestamp, started_at))) / 60
  AS INTEGER) AS elapsed_min
FROM agent_slots
WHERE status = 'active'
HAVING elapsed_min >= :advisory_min;
```

`elapsed_min` に応じてアクション分岐:

```python
if elapsed_min >= release_min:
    stage = "release"
elif elapsed_min >= warn_min:
    stage = "warn"
else:
    stage = "advisory"
```

### helix doctor への統合

| 段階 | helix doctor 出力 |
|---|---|
| advisory | `INFO  PLAN-146 slot <slot_id> (<role>) advisory: 5〜9 min 経過` |
| WARN | `WARN  PLAN-146 slot <slot_id> (<role>) stuck 疑い: 10〜14 min 経過` |
| release | `WARN  PLAN-146 slot <slot_id> (<role>) auto-released: 15+ min 経過` |

advisory は INFO に留め、helix doctor の warn カウントを増やさない。
WARN / release は既存 warn カウントに含め、PM に明示する。

## 実装計画

### Sprint .1: 3 段階 threshold logic 実装 (Codex se 委譲、size S)

**Entry 条件**: PLAN-129 Sprint .1 完了 (migration v36 + `get_stuck_slots` 動作確認済)

実施内容:

1. `cli/lib/helix_db.py` の `get_stuck_slots` を 3 段階対応に拡張
   - `get_slot_timeout_stages(advisory_sec, warn_sec, release_sec)` 追加
   - 返り値: `list[SlotTimeoutResult]` (slot_id / role / elapsed_min / stage)
2. advisory / WARN / release の分岐 logic を `sprint_auto_check.py` ではなく
   `helix_db.py` helper に集約する
3. env 変数 `HELIX_SLOT_ADVISORY_MIN` / `HELIX_SLOT_WARN_MIN` / `HELIX_SLOT_RELEASE_MIN` 読み込み
4. `python3 -m py_compile cli/lib/helix_db.py` PASS (mandatory in sprint)

受入条件:
- `get_slot_timeout_stages` が 3 段階に正しく分類する
- env 変数で閾値を上書きできる
- PLAN-129 の `get_stuck_slots(threshold_sec=600)` と同一 interface を維持する

### Sprint .2: fixture テスト実装 (Codex qa 委譲、size S)

**Entry 条件**: Sprint .1 `get_slot_timeout_stages` 動作確認済

実施内容:

1. `cli/lib/tests/test_agent_slot_timeout_graduation.py` 新規作成
   - 5 シナリオ fixture (fake `last_activity_timestamp` を動的生成)
   - `datetime.now(timezone.utc)` ベースで固定値 flake 防止
2. `python3 -m pytest cli/lib/tests/test_agent_slot_timeout_graduation.py -v` 全 PASS

受入条件:
- 5 シナリオ全 PASS
- flake なし (動的 timestamp)

## テスト設計 (V-model L4 単体テスト設計、Sprint .2 対応)

| テスト ID | シナリオ | elapsed_min | 期待 stage |
|---|---|---|---|
| T146-001 | 正常 active (advisory 未満) | 3 min | none (no stage) |
| T146-002 | advisory 段階 | 7 min | advisory |
| T146-003 | WARN 段階 | 12 min | warn |
| T146-004 | auto-release 段階 | 17 min | release |
| T146-005 | `last_activity_timestamp` NULL (started_at fallback) | 20 min | release |

## DoD (Definition of Done)

- [ ] `python3 -m py_compile cli/lib/helix_db.py` PASS (PLAN-129 Sprint .1 継承)
- [ ] `get_slot_timeout_stages` が 3 段階に正しく分類する
- [ ] env 変数 3 種で閾値を外部化
- [ ] 5 シナリオ fixture テスト全 PASS (T146-001〜T146-005)
- [ ] advisory が helix doctor INFO に留まり warn カウントを増やさない
- [ ] PLAN-129 `get_stuck_slots` interface との互換性維持
- [ ] `helix doctor` warn 増加なし

## V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 (本 PLAN) | §設計方針 / §実装計画 |
| ③ テスト設計 | 本 PLAN §テスト設計 (T146-001〜T146-005) |
| ② 実装コード | cli/lib/helix_db.py の `get_slot_timeout_stages` 拡張 (Sprint .1 で実装) |
| ④ テストコード | cli/lib/tests/test_agent_slot_timeout_graduation.py (Sprint .2 で実装) |

双方向 trace:
- 本 PLAN → テスト設計: Sprint .2 ケース一覧に T146 番号明記
- テストコード → 設計: pytest test に `# PLAN-146 T146-NNN` コメントで対応付け
- テスト設計 → テストコード: test 関数名で T146-NNN 対応

## risks

| リスク | 影響 | 緩和策 |
|---|---|---|
| PLAN-129 Sprint .1 未完了で実装着手 | `get_stuck_slots` 不在で compile error | Entry 条件チェックを Sprint .1 開始前に必須化 |
| advisory ノイズ (INFO が多すぎる) | PM の注意散漫 | INFO は helix doctor --verbose 時のみ表示を検討 |
| 閾値デフォルト値の運用合意不足 | 意図しない auto-release | 初回デプロイ時は WARN のみ (release 無効) の段階導入を ADR に記録 |

## 関連 reference

- PLAN-129 §設計方針 (stuck 検出 3 段階ポリシーの正本、本 PLAN は threshold 段階化 refactor)
- PLAN-088 (agent_slots テーブル lifecycle 正本)
- PLAN-099 §Layer 5 (heartbeat と stuck 検出の協調)
- [[feedback_pytest_fixture_time_dependent_flake]] (動的 timestamp fixture 必須の根拠)

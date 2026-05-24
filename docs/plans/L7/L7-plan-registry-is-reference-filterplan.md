---
plan_id: L7-plan-registry-is-reference-filterplan
title: "L7-plan-registry-is-reference-filterplan: plan_registry に is_reference field 追加 + drift check filter (helix doctor advisory 54 件 root cause 修正)"
kind: troubleshoot
layer: L7
drive: be
status: draft
process_layer: L7
parent_process: HELIX-workflows/HELIX-process-L0-L14.md
parent_design: cli/lib/plan_registry.py
pairs_test_design:
  - cli/lib/tests/test_plan_registry.py
  - cli/lib/tests/test_doctor_plan_checks.py
is_reference: false
size: M
created_at: 2026-05-24
authors:
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — migration v36 + plan_registry.py + doctor_plan_checks.py 修正 + test 実装"
  - role: pmo-sonnet
    slot_label: "PMO — root cause 調査 / DoD review / drift 件数確認"
  - role: tl-advisor
    slot_label: "TL-advisor — schema 変更 adversarial check (Step 4)"
  - role: pm-advisor
    slot_label: "PM-advisor — scope escalation 判断 (on-demand)"
generates:
  - artifact_type: python_module
    artifact_path: cli/lib/migrations/v36_plan_registry_is_reference.py
  - artifact_type: python_module
    artifact_path: cli/lib/plan_registry.py
  - artifact_type: python_module
    artifact_path: cli/lib/doctor_plan_checks.py
  - artifact_type: test
    artifact_path: cli/lib/tests/test_plan_registry.py
  - artifact_type: test
    artifact_path: cli/lib/tests/test_doctor_plan_checks.py
dependencies:
  requires: []
  blocks: []
---

## §0 PLAN concept (root cause)

### 現象

`helix doctor` 実行時、plan drift advisory (reason=missing_artifact) が 54 件表示される。
大半は旧 V1 PLAN (is_reference: true、commit f409c55 で一括 marking された 223 件) の
`generates` path に由来する。

### root cause 詳細

pmo-sonnet 調査 (本 session、commit 前) で判明した 3 層の連鎖:

```
① plan_registry table に is_reference column が存在しない
        ↓
② plan_generates table には V1 PLAN の generates 行が登録済み
        ↓
③ run_check_plan_drift() の SQL が plan_registry.is_reference で除外 JOIN できない
        ↓
④ is_reference=true の V1 PLAN generates path が全て drift check 母集団に含まれる
        ↓
⑤ V1 PLAN generates は将来補充する意図がない (superseded / V2 命名で書き直し)
        ↓
結果: missing_artifact advisory 54 件 (大半が is_reference PLAN 由来のノイズ)
```

### 既存の部分対策 (doctor_plan_checks.py)

`run_check_vmodel_lint()` / `run_check_impl_process_layer()` はすでに
frontmatter.get("is_reference") == True のとき skip する実装が存在する (line 264〜280 / 315〜328)。

しかし `run_check_plan_drift()` (line 105〜166) は plan_generates JOIN のみ参照し、
`is_reference` 除外が未実装 → 本 PLAN で解消する。

### 修正方針

- **SQL JOIN で除外** を正本とする: `plan_registry.is_reference = 1` を `WHERE NOT` 条件に追加
- schema 拡張 (migration v36): `plan_registry` に `is_reference INTEGER NOT NULL DEFAULT 0` を additive 追加
- `plan_registry.py` upsert: frontmatter `is_reference: true` 値を column に書き込み
- `doctor_plan_checks.py` `run_check_plan_drift()`: SQL に `WHERE (r.is_reference IS NULL OR r.is_reference = 0)` を追加

---

## §1 工程表 (7 step)

| Step | 担当 | 内容 | 受入条件 |
|------|------|------|---------|
| 1 | PMO | ✅ done root cause 確認 + scope 承認 | 本 PLAN 内容に齟齬なし |
| 2 | SE | migration v36 設計 (additive、idempotent) | CURRENT_SCHEMA_VERSION = 36 |
| 3 | SE | plan_registry.py upsert 修正 | is_reference 値を column に書き込み |
| 4 | TL-advisor | adversarial check | P0 指摘 0 件で proceed |
| 5 | SE | ✅ done doctor_plan_checks.py `run_check_plan_drift()` 修正 | SQL 変更 + test 3 件新規 |
| 6 | PMO | ✅ done helix doctor 検証 | drift advisory 54 → 大幅減 (≤10 件目標) |
| 7 | PM | commit + push | pytest 全 PASS / helix doctor warn 減少確認 |

実装メモ (2026-05-24): 実 DB schema に `plan_registry.is_reference` column が未存在だったため、
TASK_INPUT の分岐条件に従い migration 追加ではなく frontmatter parse fallback で
`is_reference: true` PLAN を drift check 母集団から除外した。

**Entry 条件**: 本 PLAN review 完了、SE slot 割当

**Exit 条件 (DoD)**:
- migration v36 apply 後 plan_registry.is_reference column が存在する
- helix doctor drift advisory が 54 → 大幅減 (is_reference: true 除外分)
- pytest 新規 3 test PASS + 既存 plan_registry / doctor test 全 PASS
- plan_validator warnings 0

---

## §2 実装計画

### §2.A migration v36 設計

**ファイル**: `cli/lib/migrations/v36_plan_registry_is_reference.py`

```python
CURRENT_SCHEMA_VERSION = 36

def migrate_v35_to_v36(conn: Connection) -> None:
    """plan_registry に is_reference column を additive 追加。"""
    # additive: column 不在時のみ追加、既存 row は DEFAULT 0 (active PLAN) で保持
    conn.execute("""
        ALTER TABLE plan_registry
        ADD COLUMN is_reference INTEGER NOT NULL DEFAULT 0
    """)
    # INDEX: is_reference=0 の active PLAN を高速 filter
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_plan_registry_is_reference
        ON plan_registry(is_reference)
    """)
    conn.execute(
        "INSERT OR REPLACE INTO schema_version(version) VALUES (?)",
        (CURRENT_SCHEMA_VERSION,)
    )
```

**注意点**:
- SQLite は `ALTER TABLE ADD COLUMN` が既存 row の DEFAULT を即時適用する → 既存 active PLAN に 0 が入り安全
- idempotent 確保: column 存在確認 (`PRAGMA table_info(plan_registry)`) を migrate 関数の先頭で行う
- `schema_version` table 更新は既存 migration pattern に準拠 (v35_plan_registry.py 参照)

### §2.B plan_registry.py upsert 修正

**ファイル**: `cli/lib/plan_registry.py`

対象: `upsert_plan()` 関数 (または `bulk_import()` 内の INSERT/REPLACE 文)

変更内容:
```python
# frontmatter から is_reference 値を取得
is_reference = 1 if frontmatter.get("is_reference") is True else 0

# INSERT OR REPLACE 文に is_reference column を追加
conn.execute("""
    INSERT OR REPLACE INTO plan_registry (
        plan_id, title, kind, layer, drive, status, size, owner,
        related_adr, frontmatter_json, doc_path, is_reference,
        created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
""", (..., is_reference, ...))
```

**保守ルール**:
- `is_reference` が frontmatter に存在しない PLAN は `0` (active) とする
- `is_reference: false` 明示も `0` とする
- 既存 test が壊れないよう、INSERT 文の column 順と VALUES を一致させる

### §2.C doctor_plan_checks.py run_check_plan_drift() 修正

**ファイル**: `cli/lib/doctor_plan_checks.py`

**変更前 SQL** (line 113〜125):
```sql
SELECT
    g.plan_id,
    g.artifact_path,
    g.artifact_type,
    p.status,
    p.updated_at
FROM plan_generates AS g
LEFT JOIN plan_registry AS p ON p.plan_id = g.plan_id
ORDER BY g.plan_id, g.artifact_path
```

**変更後 SQL**:
```sql
SELECT
    g.plan_id,
    g.artifact_path,
    g.artifact_type,
    p.status,
    p.updated_at
FROM plan_generates AS g
LEFT JOIN plan_registry AS p ON p.plan_id = g.plan_id
WHERE (p.is_reference IS NULL OR p.is_reference = 0)
ORDER BY g.plan_id, g.artifact_path
```

**設計判断**:
- `LEFT JOIN` を維持 (plan_generates に plan_registry 登録なし行を含む現行仕様保護)
- `p.is_reference IS NULL` で plan_registry 未登録 PLAN (LEFT JOIN の NULL 行) を通過させる
  - 未登録 PLAN は active 扱い → 既存の warning 検出を維持
- `p.is_reference = 0` で active PLAN のみ drift check 対象
- `p.is_reference = 1` (V1 PLAN、is_reference: true) は除外 → missing_artifact advisory から除去

**migration v36 未適用環境 (is_reference column 不在) への対応**:
- `_table_names()` と同様の pattern で `PRAGMA table_info(plan_registry)` を確認
- column 不在時は従来 SQL (WHERE なし) にフォールバック + warning 1 件を results に追加

### §2.D test 設計 (新規 3 件 + 既存回帰)

**新規テスト**:

```python
# test_plan_registry.py
def test_plan_registry_stores_is_reference_field():
    """is_reference: true の PLAN が is_reference=1 で登録されること。"""
    # GIVEN: is_reference=true の frontmatter
    # WHEN: upsert_plan() 実行
    # THEN: plan_registry.is_reference = 1

def test_plan_registry_stores_active_plan_as_not_is_reference():
    """is_reference: false (または未設定) の PLAN が is_reference=0 で登録されること。"""
    # GIVEN: is_reference 未設定の frontmatter
    # WHEN: upsert_plan() 実行
    # THEN: plan_registry.is_reference = 0

# test_doctor_plan_checks.py
def test_drift_check_excludes_is_reference_plans():
    """is_reference=1 の PLAN の generates が drift check 対象外になること。"""
    # GIVEN: plan_registry に is_reference=1 の PLAN + plan_generates に対応する generates 行
    # WHEN: run_check_plan_drift() 実行
    # THEN: 結果に is_reference=1 の plan_id が含まれない

def test_drift_check_includes_active_plans():
    """is_reference=0 (active) の PLAN は引き続き drift check 対象であること (regression)。"""
    # GIVEN: plan_registry に is_reference=0 の PLAN + plan_generates に generates 行
    # WHEN: run_check_plan_drift() 実行
    # THEN: 結果に is_reference=0 の plan_id が含まれる (warning or ok)

def test_drift_check_fallback_without_is_reference_column():
    """is_reference column 不在時に従来動作 (全件 check) にフォールバックすること。"""
    # GIVEN: plan_registry に is_reference column なし (migration 未適用 simulation)
    # WHEN: run_check_plan_drift() 実行
    # THEN: warning result に "missing_is_reference_column" reason が含まれる
```

**既存回帰確認対象**:
- `test_plan_registry.py` 内の全 upsert / bulk_import test
- `test_doctor_plan_checks.py` 内の既存 drift / vmodel / impl_process_layer check

---

## §3 成果物一覧

| artifact | path | 種別 |
|----------|------|------|
| migration v36 | `cli/lib/migrations/v36_plan_registry_is_reference.py` | 新規 python_module |
| plan_registry 修正 | `cli/lib/plan_registry.py` | 更新 python_module |
| doctor_plan_checks 修正 | `cli/lib/doctor_plan_checks.py` | 更新 python_module |
| テスト追加 | `cli/lib/tests/test_plan_registry.py` | 更新 test_code |
| テスト追加 | `cli/lib/tests/test_doctor_plan_checks.py` | 更新 test_code |

---

## §4 受入条件 / DoD (全件必須)

- [ ] `cli/lib/migrations/v36_plan_registry_is_reference.py` が存在し、CURRENT_SCHEMA_VERSION = 36
- [ ] migration apply 後: `PRAGMA table_info(plan_registry)` に `is_reference` column が存在
- [ ] `is_reference: true` の PLAN を upsert → `plan_registry.is_reference = 1`
- [ ] `is_reference` 未設定の PLAN を upsert → `plan_registry.is_reference = 0`
- [ ] `helix doctor` 実行後の drift advisory count: 54 → 10 件以下 (is_reference 除外分)
- [ ] pytest 新規 test 5 件 (plan_registry 2 件 + doctor_plan_checks 3 件) PASS
- [ ] 既存 plan_registry + doctor_plan_checks test 全 PASS (regression 0 件)
- [ ] `helix plan lint` / plan_validator warnings 0 件
- [ ] migration 未適用環境での fallback 動作確認 (column 不在 → 従来 SQL にフォールバック)

---

## §5 リスク評価

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| ALTER TABLE ADD COLUMN が既存 row の is_reference を誤設定する | 高 (active PLAN が drift check 除外) | DEFAULT 0 → 既存 row は active 扱い、migration テストで確認 |
| migration v36 適用前の環境で column アクセス失敗 | 中 (doctor crash) | `PRAGMA table_info` 確認 + fallback SQL で防御 |
| plan_generates の plan_id が plan_registry 未登録 (LEFT JOIN NULL) | 低 (従来と同じ warning) | WHERE 条件に `IS NULL` を含め通過させる |
| is_reference: false 明示 vs 未設定の区別 | 低 | 両方 0 扱いで統一、edge case test で保護 |
| 残 advisory 10 件以下の目標未達 | 低 (advisory 自体は V2 PLAN 起票で漸減) | is_reference 除外後の残件は V2 generates 補充 carry として別 PLAN 起票 |

---

## §6 後続 PLAN 候補

1. **helix doctor advisory level 細分化 (P0/P1/P2/P3)**: 残 advisory を severity 分類し、P0 のみ CI fail-close 対象にする
2. **plan_generates bulk cleanup**: is_reference=true PLAN の generates 行を plan_generates から物理削除 (disk 節約)
3. **pre-commit hook で plan_registry sync 強化**: PLAN doc Edit/Write 時に自動 upsert する PostToolUse hook 連携

---

## §7 進捗

| Sprint | 内容 | 状態 |
|--------|------|------|
| Sprint .1 | root cause 確認 + PLAN 起票 (本 §) | complete |
| Sprint .2 | migration v36 + plan_registry.py 修正 + test 2 件 | pending |
| Sprint .3 | doctor_plan_checks.py 修正 + test 3 件 | pending |
| Sprint .4 | TL-advisor adversarial check + 必要修正 | pending |
| Sprint .5 | helix doctor 検証 + commit + push | pending |

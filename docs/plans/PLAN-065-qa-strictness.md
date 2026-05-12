---
plan_id: PLAN-065
title: "PLAN-065（QA 強化: test 厳格化 + reviewer 切替 + regression baseline）"
status: finalized
created: 2026-05-12
author: "PM (Opus)"
priority: high
size: M
phases_affected: "cli/helix-plan (review CLI) / cli/lib/helix_db.py (regression baseline) / cli/templates/plan/*.yaml / docs/qa/criteria-2026.md"
parent_plan: null
acceptance:
  qa_reviewer:
    verification_commands: { command: "cli/helix plan review --id PLAN-063 --reviewer qa", expected: "exit 0、QA 観点 critique (test pyramid / coverage / regression baseline) を出力" }
  regression_baseline:
    verification_commands: { command: "sqlite3 .helix/helix.db 'SELECT COUNT(*) FROM test_baseline WHERE status=\"PASS\", expected: "≥ 1500 (shell 614 + pytest 1071 + bats 420 規模の baseline 取得)" }
  acceptance_template:
    verification_commands: { command: "grep -E 'test_pyramid|coverage_target|regression_baseline' cli/templates/plan/acceptance.yaml", expected: "3 必須 field が template 化されている" }
  criteria_doc:
    verification_commands: { command: "test -f docs/qa/criteria-2026.md && wc -l docs/qa/criteria-2026.md", expected: "200 行以上、QA gate / pyramid / coverage / regression baseline / skip discipline の 5 軸明文化" }
  v_model:
    verification_commands: { command: "sqlite3 .helix/helix.db 'SELECT name FROM sqlite_master WHERE type=\"table\" AND name IN (\"contract_entries\",\"code_index\",\"test_design_entries\",\"test_baseline\",\"design_review\")", expected: "5 table すべて存在 (V-model 4 layer + design_review)、PLAN ごとに gap query が動作" }
  design_review_pair_check:
    verification_commands: { command: "cli/helix gate G1 --pair-check requirement --plan-id PLAN-063 && cli/helix gate G2 --pair-check architecture --plan-id PLAN-063 && cli/helix gate G3 --pair-check detailed --plan-id PLAN-063 && cli/helix gate G4 --pair-check functional --plan-id PLAN-063", expected: "すべて exit 0 (G1/G2/G3/G4 各 layer の縦 + 横 review 両方 passed を機械確認)" }
finalized: 2026-05-12
---

# PLAN-065: QA 強化 — test 厳格化 + reviewer 切替 + regression baseline

## §1 背景 (ざる testing からの脱却)

PLAN-051 で bats-lite errexit fix 前は **67 件 hidden failure** が「全 PASS」として通っていた。
これは「テスト 全 PASS」の意味が曖昧 + 規律未整備の典型。直近 PLAN-052/053/054/055 で順次解消したが、
基準を pattern 化していないため再発リスク残存。

ユーザー指摘 2026-05-12: 「テストの基準がざるな感じがしてる」。

## §2 5 軸の QA 強化

### 軸 A: `helix plan review --reviewer qa` (CLI 新オプション)

現在 `helix plan review --id PLAN-NNN` は TL (5.5) 専属。
QA (5.5、`cli/roles/qa.conf`) 観点 critique を CLI から呼び出せるようにする。

```bash
helix plan review --id PLAN-063 --reviewer tl   # default、設計 critique
helix plan review --id PLAN-063 --reviewer qa   # 新規、テスト観点 critique
helix plan review --id PLAN-063 --reviewer both # 両方 (2 並列)
```

QA critique 観点:
- acceptance に test pyramid 比率 (Unit/Integration/E2E) があるか
- coverage 目標値 (≥80% など) が明示されているか
- regression baseline 接続が明記されているか
- skip annotation の discipline が遵守されているか
- E2E critical path が定義されているか

### 軸 B: PLAN acceptance template 強化 (test 規律必須化)

`cli/templates/plan/acceptance.yaml` に 3 必須 field 追加:

```yaml
acceptance:
  feature_X:
    verification_commands: ...
  test_pyramid:               # NEW
    unit_target: "≥80%"
    integration_target: "主要フロー全カバー"
    e2e_target: "critical path 100%"
  coverage_target:            # NEW
    new_files: "≥85%"
    modified_files: "前回比 ≥ 0pt (低下禁止)"
  regression_baseline:        # NEW
    previous_pass_count: "(自動取得: 前 commit の baseline)"
    current_fail_tolerance: "PASS→FAIL は判定 (a) 単発 fail (連続 < 3 回) かつ flaky 履歴あり (test_baseline 直近 5 件で 1 件以上 FAIL あり) → warning、(b) 連続 3 回 FAIL or 非 flaky → G4 fail-close。flaky 判定 = 直近 5 件で 1 件以上 FAIL (窓は全判定で統一)"
```

新規 PLAN draft 起票時、これら 3 field の存在を `helix plan lint` で機械検証。

### 軸 C: regression baseline DB (helix.db v20)

`test_baseline` テーブル新設:

```sql
CREATE TABLE test_baseline (
  id INTEGER PRIMARY KEY,
  commit_sha TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  suite TEXT NOT NULL,         -- shell / pytest / bats
  test_name TEXT NOT NULL,
  status TEXT NOT NULL,        -- PASS / FAIL / SKIP
  duration_ms INTEGER,
  skip_reason TEXT,
  UNIQUE (commit_sha, suite, test_name)
);
CREATE INDEX idx_baseline_suite_name ON test_baseline(suite, test_name);
CREATE INDEX idx_baseline_commit ON test_baseline(commit_sha);
```

実装:
- `cli/helix test` 完了時に hook で test_baseline に bulk insert (test 名 + status)
- 次回実行時、前回 baseline と diff:
  - PASS → FAIL: `current_fail_tolerance` ロジックで判定 (flaky 履歴は warning、3 連続 FAIL or 非 flaky のみ G4 fail-close)
  - FAIL → PASS: improvement、ログのみ
  - 新規 PASS: ベースライン追加
- `helix qa baseline diff --base HEAD~1` で前回比表示

**regression 判定ルールは current_fail_tolerance (line 71) の 1 箇所に統一**。本 PLAN 内に「即時 fail-close」記述は他にない。

### 軸 D: skip annotation discipline

現状 skip annotation は理由 free-text。これを構造化:

```python
@pytest.mark.skip(reason="HELIX-SKIP: <category> | <PLAN-NNN> | <due_date: 2026-MM-DD>")
```

- category: env_dependent / bats_lite_limit / external_blocker / migration_pending
- PLAN-NNN: 解消予定 PLAN ID
- due_date: skip 期限 (>30 日経過で G6 警告)

linter: `cli/lib/skip_annotation_linter.py` が全 skip を scan、不適合は G4 fail-close。

### 軸 E: QA criteria 正本 (`docs/qa/criteria-2026.md`)

「テストがざるでない」最低条件を明文化、200+ 行:

- ピラミッド比率 (Unit 70% / Integration 20% / E2E 10%)
- coverage 目標 (新規 ≥85% / 修正 前回比 0pt 低下禁止)
- regression baseline 接続必須
- skip discipline (4 category + 期限 + PLAN ID)
- E2E critical path 定義 (各 PLAN で acceptance に明示)
- 性能テスト (perf role が L6 で実施、baseline + 5% 以内)
- セキュリティテスト (security role が G2/G4/G6 で 3 段階)

各 PLAN の test acceptance はこの criteria を満たすことが G4 通過条件。

## §2.5 HELIX-V model 構造 (ユーザー指示 2026-05-12) — 工程粒度 5-level

HELIX 工程と V-model 5 設計層 / 5 テスト層を 1:1 対応させる。

```
                       HELIX 工程 × V-model 5-level
                       ───────────────────────────

[企画 / PLAN goal] design_level=planning        ←─→  [L11 運用学習]         test_level=operational          運用テスト
            │
[L1 要件定義]     design_level=requirement      ←─→  [L8 受入]              test_level=acceptance           受入テスト
            │
[L2 基本設計]     design_level=architecture     ←─→  [L6 統合検証]          test_level=system_integration  統合テスト
            │
[L3 詳細設計]     design_level=detailed         ←─→  [L6 統合検証]          test_level=integration          結合テスト
            │
[L4 機能設計]     design_level=functional       ←─→  [L4 実装内]            test_level=unit                 単体テスト
            ↓                                                                  ↑
       code_index (実装 symbol)  ───[L4 code review = V の底 apex]───→  test_baseline (実行結果 + coverage)
```

**V の底 apex = L4 code review (dual-target)**: 左脚 (機能設計) と右脚 (単体テスト) を結節する verification step。**実装コード + テストコード の両方を review 対象**。
- 既存 `helix-codex` TL review を **code review** として `invocation_log.type='code_review'` で記録
- review scope: (a) code_index (実装 symbol)、(b) 対応 test ファイル (テストコード自体)。テストにもバグが入るため両方必須
- 各 L4 sprint で code review 必須化、record 無し L4 は G4 fail-close
- contract_entries (functional) → code_index → test_baseline (unit) chain を review が確認、3 層 traceability を担保

### 縦レビュー / 横レビュー (2 軸検査による V 進行)

各 phase の通過条件 = **縦レビュー + 横レビュー の両方 passed**。

| 軸 | 対象 | 確認内容 |
|---|---|---|
| **縦レビュー** | 同脚内の隣接 layer (設計連鎖) | 上位 layer から brisk down が正しいか |
| **横レビュー** | 同 phase の 設計 ↔ テスト ペア (V 対角線) | 設計と対応テストレベルの 1:1 対応 |

各 gate 評価:

| Phase / Gate | 縦レビュー | 横レビュー |
|---|---|---|
| G1 (要件完了) | planning → requirement | requirement ↔ acceptance test |
| G2 (設計凍結) | requirement → architecture | architecture ↔ system_integration test |
| G3 (実装着手) | architecture → detailed | detailed ↔ integration test |
| G4 (実装凍結) | detailed → functional + L4 code review apex | functional ↔ unit test |
| G11 (運用学習) | functional → operational metric | planning ↔ operational test |

### `design_review` テーブル (V-graph record)

```sql
CREATE TABLE design_review (
  id INTEGER PRIMARY KEY,
  plan_id TEXT NOT NULL,
  layer TEXT NOT NULL,          -- planning/requirement/architecture/detailed/functional
  review_axis TEXT NOT NULL,    -- vertical / horizontal
  source_layer TEXT,            -- 縦: 上位 layer / 横: paired test_level
  target_id INTEGER,            -- contract_entries.id or test_design_entries.id
  reviewed_at TEXT NOT NULL,
  reviewer TEXT NOT NULL,       -- codex_tl / codex_qa / opus / human
  verdict TEXT NOT NULL,        -- passed / changes_required / blocked
  raw_findings TEXT
);
CREATE INDEX idx_design_review_plan ON design_review(plan_id, layer, review_axis);
```

### 個別整合性チェック (each gate)

各 gate runner は対応する縦 + 横 review record の存在を 2 軸とも確認 (一括検査ではなく phase 単位):

```sql
-- G2 通過条件 (architecture layer)
SELECT
  EXISTS(SELECT 1 FROM design_review WHERE plan_id=? AND layer='architecture' AND review_axis='vertical' AND verdict='passed') AS vertical_ok,
  EXISTS(SELECT 1 FROM design_review WHERE plan_id=? AND layer='architecture' AND review_axis='horizontal' AND verdict='passed') AS horizontal_ok;
```

両方 true で G2 通過、片方 false なら fail-close。`helix gate G<N> --pair-check <layer>` で個別実行可能。

**完全 V-graph**: HELIX 11 phase + 底 apex code review (impl + test 両 review) + 縦 5 軸 + 横 5 軸 = HELIX 全工程 traceability。

設計層 5 値 (planning / requirement / architecture / detailed / functional) × テスト層 5 値 (operational / acceptance / system_integration / integration / unit) を 1:1 paired_design_level で結合し、SQL 1 発で**工程ごとのテスト整合**を網羅検査。

**HELIX gate 接続 (5-level paired)**
- G0.5 / G11 (運用学習): planning ↔ operational ペア。本番影響の最終 KPI 検査
- G1 (要件完了) / L8 (受入): requirement ↔ acceptance ペア。受入条件と機能の対応
- G2 (設計凍結) / G6 (RC 判定): architecture ↔ system_integration ペア
- G3 (実装着手) / G6 (RC 判定): detailed ↔ integration ペア
- G4 (実装凍結): functional ↔ unit ペア。実装と単体テストの 1:1 対応

contract_entries / code_index / test_design_entries / test_baseline の 4 table を統一スキーマで結合し、SQL 1 発で**工程ごとのテスト整合**を網羅検査する。

### 新規 table: test_design_entries (V-model 5-level 対応)

```sql
CREATE TABLE test_design_entries (
  id INTEGER PRIMARY KEY,
  plan_id TEXT NOT NULL,
  acceptance_key TEXT NOT NULL,                                                  -- PLAN.yaml の acceptance.<key>
  contract_id INTEGER,                                                            -- FK -> contract_entries.id (横軸 link)
  test_level TEXT NOT NULL CHECK (test_level IN
    ('operational','acceptance','system_integration','integration','unit')),     -- V-model 5 値
  paired_design_level TEXT NOT NULL CHECK (paired_design_level IN
    ('planning','requirement','architecture','detailed','functional')),          -- 横レビュー対ペア (1:1)
  pyramid_layer TEXT NOT NULL,                                                    -- unit / integration / e2e (test pyramid 比率算出用)
  test_target TEXT,                                                               -- 想定テスト名 or pattern
  expected_status TEXT NOT NULL,                                                  -- required / optional / skip-ok
  created_at TEXT NOT NULL,
  UNIQUE (plan_id, acceptance_key, test_level)
);
CREATE INDEX idx_test_design_plan ON test_design_entries(plan_id);
CREATE INDEX idx_test_design_contract ON test_design_entries(contract_id);
CREATE INDEX idx_test_design_levels ON test_design_entries(test_level, paired_design_level);

-- contract_entries に design_level を追加 (V-model 5-level の左脚)
ALTER TABLE contract_entries ADD COLUMN design_level TEXT NOT NULL DEFAULT 'detailed'
  CHECK (design_level IN ('planning','requirement','architecture','detailed','functional'));
CREATE INDEX idx_contract_design_level ON contract_entries(design_level);
```

paired_design_level ↔ test_level の 5 ペア:
- planning ↔ operational
- requirement ↔ acceptance
- architecture ↔ system_integration
- detailed ↔ integration
- functional ↔ unit

### 軸 C test_baseline schema 拡張

```sql
-- 既存 (PLAN-065 §2 軸 C) に列追加:
ALTER TABLE test_baseline ADD COLUMN code_entry_id INTEGER;       -- 実装 ↔ カバレッジ link
ALTER TABLE test_baseline ADD COLUMN test_design_id INTEGER;      -- テスト設計 ↔ 実行 link
CREATE INDEX idx_baseline_code_entry ON test_baseline(code_entry_id);
CREATE INDEX idx_baseline_test_design ON test_baseline(test_design_id);
```

### V-model SQL クエリ例

```sql
-- 設計はあるがテストが無い項目 (左上 → 右上のギャップ)
SELECT c.id, c.source_path FROM contract_entries c
  LEFT JOIN test_design_entries t ON t.contract_id = c.id
  WHERE t.id IS NULL;

-- 実装はあるがカバレッジが無い symbol (左下 → 右下のギャップ)
SELECT e.id, e.path, e.symbol_line FROM code_index e
  LEFT JOIN test_baseline b ON b.code_entry_id = e.id
  WHERE b.id IS NULL AND e.bucket = 'coverage_eligible';

-- テスト設計はあるが実行されていない (右上 → 右下のギャップ)
SELECT td.id, td.plan_id FROM test_design_entries td
  LEFT JOIN test_baseline b ON b.test_design_id = td.id
  WHERE b.id IS NULL;

-- 全 4 layer 整合 (健全な PLAN)
SELECT c.source_path, e.path, td.acceptance_key, b.status
  FROM contract_entries c
  JOIN code_index e ON e.path LIKE c.source_path||'%'
  JOIN test_design_entries td ON td.contract_id = c.id
  JOIN test_baseline b ON b.test_design_id = td.id
  WHERE c.id = ?;
```

### V-model 整備のメリット

- **設計欠落検知 (G2)**: PLAN.yaml acceptance に対応する contract_entries が無い → G2 (設計凍結) fail-close
- **テスト設計欠落検知 (G3)**: contract_entries 定義済だが test_design_entries に対応無し → G3 (実装着手) fail-close。テスト設計は実装前に必須
- **実装欠落検知 (G4)**: contract_entries 定義済だが code_index に該当 symbol 無し → G4 (実装凍結) fail-close。G3 時点は実装未着手前提なので fail-close 対象外
- **カバレッジ欠落検知 (G4)**: code_index (coverage_eligible) だが test_baseline で実行履歴無し → G4 fail-close
- **回帰検知 (G4)**: 軸 C current_fail_tolerance のロジックに従い、(a) 単発 fail + flaky 履歴 → warning、(b) 3 連続 FAIL or 非 flaky → G4 fail-close。即時 fail-close 条件は記述しない
- **カバレッジ低下検知**: 前 commit と比較し coverage% が -1pt 以上低下 (test status 変化ではなく coverage 値 diff) → G4 fail-close。regression (status 変化) は別判定 (current_fail_tolerance)
- **PLAN ごとの V-model 整合度スコア化**: 4 layer すべて埋まっている率 = QA 健全性 KPI

PLAN-063 軸 10 relation graph はこの V-model を mermaid で可視化する dashboard を提供する。

## §3 Sprint 構成 (7 Sprint、size=M)

| Sprint | 内容 | 委譲先 |
|---|---|---|
| W-0 | draft + TL R1 + QA R1 + finalize | PM |
| W-1 | 軸 A: `helix plan review --reviewer qa` 実装 | PG medium |
| W-2 | 軸 C: helix.db v20 test_baseline + **test_design_entries** schema (V-model 統合) + record hook + diff CLI | SE high |
| W-3 | 軸 D: skip annotation linter + acceptance.yaml template 強化 | PG medium |
| W-4 | 軸 E: docs/qa/criteria-2026.md 起草 (200+ 行) | docs / 5.4 |
| **W-5** | **§2.5 V-model 中核実装: design_review table 新規 + `helix gate G<N> --pair-check <layer>` 5 phase 縦/横 record + L4 code review apex (impl + test dual-target)** | **SE high** |
| W-final | 統合検証 + retro + push | Opus |

**並列可否 (W-2 schema が前提依存元)**:
- W-1 (reviewer CLI、QA conf 利用): W-2 非依存、W-0 finalize 後即可
- W-2 (helix.db v20 schema): 全 V-model 関連 Sprint の前提、最優先
- W-4 (criteria 文書): W-2 非依存、W-0 finalize 後即可
- W-3 (skip linter + acceptance template): W-2 後 (acceptance template が v20 schema 由来 field を含むため)
- W-5 (design_review table + pair-check): W-2 後 (design_review schema を v20 に統合するため)

正確な依存:
- W-0 完了後: W-1 ∥ W-2 ∥ W-4 (3 並列)
- W-2 完了後: W-3 ∥ W-5 (2 並列)
- 全完了後 W-final 統合

## §4 PLAN-063 軸 11 との関係

PLAN-063 軸 11 Regression detection と一部 overlap。責務分離:
- PLAN-063 軸 11: detector としての runtime 監視 (CLI invocation + observe + accuracy 集計)
- PLAN-065: QA gate / review / acceptance template / regression baseline DB / criteria 正本

PLAN-065 が **規律と基準**、PLAN-063 軸 11 が **検知の自動化**。両者は test_baseline テーブルを共有する (PLAN-065 W-2 で schema 作成、PLAN-063 軸 11 で detector が活用)。

## §5 Out of Scope

- 各 PLAN への retroactive test 追加 (本 PLAN は基盤、既存 PLAN への遡及適用は別 PLAN)
- 性能 baseline (perf role の責務、別 PLAN carry)
- セキュリティ scan の体系化 (security role / OWASP は PLAN-066 候補)
- 自動テスト生成 (LLM 経由のテスト code 起草、別 PLAN carry)

## §6 リスク

- **既存 PLAN への影響**: acceptance template 強化で過去 PLAN 64 件すべてが「不適合」扱い → grace period 設定 (新規 PLAN のみ強制、既存は warning)
- **regression baseline の偽陽性**: flaky test が PASS→FAIL→PASS で振動 → 3 連続 FAIL のみ regression 判定
- **skip annotation 移行コスト**: 67 件 skip すべてに category + PLAN ID 付与必要 → W-3 で bulk migration script 提供
- **QA reviewer の余計な厳しさ**: 既存 PLAN を片っ端から reject する可能性 → grace period + threshold opt-in

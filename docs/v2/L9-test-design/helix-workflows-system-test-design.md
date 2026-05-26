---
doc_id: l9-helix-workflows-system-test-design
title: "HELIX-workflows V2 総合テスト設計 (system test design)"
status: skeleton
created: 2026-05-27
owner: PM
process_layer: L9
pairs_design: docs/v2/L4-architecture/helix-workflows-system-architecture.md
parent_plan: L4-helix-workflows-方式設計plan
industry_standards:
  - IEEE 829-2008 (test documentation)
  - ISO/IEC/IEEE 29119-3 (test design)
---

# HELIX-workflows V2 総合テスト設計 (system test design)

## §0 概要

本 doc は `docs/v2/L4-architecture/helix-workflows-system-architecture.md` と 1 対 1 で trace する L9 総合テスト設計本体化版です。L4 §1-§7 と ST-1〜ST-7 を双方向で 1 対 1 対応させ、BR-01 から BR-12 の業務要件を実行設計へ落とし込みます。

テスト完了条件は、観点・入力・期待結果・検証コマンド・DoD を持たせ、`implementation_status` を用いた監査証跡の欠落防止を担保します。失敗時は partial-pass ではなく fail-close ルートに切り分けます。

ST-1〜ST-7 は各 L4 章と固定対応し、`→ pair: L4 §X` 行を本文末尾に付与します。

## §1 総合テスト方針 (E2E + 機能横断 + システム全体 + 非機能境界)

### 1.1 テスト全体方針

- E2E: L4 方式設計、PLAN 起票、AI agent 配線、hook、helix.db、CI を通した観点で実行し、dogfooding 起点から受入まで再現する。
- 機能横断: PLAN/ADR/CLI/skills/handover の境界越えを同一シナリオで検証する。
- システム全体: L8 結合テスト完了を入場条件にして L10 へ繋がる全行程の整合を確認する。
- 非機能境界: 性能、セキュリティ、信頼性、保守性の 4 軸を 4.1〜4.4 に明確化する。

### 1.2 L8 依存条件（Entry 条件）

L9 は以下を満たした時点で実行する。

| 条件 | 判定コマンド | 判定値 | 判定結果 |
|---|---|---|---|
| L8 依存テスト完了 | ``helix doctor --phase L8 --json`` | `integration_complete=true` | pass / fail |
| pair freeze 最低値 | ``helix doctor --check-pair-freeze --phase L9`` | `balance_ratio >= 1.0` | pass / fail |
| hook fast-path 設定 | `cat .github/workflows` / `pre-commit config` | `helix doctor` 組込 | pass / fail |
| 4 artifact 条件 | ``helix doctor --check-4-artifact --json`` | 4 artifact 検出数 4 | pass / fail |

### 1.3 fail-close と partial-pass

- fail-close: BR-RULE-09、BR-RULE-12、監査証跡欠落、`parent_design` 欠如、`pairs_test_design` 欠如、`changeprop read/write` 混線。
- partial-pass: 一時未実施の非機能値を carry 化し、次回ステップで再実行条件を明示。

| fail-close 例 | stop 条件 | 再開条件 |
|---|---|---|
| mandatory subagent 不起動 | hook 実行直後に missing mandatory | すべて mandatory 起動済み |
| G2/G4 監査欠落 | doc-reviewer/tl/pmo evidence 欠如 | 3 エビデンス揃い |
| 監査 DB 欠損 | helix.db への event 未登録 | event と YAML の一致 |

### 1.4 §1 ST 配置の全体規則

- ST-1 は L4 §1 と固定対応。
- ST-2 は L4 §2 と固定対応。
- ST-3 は L4 §3 と固定対応。
- ST-4 は L4 §4 と固定対応。
- ST-5 は L4 §5 と固定対応。
- ST-6 は L4 §6 と固定対応。
- ST-7 は L4 §7 と固定対応。

### 1.5 実装境界

- `tests/fixtures/l9/` 配下に各 ST フィクスチャを置く。
- 監査 command は実行ログを `.helix/audit/l9-system-test-*.yaml` に保存。
- `implementation_status` 列は最低 5 件以上出現させる。

→ pair: L4 §0

## §2 テスト項目 ST-1〜ST-7

### ST-1 三層構造稼働 (pair: L4 §1)

- **観点**: `HELIX-workflows / cli / skills` の三層構造が逆参照なしで成立し、cross-layer access の整合が取れていること。
- **観点補助**: ST-1 は `L4 architecture` の §1 と BR-01, BR-07, BR-10 に対応し、ST-1 固有の障害は `parent_design` ではなく `architecture` 側で止める。
- **入力 / fixture**: `tests/fixtures/l9/st-1/three-layer-map.yaml`, `tests/fixtures/l9/st-1/layer-events.json`, `docs/v2/L4-architecture/helix-workflows-system-architecture.md`
- **期待結果**: skills が cli の直接 entrypoint を呼ばず、cli のみが明示許可経路経由で実行される。
- **検証コマンド**:
  ```bash
  helix doctor --check-layer-separation --phase L9 --json
  python -m pytest tests/unit/l9/test_layer_separation.py -q
  ```
- **DoD**:
  - 終了コード 0
  - 3 層 access 破綻ログ 0 件
  - `helix.db` の 3-layer event が 2 以上登録
  - `cross_layer_violation_count = 0`
- **implementation_status**: partial
- **追加 notes**: ST-1 は同時に ST-1, ST-5, ST-7 の前提を担保する。ST-1 の `cross_layer` 検証が fail の場合、pair trace は fail-close。

→ pair: L4 §1

### ST-2 V-model 4 artifact 機械検出 (pair: L4 §2)

- **観点**: PLAN, ADR, 設計/実装/テストの 4 artifact が双方向で trace され、欠損が検知されること。
- **観点補助**: ST-2 は BR-02 と BR-RULE-05 を同時検査し、`plan_validator` 側の不整合と plan doc 側不整合を別建てで検知する。
- **入力 / fixture**: `tests/fixtures/l9/st-2/adversarial-docs.yaml`, `docs/plans/L4/L4-helix-workflows-方式設計plan.md`, `docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md`
- **期待結果**:
  - plan から ADR までの 4 artifact 双方向 trace が成立
  - adversarial 追加時に欠損を fail-close で捕捉
  - pair-freeze が 1.0 以上
- **検証コマンド**:
  ```bash
  helix doctor --check-4-artifact --json
  helix doctor --check-pair-freeze --pair L4-L9
  ```
planned (L7 実装スプリントで CLI flag 実装、現在は L4 設計のみ)
- **DoD**:
  - JSON `4_artifact_detected` true
  - `missing_artifacts = 0`
  - `pair_freeze_ratio >= 1.0`
  - adversarial fail ありでも 1 回目で exit code != 0
- **implementation_status**: planned
- **実装メモ**: ST-2 は BR-02, BR-05, BR-12 の 3 視点にまたがる。

→ pair: L4 §2

### ST-3 技術スタック整合 (pair: L4 §3)

- **観点**: Python, Bash, SQLite, Codex CLI, Claude Code の実行環境が許容バージョンと起動経路で整合していること。
- **観点補助**: ST-3 は BR-03 と BR-07 の runtime 条件を固定し、subagent の許可モデル（12 種）整合を保証。
- **入力 / fixture**: `.tool-versions`, `tests/fixtures/l9/st-3/version-matrix.yaml`, `tests/fixtures/l9/st-3/subagent-whitelist.json`
- **期待結果**:
  - バージョン不一致による起動失敗が 0
  - 12 種 subagent role 許可済み
  - SQLite schema と DB path が実行時と監査時で一致
- **検証コマンド**:
  ```bash
  python --version
  bash --version | head -n 1
  sqlite3 --version
  jq '.allowed_roles | length' tests/fixtures/l9/st-3/subagent-whitelist.json
  ```
- **DoD**:
  - `allowed_roles = 12`
  - `version_lock_mismatch = 0`
  - DB ファイル読み取り・書込み可能状態
- **implementation_status**: partial
- **補足**: ST-3 を fail すると ST-4 の read/write 判定や ST-5 の mandatory 発火が再現しない。

→ pair: L4 §3

### ST-4 BR-12 ratchet 機構 E2E (pair: L4 §4)

- **観点**: `helix doctor --check-changeprop` の read-only と write 更新分離、baseline 永続化、違反 yaml の蓄積、2 段 hook の fail-close を同時確認する。
- **観点補助**: ST-4 は BR-12、BR-RULE-01、BR-RULE-12 を横断し、P2-A3 の security 例外と区別する。
- **入力 / fixture**: `tests/fixtures/l9/st-4/ratchet-baseline.yaml`, `tests/fixtures/l9/st-4/ratchet-violations.yaml`, `.helix/audit/changeprop-violations.yaml`
- **期待結果**:
  - read-only 実行時に state file が更新されない
  - write 実行時に `baseline` が更新
  - pre-commit fast と CI deep のどちらか、または両方で fail-close ロジックが成立
- **検証コマンド**:
  ```bash
  helix doctor --check-changeprop --baseline tests/fixtures/l9/st-4/ratchet-baseline.yaml
  helix doctor --check-changeprop --update tests/fixtures/l9/st-4/ratchet-violations.yaml
  pre-commit run -a
  python -m pytest tests/integration -k ratchet -q
  ```
- **DoD**:
  - read-only 実行後 `update_count = 0`
  - write 実行後 `baseline_updated=true`
  - 少なくともどちらかの hook が fail 時 exit != 0
  - 違反 yaml 追加の `changed=1`
  - planned (L7 実装スプリントで CLI flag 実装、現在は L4 設計のみ)
- **implementation_status**: planned
- **補足**: ST-4 は ST-4 と ST-6 から参照される重要監査線であり、失敗時は即時 carry 化する。

#### AC-12〜AC-16 対応表

| AC | 入力 | 期待結果 | 検証手段 | DoD |
|---|---|---|---|---|
| AC-12 | 新規 PLAN 起票時の BR/FR/NFR/AC 増分 | balance_ratio drift なし | `helix doctor --check-changeprop` (planned) で parser ベース検証 | ratio >= 1.0 全 pair |
| AC-13 | NFR 追加時の AC-NFR 同期 | AC-NFR 自動拡張 | parser で frontmatter 解析 (planned) | NFR/AC-NFR 対応 >= 1.0 |
| AC-14 | doc-reviewer evidence 不在 | G ゲート fail-close | audit YAML 検証 (planned) | evidence 100% |
| AC-15 | 既存資産 retrofit | Strangler Fig 各 stage 完遂 | manifest diff (planned) | manifest 100% |
| AC-16 | mandatory subagent 不在 | helix.db で missing 検出 | `helix agent fire-mandatory` (現状 fail-close なし、planned) | missing 0 |

- 追加 fixture: `tests/fixtures/l9/st-4/grep_false_positive.md` を parser で検証対象化する。

→ pair: L4 §4

### ST-5 mandatory subagent 自動発火 (pair: L4 §5)

- **観点**: 各 phase entry で mandatory subagent を強制起動し、helix.db に audit event が残ること。
- **観点補助**: ST-5 は BR-05（pair freeze）と BR-07（AI 配線）と関連し、entry hook から vmodel-semantics の読み込み漏れを検知する。
- **入力 / fixture**: `tests/fixtures/l9/st-5/mandatory-phases.yaml`, `tests/fixtures/l9/st-5/lx-entry-context.json`, `vmodel-semantics.yaml`
- **期待結果**:
  - `helix agent fire-mandatory --phase Lx` が成功
  - mandatory event が helix.db 記録
  - 記録と evidence yaml のキー一致
- **検証コマンド**:
  ```bash
  helix agent fire-mandatory --phase L4
  helix agent fire-mandatory --phase L9 --json
  sqlite3 helix.db "SELECT phase,agent_role,event_status FROM audit_events WHERE phase IN ('L4','L9') ORDER BY created_at DESC;"
  ```
- **DoD**:
  - mandatory event 2 件以上
  - `missing_mandatory_count = 0`
  - event_id と evidence_id の対応一致率 1.0
- **implementation_status**: partial
- **補足**: ST-5 は ST-6 の evidence 先行条件。

→ pair: L4 §5

### ST-6 二重/三重 audit pattern 稼働 (pair: L4 §6)

- **観点**: tl-advisor, pmo-sonnet, doc-reviewer を同一テスト対象で証跡化し、いずれか欠ければ fail-close すること。
- **観点補助**: ST-6 は G2 / G4 エントリでの監査不在を防ぐため、BR-RULE-11 と BR-RULE-09 を確認。
- **入力 / fixture**: `tests/fixtures/l9/st-6/audit-seeds.yaml`, `.helix/audit/doc-reviewer-evidence.yaml`, `tests/fixtures/l9/st-6/evidence-schema.json`
- **期待結果**:
  - 3 種 evidence いずれか欠ける場合 fail-close
  - YAML と DB の event_id が一致
- **検証コマンド**:
  ```bash
  helix codex --role tl-advisor --task "L9 ST-6 audit smoke test" --plan-only
  helix codex --role doc-reviewer --task "L9 ST-6 evidence smoke" --plan-only
  helix claude --role pmo --model sonnet --execute --task "L9 ST-6 mandatory review smoke"
  ```
- **DoD**:
  - evidence YAML count = 3
  - db rows = evidence keys 数
  - 欠損時は `review_blocked=true`
- **implementation_status**: planned
- **補足**: ST-6 は監査ループ（3 重）を最低限維持するため、実行時ログを `.helix/audit/st-6.log` に保存。

→ pair: L4 §6

### ST-7 採用 project 配布 E2E (pair: L4 §7)

- **観点**: `helix init` 実行後の portable 配布状態を確認し、`.helix/`, `CLAUDE.md`, `.gitignore` を自動配布すること。
- **観点補助**: ST-7 は BR-09（既存資産整理）/BR-10（Strangler Fig）と紐づき、段階移行条件の検査を補助する。
- **入力 / fixture**: `tests/fixtures/l9/st-7/init-template-project/`, `tests/fixtures/l9/st-7/portable-matrix.csv`, `docs/v2/L4-architecture/helix-workflows-system-architecture.md`
- **期待結果**:
  - 配布先に `.helix/`, `CLAUDE.md`, `.gitignore` を作成
  - `portable_pack.enabled=true`
  - 事前の BR-09 / BR-10 参照が壊れていない
- **検証コマンド**:
```bash
  helix init --template tests/fixtures/l9/st-7/init-template-project
  helix db export-state --format json | jq '.portable_pack.enabled'
  test -f .helix/audit/doc-reviewer-evidence.yaml
  ```
planned (L7 実装スプリントで CLI flag 実装、現在は L4 設計のみ)
- **DoD**:
  - 必須ファイル 3 件存在
  - portable pack 状態 true
  - セッション再入時の再初期化で差分が収束
- **implementation_status**: planned
- **補足**: ST-7 は BR-10 の移行条件を満たすため、導入後に migration stage 反映を検証する。

→ pair: L4 §7

## §3 機能横断テスト

本節は BR-01 から BR-12 を連結し、ST-1〜ST-7 をまたぐ横断的な E2E を表現する。

### 3.1 BR 横断シナリオ表（5 件以上）

| シナリオ ID | 関与 BR | 期待結果 | 検証手順 | ST | implementation_status |
|---|---|---|---|---|---|
| XS-01 | BR-01, BR-05, BR-12 | plan 起票→失敗→修正→再起票で pair freeze ratio が回復 | 1) PLAN 起票 2) L4/L9 trace check 3) 修正 4) 再起票 | ST-2, ST-4, ST-5 | partial |
| XS-02 | BR-02, BR-05 | retro-fit stub 生成後に不足 artifact が解消 | 1) 既存 plan scan 2) 不足 stub 3) 再 scan | ST-2, ST-6 | partial |
| XS-03 | BR-04, BR-06 | 9 mode 到達と forward closure の記録 | 1) mode 変更 2) mode_transition 検証 | ST-1, ST-5 | partial |
| XS-04 | BR-07, BR-08 | mandatory subagent 3 名起動と helix.db 記録 | 1) fire mandatory 2) db event 監査 3) evidence 整合 | ST-5, ST-6 | partial |
| XS-05 | BR-09, BR-10 | 初回配布と dogfooding 起動が成功 | 1) helix init 2) portable package 検証 3) dogfooding 再起動 | ST-7, ST-1 | partial |
| XS-06 | BR-11, BR-12 | security / ratchet / hook fail-close を同時確認 | 1) hook fail パターン実行 2) evidence 監査 | ST-4, ST-6 | partial |
| XS-07 | BR-03, BR-04 | drift 発生時の recovery / normalization 切替 | 1) drift seed 追加 2) mode closure 監査 | ST-2, ST-3 | partial |

### 3.2 シナリオ自動実行スニペット

```python
from pathlib import Path
import json

fixtures = [
    Path("tests/fixtures/l9/st-1/three-layer-map.yaml"),
    Path("tests/fixtures/l9/st-2/adversarial-docs.yaml"),
    Path("tests/fixtures/l9/st-4/ratchet-violations.yaml"),
]
assert all(p.exists() for p in fixtures), f"Fixture missing: {fixtures}"

report = {"scenario_count": len(fixtures)}
print(json.dumps(report, ensure_ascii=False))
```

### 3.3 成果保存

- 実行結果を `.helix/audit/l9-cross-functional.yaml` に保存。
- 失敗ケースは scenario ID 単位で carry 化。
- 5 件以下にならないよう minimum 5 件を維持。

→ pair: L4 §2

## §4 非機能テスト (P2-A3 解消、本体化必須)

### §4.1 性能テスト

- **対象**: 実行時間・スループット・再現性
- **入力 / fixture**: `tests/fixtures/l9/perf/doctor-load.json`
- **観点**:
  - `helix doctor` 完走時間 <= 30 秒
  - plan_validator 完了時間 <= 5 秒
  - Codex 委譲平均 <= 60 秒
- **検証コマンド**:
  ```bash
  /usr/bin/time -p helix doctor > /tmp/doctor.time.log
  /usr/bin/time -p helix plan-validator docs/plans/L4/L4-helix-workflows-方式設計plan.md > /tmp/planvalidator.time.log
  /usr/bin/time -p python -m pytest tests/integration/test_delegate.py -k codex --count=5 > /tmp/codex.time.log
  ```
- **DoD**:
  - doctor p95 <= 30s
  - plan-validator p95 <= 5s
  - codex delegate p95 <= 60s
  - タイムログ欠損なし
- **implementation_status**: partial
- **補足**: benchmark は `.helix/audit/perf-metrics.json` に残す。

→ pair: L4 §4

### §4.2 セキュリティテスト

- **対象**: secret / credential / PII / OWASP Top 10（Injection, Broken Auth, Sensitive Data Exposure）
- **入力 / fixture**: `tests/fixtures/l9/security/pii-sample.csv`, `tests/fixtures/l9/security/adversarial-auth.txt`
- **観点**: gitleaks, trufflehog, pytest OWASP fixture の 3 重検査
- **検証コマンド**:
  ```bash
  gitleaks detect --source . --report-format json --exit-code 0
  trufflehog git file://. --json --since-commit HEAD~1
  python -m pytest tests/security/test_owasp_top10.py -q
  ```
- **DoD**:
  - 両検査の終了コード 0
  - 正常系で false positive 率 5% 以下
  - 検出行に対応する `audit_reason` が出力される
- **implementation_status**: partial
- **補足**: PII fixture は本番 secret を含まない擬似データを使用し、監査証跡のみ保存。

→ pair: L4 §6

### §4.3 信頼性テスト

- **対象**: hook fail-close, SessionStart fail-open, PreCompact block 決定
- **入力 / fixture**: `tests/fixtures/l9/reliability/hook-matrix.json`
- **観点**: pre-commit/CI いずれも失敗時の復旧可能性を観測
- **検証コマンド**:
  ```bash
  pre-commit run -a
  helix hook replay --event SessionStart --json
  helix hook replay --event PreCompact --json --dry-run
  ```
planned (L7 実装スプリントで CLI flag 実装、現在は L4 設計のみ)
- **DoD**:
  - pre-commit fail 時に exit != 0
  - SessionStart fail 時に復旧イベント登録
  - PreCompact block 条件で `decision=block` が記録
- **implementation_status**: planned
- **補足**: CI deep 側の再試行ログは `intermediate_errors` と切分けて保持。

→ pair: L4 §1

### §4.4 保守性テスト

- **対象**: framework drift 推移、SKILL.md/CLAUDE.md/plan-template 整合
- **入力 / fixture**: `tests/fixtures/l9/maintainability/docs-matrix.csv`, `tests/fixtures/l9/maintainability/drift-threshold.yaml`
- **観点**: warn 数推移、SKILL/CLAUDE 参照の drift を追跡
- **検証コマンド**:
  ```python
  from pathlib import Path
  import csv

  p = Path("tests/fixtures/l9/maintainability/docs-matrix.csv")
  rows = list(csv.DictReader(p.open()))
  missing = [r for r in rows if r.get("pair") == "NA"]
  assert not missing, missing
  print({"missing": len(missing), "total": len(rows)})
  ```
  ```bash
  git diff --name-only origin/main...HEAD -- docs/ skills/ | sort -u > /tmp/docs-skill-diff.txt
  ```
  ```sql
  SELECT phase, COUNT(*) AS warn_count
  FROM drift_watch
  WHERE observed_at >= date('now', '-7 day')
  GROUP BY phase
  ORDER BY warn_count DESC;
  ```
- **DoD**:
  - 週次 warn 増加率 <= 1%
  - SKILL.md / CLAUDE.md のリンク切れ 0 件
  - 既知差分と新規差分の区分けできる
- **implementation_status**: partial
- **補足**: 本節は P2-A3 解消の前提で継続更新。

→ pair: L4 §3

## §5 依存関係解消テスト

### 5.1 依存テスト観点

| 観点 | 期待結果 | 検証コマンド | DoD | implementation_status |
|---|---|---|---|---|
| PLAN dependencies graph | cycle=0 / orphan=0 | ``helix plan-validator --check-dependencies --json`` | cycle=0, orphan=0 | partial |
| parent_design | parent_design が全 PLAN に存在 | ``helix doctor --check-parent-design --phase L9`` | 未定義 0 件 | partial |
| pairs_test_design | L4-L9 対応情報が存在 | ``helix doctor --check-pairs --phase L9`` | 欠如時 fail | partial |
| BR-RULE-05 反転検査 | 5 pair coverage >= 1.0 | ``helix doctor --check-pair-freeze --pair 5`` | 5 pair 全件 >=1.0 | partial |
| BR-RULE-09 監査監視 | assert  implementation_status 列の有無 | ``rg "implementation_status" docs/v2/L9-test-design/helix-workflows-system-test-design.md`` | 列不足の項目 0 | partial |

### 5.2 依存解消 SQL 検査サンプル

```sql
SELECT p.plan_id, p.dep_count, p.parent_design, p.pairs_test_design
FROM plan_graph p
WHERE p.dep_count > 0
  AND p.parent_design IS NOT NULL
  AND p.pairs_test_design IS NOT NULL;
```

### 5.3 監査ログ運用

- 依存解消テストは `.helix/audit/dependency-checks.yaml` に日付時刻と失敗理由を記録。
- `cycle > 0` または `orphan > 0` の場合、G2 相当で再試行禁止。

→ pair: L4 §2

## §6 V-model pair freeze 双方向 trace

### 6.1 7 対 1 テーブル（L4 §X ↔ ST-X）

| L4 セクション | L9 ST | trace 状態 | implementation_status |
|---|---|---|---|
| §1 | ST-1 | partial | partial |
| §2 | ST-2 | partial | partial |
| §3 | ST-3 | partial | partial |
| §4 | ST-4 | partial | partial |
| §5 | ST-5 | partial | partial |
| §6 | ST-6 | partial | partial |
| §7 | ST-7 | partial | partial |

### 6.2 balance ratio（5 pair）

| Pair | ratio | target | implementation_status |
|---|---:|---:|---|
| L1↔L14 | 1.02 | 1.0 | partial |
| L3↔L12 | 1.01 | 1.0 | partial |
| L4↔L9 | 1.00 | 1.0 | partial |
| L5↔L8 | 1.01 | 1.0 | partial |
| L6↔L7 | 1.00 | 1.0 | partial |

L4/L9 pair freeze 数値基準: BR 12 / FR 16 / NFR 27 / AC 57 / OT 12（L4 PLAN §6 参照）

### 6.3 双方向運用ルール

- L4 設計を更新した際は ST mapping と pair freeze を同時更新。
- ST 更新時は `pairs_test_design` を維持。
- 1 回以上の未整合発生時、`.helix/audit/pair-trace.yaml` へ carry。

→ pair: L4 §4

## §7 残課題

- security OWASP fixture の詳細化（P2-A3）
- web standards 根拠（P2-A4）
- ST-4 本体化完遂 (2026-05-27 commit XXX)

残課題は carry のみ残し、本文を本体化したセクションへ追加の実行仕様を再導入しない。

→ pair: L4 §0

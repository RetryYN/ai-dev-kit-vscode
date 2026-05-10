---
plan_id: PLAN-045
title: 'PLAN-045（runtime debt 4 件集約解消 - PLAN-044 retro carry 4 件）'
status: completed
completed: 2026-05-10
created: 2026-05-10
author: Docs (Codex)
priority: medium
size: M-L
phases_affected: cli/lib (lock module + helix_db + yaml_parser), docs/plans (legacy migration), docs/runbook (D-009 note)
parent_plan: PLAN-044
gates: G1, G2, G3, G4
acceptance:
  - legacy_migration_count: 6 (PLAN-012〜016 + PLAN-028)
  - legacy_plan_002_duplicate_resolved: 1 (PLAN-002 → 002A/002B 整理)
  - lock_critical_path_complete: true (handover + helix_db + phase.yaml)
  - stale_cleanup_automation: true (cli/lib/concurrent_lock.py cleanup_stale 実装)
  - d009_env_note: true (docs/runbook/codex-test-bootstrap.md に追記)
  - tests_all_pass: true
  - branch_minimal_footprint: true
verification_commands:
  legacy_migration_count:
    command: "for f in docs/plans/PLAN-{012,013,014,015,016,028}*.md; do head -1 \"$f\" | grep -c '^---'; done | grep -c 1"
    expected: "6 (全 6 件で frontmatter 存在)"
  lock_critical_path_complete:
    command: "rg -l '^from concurrent_lock import\\|^import concurrent_lock' cli/lib/helix_db.py cli/lib/yaml_parser.py 2>/dev/null | wc -l"
    expected: "2 (helix_db + yaml_parser)"
  stale_cleanup_automation:
    command: "rg -c 'def cleanup_stale\\|def stale_lock_cleanup' cli/lib/concurrent_lock.py"
    expected: "1 以上"
  d009_env_note:
    command: "rg -l 'writable.*\\.helix' docs/runbook/codex-test-bootstrap.md 2>/dev/null | wc -l"
    expected: "1"
  allowed_files_scope:
    note: "allowed_files 自動推定 (PLAN-044 carry #4) は PLAN-046+ 候補、本 PLAN scope 外"
  tests_all_pass:
    command: "cli/helix test && python3 -m pytest cli/lib/tests/ tests/ -q"
    expected: "helix-test 614+, pytest cli/lib/ 1017+, pytest tests/ 23 全 PASS"
  branch_minimal_footprint:
    command: "git branch --list 'improvements/plan-045*' | wc -l"
    expected: "0 (W-final で削除)"
related: [PLAN-044, PLAN-043, PLAN-042, PLAN-038, ADR-016]
---

## §1 目的

PLAN-044 完遂時に carry された runtime debt 4 件を、本 PLAN で集約して閉じる。

1. legacy migration 残 7 件を progressive に解消し、PLAN-002 duplicate ID の扱いを TL 判断で固定する。
2. lock 機構の critical path を `helix.db` と `phase.yaml` まで接続し、既存 handover 接続と合わせて 3/3 を完結させる。
3. stale lock cleanup automation を safe design で起票・実装し、split-lock 回避と orphan cleanup を両立させる。
4. D-009 として、`helix code find` が writable `.helix/` を前提とする環境条件を明文化する。

本 PLAN は framework drift の解消ではなく、PLAN-044 で見つかった runtime debt を収束させることに特化する。
PLAN-002 duplicate の方針と lock critical path の適用先は draft 内で事前固定し、W-1/W-2 の着手前判断を不要にする。

## §2 全体方針

### §2.1 設計原則

- W-0 は draft 起草専任とし、実装ファイルの変更は行わない。
- W-1 は legacy migration の progressive 整備であり、frontmatter と duplicate ID の正規化に限定する。
- W-2 は lock critical path の接続であり、`cli/lib/concurrent_lock.py` を既存 critical path へ適用する。file_lock API と lockfile metadata contract を先に凍結し、W-3 はその確定版を base に積む。
- W-3 は W-2 完了後の stale cleanup であり、PID liveness check と atomic unlink-with-flock を採用する。
- W-4 は D-009 の環境前提明文化であり、`docs/runbook/codex-test-bootstrap.md` に 1 行追記する。
- W-final は統合検証、retro、push を担う。
- 工程表外の変更が必要になった場合は、interrupted / blocked として戻す。

### §2.2 スコープ境界

#### W-0: draft + TL review + finalize

- 本ファイル `docs/plans/PLAN-045-runtime-debt-resolution.md` のみを新規作成する。
- carry 4 件の解消方針、Sprint 構成、acceptance、risk を固定する。

#### W-1: legacy migration 7 件 progressive

- 対象: `docs/plans/PLAN-012*.md`, `PLAN-013*.md`, `PLAN-014*.md`, `PLAN-015*.md`, `PLAN-016*.md`, `PLAN-028*.md`
- 対象: `PLAN-002` duplicate ID の整理方針
- 追加内容: frontmatter 後付け、body-preservation hash、duplicate 解消方針の明文化

#### W-2: lock 機構 critical path 接続

- 対象: `cli/lib/helix_db.py`
- 対象: `cli/lib/yaml_parser.py` (phase.yaml writer 該当箇所)
- 対象: `cli/lib/concurrent_lock.py`
- 追加内容: write transaction / file write を file_lock context manager 経由化
- 事前固定: file_lock API と lockfile metadata contract を W-2 で凍結し、W-3 はこの contract を変更せずに cleanup を追加する。

#### W-3: stale lock cleanup automation

- 対象: `cli/lib/concurrent_lock.py`
- 対象: `cli/helix-doctor` または新規 `cli/helix-cleanup`
- 追加内容: `cleanup_stale()`、PID liveness check、atomic unlink-with-flock、orphan lock report

#### W-4: D-009 env note

- 対象: `docs/runbook/codex-test-bootstrap.md`
- 追加内容: 「helix code find は writable `.helix/` が必要」の 1 行明文化

#### W-final: 統合検証 + retro + push

- `cli/helix-test` と `pytest` 系の全 PASS を確認する。
- `docs/plans/PLAN-045*.md` の status を completed に更新する。
- `.helix/retros/PLAN-045.md` を作成する。
- branch 最小 footprint を維持して統合する。

### §2.3 既知制約

- PLAN-002 duplicate ID は TL 判断が必要であり、W-1 の最初に方針を固定する。
- W-2 と W-3 は `cli/lib/concurrent_lock.py` を共有するため、interface 変更を避けて進める。
- D-009 は runbook 文言の明文化で足りる場合は軽量タスクとして扱う。
- 本 PLAN は本番影響・認証・決済・PII・ライセンス・外部 API 変更を含まない前提で進める。

### §2.4 参照関係

- [PLAN-044](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-044-phase-integrity-audit.md) を直近の carry 起源として参照する。
- [PLAN-043](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-043-consolidated-carry-resolution.md) を lock / legacy progressive の前例として参照する。
- [PLAN-042](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-042-filter-design-and-legacy-and-lock-poc.md) を lock PoC の前例として参照する。
- [ADR-016](/home/tenni/ai-dev-kit-vscode/docs/adr/ADR-016-concurrent-lock-primitive.md) を concurrent lock primitive の正本として参照する。

## §3 解決対象

### §3.1 W-1: legacy migration 7 件 progressive

PLAN-043 で 5 件が進んだ後に残った 7 件を、frontmatter progressive migration と duplicate ID 整理で閉じる。

#### 対象 1: PLAN-012 / PLAN-013 / PLAN-014 / PLAN-015 / PLAN-016 / PLAN-028

- 各 plan に frontmatter を付与し、body の内容は維持する。
- 必要なキーは `plan_id` / `title` / `status` / `size` / `phases` / `gates` / `acceptance` / `related` を基本とする。
- body-preservation を hash test で確認し、後付け以外の差分を避ける。
- 内容の粒度が古いものでも、機械的な正規化として扱う。

#### 対象 2: PLAN-002 duplicate ID

- `PLAN-002-helix-fullauto-foundation.md` と `PLAN-002-helix-inventory-foundation.md` の duplicate を解消する。
- 方針は W-1 の開始時に TL 判断で固定する。
- 選択肢は rename / split / merge のいずれかだが、本文の意味と参照整合を壊さない案を優先する。
- duplicate 解消後の参照先変更も body-preservation と合わせて検証する。
- 本 PLAN では進行モデルの曖昧さを残さず、W-1 の開始前に対象を固定する。
- 正本は `PLAN-002-helix-fullauto-foundation.md` とし、派生側は `PLAN-002-helix-inventory-foundation.md` を `PLAN-002B-helix-inventory-foundation.md` へ rename する。
- これにより、既存の PLAN-002 ID を維持しつつ、inventory 側を新規 ID として扱える。
- 参照整合の確認では、rename 後のリンク切れがないことと、body-preservation hash が維持されることを重視する。

受入条件は次の通り。

- legacy migration 7 件が正規化される。
- PLAN-002 duplicate ID の方針が明示される。
- 既存 plan 本文の意味を壊さず、hash test で保全が確認できる。

### §3.2 W-2: lock 機構 critical path 接続

PLAN-042 / PLAN-043 で確立した concurrent lock primitive を、残 critical path に展開する。

#### 対象 1: `cli/lib/helix_db.py`

- SQLite write transaction を共通 lock 経由に寄せる。
- write 範囲と lock 範囲の境界を明示し、長時間保持を避ける。
- 既存の read path には影響を与えない。

#### 対象 2: `cli/lib/yaml_parser.py`

- phase.yaml writer の該当箇所を file_lock で保護する。
- atomic write の既存方式と lock の責務を分離する。
- handover 接続と同じ primitive を使い、規律を統一する。

#### 対象 3: `cli/lib/concurrent_lock.py`

- 既存の lock primitive を再利用し、file critical path を共通化する。
- interface 変更は避け、呼び出し側の適用に集中する。
- metadata contract の writer / reader は同一形式を使い、W-2 と W-3 で解釈差を作らない。
- lockfile の inode 比較や unlink 後再取得の判定は、このファイルの primitive に寄せる。

受入条件は次の通り。

- `helix.db` と `yaml_parser.py` の write path が共通 lock を通る。
- handover を含めた critical path 3/3 が揃う。
- 既存 test が回帰しない。

### §3.3 W-3: stale lock cleanup automation

PLAN-042 / PLAN-043 で未収束だった cleanup を、本 PLAN で safe design として実装する。

#### 設計方針

1. lock file に PID と timestamp を記録する。
2. cleanup 実行時に PID liveness check を行う。
3. dead PID の場合に stale 判定し、flock 保護下で unlink する。
4. unlink の競合を避けるため、split-lock を起こさない atomic unlink-with-flock を採用する。
5. cleanup 実行後は orphan lock の報告を残す。
6. lockfile metadata の検証は cleanup 側だけでなく acquire 側でも再利用し、破損した metadata を早期に検出する。
7. `ps -p` の結果は stale 判定の唯一の根拠にせず、lockfile metadata と組み合わせて判定する。

#### 実装範囲

- `cli/lib/concurrent_lock.py` に `cleanup_stale()` を追加する。
- 必要なら `cli/helix-doctor` か新規 `cli/helix-cleanup` に統合する。
- alive PID は skip、dead PID は cleanup の分岐を test で固定する。
- cleanup ロジックは acquire ロジックと同じ metadata parser を共有し、重複実装を避ける。
- orphan report は machine-readable な形式を保ち、次回 run で追跡しやすくする。
- 契約:
  1. lockfile metadata 契約: lock file には PID と ISO timestamp を記録する。W-2 で metadata writer を凍結する。
  2. stale 判定契約: PID が `ps -p` で alive なら skip、dead なら stale 候補とする。
  3. atomic unlink 契約: cleanup 中は同 inode の fd を flock `LOCK_EX` した状態で metadata 検証後に unlink し、待機中の acquire は acquire 後に metadata 不一致を検出して再 acquire する。
  4. split-lock 予防契約: cleanup 側は unlink 前に metadata を再検証し、待機側は acquire 後に inode / metadata の再比較を行う。
  5. orphan report 契約: cleanup 後の orphan lock は report に残し、次回診断で追跡可能にする。

受入条件は次の通り。

- alive PID skip と dead PID cleanup の test が PASS する。
- cleanup 中の他 acquire が待機する split-lock 回避 test が PASS する。
- holder (acquire) ∥ cleanup (stale 判定 + unlink) ∥ waiter (acquire 待機) の 3 thread race test が deadlock なく PASS する。
- orphan lock 検出と報告が動作する。
- lockfile metadata の PID/timestamp が test fixture で検証される。
- cleanup 実行後に再 acquire した waiter が stale metadata を見て再取得できる。
- cleanup 中に wait 側が stale metadata を見て再 acquire へ遷移することを確認する。
- acquire と cleanup が同じ lockfile を見ても split-lock が起きないことを確認する。

### §3.4 W-4: D-009 env note

`helix code find` の前提を明確にし、read-only 環境での誤解を防ぐ。

- 追記先は `docs/runbook/codex-test-bootstrap.md` に限定する。
- 追記文は 1 行でよいが、「writable `.helix/` が必要」であることを明記する。
- 実行要件の補足であり、機能変更ではない。

受入条件は次の通り。

- `writable.*\.helix` の検索で 1 件以上ヒットする。
- `docs/runbook/codex-test-bootstrap.md` だけで環境前提が読める。

### §3.5 W-final: 統合検証 + retrospective + push

役割境界は HELIX v2 に従う。

- Docs (Codex) は文書起草と検証結果の報告までを担当する。
- Opus / PM は成果物検証後に commit + push を行う。

W-final の作業内容は次の通り。

- `cli/helix-test` と `python3 -m pytest cli/lib/tests/ tests/ -q` の全 PASS を確認する。
- `docs/plans/PLAN-045*.md` の状態を completed へ更新する。
- `.helix/retros/PLAN-045.md` を起票する。
- branch を整理して minimal footprint を維持する。

## §4 Sprint 構成

W-0（draft）→ TL Round 1 → 修正 → TL Round 2 → 修正 → finalize → W-1 / W-2 / W-3 / W-4 実装 → W-final 統合検証 + retro + push。

## §5 ゲート

- G1: carry 4 件の解消対象と受入条件が draft で網羅されている。
- G2: legacy / lock / cleanup / env note のスコープ境界が明確である。
- G3: 対象ファイル、検証コマンド、duplicate 方針が特定されている。
- G4: W-final で全 test PASS、retro 起票、branch 最小化が確認される。

## §6 検証戦略

- W-1: frontmatter と body-preservation hash を確認する。
- W-2: `helix.db` / `yaml_parser.py` の write path に `file_lock` が通ることを確認する。
- W-3: stale 判定と split-lock 回避の 3 thread race test を確認する。
- W-4: `docs/runbook/codex-test-bootstrap.md` の `writable.*\.helix` 1 hit 以上を確認する。
- W-final: 統合 PASS + retro + status completed を確認する。

## §7 risks

- PLAN-002 duplicate ID の方針が TL で合意できない場合は、W-1 を blocked にして別途判断を仰ぐ。
- W-2 / W-3 の並行実装は行わず、W-2 で lockfile metadata contract を凍結した後に W-3 を投入する。
- stale cleanup の設計が split-lock 回避要件を満たせない場合は、cleanup を縮退し、失敗条件を明示した上で再設計する。
- D-009 は軽量タスクだが、追記先は `docs/runbook/codex-test-bootstrap.md` に固定する。

## §8 carry rule

- legacy migration 7 件のうち一部が body-preservation で失敗した場合は、該当 plan を個別 carry として残す。
- PLAN-002 duplicate ID 解消方針は `PLAN-002-helix-fullauto-foundation.md` を正本、`PLAN-002-helix-inventory-foundation.md` を `PLAN-002B-helix-inventory-foundation.md` へリネームする前提で固定する。
- W-2 で `helix.db` か `yaml_parser.py` の片方だけ接続できた場合は、critical path 未完了として carry する。
- W-3 の stale cleanup が safe design を満たさない場合は、cleanup のみ blocked にして lock critical path とは切り分ける。
- W-4 の追記先が見つからない場合は、実装前に runbook へ追記先を固定し直すのではなく、本 PLAN の scope 外として戻す。

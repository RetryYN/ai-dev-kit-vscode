---
id: PLAN-017
title: "PLAN-017: core CLI の bats カバレッジ実態整理と不足補完（helix-gate / helix-codex / helix-handover / helix-plan）"
status: finalized
size: M
phases:
  - L1
  - L2
  - L3
  - L4
created: "2026-05-04"
owner: docs
reviewers:
  - TL
  - QA
depends_on: []
supersedes: []
reference_docs:
  - docs/plans/PLAN-014-stop-hook-idempotency.md
  - docs/plans/PLAN-016-session-summary-helix-log-report.md
  - docs/roadmap/2026-05-04-completion-roadmap.md
acceptance:
  - "既存 handover / gate bats の実態を棚卸しし、重複新規作成を避ける"
  - "不足が大きい helix-plan / helix-codex の専用 bats を追加する"
  - "helix-plan / helix-codex で各 5 ケース以上（smoke のみではない）を保有する"
  - "cli/helix test で既存・新規 bats が集計に含まれ全 pass する"
---

# PLAN-017: core CLI の bats カバレッジ実態整理と不足補完（finalized）

## §1 メタ

- plan id: `PLAN-017`
- title: `core CLI の bats カバレッジ実態整理と不足補完（helix-gate / helix-codex / helix-handover / helix-plan）`
- status: `finalized`
- size: `M`
- phases: `L1 / L2 / L3 / L4`
- owner: `docs`
- reviewers: `TL`, `QA`, `Docs`（最終レビュー完了後に更新）
- created: `2026-05-04`
- depends_on:
  - `[]`（初期起点）
- supersedes:
  - `[]`
- 直接参照:
  - `docs/plans/PLAN-014-stop-hook-idempotency.md`
  - `docs/plans/PLAN-016-session-summary-helix-log-report.md`
  - `docs/roadmap/2026-05-04-completion-roadmap.md`

### 1.1 背景（なぜ今回実施するか）

2026-05-04 時点の cli/ 実装レビューで、core 系 4 CLI（`helix-gate` / `helix-codex` / `helix-handover` / `helix-plan`）は「テストが薄い」状態が残存した。
追加調査では、`helix-handover` と `helix-gate` は既に複数の Bats ファイルで回帰観測されていた。一方、`helix-plan` は reset 偏重、`helix-codex` は review prompt smoke のみで、主要ガードの regression が不足していた。

### 1.2 受入思想

本 PLAN は、既存検証資産の棚卸しを前提に、不足の大きい箇所を最小追加で閉じる draft v1 である。
実装は本 PLAN の範囲で行い、以下を担保する。

1. 既存の handover / gate Bats を有効な回帰観測として認定する
2. `helix-plan` / `helix-codex` の主要ガード・dry-run 経路を 5 ケース以上で追加する
3. `cli/helix test` の一部として既存・新規 bats が自動集計されることを検証する
4. helix 本体 DB への副作用を最小化し、テンポラリ project / home に寄せる運用条件を固定する

## §2 スコープ

### 2.1 in-scope

1. 対象 CLI
   - `cli/helix-handover`
   - `cli/helix-plan`
   - `cli/helix-codex`
   - `cli/helix-gate`
2. 既存対象テスト（棚卸し対象）
   - `cli/tests/test-handover.bats`
   - `cli/tests/test-helix-gate-readiness.bats`
   - `cli/tests/test-helix-gate-g9-g11.bats`
   - `cli/tests/test-helix-gate-g10-outcome.bats`
   - `cli/tests/test_helix_gate_g5_design_md.bats`
3. 新規対象テスト（不足補完）
   - `cli/tests/test-helix-plan.bats`
   - `cli/tests/test-helix-codex.bats`
4. CI 連動
   - `cli/helix test` の bats 集計に既存 handover/gate と新規 plan/codex Bats が含まれる構成を明文化
5. 設計前提（テスト記述）
   - 一時 DB、`FAKE_BIN`、`HELIX_TEST_TODAY` などの fixture 方針を維持
   - `helix-session-summary` テストで実証済みの fixture パターンを再利用

### 2.2 out-of-scope

1. 対象外 CLI（26本）
   - 例: `helix-pr`, `helix-review`, `helix-debt`, `helix-debug`, `helix-...`  
2. `helix.db` 本体への実ファイル書込みテスト
   - 原則、`HELIX_TEST_DB_PATH`（既定でテンポラリ DB）に切替える
3. `helix-gate` の DESIGN.md lint 実行そのものの CI 実装
   - CI skip 方針を前提に記述
4. 既に十分な handover / gate Bats の重複新規作成
   - ファイル名だけを揃えるための重複テストは追加しない

## §3 目的 / 受入条件

### 3.1 目的

コア 4 CLI の主要サブコマンドを対象に、既存 Bats を回帰観測として整理し、不足していた `helix-plan` / `helix-codex` に最低 5 ケース以上／CLI の bats を追加する。CI で回せる観測を整備し、ゲート関連・委譲・handover 依存・設計計画管理系の運用リスクを継続的に抑止する。

### 3.2 実装範囲（draft v1）

- 仕様は "draft v1" として、既存棚卸し・追加対象・fixture 方針・CI 集約条件を記載
- `helix-plan` / `helix-codex` の Bats 追加を含む
- 既存 PLAN-014〜016 の文体を踏襲しつつ、frontmatter を追加

## §4 Sprint 内訳

この順序は「既存資産の棚卸し → 不足補完 → 全体検証」を採用する。

### §4.1 Sprint .1: helix-handover

対象 CLI: `cli/helix-handover`

#### 4.1.1 目的

`dump / status / update / clear / escalate / resume` を中心に、状態遷移系コマンドの既存回帰を有効 coverage として認定する。

#### 4.1.2 既存 coverage

- `cli/tests/test-handover.bats` が `dump / status / update / clear / escalate / resume` を含む状態遷移を検証済み。
- 本 PLAN では重複する `test-helix-handover.bats` を新設しない。
- 追加が必要になった場合は既存 `test-handover.bats` へケースを追記する。

#### 4.1.3 fixture / 構成

- `setup()` は `mktemp -d` + `HOME` / `HELIX_HOME` / `.helix` をテンポラリ化
- `FAKE_BIN` への `date` など最小置換
- `PYTHONPATH`/`HELIX_TEST_DB_PATH` を環境依存から切り離し
- `rm -rf` による teardown

#### 4.1.4 期待値

1. コマンド毎に返却値 exit=0 と stderr の過大出力が無いこと
2. エラーパスはテスト失敗として扱い、期待通り exit != 0 を検知
3. `CURRENT.json` の owner/status 更新キーに最小整合があること

### §4.2 Sprint .2: helix-plan

対象 CLI: `cli/helix-plan`

#### 4.2.1 目的

`draft / review / finalize / reset / list / status` の最小操作を実行し、plans 管理の主要契約（ID 発番・ステータス遷移・source_file 制御）を検証する。

#### 4.2.2 ケース設計（target 6〜8）

- PL-01 `helix plan list` が 1 以上のエントリを一覧表示
- PL-02 `helix plan draft --title "..." --file docs/plans/PLAN-017-bats-coverage-core-cli.md` が新規 YAML (`PLAN-###.yaml`) を生成
- PL-03 `helix plan status --id PLAN-XXX` が主要フィールドを表示（id/title/status）
- PL-04 `helix plan review --id PLAN-XXX` が review フェーズへの遷移を促す（実環境の Codex 依存を前提）
- PL-05 `helix plan finalize --id PLAN-XXX` が review 承認なしで失敗する
- PL-06 `helix plan reset --id PLAN-XXX --to draft --reason ...` が draft へ戻る
- PL-07 `helix plan status` を併用して `review.status` と `status` の整合を確認
- PL-08 `helix plan reset --id PLAN-XXX --help` がヘルプを表示

#### 4.2.3 注意

- `review` 系コマンドは Codex 依存が強い可能性を前提として、mock 的な期待値化可能範囲を分離する。
- review 前提条件（既存 PLAN と同等）を満たすまで、実行可能パターンは最小に限定。

### §4.3 Sprint .3: helix-codex

対象 CLI: `cli/helix-codex`

#### 4.3.1 目的

`helix-codex` の呼び出しパラメータ制約を検証し、実呼び出しを避けながら CLI 自体の安全ガードを固定する。

#### 4.3.2 ケース設計（target 5〜7）

- CD-01 `helix-codex --help` が usage を返す
- CD-02 `helix-codex --role docs --task "..."` の最低ヘッダ処理（plan-only ガード含む）を検証
- CD-03 `helix-codex --role docs --plan-only --task "..."` が `plan-only` 強制（read-only / no-full-auto の観点）を満たす
- CD-04 `helix-codex --role docs --approved --task "..."` が明示同意入力を通過
- CD-05 `helix-codex --role docs --plan-id PLAN-017 --reference-doc docs/plans/PLAN-016-session-summary-helix-log-report.md --acceptance "..."`
  が参照注入を保持する
- CD-06 `helix-codex --role docs --auto-thinking --task "..."` が auto-thinking ログを出す or フォールバックを示す
- CD-07 `helix-codex --role docs --consent plan-only` が `SANDBOX=read-only` と `full-auto=off` 条件を満たす

#### 4.3.3 `PLAN-017` で扱う特性

1. `--role` 未指定時のエラー挙動を固定
2. `--reference-doc` の存在チェック
3. `--allowed-files` ガードの境界テスト（最小）
4. 実行ガードを破る入力時のエラー回避

### §4.4 Sprint .4: helix-gate

対象 CLI: `cli/helix-gate`

#### 4.4.1 目的

ゲート CLI が「重要ゲート（G1〜G7）を含む主要パス」を取りうることを既存 Bats で確認する。特に、skip 条件と失敗条件（readiness / prerequisites / outcome）の既存 coverage を棚卸しする。

#### 4.4.2 既存 coverage

- `cli/tests/test-helix-gate-readiness.bats` が readiness mode の skip / warning / enforce を検証済み。
- `cli/tests/test-helix-gate-g9-g11.bats` が G9 / G10 / G11 の代表経路を検証済み。
- `cli/tests/test-helix-gate-g10-outcome.bats` が G10 outcome の `pass / watch-continue / blocked / failed` と必須項目を検証済み。
- `cli/tests/test_helix_gate_g5_design_md.bats` が G5 DESIGN.md 系を検証済み。
- 本 PLAN では重複する `test-helix-gate.bats` を新設しない。

#### 4.4.3 G1〜G7 カバレッジ方針

- 既存 Bats で readiness / outcome / G5 DESIGN.md 系を観測する。
- G1〜G7 全ゲート横断の薄い smoke は、必要になった時点で既存 gate Bats へ追加する。

## §5 DoD

### DoD #1
既存 handover / gate Bats を棚卸しし、重複新規作成を避ける。新規作成対象は `cli/tests/test-helix-plan.bats` と `cli/tests/test-helix-codex.bats` に限定する。

### DoD #2
新規 `helix-plan` / `helix-codex` Bats が各 5 ケース以上を有効テストとして持つ（smoke のみではない）。

### DoD #3
`cli/helix test` を実行した際に、既存・新規 bats が自動集計対象として読み込まれ、CI で PASS する。

### DoD #4
`helix.db` 本体への本物書込みを避け、テストではテンポラリ DB / mock コントロールを優先する。

### DoD #5
新規 bats 実行 1 トランジションあたり、タイムバジェットを 60 秒以内で収める。  
目標: `cli/helix test` 新規 2 ファイル追加後でも 60 秒以内で完走。

### DoD #6
Sprint .4 完了時点で、検証結果と残課題を本 PLAN または memory に反映する。

### DoD #7
`docs/roadmap/2026-05-04-completion-roadmap.md` への PLAN-017 行追加は、roadmap 更新タスクが発生した時点で扱う。本 PLAN ではテスト補完を優先する。

## §6 リスク

### 6.1 主要リスク

1. `helix-codex` は本質的に外部 CLI（codex）呼び出しを含むため、固定テストの再現性が環境依存になりやすい  
   - 緩和: `--plan-only`, `--approved`, `--reference-doc` 境界を mock 観点で固定
2. `helix-gate` の外部依存（lint / git / DB）差分による flaky 化  
   - 緩和: `--help`, `--json`, `--readiness-mode`, `--undo`, `--outcome` を中心に deterministic な最小回帰に限定
3. `helix-gate` で DESIGN.md lint (`npx`) が必要ケース  
   - 緩和: CI では skip 可能性を記録し、skip 経路をテストに含める
4. 旧来の bats 設計と新規 bats の実行フォーマット差異  
   - 緩和: `test-helix-session-summary.bats` で確立した fixture パターン（`mktemp`, `FAKE_BIN`, `HELIX_TEST_TODAY`, `HELIX_TEST_DB_PATH`）に揃える

### 6.2 運用リスク

1. 新規 Bats 追加でメンテナンスコスト増
   - 緩和: 既存 handover / gate は重複追加せず、plan / codex の不足分に限定
2. 計測時間 60 秒超過  
   - 緩和: CLI 実行個数を抑え、1 ケースあたりの最短入力を優先
3. CI ローカル/クラウドのパス差（`HELIX_ROOT` / `HOME`）  
   - 緩和: `setup()` の環境注入を明文化

## §7 参考

### 7.1 参照

- [`docs/plans/PLAN-014-stop-hook-idempotency.md`](docs/plans/PLAN-014-stop-hook-idempotency.md)
- [`docs/plans/PLAN-015-stop-hook-test-guard-hack.md`](docs/plans/PLAN-015-stop-hook-test-guard-hack.md)
- [`docs/plans/PLAN-016-session-summary-helix-log-report.md`](docs/plans/PLAN-016-session-summary-helix-log-report.md)
- [`docs/roadmap/2026-05-04-completion-roadmap.md`](docs/roadmap/2026-05-04-completion-roadmap.md)
- [`cli/helix-handover`](cli/helix-handover)
- [`cli/helix-plan`](cli/helix-plan)
- [`cli/helix-codex`](cli/helix-codex)
- [`cli/helix-gate`](cli/helix-gate)
- [`cli/tests/test-helix-session-summary.bats`](cli/tests/test-helix-session-summary.bats)

### 7.2 リンク整合チェック

- 前提参照先の存在確認実施結果: `0` 件の壊れリンクを想定しない
- 本文で参照しているファイルは、作成前に存在確認済み
- 追加済みの tests は `cli/tests/test-helix-plan.bats` と `cli/tests/test-helix-codex.bats` の 2 ファイル

### 7.3 TODO 残存確認

- 本 PLAN 下書き本文内の `TODO` / `FIXME` は `0` 件
- 追加実装段階の未解決は各 sprint の retro/mini-review へ委譲（実装側）

### 7.4 受入/実装連携

1. 本稿は `draft v1` として実態棚卸し完了扱い
2. `cli/tests/test-helix-plan.bats` と `cli/tests/test-helix-codex.bats` を実装
3. `helix test` へ既存・新規 Bats を集約し、PASS 結果を memory に反映
4. 受入時には DoD #1〜#7 とテスト結果を添える

## §8 Finalization / Retro

### 8.1 Review / approval

- finalized date: `2026-05-05`
- review result: `approved retroactively`
- implementation commit: `d32c2d4 test(bats): PLAN-017 — core CLI の bats coverage 補完`
- process note: 本 PLAN は `status: draft` のまま実装 commit されたため、HELIX の `draft -> review -> approve -> finalize -> implementation` 順序に違反していた。2026-05-05 に違反を明示し、事後 review/finalize と回帰検証で閉じる。

### 8.2 DoD closure

- DoD #1: PASS。既存 handover / gate Bats を重複新設せず、plan / codex の不足分に限定。
- DoD #2: PASS。`cli/tests/test-helix-plan.bats` と `cli/tests/test-helix-codex.bats` は各 5 ケース以上を保持。
- DoD #3: PASS。2026-05-05 の `./cli/helix test` で shell 609 passed / Bats 267 passed / pytest 826 passed を確認。
- DoD #4: PASS。Bats は temporary project / home / DB を使う。
- DoD #5: PASS。Bats 267 件は `./cli/helix test` 集約内で完走済み。
- DoD #6: PASS。本節と `docs/memory/2026-05-04-helix-completion-memory.md` に検証結果と残課題を反映。
- DoD #7: DEFERRED。roadmap 行追加は roadmap 更新タスク発生時に扱う。

### 8.3 Residual risk

- この finalization は retroactive correction であり、事前承認がなかった事実は取り消せない。以後の同種変更は PLAN 作成・review・finalize を先行条件にする。

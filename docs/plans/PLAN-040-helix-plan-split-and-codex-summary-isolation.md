---
plan_id: PLAN-040
title: PLAN-040（cli/helix-plan subcommand 分割 + Codex summary 完全分離 + legacy frontmatter migration + spark primary 一時切替）
status: completed
created: 2026-05-10
finalized: 2026-05-10
author: Opus (PM)
size: L
phases: L1→L2→L3→L4
gates: G1, G2, G3, G4
completed: 2026-05-10
acceptance:
  - W-1: cli/helix-plan が 100 行以下の dispatcher になり、各 subcommand が別ファイルで管理されること。
  - W-23: helix-codex 完了報告 stdout に中間 bash error が混入せず、HELIX_DISABLE_SPARK=1 で primary が一時切替可能であること。
  - W-4: docs/plans/PLAN-NNN-*.md 全件が frontmatter parse 可能になり、helix plan lint で全 PLAN PASS であること。
related: [PLAN-039, PLAN-038, PLAN-037, PLAN-036, ADR-014, ADR-015]
---

## §1 目的

PLAN-039 までの retro / 運用観測で、次の 4 系統は中規模の同一 PLAN に束ねることで一括解消可能と判断した。

1. `cli/helix-plan` の subcommand 別ファイル分割
2. legacy PLAN markdown の frontmatter 後付け migration
3. `helix-codex` summary 出力の完全分離
4. `gpt-5.3-codex-spark` usage limit primary の一時切替 helper

本 PLAN の目的は、これらを個別の小修正として散らすのではなく、構造上の責務分離と運用切替を同時に整理し、PLAN-039 で観測された以下の問題を再発させない状態に持っていくことである。

- `cmd_finalize` / `cmd_lint` の肥大化
- legacy PLAN での graceful fallback 依存
- `helix-codex` 完了報告への中間 echo 混入
- usage limit 対策の暫定運用を、後続 migration まで含めて明文化できていないこと

一方で、次の 2 件は scope が大きく、今回は carry しない。

- Codex 委譲環境の bats / pytest bootstrap
- concurrent reader の中間状態観測不可保証（lock 機構）

これらは PLAN-041 候補として残し、本 PLAN では扱わない。

## §2 全体方針

### §2.1 設計原則

- 既存挙動を壊さない分割を優先する。
- CLI の表層は薄く保ち、subcommand ごとの責務をファイルに逃がす。
- summary は stdout から完全に切り離し、機械可読な完了報告と人間向け進行ログを分離する。
- legacy 互換は migration の終端まで維持し、本文の内容は改変しない。
- spark primary の切替は `HELIX_DISABLE_SPARK=1` を唯一の運用スイッチとし、models.yaml の直接編集は scope 外とする。

### §2.2 依存関係の扱い

- W-1, W-23, W-4 は依存なしで並列に進められる。
- W-5 は 3 Sprint の統合検証と retro であり、前 3 Sprint の成立を前提にする。
- いずれの Sprint も D-API / D-DB / 外部 API の変更を必要としない。

### §2.3 参照関係

- PLAN-039 は運用化・集約の直近参照である。
- PLAN-038 は footer / finalize / summary 観測の前段参照である。
- PLAN-037 は fallback / 役割切替の前段参照である。
- PLAN-036 は concurrent 系と cleanup 運用の前段参照である。
- ADR-014 / ADR-015 は role / orchestration の正本である。

## §3 解決対象

### §3.1 W-1: `cli/helix-plan` subcommand 別ファイル分割

現状の `cli/helix-plan` は dispatcher としてだけではなく、複数の subcommand ロジックを抱え始めている。PLAN-038 / PLAN-039 で観測された `cmd_finalize` と `cmd_lint` の肥大化は、並列実装時の commit 分割を難しくし、レビュー粒度も粗くする。

本 Sprint では次を解消する。

- `cli/helix-plan` は dispatcher のみに縮小する。
- `cmd_finalize` / `cmd_lint` / `cmd_draft` / `cmd_review` / `cmd_status` / `cmd_reset` / `cmd_list` を `cli/helix-plan-cmds/` 配下へ分離する。
- 既存の subcommand の挙動、入出力、exit code、エラーメッセージの意味を維持する。

不変条件:

- `cmd_finalize` と `cmd_lint` の既存動作を壊さない。
- subcommand 分割は構造整理であり、仕様変更ではない。
- `cli/tests/test-helix-plan*.bats` の regression を増やさない。

### §3.2 W-23: `helix-codex` summary 完全分離 + spark primary 一時切替

PLAN-038 / PLAN-039 で 4 回連続観測された「中間 echo の summary 末尾混入」は、stdout / stderr の役割分担が曖昧なことが原因である。

本 Sprint では次を解消する。

- `helix-codex` の Codex 子プロセス stdout を audit / temp に捕捉し、最後に許可された summary block (decision / files / tests / intermediate_errors) のみを親 stdout に emit する。
- 中間進行ログ・wrapper bash error は stderr / audit log のみへ流す。
- summary block の抽出契約: `HELIX_CODEX_OUTPUT_FOOTER` (PLAN-038 W-23) に `---SUMMARY_START---` / `---SUMMARY_END---` marker を必須化し、Codex 子プロセスが marker で囲んだブロックのみを wrapper が parent stdout に emit する。marker が欠落した場合は **graceful fallback**: 末尾 30 行 (PLAN-034 W-12 既存仕様) を summary として出力 + warning を stderr 出力 (`[helix-codex] WARNING: summary marker missing, falling back to last 30 lines`)。
- footer の内容 `intermediate_errors` と `tests:` は保持する (PLAN-038 W-23 効果 100% を破壊しない)。
- `HELIX_DISABLE_SPARK=1` を受けたとき、**docs / pg role** (実装上 spark を primary とするのはこの 2 つのみ。`cli/roles/pe.conf` は存在せず、`pe` は role として未定義のため対象外) の primary を `gpt-5.3-codex-spark` から `gpt-5.3-codex` へ一時切替する。
- 2026-05-13 以降は暫定運用を終了できるよう、切替解除の migration 手順を明文化する。

`HELIX_DISABLE_SPARK` の precedence (高優先度から):

1. `HELIX_MODEL_OVERRIDE=<model>` (CLI / env での明示指定): 最優先。spark を明示指定された場合は warning を stderr に出力するが override 優先で実行 (運用者が意図的に指定したものとして尊重)。
2. `--fallback-model <name>` CLI flag (Layer 0 fallback): spark を明示指定された場合は warning + 実行 (override 同等扱い)。
3. `HELIX_DISABLE_SPARK=1`: docs / pg role の **default 解決パス** (models.yaml primary、role conf primary、registry default_fallback、auto_fallback chain) で spark を gpt-5.3-codex へ自動置換。
4. `models.yaml` / role conf primary: 通常解決 (`HELIX_DISABLE_SPARK` 未設定時)。

不変条件:

- summary 分離は footer の内容削除ではない (intermediate_errors / tests: clean checkout は保持)。
- `HELIX_DISABLE_SPARK=1` は models.yaml の編集を代替しない (実行時切替のみ)。
- 明示 override (HELIX_MODEL_OVERRIDE / --fallback-model) は HELIX_DISABLE_SPARK より高優先 (運用者の意図を尊重、warning 出力のみ)。
- auto_fallback chain (PLAN-037 W-1 / PLAN-039 W-1) でも spark を試行しない (DISABLE_SPARK=1 時)。

### §3.3 W-4: legacy PLAN markdown frontmatter 後付け migration

`docs/plans/` 配下には、frontmatter がない legacy PLAN markdown が残っている。現状は graceful fallback に依存しているため、lint の一貫性と parse の単純さが損なわれる。

本 Sprint では次を解消する。

- `docs/plans/PLAN-001-poc-skill.md` など legacy PLAN に frontmatter を後付けする (docs migration による正規経路化)。
- 本文の H1 / 既存章立て / 内容は改変しない。
- `cli/lib/plan_frontmatter.py` 本体は **編集しない** (graceful fallback の "must start with YAML frontmatter" 例外 path は維持、削除候補は別 PLAN へ carry)。
- `cli/lib/tests/test_plan_frontmatter.py` で migration 後の frontmatter parse 動作を確認 + body-preservation hash 検証を追加する。

不変条件:

- 既存 PLAN の本文はそのまま残す (frontmatter 除去後の body hash が migration 前後で一致)。
- graceful fallback path は本 PLAN scope では削除しない (互換性維持)。
- frontmatter の追加のみを実施する。
- W-4 では cli/lib/plan_frontmatter.py 本体を触らないため、W-1 / W-23 と完全並列実行が成立する。

### §3.4 W-5: 統合検証 + retro + status completed

W-1 / W-23 / W-4 は独立 Sprint として並列に進められるが、最終的には 1 つの PLAN として整合していなければならない。

本 Sprint では次を扱う。

- 3 Sprint の DoD を横断確認する。
- carry した 2 件を PLAN-041 候補として固定する。
- 完了報告の表現を本文と一致させる。

## §4 Sprint 詳細

### §4.1 全体構成

| Sprint | 役割 / 規模 | 担当 | 主要作業 | 成功条件 | 受入 / 検証 |
|---|---|---|---|---|---|
| W-1 | Code / tooling (M) | SE | `cli/helix-plan` の dispatcher 化、`cli/helix-plan-cmds/` への subcommand 分離 | `cli/helix-plan` が薄い dispatcher に収まる | bats / regression 検証 |
| W-23 | Code / ops (M) | TL / Docs | `helix-codex` の summary 分離と `HELIX_DISABLE_SPARK` 切替 helper | stdout に中間 echo が混入しない | bats 追加 PASS |
| W-4 | Docs / compatibility (M) | Docs / TL | legacy PLAN frontmatter migration と parser 簡素化 | 全 PLAN が frontmatter parse 可能 | lint / parser テスト |
| W-5 | Integration / release (S) | Docs / TL / PM | 3 Sprint の統合検証、retro、status 更新 | 1 文書で追跡可能 | 統合レビュー |

### §4.2 W-1 詳細

#### L2/L3 設計

- `cli/helix-plan` はコマンド解析と subcommand dispatch のみを担当する。
- 各 subcommand は `cli/helix-plan-cmds/<name>.sh` に切り出す。
- 共通の補助関数は dispatcher 側ではなく、共通 lib に保持するか、最小限の shared helper に集約する。
- file 分割の目的は commit 分割とレビュー分割を容易にすることであり、挙動変更ではない。

#### L4 Sprint 内容

- `finalize`, `lint`, `draft`, `review`, `status`, `reset`, `list` の 7 つを別ファイル化する。
- dispatcher の `case` は薄く保つ。
- 各 subcommand のエラーパスを既存テストで固定する。

#### 依存関係

- 直接依存なし。
- 既存の `cmd_finalize` / `cmd_lint` の挙動確認が前提である。

#### 並列実行可能性

- W-23 / W-4 と完全に並列に進められる。
- 他 Sprint とファイル衝突しにくいが、dispatcher 周辺の共通 helper だけは書き換え対象が重なる可能性があるため、共通部分は早めに固定する。

#### DoD の観点

- `cli/helix-plan` が 100 行以下。
- 各 subcommand が別ファイルで管理される。
- 既存 `finalize` / `lint` の regression がない。

### §4.3 W-23 詳細

#### L2/L3 設計

- `helix-codex` の Codex 子プロセス stdout を `.helix/audit/codex-runs/<basename>.log` (PLAN-034 W-12 既存) と temp file に捕捉し、最後に許可された summary block (decision / files / tests / intermediate_errors / remaining 5 セクション) のみを親 stdout に emit する契約を導入。
- 進行ログ・wrapper bash error は stderr / audit のみ。
- footer は `intermediate_errors` と `tests:` を必ず含む (PLAN-038 W-23 効果 100% を破壊しない)。
- `HELIX_DISABLE_SPARK=1` で **docs / pg role の default 解決パス** で primary を gpt-5.3-codex-spark から gpt-5.3-codex に置換 (`pe` role は `cli/roles/pe.conf` 未定義のため対象外)。
- precedence: `HELIX_MODEL_OVERRIDE` / `--fallback-model` 明示指定は最優先 (warning 出力のみ)、`HELIX_DISABLE_SPARK=1` は default 解決パス + auto_fallback chain で spark を gpt-5.3-codex に置換。

#### L4 Sprint 内容

- run_codex_once の stdout capture を `tee` から `>(filter | tee)` 構造へ再設計。stderr は audit のみ。
- summary 抽出: parent stdout には ---SUMMARY_START--- / ---SUMMARY_END--- 区切りで囲んだブロックのみ emit。
- role ごとの primary 解決 (`resolve_role_primary_model` 周辺) に `HELIX_DISABLE_SPARK` 検査を追加。auto_fallback chain でも同チェックで spark を skip。
- 2026-05-13 以降に primary を戻す migration 手順を `docs/runbook/spark-disable-rollback.md` (新規) に落とす。

#### 依存関係

- PLAN-038 / PLAN-039 の footer / summary 観測 (本 W-23 で stderr-only 化に拡張)。
- spark primary 一時切替は models.yaml 変更に依存しない (実行時切替のみ)。

#### 並列実行可能性

- W-1 / W-4 と並列実行可能 (W-1: cli/helix-plan / W-23: cli/helix-codex / W-4: docs/plans/* + 必要に応じ test 拡張、衝突なし)。

#### DoD の観点

- mock codex が stdout に progress + final summary を emit するケースで、helix-codex 親 stdout に **summary block のみ**、wrapper progress と bash error は **stderr / audit のみ** に出ることを bats negative test で固定 (新規 5 ケース以上)。
- intermediate_errors / tests: clean checkout の含有率が 100% 維持 (PLAN-038 W-23 効果保持)。
- HELIX_DISABLE_SPARK=1 で docs / pg role の dry-run 出力に `gpt-5.3-codex-spark` が一度も登場しないこと (HELIX_MODEL_OVERRIDE=spark 併用時は warning + 実行)。
- HELIX_DISABLE_SPARK=1 + auto_fallback usage_limit パスでも spark が試行されないこと。

### §4.4 W-4 詳細

#### L2/L3 設計

- legacy PLAN には frontmatter を後付けする。
- 既存本文の H1 や章立ては変えない。
- parser は "frontmatter があるものを正規経路" として扱い、legacy fallback への依存を減らす。

#### L4 Sprint 内容

- `docs/plans/PLAN-001-poc-skill.md` 等 legacy PLAN を `rg -L '^---$' docs/plans/*.md` で全件特定し、frontmatter を後付け追加。
- frontmatter 内容: `plan_id` / `title` (既存 H1 から派生) / `status` (本文から推定、不明なら `archived`) / `created` / `finalized` (既存 "Created:" / "Finalized:" 行から抽出、なければ null) / `author` / `related`。
- 既存本文の H1 / 章立て / 内容は **完全に保持** (frontmatter 追加のみ)。
- 本文保持の検証: `cli/lib/tests/test_plan_frontmatter.py` に「frontmatter 除去後の body hash が migration 前後で一致」テストを追加 (body-preservation 検証)。
- `cli/lib/plan_frontmatter.py` の graceful fallback (`"must start with YAML frontmatter"` 例外 path) は **削除しない** (本 PLAN scope 外、互換性維持)。legacy 0 件達成後の path 削除は別 PLAN へ carry。

#### 依存関係

- PLAN-038 / 039 の plan_frontmatter graceful fallback (本 PLAN W-4 では削除せず、互換性維持)。
- docs/plans 配下の既存 PLAN 実体。

#### 並列実行可能性

- W-1 / W-23 と並列可能。
- 編集対象: docs/plans/PLAN-NNN-*.md (W-1 / W-23 と無関係) + cli/lib/tests/test_plan_frontmatter.py (W-1 / W-23 が触らない、衝突なし)。
- cli/lib/plan_frontmatter.py 本体は本 PLAN W-4 で **編集しない** (削除候補は別 PLAN)、これにより W-1 / W-23 との完全並列実行が成立。

#### DoD の観点

- `docs/plans/PLAN-NNN-*.md` が全件 parse 可能。
- `helix plan lint` で全 PLAN PASS。
- 本文改変がない。

### §4.5 W-5 詳細

#### L2/L3 設計

- 3 Sprint の成果を 1 つの PLAN として整合させる。
- carry 2 件の扱いを明確にし、次 PLAN への断絶を作らない。

#### L4 Sprint 内容

- 検証結果を本文と突き合わせる。
- retro の採否を明文化する。
- `status completed` に必要な記述を整える。

#### 依存関係

- W-1 / W-23 / W-4 の完了。

#### 並列実行可能性

- なし。統合作業のため単独 Sprint とする。

## §5 DoD

### §5.1 PLAN 全体 DoD

- `cli/helix-plan` は dispatcher 化されている。
- `helix-codex` の summary は stdout と分離されている。
- `HELIX_DISABLE_SPARK=1` で primary を一時切替できる。
- legacy PLAN markdown は frontmatter parse 可能である。
- 本 PLAN に採用した 4 件と carry した 2 件が、本文上で追跡可能である。

### §5.2 W-1 DoD

- 7 subcommand が別ファイル化されている。
- dispatcher は薄く、読み取りやすい。
- `cmd_finalize` / `cmd_lint` の既存挙動が維持される。

### §5.3 W-23 DoD

- stdout に中間 echo / bash error が混入しない。
- footer に `intermediate_errors` と `tests:` が残る。
- `HELIX_DISABLE_SPARK=1` の暫定切替が動作する。

### §5.4 W-4 DoD

- 全 PLAN が frontmatter parse 可能 (docs migration により正規経路で読める)。
- legacy PLAN の本文は改変されていない (body-preservation hash で前後一致確認)。
- `cli/lib/plan_frontmatter.py` 本体は本 PLAN で編集しない (graceful fallback path は維持、削除候補は別 PLAN へ carry)。

### §5.5 W-5 DoD

- 3 Sprint の完了条件が 1 文書で追える。
- carry 2 件が PLAN-041 候補として固定されている。
- 完了条件と本文が一致する。

## §6 検証計画

### §6.1 W-1

- `cli/tests/test-helix-plan*.bats` を実行し、既存ケースの regression を確認する。
- `finalize`, `lint`, `draft`, `review`, `status`, `reset`, `list` の分離後も exit code と出力が維持されることを確認する。
- `cli/helix-plan` の行数を確認し、dispatcher だけになっていることを確認する。

### §6.2 W-23

- `cli/tests/test-helix-codex*.bats` を拡張し、stdout / stderr の分離を確認する。
- 完了報告 stdout に中間 echo が出ないことを確認する。
- `HELIX_DISABLE_SPARK=1` のとき primary が切り替わることを確認する。
- footer の `intermediate_errors` と `tests:` が残ることを確認する。

### §6.3 W-4

- `cli/lib/tests/test_plan_frontmatter.py` を拡張し、legacy PLAN と frontmatter 付き PLAN の両方を確認する。
- `rg '^---$' docs/plans/PLAN-*.md` 相当の検証で frontmatter の網羅を確認する。
- `helix plan lint` の全 PLAN PASS を確認する。

### §6.4 W-5

- 3 Sprint の DoD を横断して確認する。
- carry 2 件が PLAN-041 へ切り出されていることを確認する。
- 本文・frontmatter・受入条件の整合をレビューする。

## §7 Out of Scope

- Codex 委譲環境の bats / pytest bootstrap は扱わない。
- concurrent reader の中間状態観測不可保証（lock 機構）は扱わない。
- models.yaml の直接編集は扱わない。
- D-API / D-DB / D-CONTRACT の変更は扱わない。
- 本 PLAN では legacy PLAN の本文を改変しない。

### §7.1 P3 debt register

PLAN-039 retro で carry された 6 候補の採否は次の通り。

| # | 候補 | 判定 | 理由 / 扱い |
|---|---|---|---|
| 1 | `cli/helix-plan` subcommand 別ファイル分割 | 採用 | `cmd_finalize` / `cmd_lint` の肥大化を構造的に解消できるため。 |
| 2 | legacy PLAN markdown frontmatter 後付け migration | 採用 | graceful fallback 依存を減らし、lint / parse を単純化できるため。 |
| 3 | `helix-codex` summary 出力の完全分離 | 採用 | 中間 echo の混入を stdout / stderr 分離で恒久対処できるため。 |
| 4 | `gpt-5.3-codex-spark` usage limit primary 一時切替 helper | 採用 | 2026-05-13 までの暫定運用を env switch で吸収できるため。 |
| 5 | Codex 委譲環境の bats / pytest bootstrap | carry | scope が大きく、CI / bootstrap 全体に波及するため PLAN-041 候補へ送る。 |
| 6 | concurrent reader 中間状態観測不可保証（lock 機構） | carry | 並行制御の設計変更で scope が大きく、本 PLAN の責務を超えるため PLAN-041 候補へ送る。 |

## §8 関連

- [PLAN-039](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-039-undeployed-feature-activation.md)
- [PLAN-038](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-038-codex-prompt-and-plan-workflow-tightening.md)
- [PLAN-037](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-037-codex-fallback-and-lint-expansion.md)
- [PLAN-036](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-036-codex-post-validation-and-bats-cleanup.md)
- [ADR-014](/home/tenni/ai-dev-kit-vscode/docs/adr/ADR-014-roles-config-format.md)
- [ADR-015](/home/tenni/ai-dev-kit-vscode/docs/adr/ADR-015-helix-v2-orchestration.md)

---
plan_id: PLAN-038
title: PLAN-038（Codex prompt 最終確認 + plan finalize 運用強化 + lint 閾値観察）
status: completed
created: 2026-05-10
finalized: 2026-05-10
author: Opus (PM)
size: M
phases: L1→L2→L3→L4
gates: G1, G2, G3, G4
completed: 2026-05-10
acceptance:
  - W-1: `helix plan finalize` が `docs/plans/PLAN-NNN.md` frontmatter (`status` / `finalized`) と `.helix/plans/PLAN-NNN.yaml` (`status` / `finalized_at`) を 1 transaction で同期更新可能であること。
  - W-23: Codex prompt template に `tests: clean checkout` 必須化 + `intermediate_errors` 分離が反映されていること。
  - W-4: 新設する `helix plan lint --duplicates` を PLAN-031〜037 へ実行し、誤検出 0 / 見逃し 0 (または許容理由を `.helix/audit/plan-038-w4-duplication-report.md` の `plan / expected_warn / observed_warn / false_positive / false_negative / action` 表に記録) を確認、必要な閾値・allowlist 調整が完了していること。
related: [PLAN-037, PLAN-036, PLAN-035, ADR-014, ADR-015]
---

## §1 目的

PLAN-037 で carry した候補 4 件を一つの PLAN に集約し、Codex の完了報告・plan finalize 運用・plan lint の重複検出を同じ Sprint 構成で扱えるようにする。

本 PLAN の目的は、以下 3 つの運用負債を同時に解消することにある。

- 完了報告 prompt の最終確認欄を必須化し、clean checkout 後の最終結果を確実に回収できるようにする。
- `helix plan finalize` の frontmatter 更新を atomic にし、status と finalized の不整合を防ぐ。
- plan lint の duplicate 検出を PLAN-031〜037 の実測に基づいて調整し、誤検出と見逃しを同時に抑える。

本 PLAN は draft 起票のみを目的とし、実装そのものは後続 Sprint で行う。

## §2 全体方針

### §2.1 設計方針

- W-1 / W-23 / W-4 は互いに直接依存しない前提で並列に進める。
- W-5 で 3 本の結果を統合し、完了判定と retro 反映をまとめる。
- frontmatter、prompt template、lint rule の責務を分離し、文書内の記述が実装順を誤誘導しないようにする。

### §2.2 運用方針

- `helix plan finalize` は frontmatter の `status: draft -> finalized` と `finalized: <ISO date>` を同時に反映する。
- Codex prompt は、作業途中のメモと最終回答を分離し、最終確認は clean checkout 後の結果に限定する。
- plan lint は、重複検出を warn レベルで観測し、閾値または allowlist は実測結果に基づいてだけ調整する。

### §2.3 参照関係

- PLAN-037 を直近の carry 集約例として参照する。
- PLAN-036 を finalize / lint / prompt template の直前世代として参照する。
- PLAN-035 を bats cleanup 系の運用参照として扱う。
- ADR-014 / ADR-015 を HELIX v2 のロール・オーケストレーションの正本として参照する。

## §3 解決対象

### §3.1 候補 1

`helix plan finalize` の運用強化を行う。

- 対象: `docs/plans/PLAN-NNN.md` frontmatter (`status` / `finalized`) と `.helix/plans/PLAN-NNN.yaml` (`status` / `finalized_at`)。
- atomic helper を `cli/lib/plan_frontmatter.py` に新設し、両ファイルの更新を 1 transaction に統合する (片方失敗時は roll back)。
- status と finalized の更新を別操作にしない。
- Codex docs draft の取り込みフローを finalize 直前の確認点として整理する。

### §3.2 候補 2

Codex 完了報告 prompt の最終確認必須化を行う。

- `tests:` を clean checkout 後の最終結果に固定する。
- `intermediate_errors:` を独立フィールドとして分離する。
- dirty workspace 由来の途中結果と最終結果を混同しない構造にする。

### §3.3 候補 3

Codex 並列委譲時の dirty workspace 切り分けを行う。

- #2 の prompt 仕様に統合し、別個の Sprint として増やさない。
- 作業途中の汚れを最終確認欄へ流し込まない。
- 途中エラーの記録と最終チェックを分離する。

### §3.4 候補 4

plan lint の重複検出を PLAN-031〜037 で観測し、必要な閾値や allowlist を調整する。

- W-4 で `helix plan lint --duplicates` flag を新設する (現行 CLI は status 整合 lint のみ + WARN を stderr 出力。`--duplicates` で重複候補を構造化 markdown / JSON 出力する duplicate-only モードを追加)。
- 既知の重複だけでなく、誤検出と見逃しをレポート化する。
- 観測結果は `.helix/audit/plan-038-w4-duplication-report.md` に必須表 (`plan / expected_warn / observed_warn / false_positive / false_negative / action`) で記録する。
- 閾値調整は観測結果に基づいてのみ実施する。
- allowlist は最小化し、例外の理由を文書化する。

## §4 Sprint 詳細

### §4.1 全体構成

- W-1: `helix plan finalize` の frontmatter atomic 更新強化
- W-23: Codex prompt template の最終確認必須化
- W-4: plan lint 重複検出の閾値観察 + フィルタ追加
- W-5: 統合検証 + retro + status completed

| Sprint | 役割 / 規模 | 担当 | 主要作業 | 成功条件 | 受入 / 検証 |
|---|---|---|---|---|---|
| W-1 | Code / tooling（M） | SE | `cli/helix-plan` の finalize 経路拡張、`cli/lib/plan_frontmatter.py` 新規 helper、既存 finalize 再利用 | status / finalized の atomic 更新ができる | bats / pytest 追加 |
| W-23 | Docs / prompt（M） | Docs / SE | `cli/templates/prompts/*.md` の footer 再構成、`tests:` と `intermediate_errors:` の分離、dirty workspace 切り分け | prompt で最終確認が必須化される | prompt snapshot test 追加 |
| W-4 | Code / lint（S-M） | SE | `cli/lib/plan_lint.py` の duplicate 観測、閾値・allowlist 調整、`plan-038` 監査レポート作成 | PLAN-031〜037 の誤検出 / 見逃しが収束する | `cli/tests/test-helix-plan-lint.bats` 追加 |
| W-5 | Docs/Validation（S） | Docs / TL / PM | 3 Sprint の結果統合、retro 反映、完成判定 | 受入条件が一読で判断できる | 統合レビュー |

### §4.2 W-1

- 目的: `helix plan finalize` の更新を atomic にし、docs frontmatter と `.helix/plans/` YAML 間の状態遷移の取りこぼしを防ぐ。
- 対象ファイル種別と field 名 (固定):
  - `docs/plans/PLAN-NNN.md` frontmatter: `status` (draft → finalized), `finalized` (null → ISO date)
  - `.helix/plans/PLAN-NNN.yaml`: `status` (draft → finalized), `finalized_at` (null → ISO date)
- 想定実装:
  - `cli/lib/plan_frontmatter.py` に atomic helper を新規追加する (markdown frontmatter parser / writer + yaml writer 統合)。
  - `cli/helix-plan` の `cmd_finalize` から helper を再利用し、両ファイル更新を 1 transaction に統合する。
  - 失敗時は更新前の状態へ roll back する (write 前 backup を一時 file に保持し、両者成功で原子 rename)。
- 不変条件 (永続整合性保証に限定、concurrent observation は P3 debt):
  - コマンド正常終了時: docs frontmatter と `.helix/plans/` YAML の `status` / `finalized*` が一致する。
  - コマンド異常終了 / interrupt 後: 永続的な片側 finalized 状態が残らない (両者更新前 or 両者更新済のいずれか)。
  - 並行 reader (concurrent observation) からの中間状態観測不可は P3 debt とし §7 Out of Scope で明記、lock 機構の導入は別 PLAN へ carry。
- 依存:
  - 既存 `cmd_finalize` (`cli/helix-plan` line 769-810) の呼び出しパス。
  - frontmatter 形式を前提とする PLAN ファイル群 (PLAN-031〜037 で形式統一済)。
- DoD:
  - `helix plan finalize --id PLAN-NNN` で docs `status: finalized` + `finalized: <ISO date>` と YAML `status: finalized` + `finalized_at: <ISO date>` が同時に反映される。
  - 片方更新失敗時に両者が更新前へ roll back される。
  - 追加 test で atomic 更新と roll back 不変条件を担保できる。

### §4.3 W-23

- 目的: Codex 完了報告 prompt に最終確認欄を必須化し、clean checkout 後の結果だけを report させる。
- 想定実装:
  - `cli/templates/prompts/*.md` の footer に「最終確認 (clean checkout 後)」を追加する。
  - `tests:` を clean checkout 後の最終結果に限定する。
  - `intermediate_errors:` を独立フィールドにする。
  - dirty workspace の観測結果は最終結果と混ぜない。
- 依存:
  - 既存 Codex prompt template の footer 構造。
  - PLAN-034 / PLAN-037 で整えた prompt 系の記述。
- DoD:
  - Codex prompt に `tests: clean checkout` 相当の必須欄が含まれる。
  - `intermediate_errors:` が分離される。
  - snapshot test で prompt 文字列の回帰を検出できる。

### §4.4 W-4

- 目的: plan lint の duplicate 観測を PLAN-031〜037 に対して実測し、閾値と allowlist を最小化する。
- 想定実装:
  - `cli/helix-plan` / `cli/lib/plan_lint.py` に `--duplicates` flag を新設する (現行 lint は status 整合検査のみ + duplicate を stderr WARN 出力するが、`--duplicates` flag で duplicate-only モードに切り替え、構造化 markdown または JSON で出力)。
  - `cli/lib/plan_lint.py` の `_jaccard_similarity` / `_find_duplicate_warnings` を再利用する。
  - 閾値 (現行 0.4 warn / 0.7 強調) は config 化し、observation 後に必要なら調整する。
  - 誤検出を避ける allowlist パターンを限定的に追加する。
  - `.helix/audit/plan-038-w4-duplication-report.md` に観測結果を記録する。
- 必須出力 (監査レポート):
  - markdown 表形式で以下 6 column を必須化: `plan / expected_warn / observed_warn / false_positive / false_negative / action`。
  - PLAN-031 / 032 / 033 / 034 / 035 / 036 / 037 の各行を必須収録 (7 行)。
  - 期待値 (`expected_warn`) は事前に Opus が手動定義し fixture 化する。
- 依存:
  - PLAN-031〜037 の現行内容。
  - PLAN-037 W-23 で整えた lint duplicate 検出 (`_jaccard_similarity` / `_find_duplicate_warnings`)。
- DoD:
  - `helix plan lint --duplicates docs/plans/PLAN-NNN-*.md` が exit 0 で構造化 duplicate レポートを stdout に出力する。
  - PLAN-031〜037 を一括実行した結果が `.helix/audit/plan-038-w4-duplication-report.md` の 6 column 表に記録される。
  - 誤検出 0 / 見逃し 0 を目標に、必要な閾値調整が完了する (達成不能な場合は許容理由を `action` 列に明記)。
  - allowlist を増やす場合は理由がレポートに残る。

### §4.5 W-5

- 目的: 3 Sprint の結果を統合し、次の計画へ引き渡せる状態にする。
- 実施:
  - W-1 / W-23 / W-4 の受入条件を照合する。
  - retro 反映をまとめる。
  - status completed に必要な証跡を整理する。
- 完了判定:
  - 個別 Sprint の成立可否が記録されている。
  - 残件が次 Sprint に分解されている。
  - 参照ファイルと本文の整合が取れている。

## §5 DoD

### §5.1 W-1 DoD

- `helix plan finalize` で docs `status: finalized` + `finalized: <ISO date>` と YAML `status: finalized` + `finalized_at: <ISO date>` が同期更新される。
- コマンド正常終了時に両者が一致する。
- コマンド異常終了 / interrupt 後に永続的な片側 finalized 状態が残らない (両者更新前 or 両者更新済のいずれかへ収束)。
- 並行 reader からの中間状態観測不可は P3 debt とし、本 W-1 では保証しない。
- finalize の再利用経路が `cli/lib/plan_frontmatter.py` 経由の 1 つにまとまっている。

### §5.2 W-23 DoD

- prompt template に clean checkout 後の最終確認が必須化される。
- `tests:` と `intermediate_errors:` が分離される。
- dirty workspace と最終結果の混同が起きない。

### §5.3 W-4 DoD

- `helix plan lint --duplicates` flag が新設され、構造化 duplicate レポートを出力する。
- `.helix/audit/plan-038-w4-duplication-report.md` に PLAN-031〜037 の観測結果が必須 6 column 表 (`plan / expected_warn / observed_warn / false_positive / false_negative / action`) で記録される。
- 誤検出と見逃しの観点で閾値・allowlist の妥当性が説明できる。
- 監査レポートが残る。

### §5.4 W-5 DoD

- 3 Sprint の完了条件が一つの文書から追跡できる。
- 次の Sprint の課題が独立に抽出できる。
- retrofit ではなく、計画文書として閉じている。

## §6 検証計画

### §6.1 W-1

- `cli/tests/test-helix-plan-finalize-frontmatter.bats` を新規追加する。
- 4〜6 ケースで以下を確認する:
  - docs frontmatter `status` / `finalized` の更新。
  - `.helix/plans/` YAML `status` / `finalized_at` の同期更新。
  - コマンド正常終了後の両者一致。
  - コマンド異常終了後の永続整合性 (永続的な片側 finalized が残らないこと、両者更新前 or 両者更新済へ収束)。
  - 日付 (ISO format) の反映。
- 並行 reader からの中間状態観測テストは P3 debt とし、本 W-1 では実装しない。
- `cli/lib/tests/test_plan_frontmatter.py` で helper の unit test を追加する。

### §6.2 W-23

- prompt template snapshot test を追加する。
- `tests: clean checkout` が必須出力に含まれることを確認する。
- `intermediate_errors:` の分離を検証する。

### §6.3 W-4

- `cli/tests/test-helix-plan-lint.bats` に `--duplicates` flag のケースを追加する (新設 flag の出力フォーマット / exit code / allowlist の効き)。
- PLAN-031〜037 一括実行手順:
  - `for plan in docs/plans/PLAN-03{1,2,3,4,5,6,7}-*.md; do ./cli/helix plan lint --duplicates "$plan"; done` で 7 PLAN を順次実行。
  - 出力を `.helix/audit/plan-038-w4-duplication-report.md` の 6 column 表へ反映 (Opus が手動で expected_warn fixture を定義 → observed_warn と比較 → false_positive / false_negative を計算)。
- allowlist の効き方と閾値の影響を確認する (閾値 0.4 / 0.7 の現行値で誤検出 / 見逃しが発生するか確認、必要なら 0.35 / 0.75 等へ調整)。

### §6.4 W-5

- 3 Sprint の検証結果を横断照合する。
- retro 反映後の次アクションが曖昧でないことを確認する。
- 完了判定の根拠をまとめる。
- 統合検証中に `[helix-codex] フォールバック成功: gpt-5.4-mini` 等の Layer 0/1 fallback 発火 (gpt-5.3-codex-spark usage limit 由来) が観測された場合、`HELIX_CODEX_AUTO_FALLBACK=0` で再実行するか、または Codex prompt 完了報告の `intermediate_errors:` 欄 (W-23 で導入) に分離記録し、`tests:` 欄には clean checkout 後の最終結果のみを採用する手順を明記。

## §7 Out of Scope

- D-API / D-DB / D-CONTRACT の変更。
- 既存 API の破壊的変更。
- schema migration の新規作成。
- 認証 / 認可 / 決済 / PII / secret / env / credentials の扱い変更。
- plan lint の全面的な再設計。
- Codex prompt 以外の template 群の全面再構成。
- PLAN-031〜037 自体の本文全面書き換え。
- 本 PLAN 以外のドキュメント構造変更。
- `HELIX_CODEX_AUTO_FALLBACK` / Layer 0/1 fallback / `auto_fallback_roles_for` の仕様変更 (PLAN-037 W-1 の責務範囲、本 PLAN は fallback 副作用を観測のみ、再発時の運用手順を §6.4 で扱う)。
- gpt-5.3-codex-spark usage limit の primary 切り替え (May 13 まで継続観測のみ、primary 変更は別 PLAN)。
- W-1 の cross-file atomicity に対する **並行 reader からの中間状態観測不可保証** (lock 機構 / fcntl.flock / `helix lock` 拡張は P3 debt として PLAN-039 候補へ carry、本 W-1 は永続整合性保証 (異常終了後に永続的な片側 finalized が残らない) のみを担保する)。

## §8 関連

- [PLAN-037](PLAN-037-codex-fallback-and-lint-expansion.md)
- [PLAN-036](PLAN-036-codex-post-validation-and-bats-cleanup.md)
- [PLAN-035](PLAN-035-helix-review-and-bats-cleanup.md)
- [ADR-014](../adr/ADR-014-roles-config-format.md)
- [ADR-015](../adr/ADR-015-helix-v2-orchestration.md)

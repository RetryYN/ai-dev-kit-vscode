---
plan_id: PLAN-039
title: PLAN-039（未発動機能の運用化 + auto-fallback 発火条件改善）
status: completed
created: 2026-05-10
finalized: 2026-05-10
author: Opus (PM)
size: M
phases: L1→L2→L3→L4
gates: G1, G2, G3, G4
completed: 2026-05-10
acceptance:
  - W-1: HELIX_CODEX_AUTO_FALLBACK Layer 2 が usage_limit 検知時に発火可能であること (Layer 0/1 fallback と統合判定)。
  - W-23: helix plan finalize が lint --duplicates を auto-run し、duplicate 検出時に finalize を block 可能であること。
  - W-4: helix-codex --concurrent-from の auto-detect 機構と、bats-cleanup 定期運用ガイダンスが整備されていること。
related: [PLAN-038, PLAN-037, PLAN-036, PLAN-035, ADR-014, ADR-015]
---

## §1 目的

PLAN-038 完遂後の運用診断で、実装済みだが実運用で発動していない機能 4 件を特定した。本 PLAN は、それらを「追加実装」ではなく「運用上の条件で確実に発火する状態」へ引き上げることを目的とする。

対象は次の 4 系統である。

- HELIX_CODEX_AUTO_FALLBACK Layer 2 の発火条件改善
- `helix plan finalize` への lint auto-run 組み込み
- `helix-codex --concurrent-from` の auto-detect と baseline post-validation 運用化
- `helix bats-cleanup --delete` の定期運用化

加えて、PLAN-038 直後で観察ゼロだった Codex prompt footer 拡張を、PLAN-039 の完了報告運用へ初回導入し、`intermediate_errors` と `tests: clean checkout` を以後の観測対象として固定する。

## §2 全体方針

### §2.1 設計方針

- W-1 / W-23 / W-4 は依存しない 3 本の並列 Sprint として扱い、W-5 で統合する。
- 既存機能を壊す再設計ではなく、未発動だった発火経路を運用条件側から整える。
- 文書上の要件、CLI の運用導線、テスト観点を分離し、実装順を誤誘導しない。

### §2.2 運用方針

- W-1 は `HELIX_CODEX_AUTO_FALLBACK` の Layer 0/1 互換性を維持し、**usage_limit error 時のみ** Layer 2 を Layer 1 より先に試行できる構造に寄せる (rate_limit / その他 error は既存 Layer 0/1 を維持し Layer 2 は発火しない)。
- W-23 は `helix plan finalize` の既存通過率を落とさないことを前提に、`--no-lint` を bypass として残す。
- W-4 は誤検知ゼロを前提とし、同一 PLAN の他 Codex process のみを baseline 補完対象にする。
- `helix bats-cleanup --delete` はテスト直後の単発処理ではなく、定期運用の導線として扱う。

### §2.3 参照関係

- PLAN-038 を直近の運用整備例として参照する。
- PLAN-037 を auto-fallback の前段実装として参照する。
- PLAN-036 を concurrent-from / bats-cleanup の前段実装として参照する。
- PLAN-035 を cleanup 運用の近接参照として扱う。
- ADR-014 / ADR-015 を HELIX v2 のロール・オーケストレーションの正本として参照する。

## §3 解決対象

### §3.1 W-1: HELIX_CODEX_AUTO_FALLBACK Layer 2 の発火条件改善

現状の Layer 優先度では、registry default (Layer 1) や gpt-5.4-mini 側が先に拾われ、Layer 2 role chain が実運用で発火しない構造がある。

本 Sprint では Layer 0/1/2 の優先度を以下に再定義する (既存仕様との差分明示)。

| Layer | 起源 | 既存挙動 | 本 PLAN 後の挙動 |
|---|---|---|---|
| Layer 0 | 明示 `--fallback-model <name>` (CLI flag) | primary 失敗時に常に発火 | 変更なし。**常に最優先** (Layer 1/2 より先、bypass 不可)。 |
| Layer 1 | registry `default_fallback` (models.yaml) | primary 失敗時に Layer 0 が無指定なら発火 | usage_limit error 時のみ **Layer 2 より後ろ** に降格 (skip ではない)、他 error 時は既存通り Layer 2 より先。 |
| Layer 2 | role chain (`auto_fallback_roles_for`、PLAN-037 W-1) | `HELIX_CODEX_AUTO_FALLBACK=1` opt-in + usage_limit 時のみ発火 | 同 opt-in 維持。usage_limit error 時に **Layer 1 より先** に試行する優先度反転を導入。Layer 2 chain 全試行失敗後に Layer 1 へ fallback 復帰。 |

不変条件:
- usage_limit error 時 + `HELIX_CODEX_AUTO_FALLBACK=1` 時のみ Layer 2 が Layer 1 より先に発火する。それ以外は既存通り。
- Layer 0 (明示) は常に最優先で bypass されない。
- rate_limit / その他 error は既存仕様 (Layer 0 → Layer 1 → 終了) を維持、Layer 2 は発火しない。
- `HELIX_CODEX_AUTO_FALLBACK=0` (default) では Layer 2 が完全に発火しない。

### §3.2 W-23: `helix plan finalize` の運用組み込みと lint auto-run

PLAN finalize の実運用で lint が通過前に finalize されると、重複や整合崩れを見逃す。

本 Sprint では次を扱う。

- `cmd_finalize` 内で `lint --duplicates` を auto-run する。
- duplicate 検出時は finalize を block し、理由を明示する。
- `--no-lint` による bypass を許可し、緊急回避手段を残す。
- Opus が `helix plan finalize` を direct Edit の代替として使う運用ガイダンスを整備する。

### §3.3 W-4: `helix-codex --concurrent-from` auto-detect と bats-cleanup 定期運用

並列投入時に baseline post-validation が未指定のまま進むと、並列作業の収束判定が弱くなる。

本 Sprint では次を扱う。

- `--plan-id` 指定時に、同一 PLAN の他 Codex process を検知した場合のみ `--concurrent-from` 相当の baseline を auto-add する。
- 誤検知ゼロを前提に、他 PLAN を誤って同一 PLAN と判定しない条件を固定する。
- `helix bats-cleanup --delete` の定期運用を、test 完了後または hook 相当の手順として文書化する。

### §3.4 W-5: 統合検証と運用完了

3 Sprint の結果を横断照合し、PLAN-039 として次の運用段階へ引き渡せる状態にする。

- W-1 / W-23 / W-4 の受入条件を照合する。
- 残件を次 Sprint に切り出す。
- 運用手順、監査観点、完了報告の証跡を本文と一致させる。

## §4 Sprint 詳細

### §4.1 全体構成

- W-1: HELIX_CODEX_AUTO_FALLBACK Layer 2 先行発火化
- W-23: `helix plan finalize` の lint auto-run + finalize block
- W-4: `helix-codex --concurrent-from` auto-detect + bats-cleanup 定期運用
- W-5: 統合検証 + retro + status completed

| Sprint | 役割 / 規模 | 担当 | 主要作業 | 成功条件 | 受入 / 検証 |
|---|---|---|---|---|---|
| W-1 | Code / tooling（M） | SE | `cli/helix-codex` の fallback 優先度再設計、usage_limit 検知時の Layer 2 先行試行、互換性維持の分岐整理 | usage_limit で Layer 2 が先に試行される | bats / mock test 追加 |
| W-23 | Code / docs（M） | TL / Docs | `cli/helix-plan` の finalize へ lint auto-run を統合、運用ガイダンス整備、`--no-lint` bypass 追加 | duplicate 検出時に finalize が block される | bats 追加 PASS |
| W-4 | Code / ops-doc（M） | SE / Docs | `cli/helix-codex` の auto-detect、`helix bats-cleanup` の定期運用導線整備 | 並列投入時のみ baseline が補完される | bats / 運用手順確認 |
| W-5 | Docs / Validation（S） | Docs / TL / PM | 3 Sprint の結果統合、retro 反映、完成判定 | 受入条件が一読で判断できる | 統合レビュー |

### §4.2 W-1

- 目的: `HELIX_CODEX_AUTO_FALLBACK` の発火順を調整し、usage_limit 系の観測時に Layer 2 が Layer 1 より先に試行されるようにする (Layer 0 は常に最優先で不変)。
- Layer 順序仕様 (§3.1 表 を実装):
  - usage_limit error 時 + `HELIX_CODEX_AUTO_FALLBACK=1`: Primary fail → Layer 0 (明示時のみ) → Layer 2 (role chain 全試行) → Layer 1 (default_fallback) → 終了
  - usage_limit 以外 (rate_limit / network / その他): Primary fail → Layer 0 → Layer 1 → 終了 (Layer 2 発火なし、既存通り)
  - `HELIX_CODEX_AUTO_FALLBACK=0` (default): Primary fail → Layer 0 → Layer 1 → 終了 (Layer 2 完全 skip、既存通り)
- 想定実装:
  - cli/helix-codex line 1262-1282 周辺の Layer 0/1/2 dispatch を再構成。
  - error_type 判定 (usage_limit) を Layer 1 dispatch 直前で実施し、auto_fallback opt-in 時に Layer 2 を先に試行する分岐を追加。
  - Layer 2 chain が全 role 失敗した場合、Layer 1 default_fallback への復帰経路を保証 (既存 logic 再利用)。
- 不変条件:
  - Layer 0 (明示 `--fallback-model`) は常に最優先で bypass 不可。
  - usage_limit + auto_fallback=1: Layer 2 が Layer 1 より先に発火、Layer 2 全失敗後に Layer 1 復帰。
  - rate_limit / その他 error: Layer 2 は発火しない、既存 Layer 0/1 logic 維持。
  - `HELIX_CODEX_AUTO_FALLBACK=0`: Layer 2 完全 skip、既存通り。
- 依存:
  - PLAN-037 W-1 の auto-fallback 実装 (`auto_fallback_roles_for` / `run_auto_role_fallback_chain`)。
  - cli/helix-codex の Layer 判定と prompt 生成経路 (line 651-652 / 763 / 1262-1282)。
- DoD:
  - 5 ケースの bats / mock test を新規追加し、以下のすべてを再現可能:
    1. usage_limit + AUTO_FALLBACK=1 + 明示 `--fallback-model`: Layer 0 が最優先で発火 (Layer 2 より先)
    2. usage_limit + AUTO_FALLBACK=1: Layer 2 が Layer 1 より先に発火
    3. usage_limit + AUTO_FALLBACK=0: Layer 1 default_fallback が発火、Layer 2 skip
    4. rate_limit + AUTO_FALLBACK=1: Layer 1 default_fallback が発火、Layer 2 skip
    5. Layer 2 chain 全失敗 + AUTO_FALLBACK=1: Layer 1 default_fallback に復帰
  - 既存テスト (cli/tests/test-helix-codex-auto-fallback.bats 4 ケース) regression なし。

### §4.3 W-23

- 目的: `helix plan finalize` の実行時に lint を自動実行し、重複がある場合は finalize を block する。
- 想定実装:
  - `cmd_finalize` で `lint --duplicates` を自動実行する。
  - duplicate 検出時は finalize を止め、警告を返す。
  - `--no-lint` で bypass 可能にする。
  - Opus が direct Edit せず finalize を運用経路として使う旨の説明を、CLAUDE / memory feedback 相当の運用文書へ反映する。
- 不変条件:
  - PLAN-031〜038 で finalize PASS していたケースは、新仕様でも PASS する。
  - duplicate がある場合のみ finalize block になる。
  - `--no-lint` は明示的な bypass として機能する。
- 依存:
  - PLAN-038 W-4 で整えた lint duplicate 検出の前提。
  - `cli/helix-plan` の finalize 経路。
- DoD:
  - auto-lint の動作を bats で確認できる。
  - duplicate 検出時に exit 1 と警告メッセージを返せる。
  - `--no-lint` による bypass が動作する。

### §4.4 W-4

- 目的: `--plan-id` 指定時の並列 Codex 実行を検知し、baseline post-validation を自動補完する。
- 想定実装:
  - 同一 PLAN の他 Codex process を検知した場合のみ `--concurrent-from` 相当の baseline を auto-add する。
  - 他 PLAN を誤って同一 PLAN と判定しない条件を固定する。
  - `helix bats-cleanup --delete` の定期運用を、test 完了後または hook 相当の運用手順として明文化する。
- 不変条件:
  - 誤検知ゼロを前提とする。
  - baseline auto-add は、並列実装時のみ発火する。
  - bats-cleanup の定期運用は、既存テストの収束を壊さない。
- 依存:
  - PLAN-036 W-1 の concurrent-from 実装。
  - PLAN-036 W-3 の bats-cleanup 実装。
- DoD:
  - `--plan-id` 指定時に他 Codex process 検知で baseline auto-add が発火する。
  - bats-cleanup の運用ガイダンスが本文で追える。
  - 誤検知ゼロの前提が検証計画に明記される。

### §4.5 W-5

- 目的: 3 Sprint の結果を統合し、次の作業へ引き渡せる状態にする。
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

- usage_limit error で Layer 2 が先に発火する。
- Layer 0/1 fallback は、他 error type で継続動作する。
- fallback 優先度の変更後も、既存の主要ケースで regression がない。

### §5.2 W-23 DoD

- `helix plan finalize` で `lint --duplicates` が auto-run される。
- duplicate 検出時に finalize が block される。
- `--no-lint` による bypass が機能する。
- 既存 finalize PASS ケースの通過率を落とさない。

### §5.3 W-4 DoD

- `--plan-id` 指定時に、同一 PLAN の他 process 検知で baseline auto-add が発火する。
- 他 PLAN を誤検知しない。
- `helix bats-cleanup --delete` の定期運用が文書として追跡できる。

### §5.4 W-5 DoD

- 3 Sprint の完了条件が一つの文書から追跡できる。
- 次 Sprint の課題が独立に抽出できる。
- 運用化と検証の境界が明確である。

## §6 検証計画

### §6.1 W-1

- `cli/tests/test-helix-codex-auto-fallback.bats` を拡張する。
- 5〜8 ケースで以下を確認する:
  - usage_limit error 時の Layer 2 先行発火。
  - Layer 2 失敗時の Layer 0/1 fallback。
  - 他 error type で既存 fallback が継続すること。
  - default 値変更時も regression がないこと。
- mock test で Layer 選択の優先度を再現する。

### §6.2 W-23

- `cli/tests/test-helix-plan-finalize-frontmatter.bats` を拡張する。
- 既存 finalize PASS ケース回帰防止 fixture:
  - PLAN-031 / 032 / 033 / 034 / 035 / 036 / 037 / 038 の 8 PLAN を fixture (read-only copy) として `cli/tests/fixtures/plan-finalize-regression/` に配置 (本 PLAN 対象外で実装、または bats setup で git ls-tree から `:`expand)。
  - 各 fixture に対して `helix plan finalize <fixture>` 相当を mock 実行し、`lint --duplicates` auto-run 後に exit 0 (duplicate なし) を確認。
- 以下のテスト matrix を確認する:

| ケース | 入力 | 期待 exit | 期待 block message |
|---|---|---|---|
| auto-lint pass | duplicate なし fixture (PLAN-031〜038) | 0 | (なし) |
| auto-lint block | duplicate あり fixture (mock) | 1 | "duplicate detected" を含む |
| `--no-lint` bypass | duplicate あり fixture + `--no-lint` | 0 | (なし) |
| 既存 finalize PASS | PLAN-001 (legacy YAML 単独) | 0 | (なし、yaml 単独 fallback) |

### §6.3 W-4

- `cli/tests/test_helix_codex_allowed_files.bats` を拡張する。
- auto-detect 入力源 (信頼境界):
  - 同一 PLAN 検出は `.helix/audit/codex-runs/*-<plan-id>-*.log` の存在 + `.helix/tmp/codex-baseline-<pid>-<stamp>.txt` の plan_id metadata + pid 生存 (`os.kill(pid, 0)`) の **3 条件 AND** で判定。
  - PLAN-036 W-1 で導入した `--concurrent-from` 5 条件信頼境界 (realpath / PROJECT_ROOT 配下 / regex / symlink reject / 実在) を継承。
- 検証 matrix (誤検知ゼロを担保):

| ケース | 入力 | 期待挙動 |
|---|---|---|
| same plan positive | 同一 plan_id の他 codex process 1 件 + 有効 baseline | auto-add 発火、baseline 1 件追加 |
| different plan negative | 別 plan_id の codex process | auto-add 発火しない |
| no plan-id negative | `--plan-id` 未指定 | auto-add 完全 skip |
| stale pid negative | baseline file 存在だが pid 既に終了 | auto-add 発火しない (stale 判定) |
| forged baseline reject | `.helix/tmp/` 外の baseline path | auto-add 発火しない (信頼境界違反) |
| symlink reject | symlink baseline path | auto-add 発火しない (PLAN-036 W-1 reject) |

- bats-cleanup の定期運用ガイダンス:
  - cli/helix-test 完了 hook (post-run) で `helix bats-cleanup --list` を実行し、5 件以上残存があれば warning 表示する案を本文に明記。
  - 自動 `--delete` は scope 外 (誤削除リスク回避)、ユーザー実行を runbook で誘導。

### §6.4 W-5

- 3 Sprint の検証結果を横断照合する。
- retro 反映後の次アクションが曖昧でないことを確認する。
- 完了判定の根拠をまとめる。
- **PLAN-038 W-23 footer 効果測定 (受入条件):**
  - W-1 / W-23 / W-4 の各 Codex 委譲完了報告に `intermediate_errors:` 欄が独立して含まれていることを確認する (3/3 が DoD)。
  - `tests:` 欄に "clean checkout" キーワードが含まれることを確認する (3/3 が DoD、または 2/3 + 不足理由を P3 debt 化)。
  - 達成率 ≤ 2/3 の場合、PLAN-040 候補に "Codex prompt template への syntax check 強化" を明示。
  - 達成率 = 3/3 の場合、W-23 footer 拡張は構造的に有効と判定し、運用継続。

## §7 Out of Scope

- D-API / D-DB / D-CONTRACT の変更。
- 既存 API の破壊的変更。
- schema migration の新規作成。
- 認証 / 認可 / 決済 / PII / secret / env / credentials の扱い変更。
- `helix plan finalize` の全面的な再設計。
- `helix-codex` の並列実行モデルそのものの再設計。
- `helix bats-cleanup` の削除ロジックの根本的変更。
- PLAN-035〜038 自体の本文全面書き換え。
- 本 PLAN 以外のドキュメント構造変更。
- `HELIX_CODEX_AUTO_FALLBACK` の Layer 0/1 互換性を壊す仕様変更。
- 誤検知を許容する auto-detect ルールの導入。

## §7.1 PLAN-038 retro 候補の本 PLAN 採否 / P3 debt register

PLAN-038 retro (.helix/retros/PLAN-038.md) で carry した 5 候補の本 PLAN 採否は以下:

| 候補 | 起源 | 本 PLAN 採否 | 理由 / carry 先 |
|---|---|---|---|
| 1. cli/helix-plan subcommand 別ファイル分割 | PLAN-038 retro Try #1 | **P3 debt (PLAN-040 候補へ carry)** | 並列 commit 分割の構造改善は scope 大 (cli/helix-plan 全体 refactor)、本 PLAN は運用化 focus のため carry。 |
| 2. legacy PLAN markdown frontmatter 後付け migration | PLAN-038 retro Try #2 | **P3 debt (PLAN-040 候補へ carry)** | PLAN-001-poc-skill.md 等の migration は graceful fallback (PLAN-038 W-1 で実装済) で実害なし。本 PLAN scope 外、定期 cleanup タイミングで実施。 |
| 3. Codex 完了報告 footer 効果測定 | PLAN-038 retro Try #3 | **採用 (W-5 §6.4 で測定受入条件化)** | 本 PLAN の Codex 委譲を通じて自然に観察可能、W-5 で集計。 |
| 4. gpt-5.3-codex-spark usage limit primary 一時切り替え | PLAN-038 retro Try #4 | **P3 debt (PLAN-040 候補へ carry)** | spark usage limit は May 13 まで継続、本 PLAN W-1 の auto-fallback Layer 2 改善で usage_limit 経路は構造改善。primary 切り替え helper は別途 PLAN-040 で扱う。 |
| 5. concurrent reader 中間状態観測不可保証 (lock 機構) | PLAN-038 W-1 P3 debt | **P3 debt (PLAN-041 候補へ carry)** | lock 機構導入は scope 大 (`helix lock` 拡張 or fcntl.flock 全面導入)、本 PLAN は永続整合性保証のみ拡張せず。 |

P3 debt は次回 retro (`/.helix/retros/PLAN-039.md`) で改めて採否を判断する。

## §8 関連

- [PLAN-038](PLAN-038-codex-prompt-and-plan-workflow-tightening.md)
- [PLAN-037](PLAN-037-codex-fallback-and-lint-expansion.md)
- [PLAN-036](PLAN-036-codex-post-validation-and-bats-cleanup.md)
- [PLAN-035](PLAN-035-helix-review-and-bats-cleanup.md)
- [ADR-014](../adr/ADR-014-roles-config-format.md)
- [ADR-015](../adr/ADR-015-helix-v2-orchestration.md)

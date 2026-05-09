---
plan_id: PLAN-041
title: PLAN-041（SUMMARY marker prompt 強化 + legacy frontmatter progressive migration + Codex bats bootstrap runbook）
status: completed
created: 2026-05-10
finalized: 2026-05-10
author: Opus (PM)
size: M
phases: L1→L2→L3→L4
gates: G1, G2, G3, G4
completed: 2026-05-10
acceptance:
  - W-1: 本 PLAN の Codex 委譲で SUMMARY marker 採用率 ≥ 50% 達成、未達なら案 B (諦め) を PLAN-042 に carry。
  - W-23: PLAN-001-poc-skill.md 含む 3 件以内の legacy PLAN に frontmatter 後付け、body-preservation hash 検証 PASS。
  - W-4: cli/helix-test で bats 不在時 warning 動作、docs/runbook/codex-test-bootstrap.md で minimal install 手順記載。
related: [PLAN-040, PLAN-039, PLAN-038, PLAN-001, ADR-014, ADR-015]
---

## §1 目的

PLAN-040 retro で carry した 4 候補のうち、scope が中規模で本 PLAN にまとめて解消できる 3 件を集約する。lock 機構のように scope が大きいものは carry し、PLAN-042 へ送る。

本 PLAN の狙いは、運用実態と文書上の設計意図を一致させることにある。

1. PLAN-040 W-23 で導入した SUMMARY marker filter の設計意図と実運用の乖離を解消する。
2. legacy PLAN markdown に frontmatter を段階的に後付けし、parser / lint の正規経路を増やす。
3. Codex 委譲環境で bats / pytest が不足していても、warning と runbook で回避手順を明確にする。

W-1 は「案 A: prompt 強化 → 再観測」を先に行い、採用率が 50% に届かなければ案 B を PLAN-042 へ carry する。
W-23 は 3 件以内に scope を限定し、残る legacy PLAN は後続 PLAN へ分割する。
W-4 は自動インストールを行わず、warning と文書ガイドだけで運用の詰まりを減らす。

## §2 全体方針

### §2.1 設計原則

- W-1 は既存 footer 効果を壊さない追加変更に限定する。
- W-23 は body 完全保持を最優先とし、frontmatter 追加以外を行わない。
- W-4 は `cli/helix-test` の warning と `docs/runbook/codex-test-bootstrap.md` の案内に閉じる。
- W-5 は 3 Sprint の統合検証と retro を担い、必要に応じて push 前の最終整合確認まで含める。

### §2.2 スコープ境界

- W-1 は `cli/helix-codex` の `HELIX_CODEX_OUTPUT_FOOTER` に限る。
- W-23 は `docs/plans/PLAN-001-poc-skill.md` / `docs/plans/PLAN-002-helix-fullauto-foundation.md` / `docs/plans/PLAN-003-auto-restart-foundation.md` の 3 件に限定する。
- W-4 は `cli/helix-test` の環境変数チェックと runbook 新規作成に限定する。
- lock 機構や concurrent reader の中間状態保証は scope 外であり、PLAN-042 へ送る。

### §2.3 参照関係

- [PLAN-040](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-040-helix-plan-split-and-codex-summary-isolation.md) を直近の carry 集約例として参照する。
- [PLAN-039](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-039-undeployed-feature-activation.md) を footer / 運用発火の前段参照として扱う。
- [PLAN-038](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-038-codex-prompt-and-plan-workflow-tightening.md) を prompt / finalize 運用の前段参照として扱う。
- [PLAN-001](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-001-poc-skill.md) を legacy migration の最初の正規化対象として扱う。
- [ADR-014](/home/tenni/ai-dev-kit-vscode/docs/adr/ADR-014-roles-config-format.md) / [ADR-015](/home/tenni/ai-dev-kit-vscode/docs/adr/ADR-015-helix-v2-orchestration.md) をロール定義と orchestration の正本として扱う。

## §3 解決対象

### §3.1 W-1: SUMMARY marker prompt 強化 + 再観測

PLAN-040 W-23 で導入した marker filter は、audit log 観測で設計意図と実運用が一致していない。

**採用率 baseline (Round 1 投入時点):**
- 旧 baseline (PLAN-040 中、W-23 commit `927e3c4` 前): 11 件中 marker 付き 0 件 = **0%**
- 現行 baseline (commit `927e3c4` 後): 4 件中 marker 付き 1 件 = **25%** (PLAN-041 W-0a docs role 委譲で初発動を観測)
- 集計対象: `.helix/audit/codex-runs/*.log` のうち commit 927e3c4 以後 (`stat --format=%Y` で filter)、`-stderr.log` を除外、`recommender` role を除外 (recommender は marker 必須対象外、別 fmt)
- 除外条件: dry-run / draft 試行失敗 (3 回 retry の途中) は分母に含めない、最終成功委譲のみ counting

本 Sprint では prompt 側を強化し、Codex 委譲時に marker を見落としにくい形へ寄せる。

- `HELIX_CODEX_OUTPUT_FOOTER` の冒頭 1-2 行目に marker 指示を前倒しする。
- footer 内に concrete output 例を追加し、出力例の見つけやすさを上げる。
- 既存の `intermediate_errors` / `tests: clean checkout` の意味は変えない。
- 強化後に即時再観測し、Codex 委譲の採用率を 50% 以上に引き上げられるか確認する。

不変条件:

- 既存 footer のフィールド構成は破壊しない。
- marker 指示は追加であり、既存の summary 抽出契約を削除しない。
- 採用率判定の母集団: 本 PLAN-041 の W-N 委譲 (W-1 / W-23 / W-4 / W-0c TL Round 2) を分母とし、最終成功委譲のみ counting。サンプル数 n ≥ 4 を確保する。
- n < 4 の場合 (サンプル不足): inconclusive 判定とし、PLAN-042 で再観測 (本 PLAN は inconclusive carry)。
- n ≥ 4 で採用率 ≥ 50% 達成: 案 A 成功、運用継続。
- n ≥ 4 で採用率 < 50% 未達: 案 B (諦め、末尾 N 行 default) を PLAN-042 へ carry。

### §3.2 W-23: legacy PLAN markdown frontmatter progressive migration

legacy PLAN markdown は一括 20 件更新ではなく、3 件以内の progressive migration に限定する。

対象は次の 3 件とする。

- `docs/plans/PLAN-001-poc-skill.md`
- `docs/plans/PLAN-002-helix-fullauto-foundation.md`
- `docs/plans/PLAN-003-auto-restart-foundation.md`

この Sprint の目的は、本文を完全保持したまま frontmatter を後付けし、parser / lint の正規経路を増やすことである。

解決内容:

- frontmatter を後付けしても本文の H1 / 章立て / 段落内容は変えない。
- migration 前後で body-preservation hash が一致することを検証する。
- `cli/lib/tests/test_plan_frontmatter.py` に hash 検証を追加する。
- 3 件以内に限定することで auto mode classifier の block を避け、ユーザー確認なしで進行可能にする。

不変条件:

- frontmatter 追加以外の本文改変を行わない。
- 3 件を超える migration は本 PLAN では行わない。
- 残りの legacy PLAN は PLAN-042 以降へ progressive 継続する。

### §3.3 W-4: Codex 委譲環境 bats / pytest bootstrap

Codex 委譲環境では、bats も pytest も必ずしも揃っていない。ここで自動インストールに寄せると誤動作リスクが高いので、警告と runbook に閉じる。

本 Sprint では次を扱う。

- `cli/helix-test` に `HELIX_CODEX_INTERNAL=1` 時の bats / pytest 不在検出を追加する。
- 不在時は warning を出し、bootstrap runbook を参照させる。
- `docs/runbook/codex-test-bootstrap.md` を新規作成し、minimal install 手順と Codex 環境への注入方法を明記する。
- 自動 bats install は scope 外とする。

不変条件:

- `HELIX_CODEX_INTERNAL` がない通常実行では挙動を変えない。
- warning だけで実行を無理に継続させない。
- runbook は最小手順に限定し、環境依存の回避策を明文化する。

### §3.4 W-5: 統合検証 + retro + push + footer 再観測

W-1 / W-23 / W-4 は独立 Sprint として並列に進められるが、最終的には 1 つの PLAN として整合していなければならない。

本 Sprint では次を扱う。

- 3 Sprint の DoD を横断確認する。
- push 前の最終整合確認を含め、本文と実装方針のズレを潰す。
- SUMMARY marker の再観測結果を本文へ反映する。
- carry した 1 件を PLAN-042 候補として固定する。

## §4 Sprint 詳細

### §4.1 全体構成

| Sprint | 役割 / 規模 | 実装担当 | レビュー担当 | 主要作業 | 成功条件 | 受入 / 検証 |
|---|---|---|---|---|---|---|
| W-1 | Code / prompt（M） | SE / Docs | TL review | `HELIX_CODEX_OUTPUT_FOOTER` の marker 指示前倒し、出力例追加、再観測 | marker 指示が冒頭に来る | footer snapshot / 再観測 |
| W-23 | Docs / migration（M） | Docs (Codex) | TL review | 3 件の legacy PLAN に frontmatter 後付け、body hash 検証 | body が変わらない | pytest / lint |
| W-4 | Ops-doc / tooling（M） | SE / Docs | TL review | `cli/helix-test` の warning 追加、bootstrap runbook 新規作成 | bats / pytest 不在時に warning | CLI smoke / docs review |
| W-5 | Integration / release（S） | Docs (Codex) for retro / Opus for commit composition | TL / PM acceptance | 3 Sprint の統合検証、retro、push 前整合、採用率再観測 | 1 文書で追跡可能 | 統合レビュー |

### §4.2 W-1 詳細

#### L2/L3 設計

- `HELIX_CODEX_OUTPUT_FOOTER` は marker 抽出の正本であり、marker 指示を前半へ寄せる。
- footer には concrete output 例を持たせ、Codex が何を出せばよいかを明示する。
- `intermediate_errors` と `tests: clean checkout` はそのまま維持する。
- 既存 footer 効果を壊さないため、構造変更は追加のみとする。

#### L4 Sprint 内容

- `cli/helix-codex` の footer テンプレートを更新する。
- `cli/tests/test_helix_codex_footer.bats` を拡張し、marker 指示の位置と出力例セクションを確認する。
- 実運用相当の Codex 委譲を再実施し、marker 採用率を測定する。

#### 依存関係

- PLAN-040 W-23 の footer / summary 抽出契約が前提である。
- `intermediate_errors` / `tests: clean checkout` の既存運用を壊さないことが前提である。

#### 並列実行可能性

- W-23 / W-4 と並列で進められる。
- footer テンプレート以外の共通 helper には触れないため、ファイル衝突は小さい。

#### DoD の観点

- footer に「出力例」セクションがある。
- marker 指示が冒頭 1-2 行目にある。
- `intermediate_errors` / `tests: clean checkout` が引き続き出力される。
- 再観測で marker 採用率 ≥ 50% を目指し、未達なら PLAN-042 へ carry する。

### §4.3 W-23 詳細

#### L2/L3 設計

- 3 件の legacy PLAN を progressive migration の最初のスライスとして扱う。
- 本文は完全保持し、frontmatter の後付けのみで正規化を進める。
- body-preservation hash は migration 前後で一致させる。
- frontmatter 追加により parser / lint の例外経路を増やさない。

#### L4 Sprint 内容

- `docs/plans/PLAN-001-poc-skill.md` / `docs/plans/PLAN-002-helix-fullauto-foundation.md` / `docs/plans/PLAN-003-auto-restart-foundation.md` に frontmatter を追加する。
- `cli/lib/tests/test_plan_frontmatter.py` に body-preservation hash 検証を追加する。
- `helix plan lint` で frontmatter parse 可能性を確認する。

#### 依存関係

- 既存の plan_frontmatter 互換経路が前提である。
- PLAN-040 までに整えた plan lint の基礎観測を前提とする。

#### 並列実行可能性

- W-1 / W-4 と並列可能である。
- 3 件に限定するため、広域の legacy file 一括更新と競合しにくい。

#### DoD の観点

- 3 件の frontmatter 後付けが完了する。
- body-preservation hash が前後一致する。
- `helix plan lint` で PASS する。
- 本 PLAN では 3 件を超える migration を行わない。

### §4.4 W-4 詳細

#### L2/L3 設計

- `HELIX_CODEX_INTERNAL=1` の場合のみ bats / pytest の存在チェックを強める。
- 不在時は warning を出し、runbook へ誘導する。
- `docs/runbook/codex-test-bootstrap.md` には minimal install 手順と Codex 環境への注入方法を記す。
- 自動 install や dependency mutation は行わない。

#### L4 Sprint 内容

- `cli/helix-test` に bats / pytest 不在 warning を追加する。
- `docs/runbook/codex-test-bootstrap.md` を新規作成する。
- runbook に minimal install、PATH / env 注入、再実行確認の手順を記載する。

#### 依存関係

- 既存の `cli/helix-test` の挙動を前提とする。
- 外部 package manager の導入や環境変数追加は scope 外である。

#### 並列実行可能性

- W-1 / W-23 と並列可能である。
- docs 追加と warning 追加は責務が分かれているため、衝突しにくい。

#### Exit semantics decision table

| 実行モード | bats 不在 | pytest 不在 | 期待 exit | stderr 出力 |
|---|---|---|---|---|
| 通常 (`./cli/helix-test`) | あり | あり | 0 (既存挙動維持、skip 扱い) | (なし、既存通り) |
| `HELIX_CODEX_INTERNAL=1 ./cli/helix-test` | あり | あり | 0 (warning のみ、fail にはしない) | `[helix-test] WARNING: bats not found, see docs/runbook/codex-test-bootstrap.md` |
| `HELIX_CODEX_INTERNAL=1` + 全揃い | なし | なし | 0 (既存通り) | (なし) |
| 通常 + `--strict-deps` (新規 option、PLAN-041 では実装しない、PLAN-042 候補) | あり | あり | 1 | `[helix-test] ERROR: bats not found (required by --strict-deps)` および `[helix-test] ERROR: pytest not found (required by --strict-deps)` を combined message として明示 |

通常実行は挙動不変、`HELIX_CODEX_INTERNAL=1` は stderr warning + runbook path 表示。`--strict-deps` の fail mode は本 PLAN scope 外、PLAN-042 候補へ carry。

#### DoD の観点

- `HELIX_CODEX_INTERNAL=1` かつ bats 不在時に warning が出る (exit 0 維持)。
- 通常実行 (HELIX_CODEX_INTERNAL=0) では warning が出ない (既存挙動完全互換)。
- runbook に minimal install 手順がある。
- auto install が導入されていない。

### §4.5 W-5 詳細

#### L2/L3 設計

- 3 Sprint の成果を 1 つの PLAN として整合させる。
- 採用率の最終観測結果と carry 判定を本文へ固定する。
- push 前の最終確認は、この PLAN の完了条件に含める。

#### L4 Sprint 内容

- W-1 / W-23 / W-4 の受入条件を照合する。
- SUMMARY marker の再観測結果を本文に反映する。
- retro の採否と carry の行き先を確定する。

#### 依存関係

- W-1 / W-23 / W-4 の成立を前提とする。
- いずれかが未達なら、W-5 は統合失敗として扱う。

#### 並列実行可能性

- なし。統合作業のため単独 Sprint とする。

#### DoD の観点

- 3 Sprint の完了条件が 1 文書で追える。
- carry 1 件が PLAN-042 候補として固定される。
- 完了条件と本文が一致する。

## §5 DoD

### §5.1 PLAN 全体 DoD

- SUMMARY marker 採用率の再観測結果が本文へ反映されている。
- legacy PLAN 3 件の frontmatter 後付けと body-preservation hash 検証が完了している。
- `cli/helix-test` の bats / pytest warning 方針と runbook が本文から追える。
- carry 1 件が PLAN-042 へ送られている。

### §5.2 W-1 DoD

- footer の marker 指示が冒頭 1-2 行目にある。
- footer に「出力例」セクションがある。
- `intermediate_errors` / `tests: clean checkout` を壊していない。
- 再観測で marker 採用率 ≥ 50% を達成、または未達を明示して PLAN-042 へ carry する。

### §5.3 W-23 DoD

- 指定 3 件に frontmatter が後付けされている。
- body-preservation hash が前後一致している。
- `helix plan lint` で PASS している。
- 3 件を超える migration は行っていない。

### §5.4 W-4 DoD

- `HELIX_CODEX_INTERNAL=1` 時に bats / pytest 不在 warning が動作する。
- `docs/runbook/codex-test-bootstrap.md` に minimal install 手順がある。
- 自動 install が scope に入っていない。

### §5.5 W-5 DoD

- 3 Sprint の結果が 1 文書で追跡できる。
- carry 1 件の行き先が明示されている。
- 本文と完了条件が一致している。

## §6 検証計画

### §6.1 W-1

- `cli/tests/test_helix_codex_footer.bats` を拡張し、marker 指示の位置と出力例セクションを検証する。
- 既存 footer field preservation regression test:
  - footer に `intermediate_errors:` が残ることを snapshot test で固定 (PLAN-038 W-23 効果保持)
  - footer に `tests:` が残ることを snapshot test で固定
  - dry-run 出力 + marker 欠落 graceful fallback (tail -n 30) の両方で `intermediate_errors` / `tests:` が tail-30 内に到達することを確認
- Codex 委譲の再観測を実施し、採用率を計測する (本 PLAN-041 W-N の最終成功委譲のみ counting、n ≥ 4)。
- 採用率算出スクリプト (母集団定義 §3.1 と整合):
  ```bash
  # 1. 対象 log 一覧 (PLAN-041 の W-1 / W-23 / W-4 / W-0c のみ、stderr / recommender 除外、retry 複数回は最終成功 run のみ手動選定)
  TARGETS=(
    "$(ls -t .helix/audit/codex-runs/*-PLAN-041-W-1.log 2>/dev/null | head -1)"
    "$(ls -t .helix/audit/codex-runs/*-PLAN-041-W-23.log 2>/dev/null | head -1)"
    "$(ls -t .helix/audit/codex-runs/*-PLAN-041-W-4.log 2>/dev/null | head -1)"
    "$(ls -t .helix/audit/codex-runs/*-PLAN-041-W-0c.log 2>/dev/null | head -1)"
  )
  # 2. denominator (n) と numerator (marker hit) を集計
  DENOM=0; NUMER=0
  for f in "${TARGETS[@]}"; do
    [[ -n "$f" && -f "$f" ]] || continue
    [[ "$f" == *stderr* ]] && continue
    DENOM=$((DENOM+1))
    grep -q "^---SUMMARY_START---$" "$f" && NUMER=$((NUMER+1))
  done
  echo "marker adoption: $NUMER / $DENOM"
  ```
- 判定: n=DENOM ≥ 4 で採用率 = NUMER / DENOM ≥ 0.5 なら案 A 成功、< 0.5 なら案 B carry。n < 4 なら inconclusive carry。

### §6.2 W-23

- `cli/lib/tests/test_plan_frontmatter.py` を拡張し、frontmatter 追加前後の body hash 一致を確認する。
- 3 件の migration 後に `helix plan lint` を実行し、parse 可能性を確認する。
- 本文が変わっていないことを手動で確認する。

### §6.3 W-4

- `HELIX_CODEX_INTERNAL=1` で `cli/helix-test` を実行し、bats / pytest 不在時 warning を確認する。
- `docs/runbook/codex-test-bootstrap.md` の minimal install 手順をレビューする。
- warning 文言が runbook 参照へつながっているかを確認する。

### §6.4 W-5

- W-1 / W-23 / W-4 の結果を横断照合する。
- carry 1 件の扱いを本文に反映する。
- push 前の最終整合確認が済んでいるかを確認する。

## §7 Out of Scope

- 4 件目の lock 機構は扱わない。
- `cli/helix-test` の自動 bats install は扱わない。
- legacy PLAN の 3 件を超える frontmatter migration は扱わない。
- `cli/lib/plan_frontmatter.py` の parser 仕様変更は扱わない。
- 外部 API / infrastructure / secret / env の追加変更は扱わない。

### §7.1 P3 debt register

PLAN-040 retro で carry された 4 候補のうち、本 PLAN の採否は次の通りとする。

| # | 候補 | 判定 | 理由 / 扱い |
|---|---|---|---|
| 1 | SUMMARY marker filter 設計意図と実運用の乖離解消 | 採用 | prompt 強化と再観測で中規模の範囲に収まり、既存 footer 効果を壊さず解消できるため。 |
| 2 | legacy PLAN markdown frontmatter progressive migration | 採用 | 3 件以内の progressive migration に縮小することで auto mode classifier の block を避け、本文保持も検証できるため。 |
| 3 | Codex 委譲環境の bats / pytest bootstrap | 採用 | warning と runbook のみに閉じれば scope 小で、誤動作リスクを増やさず運用改善できるため。 |
| 4 | concurrent reader 中間状態観測不可保証（lock 機構） | carry | scope が大きく、lock 機構導入は本 PLAN の責務を超えるため PLAN-042 へ送る。 |

## §8 関連

- [PLAN-040](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-040-helix-plan-split-and-codex-summary-isolation.md)
- [PLAN-039](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-039-undeployed-feature-activation.md)
- [PLAN-038](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-038-codex-prompt-and-plan-workflow-tightening.md)
- [PLAN-037](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-037-codex-fallback-and-lint-expansion.md)
- [PLAN-036](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-036-codex-post-validation-and-bats-cleanup.md)
- [PLAN-001](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-001-poc-skill.md)
- [PLAN-002-helix-fullauto-foundation](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-002-helix-fullauto-foundation.md)
- [PLAN-003-auto-restart-foundation](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-003-auto-restart-foundation.md)
- [ADR-014](/home/tenni/ai-dev-kit-vscode/docs/adr/ADR-014-roles-config-format.md)
- [ADR-015](/home/tenni/ai-dev-kit-vscode/docs/adr/ADR-015-helix-v2-orchestration.md)

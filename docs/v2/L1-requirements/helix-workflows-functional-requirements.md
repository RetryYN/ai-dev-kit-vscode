---
doc_id: L1-helix-workflows-functional-requirements
title: "HELIX-workflows V2 機能要求 (Functional Requirements)"
status: draft
created: 2026-05-26
owner: PM
process_layer: L1
pairs_with: L14
next_pair_freeze: L3
canonical_source: HELIX-workflows/helix-process/L1-requirements.md
parent_plan: L1-helix-workflows-機能要求plan
related_l0: docs/v2/L0-helix-workflows/concept.md
---

# HELIX-workflows V2 機能要求 (Functional Requirements)

> **本 doc の位置づけ**: HELIX-workflows V2 dogfooding における **機能要求 (FR-*)** の L1 正本。L0 [見直し企画書](../L0-helix-workflows/concept.md) §5 / §6.5 / §8 と、L1 [業務要求 doc](./helix-workflows-business-requirements.md) で定義した BR を受け、HELIX が備えるべき機能を **要望レベル** で整理する。
>
> **境界**: 本 doc は L1 のため、API / schema / detector 実装詳細までは固定しない。詳細契約は L3 L3 3 PLAN (業務要件 / 機能要件 / 非機能要件)、技術詳細は L1 技術要求 plan、受入ペア凍結は L3↔L12 で確定する。
>
> **件数 (2026-05-26 tl-advisor G1 audit P0 #2 確定)**: 機能要求は **FR-01〜FR-12 (計 12 件)**。L3 詳細化 (G3 凍結) で更に細分化される。

> **SSoT 参照** (2026-05-26 doc-system-architect retrofit): ユビキタス言語 = [L0 §12 Glossary](../L0-helix-workflows/concept.md) / 業界標準整合 = §13 / Bounded Context = §14。本 doc は L0 §12-§14 を parent_doc reference とし、用語独自定義は行わない (anti-corruption layer)。

## §1 機能一覧

| FR-ID | 機能名 | 振り分け / 根拠 | 概要 |
|---|---|---|---|
| FR-01 | NSM 計測機能 | L1-IN-01 | Primary NSM「V-model 整合 PLAN 完遂数」を 6 axes (`layer / kind / pair_freeze / 4artifact / gate_pass / done`) で機械判定し、helix.db query で集計できること。 |
| FR-02 | Guardrail 3 軸 fail-close 機能 | L1-IN-02 | Pair Freeze Coverage、Agent Error Budget Consumption、TTFSP を相互独立に計測し、しきい値逸脱時は fail-close を発火できること。しきい値は少なくとも `Coverage < 80%`、`Error Budget > 5%`、`TTFSP > 30min` を扱えること。 |
| FR-03 | TDD 順序 fail-close 機能 | L1-IN-11 | L7 sprint 7 step (`S1 PLAN → S2 受入 test → S3 最小実装 → S4 3 点 review → S5 強化 test → S6 テスト → S7 修正`) の順序を機械強制し、S2 不在の S3 着手や S5 不在の S7 着手を block できること。 |
| FR-04 | 9 mode 入口判定機能 | L0 §6.5.2 | detector / signal により Discovery、Scrum、Reverse、Incident、Add-feature、Refactor、Retrofit、Research、Recovery の入口を機械判定し、推奨 route を返せること。 |
| FR-05 | gate 機械判定機能 | L0 §6.5.4 | `gate_verdict = static_subchecks AND ai_review_required_when(...)` の合成式で gate 判定でき、AI 判定が必要な gate でも static 部分は AI なしで先行実行できること。 |
| FR-06 | 影響範囲 query 機能 | L0 §5.3 | 機能改修 trigger から過去 trace を 5 秒以内に取得し、関連 PLAN / 設計 / テスト設計 / 実装 / mode_transition を横断して影響範囲を返せること。 |
| FR-07 | Forward 復帰 event 機能 | L1-IN-08 / L0 §6.5.2 | 9 mode の closure 時に Forward 復帰 event を記録し、昇格先 (`L1 / L3 / L4-L6 / L7-L14`) を機械判定できること。 |
| FR-08 | 4 artifact / pair freeze 監査機能 | L1-IN-04 | `parent_design` / `pairs_test_design` / trace link の存在を確認し、`expected_pair_freeze` / `expected_4artifact_trace` との差分を warn または fail-close で示せること。 |
| FR-09 | 資産 inventory / density 可視化機能 | L1-IN-06 | skill、CLI、PLAN、docs、helix.db schema を L0-L14 工程へ双方向 mapping し、工程別の密度と未整備箇所を可視化できること。 |
| FR-10 | layer context injection 機能 | L1-IN-07 | 対象工程に応じて mandatory skill、推奨 command、orchestration mode を自動注入し、AI の選択空間を工程単位で絞れること。 |
| FR-11 | discrepancy routing 機能 | L1-IN-05 / 08 / 10 | drift、trace 欠落、gate 不整合、mode 復帰漏れを `discrepancy_log` 相当で検知し、interrupt / recovery / reverse normalization / manual review のどれに送るかを提案できること。 |
| FR-12 | PLAN dependency / generates trace 機能 | L1-IN-03 / 09 | PLAN frontmatter の `dependencies` と `generates` を解釈し、上流下流関係と生成物 path の整合を機械的に追跡できること。 |

## §2 利用シナリオ

| UC-ID | シナリオ | 期待される機能 |
|---|---|---|
| UC-01 | PM が新規プロダクト企画を L0 起票し、L1 業務要求 / 機能要求 / 技術要求 / 非機能要求へ分解して次工程へ渡す | FR-01, FR-05, FR-12 |
| UC-02 | Codex SE が承認済みタスクを `helix plan` / `helix gate` / `helix handover` 経由で継続し、途中で interrupt なく L3 へ接続する | FR-03, FR-05, FR-12 |
| UC-03 | 本番障害 alert を入口に Incident mode が起動し、hotfix は L7、恒久対策は L1/L3/L4-L6、postmortem は L14 に並走接続する | FR-04, FR-07, FR-11 |
| UC-04 | AI 暴走または工程逸脱を検知し、Recovery mode に切り替えて設計差戻しと実装差戻しを分離する | FR-04, FR-10, FR-11 |
| UC-05 | 既存機能の差分改修時に、過去の PLAN / 設計 / テスト設計 / 実装 trace を検索して 5 秒以内に影響範囲を把握する | FR-06, FR-08, FR-09 |
| UC-06 | Reverse / Discovery / Add-feature / Retrofit の完了後に、Forward 復帰 event を記録して次工程へ自動昇格する | FR-04, FR-07, FR-11 |
| UC-07 | TL が G1/G3/G4 などの gate を評価する際に、static_subchecks 先行通過と AI review 必須部の境界を分離して確認する | FR-02, FR-05, FR-08 |

## §3 操作とデータの流れ

### 1. PLAN 起票と依存関係の確立

`helix plan draft --kind requirements --layer L1` 相当の起票で、PLAN frontmatter が生成され、`dependencies` / `generates` / `process_layer` が解釈される。これにより `plan_registry` 相当の管理対象へ登録され、後工程 PLAN (L3 3 PLAN (業務要件 / 機能要件 / 非機能要件)) への `blocks` 関係が確立される。

### 2. Gate 判定と証跡化

PLAN file と製本 doc を入力に `helix gate G1` などを実行し、detector・frontmatter・count 系の `static_subchecks` を先行評価する。必要に応じて AI review が加わり、結果は `gate_pass` / `decision_trace` 相当へ保存される。

### 3. Mode 判定と Forward 復帰

入口 signal は `helix route eval|suggest` や `helix mode` により mode 候補へ変換される。Discovery / Reverse / Incident / Recovery などの mode 実行中は補助 state を保持し、closure 時に `mode_transition` event を記録して Forward の次工程候補を決定する。

### 4. Trace / Inventory / Query

`helix code find` や影響範囲 query は、PLAN / 設計 / テスト設計 / 実装 / mode event の link をたどり、`v_model_alignment_score`、`expected_pair_freeze`、`expected_4artifact_trace`、`discrepancy_log` 相当の view から整合性と不足を返す。利用者はその結果を基に gate 継続、interrupt、recovery、reverse normalization を選択する。

## §4 入出力

| command | input | output | 副作用 |
|---|---|---|---|
| `helix plan draft` | title / file / plan-id / template / frontmatter | PLAN file | PLAN frontmatter が生成され、`dependencies` / `generates` の追跡対象になる |
| `helix plan review` | plan-id / reviewer | review 結果 | レビュー証跡が PLAN に紐づく |
| `helix plan finalize` | approve 済み plan-id | finalized PLAN | status 更新、後工程から参照可能になる |
| `helix plan generates` | plan-id または artifact path | 生成物一覧 / 逆引き結果 | PLAN と製本 doc の参照整合確認に使われる |
| `helix gate G1` | gate 名、PLAN file、製本 doc、pair-check 条件 | `pass / fail / blocked / watch-continue` などの verdict | `gate_pass` / readiness / decision trace の更新 |
| `helix mode` | mode 名または `--drive` 指定 | 現在 mode、切替結果、影響範囲 | drive 変更時は若い passed gate 以降の invalidation が起こりうる |
| `helix route eval|suggest` | signal または detect JSON | RouteResult または suggest_command | mode 入口候補の確定、Forward 復帰先の評価に使う |
| `helix discovery decide` | hypothesis、verify 結果、`--confirmed|--rejected|--pivot` | 仮説判定 | confirmed 時は Forward 昇格候補が確定する |
| `helix reverse <type> run|R0..R4|rgc` | reverse type、対象 path / artifact、review 指示 | stage 実行結果、status、routing 情報 | Reverse state と Forward routing 情報が更新される |
| `helix incident hotfix|route` | incident signal、triage 結果 | hotfix 実行結果、route 情報 | hotfix / permanent / postmortem の並走経路が決まる |
| `helix add-feature add-design|add-impl` | add-feature 対象、設計または実装の差分 | status / route | 既存系への追補経路が記録される |
| `helix retrofit init|plan` | matrix / config / target | retrofit plan / status | 段階移行用の matrix / plan が作られる |
| `helix recovery start|done` | recovery session 情報、cutover 判断 | session status、完了確認 | cutover と差戻し経路が記録される |
| `helix handover status|update` | handover snapshot、owner、note | status / 更新済 snapshot | CURRENT.json / CURRENT.md の責務と所有者が更新される |
| `helix interrupt start|resume` | reason、kind、scope または interrupt-id | interrupt 状態 | sprint / task の interrupted と再開状態が更新される |
| `helix code find` | query、bucket、件数 | 流用候補一覧 | 既存資産の再利用可否判断に使われる |

## §5 L0 §8 L1-IN-01/02/11 反映

| L1 バトン | 本 doc での反映 | carry |
|---|---|---|
| L1-IN-01 | FR-01 で 6 axes NSM 判定を定義 | 集計 SQL / schema / view 名の厳密契約は L1 技術要求 plan と L3 で固定 |
| L1-IN-02 | FR-02 で Guardrail 3 軸の独立計測と fail-close を定義 | 逸脱時の gate 連動ルールは L3 / gate-policy 側で詳細化 |
| L1-IN-11 | FR-03 で TDD 順序強制を定義 | detector / sprint state machine は L3 以降で詳細化 |

関連して、FR-04〜FR-12 では L1-IN-06 / 07 / 08 / 10 と L0 §5 / §6.5 の機能的な帰結を整理した。これらは主 scope の補助機能として扱い、詳細 schema・API・detector 実装は技術要求 plan と L3 に引き渡す。

**L1-IN-09 (PLAN template 手順書化、carry)**: 各工程 template (`cli/templates/plan/v2/L00-L14-*-template.md` 全 15 件) に `agent_slot` + `workflow_ref` field を組込み、step ごとに担当 agent と workflow ref を機械強制する要求。本 doc では FR 化せず、L1 技術要求 plan §8 carry + L4 基本設計 PLAN 起票時に template lint 機能として詳細化する (tl-advisor / pmo-sonnet Phase C audit 2026-05-26 指摘反映)。

### L14 / L3 ペア凍結の扱い

L1↔L14 の直接ペア凍結は [業務要求 doc](./helix-workflows-business-requirements.md) と運用テスト設計で担保する。本 doc は `pairs_with: L14` + `next_pair_freeze: L3` とし、機能要求の詳細化と受入テスト設計の pair freeze は L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) 起票時に `L12` 側 artifact と対で凍結する。

> **L3 接続規約 (2026-05-26 tl-advisor G1 P1 #2/#3 反映、4 L1 doc 共通)**: L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) は L1 4 PLAN 全件 (業務 / 機能 / 技術 / 非機能) を `dependencies.requires` に列挙し、`docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` を pair artifact として同時起票して FR-* AC-* と pair freeze する (詳細は業務要求 doc §7 参照)。

## §6 関連 doc

- **上流 L0**: [docs/v2/L0-helix-workflows/concept.md](../L0-helix-workflows/concept.md)
- **parent PLAN**: [docs/plans/L1/L1-helix-workflows-機能要求plan.md](../../plans/L1/L1-helix-workflows-機能要求plan.md)
- **sibling BR doc**: [helix-workflows-business-requirements.md](./helix-workflows-business-requirements.md)
- **HELIX-workflows L1 正本**: [HELIX-workflows/helix-process/L1-requirements.md](../../../HELIX-workflows/helix-process/L1-requirements.md)
- **工程 doc**: [docs/v2/process/L01-requirements-and-operational-test-design.md](../process/L01-requirements-and-operational-test-design.md)
- **並走 PLAN**: `L1-helix-workflows-技術要求plan` / `L1-helix-workflows-非機能要求plan`
- **下流 PLAN**: L3 3 PLAN (業務要件 / 機能要件 / 非機能要件)

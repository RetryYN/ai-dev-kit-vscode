---
plan_id: process-2026-06-01-plan-rule-closure
title: "Process Plan: PLAN 起票ルール整備（内部監査 → web検索 → Discovery → Reverse）"
plan_scope: process
workflow_chain: "内部監査 → web検索 → Discovery → Reverse"
kind: research
layer: L1
drive: discovery
status: draft
created: 2026-06-01
owner: PM
contains_action_plans:
  - docs/plans/discovery/poc-2026-06-01-recovery-closureplan.md
forward_return: "Reverse → Forward L4（closure 設計）+ PLAN モデル正本化"
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 行程設計・Forward 昇格判断"
  - role: tl-advisor
    slot_label: "TL — モデル/契約 adversarial check"
  - role: se
    slot_label: "SE — validator/hook/lint 実装（Codex）"
generates:
  - artifact_path: HELIX-workflows/helix-process/plan-model.md
    artifact_type: markdown_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - docs/v2/L0-helix-workflows/concept.md
  - HELIX-workflows/helix-process/discovery-workflow.md
  - HELIX-workflows/helix-process/reverse-workflow.md
---

# Process Plan: PLAN 起票ルール整備（内部監査 → web検索 → Discovery → Reverse）

> `plan_scope: process`（親 = 行程）。本 PLAN は「今回どう進めるか」の**ワークフロー連鎖**を文書化する。各ワークフロー内部の実行ループは **Action Plan（子）**として別に持つ。
> 本 PLAN は **Process⊃Action モデルの第一インスタンス（dogfood）**。モデルの正本定義は §4 で正本化する（完了後ここからリンク）。

## §1 Process と Action（モデルの要点）

- **Process Plan（本書 = 親）**: 駆動モデル・工程の**連鎖** = 行程。今回 = 内部監査 → web検索 → Discovery → Reverse。駆動モデルが連続するとき、その繋がりが Process になる。
- **Action Plan（子）**: 1 つのワークフロー**内部の実行ループ**。例: Discovery 内部 = 仮説 → 実装 → 検証 → 改善 → 検証 → 改善 →（収束）。駆動モデルの**収束地点を決める**のが Action。
- **規律 = 親子を守る（Process ⊃ Action）**。横に並べない。
  - **L単位**: それ自体が Process を兼ねる → L の中に内包する駆動モデルは **Action だけ**を書く。
  - **単独立ち上げ（今回）**: 親 Process がない → **Process 設計から入り**、その下に **個別 Action** を設計する。

## §2 今回の Process（行程）

| # | step | workflow | 状態 | 中身 / 成果 |
|---|---|---|---|---|
| 1 | 内部監査 | audit | **done** | PLAN 起票ルールの実態 verify。判明: validator が workflow PLAN を `unknown` 扱い / `helix plan lint` は status 整合のみ / design-doc hook `:130` の `docs/plans/PLAN-*` matcher 残存 / 命名が 3 分裂（V1 `PLAN-NNN` / V2 `L<NN>-…plan` / de-facto `<kind>-<date>-<topic>plan`）|
| 2 | web検索 | research | **todo** | 外部知見で設計を補強（plan/workflow の分類・closure / state-machine パターン）。raw WebSearch でなく **pmo-tech-docs / pmo-tech-news 経由**（[[reference_nfr_quality_standards_2026]] と同方針）|
| 3 | Discovery | discovery | **in_progress** | **H-CLOSURE-01**（closure 閉ループ検証）。内部 Action Plan = §3。詳細正本 = `docs/plans/discovery/poc-2026-06-01-recovery-closureplan.md` |
| 4 | Reverse | reverse | **todo** | confirmed を Forward へ翻訳・収束。closure event = 「枝が何を完了しどの L へ戻るか」の戻り transaction / Reverse = branch 結果を Forward 用語へ写す anti-corruption layer |

## §3 Discovery 内部の Action Plan（子）

対象: **H-CLOSURE-01**（詳細正本は既存 `docs/plans/discovery/poc-2026-06-01-recovery-closureplan.md` = この Action の本体）。

ループ: **仮説 → 実装 → 検証 → 改善 → 検証 → 改善 →（収束 = decide）**

- **仮説**: Recovery 完了の closure event（`source_workflow` / `target_forward_layer` / `closure_reason` / `idempotency_key`）を `mode_transition` へ冪等記録 + Forward 再開候補を機械復元できる
- **実装**: closure adapter + verify script（Codex se / DBA、**`mode_transition` schema = escalation でユーザー承認後**）
- **検証**: AC-1 冪等（二重記録されない）/ AC-2 target 保存 / AC-3 復元（route → recover → closure → Forward candidate）
- **改善 → 検証** 反復
- **収束（収束地点を決める = Action の核）**: decide（confirmed / rejected / pivot）。confirmed の収束地点 = `target_forward_layer`（L4）

## §4 この Process 完遂で正本化するもの（整備の本体）

Discovery confirmed → Reverse で Forward へ戻す過程で正本化する:

1. **概念正本化**: Process⊃Action モデルを正本 doc に定義（住所は §5 で確定）+ `concept.md §12 Glossary` に用語追記（Process plan / Action plan / 親子規律）
2. **起票規約**: Process plan / Action plan の書き方・命名・**親子リンク必須**（`docs/commands/plan.md` + workflow doc の「起票する PLAN kind」節）
3. **validator**（Codex 委譲）: workflow PLAN の `unknown` 解消 + `plan_scope`(process/action) 分類 + 親子リンク強制
4. **design-doc hook**（Codex 委譲）: matcher を現行命名に合わせて意図的 include/exclude へ更新
5. **`helix plan lint --strict-frontmatter`**（Codex 委譲）: required fields 欠落を fail-close

> 順序（TL 推奨）: **Discovery を先に confirmed → Reverse で L4/L5 へ翻訳して契約凍結 → L6/L7 で validator/hook 実装**。モデルを先に焼くと未検証 closure 契約を schema に固定するリスク。これは Refactor ではなく概念・契約の設計変更。

## §5 ヒアリングシート（確認事項 = 自己決定しない）

- ~~**正本住所**~~ **【解決 2026-06-01 TL】**: **G 正本 + P 用語ミラー**。定義本文 = G [`HELIX-workflows/helix-process/plan-model.md`](../../../HELIX-workflows/helix-process/plan-model.md)、用語 = P [`concept.md §12.1.3`](../../v2/L0-helix-workflows/concept.md)、`helix/` は参照のみ。定義本文を二重化しない。
- **transition table の名称 SSoT**: `mode_transition` / `workflow_transition` / `transition_history` が割れている（TL P1）。**closure 契約と分離**し L4 closure 設計で確定（escalation 承認後）。本 PLAN モデル整備には焼かない。
- ~~**本 PLAN frontmatter の暫定フィールド**~~ **【正本化 2026-06-01】**: `plan_scope` / `workflow_chain` / `contains_action_plans` / `forward_return` は [plan-model.md §5 contract](../../../HELIX-workflows/helix-process/plan-model.md) で正式化。validator 実装は Block 4（Codex）。
- **残（TL ガード）**: Process は `forward_return` 必須（Forward 代替にしない）/ `process⊃action[]` 1 段のみ / L単位に plan_scope 強制しない / `web検索` は workflow でなく step type。

## §6 dogfood note

本 PLAN 自身が Process⊃Action モデルの**第一インスタンス**。`plan_scope: process` は validator 未対応のため当面 `unknown` / WARN になりうる（§4-3 validator 整備で解消）。`helix plan lint`（status 整合）は PASS する。

## §7 自走スケジュール + 進捗ログ（2026-06-01 08:21 → ~22:00 連続稼働）

> ユーザー不在中の連続稼働。規律: schema migration(`mode_transition`)= escalation で承認待ち → 不在中は**設計止まり**。技術判断は TL に諮問。commit はローカルのみ・push しない。Codex は commit せず PM 検証後に commit。スコープ = PLAN ルール整備(Process⊃Action)。

| 時刻 | Block | 内容 | status |
|---|---|---|---|
| 08:21–09:00 | 0 Setup | schedule + TL(修正モデル) + web検索 dispatch | **done** |
| 09:00–10:00 | 1 モデル統合 | TL+研究 統合 → Process⊃Action 定義 起草 | **done** |
| 10:00–11:00 | 2 概念正本化 | 正本 doc + Glossary 追記 → commit | **done** |
| 11:00–12:00 | 3 起票規約 | Process/Action 命名・親子・structure → commit | **done** |
| 12:00–13:00 | 4 validator 委譲 | contract 確定 → Codex se(分類/unknown/親子/drift test) | **done** |
| 13:00–14:00 | 5 validator 検証 | Codex 検証 + 修正 → commit | **done** |
| 14:00–15:00 | 6 hook+lint | design-doc hook matcher + `--strict-frontmatter` (Codex) | **done** |
| 15:00–16:00 | 7 二重audit | tl-advisor + pmo-sonnet → 反映 | **done** (P1 修正済) |
| 16:00–17:00 | 8 closure設計 | mode_transition SSoT/closure adapter 設計doc ※実装は escalation 待ち | **done** (§4.5) |
| 17:00–18:00 | 9 親子retrofit | 既存 PLAN へ plan_scope 付与方針・PoC を Action 正式リンク | **done** (PoC 双方向リンク) |
| 18:00–19:00 | 10 全体整合 | helix doctor + テスト必要範囲 | **done** (doctor 0 fail / **フル pytest 2322 passed**・回帰ゼロ) |
| 19:00–20:00 | 11 仕上げ | commit 整理・残課題棚卸し | **done** (8 commit clean) |
| 20:00–21:00 | 12 Reverse戻し | 整備の軌跡を Forward へ + memory carry | **done** (§8 + memory) |
| 21:00–22:00 | 13 最終report | escalation 待ち明示 + handover 更新 → 終了 | **done** (早期完遂) |

### 進捗ログ
- **08:21 Block 0 done**: 現在地確認(setup完了/slot release/handover無し)、PLAN ルール実態 internal audit 完了(validator unknown / lint status のみ / hook:130 drift / 命名3分裂)、Process Plan 起票、TL(`b2mjkwpln`)+web検索(pmo-tech-docs)を background dispatch。
- **08:40 Block 1+2 done**: TL=条件付き推奨(closure 契約と分離なら先行整備可 / 住所=G正本+P用語ミラー / forward_return 必須 / process⊃action[] 1段 / L単位 plan_scope 非強制)。web検索=業界横断で二層分離を支持(Temporal/Airflow/Argo/ISO9001/OODA/Saga、収束=Pivot transaction)。G 正本 `HELIX-workflows/helix-process/plan-model.md` 作成(§1-8、業界 anti-corruption mapping 込み)、concept.md §12.1.3 用語ミラー追加、§5 住所問題 解決。commit `99d6bbd`(push せず)。
- **08:50 Block 3 done**: `docs/commands/plan.md` に「PLAN の種別と住所(Process/Action/L)」節 + plan-model.md 参照を追加、legacy PLAN-XXX template 参照に注記。commit `928b646`。
- **08:58 Block 4 dispatch (Codex se)**: 初回投入後 contract の穴に気づき停止→修正→再投入(`b8lc4yowr`)。修正点=命名 fallback 分類(plan_scope 未宣言でも `recovery-`/`poc-`/`refactor-` を action 分類 → 既存 workflow PLAN の unknown も解消)+ 親子 required 警告は plan_scope 明示時のみ(既存を強制 retrofit しない)。Block 6(hook 是正+strict-frontmatter)の Codex contract も prep 済。
- **09:20 Block 4+5 done**: Codex(`b8lc4yowr`)実装完了(exit 1 は私の未 commit §7 編集を allowed-files guard が誤検知しただけ、コード無傷)。独立検証=py_compile OK / pytest 40+350 passed 回帰なし / process PLAN・既存 recovery PLAN とも unknown 解消 / 命名 fallback + 親子は plan_scope 明示時のみ(gradual)/ VALID_PLAN_SCOPES 単一ソース(plan_lint が import)+ drift test。dogfood Process Plan に agent_slots/generates/dependencies 補完で警告ゼロ。教訓=Codex 投入前に tracking 編集を commit する。commit `4c3e210`。
- **09:40 Block 6 done**: Codex(`bzdr1l4gv`)完了 exit 0。独立検証=bash -n/py_compile OK / bats hook 2/2 / pytest 43 / hook が全 PLAN 形式除外・ADR のみ対象 / `--strict-frontmatter` 不完全 process PLAN で exit 1 fail-close・完全/非strict exit 0。2 commit に分割(`4f2d381` hook drift fix=recovery 根本原因解消 / `f3bce65` strict-lint)。**コア整備(Block 2-6)完了=recovery 指摘 3 件全解消**。repo 健全性=helix doctor 0 fail。
- **09:55 Block 8+9 done**: PoC を Process の Action 子に retrofit(plan_scope=action+parent_process+workflow=discovery、双方向リンク完成、検証=action分類/警告0/strict exit0)。closure SSoT 分析を PoC §4.5(mode_transition lean、reverse_local_loops 既存パターン発見、Saga Pivot 枠組み、実装は escalation 承認後)。
- **10:05 Block 7 audit done**: pmo-sonnet=整合 OK(要対応なし)。tl-advisor=**changes_required**: P1=①forward_return 常時 fail-close でない(warning+strict のみ) ②親子 reciprocal 未検査(子の plan_scope/parent_process 逆参照)。P2/P3=inferred-action warning+retrofit carry / path suffix 揺れ / hook 実質 ADR のみ / generates:[] 許容 / Glossary status 更新。P1 を Codex で修正してから完了宣言。doc commit `1625171`。
- **10:30 Block 7-fix done + 整備完了**: Codex(`bi62n3ur2`)で P1 解消。独立検証=pytest 49+359 passed / forward_return 欠落 process は非strict で exit 1(常時 fail-close)/ dogfood Process・PoC とも reciprocal clean / 既存 recovery PLAN に inferred_action warning。commit `5e6865b`。Glossary §12.1.3 status → installed、plan-model.md §9 に P2/P3 carry(file 命名 suffix / hook docs/v2 範囲 / inferred retrofit / closure escalation)。Block 10 全体整合=helix doctor 0 fail + pytest 359 回帰 passed で confirmed。**tl-advisor P1 全解消、Block 2-10 完了**。残=Block 12 Reverse 戻し記録 + memory / Block 13 最終報告。
- **10:50 Block 10-13 done + 自走完了**: フル pytest **2322 passed / 4 skipped / 1 failed**。失敗=`test_audit_log.py::test_pretooluse_opus_repo_block_records_hook_and_gate`（opus-repo-block が製造元除外/inert で 0、test は 2 期待）= **前 session(`ae63be3`/`01cfa11`)由来の pre-existing drift、私の変更ファイルと無関係・スコープ外**（carry）。私の整備は回帰ゼロ。memory carry 記録(`project_2026_06_01_plan_model_process_action`)。§8 に Process closure 状態。**doc commit 8件ローカル(`99d6bbd`→`65e623b`)、未 push。22時指示に対し ~10:50 で非ブロック作業を完遂、closure は escalation でブロックのため busywork で埋めず停止。**

## §8 Process 完了状態 / Forward 接続（closure 記録）

本 Process（内部監査 → web検索 → Discovery → Reverse）の closure 状態:

| step | 状態 | Forward 接続 |
|---|---|---|
| 内部監査 | ✅ 完了 | PLAN 起票ルール実態を audit（未整備と判明） |
| web検索 | ✅ 完了 | pmo-tech-docs で業界二層分離を確認、設計補強 |
| Discovery（H-CLOSURE-01） | 🔶 設計のみ | closure 閉ループ検証。実装は **schema escalation 承認待ち**でブロック |
| Reverse | 🔶 部分 | **PLAN モデル整備の枝は Forward 正本へ収束済**（`plan-model.md` = G process-model 正本 / `concept.md §12.1.3` 用語）。closure Discovery の枝は escalation 解除後に Reverse → Forward(L4) |

→ **本 Process は部分 closure**: PLAN モデル整備（`forward_return` 前半「PLAN モデル正本化」）は Forward へ収束済（Core 原則「枝は Forward へ戻す」を満たす）。closure Discovery（同後半「L4 closure 設計」）は **schema escalation 承認が entry 条件**のため open。ユーザー復帰時に escalation 判断 → closure adapter 実装 → verify → decide → L4 昇格で **完全 closure**。

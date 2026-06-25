# HELIX V3 — harness 設計（AI 実行規律の機械強制 + DB 化）

> **status: 再構築中** / base SSoT = [capture §7](../audit/2026-06-26-new-base-comprehensive-capture.md) / 実体 = clean harness `src/runtime/*` / `src/gate/*` / `src/team/*` / `.claude/hooks/*`。
> 方針: **harness の AI 実行規律を忠実に盗む**（Python 化）。HELIX 既存の hook 群（agent-guard.sh / askuser / opus-repo-block / raw-push）は capture 後の HELIX 独自強化として上乗せ（§6）。
> 接続: [L5 review_evidence_registry/guardrail_decisions](../L0-L14/L5-detailed-design.md) / [L6 FN-DET-09](../L0-L14/L6-functional-design.md) / [engine C6 gate/review tier](../engine/doc-workflow-rules.md)。

## 0. 方針

harness は AI agent の暴走・逸脱を**機械（hook + gate + pure 判定）で抑える**。判定ロジックは pure function、I/O は hook shim 側（review-guard 同型）。定性 review と TDD 証跡は DB（review_evidence_registry / test_result_events / guardrail_decisions）へ投影し、detector + baseline ratchet で advisory→fail-close 昇格する。

## 1. AI 実行規律 8 層（capture §7）

| # | 機構 | 規律 | source/方式 | bypass |
|---|---|---|---|---|
| 1 | **agent-guard**（PreToolUse Agent） | subagent_type allowlist(14) / model 必須 / frontmatter `model:` family 一致。未指定/許可外/不一致 = exit 2。stdin parse 失敗も fail-close | hook shim → pure `evaluate_agent_guard` | `*_ALLOW_RAW_AGENT=1`+evidence |
| 2 | **model family 一致** | 宣言 family(haiku/sonnet/opus) と呼出 model 不一致 = block | agent-guard 内 | 同上 |
| 3 | **tier-router** | T0(opus/gpt-5.5)=consult/verify のみ・`FrontierAuth.explicit` 必須 / worker(se/docs)=T1/T2 固定（上位帯到達不可） | pure `tier_router` | — |
| 4 | **work-guard**（PreToolUse Edit/Write） | 他 runtime の uncommitted file への盲目 Edit を exit 2。git uncommitted × session touched 突合 | hook shim、I/O 失敗 fail-open | `*_ALLOW_FOREIGN_EDIT=1`+marker(理由) |
| 5 | **review-guard** | read-only role(tl/qa/uiux/reviewer 等)の working-tree 変更を violation（IMP-137 再発防止） | **git 計算（source_kind=file_snapshot）** → `guardrail_decisions` | — |
| 6 | **attempt-escalation** | 同一 subject 3 連続失敗 → `EscalationSignal`（症状追いループを機械停止） | pure、直前 session log のみ参照 | — |
| 7 | **forced-stop** | ESC/Ctrl+C で session_end 無く閉じた session を次回検出 → pmo-haiku で mistake/feedback 分類、high=Recovery 提示 | hook（SessionStart）、fail-open | — |
| 8 | **agent-slots** | default 8 並列、超過 warn(fail-open)、stale 5 分失効。atomic write(tmp→rename) | hook（SubagentStop）| — |

- **2 MUST 原則**（concept §2.1.0）: ①ルール同一性（Claude/Codex 同一判定・同一 exit code）②hybrid 機能分散（frontier-reviewer ≠ worker runtime）。
- **session-log**（fail-open）: tool/path/verb のみ記録（値・引数・secret はマスク `sanitize`、120 字 truncate）。commit から PLAN ID 推論で active plan 配線。`compress_plan_digest` は high-watermark で過少計上防止。

## 2. review tier（capture §6 — judgment gate）

`JUDGMENT_GATES = G0.5/G2/G4/G5/G6/G7/R4`。review_kind:
- **cross_agent**（hybrid）: worker_model ≠ reviewer_model（同 model self-review を fail-close）。
- **intra_runtime_subagent**（single-runtime）: checklist 7（DOC/TST/COD/XR/DEP/DUP/MOD）。
- **human**（standalone）。
naive self-review 常時 block。`tests_green_at ≤ reviewed_at`（test-before-review）を機械強制。

## 3. C1 table 増分（契約は L5 §1.6 / capture §B3、review-guard は table 不要）

| table | 目的 | 区分 |
|---|---|---|
| `review_evidence_registry` | reviewer_model/worker_model/tests_green_at/reviewed_at/verdict/has_evidence | projection |
| `test_result_events`（V3 新設） | test 実行を時系列 append（red/green 証跡 + command + digest） | append_event |
| `hook_events` | hook 実行ログ（hook_name/event_type/digest） | append_event |
| `guardrail_decisions` | guard 判定 + bypass 記録（guardrail/decision/mode/human_signoff_required） | append_event |
| `impact_rules` / `impact_results` | change-impact の rule と走査結果 | config / append_event |

> **review-guard は専用 table を持たない**（capture: harness は working-tree mutation を git で計算し判定を `guardrail_decisions` へ記録）。`working_tree_snapshots` table は作らない。detector は `guardrail_decisions` を query + loader が git working-tree を snapshot 化（source_kind=file_snapshot）。**live `git diff` への依存は loader 内に隔離**し analyze は pure に保つ。

## 4. C2 projection 増分

| projector | 投影内容 |
|---|---|
| `project_review_evidence` | PLAN frontmatter の `review_evidence` ブロック（C6 schema = L5 §3）→ `review_evidence_registry` |
| `project_test_result_events` | pytest/bats 実行ログ → `test_result_events` へ `(ut_id, status, run_at, digest, command)` を append |
| `project_hook_events` / `project_guardrail` | hook 実行・guard 判定/bypass → `hook_events` / `guardrail_decisions` へ append |

## 5. C3 detector 増分（L6↔L7 で UT 対）

| FN-ID | detector | source_kind | 検出 | 優先 |
|---|---|---|---|---|
| FN-DET-09 強化 | review-evidence | db_projection | reviewer_model=worker_model / tests_green_at>reviewed_at / evidence tamper を **fail-close**（advisory→hard 昇格が核心） | **P1 必須** |
| FN-HRN-01 | review-guard | hybrid（git snapshot + guardrail_decisions） | read-only 宣言 role の working-tree 変更 = violation | **P1 必須** |
| FN-HRN-02 | red-first-evidence | db_projection（test_result_events） | UT-ID ごと red event が green より前に**無い** = TDD 違反（baseline で既知 debt 除外） | **P1 必須** |
| FN-HRN-03 | green-command-digest | db_projection | green 時の command+digest 固定、digest 変化 = assertion 弱体化の疑い | **P1** |
| FN-HRN-04 | change-impact | hybrid（impact_results + git diff loader） | 変更 artifact の推移的影響（PLAN/test/FR）の未追従 | P1-P2 |
| FN-HRN-05 | dependency-drift | file_snapshot（AST import） | layer 境界越え・循環依存・orphan module（ADR-002） | P1-P2 |
| FN-HRN-06 | guardrail-bypass-audit | db_projection | bypass 頻度・理由の異常を advisory surface | P2 |

必須（concept P2/P4）= FN-DET-09 強化 + FN-HRN-01 review-guard + FN-HRN-02 red-first。残りは Phase 8 で baseline ratchet 昇格。

## 6. HELIX 独自強化（capture 後に上乗せ）

harness の AI 規律を base に、HELIX 既存の fail-close hook を上乗せ:
| hook | 規律 | bypass |
|---|---|---|
| `pretooluse-agent-guard.sh` | Agent を PMO+PdM 12 種のみ許可 | `HELIX_ALLOW_RAW_AGENT=1` |
| `pretooluse-askuserquestion.sh` | 直近 5 分に tl-advisor 相談無ければ AskUserQuestion deny | `HELIX_ALLOW_ASKUSER=1`+理由 |
| `pretooluse-opus-repo-block.sh` | Opus の repo 直接編集 block（製造元は `cli/**` のみ） | `HELIX_ALLOW_OPUS_REPO_EDIT=1`+理由 |
| raw push guard | gate 非経由 `git push` を block | `HELIX_ALLOW_RAW_PUSH=1` |

これらは harness の agent-guard/tier-router/work-guard と整合させ二重化を避ける（同一判定を 1 本化）。

## 7. 検証 / 未確定

- 受入（L3↔L12）: AT-HRN-01 cross_agent で reviewer_model 未設定 → FN-DET-09 fail-close / AT-HRN-02 red 行なし直 green → FN-HRN-02 / AT-HRN-03 read-only role が Edit → FN-HRN-01。
- 単体（L6↔L7）: FN-DET-09 / FN-HRN-01..06 に UT 1:1（DB fixture + git snapshot fixture）。
- 未確定: event table 保持期間 / digest 算法（C5 ADR）。worker_model/reviewer_model 取得元（agent-guard subagent_type↔model family）。dependency-drift の AST 解析実体（lint-wiring 到達解析と共通基盤化候補）。

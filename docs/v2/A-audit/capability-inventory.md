# FR-INV01 Capability Inventory

最終更新: 2026-05-14

## 概要

本書は V1 (HELIX 現状) の capability 棚卸しです。`Phase 1` の監査成果物として、実装の有無だけでなく、どの PLAN 起源で入ったか、V2 のどの Phase に再配置・再実装されそうかを固定します。

注記:

- `V2 phase 紐付け候補` は `docs/v2/L1-REQUIREMENTS.md` の Phase 1〜5 定義を基準にした**推定**を含みます。
- `起源 PLAN` は実装ファイル内コメント、PLAN 本文、関連 docs から引いたもので、複数 PLAN にまたがるものは併記します。
- `状態=廃止候補` は「不要」ではなく、V2 で別 capability に吸収される可能性が高いものを指します。

## Inventory

| capability 名 | 起源 PLAN | 状態 | 実装ファイル | 役割 | V2 phase 紐付け候補 |
|---|---|---|---|---|---|
| V-model schema / QA baseline schema | PLAN-065 | 部分実装 | `cli/lib/helix_db.py:618`, `cli/lib/helix_db.py:639`, `cli/lib/helix_db.py:661`, `cli/lib/helix_db.py:1021`, `cli/lib/helix_db.py:1387` | `test_baseline` / `test_design_entries` / `design_review` と `contract_entries.design_level` を `helix.db v20` に追加する | Phase 2, Phase 3 |
| 14 detector system | PLAN-063 | 実装済 | `cli/helix-detect:1`, `cli/lib/detectors/registry.py:26`, `cli/lib/detectors/registry.py:39`, `cli/lib/detectors/base.py:66` | axis-01〜14 を router 経由で起動し、結果を `detector_runs` に記録する | Phase 4 |
| 契約 extractor / contract registry | PLAN-063, PLAN-065 | 部分実装 | `cli/lib/contract_registry.py:92`, `cli/lib/contract_registry.py:121`, `cli/lib/helix_db.py:1063` | `docs/features/**/D-API/*.yaml` を走査し `contract_entries` に登録する | Phase 3, Phase 5 |
| handover protocol | PLAN-016, ADR-016 | 実装済 | `cli/lib/handover.py:343`, `cli/lib/handover.py:392`, `cli/lib/handover.py:440`, `cli/helix-handover:18` | `CURRENT.json` / `CURRENT.md` / `ESCALATION.md` による担当移譲と停止判断を管理する | Phase 1, Phase 5 |
| skill 推挙 / skill chain | PLAN-024, PLAN-043 | 実装済 | `cli/helix-skill:101`, `cli/lib/skill_recommender.py:20`, `cli/lib/skill_recommender.py:116`, `cli/lib/skill_dispatcher.py:223` | `gpt-5.4-mini` recommender で skill を推挙し、そのまま role/agent 委譲へ接続する | Phase 1, Phase 5 |
| Reverse HELIX (R0-R4 + RGC, 5 type) | PLAN-049 | 実装済 | `cli/helix-reverse:9`, `cli/helix-reverse:44`, `cli/helix-reverse:94`, `docs/plans/PLAN-049-reverse-docs-enhancement.md:60` | code/design/upgrade/normalization/fullback の reverse 導線を提供する | Phase 2 |
| Scrum HELIX (S0-S4 + trigger) | PLAN-007 | 実装済 | `cli/helix-scrum:4`, `cli/helix-scrum:32`, `cli/lib/helix_db.py:1342`, `docs/plans/PLAN-007-scrum-multitype-trigger.md:23` | 仮説検証用の scrum mode と trigger persistence を提供する | Phase 2 |
| Agent Transformation 散在 (`helix codex` / `helix claude` / `helix-skill`) | PLAN-028, PLAN-043 | 部分実装 | `cli/helix-codex:4`, `cli/helix-claude:4`, `cli/lib/skill_dispatcher.py:23`, `cli/lib/agent_policy_guard.py:15` | role/harness/skill dispatch が別実装に散在したまま委譲を実現している | Phase 5 |
| PMO / advisor role system | PLAN-028 | 実装済 | `cli/ROLE_MAP.md:44`, `cli/roles/pmo-sonnet.conf:1`, `cli/roles/pmo-haiku.conf:1`, `cli/roles/pm-advisor.conf:1`, `cli/roles/tl-advisor.conf:1`, `cli/helix-claude:106` | PMO Sonnet/Haiku と advisor 系 role を分離し、execute 制約も付けている | Phase 1, Phase 5 |
| Stop hook session-summary shim | PLAN-014, PLAN-015, PLAN-016 | 廃止候補 | `cli/helix-session-summary:6`, `cli/lib/merge_settings.py:95`, `docs/plans/PLAN-016-session-summary-helix-log-report.md:12` | Stop hook 自体は残しつつ、session summary の主体を md から `cost_log` + `helix log report session` へ移した | Phase 5 |
| Codex / Claude harness + PreToolUse guard | PLAN-028, PLAN-043 | 実装済 | `cli/helix-codex:58`, `cli/helix-claude:24`, `cli/lib/merge_settings.py:27`, `cli/libexec/helix-post-tool-use:4`, `cli/lib/research_tool_guard.py:1` | `helix codex` / `helix claude` harness、PreToolUse/PostToolUse/Stop hook を束ねる | Phase 5 |
| code-index (`find/build/stats`) | PLAN-011, PLAN-012, PLAN-013 | 実装済 | `cli/lib/helix_db.py:1354`, `cli/lib/helix_db.py:1360`, `skills/SKILL_MAP.md:422`, `helix/HELIX_CORE.md:47` | code catalog、uncovered 計測、bucket taxonomy を使った再利用探索基盤 | Phase 1, Phase 3 |
| budget guard / auto-thinking support | PLAN-024, helix-budget-autothinking feature docs | 部分実装 | `cli/helix-budget:6`, `cli/lib/budget_cli.py:68`, `cli/lib/budget.py:48`, `cli/lib/budget.py:171` | Claude/Codex 消費率の可視化と model/thinking 推奨を行う | Phase 4, Phase 5 |
| Gate runner (`helix gate` G0.5〜G11) | PLAN-063, PLAN-067 | 部分実装 | `cli/helix-gate:153`, `cli/helix-gate:195`, `cli/helix-gate:2064`, `docs/plans/PLAN-067-helix-automation-layer.md:120` | G0.5〜G11 の gate 入口と pair-check はあるが、detector auto-run / auto-record の全面統合は未完 | Phase 4, Phase 5 |

## 補足評価

### 実装済が強い領域

- `14 detector`
- `Reverse HELIX`
- `Scrum HELIX`
- `PMO / advisor role system`
- `Codex / Claude harness`
- `code-index`

これらは CLI 入口と supporting module が両方存在し、テスト痕跡や ROLE / SKILL / command docs も揃っているため、V1 capability としては安定しています。

### 部分実装として扱った領域

- `V-model schema`: schema はあるが、`docs/v2/CONCEPT.md` の通り record がまだ空運用寄り
- `契約 extractor`: 手動/CLI 起点の抽出はあるが、V2 で求める auto-record までは未接続
- `Agent Transformation 散在`: 実現済みだが集約設計になっていない
- `budget guard`: `helix budget` はあるが、要件名の `cli/lib/cost_guard.py` は未実装で、中心機能は `budget.py` / `budget_cli.py` 側に分散
- `Gate runner`: gate CLI 自体は広いが detector 連動の本丸は `PLAN-067` 側で継続中

### 廃止候補

- `Stop hook session-summary`
  - 理由: `PLAN-016` で md 生成主体は外され、現状の `cli/helix-session-summary` は `cost_log` INSERT だけを担う静かな shim になっている。
  - したがって V2 では「session summary capability」単体ではなく、「Stop hook telemetry / session accounting」へ名称変更または吸収が妥当。

## 推奨

1. Phase 1 完了条件として、この inventory を `MASTER` / `Phase A audit` から参照し、各 capability の owner PLAN を固定する。
2. Phase 2 では `V-model schema`、`Reverse HELIX`、`Scrum HELIX` を同じ semantic layer に載せる設計を優先する。
3. Phase 5 では `契約 extractor`、`Gate runner`、`skill 推挙`、`session-start/stop hook` を「automation layer」としてまとめ直す。
4. `Stop hook session-summary` と `budget guard` は命名と実体がずれているため、V2 で capability 名の正規化を先に行う。

---
doc_id: L1-helix-workflows-technical-requirements
title: "HELIX-workflows V2 技術要求 (Technical Requirements)"
status: draft
created: 2026-05-26
owner: PM
process_layer: L1
pairs_with: L14
next_pair_freeze: L4
canonical_source: HELIX-workflows/helix-process/L1-requirements.md
parent_plan: L1-helix-workflows-技術要求plan
related_l0: docs/v2/L0-helix-workflows/concept.md
---

# HELIX-workflows V2 技術要求 (Technical Requirements)

> **本 doc の位置づけ**: HELIX-workflows V2 dogfooding に必要な runtime / DB / inventory / injection / mode recovery / compatibility の **技術要求** を整理する L1 正本。L1 段階では要望・制約・互換条件を確定し、L4 基本設計で具体 schema / state machine / migration / audit 実装へ落とし込む。
>
> **scope**: L1-IN-05/06/07/08/10 を中心に、技術選定・制約・外部連携・既存資産制約を明記する。破壊的 schema 変更、CLI 互換切替、mode event 永続化方式の細部は L4-L5 で確定する。

> **SSoT 参照** (2026-05-26 doc-system-architect retrofit): ユビキタス言語 = [L0 §12 Glossary](../L0-helix-workflows/concept.md) / 業界標準整合 = §13 / Bounded Context = §14。本 doc は L0 §12-§14 を parent_doc reference とし、用語独自定義は行わない (anti-corruption layer)。

## §1 採用技術・技術制約

| TR-ID | 領域 | 採用技術 / 制約 |
|---|---|---|
| TR-01 | runtime | Python 3.11+ (`cli/lib/`) + Bash 5.0+ (`cli/helix-*`) + SQLite 3.40+ (`.helix/helix.db`) を継続採用する |
| TR-02 | AI model | PM=Opus 4.7 / TL=Codex gpt-5.5 / SE=Codex gpt-5.4 / PE=Codex gpt-5.3-codex-spark / PMO=Sonnet 4.6 or Haiku 4.5 を採用し、正本は `cli/config/models.yaml` とする |
| TR-03 | OS / 環境 | Linux (WSL2 含む) / macOS を対象とし、Claude Code + Codex CLI の両方で同一 workflow を実行可能にする |
| TR-04 | test framework | pytest (Python) + Bats (Bash) + `verify/*.sh` (smoke test) を併用し、設計・CLI・DB の変更を機械検証可能に保つ |
| TR-05 | DB schema 管理 | sqlite3 + migration script (`cli/lib/helix_db.py`) を継続し、現状の `PRAGMA user_version` 主体運用から `schema_migration_log` 中心の追跡へ移行できる要求を持つ |
| TR-06 | trace / inventory | 4 artifact trace、工程 inventory、mode closure event を格納できる DB 構造を前提とし、各 row に `source_workflow` など起源追跡可能な metadata を持たせる |
| TR-07 | injection | `cli/config/vmodel-semantics.yaml` を L 別注入セットの正本とし、`mandatory_agents` / `recommended_skills` / `recommended_commands` / `orchestration_mode` を機械参照可能にする |
| TR-08 | compatibility | 既存 `cli/helix-*` router + subcommand は deprecated warning を伴っても 1 release 互換を維持し、PLAN / skill / schema の移行は段階 retrofit とする |

## §2 外部連携 + インターフェース要望

- **Anthropic API**: Claude Code CLI / Claude Agent SDK 経由で Opus / Sonnet / Haiku を利用できること。HELIX は provider SDK 直結ではなく `helix claude` harness を正規入口にする。
- **OpenAI Codex**: gpt-5.5 / 5.4 / 5.3 系は codex CLI 経由で利用し、`helix codex` が plan-only guard、approved guard、role context 注入を担う。
- **GitHub**: Actions / API / SSH を通じて review、CI、PR 導線を維持する。技術要求としては provider 切替よりも audit trail と workflow 再現性を優先する。
- **VS Code 拡張**: Claude Code native extension と Codex CLI の併用を前提にし、AGENTS / CLAUDE / hook / memory の context guard を破らないこと。
- **Interface contract**: 外部連携は raw CLI 直叩きではなく HELIX harness (`helix codex` / `helix claude` / `helix review` / `helix handover`) を優先し、role・plan・handover 文脈を失わないこと。

## §3 既存システム制約

- 現状の `cli/lib/helix_db.py` は schema version 36 を持つ 30+ table 構成であり、L1-IN-10 ではこれを **V モデル DB 10 core + audit/event + derived views 7** に再構成する要求を定義する。移行は migration で吸収し、既存利用者へ即時破壊的変更を強制しない。
- 既存 PLAN 324 件には V1 reference と V2 製本対象が混在する。retrofit は L1-IN-04 連携で段階的に行い、技術要求側では inventory registration と traceability の土台だけを要求する。
- skill 118 件は flat 配置のままでは L0-L14 工程注入に不向きである。L1-IN-06 では工程別 inventory schema、L1-IN-07 では L 別注入契約への再 mapping を要求する。
- 既存 `cli/helix-*` 60 個の router + subcommand は互換維持が前提であり、新構造へ寄せる場合も warning + 1 release 維持を最小条件とする。
- `cli/config/vmodel-semantics.yaml` は既に injection を持つが、L1 時点では BE spine と role injection が中心で、9 mode 共通 closure や doctor audit との一貫 enforcement は未完である。

## §4 helix.db schema 二層構造 (L1-IN-10)

L1-IN-10 の要求は、`helix.db` を **V モデル DB (正本)** と **補助 DB (中間 state)** の二層構造として整理し、Forward 正本と mode 別の一時状態を分離することにある。

| 区分 | 要求対象 | 要求内容 |
|---|---|---|
| core tables (10) | `plan_registry`, `design_artifact`, `test_design_pair`, `test_implementation`, `code_implementation`, `coverage_link`, `gate_pass`, `transition_history`, `decision_trace`, `schema_migration_log` | L0-L14 の正本 trace を保持し、主キーと参照関係は V モデルの pair freeze を表現できること |
| audit/event tables (1+) | `volume_metrics` を最小構成とする | 設計数 / test 数 / gate 実行数 / mode closure 数を計測できること |
| derived views (7) | `pair_volume_balance`, `expected_pair_freeze`, `expected_4artifact_trace`, `expected_mode_transition`, `expected_volume_balance`, `v_model_alignment_score`, `discrepancy_log` | fail-close や alert の入力になる可観測 view を提供すること |
| 補助 DB (9 mode 別) | `reverse_*`, `discovery_*`, `scrum_*`, `incident_*`, `refactor_session`, `retrofit_*`, `research_*`, `recovery_*`, `addfeature_*` | mode ごとの中間 state を保持し、Forward 正本と分離すること |

closure event 契約:
- `idempotency_key = mode + plan_id + closure_event_id` を持ち、重複 closure を吸収できること。
- rollback と conflict resolution を要求として持ち、V モデル DB 既存 row との競合時に安全側へ倒すこと。
- `source_workflow` を持ち、Forward / Reverse / Discovery / Incident など起点を追跡できること。

## §5 工程別 skill 注入機構 (L1-IN-07)

L1-IN-07 の要求は、工程ごとの選択空間を人手ではなく機械で絞り込むことにある。

- `cli/config/vmodel-semantics.yaml` を L 別注入セットの正本とし、少なくとも `owner_role` / `mandatory_agents` / `recommended_agents` / `recommended_skills` / `recommended_commands` / `orchestration_mode` を保持する。
- `helix-context` は L への entry 時に、対応する skill 群、agent slot、推奨 command を bundle 化し、AI が工程外の手を打ちにくい導線を生成する。
- `helix doctor` は skill 不在、command drift、mode 定義漏れ、frontmatter 欠損を audit できること。
- `helix review` や gate 系コマンドは、この注入契約に依存して「その工程で何を呼ぶべきか」を検証できること。
- L1 では要望レベルに止め、L4 で enforcement point、L5 で doctor / context / hook への実装責務を確定する。

## §6 9 mode 共通基盤 (L1-IN-08)

L1-IN-08 の要求は、Reverse だけでなく Discovery / Scrum / Incident / Add-feature / Refactor / Retrofit / Research / Recovery を含む 9 mode すべてが、同じ closure pipeline で Forward に戻れることにある。

- R0-R4 + RGC を「Reverse 専用」ではなく **共通 closure language** として再利用できること。
- 各 mode 完了時には Forward 接続 event を `helix.db` に登録し、L1 / L3 / L4-L6 / L7 のどこへ昇格したか追跡できること。
- mode 固有の中間 state は補助 DB へ保存し、closure 後に V モデル DB へ merge する。
- gate block / interrupt / incident / recovery への切替条件は `discrepancy_log` や doctor audit から機械起動できること。
- L1 では「共通化する」という要求のみを確定し、L4 で mode transition state machine と event schema を定義する。

## §7 drift 解消方針 (L1-IN-05/06)

L1-IN-05 は **HELIX-workflows ↔ cli/helix-* ↔ skill ↔ helix.db** の drift を常時検出し解消する運用要求である。L1-IN-06 は、そのための inventory schema を定義する要求である。

- detector は週次以上で起動し、axis-* / `helix doctor` / `helix drift-check` を束ねて drift を検出できること。
- inventory schema は skill 118 / `cli/helix-*` 60 / helix.db table 30+ / PLAN 324 / docs を L0-L14 工程へ双方向 mapping できること。
- 新規 asset 登録時に工程未割当を許容しない、または warning として残すこと。
- drift 検出後は Reverse normalization mode など既存 workflow に接続し、手動判断待ちで放置しないこと。
- 運用目標は **新規 drift 0 件 / week** を維持することで、BR-03 / OT-03 と整合する。

## §8 関連 doc

- **上流 (L0)**: [docs/v2/L0-helix-workflows/concept.md](../L0-helix-workflows-concept.md)
- **PLAN**: [docs/plans/L1/L1-helix-workflows-技術要求plan.md](../../plans/L1/L1-helix-workflows-技術要求plan.md)
- **並走 L1 doc**: [helix-workflows-business-requirements.md](helix-workflows-business-requirements.md)
- **HELIX-workflows L1 正本**: [HELIX-workflows/helix-process/L1-requirements.md](../../../HELIX-workflows/helix-process/L1-requirements.md)
- **実装版工程 doc**: [docs/v2/process/L01-requirements-and-operational-test-design.md](../process/L01-requirements-and-operational-test-design.md)
- **schema / injection 正本**:
  - [cli/lib/helix_db.py](../../../cli/lib/helix_db.py)
  - [cli/config/vmodel-semantics.yaml](../../../cli/config/vmodel-semantics.yaml)
  - [cli/config/models.yaml](../../../cli/config/models.yaml)
- **carry**: 技術要求 doc は L1↔L14 ではなく **L4 基本設計 ↔ L9 総合テスト設計** でペア凍結する。L4 基本設計起票時に L9 総合テスト設計を pair artifact 化する (`next_pair_freeze: L4` を frontmatter に明記)。
- **L3 接続規約 (2026-05-26 tl-advisor G1 P1 #2/#3 反映、4 L1 doc 共通)**: L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) は L1 4 PLAN 全件 (業務 / 機能 / 技術 / 非機能) を `dependencies.requires` に列挙し、`docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` を pair artifact として同時起票して L3 技術要件 (採用技術詳細 / 制約) と L12 受入テスト設計の技術系 AC-* を pair freeze する (詳細は業務要求 doc §7 参照、L4↔L9 は更に下流の多層検証)。

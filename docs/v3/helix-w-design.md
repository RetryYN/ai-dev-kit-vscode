# HELIX V3 — HELIX W 設計（2 段 V 合流・agent system 向け）

> **status: 再構築中**（[capture §5 concept v3.1 §2.3.3](audit/2026-06-26-new-base-comprehensive-capture.md) 整合: harness 自身は単一 V、製品が agent system のとき W を提供）
> 出自: HELIX W（2 段 V モデル）。**V3 が作る対象 = AI エージェントハーネス自身**なので、W モデルは consumer の agent system 製造への提供物として不可欠。harness concept §2.3.3 = 「harness 自身は外殻既存のため単一 V」。
> canonical（G-tier、重複させず参照）: `HELIX_CORE.md §1`（W モデル定義）/ `HELIX-workflows/helix-process/two-stage-agent-design.md`
> 接続: [L0 概念](L0-L14/L0-concept.md) / [L4 §1 C1-C6](L0-L14/L4-basic-design.md) / [harness 設計](harness/harness-design.md)

## 0. なぜ V3 に HELIX W が要るか

V3 が作る製品は **AI エージェントを規律するハーネス**（fork = UT-TDD **Agent** Harness）。HELIX Core §1 は「作る対象が AI エージェントシステムの場合、V モデルを 2 回通す（W モデル）」と定める。**V3 自身がこの条件に該当**するため、W モデルを V3 corpus に持ち、両 Phase が同一 V モデル DB へ収束することを設計で保証する。

## 1. W モデル（V を 2 回適用した合成）

- **Phase 1（一般システム）**: L1-L9 を通常 V モデルで。CLI / DB engine / 配布 = 普通のソフトとして設計・検証。
- **Phase 2（エージェント昇華）**: L1-L9 をもう一度 V モデルで。agent/role harness・worker≠reviewer・hook 規律・review evidence = エージェント固有の品質を設計・検証。
- **合流**: L10 で 2 Phase を合流し、**L10-L14 を一度だけ**通す（UX 磨き → レビュー → 受入 → 運用検証 → 運用学習）。
- W は別の起点ではない。**V モデルを 2 回適用した合成**であり、両 Phase とも**同一の V モデル DB（C1）へ収束**する（絶対原則は各 Phase と合流点の両方で成立）。

```
Phase1 一般:   L1──…──L9 ┐
                          ├─ L10 合流 ─ L11 ─ L12 ─ L13 ─ L14
Phase2 agent:  L1──…──L9 ┘
（両 Phase → 同一 C1 V モデル DB へ projection）
```

## 2. V3 closed-loop への写像（C1-C6）

HELIX W は新しい table 種別を要求しない。**既存 C1 table に `phase` 次元を持たせる**ことで両 Phase を 1 DB で扱う:

| 機構 | W での扱い | C1/C2/C3 |
|---|---|---|
| Phase 区別 | plan_registry / artifact_registry / trace_edges に `phase ∈ {general, agent}` 列 | C1 列追加（物理 column は L7） |
| Phase 2 の agent 品質 | harness 設計（review_evidence_registry / test_result_events（履歴）/ hook_events）= **Phase 2 の成果物**として投影 | C2 project_*（[harness 設計](harness/harness-design.md)） |
| L10 合流 | 両 Phase の L9 exit 後、L10 で合流（合流点で pair_closure を両 Phase 分要求） | C3 detector: phase ごとの片肺 + 合流もれ検出 |
| 収束保証 | 両 Phase が同一 V モデル DB へ収束（off-V モデル成果は載らない＝絶対原則 3） | C3 FN-DET（trace-symmetry を phase-aware に） |

- **detector の phase 対応**: FN-DET-03 trace-symmetry / FN-DET-04 descent-obligation を **phase 次元込み**で評価（general phase の片肺と agent phase の片肺を別々に検出し、合流点で両方 clean を要求）。
- **harness 設計（Phase 2 の agent 品質）は HELIX W の Phase 2 成果物**。worker≠reviewer・red-first・review-evidence は「エージェント昇華」の検証 = W の右腕。

## 3. V3 での適用範囲

- V3 corpus 自体（このハーネスを作る作業）は HELIX W で運営しうるが、**Phase 1-8 の段取りは Forward V モデルを正本**とする（charter §6）。W は「製品が agent system のとき V を 2 回」の構造定義であり、V3 の段取りを W で置き換えるものではない。
- **consumer プロジェクトが agent system を作る場合**、V3 harness が W モデル（phase 次元 + 合流 gate）を提供する。これが V3 の HELIX W 優位（fork は単一 V のみ、2 段合流の機械化を持たない）。

## 3.5 内部 query contract pattern（Phase 2 agent 昇華・ユーザー提案 2026-06-26 + TL refine）

agent system（W Phase 2）で、**unit 境界をまたぐ問い合わせ**（agent↔agent / agent↔tool）を **型付き request/response contract** として設計する。エージェント内部通信を、他の全てと同じ「契約 + DB + detector」規律に載せる（HELIX カラーの均質性）。

- **MCP "風" の contract 形状**（discoverable / typed / versioned）だが **重量 RPC ではない**: in-process は型付き dispatch、跨プロセス/跨エージェントのみ実 MCP server。
- **既存 MCP table（`mcp_server_*`）は流用しない（TL P1）**: あれは外部 MCP server の config/projection。内部 query audit を混ぜると C1 table 分類 + C2 rebuild/append 分離を壊す。**C1-C6 core schema は不変**（freeze 維持）。
- **投影は既存経路のみ**: query contract 定義 → `artifact_registry`（contract artifact）+ `trace_edges`（unit 境界接続）、定性証跡 → `review_evidence_registry`。**実行ログは payload 非保存 = digest/evidence 化**（secret/PII/raw transcript 非保存 = C-5）。必要時のみ既存 `tool_runs`/`model_runs`/`guardrail_decisions` の意味に合う範囲へ限定。
- **scope guardrail（TL P2）**: 全関数を契約化しない。**有意な unit 境界（[C6 §4.5 unitized L5-L7 descent](engine/doc-workflow-rules.md) の unit 境界）をまたぐ query のみ**。unit 内部関数は L6 DbC で足りる（契約化は過剰分割）。→ **proposal 1 の unit 分解粒度 = query 契約境界が一致**（相互補強）。
- **AI 規律が境界に効く**: worker≠reviewer / tier-router / work-guard が query 境界で発火（[harness §1](harness/harness-design.md)）。handler registry が contract↔実装を解決。
- **detector（C3、source_kind=hybrid: contract=db_projection / handler=file_snapshot loader）**: `unresolved-query`（contract から handler 解決不能）/ `contract-drift`（request/response schema hash ≠ handler signature）/ `query-without-handler`（handler registry に対応 contract なし）。
- **実装フェーズ**: engine/cutover 後の **HELIX 独自強化**（agent system 向け提供物）。検証 = contract-without-handler / handler-signature-drift / valid-handler-clean / 外部 MCP profile と内部 query の非干渉 / payload·secret 非保存 / unit 境界 query が `trace_edges` 接続 & unit pair_closure と query detector 同時 green。

## 4. 検証（V-model pair）

- L4↔L9（総合）: 両 Phase の L9 が独立に閉じ、L10 合流で両 Phase 分の pair_closure が揃うこと（合流もれ = detector violation）。
- 受入（L3↔L12）: AT-W-01 agent phase の成果物（review_evidence）が general phase と同一 DB に phase=agent で投影される / AT-W-02 一方 Phase の片肺が合流 gate を block する。
- 単体: phase-aware trace-symmetry の UT（general 片肺 / agent 片肺 / 合流もれ の 3 境界）。

## 5. 確定（P1-5）と未確定

**確定**（TL re-review P1-5 / L5 §1.6 と一致）:
- `phase ∈ {general, agent}` は `plan_registry` / `artifact_registry` / `trace_edges` の**属性列**で持つ（`phase_join` table は立てない＝1 DB・列方式）。default=`general`、single-V（agent system でない）は全行 general の degenerate。logical_key には含めない（plan は 1 phase 所属）。
- L10 合流 gate の判定式 = C3 が「`phase=agent` 行が存在するとき**両 phase の pair_closure AND**」を要求（一方 phase 単独 clean では合流させない）。

**未確定**（L6 で detector 仕様化）:
- phase-aware trace-symmetry / descent-obligation の UT 境界（general 片肺 / agent 片肺 / 合流もれ）。
- agent phase の「昇華」成果物の最小集合（review_evidence は必須、他に何を agent phase 必須とするか）。

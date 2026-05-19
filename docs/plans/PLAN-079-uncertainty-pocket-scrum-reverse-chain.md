---
plan_id: PLAN-079
title: "PLAN-079: Uncertainty Pocket Scrum + Scrum-to-Reverse-to-Forward chain (framework 拡張)"
status: completed
size: L
drive: be
created: 2026-05-17
owner: PM
phases: framework
gates: G1, G2, G3, G4
related_plans:
  - PLAN-075 (V-model 4 artifact、本 PLAN にも適用)
  - PLAN-078 (agent slot、record strand 並走)
  - 既存 Reverse HELIX (R0-R4 + RGC、type matrix)
  - 既存 HELIX Scrum (S0-S4)
trigger: |
  2026-05-17 PLAN-075 Phase 4 完遂時のユーザー指摘 2 連続:

  指摘 1: 「Forward HELIX だからスクラムを含まないって考え方がよくないな。
  スクラムは工程の内部の実装してみないと分からないところに差し込んで使うのも考えてある？」

  指摘 2: 「スクラムからリバースに続けて設計し直して実装するみたいなのはできるかい？
  これはリバースを差し込んでドキュメント化する工程も挟んだほうがいい。
  つまり、基本工程とスクラム＆リバースでカバーするって感じだな。」

  → 現状 HELIX framework は Forward / Reverse / Scrum を **独立 3 モード** として扱い、
    Forward 進行中に Scrum / Reverse を差し込む運用が明示されていない。
  → 3 軸を interlocked な chain として運用できる framework 拡張が必要。

  本セッション (PLAN-075 Phase 4) で実体は scrum-like / reverse-like な pivot を行っていた:
  - T401 pmo-sonnet が tool_uses 上限で 2 度 turn 返却 → 仮説 rejected → pivot
  - PLAN-070/071 retrofit task-plan 前提 → audit 後に「設計系 PLAN は構造的に 4 artifact 揃わない」と判明 → grandfather に pivot
acceptance:
  - HELIX framework に "Uncertainty Pocket Scrum (UPS)" パターンが明文化される
  - HELIX framework に "Scrum-to-Reverse-to-Forward (SRF) chain" パターンが明文化される
  - Reverse type matrix に新 type `scrum-to-forward` が追加される
  - helix.db に `scrum_local_loops` table + `reverse_local_loops` table (v29、PLAN-078 v28 の次)
  - CLI: `helix scrum local <subcommand>` + `helix reverse from-scrum`
  - HELIX_CORE.md + SKILL_MAP.md + CLAUDE.md (project) に framework 拡張を明文化
  - PLAN-079 自身が V-model 4 artifact 双方向 trace 完備 (PLAN-075 原則)
---

# PLAN-079: Uncertainty Pocket Scrum + Scrum-to-Reverse-to-Forward chain

## §1 背景

### 1.1 現状 framework の 3 モード独立構造

HELIX framework は現状 3 モードを **独立** に扱う:

```
[Forward HELIX]    [Reverse HELIX]    [HELIX Scrum]
  L1 → L11           R0 → R4 + RGC      S0 → S4
  標準工程            既存コード復元      検証駆動 (要件未確定)
```

`SKILL_MAP.md §4 フェーズ思想` でも 3 モードは別 phase として扱われ、内部で組み合わせる運用は明示されていない。

### 1.2 現実の運用パターン (本セッションで観察)

Forward 進行中、以下の局所的不確実性が頻繁に発生する:

| 観察事象 | 種別 | 現状対応 |
|---|---|---|
| 「pmo-sonnet で 8 PLAN audit 可能か」が tool_uses 上限で破綻 | scrum-like (仮説検証) | 個人判断で pivot、framework trace なし |
| 「Codex 4 並列が helix codex validation で reject」 | scrum-like (仮説検証) | 個人判断で workaround、trace なし |
| 「動いた PoC があるが設計書がない」 | reverse-like (artifact 化要請) | 個人判断 or 別 PLAN 起票、framework chain なし |

これらは Forward 内部に **Scrum / Reverse を差し込んで pivot 履歴を残す** べき場面だが、現状 framework ではサポートされていない。

### 1.3 framework 拡張の方向性

ユーザー指摘から導出される 2 つのパターン:

#### Pattern A: Uncertainty Pocket Scrum (UPS)
Forward 進行中、局所的不確実性 (pocket) に **scrum sub-loop を差し込む**。動いたら Forward 続行、破れたら設計戻し or pivot。

#### Pattern B: Scrum-to-Reverse-to-Forward (SRF) chain
UPS で動いた PoC を **そのまま Forward に持ち込まず、Reverse でドキュメント化** してから本実装する。

```
Forward L4 進行中
  └─ uncertainty pocket
       ↓ UPS (Pattern A)
       S-LOCAL-0〜3 → confirmed = 動いた PoC
       ↓ SRF chain (Pattern B)
       └─ R-LOCAL-0〜4 (mini reverse、scrum 成果物起点)
            └─ ドキュメント化された設計
                 ↓
                 Forward L2/L3 再設計 → L4 本実装
```

### 1.4 関連既知パターン

- 既存 Reverse type matrix の `fullback` (実装完遂後の文書整合) と類似だが、起点が「Scrum 成果物 (動く PoC)」というのが新規
- 既存 `helix scrum decide --confirmed` は Forward L1 接続を想定、本 PLAN は L4 等の途中接続を可能化

## §2 V-model 4 artifact (PLAN-075 準拠)

本 PLAN は PLAN-075 で確立した V-model 4 artifact 双方向 trace 原則を **自身に適用**:

| Artifact | 担当層 | 想定パス |
|---|---|---|
| ① 設計 (詳細) | L3 詳細設計 | docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md §X scrum_local_loops + reverse_local_loops |
| ② 実装コード | L4 実装 | cli/lib/scrum_local.py + cli/lib/reverse_local.py + cli/helix-scrum + cli/helix-reverse (既存に subcommand 追加) |
| ③ テスト設計 (結合 + 単体) | L4 設計 | docs/v2/L4-test-design/PLAN-079-{unit,integration}-test-design.md |
| ④ テストコード | L4 実装 | cli/lib/tests/test_scrum_local*.py + test_reverse_local*.py |

## §3 設計

### 3.1 Pattern A: Uncertainty Pocket Scrum (UPS)

#### 起動条件
Forward HELIX の任意層 (主に L4 実装中) で、以下のいずれかが発生:
- 「実装してみないと動作が分からない」局所 (技術不確実性)
- 既存 framework / tool / API の仕様が想定と違う可能性 (環境不確実性)
- 並列実行や resource 使用が想定通り動くか不明 (運用不確実性)

#### S-LOCAL state machine

```
S-LOCAL-0: 仮説立て
  - 仮説 ID (H-LOCAL-XXX) 採番
  - 検証質問 + 成功条件 を 1-3 行で明示
  - 関連 Forward 層 (L1-L11) を記録
  ↓
S-LOCAL-1: PoC 実投入
  - 仮説検証用の小規模実装 (size: S 厳守)
  - helix.db に scrum_local_loops INSERT (status=running)
  ↓
S-LOCAL-2: Verify
  - 期待動作したか確認
  - 副作用、コスト、回帰を観察
  ↓
S-LOCAL-3: Decide
  - confirmed: Forward 続行 (PoC を本実装に昇格 or 別 PLAN へ artifact 化)
  - rejected: 仮説破棄、Forward 設計戻し (L2/L3 へ)
  - pivot: 別仮説に切替 → S-LOCAL-0 再帰
```

#### CLI 設計

```
helix scrum local init --layer L4 --hypothesis "..." --acceptance "..."
  → S-LOCAL-0 (scrum_local_loops INSERT、loop_id 採番)

helix scrum local poc --loop-id H-LOCAL-001 [--commit-sha ...]
  → S-LOCAL-1 (PoC 投入記録)

helix scrum local verify --loop-id H-LOCAL-001 --result confirmed|rejected|pivot
  → S-LOCAL-2/3 (decide 記録)

helix scrum local list [--layer L4] [--active] [--json]
  → 現在 active な UPS loop 一覧

helix scrum local stats [--days 7]
  → confirmed / rejected / pivot の集計
```

### 3.2 Pattern B: Scrum-to-Reverse-to-Forward (SRF) chain

#### 起動条件
UPS で `confirmed` 判定後、以下のいずれかに該当:
- PoC コードが本実装にそのまま使えない (設計が不在 / 文書化が必要)
- 動作は OK だが副作用 / 契約が不明確で本実装前に reverse engineering 必要
- 複数 UPS confirmed の統合設計が必要

#### Reverse type matrix への追加

既存 type matrix:
| Type | 起点 | 用途 |
|---|---|---|
| code | レガシーコード | 既存 system 復元 |
| design | デザイン資産 | デザイン起点設計化 |
| upgrade | version diff | 既存 system 更新 |
| normalization | 設計 drift | 正規化 |
| fullback | 実装完遂後 | 文書整合 |

**新規追加** (本 PLAN):
| Type | 起点 | 用途 |
|---|---|---|
| **scrum-to-forward** | **Scrum 成果物 (動く PoC)** | **PoC artifact 化 → Forward 本実装に橋渡し** |

#### R-LOCAL state machine

```
R-LOCAL-0: Evidence acquisition (scrum 成果物起点)
  - confirmed UPS loop の PoC コード、操作ログ、verify 結果を evidence 化
  - helix.db に reverse_local_loops INSERT (parent_scrum_loop_id FK)
  ↓
R-LOCAL-1: Observed contracts
  - PoC コードの実 API / DB / 型を抽出
  - characterization tests を最小限実装 (PoC コードの現挙動固定)
  ↓
R-LOCAL-2: As-Is design
  - PoC コードからアーキテクチャ復元
  - ADR 推定 (なぜこの方式を選んだか、PoC 中の判断理由)
  ↓
R-LOCAL-3: Intent hypothesis
  - 要件仮説の PO 検証
  - 本実装で残す機能 / 落とす機能を確定
  ↓
R-LOCAL-4: Gap & routing (Forward 再合流)
  - As-Is と本実装 To-Be の gap を集約
  - Forward L1/L2/L3/L4 のどこに合流するか routing 決定
  - 復元 ADR / 設計 doc を本実装側 PLAN に転記
```

#### CLI 設計

```
helix reverse from-scrum --scrum-loop-id H-LOCAL-001
  → R-LOCAL-0 起動 (scrum 成果物を evidence 化、reverse_local_loops INSERT)

helix reverse local stage --loop-id RL-001 --stage R0|R1|R2|R3|R4
  → 既存 helix reverse と同じ stage 遷移 CLI

helix reverse local route --loop-id RL-001 --target-plan PLAN-XXX --target-layer L4
  → R-LOCAL-4 routing (Forward 合流先決定)
```

### 3.3 helix.db schema (v29、PLAN-078 v28 の次)

```sql
CREATE TABLE scrum_local_loops (
    loop_id              TEXT PRIMARY KEY,           -- H-LOCAL-XXX
    forward_layer        TEXT NOT NULL,              -- L1-L11
    forward_plan_id      TEXT,                       -- 親 Forward PLAN
    hypothesis           TEXT NOT NULL,
    acceptance           TEXT NOT NULL,
    state                TEXT NOT NULL DEFAULT 'S0', -- S0 / S1 / S2 / S3
    decide_result        TEXT,                       -- confirmed / rejected / pivot
    started_at           TEXT NOT NULL,
    decided_at           TEXT,
    parent_loop_id       TEXT,                       -- pivot 時の親 (FK 自己参照)
    related_agent_slot_id INTEGER,                   -- FK agent_slots.id (PLAN-078)
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (parent_loop_id) REFERENCES scrum_local_loops(loop_id)
);

CREATE TABLE reverse_local_loops (
    loop_id              TEXT PRIMARY KEY,           -- RL-XXX
    parent_scrum_loop_id TEXT NOT NULL,              -- FK scrum_local_loops.loop_id (起点)
    reverse_type         TEXT NOT NULL DEFAULT 'scrum-to-forward',
    state                TEXT NOT NULL DEFAULT 'R0', -- R0 / R1 / R2 / R3 / R4
    target_forward_plan  TEXT,                       -- R-LOCAL-4 routing 先
    target_forward_layer TEXT,                       -- L1 / L2 / L3 / L4
    started_at           TEXT NOT NULL,
    routed_at            TEXT,                       -- R-LOCAL-4 完了時刻
    artifact_links       TEXT,                       -- JSON [{type: "code/design/test", path: "..."}]
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (parent_scrum_loop_id) REFERENCES scrum_local_loops(loop_id)
);

CREATE INDEX idx_scrum_local_state ON scrum_local_loops(state);
CREATE INDEX idx_scrum_local_layer ON scrum_local_loops(forward_layer);
CREATE INDEX idx_reverse_local_state ON reverse_local_loops(state);
CREATE INDEX idx_reverse_local_parent ON reverse_local_loops(parent_scrum_loop_id);
```

### 3.4 framework 上の位置付け

3 軸の relationship 図示:

```
基本軸 (Forward HELIX L1-L11)
  └─ uncertainty pocket
       ↓
       Pattern A: UPS (scrum_local_loops)
         S-LOCAL-0 → S-LOCAL-3
       ↓ confirmed
       Pattern B: SRF chain (reverse_local_loops)
         R-LOCAL-0 → R-LOCAL-4
       ↓
       Forward 再合流 (本実装)

基本工程 (Forward) + UPS (Scrum 差し込み) + SRF (Reverse 差し込み + ドキュメント化)
= 3 軸 interlocked framework
```

## §4 Phase 構成

| Phase | スコープ | size | Gate |
|---|---|---|---|
| **Phase 1** | UPS のみ (Pattern A) | M | G4 |
| **Phase 2** | SRF chain (Pattern B + Reverse type matrix 拡張) | M | G4 |
| **Phase 3** | HELIX_CORE.md + SKILL_MAP.md + CLAUDE.md 明文化 + helix doctor 統合 | S | G4 |

Phase 分割により段階導入。Phase 1 のみで UPS は使えるようになり (動作データを集めてから SRF を判断)、Phase 2 で chain 完成。

## §5 受入条件 (Phase 全体)

- [ ] helix.db v29 migration で scrum_local_loops + reverse_local_loops table 追加
- [ ] cli/helix-scrum に `local` subcommand 追加 (init / poc / verify / list / stats)
- [ ] cli/helix-reverse に `from-scrum` + `local` subcommand 追加
- [ ] Reverse type matrix に `scrum-to-forward` type 追加 (SKILL_MAP.md)
- [ ] HELIX_CORE.md / SKILL_MAP.md / CLAUDE.md に 3 軸 interlocked framework を明文化
- [ ] PLAN-079 自身が V-model 4 artifact 双方向 trace 完備
- [ ] pytest / bats 全回帰 PASS
- [ ] 実運用 dogfooding: 次セッション以降の Forward 進行で UPS / SRF を 1 回以上使い、helix.db 記録を確認

## §6 リスク

| ID | リスク | 影響 | 緩和策 |
|---|---|---|---|
| R-01 | 3 軸 interlocked で運用複雑性増大、覚えるべき CLI が多すぎる | 採用率低下 | helix size --uncertain-local で自動判定、CLI は既存 helix scrum / helix reverse に subcommand 追加で導線統一 |
| R-02 | UPS loop の release 漏れ (S-LOCAL-3 未到達で放置) | 状態管理破綻 | stale 検出 (helix scrum local list --stale)、Stop hook で自動 timeout |
| R-03 | SRF chain で R-LOCAL-4 routing 先が見つからない (Forward 接続不能) | dead-end | R-LOCAL-4 で blocked 判定可能、別 PLAN として escalation |
| R-04 | 既存 helix scrum (Forward 開始前用) との混同 | 設計混乱 | local subcommand で明確分離、ドキュメントで「helix scrum init」(Forward 開始前) vs 「helix scrum local」(Forward 内部) を対比 |
| R-05 | scrum-to-forward type が既存 fullback type と概念混乱 | 設計混乱 | fullback = 実装完遂後の文書整合 (Forward L8/L11 後)、scrum-to-forward = PoC の本実装前 artifact 化 (Forward L4 内部) と用途差を明示 |

## §7 依存関係

- 前提: PLAN-075 V-model 4 artifact 原則 (確立済)、PLAN-078 helix.db v28 agent_slots (並走)
- 独立並行可能: PLAN-075 Phase 5 / PLAN-078 Phase 1 (Sprint .1b 以降) / PLAN-079 はそれぞれ別 scope
- 後続: 本 PLAN 完遂後、Phase 4-5 carry / 072/073 retrofit などの実運用で UPS / SRF を dogfooding

## §8 Sprint 構成 (HELIX 標準粒度、Phase 1 のみ詳細化)

| Sprint | 内容 | role | 並列 | estimate |
|---|---|---|---|---|
| .1a | 既存 helix scrum CLI 実装調査 (cli/helix-scrum 構造 / scrum-handoff.md.template) | pm | 単独 | 15 |
| .1b | scrum_local_loops schema 設計 + state machine | pm/tl | 単独 | 20 |
| .2a | D-DB EXT §X scrum_local_loops 起票 | docs | 単独 | 25 |
| .2b | ③ test-design (unit + integration) 起票 | docs | 2 並列 | 40 |
| .3a | v29 migration + cli/lib/scrum_local.py 実装 | se | 単独 | 40 |
| .3b | cli/helix-scrum local subcommand 追加 | se | .3a 完了後 | 30 |
| .4 | ④ test 実装 (Codex pg 2 並列) | qa/pg | 2 並列 | 50 |
| .5 | 4 artifact 双方向 trace 確認 + 全回帰 | pm | 単独 | 20 |
| .6 | commit + push (Phase 1 完遂) | pm | 単独 | 5 |

Phase 1 total estimate: 約 245 分 (size M、PLAN-078 と同規模)
Phase 2 / Phase 3 は別途 Sprint 構成 (本 PLAN finalize 時に詳細化)

## §9 業界標準引用 Retrofit (W5c-12)

PLAN-087 で確立した「業界標準引用ガードレール」に従い、以下を PLAN-079 に接続する。  
対象は 3 つ:

- **Hypothesis-driven validation**: UPS は仮説・検証・判定を短周期で回すため、Lean Startup の *Build-Measure-Learn* / Eric Ries が示す検証ループに整合させる。  
  参照: [The Lean Startup](https://en.wikipedia.org/wiki/The_Lean_Startup)
- **レガシーコード/PoC の記述化**: SRF では PoC 成果物起点での reverse を行うため、Legacy Code 典型文献における *characterization tests*（振る舞い固定）を逆工学前提の安全策として採用する。  
  参照: [Working Effectively with Legacy Code](https://books.google.com/books/about/Working_Effectively_with_Legacy_Code.html?id=fB6s_Z6g0gIC), [Working Effectively with Legacy Code (著書解説)](https://www.oreilly.com/library/view/working-effectively-with/0131177052/)
- **段階的導入・意思決定ゲート**: SRF の R-LOCAL-4 routing と UPS 継続条件は、Stage-Gate/SAFe のゲート運用に近い意思決定分離として扱う。  
  参照: [Scaled Agile — Inspect and Adapt](https://framework.scaledagile.com/inspect-and-adapt), [Cynefin framework](https://en.wikipedia.org/wiki/Cynefin_framework)

### W5c-12 反映点

- UPS S-LOCAL-0〜3 は `Build-Measure-Learn` の仮説立案→投入→測定→判断に対応し、`S-LOCAL-3` の `confirmed/rejected/pivot` を設計判断ログとして明文化する。
- SRF R-LOCAL-1 の characterization test は PoC 逆工学の最小保証として明示し、PoC 仕様の「挙動不変性」を維持してから Forward 再設計へ移行する。
- `Phase 1 の Gate 受入` は段階的導入ゲートの最小版とみなし、`Phase 2`/`Phase 3` へ進む際に次回導入判断を明示する。

## §10 Next Action

1. **本 commit**: PLAN-079 draft 起票のみ
2. **次セッション以降**: PLAN-078 Sprint .1b と並行可能、Phase 5 (PLAN-075 残) とも並行可能 (3 並列 scope)
3. **dogfooding 機会**: 本 PLAN-079 自身の実装中に UPS / SRF を実運用すれば、framework 妥当性検証になる

## Revision History

| 日付 | WBS / Task | 更新内容 | 担当 |
|---|---|---|---|
| 2026-05-19 | W5c-12 | 業界標準引用 retrofit を追加 (Lean Startup, Legacy Code documentation, phased rollout decision gate) | Docs |

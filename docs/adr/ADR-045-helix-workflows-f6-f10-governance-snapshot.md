---
adr_id: ADR-045
title: "HELIX-workflows V2 F6-F10 governance and survival operations snapshot"
status: Proposed
author: PM
created: 2026-05-27
owner: PM
parent_plan: L4-helix-workflows-機能設計plan
process_layer: L4
related_design: docs/v2/L4-architecture/helix-workflows-functional-design.md
sibling_adr: ADR-044
industry_standards:
  - IEEE 42010:2022
  - arc42 §10 Quality Requirements (https://docs.arc42.org/section-10/)
  - arc42 §11 Risks and Technical Debts (https://docs.arc42.org/section-11/)
  - arc42 §9 Design Decisions
  - arc42 §3 Context and Scope
  - DDD Anti-Corruption Layer (Eric Evans 2003, Open Group DDD Strategic Patterns)
  - DDD Bounded Context (Eric Evans 2003)
  - CNCF 2026 Forecast - Autonomous Enterprise Four Pillars (Golden Paths / Guardrails / Safety Nets / Manual Review)
  - SDLC Phase Gate Process
---

# ADR-045: HELIX-workflows V2 F6-F10 governance snapshot

## Context

この ADR は、L4 機能設計 (`docs/v2/L4-architecture/helix-workflows-functional-design.md`) §6〜§10 で導入された **生物学欠落 5 領域 (F6-F10)** の大局判断を、ADR-044 sibling として snapshot 化するためのもの。

ADR-044 は HELIX-workflows V2 三層構造 (Decision-1) / 永続化 4 種 (Decision-2) / BR-12 ratchet (Decision-3) / 二重三重 audit (Decision-4) の 4 大方式を凍結している。本 ADR は **F6-F10 機能領域固有の運用統治 (governance) 軸** を、accepted ADR-044 の汚染を避けつつ追補で凍結する。

### 1.1 ADR-045 が必要な理由

L4 機能設計 doc は前 session で +1402 行追加され、F6-F10 (恒常性/進化/繁殖/排泄/共生) を本体化した。これらは ADR-044 の 4 大方式 (構造/永続化/ratchet/audit) には収まらない **運用統治 (governance) 軸** を持つ。

tl-advisor R1 (2026-05-27 audit) が以下を P0/P1 で指摘:

1. functional-design 内で `Decision-5 (homeostasis governance)` / `Decision-6 (survival operations)` が ADR-044 dangling 参照 (ADR-044 は Decision-1〜4 のみ)
2. F6 metric / F7 promote-guard / F8 migration order / F9 destructive approval / F10 DDD anti-corruption layer の判断未確定

tl-advisor 構造的代替案として「**ADR-044 revision 汚染回避のため ADR-045 として新規起票**」が提示され、本 ADR でこれを採用する。

### 1.2 F6-F10 と ADR-044 の責務分離

| ADR | 対象 | 軸 |
|---|---|---|
| ADR-044 | F1-F5 + 全体 | 構造 / 永続化 / ratchet / audit (アーキテクチャ) |
| **ADR-045** | F6-F10 | 統治 / 安全境界 / 承認ゲート (運用) |

F6-F10 は「生物学欠落 5 領域」として **framework の延命・進化・継承・終了・共生** を担い、ADR-044 の構造判断とは異なる **lifecycle / governance** の判断軸を持つ。

### 1.3 業界標準対応

arc42 公式 (docs.arc42.org) と DDD 戦略設計 (Open Group / Eric Evans 2003) + CNCF 2026 framework governance forecast を参照した。

- **arc42 §10 Quality Requirements**: F6 homeostasis (health monitor) — 品質要件として framework 健全性を測定可能にする
- **arc42 §11 Risks and Technical Debts**: F7 evolution / F9 excretion (selection / lifecycle) — 進化と排泄は技術負債と表裏一体
- **arc42 §9 Design Decisions**: F8 reproduction (version migration) — 世代継承の意思決定
- **arc42 §3 Context and Scope**: F10 symbiosis (framework coexistence) — 外部システムとの境界定義
- **DDD anti-corruption layer**: F10 共生境界 — internal/external context 間の翻訳・防御
- **DDD bounded context**: F10 internal/external 分離
- **CNCF 2026 Four Pillars**: F6 Guardrails (statusLine homeostasis warning) / F9 Safety Nets (apoptosis dry-run + rollback) / F7 Manual Review (promote 承認) / F8 Golden Paths (migration 順序固定)
- **SDLC Phase Gate Process**: F7 promote guard (canary 期間 + 人間承認)
- **IEEE 42010:2022**: 全 Decision の concerns / viewpoint / view 整合

## Decision

以下の 5 大運用統治判断を採択する。全 Decision で `implementation_status` を明記し、BR-12 ratchet を満たす。

### Decision-1: F6 Homeostasis Governance（恒常性統治）

#### implementation_status

`planned`

#### 1.1 選択構造

HELIX framework の **健全性 (health)** を継続的に監視・保護する仕組みを framework として制度化する。

- 監視 metric (planned)
  - `opus_residual_ratio`: Opus 直接実装の残存比率 (delegation ratio の逆数、目標 <20%)
  - `delegation_ratio`: 委譲率 (Codex/Agent 経由実装の比率、目標 >80%)
  - `parallel_compliance_ratio`: 8 並列 default 達成率 (目標 >70%)
  - `gate_pass_rate`: G0-G14 各ゲート通過率
  - `audit_drift_count`: ratchet 違反検出件数 (週次)
  - `carry_residual_count`: session 跨ぎ carry 残数

- 監視周期と発火
  - `statusLine` hook で文脈消費 % 監視 (毎 turn)
  - `PreCompact` hook で重要 state 永続化
  - 週次 `helix budget --homeostasis` で集計と告警

- 反応 (homeostatic response)
  - 閾値超過時に `helix doctor --check-homeostasis` で警告
  - 重大乖離時に PM へエスカレーション (advisor 召喚推奨)
  - 自動修復は基本行わない (人間判断介在を保持)

#### 1.2 採用理由

framework が成熟しても **「Opus が実装に降りる」「並列を取らない」「carry が溜まる」** という運用上の劣化 (homeostasis 喪失) が継続的に発生する。これを **定量監視 + 警告 + 人間判断介在** の 3 段で抑制する。

biology metaphor: 体温/血糖/pH を恒常的に維持する homeostasis 機構と同型。「恒常性」は framework の延命に直結する。

業界標準: arc42 §10 Quality Requirements (測定可能な品質目標) + CNCF 2026 Guardrails (高レベル準拠要件 → 実行可能な自動 enforcement) に整合。

#### 1.3 実装要件

- `helix.db.metrics_log` table で metric 永続化
- `cli/lib/homeostasis.py` で metric 集計
- `helix budget --homeostasis` CLI 実装 (L5 詳細設計 carry)
- `helix doctor --check-homeostasis` check 実装 (L5 carry)
- 監視周期 / 閾値は L5 で確定

#### 1.4 L4 §6 適用

L4 functional-design §6 (F6 恒常性) で機能定義 + 監視 metric 列挙。本 ADR でその governance ルール (反応 / 閾値 / エスカレーション境界) を凍結。

#### 1.5 期待効果

1. framework 劣化の早期検出
2. delegation ratio の継続的可視化
3. carry 残存の自動 alert 化
4. Opus / Codex / Agent の責務境界維持

---

### Decision-2: F9 Survival Operations（生存運用 / apoptosis + autophagy）

#### implementation_status

`planned`

#### 2.1 選択構造

framework の **不要要素を能動的に排除する仕組み (apoptosis)** + **不要 state を自浄する仕組み (autophagy)** を制度化する。

- apoptosis (能動的排除)
  - 対象: 古い PLAN / superseded ADR / 廃止 skill / 不要 file
  - 発火: `helix plan apoptosis` CLI (手動 + 週次 cron)
  - 安全 gate: **dry-run 先行 + 承認 + idempotency + 保護対象リスト**
  - 履歴: `helix.db.obsolete_record` table に保存 (rollback 可能)

- autophagy (自浄)
  - 対象: helix.db 古い event_log / metrics_log / audit_link
  - 発火: `helix db autophagy` CLI (週次)
  - 安全 gate: retention policy + 重要 evidence の自動保護
  - 履歴: 削除 manifest を git history に commit

#### 2.2 採用理由

framework が成熟すると **古い PLAN / 廃止 skill / stale event** が累積し、検索性 / 可読性 / 性能を劣化させる。これを **能動的排除 (apoptosis)** + **自浄 (autophagy)** の 2 段で制度化する。

biology metaphor: 細胞の programmed cell death (apoptosis) + 自己消化 (autophagy) と同型。framework の **若返り** に直結する。

業界標準: CNCF 2026 Safety Nets (auto-revoking permissions + time-bound limits) + SDLC retire phase の延長として扱う。

#### 2.3 実装要件 (★ 安全ゲート必須)

- **dry-run 先行**: 削除前に対象 list を生成、人間確認
- **保護対象リスト**: `accepted` 状態の ADR / `implemented` 状態の機能 PLAN / 直近 N 日の event は除外
- **idempotency**: 二重発火しても副作用なし
- **承認ゲート**: production 環境では `--approved` flag 必須
- **rollback evidence**: 削除分は `.helix/audit/apoptosis-YYYYMMDD.yaml` に full manifest 保存
- **destructive 監査**: G14 運用ゲートで apoptosis 履歴を audit

#### 2.4 L4 §9 適用

L4 functional-design §9 (F9 排泄) で機能定義。本 ADR でその governance ルール (安全ゲート + 承認 + rollback evidence) を凍結。

#### 2.5 期待効果

1. PLAN / ADR 蓄積による検索性劣化を防止
2. helix.db サイズの自然増を抑制
3. 廃止 skill の混入を阻止
4. **誤削除リスクを承認ゲートで最小化**

---

### Decision-3: F7 Evolution Promotion Guard（進化 promote 安全境界）

#### implementation_status

`planned`

#### 3.1 選択構造

framework / PLAN / skill / hook の **進化 (variation + selection)** を制度化しつつ、自動 promote の暴走を阻止する安全境界を導入する。

- 進化サイクル
  - **Variation**: `helix plan fork` で代替案を分岐
  - **Selection**: `helix evolution score` で metric ベース評価
  - **Promotion**: `helix evolution promote` で正本昇格
  - **Deprecation**: `helix evolution deprecate` で旧 fork 廃止

- 安全境界 (★ promote 自動化のリスク制御)
  - **score 閾値**: promote には minimum score (例: 0.7+) を必須
  - **dry-run 期間**: production 反映前に dry-run / canary 期間 (例: 1-2 session)
  - **人間承認 or advisor 承認**: 重要変更 (parent_design / accepted ADR 改変) は人間承認必須
  - **revert 経路**: promote 後 N session 以内なら無条件 revert 可能

#### 3.2 採用理由

framework が成熟すると **「より良い PLAN / skill / hook」への進化** が常時候補化される。これを無制御で promote すると **設計 drift を増幅** するリスク (前 session の `feedback_two_round_audit_dogfood_drift_pattern` Pattern A 該当)。

biology metaphor: 変異 (variation) と自然選択 (selection) の進化サイクル。**過度な自動化は drift を加速** するため、score + dry-run + 承認の 3 段で抑制。

業界標準: SDLC Phase Gate Process (各 phase で risk control + accountability) + CNCF 2026 Manual Review Workflow (重要変更は人間判断介在) + canary release pattern。

#### 3.3 実装要件

- `helix.db.plan_history` table で fork / score / promote 履歴を永続化
- `helix plan fork` / `helix evolution {score,promote,deprecate}` CLI (L5 carry)
- score 算定式は L5 で確定 (delegation_ratio / gate_pass_rate / audit_drift_count を入力)
- promote dry-run 期間と canary 範囲は L5 で確定

#### 3.4 L4 §7 適用

L4 functional-design §7 (F7 進化) で機能定義。本 ADR でその promote guard (score 閾値 / dry-run / 承認境界 / revert 経路) を凍結。

#### 3.5 期待効果

1. fork-based 改善の体系化
2. 設計 drift の制御された promote
3. revert 可能性の保証
4. 自動化と人間判断の責務境界明確化

---

### Decision-4: F8 Reproduction Order（繁殖 / version migration 順序固定）

#### implementation_status

`planned`

#### 4.1 選択構造

HELIX framework / project の **世代継承 (reproduction)** で、breaking change を伴う migration 順序を **固定** する。

- 固定順序 (★ 順序逸脱は data loss リスク)
  1. **schema_version bump** (`helix.db` schema)
  2. **plan_version bump** (PLAN frontmatter schema)
  3. **portable export** (`helix portable export` で旧版 snapshot)
  4. **project apply** (`helix migrate` で新版適用)
  5. **rollback evidence** (`.helix/audit/migration-YYYYMMDD.yaml` に full state)
  6. **smoke test** (G13 安定性確認)

- 互換性
  - **backward compat 1 stage**: 1 つ前の schema からの自動 migrate を保証
  - **forward compat warn-only**: 新版 framework で旧版 PLAN を読み込んだ場合は warn のみ
  - **breaking change cap**: 1 release 内で複数 schema bump 禁止

#### 4.2 採用理由

framework の version 進化で migration を **不規則順序** で実行すると、PLAN / ADR / helix.db の整合が崩れ、復旧不可能になるリスクがある。**順序固定 + rollback evidence** の 2 段で安全化。

biology metaphor: DNA replication の order-preserving 複製と同型。「世代継承」は framework の継続性に直結。

業界標準: arc42 §9 Design Decisions (重要決定の文書化) + CNCF 2026 Golden Paths (推奨経路の固定化) + 12-factor migration discipline。

#### 4.3 実装要件

- `helix.db.version_tag` table で migration 履歴を保存
- `helix version bump` / `helix migrate` / `helix portable {export,import,adopt}` CLI (L5 carry)
- backward compat 自動 migration script は L5 で確定
- breaking change の `BREAKING.md` 必須化 (G14 audit)

#### 4.4 L4 §8 適用

L4 functional-design §8 (F8 繁殖) で機能定義。本 ADR でその migration order (6 step 固定) + 互換性 + breaking change cap を凍結。

#### 4.5 期待効果

1. data loss リスクの最小化
2. rollback の always-available 性
3. migration debug の容易化
4. multi-project / multi-version 並走の安全性

---

### Decision-5: F10 Symbiosis DDD Anti-Corruption Layer（共生 / 境界保護）

#### implementation_status

`planned`

#### 5.1 選択構造

HELIX framework が **第三者 framework / skill / project と共生** する際の境界保護を、**DDD anti-corruption layer + Bounded Context** で制度化する。

- 境界保護構造
  - **Internal context (HELIX core)**: cli / skills / docs / helix.db
  - **External context (第三者)**: Codex CLI / Claude Code / GitHub / MCP server / 他 OSS
  - **Anti-Corruption Layer (ACL)**:
    - **adapter**: `cli/helix-codex` / `cli/helix-claude` / `cli/helix-coexist` 等の wrapper
    - **translator**: 外部 schema → HELIX schema への変換層
    - **guard**: external 変更が internal context を破壊しない fail-close

- 共生受入規約
  - `helix coexist framework <name>` で第三者 framework を宣言
  - `helix coexist status` で現状一覧
  - `helix coexist adopt --compatibility-adr <ADR-NNN>` で互換 ADR を併設
  - namespace 競合は宣言時に rejection

- 互換 ADR schema
  - 第三者 framework の version range
  - HELIX 側 adapter 実装位置
  - 境界 contract (input / output / error semantics)
  - rollback 戦略

#### 5.2 採用理由

framework が孤立すると価値が低下し、他システムと安直に統合すると internal context が **腐食 (corruption)** する。**ACL + Bounded Context** で **接続するが侵されない** 共生を保つ。

biology metaphor: endosymbiosis (細胞内共生) と mutualism (相利共生)。境界 (細胞膜) を維持しつつ相互利益を取る。

業界標準: DDD Strategic Design (Eric Evans 2003 + Open Group DDD Strategic Patterns) の Anti-Corruption Layer pattern を framework 境界に適用。Microsoft Azure Architecture Center の ACL pattern 解説 (https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer) と整合。bounded context により internal/external semantics の混入を防ぐ。

#### 5.3 実装要件

- `helix.db.coexist_config` table で第三者 framework 一覧と互換 ADR link を保存
- `helix coexist {framework,status,adopt}` CLI (L5 carry)
- ACL adapter 実装位置は `cli/helix-<external-name>` 命名規則で固定
- 互換 ADR schema は L5 で確定 (ADR-NNN-coexist-<name>.md template)
- namespace 競合 fail-close は `helix doctor check_framework_coexist` で機械化

#### 5.4 L4 §10 適用

L4 functional-design §10 (F10 共生) で機能定義。本 ADR でその DDD ACL 構造 + 受入規約 + namespace 競合 fail-close を凍結。

#### 5.5 期待効果

1. 第三者 framework との安全な統合
2. internal context の腐食阻止
3. multi-framework 環境での namespace 安全性
4. 互換 ADR による version 進化追従

---

## Consequences

### 採択の積極効果

1. **F6-F10 governance の体系化**: framework の延命・進化・継承・終了・共生が運用ルールとして凍結
2. **ADR-044 汚染回避**: accepted 状態の ADR-044 を改変せずに F6-F10 大局判断を追補
3. **dangling 参照解消**: functional-design 内の `Decision-5/6` 参照が ADR-045 へ正規 link 化
4. **業界標準整合**: arc42 §9/§10/§11/§3 + DDD ACL + CNCF 2026 Four Pillars を framework に明示的に統合
5. **biology metaphor の framework 還元**: 神 metaphor (恒常性/進化/繁殖/排泄/共生) が運用判断軸として制度化

### 既存 doc への影響

| doc | 修正内容 |
|---|---|
| `docs/v2/L4-architecture/helix-workflows-functional-design.md` | `Decision-5/6` 参照を `ADR-045 Decision-1/2` に書換 (P0-B 修正と同時) |
| `docs/plans/L4/L4-helix-workflows-機能設計plan.md` | frontmatter `adr_snapshot` に `ADR-045` 追加 |
| `docs/v2/L9-test-design/helix-workflows-functional-test-design.md` | ST-F6〜F10 の DoD に ADR-045 Decision-N pair freeze 明示 |
| `docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md` | sibling_adr セクションに ADR-045 link 追加 |

### リスクと対策

| リスク | 対策 |
|---|---|
| ADR-045 が ADR-044 と重複しないか | 軸分離明示 (044 = 構造/永続化/ratchet/audit, 045 = governance/lifecycle) |
| F6-F10 CLI が planned のまま放置 | L5 carry に明示、`helix doctor check_planned_cli_age` で stale 検出 |
| ACL pattern が複雑化 | L5 で adapter template 確定、第三者 framework 受入は 1 件目を pilot として実装 |
| apoptosis 誤削除 | 安全ゲート 4 段 (dry-run / 保護 list / 承認 / rollback evidence) で多層防衛 |
| evolution promote drift | score 閾値 + canary 期間 + 人間承認境界で抑制 |

### 監査 trace

- 各 Decision は `helix.db.metrics_log` / `plan_history` / `version_tag` / `obsolete_record` / `coexist_config` table に対応
- G7 (実装完了) で `implementation_status` を check
- G14 (運用学習) で homeostasis / apoptosis 履歴を audit

## Alternatives

### Alt-1: ADR-044 に Decision-5〜9 として追加

却下。理由:
- ADR-044 は accepted state に近く revision 汚染リスク
- ADR-044 の軸 (構造/永続化/ratchet/audit) と F6-F10 軸 (governance/lifecycle) は責務が異なる
- 単一 ADR が肥大化すると可読性 / 改訂頻度のバランスが悪化

### Alt-2: F6-F10 を全て個別 ADR (ADR-045〜049) に分割

却下。理由:
- 5 ADR の同時起票はレビュー負荷が過大
- F6-F10 は「生物学欠落 5 領域」として一体性があり、分離すると cross-reference が複雑化
- 後段の L5 詳細設計で各 Decision が独立 ADR に分離する余地は残す (ADR-045a/b/c... の sub-id 採番ルール検討)

### Alt-3: ADR-045 を skip し functional-design 内で governance を直接定義

却下。理由:
- 大局判断 (governance / 安全境界) は L2 snapshot として ADR に永続化が筋 (PLAN ⊃ ADR layer 併存原則)
- doc 内直接記述は drift しやすく、accepted 状態管理が困難
- 業界標準 (IEEE 42010 / arc42) との整合が ADR に集中する方が trace 性が高い

## Compliance

- **IEEE 42010:2022**: 全 Decision で concerns / viewpoint / view 整合を明示
- **arc42 §9 Decisions**: F8 reproduction
- **arc42 §10 Quality**: F6 homeostasis
- **arc42 §11 Risks**: F7 evolution / F9 excretion
- **arc42 §3 Context**: F10 symbiosis
- **DDD anti-corruption layer**: Decision-5
- **DDD bounded context**: Decision-5
- **CNCF 2026 Four Pillars** (Golden Paths / Guardrails / Safety Nets / Manual Review): Decision-1〜5
- **SDLC Phase Gate Process**: Decision-3 promote guard
- **BR-12 ratchet**: 各 Decision で `implementation_status` 明記
- **PLAN ⊃ ADR layer 併存**: L4 PLAN tree 内で本 ADR を snapshot

## 関連 ADR 参照

- **ADR-044** (sibling): HELIX-workflows V2 三層構造 + 永続化 4 種 + BR-12 ratchet + 二重三重 audit
- **ADR-040** (workspace isolation): Codex sandbox 境界、本 ADR-045 Decision-5 の境界保護と整合
- **ADR-041** (drift type 7 categories routing): 本 ADR-045 Decision-1 監視 metric の drift 分類と整合
- **ADR-043** (mode enum extension retrofit): 本 ADR-045 Decision-4 backward compat 思想と整合

## 実装状況ノート

- 本 ADR は `Proposed` 状態で起票。各 Decision の CLI / hook / table 実装は L5 詳細設計 carry
- L4 functional-design (`docs/v2/L4-architecture/helix-workflows-functional-design.md`) で `Decision-5/6` 参照を本 ADR の Decision-1/2 link に書換 (同 wave で実施)
- L4 機能設計 plan (`docs/plans/L4/L4-helix-workflows-機能設計plan.md`) frontmatter `adr_snapshot` に ADR-045 追加 (同 wave で実施)
- 各 Decision の `implementation_status` は `planned`、L7 実装完了時に `implemented` 遷移

## TODO 残存

- [ ] L5 詳細設計で各 Decision の CLI/hook/table を確定
- [ ] L9 test design ST-F6〜F10 の DoD に ADR-045 Decision-N pair freeze 明示
- [ ] F10 互換 ADR schema template (`ADR-NNN-coexist-<name>.md`) を L5 carry で確定
- [ ] F9 apoptosis 安全ゲート 4 段の具体閾値 (保護対象 N 日) を L5 で確定
- [ ] F7 evolution score 算定式 (delegation_ratio / gate_pass_rate / audit_drift_count) を L5 で確定
- [ ] ACL adapter 1 件目 pilot 実装 (Codex / Claude のうち 1 つを reference 化)

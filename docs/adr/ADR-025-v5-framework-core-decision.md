# ADR-025: V5 framework 本体採用判断

## Status

Proposed (2026-05-20、PLAN-091 と同時起票、draft 段階)

> 遷移予定: Proposed → Accepted (PLAN-091 tl-advisor Round 3 adversarial check PASS 後、PO 承認で Accepted)

## Deciders

- PM (Opus、PM 設計判断・最終承認)
- TL (Codex tl-advisor gpt-5.5 high、adversarial check Round 2 以降)
- PO (yoshiyuki0907yn@gmail.com、Accepted 承認)

## Supersedes

なし (新規採用判断)

## Related

- [PLAN-091](../plans/PLAN-091-v5-framework-core.md): 本 ADR の実装 tree (本 ADR は PLAN-091 の L2 大局判断 snapshot)
- [PLAN-MM-001](../plans/PLAN-MM-001-v5-framework-master-plan.md): V5 全体構想 (親設計)
- [ADR-018](ADR-018-db-separation-and-event-sourcing.md): V2 DB 分離の L2 凍結 (本 ADR の前段 framework 確立)
- [ADR-019](ADR-019-event-sourcing-dual-helix-strand.md): 二重らせん strand の L2 凍結 (本 ADR の前段)
- [ADR-014](ADR-014-roles-config-format.md): roles 設定形式の L2 凍結 (本 ADR の agent_slots 設計の前提)
- [ADR-015](ADR-015-helix-v2-orchestration.md): HELIX V2 orchestration の L2 凍結 (本 ADR の前段 V2 方針)
- PLAN-087: 設計 doc Web 検索ガードレール (§3 WebSearch 義務の根拠 PLAN)
- PLAN-088: TodoWrite × agent slot framework (§5.5 agent_slots の前段 PLAN)
- PLAN-089: gate fail-close staged adoption (§9 段階導入 P3 の前段 PLAN)
- PLAN-090: PostToolUse continueOnBlock + active guidance loop (ADR snapshot × PostToolUse の前段 PLAN)

---

## 業界 standard 参照 (PLAN-091 §3 と同一 Sources)

| 参照 | Source URL | 本 ADR での引用箇所 |
|---|---|---|
| GitHub Spec-Kit | https://github.com/github/spec-kit | §Decision の PLAN = self-contained doc 設計の業界整合 |
| AWS Kiro Spec-Driven Development | https://thebcms.com/blog/spec-driven-development | kind 別 template embed の業界整合 |
| ADR best practices — AWS Architecture Blog | https://aws.amazon.com/blogs/architecture/master-architecture-decision-records-adrs-best-practices-for-effective-decision-making/ | ADR snapshot 必須化 (V5 要素 #11) の業界根拠、append-only log 原則 |
| Microsoft Azure Well-Architected ADR | https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record | ADR の Supersedes / Related フィールド設計根拠 |
| Flagsmith: Feature flags staged rollout | https://www.flagsmith.com/blog/how-to-enhance-phased-rollouts-with-feature-flags | 段階導入 5 Phase (P1 warn-only → P3 fail-close) の業界整合 |
| OpenFeature / Cloudflare Flagship progressive delivery | https://www.infoq.com/news/2026/05/cloudflare-flagship-openfeature/ | P2 matrix 検証 → P3 fail-close 段階遷移設計の根拠 |
| CrewAI Core Concepts — Agent roles | https://docs.crewai.com/core-concepts/Agents/ | agent_slots 定義の業界整合 |

---

## Context

### C1. V1→V5 確立過程

2026-05-19〜20 の session で、HELIX PLAN 管理の根本的な再設計が V1 から V5 まで確立された。

| Round | 確立要素 | TL verdict |
|---|---|---|
| v1 | matrix + 種別 (5 kind) | passed (bs9wuvqcs) |
| v2 | + 依存 + agent_slots + 自動登録 | passed (bppaf3fwe) |
| v3 | + template embed + kind 11 種 | passed (bkac94gnw) |
| v4 | + V-model TDD + PoC リバース合流 | passed (baq742e62) |
| **v5** | + 自動走行 framework 18 番要素 | **passed_with_minor_changes** (bdnmyhznq) |

本 ADR は v5 の「passed_with_minor_changes」の修正条件 (Critical 3 + Important 6 + Minor 3) を全件反映した改訂版 (Round 2 反映)。

### C2. 既存 HELIX 資産の限界

V5 framework 導入前の HELIX では:

1. **PLAN frontmatter 不在**: kind / layer / drive / generates / dependencies / agent_slots が機械可読形式で存在しない
2. **種別不在**: design / impl / poc / reverse 等の区別が自然言語のみ、CLI 強制不可
3. **dependency 管理不在**: PLAN 間の依存が文書化されず、並列投入時の衝突リスク管理不可
4. **workflow_phase 不在**: R0-R4 / S0-S4 を layer に混在させた設計が行われ、validator 矛盾が潜在化
5. **PostToolUse 自動登録不在**: PLAN.md を Write しても helix.db に自動登録されない
6. **単一実行正本不在**: task_queue / TodoWrite / helix job / handover が競合、「どれが正本か」不明
7. **ADR snapshot 任意**: L2 大局判断があっても ADR snapshot が起票されない PLAN が存在 (PLAN-087〜090)
8. **agent_slots 独自 slug 問題**: codex-tl / codex-se 等の独自 role 名が ROLE_MAP と乖離

### C3. TL v5 round 5 修正条件の主要点 (Round 2 で反映)

v5 passed_with_minor_changes の修正条件のうち、本 ADR に直接影響する主要項目:

1. **P0 (絶対遵守)**: 承認なし task pop は HELIX discipline 破壊 → queue worker は必ず plan guard を通す。plan_valid は前提条件に過ぎず、実行許可には explicit_consent / wbs_match / handover_match の 3 条件のいずれかが必須
2. **P1 (設計時要考慮)**: task_queue / TodoWrite / helix job / handover の競合 → 単一実行正本を決める
3. **Critical: workflow_phase 新設**: R0-R4 / S0-S4 を layer と別フィールドに分離し、layer は L 系 15 種 + cross のみに限定
4. **Critical: agent_slots ROLE_MAP 整合**: role は cli/ROLE_MAP.md の 30 種 enum に固定、モデル名は frontmatter から排除
5. **Critical: P0 guard 設計強化**: helix plan validate (構文 validator) ≠ 実行承認。authorization_ref / authorized_by / approved_at / source_plan_id の必須フィールド追加
6. **Important: CLI 命名衝突解消**: helix plan create / validate / show の新命名を既存 draft / lint --v5 / status --frontmatter に統合
7. **Important: template commit step 削除**: 委譲 Codex は git commit 禁止 (CLAUDE.md §委譲 Codex のコミット禁止)
8. **Important: QA 追加テスト位置付け**: L6 で独立レイヤーとして追加、既存設計 doc を置換しない

### C4. Tier A/B/D 前提誤りの訂正 (2026-05-20、本 session 確認)

本 session 開始時点で Opus は以下の整理を行っていた:
- Tier A: handover 6 件 pending (PLAN-087〜090 + ADR-021〜024)
- Tier B: V5 framework 9 PLAN + 8 ADR の新規起票
- Tier D: recovery 個別起票

ユーザーより「V5 framework 9 PLAN がそれをすべて含み、それを除けば他は破棄してよい」と指摘。

**訂正**: この整理は誤り。正しくは「V5 framework (Tier B の 9 PLAN + 8 ADR) は Tier A/D を吸収した上位概念ではなく、Tier A/B/D の分類自体が不要になる framework」。

具体的には:
- ADR-021〜024 (Tier A) は V5 の 9 PLAN/8 ADR 体系の中の retrofit PLAN-100 で一括対処
- recovery 個別起票 (Tier D) は V5 の kind=recovery + PLAN-098 で体系化
- Tier A/B/D の 3 分類は V5 起票後に廃止してよい

この訂正により、次 session 以降は「Tier X carry」という表現を使わず、「V5 子 PLAN NNN」という表現に統一する。

---

## Decision

### D1. V5 framework 18 要素を HELIX 正規体系として採用する

V5 framework の以下 18 要素を HELIX の正規 PLAN 管理体系として採用する:

1. PLAN = self-contained workflow ルール doc (TodoWrite → PLAN 永続化置換)
2. V-model layer (L0-L11、L3.5/L4.5) × drive (9 種) matrix + workflow_phase (S0-S4/R0-R4) 別フィールド
3. 種別正規化 (11 kind)
4. matrix 外 / kind 不在を helix plan CLI で fail-close (段階導入 P3 以降)
5. 生成物 trace (frontmatter `generates`、16 artifact_type)
6. 依存関係 graph (frontmatter `dependencies`、cycle + reciprocal + self-edge 検証)
7. agent slot 割当 (frontmatter `agent_slots`、ROLE_MAP 30 種 enum)
8. PostToolUse hook で PLAN.md → helix.db 自動登録 (PLAN-092 担当)
9. PLAN ↔ 設計 doc drift 検出 (PLAN-093 担当)
10. 進捗 trace (PLAN-092/093 担当)
11. ADR snapshot 必須化 (PLAN ⊃ ADR レイヤー併存)
12. kind 別 workflow template embed (11 種、commit step なし)
13. V-model TDD 駆動 (設計⇔テスト設計 pair freeze + QA 追加テスト独立レイヤー)
14. PoC = Scrum × Reverse 連携 matrix (PLAN-095 担当)
15. GitHub 運用ルール統合 (PLAN-096 担当)
16. helix_improvement_plan_draft.md 6 Phase 統合 (PLAN-093/097 担当)
17. リカバリープラン kind (PLAN-098 担当)
18. 自動走行 framework 5-layer (PLAN-099 担当)

### D2. 単一実行正本を以下の 4 者分担で確定する (TL v5 P1 解消)

| 候補 | 役割 | 決定 |
|---|---|---|
| PLAN (plan_registry) | PLAN 定義の単一 source of truth | **plan_registry テーブル (PLAN-092)** |
| helix job / scheduler | runnable execution queue | **既存継続、task_queue 新設禁止** |
| handover | session continuity | **既存継続** |
| TodoWrite | ephemeral checklist | **既存継続、昇格条件を PLAN-091 §6.3 で定義** |

PLAN-099 §Layer 1 の「PLAN.md Write → auto-enqueue」設計は `helix job enqueue` への enqueue として実装する。

### D3. 段階導入 5 Phase を採用する (feature flag 段階遷移)

| Phase | 内容 | fail-close |
|---|---|---|
| P1 | warning 導入 (matrix 外でも続行) | exit 0 + stderr 警告 |
| P2 | matrix 検証 (helix plan lint --v5) + reciprocal consistency | exit 0 + warn |
| P3 | fail-close 強制 (matrix 外 reject、layer に R0/S0 等も reject) | exit 2 |
| P4 | retrofit (PLAN-001〜090 一括拡張) | — |
| P5 | Curator 自動化 | — |

P3 fail-close は PLAN-089 (gate fail-close staged adoption) の設計パターンに準拠。

### D4. P0 承認 guard を設計に組み込む (TL v5 P0 遵守)

**plan_valid は前提条件、実行許可は 3 条件 OR**:

queue worker が task を pop する前に以下の **3 条件のいずれかを fail-close で確認**する:

| 条件 | 説明 |
|---|---|
| `explicit_consent` | ユーザーの明示承認 (OK / 実装して / proceed 等) |
| `current_wbs_match` | 作業対象が L3 工程表 / task-plan.yaml の現在行に一致 |
| `handover_next_action_match` | handover Next Action に明示記載された task |

`helix plan lint --v5` (plan_valid) は上記 3 条件の前提であり、それだけでは dispatch を許可しない。job payload に `authorization_ref / authorized_by / approved_at / source_plan_id` を必須追加 (PLAN-092 schema 設計)。

### D5. Layer A → B → C の着手順序を採用する

```
Layer A (本 ADR の対象、工程ルール整備)
  → Layer B (PLAN-092/093、helix.db 型ハーネス)
    → Layer C (PLAN-099、連携自動化ハーネス)
```

Layer C の PoC C 案 (Layer 4+5) のみ Layer A/B 確定前に並行 PoC 可。

### D6. workflow_phase フィールドを新設し R0-R4 / S0-S4 を layer から分離する

- layer: L 系 15 種 + cross のみ許可 (validator P3 以降で R0-R4 / S0-S4 を layer に書いたら exit 2)
- `poc` / `reverse` kind の詳細フェーズは frontmatter `workflow_phase: S0|S1...|R0|R1...` で表現
- SKILL_MAP §Phase R / §Phase S との整合を workflow_phase で実現

### D7. agent_slots.role を cli/ROLE_MAP.md の 30 種 enum に固定する

- `codex-tl` / `codex-se` / `codex-pg` 等の独自 slug は廃止
- `slot_label` フィールドで表示名を自由記述
- モデル名 (gpt-5.5 等) は frontmatter に書かず cli/config/models.yaml 参照

---

## Consequences

### Positive

| 効果 | 詳細 |
|---|---|
| drift 検出 | generates trace により設計 doc ↔ 実装ファイルの drift を helix doctor で自動検出可能 |
| 進捗 trace | sprint_progress テーブルで PLAN 単位の進捗を DB 管理、handover メモを短縮化 |
| agent slot 機械化 | frontmatter agent_slots から PLAN-088 経由で parallel 投入計画を機械生成可能 |
| ADR snapshot 必須化 | L2 大局判断の文書化漏れを helix doctor で検出、知識の揮発を防ぐ |
| recovery 標準化 | kind=recovery で session 断絶リカバリーを標準 workflow として扱える |
| fail-close 段階導入 | P1 warning → P3 fail-close の段階遷移で blast radius を最小化しつつ規律を強化できる |
| 単一実行正本 | task_queue / TodoWrite / helix job / handover の競合が解消される |
| P0 guard 明確化 | plan_valid ≠ 実行許可、3 条件 OR による承認 trace が完全 |
| workflow_phase 分離 | R0-R4 / S0-S4 の layer 混在による validator 矛盾が解消される |
| ROLE_MAP 整合 | agent_slots が 30 種 enum で機械強制され、独自 slug による drift が防止される |

### Negative / Risks

| リスク | 緩和策 |
|---|---|
| 既存 PLAN-001〜090 の retrofit コスト | PLAN-100 で docs role 並列 retrofit (段階化)、helix doctor advisory mode |
| helix.db schema v33 → v35 migration | PLAN-092 で migration idempotent 設計 + PLAN-085 staging 演習パターン準拠 |
| PostToolUse hook の性能影響 | PLAN-092 で fail-open 設計、重い sync は background 処理 (TL v5 P2) |
| PoC C 案 PreCompact decision:block の誤用 | 3 条件 AND 限定 (PLAN-099 §Layer 3)、通常は warning のみ |
| statusLine のノイズ化 | debounce + hysteresis 実装必須 (PLAN-099 §Layer 2)、TL v5 P2 |
| claude-brain 型履歴保存の PII リスク | transcript_path 参照 + 要約 state のみ。全量キャプチャ禁止 (PLAN-099 §Layer 4)、TL v5 P3 |
| frontmatter 語彙の drift (子 PLAN 間) | 本 ADR + PLAN-091 §5 が唯一の正本。変更は ADR-025 改訂 + tl-advisor 必須 |
| P0 guard 段階導入中の既存 job との互換性 | P1/P2 では authorization_ref 不在でも warn のみ、P3 以降で fail-close |

---

## Alternatives

### Alt 1: V2 現状維持 (棄却)

V2 framework のまま frontmatter なし / 種別なし / dependency なし で運用継続。

**棄却理由**: PLAN-087〜090 で L2 大局判断に ADR snapshot が不在となり「PLAN ⊃ ADR レイヤー併存違反」が発覚。同様の問題が今後も累積するため、機械的強制が必要。また PLAN の依存関係が文書化されないまま並列投入が行われ、衝突リスク管理が不可能。

### Alt 2: 部分採用 (frontmatter のみ追加、kind/layer/drive 導入省略) (棄却)

frontmatter に plan_id と status のみ追加し、matrix / template embed は省略。

**棄却理由**: TL v5 adversarial check で「matrix 外を CLI で検出できないと drift が止まらない」と指摘。種別 (kind) と layer が機械可読でないと PLAN-092 の PostToolUse 自動登録や PLAN-093 の drift 検出が意味を持たない。部分採用は「形だけ frontmatter」状態になり、5 Phase 段階導入の P3 fail-close に到達できない。

### Alt 3: V5 18 要素全採用 (採用)

本 ADR §Decision の通り、18 要素を Layer A→B→C の 3 層 + 段階導入 5 Phase で採用する。TL 5 ラウンド adversarial check 全 passed の根拠に基づき採用。

### Alt 4: task_queue 独立新設 (棄却)

helix job とは別に task_queue テーブルを新設し、PLAN からの自動 enqueue 先として使用する。

**棄却理由**: TL v5 P1 指摘「単一の実行正本を決める」に直接違反。task_queue / helix job / handover の三者が競合し、「どれが正本か」問題が再発する。責務が重複する 2 つの queue を維持するコストも高い。

### Alt 5: 既存 helix plan lint 拡張のみ (棄却)

matrix / dependencies / agent_slots の検証を既存 lint に追加するだけで、新フィールド (workflow_phase / agent_slots.role) は追加しない。

**棄却理由**: 種別正規化 (kind 11 種) / dependencies 3-rule 検証 / agent_slots ROLE_MAP 整合を既存 lint の拡張として表現するには、実質的に V5 の機能追加が必要であり差異がない。また workflow_phase フィールドを導入しない場合、poc / reverse kind を使う PLAN で layer に R0-S0 が混在し続け、matrix validator の矛盾が解消されない。

### Alt 6: ADR snapshot 任意継続 (棄却)

L2 大局判断があっても ADR snapshot は任意のまま、强制しない。

**棄却理由**: PLAN-087〜090 の 4 件全てで ADR snapshot が起票されず、「PLAN ⊃ ADR レイヤー併存違反」が発覚した。任意のままでは同じ問題が繰り返される。helix doctor による機械検出 + fail-close (Phase 3 以降) が必要。

---

## Implementation Plan

本 ADR の採用決定に基づき、以下の順序で実装する:

| PLAN | 担当 | Layer | 優先度 |
|---|---|---|---|
| PLAN-091 (本 PLAN) | 本体 (matrix + 種別 + template + 単一実行正本 + P0 guard) | Layer A | 最優先 (契約 seed) |
| PLAN-092 | PostToolUse 自動登録 + helix.db v35 schema + P0 guard payload | Layer B | PLAN-091 後 |
| PLAN-093 | drift 検出 + 進捗 trace + Curator + check_plan_adr_snapshot | Layer B | PLAN-091 後 |
| PLAN-100 | 既存 retrofit + V2 全面見直し + ADR-021〜024 後追い snapshot | Layer A (retrofit) | PLAN-091 後 |
| PLAN-095 | PoC = Scrum × Reverse matrix | Layer A | PLAN-091 後 |
| PLAN-096 | GitHub Actions + ブランチパイプライン | Layer A | PLAN-091 後 |
| PLAN-097 | 抽象化層 + エスカレーション | Layer A | PLAN-091 後 |
| PLAN-098 | リカバリープラン kind 正規化 | Layer A | PLAN-091 後 |
| PLAN-099 | 自動走行 framework 5-layer (PoC C 案は Layer A/B 並行可) | Layer C | PoC C 案は並行可、本実装は Layer A/B 後 |

---
plan_id: PLAN-100
title: "PLAN-100: 既存 PLAN-001〜090 retrofit + V2 全面見直し + ADR-021〜024 snapshot 後追い起票"
layer: cross
kind: retrofit
status: draft
size: L
drive: be
created: 2026-05-20
revised: "2026-05-21 (PLAN-094 → PLAN-100 リネーム、PLAN-099 完了後着手の後段化、V5 framework 着手 scope は PLAN-091〜099 に限定)"
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・V2 見直し整合・finalize"
  - role: pmo-sonnet
    slot_label: "PMO — retrofit 計画策定・整合確認・ADR snapshot 起票"
  - role: docs
    slot_label: "Docs retrofit parallel #1 — PLAN-087〜090 frontmatter (P1)"
  - role: docs
    slot_label: "Docs retrofit parallel #2 — PLAN-075〜086 frontmatter (P2 前半)"
  - role: docs
    slot_label: "Docs retrofit parallel #3 — PLAN-040〜074 frontmatter (P3 前半)"
  - role: docs
    slot_label: "Docs retrofit parallel #4 — PLAN-001〜039 frontmatter (P4)"
generates:
  - artifact_path: docs/adr/ADR-021-design-doc-web-search-guardrail-snapshot.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-022-todowrite-agent-slot-framework-snapshot.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-023-gate-fail-close-staged-adoption-snapshot.md
    artifact_type: adr_snapshot
  - artifact_path: docs/adr/ADR-024-continueonblock-active-guidance-loop-snapshot.md
    artifact_type: adr_snapshot
  - artifact_path: docs/plans/PLAN-001-through-090-frontmatter
    artifact_type: design_doc
  - artifact_path: docs/v2/CONCEPT.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L1-REQUIREMENTS.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L2-MASTER.md
    artifact_type: design_doc
  - artifact_path: docs/v2/V5-plan-outlines.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-091
    - PLAN-MM-001
    - PLAN-099-autonomous-runtime-framework-5layer
  blocks:
    - PLAN-097-abstraction-layer-escalation
related_adr:
  - ADR-021-design-doc-web-search-guardrail-snapshot
  - ADR-022-todowrite-agent-slot-framework-snapshot
  - ADR-023-gate-fail-close-staged-adoption-snapshot
  - ADR-024-continueonblock-active-guidance-loop-snapshot
related_plans:
  - PLAN-087-design-doc-web-search-guardrail
  - PLAN-088-todowrite-agent-slot-framework
  - PLAN-089-gate-fail-close-design-doc-web-search-audit
  - PLAN-090-posttooluse-continueonblock-refactor
  - PLAN-MM-001-v5-framework-master-plan
  - PLAN-091-v5-framework-core
related_docs:
  - docs/v2/CONCEPT.md
  - docs/v2/L1-REQUIREMENTS.md
  - docs/v2/L2-MASTER.md
  - docs/v2/V5-plan-outlines.md
  - CLAUDE.md §V5 framework 18 要素
  - helix/HELIX_CORE.md
---

# PLAN-100: 既存 PLAN-001〜090 retrofit + V2 全面見直し + ADR-021〜024 snapshot 後追い起票

> **kind**: retrofit (既存 doc を V5 framework 新規約に合わせる更新)
> **layer**: cross (PLAN-001〜090 全範囲 + V2 doc 全体に横断影響)
> **drive**: be (CLI / framework 実装中心)
> **本 PLAN の役割**: PLAN ⊃ ADR レイヤー併存の修正救済 (PLAN-087〜090 の L2 凍結 ADR snapshot 後追い起票) + PLAN-001〜090 frontmatter retrofit 計画 + V2 全面見直し計画。
> **重要制約**: 本 PLAN 内 §4 は PLAN-100A〜D に分割しない。§4.1〜§4.4 の内部構造として管理する。ADR-021〜024 は各独立 file で起票する。

---

## §0. 本 PLAN の位置付け

本 PLAN は **V5 framework Layer A (工程・ドキュメント運用ルール整備) の retrofit 担当**。PLAN-MM-001 §6 の依存グラフで「PLAN-100 ↔ ADR-021/022/023/024」として位置付けられており、以下の 3 責務を持つ:

1. **ADR snapshot 後追い起票** (§4): PLAN-087〜090 が L2 大局判断を含むにも関わらず ADR snapshot 不在だった問題を救済する (HELIX レイヤー併存違反の修正)。本 session で ADR-021〜024 を独立 file として起票する。
2. **PLAN-001〜090 frontmatter retrofit 計画** (§5): 既存 PLAN 全 90 件に V5 framework 語彙 (kind / layer / drive / dependencies / agent_slots / generates) を追加する計画を立てる。実施は別 session。
3. **V2 doc 全面見直し計画** (§6〜§7): CONCEPT / L1-REQUIREMENTS / L2-MASTER + V5-plan-outlines.md を V5 framework 18 要素と整合させる計画を立てる。実施は別 session。

### デグレ禁止 (本 PLAN 内 CRITICAL)

- 既存 PLAN-087/088/089/090 doc は **編集しない** (本 PLAN は ADR 別 file 起票のみ)
- 既存 V2 doc (CONCEPT/L1-REQUIREMENTS/L2-MASTER/V5-plan-outlines.md) は **編集しない** (計画化のみ)
- 既存 SKILL_MAP / HELIX_CORE / CLAUDE.md / AGENTS.md は **編集しない**
- 本 PLAN で「retrofit 計画」を立てるが、実 retrofit は別 session 実施

---

## §1. 目的

1. PLAN-087〜090 の L2 凍結 ADR snapshot を後追い起票し、PLAN ⊃ ADR レイヤー併存違反 (feedback_adr_before_plan_violation で確立) を修正する
2. PLAN-001〜090 全 90 件に V5 framework frontmatter (kind / layer / drive / dependencies / agent_slots / generates) を retrofit する計画を確立する
3. V2 doc (CONCEPT / L1-REQUIREMENTS / L2-MASTER) を V5 framework 18 要素と整合させる全面見直し計画を確立する
4. V5-plan-outlines.md の 17 要素 → 18 要素 drift を解消する計画を確立する
5. PLAN-091 で定義した frontmatter 語彙 (§5 語彙正本) を正本として、retrofit 基準を統一する

---

## §2. 背景

### 2.1 PLAN ⊃ ADR レイヤー併存違反の発覚

本 session (2026-05-19〜20) で以下の 4 PLAN が L2 大局判断を含むにも関わらず ADR snapshot なしで起票された問題が発覚した:

| PLAN | L2 大局判断の内容 | ADR 不在の理由 |
|---|---|---|
| PLAN-087 | 設計 doc 作成時に Web 検索 3 query 以上を必須化する新 framework 採用 | 当時「ADR 先 / PLAN 後」の誤認識で ADR 起票を PLAN の後と理解していた |
| PLAN-088 | TodoWrite × agent slot framework 採用 (prefix 機械化・PreToolUse fail-close) | 同上 |
| PLAN-089 | gate fail-close の advisory → fail-close 段階遷移採用 (helix-gate + v33 migration) | 同上 |
| PLAN-090 | Claude Code 2.1.139 continueOnBlock 仕様採用 + active guidance loop pattern 確立 | 同上 |

ユーザー指摘 2 件 (「ADR 先だよ」→ 訂正「PLAN ⊃ ADR レイヤー併存」) で正規 pattern が確立。正規 pattern は「PLAN = 1 トピックの implementation tree (L1〜L4 内包)、ADR = PLAN tree 内 L2 大局判断 snapshot (任意、必要時のみ)」。詳細: memory feedback_adr_before_plan_violation。

### 2.2 既存 PLAN frontmatter 不在問題

PLAN-001〜090 の frontmatter は V5 framework 確立前に作成されたため、kind / layer / drive / dependencies / agent_slots / generates が不在。PLAN-091 §5 で定義した語彙を全件に retrofit することで、PLAN-093 (drift 検出) / helix plan validate / plan_registry (PLAN-092) の機械化が機能するようになる。

### 2.3 V2 doc と V5 framework の drift

docs/v2/ 配下の V2 doc (CONCEPT.md / L1-REQUIREMENTS.md / L2-MASTER.md) は V5 framework (18 要素 + 3 層構造) 確立前の記述であり、以下の drift が存在する:

| doc | drift 内容 |
|---|---|
| CONCEPT.md | V5 framework 18 要素 + 3 層構造の記述なし |
| L1-REQUIREMENTS.md | V5 framework 関連の FR (FR-V5-01〜18) なし |
| L2-MASTER.md | §0 line 36 の PLAN↔ADR 範例が PLAN-084↔ADR-018/019 のまま (PLAN-MM-001 + PLAN-091〜099 + ADR-021〜032 を反映する必要あり) |
| V5-plan-outlines.md | 冒頭「17 要素」表記 (18 要素 = PLAN-099 追加後の正本) |

---

## §3. 業界 standard 参照 (Web 検索 3 query ベース、PLAN-087 ガードレール準拠)

本 PLAN 起票前に以下 3 query で業界 standard を調査した。

| Query | Source URL | 本 PLAN での引用箇所 |
|---|---|---|
| "retrofit refactor framework existing codebase decision record 2026" | https://martinfowler.com/articles/patterns-of-legacy-displacement/ | §5 gradual retrofit 方針 (PLAN-001 古い順から PLAN-090 新しい順へ gradual 適用) の業界整合 |
| "schema migration frontmatter YAML batch update tools 2026" | https://jekyllrb.com/docs/front-matter/ / https://pandoc.org/MANUAL.html#yaml-metadata-block | §5 frontmatter YAML batch update のツール参考 (Jekyll / Pandoc frontmatter 標準) |
| "legacy plan modernization architecture documentation best practices 2026" | https://aws.amazon.com/blogs/architecture/master-architecture-decision-records-adrs-best-practices-for-effective-decision-making/ | §4 ADR snapshot 後追い起票 (append-only ADR の後追い snapshot が業界標準 pattern) |
| 補足: "architecture decision records retroactive documentation" | https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions | ADR は retroactive (後追い) に起票しても有効 (Nygard ADR original pattern) |
| 補足: "yaml frontmatter batch migration python script" | https://github.com/JamieMagee/waypoint | §5 機械化 CLI (helix plan retrofit / helix plan draft 拡張、PLAN-091 §11 実装時確定) の参考 implementation |

**業界知見の要約**:
- Nygard ADR 原典は retroactive (後追い) 起票を明示的に許容。本 PLAN の ADR-021〜024 後追い起票は業界標準 pattern に準拠する
- YAML frontmatter の batch update は Jekyll / Pandoc / Waypoint 等で実績があり、Python スクリプトによる機械化が一般的
- Legacy system の gradual modernization は「古いものから順に」ではなく「最も価値が高いものから」が業界推奨 (Fowler §Strangler Fig)。PLAN retrofit では依存関係 graph 上流 (PLAN-MM-001 / PLAN-091) を先行し、下流 (PLAN-001 等) を後続とする

---

## §4. PLAN-087〜090 L2 凍結 ADR snapshot 後追い起票 (本 session で完遂)

PLAN-087〜090 の PLAN tree 内に L2 大局判断が含まれるにも関わらず ADR snapshot が不在だった問題を修正する。本 §4 は PLAN-100A〜D には分割しない。§4.1〜§4.4 の内部セクション構造として管理する。

**起票方針**: 各 ADR は独立 file (docs/adr/ADR-021〜024-*.md) として起票し、PLAN-087〜090 ↔ ADR-021〜024 の双方向 reference を確立する。PLAN-087〜090 本体への ## L2 凍結 (ADR snapshot) section 追加は別 session (PLAN-100 Phase 2)。

---

### §4.1 ADR-021: PLAN-087 Web 検索ガードレール採用 (L2 凍結 snapshot)

**Context**:
- PLAN-085/086/ADR-020 で SaaS 過剰適用問題が発覚 (local CLI tool に SaaS 本番運用テンプレートを適用)
- 第 1 次 scope down は Web 検索なしの「思いつき書き」で再度 scope 問題
- ユーザー指摘「設計 doc 作るとき Web 検索を挟め、工程内にガードレール組み込め」でガードレール必要性を認識

**Decision**:
- 設計 doc (ADR / PLAN / spec) 新規起票・大幅 scope 変更時に WebSearch / WebFetch / pmo-tech-docs / pmo-tech-fork で 3 query 以上必須化
- PreToolUse hook (pretooluse-design-doc-web-search-guard.sh) で fail-close 機械強制
- 設計 doc に「業界 standard 参照」section を必須化 (Sources URL を含む)

**独立 DoD**:
- docs/adr/ADR-021-design-doc-web-search-guardrail-snapshot.md が存在する
- PLAN-087 frontmatter に `related_adr: [ADR-021-design-doc-web-search-guardrail-snapshot]` が追加されている (別 session)
- ADR-021 本文に `Related: PLAN-087-design-doc-web-search-guardrail` が記載されている

---

### §4.2 ADR-022: PLAN-088 TodoWrite × agent slot framework 採用 (L2 凍結 snapshot)

**Context**:
- 並列実行時の TodoWrite content が agent 間で可視化されず、in_progress 重複・上限超過・依存不在の待ち行列が発生していた
- `.claude/hooks/pretooluse-agent-guard.sh` は PMO/PdM 12 種の fail-close を持つが TodoWrite には未適用
- agent_type の可観測性ゼロで並列 8 の達成状況が追跡不能

**Decision**:
- TodoWrite content に `[agent_type]` prefix を機械的に必須化
- PreToolUse hook (pretooluse-todowrite-prefix-check.sh) で prefix 逸脱を早期検知・fail-close 化
- helix.db v34 で `todo_entries` table を新設、agent_type を DB 集計可能に

**独立 DoD**:
- docs/adr/ADR-022-todowrite-agent-slot-framework-snapshot.md が存在する
- PLAN-088 frontmatter に `related_adr: [ADR-022-todowrite-agent-slot-framework-snapshot]` が追加されている (別 session)
- ADR-022 本文に `Related: PLAN-088-todowrite-agent-slot-framework` が記載されている

---

### §4.3 ADR-023: PLAN-089 gate fail-close 段階遷移採用 (L2 凍結 snapshot)

**Context**:
- PLAN-087 Phase 3 で helix-gate に run_gate_design_doc_web_search_audit (G2/G3 advisory) を実装したが、advisory は warn のみで gate 通過を block しない
- advisory と fail-close の一括切替は blast radius が大きく、advisory 計測期間なしの即時 fail-close は危険
- helix.db v33 migration 実装と schema_version drift 修正も同時完遂

**Decision**:
- advisory → fail-close を段階的に導入 (Phase 1 計測 → Phase 2 fail-close → Phase 3 retrofit → Phase 4 carry)
- tl-advisor 相談 (bi9qaatd6) で段階遷移の妥当性を確認
- bypass env を settings.json に永続化しない (恒久例外化リスク防止)

**独立 DoD**:
- docs/adr/ADR-023-gate-fail-close-staged-adoption-snapshot.md が存在する
- PLAN-089 frontmatter に `related_adr: [ADR-023-gate-fail-close-staged-adoption-snapshot]` が追加されている (別 session)
- ADR-023 本文に `Related: PLAN-089-gate-fail-close-design-doc-web-search-audit` が記載されている

---

### §4.4 ADR-024: PLAN-090 continueOnBlock + active guidance loop 採用 (L2 凍結 snapshot)

**Context**:
- Claude Code 2.1.139 で PostToolUse に continueOnBlock が追加された外部仕様採用判断
- 従来の PostToolUse 二重防御 (stderr + exit 1 warn-only) は reject reason を Claude に返せず、同一ターン内での自動リトライ不可
- Issue #24327 での exit 2 後 Claude 待機問題はモデル挙動の問題で hook 解決不可

**Decision**:
- PostToolUse hook で `decision: "block"` + continueOnBlock を採用し、reject reason を Claude が同一ターン内で受け取り再実行できる「active guidance loop」を実現
- 二重防御より新仕様準拠 (continueOnBlock) を優先
- Codex CLI 内 Write は Claude Code hook を bypass (別 process なため)、helix codex 委譲時は hook 対象外として設計

**独立 DoD**:
- docs/adr/ADR-024-continueonblock-active-guidance-loop-snapshot.md が存在する
- PLAN-090 frontmatter に `related_adr: [ADR-024-continueonblock-active-guidance-loop-snapshot]` が追加されている (別 session)
- ADR-024 本文に `Related: PLAN-090-posttooluse-continueonblock-refactor` が記載されている

---

## §5. PLAN-001〜090 frontmatter retrofit 計画 (別 session 実施)

### 5.1 retrofit 対象と優先順序

全 90 PLAN を V5 framework frontmatter (kind / layer / drive / dependencies / agent_slots / generates) で更新する。業界 standard (Fowler §Strangler Fig) に倣い、依存関係 graph の上流から順に実施する:

| 優先 | 対象 | 理由 | 担当 agent |
|---|---|---|---|
| 最優先 (P1) | PLAN-087〜090 (4 件) | ADR snapshot 後追い起票の双方向 trace 確立 (別 session で ## L2 凍結 section 追加) | pmo-sonnet |
| 高優先 (P2) | PLAN-075〜086 (12 件) | V-model / subagent / Sprint 標準等の直近実装 PLAN、依存 graph 上流 | docs × 2 並列 |
| 中優先 (P3) | PLAN-040〜074 (35 件) | 比較的新しい PLAN 群 | docs × 4 並列 |
| 低優先 (P4) | PLAN-001〜039 (39 件) | 古い PLAN 群、V5 framework 適用前から存在 | docs × 4 並列 |

### 5.2 retrofit ルール (PLAN-091 §5 語彙正本準拠)

各 PLAN に追加する frontmatter フィールド:

```yaml
# 追加フィールド (PLAN-091 §5 準拠)
kind: <11 種から選択>
layer: <15 種から選択 or cross>
drive: <9 種から選択>
agent_slots:
  - <担当した agent>
generates:
  - artifact_path: <生成物パス>
    artifact_type: <種別>
dependencies:
  parent: <親 PLAN または null>
  requires: []
  blocks: []
```

### 5.3 機械化 CLI 設計 (PLAN-091 実装後に追加)

> **注**: `helix plan retrofit` は PLAN-091 §11 CLI 拡張案の既存 subcommand 一覧 (draft / review / finalize / reset / list / status / lint / import / deps / generates) に未定義。PLAN-091 実装 session にて `helix plan draft` の拡張 subcommand として追加するか、`helix plan retrofit` を新規 subcommand として衝突確認の上追加する判断が必要。以下はその設計案:

```bash
# PLAN frontmatter retrofit (PLAN-091 実装後、CLI 命名は PLAN-091 §11 実装時に確定)
helix plan retrofit --plan-id PLAN-075 --kind impl --layer L4 --drive be \
  --agent-slots "docs,pmo-sonnet" --auto-generates

# 全件 dry-run (欠損フィールド一覧)
helix plan retrofit --all --dry-run --check-missing

# batch retrofit (4 並列)
helix plan retrofit --range 040-074 --parallel 4 --kind-auto
```

### 5.4 retrofit 完了確認

```bash
# 全 PLAN の frontmatter 整合確認
helix plan validate --all --strict
helix doctor check_plan_frontmatter

# ADR snapshot 後追い必要 PLAN 一覧
helix doctor check_plan_adr_snapshot --all
```

---

## §6. V2 doc 全面見直し計画 (別 session 実施)

### 6.1 CONCEPT.md 更新計画

V5 framework 18 要素 + 3 層構造を §V2-V5 framework 統合 section として追加する:

- 追加場所: CONCEPT.md 末尾 (既存 §1〜§末 を保持して追記)
- 追加内容:
  - §N: V5 framework 18 要素 マッピング表 (V5 要素 #1〜#18 と子 PLAN-091〜099)
  - §N+1: V5 framework 3 層構造 (Layer A→B→C 着手順序)
  - §N+2: PLAN ⊃ ADR レイヤー併存の正規 pattern (L2-MASTER §0 line 36 の更新先)
- 担当: pmo-sonnet (draft 起草) + Opus (finalize)

#### Sprint 0 補完 (2026-05-21)

- **status 遷移**: `status: draft` のままとなっている CONCEPT.md に `review` 遷移フローを追記し、承認日記入欄を設ける (Phase 4 実施時に同時処理)
- **§9 V1 資産表更新**: 旧 PLAN-065/063 参照を V5 PLAN-091〜099 に置換する (V5 framework 子 PLAN 全 9 件を資産表に反映)
- **AC-12 テスト baseline 更新**: `pytest 1138+` → `1820+` / `bats 433+` → `509+` に修正し現実値と整合させる (origin/main `9d546dc` 時点実績値)

### 6.2 L1-REQUIREMENTS.md 更新計画

V5 framework 関連の FR を追加する:

```
FR-V5-01: PLAN frontmatter は kind / layer / drive / dependencies / agent_slots / generates を含むこと
FR-V5-02: PLAN tree 内に L2 大局判断がある場合、対応する ADR snapshot を同時起票すること (PLAN ⊃ ADR レイヤー併存)
FR-V5-03: kind は 11 種 (PLAN-091 §5.1) のいずれかであること
FR-V5-04: layer は 15 種 (PLAN-091 §5.2) または cross であること
FR-V5-05: drive は 9 種 (PLAN-091 §5.3) のいずれかであること
FR-V5-06: 設計 doc 新規起票時に WebSearch 3 query 以上を実施すること (PLAN-087)
FR-V5-07: TodoWrite content に [agent_type] prefix を付与すること (PLAN-088)
FR-V5-08: helix-gate G2/G3 で Web 検索 audit を実施すること (PLAN-089)
FR-V5-09: PostToolUse hook は continueOnBlock を使用すること (PLAN-090)
FR-V5-10〜18: (PLAN-092〜099 実装後に追加)
```

#### Sprint 0 補完 (2026-05-21)

- **§11 FR 件数訂正**: 74 → 80 に修正 (§3.4 GR08〜GR13 の 6 件追加分が未カウント)。G1 通過チェックリストの GR 行を `GR01-13 (13)` に修正する。
- **NFR-03 stale 更新**: `v30 → v31 migration` 記述を `v30 → v35 (current)` 系列に更新し、helix.db schema_version の現実値 (origin/main `9d546dc` 時点) と整合させる。
- **§5 AC-18〜24 追加**: V5 framework 実装を受入条件として追加する — AC-18 (PLAN-091 plan_validator PASS) / AC-19 (PLAN-092 PostToolUse auto-register 5s 以内) / AC-20 (PLAN-093 P0 guardian block) / AC-21 (PLAN-099 自動走行 heartbeat carry 0 判定) / AC-22 (recovery plan kind 起票機構) / AC-23 (Curator P1/P2 escalation 閾値) / AC-24 (UserPromptSubmit hook dogfooding 稼働)。
- **§6 スコープ更新**: Phase K として「V5 framework 統合 (PLAN-091〜099)」を追記し、PLAN-100 retrofit との接続 (Phase K 完遂後に PLAN-100 Phase 3 着手可能) を明示する。
- **FR-V5-10〜18 placeholder 確定方針**: Phase 4 実施前に PLAN-092〜099 の generates artifact_path リストと照合し、各 FR placeholder を確定する手順を §6.2 末尾に注記として追記する。

### 6.3 L2-MASTER.md 更新計画

§0 line 36 の PLAN↔ADR 範例を更新する:

- 現状: 「PLAN-084 で L1 確定、ADR-018/019 で L2 凍結」
- 更新後: 「PLAN-MM-001 で V5 全体設計確定、PLAN-091〜099 + ADR-025〜032 で実装・L2 凍結 (後追い例: PLAN-087〜090 ↔ ADR-021〜024)」

また §12 既知矛盾 M-01〜M-04 に V5 framework 関連の drift 解消状況を追記する。

#### Sprint 0 補完 (2026-05-21)

- **§12 M-09〜M-12 具体内容追記**:
  - M-09: PRAGMA user_version → schema_version table 置換 (PLAN-085 系、commit `877845a` で resolved)
  - M-10: PLAN 種別 11 種 / agent_slots ROLE_MAP 30 enum が L2-MASTER §3.2 drive variant 表に未反映 (open。解消先 = PLAN-091 §5 語彙正本 + PLAN-100 §5 retrofit 計画による機械的適用)
  - M-11: V5-plan-outlines.md 17 要素表記 drift (PLAN-099 追加後は 18 要素が正本、open)
  - M-12: 既存 60 incomplete PLAN の V-model 4 artifact 不整備 (P2、PLAN-100 §5 で解消計画あり、status=planned)
- **§0 / §1 両方への Layer A→B→C 追記**: §0 line 36 のみでなく §1 (アーキテクチャ全景) にも Layer A→B→C 着手順序への reference を追記する (外部参照: CLAUDE.md §V5 framework 3 層構造)。
- **附録 A 連動記載**: L1-REQUIREMENTS の FR-V5-01〜09 追加と L2-MASTER 附録 A FR/AC 対応表更新を同一 Phase 4 session 内で同時実施する手順を §6.3 末尾に明記する。
- **§12 判断保留更新**: `sync cycle における 3 origin_mode 統合管理の最終方針` は PLAN-095 (PoC=Scrum×Reverse matrix) で解消見込み。§12 保留欄に「→ PLAN-095 Sprint .3 完遂で close 予定」の注記を追加する。

---

## §7. V5-plan-outlines.md drift 解消計画 (別 session 実施)

### 7.1 現状 drift

| 箇所 | 現状 | 正本 (CLAUDE.md) | drift |
|---|---|---|---|
| 冒頭「17 要素」表記 | 17 要素 | 18 要素 (PLAN-099 追加) | ✅ drift あり |
| PLAN-099 outline | 本文には記載あり | 同じ内容 | ❌ drift なし |
| 9 PLAN 起票案 | PLAN-091〜098 8 件 | PLAN-091〜099 9 件 | ✅ drift あり |
| ADR 8 件起票案 | ADR-025〜031 7 件 | ADR-025〜032 8 件 | ✅ drift あり |

### 7.2 更新内容

1. 冒頭「17 要素」→「18 要素」に変更
2. 「8 PLAN 起票案」→「9 PLAN 起票案 (PLAN-099 を含む)」に更新
3. 「7 ADR 起票案」→「8 ADR 起票案 (ADR-032 を含む)」に更新
4. 「正本は CLAUDE.md §V5 framework 18 要素」注記を冒頭に追加

---

## §8. 段階導入 4 Phase

| Phase | 内容 | 実施 session | 担当 | 完了条件 |
|---|---|---|---|---|
| **P1** | 本 task: ADR-021〜024 独立 file 起票 (本 session 完遂) | 本 session | pmo-sonnet | ADR-021〜024 全 4 file 存在 + PLAN-100 ↔ ADR 双方向 reference 確立 |
| **P2** | 別 session: PLAN-087〜090 への `## L2 凍結 (ADR snapshot)` section 追加 + related_adr frontmatter 追加 | 別 session | pmo-sonnet | PLAN-087〜090 ↔ ADR-021〜024 双方向 trace 完全確立 |
| **P3** | 別 session: PLAN-001〜090 全件 frontmatter retrofit (§5 計画実施) | 別 session | docs × 4 並列 | `helix plan validate --all --strict` が全件 PASS |
| **P4** | 別 session: V2 全面見直し (§6〜§7 計画実施) | 別 session | pmo-sonnet + Opus | L2-MASTER §0 更新 + CONCEPT V5 section 追加 + V5-plan-outlines.md 18 要素版 |

---

## §9. デグレ禁止項目 (本 task 内絶対遵守)

本 PLAN 起票 + ADR-021〜024 起票は **新規 doc 作成のみ**。以下は一切編集しない:

1. 既存 PLAN-087/088/089/090 本文 (ADR 別 file 起票のみ、PLAN への section 追加は Phase 2)
2. 既存 V2 doc (CONCEPT/L1-REQUIREMENTS/L2-MASTER/V5-plan-outlines.md)
3. 既存 SKILL_MAP / HELIX_CORE / CLAUDE.md / AGENTS.md
4. 既存 cli/ / .claude/hooks/ / cli/lib/ / cli/templates/
5. 既存 docs/adr/ADR-001〜020 / ADR-025 (既存 ADR は編集禁止、新規追加のみ)

---

## §10. DoD (Definition of Done)

### Phase 1 (本 session) DoD

1. docs/adr/ADR-021-design-doc-web-search-guardrail-snapshot.md が存在する
2. docs/adr/ADR-022-todowrite-agent-slot-framework-snapshot.md が存在する
3. docs/adr/ADR-023-gate-fail-close-staged-adoption-snapshot.md が存在する
4. docs/adr/ADR-024-continueonblock-active-guidance-loop-snapshot.md が存在する
5. 各 ADR に Related: PLAN-08N (対応 PLAN) が記載されている
6. 本 PLAN-100 frontmatter に generates / related_adr / dependencies が完備されている
7. デグレ禁止 (§9) を侵していないことを git diff で確認

### Phase 2〜4 (別 session) DoD

8. PLAN-087〜090 に related_adr frontmatter + ## L2 凍結 section が追加されている
9. `helix plan validate --all --strict` が全 90 PLAN で PASS
10. L2-MASTER §0 line 36 + CONCEPT.md V5 section + V5-plan-outlines.md 18 要素版が完成

---

## §11. V-model 4 artifact trace

本 PLAN は **設計 artifact (①)** として機能する。

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-100-existing-retrofit-v2-revision.md |
| ② 実装コード | Phase 3〜4 以降 (別 session) | cli/helix-plan retrofit / PLAN-001〜090 frontmatter / V2 docs |
| ③ テスト設計 | 未起票 (別 session) | docs/v2/L4-test-design/PLAN-100-retrofit-test-design.md (予定) |
| ④ テストコード | 未着手 (別 session) | cli/lib/tests/test_plan_retrofit.py (予定) |

**双方向 reference**:
- 本 PLAN → ADR-021〜024: frontmatter `related_adr` + §4.1〜§4.4
- ADR-021〜024 → 本 PLAN: 各 ADR の `Related` section に `PLAN-100 (retrofit master)` を記載
- 本 PLAN → PLAN-087〜090: frontmatter `related_plans`
- PLAN-087〜090 → 本 PLAN + ADR-021〜024: Phase 2 (別 session) で双方向 trace 確立

---

## §12. 関連 PLAN / ADR / memory

### 前段 PLAN (requires)
- PLAN-091: frontmatter 語彙正本 (§5 retrofitルール の根拠)
- PLAN-MM-001: 親設計、PLAN-100 の起票元 §6 PLAN-100 参照

### 後段 PLAN (blocks)
- PLAN-097: 抽象化層設計は V2 全面見直し (§6) 完了後に整合確認が必要

### related_adr (本 PLAN が起票する ADR)
- ADR-021: PLAN-087 retrofit snapshot
- ADR-022: PLAN-088 retrofit snapshot
- ADR-023: PLAN-089 retrofit snapshot
- ADR-024: PLAN-090 retrofit snapshot

### related_memories
- feedback_adr_before_plan_violation: PLAN ⊃ ADR レイヤー併存違反発覚 (本 PLAN の直接動機)
- feedback_design_doc_web_search_required: §3 WebSearch 義務 (ADR-021 の根拠)
- project_2026_05_20_v5_framework_evolution_recovery: V5 確立過程の全記録

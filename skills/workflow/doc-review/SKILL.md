---
name: doc-review
description: HELIX-workflows ドキュメント品質レビュー専用 skill。4 視点 (Correctness / Completeness / Consistency / Clarity) + 業界標準整合 (Diátaxis / arc42 / ISO/IEC/IEEE 26515 / DDD SSoT) + HELIX 固有 V-model 量閉じ性 / implementation_status 列必須を統合検査。doc-reviewer role (gpt-5.5 high) で召喚、tl-advisor (技術判断) / code-reviewer (5 軸) / pmo-sonnet (汎用) と責務分離。
metadata:
  helix_layer: cross-cutting
  triggers:
    - 大規模 doc 改定 (L0/L1/L3 製本 doc 等、~500 行+)
    - V-model 4 artifact pair freeze 前 (G0.5 / G1 / G3 / G7 ゲート evidence)
    - implementation_status 列の verify-before-act 監査
    - 業界標準整合 audit (arc42 / Diátaxis / ISO 26515)
---

## §1 目的

HELIX-workflows の **ドキュメント品質 review 専用** skill。設計判断 adversarial (tl-advisor) や 5 軸 code review (code-reviewer) や汎用構造化 read-only (pmo-sonnet) と責務分離し、**doc 品質 + 業界標準整合 + HELIX 固有 V-model 量閉じ性** に特化する。

## §2 4 視点 review (HELIX standard)

| 視点 | 内容 | 検出 pattern |
|---|---|---|
| **Correctness** (事実整合) | doc 内主張が実体と一致するか。`implementation_status` 列 (installed / partial / L4-carry / not-implemented) で verify-before-act 必須。机上宣言禁止 | claim ↔ 実在資産 (CLI / file / schema field / table / view / config) の diff |
| **Completeness** (章充足) | doc-system-architect 必須項目 6 件 (背景 / 課題 / scope / ROI / 成功条件 / リスク) + V-model 4 artifact (設計 / 実装 / テスト設計 / テストコード) の存在 | arc42 12 章 / Diátaxis 4 mode (Tutorial / How-to / Reference / Explanation) の章構成 |
| **Consistency** (用語・構造整合) | ユビキタス言語 SSoT (L0 §12 Glossary) と用語ゆれなし。anti-corruption layer 経由で他 BC 固有用語を引用 | 用語表記ゆれ / 同義語 / 略称差異 / Glossary 未定義用語の grep |
| **Clarity** (可読性) | Why > What > How 順序、初見読者が脱落せず読了可能、図表 / 例 / cross-reference の適切性 | section 構造 / 1 文字数 / 略語率 / 図 vs 文章比率 |

## §3 業界標準整合 (doc-system-architect 子 skill として実体化)

| 標準 | 適用 |
|---|---|
| **Diátaxis** (Daniele Procida 2017) | doc 種別判定 (Tutorial / How-to / Reference / Explanation) と章構成整合 |
| **arc42 v8** | アーキテクチャ doc の 12 章構造整合 (Introduction / Constraints / Context / Solution Strategy / Building Blocks / Runtime / Deployment / Crosscutting / Quality / Risks / Glossary) |
| **ISO/IEC/IEEE 26515:2018** | Systems and software engineering — Developing user documentation in an agile environment、agile doc 品質基準 |
| **DDD Ubiquitous Language** (Eric Evans 2003) | SSoT 単一化、Bounded Context 別用語 + anti-corruption layer |
| **ISO/IEC/IEEE 26513:2017** | Systems and software engineering — Requirements for testers and reviewers of information for users |
| **Keep a Changelog v1.1.0** | CHANGELOG / decision_log の構造整合 |

## §4 HELIX 固有 V-model 量閉じ性 (本 skill 中核、他標準にない HELIX オリジナル軸)

| 観点 | 検査内容 |
|---|---|
| **balance_ratio ≥ 1.0** | pair_volume_balance (Chargaff 比喩、test_count / design_count) を各 V-model pair で確認 (L1↔L14 / L2↔L10 / L3↔L12 / L4↔L9 / L5↔L8 / L6↔L7) |
| **pair freeze frontmatter** | `pairs_test_design` / `pairs_with` / `next_pair_freeze` 必須充足 |
| **implementation_status 列** | 設計 doc 内の「対応 CLI / file path / schema field / table / view / config」主張に対し `installed / partial / L4-carry / not-implemented` 列必須 (BR-RULE-09 整合) |
| **V-model 4 artifact 双方向 trace** | ① 設計 ↔ ② 実装 ↔ ③ テスト設計 ↔ ④ テストコード の双方向 reference 完備 |
| **migration pipeline 整合** | V1→V2 / 旧→新 enum の Strangler Fig 段階置換進捗を doc 内で明示 (BR-RULE-10 整合) |

## §5 doc 種別別 checklist

| doc 種別 | 重点視点 | 必須 section |
|---|---|---|
| **L0 企画書** | Why > What 整合、L1 バトン充足、AC 機械判定可能 | 背景・目的 / 解決する課題 / scope / ROI / 成功条件 / リスク / Glossary / 業界標準整合 / BC / decision_log |
| **L1 要求 doc** | BR / FR / TR / NFR 件数明示、pair freeze (L14) 充足、業務 entity ↔ L0 Glossary 1:1 対応 | 目的・背景 / 対象業務一覧 / 業務フロー / ステークホルダー / 現状課題 / scope / pair 対応 / 関連 doc / carry / entity 列挙 |
| **L3 要件 doc** | BR-RULE 業務ルール / FR-* CLI 契約 / NFR IPA グレード値、L12 pair AC 1:1 対応 | 業務フロー / 業務ルール / scope / L1→L3 trace / 関連 / carry / L0 §8 closure |
| **L4 基本設計 doc** | arc42 §5 Building Block View / ADR snapshot / L9 pair (総合テスト) | アーキテクチャ / ADR / quality 観点 / risks |
| **設計 doc (D-API / D-DB / D-CONTRACT)** | implementation_status 列必須 / api-contract skill 整合 / 双方向 trace | endpoint / schema / 副作用 / 制約 / 実装ファイル ↔ コード reference |
| **ADR (Nygard format)** | Context / Decision / Status / Consequences の 4 section 完備、accept date 明示 | accept timestamp / superseded by / linked PLAN |
| **runbook** | Google SRE 標準、手順 / rollback / on-call / 監視 reference | 手順 step / 異常時 action / connect 先 |
| **postmortem** | Google SRE 5 章 (TL;DR / Impact / Detection / RCA / Action Items) | timeline / contributing factors / action items に owner |

## §6 召喚タイミング

### 自動発火 (PM が自発的に起動)

- 大規模 doc 改定 (~500 行+) の commit 前 (G0.5 / G1 / G3 / G7 evidence)
- V-model 4 artifact pair freeze 前
- implementation_status 列の verify-before-act 監査時 (BR-RULE-09)
- migration pipeline 凍結前 (BR-RULE-10)

### 任意発火 (PM 判断)

- 既存 doc の用語 SSoT 整合 audit
- 業界標準整合 audit (新 doc 種別追加時)
- L0 §12 Glossary update 時 (用語追加 / rename)

### スキップ条件

- 軽微な typo 修正 (≤ 5 行)
- code 中心 commit (doc 修正なし)
- reference doc (kind=reference / is_reference: true) の場合

### 既存 review 体制との責務分離

| Skill / Role | 担当 |
|---|---|
| **doc-review (本 skill、doc-reviewer role gpt-5.5 high)** | **doc 品質 4 視点 + 業界標準整合 + V-model 量閉じ性** |
| common/code-review (code-reviewer agent) | 5 軸 code review (Correctness / Readability / Architecture / Security / Performance) |
| workflow/adversarial-review | G2/G4/G6 前の悪魔の代弁者 (設計判断 adversarial) |
| tl-advisor (Codex gpt-5.5) | TL 級技術難判断 (契約 / 設計 / リスク / テスト戦略) |
| pm-advisor (Claude Opus) | PM 級大局判断 (スコープ / 優先度 / 委譲先) |
| pmo-sonnet | 汎用構造化 read-only / 軽実装判断支援 |
| workflow/review-stage-routing | 6 段階 × ロール 分業境界 (本 skill とは分業軸が違う) |

## §7 出力フォーマット (本 skill 召喚時の期待 response)

```
判定: approve / conditional_approve / blocked
- P0: gate stop、即修正必須 (構造的欠陥 / 事実誤認 / SSoT 違反)
- P1: gate stop OR carry、PM 承認必要 (重要だが回避可能)
- P2: 次工程開始まで or deferred-finding carry (軽微)
- P3: 任意 carry (好み)

各指摘ごとに:
1. 観点 (Correctness / Completeness / Consistency / Clarity / 業界標準 / V-model)
2. 該当 file:line
3. 現状記述
4. 修正案 (1-2 行)
5. 判定根拠

最終 ratification:
- approve: P0 = 0、P1 ≤ 2
- conditional_approve: P0 = 0、P1 ≤ 5 (修正必須項目を明示)
- blocked: P0 ≥ 1 または P1 ≥ 6 (再起草)
```

## §8 機械判定 carry (L4 で実装、本 skill では仕様宣言)

- `helix doctor check_doc_quality` (新設): 本 skill の 4 視点 + V-model 量閉じ性を機械判定、failed doc を warn
- `helix doctor check_glossary_coverage` (BR-RULE-09 由来): implementation_status 列充足
- `helix doctor check_doc_industry_standard` (新設): arc42 / Diátaxis / ISO 26515 整合
- `helix doctor check_bc_anti_corruption` (BC anti-corruption): 用語 SSoT 違反検出
- `helix doctor check_doc_review_coverage` (BR-11 由来): 大規模 doc 改定で doc-reviewer 召喚 evidence audit

## §9 関連

- 親 skill: `workflow/doc-system-architect` (doc 体系設計、本 skill は review 専用子 skill)
- 隣接 skill:
  - `common/code-review` (code 5 軸 review)
  - `workflow/adversarial-review` (G ゲート adversarial)
  - `workflow/review-stage-routing` (6 段階 × ロール分業)
  - `workflow/design-doc` (D-API / D-DB / D-CONTRACT 作成)
  - `writing/explain` (技術文書品質 EEAT)
- 上位要件: L1 BR-11 doc-review continuous (本 skill の業務要求側)
- 業界標準: ISO/IEC/IEEE 26515:2018 / ISO/IEC/IEEE 26513:2017 / Diátaxis / arc42 v8 / DDD (Eric Evans 2003)
- メモリ参照:
  - [[feedback_memory_verify_before_act]] (Correctness 視点の根拠)
  - [[feedback_two_round_audit_for_design_docs]] (二重 audit pattern、本 skill 適用パターン)
  - [[feedback_doc_system_architect_retrofit_pattern]] (doc-system-architect retrofit、本 skill の親 pattern)
  - [[feedback_helix_fill_holes_principle]] (機械判定化原則、§8 carry の根拠)

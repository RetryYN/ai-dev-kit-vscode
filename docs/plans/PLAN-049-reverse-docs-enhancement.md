---
plan_id: PLAN-049
title: 'PLAN-049（Reverse HELIX ドキュメント強化 - 5 axis 集約）'
status: completed
completed: 2026-05-10
created: 2026-05-10
finalized: 2026-05-10
author: 'PM (Opus)'
priority: medium
size: M
phases_affected: skills/workflow/reverse-* / docs/commands/reverse.md / SKILL_MAP.md
parent_plan: PLAN-048
acceptance:
  type_specific_notes_section_present:
    verification_commands:
      command: "for f in r0 r2 r3 r4 rgc; do grep -cE '^## type 別 operational notes' skills/workflow/reverse-$f/SKILL.md; done | awk '$1>=1' | wc -l"
      expected: "5 (R0/R2/R3/R4/RGC 全 SKILL に section header)"
  type_specific_notes_5types_covered:
    verification_commands:
      command: "for f in r0 r2 r3 r4 rgc; do for t in code design upgrade normalization fullback; do grep -c \"^| $t\\b\\| $t :\\|^- $t\" skills/workflow/reverse-$f/SKILL.md; done; done | awk '$1>=1' | wc -l"
      expected: "≥ 25 (5 SKILL × 5 type の table 行)"
  r1_extraction_tools_section:
    verification_commands:
      command: "grep -cE '^## 機械抽出ツールチェーン|^### 選択基準|decision tree' skills/workflow/reverse-r1/SKILL.md"
      expected: "≥ 2 (新規 section header + decision tree)"
  r1_extraction_specific_tools:
    verification_commands:
      command: "grep -cE 'OpenAPI generator|INFORMATION_SCHEMA|tsc --emitDeclarationOnly|cargo expand|swagger' skills/workflow/reverse-r1/SKILL.md"
      expected: "≥ 4 (具体ツール名 4 種以上)"
  r4_routing_table_separated:
    verification_commands:
      command: "grep -cE '^## routing 判定基準|primary_routing|post_forward_action' skills/workflow/reverse-r4/SKILL.md"
      expected: "≥ 3 (新規 section + 列名 2 個)"
  r4_routing_primary_l1_l4:
    verification_commands:
      command: "awk -F'|' '/^\\| (critical|high|medium|low)/{gsub(/ /,\"\",$4); print $4}' skills/workflow/reverse-r4/SKILL.md | grep -cE '^L[1-4]$'"
      expected: "≥ 4 (table の primary_routing 列に L1-L4 値が ≥ 4 行存在、列位置ベース検証)"
  r1_type_notes_table:
    verification_commands:
      command: "for t in code design upgrade normalization fullback; do grep -cE \"^\\| $t \\|\" skills/workflow/reverse-r1/SKILL.md; done | awk '$1>=1' | wc -l"
      expected: "5 (reverse-r1 の type 別 table に 5 type 全行が存在)"
  helix_code_integration:
    verification_commands:
      command: "grep -lE '^## helix code 連携|helix code (find|stats|build)' skills/workflow/reverse-r0/SKILL.md skills/workflow/reverse-r1/SKILL.md | wc -l"
      expected: "= 2 (R0/R1 両方に helix code 連携 section)"
  worked_example_present:
    verification_commands:
      command: "grep -cE '^## Worked Example|^### シナリオ' docs/commands/reverse.md"
      expected: "≥ 1 (Reverse → Forward handoff worked example の section)"
  tests_all_pass:
    verification_commands:
      command: "cli/helix test"
      expected: "exit 0 / 0 failed"
  branch_minimal_footprint:
    verification_commands:
      command: "git branch --list 'improvements/plan-049*' | wc -l"
      expected: "0"
---

# PLAN-049: Reverse HELIX ドキュメント強化 (5 axis 集約)

## §1 背景

PLAN-008 (multi-type 対応) と PLAN-044 (Phase Integrity Audit) で Reverse の骨格は整ったが、
運用観点で以下のギャップが残存:

1. **type 別 operational guidance が薄い**: reverse-analysis Router に type matrix はあるが、
   各 reverse-r* SKILL は code type 主体で、design/upgrade/normalization/fullback での違いが
   明示されていない (R0/R1 で何が変わるか、ゲート条件のスキップ判定など)。
2. **R1 機械抽出ツールが抽象的**: OpenAPI 生成 / DB introspection / 型抽出の選択基準が
   書かれておらず、利用者が現場でツールチェーン選択に迷う。
3. **R4 routing 基準の判断軸が不足**: gap severity と routing target (L1-L4) のマッピングが
   個別判断に委ねられ、gap_register 作成時の再現性が低い。
4. **helix code (PLAN-011/012/013) との連携不在**: R0 evidence_map / R1 observed_contracts に
   `helix code find` / `helix code stats` を活用する記述がなく、機械抽出 + 人手検証の
   併用パターンが利用者に伝わらない。
5. **worked example 不在**: docs/commands/reverse.md は CLI レファレンスに留まり、
   Reverse → Forward handoff の完走シナリオがない (R4 結果を Forward L1-L4 にどう投入するか)。

これら 5 axis を集約 PLAN として 1 サイクルで解消する。

## §2 解消対象 (5 axis)

### Axis 1: type 別 operational notes 追加 (W-1)

各 reverse-r* SKILL に「## type 別 operational notes」セクションを追加。
**統一 table 形式で line budget を制約**:

各 SKILL の section は以下の 5 行 table のみで構成:

```markdown
## type 別 operational notes

| type | phase-specific action | skip / gate note |
|---|---|---|
| code | (1 行) | (1 行) |
| design | (1 行) | (1 行) |
| upgrade | (1 行) | (1 行) |
| normalization | (1 行) | (1 行) |
| fullback | (1 行) | (1 行) |
```

Section header + table = **section 全体で 10 行以内** (header 2 + 空行 1 + table header 2 + 5 type × 1 = 10 行)。

対象 SKILL (5 つ、reverse-r1 は **W-2 で吸収**):
- **reverse-r0/SKILL.md**: phase-specific action = R0 evidence 収集対象 (例: design = figma/sketch、upgrade = version diff)
- **reverse-r2/SKILL.md**: phase-specific action = As-Is 捉え方 (design = DAG / upgrade = diff / normalization = drift / fullback = alignment)
- **reverse-r3/SKILL.md**: phase-specific action = PO 検証対象 (intent / design / version / document)
- **reverse-r4/SKILL.md**: phase-specific action = primary routing target (W-3 と整合)
- **reverse-rgc/SKILL.md**: phase-specific action = closure 判定基準 (upgrade は RGC skip と注記)

**reverse-r1 は W-2 内で type 別 + ツール記述を統合扱い** (P1 衝突回避)

### Axis 2: R1 機械抽出 references 具体化 + r1 type 別 notes 統合 (W-2)

`reverse-r1/SKILL.md` に 2 セクションを追加 (W-1 衝突回避のため type 別 notes も本 Sprint で実施):

#### A. type 別 operational notes (W-1 と同形式の 5 行 table)

| type | phase-specific action | skip / gate note |
|---|---|---|
| code | OpenAPI/DB 抽出を実施 | RG1 必須 |
| design | (skip) | RG1 不要、R2 へ直行 |
| upgrade | version diff の影響分析 | RG1 必須 |
| normalization | (skip) | RG1 不要、R2 で drift map |
| fullback | 文書 gap の抽出 | RG1 必須 |

#### B. 機械抽出ツールチェーン

- API 抽出: FastAPI / Express / Spring の OpenAPI generator、既存 swagger spec
- DB 抽出: PostgreSQL `\d+` / MySQL INFORMATION_SCHEMA / SQLite `.schema`、ORM introspection
- 型抽出: TypeScript `tsc --emitDeclarationOnly` / Python `pyright` / `mypy --reveal-locals`
- Trait 抽出: Rust `cargo expand` / Go `go doc -all`
- **選択基準** (decision tree 1 つ、1 figure 程度):
  - 既存 spec あり? → spec を正本に補完
  - monorepo? → 言語別 extractor を順次実行
  - 言語混在? → API は OpenAPI、型は言語別
  - 単一言語? → 言語標準 introspection

### Axis 3: R4 routing 基準明文化 (W-3)

`reverse-r4/SKILL.md` に「## routing 判定基準」section 追加。
**primary_routing 列 (L1-L4) と post_forward_action 列 (L8-L11/debt_register) を分離** (既存 R4 契約は L1-L4 単一値):

| severity | gap kind | primary_routing | post_forward_action | 理由 |
|---|---|---|---|---|
| critical | 要件未定義 | L1 | - | PO 合意必須、L2 以降では覆せない |
| critical | 設計矛盾 | L2 | - | ADR 起こし、影響波及確認 |
| critical | 契約不整合 | L3 | - | API/DB Freeze 前 |
| high | 実装欠落 | L4 | - | Sprint で実装 |
| high | 受入条件未定 | L1 | - | acceptance に追加 |
| medium | 文書不足 | L2 | runbook (L11) | ADR + runbook |
| medium | 運用ギャップ | L4 | observability (L10) | 実装 + 観測 |
| low | 命名・整合性 | L4 | debt_register | 次サイクルへ carry |

- **primary_routing**: gap_register の routing 列 (L1/L2/L3/L4 の単一値、既存契約準拠)
- **post_forward_action**: Forward 完遂後の追加 action (L8-L11 / debt_register)、optional

severity 判定基準も併記 (impact × likelihood × reversibility、3 軸 1-5 採点)。

### Axis 4: helix code 連携記述 (W-4)

`reverse-r0/SKILL.md` と `reverse-r1/SKILL.md` に「## helix code 連携」セクション追加:

- R0: `helix code build` で initial catalog 作成、`helix code stats --by domain` で
  証拠網羅性の機械チェック (domain 別 entry 数で coverage 推定)
- R1: `helix code find "<keyword>"` で類似実装検索、observed_contracts への
  evidence link、`helix code dup --threshold 0.85` で重複契約検出 (R1 contradictions の
  事前検出に活用)
- 制約: helix code は public symbol 中心。private helper / runtime-only 契約は別手段で補完

### Axis 5: Reverse → Forward worked example (W-5)

`docs/commands/reverse.md` に「## Worked Example: legacy CRUD → Forward L4」追加:

- シナリオ: 設計書なし legacy CRUD app (Express + PostgreSQL) を Reverse → Forward 連携
- R0: helix code build + DB introspection で evidence_map
- R1: OpenAPI extractor で API 抽出、PostgreSQL `\d+` で DB
- R2: ADR 仮説 3 件 (auth strategy / cache layer / error handling)
- R3: PO 検証で intent 5 件確定 / accidental 2 件 / unknown 1 件
- R4: gap_register 4 件 (1 critical L1 / 2 high L4 / 1 medium L2 + post_forward_action L8 runbook)
- Forward 接続: helix plan で L1-L4 に gap を投入する例 (1 commit 引用)
- 完走時間目安: small (1k LOC) で 4-8h、medium (10k LOC) で 1-2 day

## §3 Sprint 構成

| Sprint | 編集対象 | 委譲先 | 想定 commit |
|---|---|---|---|
| W-0 | draft + 2R TL + finalize | docs / TL ×2 | feat(plan-049): W-0 |
| W-1 | reverse-r0/r2/r3/r4/rgc に type 別 5 行 table 追加 (5 SKILL) | docs | feat(plan-049): W-1 |
| W-2 | reverse-r1 に type 別 notes + 機械抽出ツールチェーン + decision tree | docs | feat(plan-049): W-2 |
| W-3 | reverse-r4 に routing 判定基準 (primary × post_forward_action) | docs | feat(plan-049): W-3 |
| W-4 | reverse-r0 + reverse-r1 に helix code 連携 section | docs | feat(plan-049): W-4 |
| W-5 | docs/commands/reverse.md worked example | docs | feat(plan-049): W-5 |
| W-final | 統合検証 + retro + status completed + push | Opus | feat(plan-049): W-final |

### 編集ファイル衝突マトリクス

| Sprint | r0 | r1 | r2 | r3 | r4 | rgc | reverse.md |
|---|---|---|---|---|---|---|---|
| W-1 | type-notes | - | type-notes | type-notes | type-notes | type-notes | - |
| W-2 | - | type-notes + tools | - | - | - | - | - |
| W-3 | - | - | - | - | routing | - | - |
| W-4 | helix-code | helix-code | - | - | - | - | - |
| W-5 | - | - | - | - | - | - | example |

衝突セル:
- **W-1 vs W-3**: r4 SKILL (W-1 type-notes + W-3 routing 表) → 直列 (W-1 → W-3)
- **W-2 vs W-4**: r1 SKILL (W-2 type-notes + tools + W-4 helix-code) → 直列 (W-2 → W-4)
- **W-1 vs W-4**: r0 SKILL (W-1 type-notes + W-4 helix-code) → 直列 (W-1 → W-4)

**整理後の依存**: W-5 ∥ (W-1 → (W-2, W-3, W-4)) でも W-2→W-4 直列が必要なため:

`W-5 ∥ (W-1 → (W-2 → W-4) ∥ W-3)`

実行段階:
- Stage A (並列): W-5 + W-1
- Stage B (W-1 後): W-2 ∥ W-3
- Stage C (W-2 後): W-4
- Stage D: W-final

### W-1 DoD (Definition of Done)

- 5 SKILL 各々に「## type 別 operational notes」section header が存在
- section は **table のみ**で構成、5 type 全てが行として登場
- section 全体で 10 行以内 (header 2 + 空行 1 + table header 2 + 5 type × 1)
- 既存記述との重複は禁止 (Router の type matrix とは異なる phase-specific な内容)

## §4 受入条件

- 11 acceptance criteria (frontmatter): type_specific_notes_section_present /
  type_specific_notes_5types_covered / r1_extraction_tools_section /
  r1_extraction_specific_tools / r4_routing_table_separated /
  r4_routing_primary_l1_l4 / r1_type_notes_table / helix_code_integration /
  worked_example_present / tests_all_pass / branch_minimal_footprint
- helix-test 614 / pytest 1049+ / bats 416+ / tests 23 全 PASS 維持
- 7 commits 程度 push 済 (W-0 / W-1 / W-2 / W-3 / W-4 / W-5 / W-final、W-final で main merge)

## §5 Out of Scope

- DS-120 の Reverse 反映 (Forward L1-L11 のみ PLAN-047 で完了、Reverse は PLAN-050+ carry)
- helix-reverse CLI 機能拡張 (本 PLAN は **ドキュメント強化のみ**、実装変更なし)
- adversarial-review の Reverse 専用化 (workflow/adversarial-review/SKILL.md は触らない)
- legacy migration / strangler pattern との統合 (advanced/legacy SKILL に委ねる)

## §6 リスク

- **W-1 過剰汎用化**: 5 type × 5 SKILL = 25 行 table が乱立すると保守不能 →
  W-1 DoD で section 全体 10 行以内 (table 5 行 + header) を強制
- **W-2 ツール chain は陳腐化が早い**: 具体ツール名は 6 ヶ月で古くなる → 「選択基準」を
  メイン記述 (decision tree)、ツール例は補助的に列挙
- **W-3 routing table の独断**: severity × routing は project ごとに異なる場合あり →
  「目安」明記 + project ローカルでの override OK
- **W-5 worked example の冗長化**: 完走シナリオは 100+ 行に膨張可 → 80 行以内、
  「実プロジェクトでの再現は 4-8h」目安だけ示す

## §7 検証方法

- W-1 単体: 各 SKILL に「type 別 operational notes」 section が存在
- W-2 単体: r1 SKILL に OpenAPI / introspection / extractor 等の具体ワード ≥ 5
- W-3 単体: r4 SKILL に severity × routing table が存在 (8 行以上)
- W-4 単体: R0/R1 SKILL に `helix code` コマンド記述 (find/stats/build いずれか)
- W-5 単体: reverse.md に Worked Example section 追加
- 統合: cli/helix-test / pytest / bats が破壊されない (docs 変更のみなので影響軽微想定)

## §8 PLAN-050 候補 (carry)

- **DS-120 の Reverse 反映**: PLAN-047 で Forward は完了、Reverse R0-R4 + RGC への
  Informative reference 追加 (政府 reverse-engineering ガイドライン視点)
- **helix-reverse CLI に worked-example スキャフォールド機能**: `helix reverse example
  --type code --target src/` で雛形生成
- **adversarial-review の Reverse 専用 worked checklist**

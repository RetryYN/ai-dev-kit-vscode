---
plan_id: PLAN-173
title: "PLAN-173: FE driver mock harness framework (fe drive 専用 mock 管理 + debt 自動 enqueue)"
layer: L4
kind: impl
status: draft
size: M
drive: fe
created: 2026-05-23
owner: PM
agent_slots:
  - role: pmo-helix-scout
    slot_label: "HELIX Scout — agent-skills/mock-driven-development SKILL.md + 既存 fe 資産の軽量確認"
  - role: tl
    slot_label: "TL — mock harness アーキテクチャ設計 + state-events.md → API 契約導出フロー確認 + ADR-057 起票判断"
  - role: se
    slot_label: "SE — Sprint .1-.3: helix-fe CLI 実装 + MockDebtManager Python module 実装"
  - role: qa
    slot_label: "QA — Sprint .4: テスト設計 + unit/integration test 実装"
  - role: pmo-sonnet
    slot_label: "PMO — Sprint .4 完了時レビュー + V-model artifact 整合確認"
generates:
  - artifact_path: cli/helix-fe
    artifact_type: cli_extension
  - artifact_path: cli/lib/mock_debt_manager.py
    artifact_type: python_module
  - artifact_path: cli/templates/fe/mock-skeleton.html
    artifact_type: template
  - artifact_path: cli/templates/fe/state-events-template.md
    artifact_type: markdown_doc
  - artifact_path: docs/adr/ADR-057-fe-mock-harness-snapshot.md
    artifact_type: adr_snapshot
  - artifact_path: docs/v2/L4-test-design/PLAN-173-unit-test-design.md
    artifact_type: design_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr:
  - ADR-057
related_plans:
  - PLAN-091-plan-framework-v5-core
  - PLAN-099-helix-auto-drive-framework
related_docs:
  - skills/agent-skills/mock-driven-development/SKILL.md
  - skills/SKILL_MAP.md
  - helix/HELIX_CORE.md
---

# PLAN-173: FE driver mock harness framework (fe drive 専用)

> **kind**: impl (CLI + Python module 実装)
> **layer**: L4
> **drive**: fe (FE 駆動タスクの中核 harness)
> **本 PLAN の役割**: HELIX `drive=fe` では mock-driven development が中核だが、mock HTML / state-events.md / API 契約導出 / mock 由来 debt の enqueue がすべて手動フローに依存している。本 PLAN は `helix fe mock` CLI + `MockDebtManager` Python module でこれらを統合的に管理する harness を実装する。

---

## §0. L2 大局判断 (ADR-057)

本 PLAN は以下の L2 大局判断を含む。詳細は ADR-057 に凍結する。

| 判断項目 | 採用案 | 根拠 |
|---|---|---|
| mock skeleton 生成方式 | HTML テンプレート + YAML state-events 雛形の組み合わせ | FE Sprint における TL の state-events.md → API 契約導出フローに直結 |
| debt enqueue 方式 | helix.db の job_queue への直接挿入 (MockDebtManager) | 既存 PLAN-099 自動走行 framework の job_queue と統一 |
| MOCK-HARDCODE / MOCK-CODE-LEAK 検出 | grep ベース + Python AST scan の 2 段構成 | false positive 削減 |
| MOCK-DERIVED-CONTRACT 検出 | state-events.md の diff と D-API の比較 | API 契約導出漏れを機械検出 |

**WebSearch 必須 3 query (Sprint .1 実施前)**:
1. `mock-driven development frontend state machine contract derivation 2025 2026`
2. `WCAG axe-core playwright mock HTML accessibility integration test pattern`
3. `frontend mock hardcode detection AST static analysis 2026`

---

## §1. 目的

1. `helix fe mock <plan-id>` コマンドで FE Sprint 用 mock skeleton (HTML + state-events.md 雛形) を生成する (Sprint .1〜.2)
2. state-events.md から API 契約 (D-API 候補) を半自動導出するフローを CLI に組み込む (Sprint .2〜.3)
3. mock 由来 debt (MOCK-HARDCODE / MOCK-CODE-LEAK / MOCK-DERIVED-CONTRACT) を検出して `helix.db` job_queue へ自動 enqueue する (Sprint .3)

---

## §2. 背景

### 2.1 現状の問題

| 問題 | 影響 |
|---|---|
| mock HTML と state-events.md が手動作成 | FE Sprint .1 の立ち上げが毎回ゼロから |
| state-events.md → API 契約導出が属人的 | TL が契約を見落とすリスク |
| MOCK-HARDCODE / MOCK-CODE-LEAK が手動 grep | G4/G6 ゲートで漏れが発生 |
| debt enqueue が未自動化 | carry として放置される debt が蓄積 |

### 2.2 SKILL_MAP.md との接続

SKILL_MAP.md §駆動タイプ別 L2〜L11 で fe drive は以下を規定する:

- G4 追加条件: `MOCK-HARDCODE` + `MOCK-CODE-LEAK` resolved 必須
- G6 追加条件: `MOCK-DERIVED-CONTRACT` resolved 必須
- L4 実装順: BE (契約ベース) ∥ FE (モック → 本実装昇格) → 統合

本 PLAN はこれらのゲート条件を機械化する harness として機能する。

### 2.3 mock 由来 debt の 3 種類

| debt 種別 | 発生タイミング | 解消条件 |
|---|---|---|
| MOCK-HARDCODE | FE 実装に mock データが直接 hardcode された | 実データ API 接続後に削除 |
| MOCK-CODE-LEAK | mock 専用 logic が本番コードに混入 | mock フラグ除去または mock ファイル分離 |
| MOCK-DERIVED-CONTRACT | state-events.md から導出した API 契約が D-API に未反映 | D-API へのトレース追加 |

---

## §3. 実装方針

### Sprint .1: WebSearch + OSS 探索 + ADR-057 起票 (pmo-helix-scout + tl)

実施内容:
1. pmo-helix-scout が `agent-skills/mock-driven-development/SKILL.md` を確認し、既存 fe 資産を列挙する
2. tl が WebSearch 3 query を実施して ADR-057 を起票する
3. mock skeleton テンプレートの仕様を確定する

完了条件:
- ADR-057 存在、mock skeleton 仕様が確定

### Sprint .2: mock skeleton 生成 CLI 実装 (Codex se)

実施ファイル:
- `cli/helix-fe` (新規、Bash dispatcher)
- `cli/templates/fe/mock-skeleton.html` (新規、mock HTML テンプレート)
- `cli/templates/fe/state-events-template.md` (新規、state-events.md 雛形)
- `cli/helix` への routing 登録 (1 行 `fe)` dispatch)

```bash
# helix fe mock <plan-id>
#   → cli/templates/fe/mock-skeleton.html をコピーして .helix/fe/<plan-id>/mock.html を生成
#   → cli/templates/fe/state-events-template.md をコピーして .helix/fe/<plan-id>/state-events.md を生成
#   → 生成ファイルパスを stdout に出力

# helix fe derive-contract <plan-id>
#   → .helix/fe/<plan-id>/state-events.md を parse して D-API 候補を stdout に列挙
#   → 出力は D-API YAML 形式の skeleton
```

完了条件:
- `bash -n cli/helix-fe` PASS
- `helix fe mock PLAN-173` が mock.html + state-events.md を生成できる (手動確認)

### Sprint .3: MockDebtManager 実装 (Codex se)

実施ファイル:
- `cli/lib/mock_debt_manager.py` (新規)

```python
# MockDebtManager の主要メソッド
# scan_hardcode(path: Path) -> list[DebtItem]
#   → grep + AST scan で MOCK-HARDCODE / MOCK-CODE-LEAK を検出
# scan_contract(state_events_path: Path, dapi_path: Path) -> list[DebtItem]
#   → state-events.md と D-API の diff で MOCK-DERIVED-CONTRACT を検出
# enqueue(items: list[DebtItem], db_path: Path) -> int
#   → helix.db job_queue に debt item を挿入して挿入件数を返す
```

CLI 統合:

```bash
# helix fe audit <plan-id>
#   → MockDebtManager.scan_hardcode() + scan_contract() を実行
#   → 検出された debt を stdout に列挙
# helix fe enqueue <plan-id>
#   → audit 結果を helix.db job_queue へ一括 enqueue
```

完了条件:
- `python3 -m py_compile cli/lib/mock_debt_manager.py` PASS
- `helix fe audit` が MOCK-HARDCODE を検出できる (fixture で確認)

### Sprint .4: テスト設計 + test 実装 (Codex qa)

実施ファイル:
- `docs/v2/L4-test-design/PLAN-173-unit-test-design.md` (V-model artifact ③)
- `cli/lib/tests/test_mock_debt_manager.py` (V-model artifact ④)

テストケース (最小 8 case):
1. `scan_hardcode` が MOCK-HARDCODE を検出すること
2. `scan_hardcode` が false positive なしでクリーンなファイルを通過すること
3. `scan_contract` が state-events.md と D-API の不一致を検出すること
4. `scan_contract` が一致している場合に debt を返さないこと
5. `enqueue` が job_queue に正しく挿入すること
6. `enqueue` が重複 debt を二重挿入しないこと
7. `helix fe mock` が mock.html + state-events.md を生成すること
8. `helix fe audit` が末端に debt 件数を出力すること

完了条件:
- `pytest cli/lib/tests/test_mock_debt_manager.py -v` 全 PASS

---

## §4. Sprint 計画

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **Sprint .1** | WebSearch 3 query + ADR-057 起票 + mock 仕様確定 | pmo-helix-scout + tl | ADR-057 存在、mock skeleton 仕様確定 |
| **Sprint .2** | `cli/helix-fe` + mock skeleton テンプレート実装 | se | bash -n PASS + 手動生成確認 |
| **Sprint .3** | `MockDebtManager` 実装 + `helix fe audit/enqueue` | se | py_compile PASS + fixture 検出確認 |
| **Sprint .4** | テスト設計 doc + unit test 8 case | qa | pytest 全 PASS |

---

## §5. デグレ禁止項目

1. `cli/helix` の既存 dispatch を書き換えない (追記のみ)
2. `helix.db` の既存テーブル schema を変更しない (job_queue への insert のみ)
3. 既存 mock 関連 shell スクリプトが存在する場合はリネームしない

---

## §6. DoD (Definition of Done)

1. `helix fe mock <plan-id>` が mock.html + state-events.md を生成できる
2. `helix fe audit <plan-id>` が 3 種類の debt を検出できる
3. `helix fe enqueue <plan-id>` が helix.db job_queue へ enqueue できる
4. `python3 -m py_compile cli/lib/mock_debt_manager.py` PASS
5. `bash -n cli/helix-fe` PASS
6. unit test 8 case 全 PASS
7. ADR-057 snapshot 起票済 (Sprint .1 完了時)
8. V-model artifact ③ test design doc (PLAN-173-unit-test-design.md) 存在
9. `python3 cli/lib/plan_validator.py docs/plans/PLAN-173-*.md` PASS

---

## §7. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN + ADR-057) | 存在 | docs/plans/PLAN-173-*.md / docs/adr/ADR-057-*.md |
| ② 実装コード | Sprint .2〜.3 で生成 | cli/helix-fe / cli/lib/mock_debt_manager.py |
| ③ テスト設計 | Sprint .4 で起票 | docs/v2/L4-test-design/PLAN-173-unit-test-design.md |
| ④ テストコード | Sprint .4 で実装 | cli/lib/tests/test_mock_debt_manager.py |

**双方向 reference**:
- 本 PLAN (①) → 実装 (②): generates.artifact_path
- 実装 (②) → 本 PLAN (①): cli/helix-fe 先頭 comment に `# PLAN-173` 明記
- 本 PLAN (①) → テスト設計 (③): generates に design_doc として登録済
- テスト設計 (③) → 本 PLAN (①): テスト設計 frontmatter に `related_plans: [PLAN-173]` 明記

---

## §8. 関連 PLAN / ADR

### 前段 (requires)
- なし (独立実施可能)

### 後段で参照される可能性
- PLAN-091 (plan_validator が fe drive template を参照する場合)
- PLAN-099 (自動走行 framework の job_queue と MockDebtManager が統合される場合)

### 関連 ADR
- ADR-057: 本 PLAN の L2 大局判断 snapshot (Sprint .1 で起票)

### 関連 docs
- `skills/agent-skills/mock-driven-development/SKILL.md`: mock-driven development の HELIX 正本
- `skills/SKILL_MAP.md §駆動タイプ別 L2〜L11`: fe drive の G4/G6 追加条件
- `helix/HELIX_CORE.md §設計⇔テスト対応`: V-model 4 artifact 規約

---

## §9. リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| AST scan の Python/JS 言語対応範囲 | JS/TS ファイルの MOCK-HARDCODE 検出漏れ | Sprint .1 で対象言語を ADR-057 に明示し、初版は Python のみで scope を限定 |
| state-events.md の形式が PLAN ごとに異なる | `derive-contract` の parse 失敗 | Sprint .2 で state-events-template.md を標準化し、format ドキュメントを README に追記 |
| helix.db job_queue schema 変更が他 PLAN に影響 | PLAN-099 等との schema 衝突 | Sprint .3 着手前に `helix.db` job_queue DDL を確認し、insert のみに限定する |
| mock skeleton HTML が FE framework (React/Vue 等) に依存 | テンプレートが特定 framework でしか使えない | 初版は framework フリーの純 HTML + Vanilla JS で起草し、framework 固有版は別テンプレートで対応 |

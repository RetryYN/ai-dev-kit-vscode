---
plan_id: PLAN-174
title: "PLAN-174: UI a11y audit framework (axe-core + Playwright 統合、helix doctor 連携)"
layer: L4
kind: impl
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: M
drive: fe
created: 2026-05-23
owner: PM
agent_slots:
  - role: pmo-tech-fork
    slot_label: "Tech Fork — axe-core / playwright-axe / pa11y / Lighthouse CI OSS 採用判断"
  - role: tl
    slot_label: "TL — a11y gate 設計 + helix doctor 統合方針 + ADR-058 起票"
  - role: se
    slot_label: "SE — Sprint .2-.3: helix-ui CLI 実装 + A11yAuditRunner Python module 実装"
  - role: qa
    slot_label: "QA — Sprint .4: テスト設計 + unit/integration test 実装"
  - role: pmo-sonnet
    slot_label: "PMO — Sprint .4 完了時レビュー + V-model artifact 整合確認"
generates:
  - artifact_path: cli/helix-ui
    artifact_type: cli_extension
  - artifact_path: cli/lib/a11y_audit_runner.py
    artifact_type: python_module
  - artifact_path: docs/adr/ADR-058-ui-a11y-audit-framework-snapshot.md
    artifact_type: adr_snapshot
  - artifact_path: docs/v2/L4-test-design/PLAN-174-unit-test-design.md
    artifact_type: design_doc
  - artifact_path: cli/lib/tests/test_a11y_audit_runner.py
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr:
  - ADR-058
related_plans:
  - PLAN-173-fe-driver-mock-harness
  - PLAN-091-plan-framework-v5-core
related_docs:
  - skills/common/visual-design/SKILL.md
  - skills/design-tools/web-system/SKILL.md
  - skills/SKILL_MAP.md
  - helix/HELIX_CORE.md
---

# PLAN-174: UI a11y audit framework (axe-core 統合)

> **kind**: impl (CLI + Python module 実装)
> **layer**: L4
> **drive**: fe (UI 実装の品質ゲートとして位置づけ)
> **本 PLAN の役割**: common/visual-design + design-tools/web-system で UI を実装するすべての FE Sprint において、a11y (アクセシビリティ) チェックが手動 review に依存している。axe-core (Playwright 連携) で WCAG 2.2 AA レベルの違反を機械検出し、`helix ui audit` CLI + `helix doctor` 統合で a11y を品質ゲートに組み込む。

---

## §0. L2 大局判断 (ADR-058)

本 PLAN は以下の L2 大局判断を含む。詳細は ADR-058 に凍結する。

| 判断項目 | 採用案 | 根拠 |
|---|---|---|
| a11y チェックエンジン | axe-core (playwright-axe / @axe-core/playwright) | OSS デファクト・WCAG 2.2 AA 対応・Python/Node 両対応 |
| 実行方式 | Playwright を Python から subprocess 起動 + JSON レポート出力 | HELIX が Python/Bash 中心のため Python wrapper が最適 |
| 判定基準 | WCAG 2.2 AA レベル (critical + serious を fail 扱い) | EU Accessibility Act 2025 + JIS X 8341-3:2016 水準 |
| helix doctor 統合 | `check_ui_a11y` 新規 check として登録、UI 系 PLAN の G4/G6 で発火 | 既存 doctor check パターンに統一 |

**WebSearch 必須 3 query (Sprint .1 実施前)**:
1. `axe-core playwright python integration WCAG 2.2 AA 2025 2026`
2. `EU Accessibility Act 2025 WCAG compliance automated testing CI integration`
3. `helix ui accessibility audit gate definition of done frontend 2026`

---

## §1. 目的

1. `helix ui audit --target <url-or-html>` で axe-core を使った WCAG 2.2 AA 違反を検出する (Sprint .2〜.3)
2. `helix doctor` に `check_ui_a11y` を追加し、UI 系 PLAN の G4/G6 ゲートで a11y を自動チェックする (Sprint .3)
3. 違反レポートを `helix.db` に記録し、carry / debt として追跡できるようにする (Sprint .3)

---

## §2. 背景

### 2.1 現状の問題

| 問題 | 影響 |
|---|---|
| a11y チェックが手動 review のみ | G4/G6 ゲートで見落とされる違反が発生 |
| WCAG 判定基準がドキュメント化されていない | reviewer によって判断が揺れる |
| 違反が carry として記録されない | debt 蓄積が不可視化される |
| axe-core が CI 統合されていない | 本番デプロイ後に違反が発覚するリスク |

### 2.2 SKILL_MAP.md との接続

SKILL_MAP.md の既存スキル強化メモ:

```yaml
common/visual-design:
  description: ... IA/モーション/UXパターン/a11y/データViz論を references/ で提供
design-tools/web-system:
  description: ... DESIGN.md形式のD-VIS-ARCH適用手順を references/ で提供
automation/browser-script:
  description: ... axe-coreによるアクセシビリティ自動検証を提供
```

`automation/browser-script` SKILL が axe-core を参照しているが、HELIX CLI として統合されていない。本 PLAN はこの gap を埋める。

### 2.3 WCAG 2.2 AA 違反の severity マッピング

| axe-core impact | HELIX 扱い | 対応 |
|---|---|---|
| critical | fail (ゲート stop) | 即時修正必須 |
| serious | fail (ゲート stop) | 即時修正必須 |
| moderate | warn (carry) | P2 carry として記録 |
| minor | info (任意) | 記録のみ |

---

## §3. 実装方針

### Sprint .1: OSS 探索 + ADR-058 起票 (pmo-tech-fork + tl)

実施内容:
1. pmo-tech-fork が axe-core / playwright-axe / pa11y / Lighthouse CI を比較調査する (WebSearch 3 query 実施)
2. tl が採用 OSS を確定し ADR-058 を起票する
3. Python subprocess 経由での axe-core 実行方式を決定する

完了条件:
- WebSearch 3 query 完了 + ADR-058 accepted
- 採用 OSS と Python 実行方式が確定

### Sprint .2: A11yAuditRunner Python module 実装 (Codex se)

実施ファイル:
- `cli/lib/a11y_audit_runner.py` (新規)

```python
# A11yAuditRunner の主要メソッド
# run(target: str, wcag_level: str = "AA") -> A11yReport
#   → Playwright + axe-core でターゲット (URL または HTML ファイルパス) を検査
#   → A11yReport (violations list + pass list + incomplete list) を返す
# save_report(report: A11yReport, db_path: Path) -> None
#   → 違反結果を helix.db の a11y_violations テーブルに保存
# to_carry_items(report: A11yReport) -> list[CarryItem]
#   → critical/serious 違反を carry item に変換して返す
```

完了条件:
- `python3 -m py_compile cli/lib/a11y_audit_runner.py` PASS
- `run()` が mock HTML に対して axe-core を実行できる (手動確認)

### Sprint .3: helix-ui CLI 実装 + helix doctor 統合 (Codex se)

実施ファイル:
- `cli/helix-ui` (新規、Bash dispatcher)
- `cli/helix` への routing 登録 (1 行 `ui)` dispatch)
- `cli/lib/helix_doctor.py` への `check_ui_a11y` 追加

```bash
# helix ui audit --target <url-or-html> [--wcag-level AA] [--plan-id PLAN-X]
#   → A11yAuditRunner.run() を実行
#   → violations を stdout に出力 (critical/serious は exit 1)
#   → --plan-id 指定時は helix.db に結果を保存

# helix ui report [--plan-id PLAN-X]
#   → helix.db から a11y 違反レポートを表示

# helix doctor check_ui_a11y --plan-id PLAN-X
#   → helix ui audit を呼び出し、critical/serious 0 件で pass
```

helix.db 変更範囲:
- `a11y_violations` テーブル新規追加 (plan_id / target / impact / rule_id / description / created_at)
- migration script として `cli/lib/migrate.py` に追記 (schema_version 更新)

完了条件:
- `bash -n cli/helix-ui` PASS
- `helix ui audit` が WCAG 違反を検出できる (fixture HTML で確認)
- `helix doctor` に `check_ui_a11y` が表示される

### Sprint .4: テスト設計 + test 実装 (Codex qa)

実施ファイル:
- `docs/v2/L4-test-design/PLAN-174-unit-test-design.md` (V-model artifact ③)
- `cli/lib/tests/test_a11y_audit_runner.py` (V-model artifact ④)

テストケース (最小 8 case):
1. `run()` が critical 違反を含む HTML で violations を返すこと
2. `run()` が違反なし HTML で空 violations を返すこと
3. `run()` が URL ターゲットで動作すること (モック Playwright 使用)
4. `save_report()` が helix.db に違反を正しく保存すること
5. `save_report()` が同一 plan_id での重複実行で上書きすること
6. `to_carry_items()` が critical/serious のみを carry item に変換すること
7. `to_carry_items()` が moderate を carry item に含めないこと
8. `helix ui audit` が critical 違反存在時に exit 1 を返すこと

完了条件:
- `pytest cli/lib/tests/test_a11y_audit_runner.py -v` 全 PASS

---

## §4. Sprint 計画

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **Sprint .1** | OSS 探索 + ADR-058 起票 | pmo-tech-fork + tl | ADR-058 accepted、採用 OSS 確定 |
| **Sprint .2** | `A11yAuditRunner` Python module 実装 | se | py_compile PASS + 手動動作確認 |
| **Sprint .3** | `cli/helix-ui` 実装 + helix doctor 統合 | se | bash -n PASS + helix doctor 統合確認 |
| **Sprint .4** | テスト設計 doc + unit test 8 case | qa | pytest 全 PASS |

---

## §5. デグレ禁止項目

1. `cli/helix` の既存 dispatch を書き換えない (追記のみ)
2. `helix.db` の既存テーブルの DDL を変更しない (新テーブル追加のみ)
3. `cli/lib/helix_doctor.py` の既存 check を削除・変更しない (check 追加のみ)
4. Playwright の追加依存が既存 test 環境 (pytest/bats) を破壊しない (opt-in install を前提とする)

---

## §6. DoD (Definition of Done)

1. `helix ui audit --target <html>` が WCAG 2.2 AA 違反を検出し、critical/serious 存在時に exit 1 を返す
2. `helix doctor check_ui_a11y --plan-id PLAN-X` が a11y gate として機能する
3. `python3 -m py_compile cli/lib/a11y_audit_runner.py` PASS
4. `bash -n cli/helix-ui` PASS
5. unit test 8 case 全 PASS
6. ADR-058 snapshot 起票済 (Sprint .1 完了時)
7. V-model artifact ③ test design doc (PLAN-174-unit-test-design.md) 存在
8. `helix commands` に `ui` が表示される
9. `python3 cli/lib/plan_validator.py docs/plans/PLAN-174-*.md` PASS

---

## §7. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN + ADR-058) | 存在 | docs/plans/PLAN-174-*.md / docs/adr/ADR-058-*.md |
| ② 実装コード | Sprint .2〜.3 で生成 | cli/helix-ui / cli/lib/a11y_audit_runner.py |
| ③ テスト設計 | Sprint .4 で起票 | docs/v2/L4-test-design/PLAN-174-unit-test-design.md |
| ④ テストコード | Sprint .4 で実装 | cli/lib/tests/test_a11y_audit_runner.py |

**双方向 reference**:
- 本 PLAN (①) → 実装 (②): generates.artifact_path
- 実装 (②) → 本 PLAN (①): cli/helix-ui 先頭 comment に `# PLAN-174` 明記
- 本 PLAN (①) → テスト設計 (③): generates に design_doc として登録済
- テスト設計 (③) → 本 PLAN (①): テスト設計 frontmatter に `related_plans: [PLAN-174]` 明記

---

## §8. 関連 PLAN / ADR

### 前段 (requires)
- なし (独立実施可能)

### 関連 PLAN (後続)
- PLAN-173: fe mock harness と同一 fe drive、PLAN-174 の a11y gate が mock HTML にも適用可能

### 関連 ADR
- ADR-058: 本 PLAN の L2 大局判断 snapshot (Sprint .1 で起票)

### 関連 docs
- `skills/common/visual-design/SKILL.md`: a11y/UX パターンの HELIX 参照先
- `skills/automation/browser-script/SKILL.md §axe-core`: axe-core 既存 SKILL 参照
- `skills/SKILL_MAP.md §既存スキル強化メモ`: automation/browser-script の a11y 強化メモ

---

## §9. リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| Playwright Node.js 依存が HELIX の Python/Bash 環境に追加 | npm install 必須化による環境複雑化 | Sprint .1 で Python only (playwright-python) の実現可能性を調査、Node 不要な経路を優先する |
| axe-core の WCAG 2.2 AA カバレッジが不完全 | 一部違反の検出漏れ | ADR-058 で採用バージョンと検出可能ルール数を明示し、検出不能項目は手動チェックリストで補完 |
| helix doctor の `check_ui_a11y` が全 PLAN で発火する | a11y 無関係な BE PLAN の doctor 結果が汚染される | UI 系 PLAN (drive=fe/fullstack) のみ発火するよう plan_id の drive を参照して条件分岐する |
| Playwright の headless browser セットアップが CI で失敗 | GitHub Actions / WSL 環境での動作不確実 | Sprint .1 で WSL + GitHub Actions 両環境での Playwright headless 動作を pmo-tech-fork が確認する |

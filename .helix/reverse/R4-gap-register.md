# R4 Gap Register & Forward HELIX ルーティング

> 生成日: 2026-04-05
> 対象: ~/ai-dev-kit-vscode (HELIX CLI v3)
> フェーズ: R4 Gap & Routing
> 入力: R0-evidence-map.yaml, R1-observed-contracts.yaml, R2-as-is-design.md

---

## 1. Gap Register

### 1.1 凡例

| 種別 | 意味 |
|------|------|
| defect | バグ・不整合 |
| assumption | 仮定が未検証 |
| quality | 品質基準未達 |
| scope | 機能不足 |

| 深刻度 | 意味 |
|--------|------|
| P0 | 即座に対応が必要（整合性破壊・セキュリティ） |
| P1 | 次スプリントで対応（品質リスク・運用障害） |
| P2 | 中期で対応（改善・拡張） |

### 1.2 Gap 一覧

| ID | Gap 内容 | 種別 | 深刻度 | Forward 接続先 | 状態 | 根拠 |
|----|---------|------|--------|--------------|------|------|
| GAP-001 | gate-checks.yaml パースに PyYAML が残存（helix-gate L428） | defect | P1 | L4 | **解決済** | R2 TD-001 |
| GAP-002 | helix-gate AI セクションの Bash 行パースが脆弱（インデント崩れ・特殊文字で誤動作） | defect | P1 | L4 | **解決済** | R2 TD-002 |
| GAP-003 | helix-task の sed による YAML 更新（同一パターン複数マッチで誤更新リスク） | defect | P1 | L4 | **解決済** | R2 TD-003 |
| GAP-004 | exit code 定義（EXIT_SUCCESS 等）が一部コマンドで未活用（helix-scrum, helix-task が exit 1 ハードコード） | defect | P2 | L4 | 未着手 | R2 TD-006, R1 common.exit_codes |
| GAP-005 | __pycache__ が git tracking に残存 | defect | P0 | L4 | **解決済** | R2 TD-009 |
| GAP-006 | SQLite FK 制約が未 enforce（PRAGMA foreign_keys = ON 未設定） | defect | P1 | L4 | **解決済** | R0 unknowns.spec_unclear, R0 unknowns.potential_risks |
| GAP-007 | gate_runs.task_run_id の FK が実 DB で未作成（定義と実態の乖離） | defect | P1 | L4 | **解決済** | R0 unknowns.spec_unclear |
| GAP-008 | Bash エラーハンドリング不統一（set -eo pipefail / set -euo pipefail 混在） | quality | P1 | L3 → L4 | **解決済** (31ファイル統一) | R2 TD-005 |
| GAP-009 | matrix_compiler.py にユニットテストなし（1435行・最重要コンパイラ） | quality | P1 | L3 → L4 | **解決済** (23テスト) | R0 unknowns.no_unit_test |
| GAP-010 | deliverable_gate.py にユニットテストなし（522行） | quality | P1 | L3 → L4 | **解決済** (13テスト) | R0 unknowns.no_unit_test |
| GAP-011 | global_store.py にユニットテストなし（611行・横断データ管理） | quality | P1 | L3 → L4 | **解決済** (15テスト) | R0 unknowns.no_unit_test |
| GAP-012 | phase_guard.py にユニットテストなし（366行） | quality | P2 | L3 → L4 | 未着手 | R0 unknowns.no_unit_test |
| GAP-013 | freeze_checker.py にユニットテストなし（351行） | quality | P2 | L3 → L4 | 未着手 | R0 unknowns.no_unit_test |
| GAP-014 | gate_check_generator.py にユニットテストなし（609行） | quality | P2 | L3 → L4 | 未着手 | R0 unknowns.no_unit_test |
| GAP-015 | matrix_advisor.py にユニットテストなし（453行） | quality | P2 | L3 → L4 | 未着手 | R0 unknowns.no_unit_test |
| GAP-016 | recipe_store.py にユニットテストなし（245行） | quality | P2 | L3 → L4 | 未着手 | R0 unknowns.no_unit_test |
| GAP-017 | team_runner.py にユニットテストなし（248行） | quality | P2 | L3 → L4 | 未着手 | R0 unknowns.no_unit_test |
| GAP-018 | merge_settings.py にユニットテストなし（146行） | quality | P2 | L3 → L4 | 未着手 | R0 unknowns.no_unit_test |
| GAP-019 | doc_map_matcher.py にユニットテストなし（111行） | quality | P2 | L3 → L4 | 未着手 | R0 unknowns.no_unit_test |
| GAP-020 | builders/ 全14モジュール（2655行）にユニットテストなし | quality | P1 | L3 → L4 | **解決済** (test_builders.py 22件 + test_builders_concrete.py 21件) | R0 unknowns.no_unit_test |
| GAP-021 | CLI 全体のアーキテクチャ設計書なし | quality | P1 | L2 | **解決済** (L2-cli-architecture.md) | R0 unknowns.no_design_doc |
| GAP-022 | Builder System の設計仕様書なし（12モジュール・2655行） | quality | P1 | L2 | **解決済** (L2-builder-system.md) | R0 unknowns.no_design_doc |
| GAP-023 | Learning Engine の設計仕様書なし（2000行・最大モジュール） | quality | P1 | L2 | **解決済** (L2-learning-engine.md) | R0 unknowns.no_design_doc |
| GAP-024 | DB マイグレーション戦略の文書なし（v1→v4 進行中） | quality | P2 | L2 | **解決済** (D-DB-MIGRATION.md) | R0 unknowns.no_design_doc |
| GAP-025 | 状態機械の遷移仕様書なし（phase_guard.py 内にハードコード） | quality | P2 | L2 | 未着手 | R0 unknowns.no_design_doc |
| GAP-026 | helix-interrupt の IIP/CC 分類ロジック仕様不明（890行） | assumption | P2 | L1 | 未着手 | R0 unknowns.spec_unclear |
| GAP-027 | helix-hook の doc-map トリガー優先度不明 | assumption | P2 | L1 | 未着手 | R0 unknowns.spec_unclear |
| GAP-028 | Builder quality_score の算出基準がビルダーごとに異なり統一基準なし | assumption | P2 | L1 → L2 | 未着手 | R0 unknowns.spec_unclear |
| GAP-029 | recipe の自動昇格閾値が文書化されていない | assumption | P2 | L1 | 未着手 | R0 unknowns.spec_unclear |
| GAP-030 | helix-test と helix-test-debug の重複管理方針不明（1540行 vs 1533行） | assumption | P2 | L2 | 未着手 | R0 unknowns.spec_unclear |
| GAP-031 | fullstack 駆動タイプの L4.5 結合フェーズの CLI 実装が不完全 | scope | P1 | L3 → L4 | **解決済** (helix-sprint に .b1/.b2/.b3 実装) | R0 unknowns.spec_unclear, R2 TD-008 |
| GAP-032 | RGC（Reverse Gap Closure）が CLI 未実装 | scope | P2 | L3 → L4 | 未着手 | R0 unknowns.spec_unclear, MEMORY.md |
| GAP-033 | Builder System と CLI の接続が設計構想段階 | scope | P1 | L2 → L3 → L4 | **部分解決** (D-BUILDER-INTEGRATION.md 作成、実装統合は未着手) | R2 TD-007 |
| GAP-034 | fullstack Phase B 結合時の contract CI 自動実行が未実装 | scope | P1 | L3 → L4 | **部分解決** (drift-check で D-CONTRACT/D-DB 簡易検証実装) | R2 TD-008 |
| GAP-035 | ADR が推定のみ（R2 ADR-001〜010）で正式文書化されていない | quality | P1 | L2 | **解決済** (ADR-001〜010 全10件正式化完了) | R2 §4 |
| GAP-036 | yaml_parser.py の制約（アンカー・マージキー・フロー非対応）が明文化されていない | quality | P2 | L2 | **解決済** (yaml_parser.py docstring で明文化) | R0 unknowns.potential_risks |
| GAP-037 | learning_engine.py が 2000行の巨大ファイル（責務分割候補） | quality | P2 | L2 → L4 | 未着手 | R0 unknowns.potential_risks |
| GAP-038 | Codex 依存のレジリエンス不足（リトライ2回のみ・代替モデルなし） | quality | P2 | L2 | 未着手 | R0 unknowns.potential_risks |
| GAP-039 | helix-debug のテストが helix-test 内に存在しない | quality | P2 | L3 → L4 | 未着手 | R0 unknowns.minimal_test_coverage |
| GAP-040 | helix-verify-all のテストが --help のみ | quality | P2 | L3 → L4 | 未着手 | R0 unknowns.minimal_test_coverage |
| GAP-041 | helix-gate の G1 が valid_values に含まれない（G0.5, G2-G7 のみ） | assumption | P2 | L1 | 未着手 | R1 helix-gate.arguments |
| GAP-042 | helix-reverse R4 の stage_gates が RG3（R3 と同一ゲート） | assumption | P2 | L1 | 未着手 | R1 helix-reverse.stage_gates |

---

## 2. Gap 統計サマリ

### 2.1 種別分布

| 種別 | 件数 | P0 | P1 | P2 | 解決済 |
|------|------|----|----|-----|--------|
| defect | 7 | 1 | 5 | 1 | 6 (P0:1, P1:5) |
| assumption | 7 | 0 | 0 | 7 | 0 |
| quality | 22 | 0 | 10 | 12 | 7 (P1:7) |
| scope | 6 | 0 | 4 | 2 | 0 |
| **合計** | **42** | **1** | **19** | **22** | **13** |

> **2026-04-14 更新**: 42件中17件が解決済み。未解決 P1: 3件（GAP-031, 033部分, 034）、未解決 P2: 22件
> Sprint F-1 通過: GAP-008, GAP-020（完全）, GAP-035（完全）、GAP-033（設計書のみ）、BUG-A 修正、ADR-007〜010 正式化、D-BUILDER-INTEGRATION.md 作成

### 2.2 Forward 接続先分布

| 接続先 | 件数 | 主な Gap |
|--------|------|---------|
| L1（要件定義） | 5 | GAP-026〜029, 041, 042 |
| L2（全体設計） | 10 | GAP-021〜025, 030, 035〜038 |
| L3→L4（詳細設計→実装） | 17 | GAP-008〜020, 031〜034, 039〜040 |
| L4（実装修正） | 7 | GAP-001〜007 |
| L1→L2（要件→設計） | 1 | GAP-028 |
| L2→L3→L4（設計→実装） | 2 | GAP-033, 037 |

---

## 3. Forward HELIX ルーティング

### 3.1 L1 行き（要件が不明確な Gap）

要件レベルで仕様が未定義・未検証の Gap。Forward L1 で要件構造化と受入条件定義が必要。

| ID | Gap 内容 | 理由 |
|----|---------|------|
| GAP-026 | helix-interrupt IIP/CC 分類ロジック仕様不明 | 890行のコマンドだが分類アルゴリズムの仕様がない。要件定義から必要 |
| GAP-027 | doc-map トリガー優先度不明 | 複数トリガー一致時の振る舞いが未定義。仕様策定が先決 |
| GAP-028 | Builder quality_score 統一基準なし | ビルダー横断の品質評価基準の要件策定が必要 |
| GAP-029 | recipe 自動昇格閾値の文書化なし | 昇格ポリシーの要件定義が必要 |
| GAP-041 | G1 ゲートが helix-gate の有効値に未含 | G1 の要件（運用上スキップなのか・意図的欠如なのか）を確認 |
| GAP-042 | R4 の stage_gates が R3 と同一（RG3） | R4 専用ゲートの要否を検討 |

### 3.2 L2 行き（設計文書が欠如している Gap）

アーキテクチャ設計・ADR・設計文書の策定が必要な Gap。

| ID | Gap 内容 | 成果物 |
|----|---------|--------|
| GAP-021 | CLI 全体のアーキテクチャ設計書なし | D-ARCH（CLI アーキテクチャ設計書） |
| GAP-022 | Builder System 設計仕様書なし | D-BUILDER-SPEC（Builder 設計仕様書） |
| GAP-023 | Learning Engine 設計仕様書なし | D-LEARNING-SPEC（Learning Engine 設計仕様書） |
| GAP-024 | DB マイグレーション戦略文書なし | D-DB-MIGRATION（マイグレーション戦略書） |
| GAP-025 | 状態機械の遷移仕様書なし | D-STATE-SPEC（状態機械仕様書） |
| GAP-030 | helix-test/helix-test-debug 重複管理方針不明 | ADR（テスト重複管理方針） |
| GAP-035 | ADR が推定のみで正式文書化されていない | ADR-001〜ADR-010 正式化 |
| GAP-036 | yaml_parser.py 制約の明文化なし | D-YAML-PARSER-SPEC（制約仕様書） |
| GAP-037 | learning_engine.py 2000行の責務分割 | D-LEARNING-REFACTOR（分割設計書） |
| GAP-038 | Codex 依存のレジリエンス不足 | D-RESILIENCE（フォールバック設計） |

### 3.3 L3→L4 行き（詳細設計・テスト設計 → 実装）

テスト戦略の策定（L3）とテスト実装（L4）の両方が必要な Gap。

| ID | Gap 内容 | L3 成果物 | L4 成果物 |
|----|---------|-----------|-----------|
| GAP-008 | Bash エラーハンドリング不統一 | D-ERROR-POLICY（エラーハンドリング規約） | 全コマンドの統一修正 |
| GAP-009 | matrix_compiler.py テストなし | テスト設計書 | test_matrix_compiler.py |
| GAP-010 | deliverable_gate.py テストなし | テスト設計書 | test_deliverable_gate.py |
| GAP-011 | global_store.py テストなし | テスト設計書 | test_global_store.py |
| GAP-012 | phase_guard.py テストなし | テスト設計書 | test_phase_guard.py |
| GAP-013 | freeze_checker.py テストなし | テスト設計書 | test_freeze_checker.py |
| GAP-014 | gate_check_generator.py テストなし | テスト設計書 | test_gate_check_generator.py |
| GAP-015 | matrix_advisor.py テストなし | テスト設計書 | test_matrix_advisor.py |
| GAP-016 | recipe_store.py テストなし | テスト設計書 | test_recipe_store.py |
| GAP-017 | team_runner.py テストなし | テスト設計書 | test_team_runner.py |
| GAP-018 | merge_settings.py テストなし | テスト設計書 | test_merge_settings.py |
| GAP-019 | doc_map_matcher.py テストなし | テスト設計書 | test_doc_map_matcher.py |
| GAP-020 | builders/ 全14モジュールテストなし | テスト設計書 | test_builders_*.py |
| GAP-031 | fullstack L4.5 結合フェーズ未実装 | D-L4.5-SPEC（結合フェーズ設計） | helix-sprint 結合ロジック |
| GAP-032 | RGC（Reverse Gap Closure）CLI 未実装 | D-RGC-SPEC（RGC 設計） | helix-reverse rgc コマンド |
| GAP-033 | Builder System と CLI の接続 | D-BUILDER-INTEGRATION（統合設計） | helix-builder 統合実装 |
| GAP-034 | fullstack Phase B contract CI 自動実行 | D-CONTRACT-CI（CI 設計） | helix-sprint Phase B 自動化 |
| GAP-039 | helix-debug テストなし | テスト設計書 | helix-test 内テスト追加 |
| GAP-040 | helix-verify-all テストが極小 | テスト設計書 | helix-test 内テスト拡充 |

### 3.4 L4 行き（実装修正のみで解決する Gap）

既に設計が明確で、実装修正のみが必要な Gap。

| ID | Gap 内容 | 修正方針 |
|----|---------|---------|
| GAP-001 | PyYAML 残存 | helix-gate の import yaml → yaml_parser.py ベースに統一 |
| GAP-002 | AI セクション Bash パース脆弱 | Python 側でパースして Bash に渡す方式に変更 |
| GAP-003 | helix-task の sed YAML 更新 | yaml_parser.py write に統一 |
| GAP-004 | exit code 未活用 | helix-scrum, helix-task の exit 1 → 定義済みコード使用 |
| GAP-005 | __pycache__ git 残存 | .gitignore に __pycache__/ 追加 + git rm --cached |
| GAP-006 | SQLite FK 未 enforce | helix_db.py の init_db で PRAGMA foreign_keys = ON 追加 |
| GAP-007 | gate_runs FK 定義と実態の乖離 | マイグレーション v5 で FK 制約を正しく適用 |

---

## 4. 改善ロードマップ

### Phase 1: 即座（P0 — 1件）

> 対応目安: 即日

| ID | Gap | 作業内容 | 工数 | 担当ロール |
|----|-----|---------|------|-----------|
| GAP-005 | __pycache__ git 残存 | .gitignore 追記 + git rm --cached 実行 | S | PG |

### Phase 2: 次スプリント（P1 — 19件）

> 対応目安: 1-2 スプリント

#### Sprint 2a: defect 修正（5件）

| ID | Gap | 作業内容 | 工数 | 担当ロール |
|----|-----|---------|------|-----------|
| GAP-001 | PyYAML 残存 | gate-checks.yaml パーサー統一 | S | SE |
| GAP-002 | AI パース脆弱 | Python パーサー化 | M | SE |
| GAP-003 | sed YAML 更新 | yaml_parser.py 統一 | S | PG |
| GAP-006 | FK 未 enforce | PRAGMA 追加 + 既存データ整合確認 | S | DBA |
| GAP-007 | FK 定義乖離 | マイグレーション v5 作成 | S | DBA |

#### Sprint 2b: 設計文書化（5件）

| ID | Gap | 作業内容 | 工数 | 担当ロール |
|----|-----|---------|------|-----------|
| GAP-021 | CLI アーキテクチャ設計書 | R2 As-Is Design をベースに正式化 | M | TL |
| GAP-022 | Builder 設計仕様書 | base.py + registry.py 中心に仕様書作成 | M | TL |
| GAP-023 | Learning Engine 設計仕様書 | recipe 生成ロジックの設計文書化 | M | TL |
| GAP-035 | ADR 正式化 | R2 推定 ADR-001〜010 を docs/adr/ に文書化 | M | TL |
| GAP-033 | Builder-CLI 統合設計 | D-BUILDER-INTEGRATION 作成 | M | TL |

#### Sprint 2c: テスト強化・優先モジュール（5件）

| ID | Gap | 作業内容 | 工数 | 担当ロール |
|----|-----|---------|------|-----------|
| GAP-009 | matrix_compiler テスト | テスト設計 + 実装（最優先） | L | QA + SE |
| GAP-010 | deliverable_gate テスト | テスト設計 + 実装 | M | QA + SE |
| GAP-011 | global_store テスト | テスト設計 + 実装 | M | QA + SE |
| GAP-020 | builders テスト | テスト設計 + 実装（base, store, history 優先） | L | QA + SE |
| GAP-008 | エラーハンドリング統一 | 規約策定 + 全コマンド修正 | L | TL + PG |

#### Sprint 2d: scope 拡張（4件）

| ID | Gap | 作業内容 | 工数 | 担当ロール |
|----|-----|---------|------|-----------|
| GAP-031 | fullstack L4.5 結合 | 設計 + helix-sprint 拡張 | M | SE |
| GAP-034 | Phase B contract CI | 設計 + 自動実行組み込み | M | SE |
| GAP-033 | Builder-CLI 接続実装 | 統合設計に基づく段階的実装 | L | SE |
| GAP-038 | Codex レジリエンス | フォールバック設計 + 実装 | M | TL + SE |

### Phase 3: 中期（P2 — 22件）

> 対応目安: 3-5 スプリント

#### Sprint 3a: 残テスト補完（8件）

| ID | Gap | 工数 |
|----|-----|------|
| GAP-012 | phase_guard.py テスト | M |
| GAP-013 | freeze_checker.py テスト | M |
| GAP-014 | gate_check_generator.py テスト | M |
| GAP-015 | matrix_advisor.py テスト | M |
| GAP-016 | recipe_store.py テスト | S |
| GAP-017 | team_runner.py テスト | S |
| GAP-018 | merge_settings.py テスト | S |
| GAP-019 | doc_map_matcher.py テスト | S |

#### Sprint 3b: 設計文書追加（4件）

| ID | Gap | 工数 |
|----|-----|------|
| GAP-024 | DB マイグレーション戦略文書 | S |
| GAP-025 | 状態機械遷移仕様書 | M |
| GAP-030 | テスト重複管理方針 ADR | S |
| GAP-036 | yaml_parser.py 制約明文化 | S |

#### Sprint 3c: 要件明確化（6件）

| ID | Gap | 工数 |
|----|-----|------|
| GAP-026 | helix-interrupt 分類ロジック仕様策定 | M |
| GAP-027 | doc-map トリガー優先度仕様策定 | S |
| GAP-028 | quality_score 統一基準策定 | M |
| GAP-029 | recipe 昇格閾値文書化 | S |
| GAP-041 | G1 ゲート要否確認 | S |
| GAP-042 | R4 専用ゲート要否検討 | S |

#### Sprint 3d: 改善実装（4件）

| ID | Gap | 工数 |
|----|-----|------|
| GAP-004 | exit code 統一 | M |
| GAP-032 | RGC CLI 実装 | M |
| GAP-037 | learning_engine.py 分割 | L |
| GAP-039〜040 | テスト拡充（debug, verify-all） | S |

---

## 5. Reverse 完了宣言

### 5.1 Reverse フェーズ実績

| フェーズ | 成果物 | 行数 | ゲート |
|---------|--------|------|--------|
| R0 | R0-evidence-map.yaml | 1166 | RG0 passed |
| R1 | R1-observed-contracts.yaml | 958 | RG1 passed |
| R2 | R2-as-is-design.md | 546 | RG2 passed |
| R3 | （R3-intent-hypotheses.md — 本プロジェクトは自開発のため R3 は N/A） | — | RG3 passed |
| R4 | R4-gap-register.md（本文書） | — | — |

### 5.2 Gap ルーティング完了確認

- **全 42 件の Gap** が Forward HELIX のフェーズ（L1/L2/L3/L4）にルーティング済み
- **未ルーティング Gap: 0件**
- 改善ロードマップで Phase 1（P0: 1件）/ Phase 2（P1: 19件）/ Phase 3（P2: 22件）に分類済み

### 5.3 Forward HELIX 接続指示

1. `phase.yaml` の `reverse.status` を `completed` に更新
2. `phase.yaml` の `reverse.completed_at` を `2026-04-05` に設定
3. `current_mode` を `forward` に切り替え
4. Phase 1（GAP-005）を即座に実行
5. Phase 2 の Sprint 2a（defect 修正）から Forward L4 マイクロスプリントを開始

### 5.4 Forward フェーズ別の着手順序

```
Phase 1 (即日)
  └── GAP-005: __pycache__ 除外 → L4 のみ

Phase 2 Sprint 2a (defect 修正)
  └── GAP-001,002,003,006,007 → L4 マイクロスプリント

Phase 2 Sprint 2b (設計文書化)
  └── GAP-021,022,023,035,033 → L2 設計ドキュメント作成

Phase 2 Sprint 2c (テスト強化)
  └── GAP-009,010,011,020,008 → L3 テスト設計 → L4 テスト実装

Phase 2 Sprint 2d (scope 拡張)
  └── GAP-031,034,033,038 → L3 詳細設計 → L4 実装

Phase 3 (中期)
  └── GAP-004,012-019,024-030,032,036-042 → 各 Forward フェーズ
```

---

> **R4 完了**: 全 Gap が Forward HELIX にルーティングされました。
> **次のアクション**: `helix mode forward` → Phase 1 即時実行 → Phase 2 スプリント計画へ。

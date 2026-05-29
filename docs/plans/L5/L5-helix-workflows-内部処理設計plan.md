---
plan_id: L5-helix-workflows-内部処理設計plan
title: "L5-helix-workflows-内部処理設計plan: HELIX-workflows V2 内部処理 / アルゴリズム / 状態機械設計"
kind: design
layer: L5
drive: be
status: finalized
created: 2026-05-27
owner: PM
process_layer: L5
parent_process: HELIX-workflows/helix-process/L5-detailed-design.md
pairs_test_design:
  - docs/v2/L8-test-design/helix-workflows-integration-test-design.md
  - docs/v2/L8-test-design/helix-workflows-dependency-resolution-design.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G5 evidence)"
  - role: doc-reviewer
    slot_label: "doc-reviewer — ドキュメント品質レビュー"
generates:
  - artifact_path: docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md
    artifact_type: design_doc
dependencies:
  parent: L4-helix-workflows-機能設計plan
  requires:
    - L4-helix-workflows-方式設計plan
    - L4-helix-workflows-機能設計plan
    - L4-helix-workflows-データ設計plan
    - L4-helix-workflows-外部IF設計plan
  blocks:
    - L5-helix-workflows-モジュール分割設計plan
    - L5-helix-workflows-データ詳細設計plan
    - L5-helix-workflows-外部IF詳細設計plan
related_docs:
  - HELIX-workflows/helix-process/L5-detailed-design.md
  - HELIX-workflows/helix-process/L8-integration-test.md
  - docs/v2/L4-architecture/helix-workflows-functional-design.md
  - docs/v2/L4-architecture/helix-workflows-system-architecture.md
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
  - docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md
---

## §0 PLAN concept

本 PLAN は L4 機能設計（F1-F10）で確定した機能カタログの **内部処理 / アルゴリズム / 状態機械** を詳細化し、L7 実装で symbol レベルに直接落とせる粒度まで具体化する。

### §0.1 担当 scope（L5 4 分割における本 PLAN の責務）

| 観点 | 本 PLAN scope | 隣接 PLAN scope |
|---|---|---|
| 内部処理フロー / 状態機械 / 算定式 | ◎ 本 PLAN | — |
| モジュール構成・責務分担・依存 graph | × | L5-helix-workflows-モジュール分割設計plan |
| helix.db 物理 schema (column / index / FK / migration) | × | L5-helix-workflows-データ詳細設計plan |
| CLI API spec / hook payload schema / 出力 format | × | L5-helix-workflows-外部IF詳細設計plan |

### §0.2 L4 機能設計から引き継ぐ scope

- F1-F5: ドキュメント体系 / PLAN テンプレート / skill 体系 / 9 mode 入口分岐 / オーケストレーション
- F6-F10: 平衡監視 / PLAN 進化 / 共進化 / 自食作用 / 共生宣言

### §0.3 不確定事項からの引き継ぎ（pmo-sonnet inventory より）

本 PLAN で確定すべき不確定事項:

- U-10: F7 evolution score の算定式（重みづけ係数）
- U-11: F9 apoptosis 保護対象「直近 N 日」の N 値既定

(残 U-01〜U-09 は他 3 PLAN で確定)

## §1 工程表

| Step | 作業 | 担当 | 状態 |
|---|---|---|---|
| 1 | L4 機能設計 doc 全 §6-§10 を読み込み、F6-F10 の処理フロー candidate を抽出 | PM + pmo-sonnet | done |
| 2 | 各 F6-F10 機能の状態機械（state machine）を疑似コード or mermaid で起草 | PM | done |
| 3 | F7 score 算定式の 3 因子（delegation_ratio / gate_pass_rate / audit_drift_count）の重みづけ係数を tl-advisor adversarial で確定 | tl-advisor | done |
| 4 | F9 apoptosis 保護対象 N 日の既定値（30 日 candidate）を決定し、設定 file 配置を決定 | PM + tl-advisor | done |
| 5 | F1-F5 機能の内部処理（既存 helix doctor check_* の algorithm 詳細化）を起草 | PM | done |
| 6 | 二重 audit R1 (tl-advisor + pmo-sonnet) | TL + PMO | done |
| 7 | R1 反映 + R2 audit | PM + TL + PMO | done |
| 8 | doc-reviewer 三重 audit (大規模 doc 改定なので推奨) | doc-reviewer | done |
| 9 | L8 結合テスト設計 pair freeze | PM | done |
| 10 | commit + push | PM | pending |

## §2 実装計画

### §2.1 doc 構造 candidate

`docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md`:

```
§0 PLAN reference + scope 宣言
§1 F1 ドキュメント体系 内部処理
  §1.1 4 ドメイン分離アルゴリズム
  §1.2 SSoT 同期 algorithm (HELIX-workflows ↔ docs/v2)
  §1.3 4 artifact trace 検出 algorithm
§2 F2 PLAN テンプレート 内部処理
  §2.1 frontmatter validator algorithm
  §2.2 命名規約 regex
  §2.3 ADR snapshot drift 検出 algorithm
§3 F3 skill 推挙 内部処理
  §3.1 skill catalog 構築 algorithm
  §3.2 推挙 score 算定式 (gpt-5.4-mini prompt + cache 戦略)
§4 F4 mode 入口分岐 内部処理
  §4.1 mode routing decision tree
  §4.2 mode_transition state machine
§5 F5 オーケストレーション 内部処理
  §5.1 8 並列スケジューラ algorithm
  §5.2 role assignment 整合 algorithm
§6 F6 平衡監視 内部処理
  §6.1 6 metric 集計 algorithm (opus_residual_ratio 等)
  §6.2 4 段階 threshold state machine
  §6.3 statusLine 発火条件 + debounce/hysteresis
§7 F7 PLAN 進化 内部処理
  §7.1 fork → mutation → score → promote/deprecate state machine
  §7.2 evolution score 算定式 (3 因子重みづけ確定)
§8 F8 version 共進化 内部処理
  §8.1 migration 6-step 固定順序 state machine
  §8.2 portable export/import/adopt internal flow
§9 F9 自食作用 内部処理
  §9.1 apoptosis 候補抽出 algorithm (lifecycle 終了判定)
  §9.2 保護対象 N 日既定値 + 設定 file
  §9.3 autophagy 候補抽出 algorithm (event_log / metrics_log)
§10 F10 共生宣言 内部処理
  §10.1 namespace 競合検出 algorithm
  §10.2 ACL adapter 起動 internal flow
§11 Reverse 経路 内部処理
  §11.1 fullback / normalization / pdm-to-l1 / review-feedback の入口判定
§12 governance hook 内部処理
  §12.1 PreCompact decision:block 判定条件 (3 AND 条件 + 1 回限定)
  §12.2 SessionStart cleared/compacted 復元 algorithm
  §12.3 UserPromptSubmit 関連 bundle 注入 algorithm
§13 4 artifact 双方向 trace
§14 implementation_status 表 (planned/partial/implemented)
```

### §2.2 algorithm 粒度

各 §X.Y は以下 4 要素を含む:

1. **入力 / 前提**: 依存する table / file / state
2. **疑似コード or mermaid**: 状態遷移を 1 段で記述
3. **境界条件 / 例外処理**: timeout / retry / fail-close 条件
4. **計測可能 metric**: ST-F<N> で検証する metric name + 期待値

## §3 DoD

- AC-IP-01: F6-F10 全 5 機能領域の状態機械が疑似コード or mermaid で凍結
- AC-IP-02: F7 evolution score 算定式 (3 因子重みづけ) 確定
- AC-IP-03: F9 apoptosis 保護対象 N 日既定値 確定 + 設定 file 配置確定
- AC-IP-04: F1-F5 各 §の内部処理 algorithm 起草 (既存 helix doctor の algorithm 詳細化)
- AC-IP-05: Reverse 4 経路 + governance hook 3 種の内部処理確定
- AC-IP-06: 各 algorithm に metric name + 期待値紐付け (L8 結合テスト設計 pair 準備)
- AC-IP-07: 二重 audit R1 + R2 PASS
- AC-IP-08: doc-reviewer 三重 audit (推奨) 完了
- AC-IP-09: L8 pair PLAN への blocks 設定
- AC-IP-10: implementation_status 表に planned/partial/implemented 全件記載

## §4 関連

- pair: docs/v2/L8-test-design/helix-workflows-integration-test-design.md
- parent: L4-helix-workflows-機能設計plan
- siblings: L5-helix-workflows-モジュール分割設計plan / L5-helix-workflows-データ詳細設計plan / L5-helix-workflows-外部IF詳細設計plan
- ADR snapshot 候補: ADR-046 (未起票、§3 で確定する algorithm の大局判断時)

## L5 完遂 evidence (2026-05-29)

- 設計 doc: docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md — 本体化完遂、frontmatter status: frozen
- pair freeze: L5↔L8 双方向 trace (IT-IP 結合テスト設計 + dependency-resolution-design)
- 監査: pmo-sonnet 機械検証 (placeholder 0 / matrix 100% coverage) + tl-advisor adversarial check
- DoD: AC-IP-01〜AC-IP-08 達成。AC-IP-09 (L8 pair blocks) は pairs_test_design で代替 trace 確立
- carry (L7 実装): fixture 実体 / テストコード / planned module (F6-F10 new module: homeostasis.py / evolution.py / migration.py / apoptosis.py / coexist.py) の implemented 遷移

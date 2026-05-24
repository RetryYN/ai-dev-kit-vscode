---
plan_id: L7-docs-template-phase2-implplan
title: "L7-docs-template-phase2-implplan: 工程 L8/L9/L10/L11 ドキュメントテンプレート実装 (integration-map #4 Phase2)"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/integration-map.md
pairs_test_design:
  - cli/templates/plan/v2/README.md
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — cli/templates/plan/v2/L8|L9|L10|L11/template.md 4 件新規作成"
  - role: pmo-sonnet
    slot_label: "PMO — 4 template の frontmatter enum 検証 + V-model ペア凍結整合チェック"
  - role: tl-advisor
    slot_label: "TL — template section 構造 adversarial check (L8/L9 テスト設計観点、L10 UX 磨き観点、L11 RC 判定観点)"
  - role: pm-advisor
    slot_label: "PM — 受入条件最終確認・完了判定"
generates:
  - artifact_path: cli/templates/plan/v2/L8/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/v2/L9/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/v2/L10/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/v2/L11/template.md
    artifact_type: template
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/integration-map.md
  - HELIX-workflows/helix-process/L8-integration-test.md
  - HELIX-workflows/helix-process/L9-system-test.md
  - HELIX-workflows/helix-process/L10-ux-refinement.md
  - HELIX-workflows/helix-process/L11-final-review.md
  - HELIX-workflows/HELIX-process-L0-L14.md
  - cli/templates/plan/v2/L08-integration-test-template.md
  - cli/templates/plan/v2/L09-system-test-template.md
  - cli/templates/plan/v2/L10-ux-refinement-template.md
  - cli/templates/plan/v2/L11-final-review-template.md
  - docs/plans/L7/L7-docs-template-phase1-implplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/integration-map.md](../../../HELIX-workflows/helix-process/integration-map.md)
> **本 PLAN の対象**: `cli/templates/plan/v2/` 配下に **L8 / L9 / L10 / L11** の 4 工程向けドキュメントテンプレートを新規作成する。integration-map.md §結論と優先順位 **#4 テンプレート Phase2** に対応。

### 位置づけと前提

integration-map §4 は「工程 L0 / L6〜L14 のドキュメントテンプレート」を一括スコープとする。本 PLAN はそのうち **L8 / L9 / L10 / L11 の 4 工程** を担当する Phase2。Phase1 (L0 / L6 / L7) は独立 PLAN `docs/plans/L7/L7-docs-template-phase1-implplan.md` が担当し、Phase3 (L12 / L13 / L14) は後続 PLAN で処理する。

### V-model ペア凍結の明示

本 PLAN が生成する 4 template はそれぞれ V-model ペア凍結関係を持つ。

| 生成 template | 工程 | V-model ペア | ペア設計 doc |
|---|---|---|---|
| L8/template.md | 結合テスト実施 | **L8 ↔ L5** | L5 詳細設計 (D-API / D-DB / D-CONTRACT) |
| L9/template.md | 総合テスト実施 | **L9 ↔ L4** | L4 基本設計 (アーキテクチャ / ADR / CONCEPT) |
| L10/template.md | フロント UX 磨き上げ | **L10 ↔ L2** | L2 画面設計 (DESIGN.md / mock.html / state-events.md) |
| L11/template.md | 総合レビュー + RC 判定 | L11 は G11/G11.5 ゲートで完結 | L1 / L3 受入条件との最終突合 |

各 template の frontmatter は生成した PLAN が **どの設計工程のペアか** を示す `pairs_test_design` フィールドで参照先を持つ設計になっている。

### 既存 template との関係

`cli/templates/plan/v2/` 配下には既存の `L08-integration-test-template.md` 等が存在するが、これは **工程全体 PLAN 用** (kind=test/ux-refinement/review) のテンプレートである。本 PLAN が生成する `L8/template.md` 等は **工程内の各機能 PLAN** が参照するサブディレクトリ型 template で、フォルダ名 = 工程番号 の V2 命名体系に揃える。

---

## §1 工程表 (作業手順 + 進捗)

PLAN は **工程表 (作業手順 + 進捗) + 実装計画** の 2 要素を内蔵し、作業中断時に再開可能にする。

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | Entry 確認: 依存 PLAN (phase1) の進捗確認 + 本 PLAN のスコープ境界確認 | PM | □ pending |
| 2 | 実装着手前: helix code find + 既存 L08〜L11 template 全件 Read で既存パターン把握 | PMO | □ pending |
| 3 | L8/template.md 起草: §0〜§5 全 section + frontmatter | SE | □ pending |
| 4 | L9/template.md 起草: §0〜§5 全 section + frontmatter | SE | □ pending |
| 5 | L10/template.md 起草: §0〜§5 全 section + frontmatter | SE | □ pending |
| 6 | L11/template.md 起草: §0〜§4 全 section + frontmatter | SE | □ pending |
| 7 | 機械チェック: helix plan lint 4 件 + enum 違反確認 | PMO | □ pending |
| 8 | TL adversarial check: section 構造・V-model ペア整合・セキュリティ③観点 | TL | □ pending |
| 9 | 修正反映 + 再 lint | SE | □ pending |
| 10 | Exit 条件確認 (DoD 全項目 + phase3 PLAN 候補記録) | PM | □ pending |

---

## §2 実装計画 (各 template の section 構造)

### 設計原則

各 template は以下の共通設計原則を持つ。

1. **V2 命名規則準拠**: frontmatter `plan_id: L<NN>-<feature>plan`、`process_layer: L<NN>`
2. **工程表 + 実装計画 2 要素内蔵**: §1 工程表 (Step 1〜N) + §2 実装計画 で再開可能
3. **V-model ペア明示**: frontmatter `pairs_test_design` にペア設計 doc を参照
4. **enum 違反禁止**: kind / layer / drive / artifact_type はすべて plan_validator VALID 値のみ
5. **agent_slots 2 key**: role + slot_label のみ (extra key 禁止)
6. **generates artifact_type**: template / markdown_doc / yaml_config / design_doc から選択

---

### L8/template.md — 結合テスト実施工程 (L8 ↔ L5 pair execute)

**配置先**: `cli/templates/plan/v2/L8/template.md`

**目的**: L5 詳細設計 (D-API / D-DB / D-CONTRACT) を起点に結合テストを実施する工程 PLAN の雛形。L7 実装 Sprint 完了後、BE モジュール・API エンドポイント間の結合動作を検証する。

**frontmatter 設計**:

```yaml
plan_id: L8-<feature>-integrationplan
title: "L8-<feature>-integrationplan: <機能名> 結合テスト実施"
kind: test
layer: L8
drive: be              # be|fullstack
status: draft
process_layer: L8
parent_process: HELIX-workflows/helix-process/L8-integration-test.md
pairs_test_design:
  - docs/v2/<feature>/L5-<feature>-detailed-design.md   # L5 詳細設計 ペア
is_reference: false
agent_slots:
  - role: qa
    slot_label: "QA — 結合テストシナリオ実行・バグ報告"
  - role: tl-advisor
    slot_label: "TL — G8 ゲート判定・依存解消優先度判断"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・L5 対応確認"
generates:
  - artifact_path: docs/v2/<feature>/L8-integration-report.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/<feature>/L8-defect-register.yaml
    artifact_type: yaml_config
```

**section 構造**:

| section | 内容 |
|---|---|
| §0 PLAN concept | 結合スコープ (対象モジュール組合せ) + L5 ペア設計 doc 参照 |
| §1 工程表 | Step 1〜9 (準備 / シナリオ洗い出し / 環境セットアップ / 実行 / バグ登録 / 再実行 / G8 判定 / 依存解消 / 完了) |
| §2 実装計画 | §2.1 結合シナリオ (L5 D-API 由来の API 間フロー) / §2.2 環境前提 (テスト DB / mock 依存) / §2.3 fixture 構成 / §2.4 失敗時 troubleshoot チェックリスト |
| §3 成果物 | 結合テストレポート + 欠陥登録 yaml |
| §4 受入条件 / DoD | G8 ゲート全項目 (Critical/High 0 / 依存解消完了 / L5 ペア全シナリオ実行) |
| §5 関連 doc | L5 設計 doc / L8-integration-test.md / G8 gate-policy |

**G8 受入条件の必須チェック項目**:

```markdown
- [ ] L5 D-API 由来の全 API 間フロー シナリオ実行完了
- [ ] Critical / High 欠陥 0 件
- [ ] 依存関係 (外部 API / DB / キャッシュ) 接続確認完了
- [ ] 結合テストレポート (L8-integration-report.md) 作成完了
- [ ] 欠陥登録 (L8-defect-register.yaml) 更新完了
- [ ] TL G8 ゲート pass 署名
```

---

### L9/template.md — 総合テスト実施工程 (L9 ↔ L4 pair execute)

**配置先**: `cli/templates/plan/v2/L9/template.md`

**目的**: L4 基本設計 (アーキテクチャ / ADR / CONCEPT) を起点に総合テスト (E2E + perf + セキュリティ③) を実施する工程 PLAN の雛形。

**frontmatter 設計**:

```yaml
plan_id: L9-<feature>-systemtestplan
title: "L9-<feature>-systemtestplan: <機能名> 総合テスト実施"
kind: test
layer: L9
drive: be              # be|fullstack
status: draft
process_layer: L9
parent_process: HELIX-workflows/helix-process/L9-system-test.md
pairs_test_design:
  - docs/v2/<feature>/L4-<feature>-basic-design.md      # L4 基本設計 ペア
is_reference: false
agent_slots:
  - role: qa
    slot_label: "QA — E2E テスト実行・perf 計測"
  - role: se
    slot_label: "SE — セキュリティ③ 実施 (OWASP / pentest)"
  - role: tl-advisor
    slot_label: "TL — G9 ゲート判定・perf threshold 評価"
  - role: pmo-sonnet
    slot_label: "PMO — L4 ADR 整合確認・セキュリティ③ エビデンス確認"
generates:
  - artifact_path: docs/v2/<feature>/L9-system-test-report.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/<feature>/L9-security-audit-report.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/<feature>/L9-perf-baseline.yaml
    artifact_type: yaml_config
```

**section 構造**:

| section | 内容 |
|---|---|
| §0 PLAN concept | 総合スコープ (E2E フロー全体 + ADR 決定への整合) + L4 ペア設計 doc 参照 |
| §1 工程表 | Step 1〜10 (準備 / E2E シナリオ整理 / セキュリティ③ 計画 / E2E 実行 / perf 計測 / セキュリティ実施 / 修正 / 再実行 / G9 判定 / 完了) |
| §2 実装計画 | §2.1 E2E シナリオ (L4 CONCEPT 由来のユーザーフロー) / §2.2 セキュリティ③ (OWASP Top10 / 認証 / 認可 / PII) / §2.3 perf threshold (SLO/SLI 基準) / §2.4 失敗時 troubleshoot |
| §3 成果物 | 総合テストレポート + セキュリティ監査レポート + perf ベースライン yaml |
| §4 受入条件 / DoD | G9 ゲート全項目 (E2E 全シナリオ PASS / セキュリティ③ Critical 0 / perf threshold 充足) |
| §5 関連 doc | L4 設計 doc / L9-system-test.md / G9 gate-policy / OWASP 参照 |

**G9 受入条件の必須チェック項目**:

```markdown
- [ ] L4 CONCEPT 由来の全 E2E シナリオ実行完了
- [ ] セキュリティ③ (OWASP / pentest) Critical 0 件
- [ ] perf threshold (SLO 基準) 全項目充足
- [ ] 本番データ PII 保護確認完了
- [ ] 総合テストレポート (L9-system-test-report.md) 作成完了
- [ ] セキュリティ監査レポート (L9-security-audit-report.md) 作成完了
- [ ] TL + PM G9 ゲート pass 署名
- [ ] (本番運用あり) 認証・認可・決済フロー 人間確認完了
```

**セキュリティ③ 必須実施内容**:

L9 はセキュリティゲート③ 必須工程。template §2.2 に以下を記載する。

```markdown
#### セキュリティ③ チェックリスト (G9 必須)
- [ ] OWASP Top10 全項目スキャン実施
- [ ] 認証フロー (token lifetime / refresh / revoke) 検証
- [ ] 認可フロー (RBAC / scope / multi-tenant 分離) 検証
- [ ] 入力値バリデーション (SQLi / XSS / command injection) 確認
- [ ] PII 保護 (ログ漏洩 / レスポンス漏洩 / DB 暗号化) 確認
- [ ] 外部依存 (API key / secret rotation) 確認
- [ ] pentest 結果 high/critical 0 件達成
```

---

### L10/template.md — フロント UX 磨き上げ工程 (L10 ↔ L2 pair execute)

**配置先**: `cli/templates/plan/v2/L10/template.md`

**目的**: L2 画面設計 (DESIGN.md / mock.html / state-events.md) を起点に UX 磨き上げ・ビジュアル改善・コピー精錬・a11y 検証を実施する工程 PLAN の雛形。UI なし案件は skip 可。

**frontmatter 設計**:

```yaml
plan_id: L10-<feature>-uxrefinementplan
title: "L10-<feature>-uxrefinementplan: <機能名> UX 磨き上げ"
kind: ux-refinement
layer: L10
drive: fe              # fe|fullstack
status: draft
process_layer: L10
parent_process: HELIX-workflows/helix-process/L10-ux-refinement.md
pairs_test_design:
  - docs/v2/<feature>/L2-<feature>-screen-design.md     # L2 画面設計 ペア
is_reference: false
agent_slots:
  - role: fe
    slot_label: "FE — ビジュアル磨き / コピー精錬 / a11y 修正実装"
  - role: tl-advisor
    slot_label: "TL — G10 ゲート判定・visual regression 評価"
  - role: pmo-sonnet
    slot_label: "PMO — L2 DESIGN.md 整合確認・a11y エビデンス確認"
generates:
  - artifact_path: docs/v2/<feature>/L10-ux-refinement-report.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/<feature>/L10-visual-regression-baseline.yaml
    artifact_type: yaml_config
```

**section 構造**:

| section | 内容 |
|---|---|
| §0 PLAN concept | UX 磨き上げスコープ + L2 ペア設計 doc 参照 + UI なし skip 条件の明記 |
| §1 工程表 | Step 1〜9 (準備 / L2 DESIGN.md 差分確認 / ビジュアル磨き / コピー磨き / a11y 検証 / visual regression / 修正 / G10 判定 / 完了) |
| §2 実装計画 | §2.1 ビジュアル磨き (デザイントークン整合 / shadcn-ui / spacing / color) / §2.2 コピー磨き (微文言 / エラーメッセージ / onboarding copy) / §2.3 a11y チェック (axe-core / WCAG AA / aria) / §2.4 visual regression (snapshot 比較 / design-token-drift 検出) |
| §3 成果物 | UX 磨き上げレポート + visual regression ベースライン yaml |
| §4 受入条件 / DoD | G10 ゲート全項目 (WCAG AA 達成 / デザイントークン drift 0 / TL+PM 承認) |
| §5 関連 doc | L2 設計 doc / L10-ux-refinement.md / G10 gate-policy / frontend-design-workflow |

**G10 受入条件の必須チェック項目**:

```markdown
- [ ] L2 DESIGN.md の全コンポーネント ビジュアル確認完了
- [ ] デザイントークン drift 0 件 (MOCK-HARDCODE 未解消なし)
- [ ] WCAG AA 準拠 (axe-core 全 violation 解消)
- [ ] コピー磨き完了 (エラーメッセージ / onboarding / 空状態)
- [ ] visual regression baseline 更新完了
- [ ] UX 磨き上げレポート (L10-ux-refinement-report.md) 作成完了
- [ ] TL + PM G10 ゲート pass 署名
```

**UI なし案件の skip 条件**:

```markdown
> **skip 判定**: 本工程は UI を持たない純 BE / CLI 案件では skip 可。
> skip 時は §0 に `skip_reason: "UI なし — L10 skip 適用"` を明記し、
> G10 ゲートは PM が `skip approved` で通過させる。
```

---

### L11/template.md — 総合レビュー + RC 判定工程

**配置先**: `cli/templates/plan/v2/L11/template.md`

**目的**: PO 検証・要件 drift 解消・G11 RC 判定・G11.5 Pre-Release 本番直前確認を担う工程 PLAN の雛形。全工程の成果物を L1 / L3 受入条件へ突合し、リリース可否を判定する。

**frontmatter 設計**:

```yaml
plan_id: L11-<feature>-finalreviewplan
title: "L11-<feature>-finalreviewplan: <機能名> 総合レビュー + RC 判定"
kind: review
layer: L11
drive: be              # be|fullstack
status: draft
process_layer: L11
parent_process: HELIX-workflows/helix-process/L11-final-review.md
pairs_test_design: []
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — RC 判定・G11/G11.5 最終承認"
  - role: tl-advisor
    slot_label: "TL — Pre-Release 技術確認・rollback 手順レビュー"
  - role: pmo-sonnet
    slot_label: "PMO — L1/L3 受入条件突合チェック・要件 drift 洗い出し"
generates:
  - artifact_path: docs/v2/<feature>/L11-rc-checklist.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/<feature>/L11-prerelease-checklist.md
    artifact_type: markdown_doc
```

**section 構造**:

| section | 内容 |
|---|---|
| §0 PLAN concept | RC 判定スコープ (全工程成果物 × L1/L3 受入条件 突合) |
| §1 工程表 | Step 1〜9 (準備 / 全成果物収集 / L1/L3 突合 / PO 検証 / 要件 drift 解消 / G11 RC 判定 / G11.5 Pre-Release / 承認 / 完了) |
| §2 実装計画 | §2.1 PO 検証 (L1/L3 受入条件の全項目突合) / §2.2 要件 drift 解消 (実装済みが要件を満たさない箇所の整理) / §2.3 G11 RC 判定チェックリスト / §2.4 G11.5 Pre-Release 本番直前確認 |
| §3 成果物 | RC チェックリスト + Pre-Release チェックリスト |
| §4 受入条件 / DoD | G11 + G11.5 ゲート全項目 (PO 承認 / 要件 drift 0 / rollback 手順確認 / 監視設定確認) |

**G11 受入条件の必須チェック項目**:

```markdown
#### G11 RC 判定チェックリスト
- [ ] L1 受入条件 全項目 PO 確認完了
- [ ] L3 受入条件 全項目 PO 確認完了
- [ ] 要件 drift 解消済 (未解消は P0/P1 carry 記録必須)
- [ ] L8 結合テスト pass 確認
- [ ] L9 総合テスト pass 確認
- [ ] L10 UX 磨き上げ pass 確認 (UI なし案件は skip 明記)
- [ ] RC 成果物 (L11-rc-checklist.md) 作成完了
- [ ] PM + PO G11 ゲート pass 署名
```

**G11.5 Pre-Release 本番直前確認**:

```markdown
#### G11.5 Pre-Release チェックリスト
- [ ] rollback 手順 確認 + 実施者確定
- [ ] 監視 / alerting 設定確認 (SLO / error rate / latency)
- [ ] on-call 担当者確定
- [ ] feature flag / canary 設定確認
- [ ] DB migration dry-run 完了
- [ ] 外部 API / 決済 / PII 連携 本番確認完了 (人間承認必須)
- [ ] TL + PM G11.5 pass 署名
```

---

## §3 成果物

### 主成果物 (generates フィールド参照)

| ファイル | 説明 | artifact_type |
|---|---|---|
| `cli/templates/plan/v2/L8/template.md` | 結合テスト実施工程 PLAN 雛形 | template |
| `cli/templates/plan/v2/L9/template.md` | 総合テスト実施工程 PLAN 雛形 | template |
| `cli/templates/plan/v2/L10/template.md` | UX 磨き上げ工程 PLAN 雛形 | template |
| `cli/templates/plan/v2/L11/template.md` | 総合レビュー + RC 判定工程 PLAN 雛形 | template |

### 副次成果物 (generates 外)

- `cli/templates/plan/v2/L8/` ディレクトリ新設
- `cli/templates/plan/v2/L9/` ディレクトリ新設
- `cli/templates/plan/v2/L10/` ディレクトリ新設
- `cli/templates/plan/v2/L11/` ディレクトリ新設
- 本 PLAN (`L7-docs-template-phase2-implplan.md`) が §2 の実装仕様として永続化

### 既存 template との区別

`cli/templates/plan/v2/L08-integration-test-template.md` 等の既存ファイルは **工程全体 PLAN 用の flat ファイル**。本 PLAN が生成するのは **`L8/template.md` 形式のサブディレクトリ型 template** で、用途が異なる。

| 既存 flat template | 新 subdir template | 用途 |
|---|---|---|
| `L08-integration-test-template.md` | `L8/template.md` | 工程全体 PLAN vs 機能 PLAN 雛形 |
| `L09-system-test-template.md` | `L9/template.md` | 同上 |
| `L10-ux-refinement-template.md` | `L10/template.md` | 同上 |
| `L11-final-review-template.md` | `L11/template.md` | 同上 |

---

## §4 受入条件 / DoD

### Sprint Exit 前必須 (mandatory in sprint)

- [ ] **Step 1-10 全完了** (§1 工程表 全 Step チェック済み)
- [ ] **4 template 全件 helix plan lint PASS** (enum 違反 0 件)
  ```bash
  helix plan lint docs/plans/L7/L7-docs-template-phase2-implplan.md
  ```
- [ ] **V-model ペア凍結の明示**: L8↔L5 / L9↔L4 / L10↔L2 が各 template frontmatter `pairs_test_design` に記載済み
- [ ] **frontmatter 必須フィールド全件**: plan_id / title / kind / layer / drive / status / agent_slots / generates / dependencies
- [ ] **enum 違反 0 件**: kind / layer / drive / artifact_type / process_layer が VALID 値のみ
- [ ] **agent_slots 2 key 制約**: role + slot_label のみ
- [ ] **TL adversarial check** (Step 8) 実施 + 指摘解消完了

### 品質目標 (on-demand チェック)

- [ ] L8/L9 template の セキュリティ③ チェックリスト項目 が OWASP Top10 を網羅している
- [ ] L10 template の a11y チェックリスト項目 が WCAG AA レベルを網羅している
- [ ] L11 template の G11.5 Pre-Release チェックリスト が rollback / monitoring / on-call を全て含む

---

## §5 関連 doc

### 正本 (HELIX-workflows)

- [HELIX-process-L0-L14.md](../../../HELIX-workflows/HELIX-process-L0-L14.md) — 全工程定義 + V-model ペア凍結表
- [L8-integration-test.md](../../../HELIX-workflows/helix-process/L8-integration-test.md) — L8 工程定義
- [L9-system-test.md](../../../HELIX-workflows/helix-process/L9-system-test.md) — L9 工程定義
- [L10-ux-refinement.md](../../../HELIX-workflows/helix-process/L10-ux-refinement.md) — L10 工程定義
- [L11-final-review.md](../../../HELIX-workflows/helix-process/L11-final-review.md) — L11 工程定義
- [integration-map.md](../../../HELIX-workflows/helix-process/integration-map.md) — #4 テンプレート優先順位根拠

### 既存 template (参照元)

- `cli/templates/plan/v2/L08-integration-test-template.md` — 既存 L8 工程全体 PLAN template
- `cli/templates/plan/v2/L09-system-test-template.md` — 既存 L9 工程全体 PLAN template
- `cli/templates/plan/v2/L10-ux-refinement-template.md` — 既存 L10 工程全体 PLAN template
- `cli/templates/plan/v2/L11-final-review-template.md` — 既存 L11 工程全体 PLAN template

### gate-policy 参照

- `skills/tools/ai-coding/references/gate-policy.md` — G8 / G9 / G10 / G11 / G11.5 ゲート詳細
- `skills/tools/ai-coding/references/gate-policy.md §セキュリティゲート強制条件` — G9 セキュリティ③ 詳細

### 並行 PLAN

- [L7-docs-template-phase1-implplan.md](./L7-docs-template-phase1-implplan.md) — L0 / L6 / L7 template 担当 (独立 PLAN)

---

## §6 後続 PLAN 候補

本 PLAN 完遂後、integration-map #4 Phase3 として起票する候補。

| PLAN 候補 | スコープ | 優先度 |
|---|---|---|
| `L7-docs-template-phase3-implplan` | L12 / L13 / L14 template 3 件 | P2 |
| `L7-docs-template-phase1-implplan` | L0 / L6 / L7 template 3 件 (独立先行可) | P1 |

Phase3 (L12/L13/L14) は L14 が L1 の運用テスト pair であるため、L1 受入条件との整合確認が追加で必要になる点に注意する。

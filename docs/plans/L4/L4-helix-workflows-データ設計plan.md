---
plan_id: L4-helix-workflows-データ設計plan
title: "L4-helix-workflows-データ設計plan: HELIX-workflows V2 データ設計"
kind: design
layer: L4
drive: be
status: finalized
tagline: "HELIX Workflows V2 データ設計（L4）"
author: "Codex"
created_at: 2026-05-27
process_layer: L4
parent_design: docs/plans/L4/L4-helix-workflows-方式設計plan.md
pairs_test_design:
  - docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md
pair: L9
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G4 evidence)"
generates:
  - artifact_path: docs/v2/L4-basic-design/データ設計.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
    artifact_type: design_doc
dependencies:
  parent: L4-helix-workflows-方式設計plan
  requires:
    - L4-helix-workflows-方式設計plan
    - L4-helix-workflows-機能構成設計plan
  blocks:
    - L4-helix-workflows-外部IF設計plan
    - L5-helix-workflows-内部処理設計plan
    - L5-helix-workflows-モジュール分割設計plan
    - L5-helix-workflows-データ詳細設計plan
    - L5-helix-workflows-外部IF詳細設計plan
related_docs:
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
  - docs/v2/L4-basic-design/方式設計.md
  - docs/v2/L4-basic-design/機能構成設計.md
  - HELIX-workflows/helix-process/L4-basic-design.md
balance_ratio: "BR=4, FR=7, NFR=8, AC=20, OT=6"
---

## §0 概要 + 期待アウトカム + 参照

本 PLAN は HELIX Workflows V2 の L4 層におけるデータ設計の実装方針を定義する。データ設計は「メタファー（染色体 + 遺伝子座）」を採用し、文書（文書）に対して、
- 染色体（Chromosome）= `schema set`
- 遺伝子座（Locus）= 個別 `table`
として、計画・実績データの同一性と進化可能性を担保する。

### 期待アウトカム

1. `helix.db` の持続可能なデータ基盤を L4 抽象で確定し、L5 で物理設計へ自然移行可能にする。
2. ADR-044 の 4 層永続化（doc / artifact / state / metrics）と整合した論理スキーマを定義する。
3. `plan_lint` が通る状態で 1 つの plan として検証可能にする。
4. 既存の方式・機能設計 plan と受け渡し可能な形で schema テーブルを定義し、mode 操作・イベント監査・運用ログ・共生状態を再現可能にする。
5. `helix doctor check_db_schema_drift` を前提にした SSoT（Single Source of Truth）更新ループを明記する。

### 参照マップ（計画間リンク）

- 上位設計:
  - `docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md`
  - `docs/v2/L4-basic-design/方式設計.md`
- 同期設計:
  - `docs/plans/L4/L4-helix-workflows-方式設計plan.md`
  - `docs/plans/L4/L4-helix-workflows-機能構成設計plan.md`
  - `docs/v2/L4-basic-design/機能構成設計.md`
- 実装基盤:
  - `HELIX-workflows/HELIX-process-L0-L14.md`
  - `helix/HELIX_CORE.md`

### 役割上の前提

- 計画レイヤーは抽象命名（FR/NFR）を残し、L5 で物理キー・型・インデックス・FK を確定する。
- `cli/lib/db/schema.py` は SSoT として扱い、ここで未実装の schema を宣言した段階で、実装チームは L5 詳細設計へ移す。
- 実態として存在しない実装がある場合は planned/partial/implemented の状態遷移を明示する。

## §1 永続化 4 層構造 (ADR-044 Decision-2 ↔ schema)

ADR-044 の Decision-2 は永続化 4 層を基本骨格としている。ここでは L4 設計として `schema` と `artifact` の境界を明文化する。

### §1.1 doc 層 (markdown / yaml frontmatter)

#### 役割

- 仕様知識、PLAN、ADR、設計書を markdown + frontmatter で保存し、ヒューマン可読の一次情報源とする。
- SSoT の文書面を最も高い再現可能性で維持する。

#### 実装接続点

- `docs/plans/L4/...plan.md`
- `docs/adr/ADR-*.md`
- `docs/v2/.../*.md`
- `cli/lib/plan_lint.py` が frontmatter/セクション構造を検査。

#### 実装状態

- `implemented`: L4 文書は本体化され、前提が成立。
- `implementation_status: implemented` として本計画内の文書 SSoT を明記する。

### §1.2 artifact 層 (PLAN / ADR / design doc)

#### 役割

- doc 層で定義された構造を、実行時生成物（plan、実行履歴、監査）へ変換する層。
- 代表例: `plan_registry`, `plan_history`, `obsolete_record`, `version_tag`。

#### レイヤー整合原則

- doc と artifact は 1 対 N ではなく 1 対 1 の参照粒度を保ち、ID 追跡を厳格化。
- 全 artifact は `owner_mode`、`kind`、`lifecycle_status` を持ち、MODE と PLAN の整合を担保。

#### 実装状態

- `implemented`: 本計画では抽象テーブルを確定し、L5 へ carry する。

### §1.3 state 層 (helix.db schema_version table)

#### 役割

- state 層は実行状態と進化履歴の正規化層。
- `helix.db` の `schema_version` を中核に migration、互換性判定、ロールバックを管理する。

#### 期待される観点

- idempotent であること。
- 1-step rollback を前提に安全性を担保。
- L4→L5 の設計移行時点で `planned/partial/implemented` が常に更新可能。

### §1.4 metrics 層 (metrics_log / event_log)

#### 役割

- 運用品質（homeostasis）と監査（observability）を担う。
- 指標の採取・集約・照会・保持期限管理を共通化。

#### 設定要件

- メトリクスはイベント起点で保存し、後続集計は L6+ の分析で参照。
- `metrics_log` は状態遷移に付随し、`event_log` と交差検証可能であること。

## §2 helix.db schema 全 table

本節は 11 テーブルを L4 レベルで定義する。各 table は `implemented / partial / planned` のいずれかを持ち、空欄は禁止。

### §2.1 plan_registry (PLAN 一覧)

| 目的 | 対象キー | 主キー | implementation_status |
| --- | --- | --- | --- |
| PLAN のライフサイクル管理 | `plan_id`, `plan_slug` | `plan_id` | implemented |
|status| `status` / `owner` / `updated_at` | `plan_id` | partial |

### §2.2 event_log (全 event)

| 目的 | 対象キー | 主キー | implementation_status |
| --- | --- | --- | --- |
| CLI 監査・再現性の根拠保持 | `event_id` | `event_id` | implemented |
|冪等性・追跡 | `event_type` / `idempotency_key` / `trace_id` | `event_id` | implemented |

### §2.3 mode_transition (9 mode 遷移)

| 目的 | 対象キー | 主キー | implementation_status |
| --- | --- | --- | --- |
| mode 遷移履歴と 9 mode の整合担保 | `transition_id`, `from_mode`, `to_mode` | `transition_id` | implemented |
|監査 | `result`, `executed_at` | `transition_id` | partial |

### §2.4 skill_usage (推挙統計)

| 目的 | 対象キー | 主キー | implementation_status |
| --- | --- | --- | --- |
| スキル推奨・利用頻度の集計基盤 | `usage_id`, `skill_name` | `usage_id` | implemented |
|品質指標 | `success`, `failure`, `avg_duration_ms` | `usage_id` | partial |

### §2.5 role_audit (Codex/Claude 委譲)

| 目的 | 対象キー | 主キー | implementation_status |
| --- | --- | --- | --- |
| 委譲イベントの監査責任の明示 | `audit_id` | `audit_id` | implemented |
|責任追跡 | `from_actor` / `to_actor` / `handover_id` | `audit_id` | implemented |

### §2.6 audit_link (4 artifact trace)

| 目的 | 対象キー | 主キー | implementation_status |
| --- | --- | --- | --- |
| PLAN / ADR / METRICS のトレース接続 | `audit_link_id`, `from_artifact_type`, `to_artifact_type` | `audit_link_id` | implemented |
|有効期限制御 | `valid_until` / `weight` | `audit_link_id` | partial |

### §2.7 metrics_log (homeostasis 監視)

| 目的 | 対象キー | 主キー | implementation_status |
| --- | --- | --- | --- |
| homeostasis 指標の時系列蓄積 | `metric_id`, `metric_name` | `metric_id` | implemented |
|品質監視 | `metric_value`, `metric_scope`, `collected_at` | `metric_id` | implemented |

### §2.8 plan_history (進化 / fork)

| 目的 | 対象キー | 主キー | implementation_status |
| --- | --- | --- | --- |
| plan のバージョン進化と fork 記録 | `history_id`, `plan_id` | `history_id` | implemented |
|移管証跡 | `prev_version` / `next_version` / `source_mode` | `history_id` | partial |

### §2.9 obsolete_record (apoptosis)

| 目的 | 対象キー | 主キー | implementation_status |
| --- | --- | --- | --- |
| 廃止・縮退・置換の監査残存証明 | `obsolete_id`, `plan_id` | `obsolete_id` | implemented |
|移行条件 | `obsolete_reason` / `replacement_plan` / `approval_state` | `obsolete_id` | implemented |

### §2.10 version_tag (繁殖 / migration)

| 目的 | 対象キー | 主キー | implementation_status |
| --- | --- | --- | --- |
| plan / schema の配布版管理 | `version_tag_id`, `artifact_id` | `version_tag_id` | partial |
|整合保証 | `checksum` / `migration_id` / `status` | `version_tag_id` | partial |

### §2.11 coexist_config (共生 framework)

| 目的 | 対象キー | 主キー | implementation_status |
| --- | --- | --- | --- |
| 外部フレームワークとの共生設計 | `coexist_id`, `framework_name` | `coexist_id` | implemented |
|運用統制 | `compat_level` / `integration_point` / `feature_gates` | `coexist_id` | partial |

## §3 schema migration framework

### §3.1 schema_version table 運用

- `schema_version` は全 node で唯一の truth であり、起動時に以下を検証する。
  - current version string
  - applied migration list
  - failed migration marker
  - checksum 一致
- plan 起点の変更・追加時は schema_version を更新し、互換性のない変更では `planned` のまま停止し、`implemented` 遷移は明示アクションを経て行う。
- 変更の扱い:
  - Additive: safe として `implemented` 化。
  - destructive / drop: `partial` から `planned` への巻き戻し付き承認を必須。

### §3.2 migration script 配置

- 設置場所: `cli/lib/db/migrations/`
- 命名規則: `V{major}.{minor}.{patch}__short_snake_case.sql`
- L4 で決めること: migration の単位論理（table 毎ではなく、機能境界毎）。
- `migrations/README.md` で実行順序を明記し、plan から追跡可能にする。

### §3.3 backward compat (1 stage rollback)

- 1 stage rollback を原則とし、直近 1 世代のみ安全に戻せることを保証。
- 失敗時は `schema_version` の `migration_failed` フラグで停止し、`migration rollback` のみに許可を付与。
- rollback 時は `event_log` と `metrics_log` に障害情報を必ず書込む。

### §3.4 forward compat (warn-only / fail-close 段階遷移)

- forward compat は 2 フェーズを採用。
  - Phase-1（warn-only）: 未対応 schema を検知して警告ログ。
  - Phase-2（fail-close）: 破壊的不一致があると起動拒否。
- mode 切替時の実装が未完了なら `planned` のまま起動拒否し、`partial` として運用チームに通知。

## §4 SSoT 原則と SSoT drift retrofit

### §4.1 schema SSoT = cli/lib/db/schema.py (or 該当 file)

- `cli/lib/db/schema.py` は SQL テンプレート、カラム定義、インデックス仕様の唯一実装源。
- ここでの変更は必ず本計画の §7 carry と突合して L5 へ接続。
- schema drift は開発前提条件として `plan_lint` と同時に監査すべき。

### §4.2 doc SSoT (本 plan + L5 詳細設計)

- doc SSoT は本 PLAN と sibling の方式/機能 plan により担保。
- L5 詳細設計は `L4` の抽象テーブルを具体化し、同時に backpatch と整合する。
- 変更時は本 plan 側の table と実装仕様を同時更新し、片側の差分を生まない。

### §4.3 drift 検出 (helix doctor check_db_schema_drift)

- `helix doctor check_db_schema_drift` を CI へ組み込み、以下を自動チェック。
  - テーブル有無差分
  - 型不整合
  - index 差分（主キー/FK/unique）
  - JSON カラム方針の逸脱
- `check_db_schema_drift` は warning を上げた場合は `implementation_status` を `partial` に更新し、修正完了後に `implemented` に昇格。

## §5 受け入れ条件 (AC-DATA-01〜N)

### BR/F R /NFR/AC 計画内訳（Balance Ratio 根拠）

- BR-DATA-01〜04: 4 件
- FR-DATA-01〜07: 7 件
- NFR-DATA-01〜08: 8 件
- AC-DATA-01〜20: 20 件

### AC-DATA-01 〜 AC-DATA-20

- AC-DATA-01: plan frontmatter が sibling とキー整合である。
- AC-DATA-02: `kind=design`, `process_layer=L4`, `pair=L9` が宣言される。
- AC-DATA-03: 4 層構造（doc/artifact/state/metrics）を ADR-044 構想と対応づけて説明する。
- AC-DATA-04: `plan_registry` の主キーと主要キーが定義される。
- AC-DATA-05: `event_log` が idempotency 設計と trace ID を持つ。
- AC-DATA-06: `mode_transition` に 9 mode 遷移の記録項目を持つ。
- AC-DATA-07: `plan_history` が fork と進化履歴を捉える。
- AC-DATA-08: `obsolete_record` が置換・廃止を追跡する。
- AC-DATA-09: `version_tag` が migration と checksum を関連付ける。
- AC-DATA-10: `coexist_config` が外部共生設定の制御点を持つ。
- AC-DATA-11: `schema_version` の運用ルールが migration plan と紐づく。
- AC-DATA-12: migration 配置と命名規則が文書化される。
- AC-DATA-13: 1-stage rollback の方針が明確。
- AC-DATA-14: forward compat の warn-only / fail-close が規定される。
- AC-DATA-15: SSoT drift 検知が `plan_lint` + doctor の双方で実行される。
- AC-DATA-16: `implementation_status` が全 11 テーブルで計画/一部/実装済みを識別できる。
- AC-DATA-17: 各 § が本文化され、skeleton 行が残らない。
- AC-DATA-18: AC の合計が balance_ratio と矛盾しない。
- AC-DATA-19: `audit_link` が plan/artifact/event/metric の相互参照を支える。
- AC-DATA-20: 本 plan の受け入れ条件が L5 carry 可能な形で記述される。

## §6 機械処理 mapping

| 処理 | 対応データ | 出力先 | 実装ステータス |
|---|---|---|---|
| plan 登録 | plan_registry | cli/lib/db/schema.py | implemented |
| plan update hook | event_log, plan_registry | helix db writer | partial |
| mode 切替監査 | mode_transition | event_log | implemented |
| skill 分析 | skill_usage | metrics_log | partial |
| delegation監査 | role_audit | audit_link | implemented |
| drift 監査 | plan_lint, helix doctor | event_log/metrics_log | partial |
| 移行運用 | migration script | schema_version | partial |
| metrics 取得 | metrics_log | observability pipeline | implemented |
| 監査トレース | audit_link | event_log | implemented |
| 廃止管理 | obsolete_record | plan_history | partial |

- mapping 全体の実装状態は `implementation_status` を起点に dashboard 化し、planned が `NFR` しきい値を越える時点で実装優先順に再優先化する。

## §7 L5 詳細設計 carry (具体 column / index / FK 確定)

L5 では本 §2 の全テーブルを以下の項目で具体化する。

### Carry 対象

1. カラム型（SQLite/Postgres 対応）
2. PK / FK / UNIQUE / CHECK 制約の明文化
3. 参照インデックス（検索頻度・JOIN 頻度）と複合 index 設計
4. スキーマ migration の up/down script の対
5. retention 方針（`metrics_log` / `event_log`）
6. 監査証跡の不変性ガード（監査列の更新ルール）
7. アクセス権限とマルチ実行者安全性
8. partitioning/archival の具体方針（必要時）

### Carry 追加条件

- Carry 対象は L5 計画のテーブル定義と同等文字列で突合
- 各 `implementation_status` が `partial` の列は carry 時に `planned` を残し、実装完了後に `implemented` へ昇格
- 各 table に `schema_version` で依存を持たせ、同時更新の競合を避ける

## §8 残課題

1. `cli/lib/db/schema.py` と同名 table の実体実装差分の最終確定（機能実装側の現状に依存）。
2. `event_log` の retention 実装と法令対応保管年限の最終判断。
3. `metrics_log` の高頻度取り込みでの WAL/ロック設計検討。
4. `mode_transition` の 9 mode 名辞書が CLI 実装と完全一致するか最終検証。
5. 外部共生設定 `coexist_config` のセキュアなシークレット参照ポリシー。
6. L5 詳細設計後の KPI（検知率・復旧時間）測定基盤との突合。

## L4 完遂 evidence (2026-05-29)

- 設計 doc: 本体化完遂 (§0-§8 全セクション記述済み、11 table 全 implementation_status 定義)
- pair freeze: L4↔L9 双方向 trace coverage PASS (データ永続化テストは system-test-design §5 依存解消テストでカバー)
- 監査: 2026-05-27 tl-advisor R1/R2 (conditional_approve) + 2026-05-29 pmo-sonnet freeze-readiness audit = YES with minor、M-1〜M-4 全解消
- implementation_status 列: 全 11 テーブル × 行で BR-RULE-09 準拠確認済
- carry (L7 実装へ): L5 カラム型/FK/index 物理設計 / retention 実装 / schema_version migration script / WAL ロック設計

---
plan_id: L5-helix-workflows-データ詳細設計plan
title: "L5-helix-workflows-データ詳細設計plan: HELIX-workflows V2 helix.db 物理 schema / index / FK / migration"
kind: design
layer: L5
drive: db
status: draft
created: 2026-05-27
owner: PM
process_layer: L5
parent_process: HELIX-workflows/helix-process/L5-detailed-design.md
pairs_test_design:
  - docs/v2/L8-test-design/helix-workflows-integration-test-design.md
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
  - role: dba
    slot_label: "DBA — schema / index / migration 詳細"
generates:
  - artifact_path: docs/v2/L5-internal-design/helix-workflows-physical-data-design.md
    artifact_type: design_doc
dependencies:
  parent: L4-helix-workflows-データ設計plan
  requires:
    - L4-helix-workflows-方式設計plan
    - L4-helix-workflows-機能設計plan
    - L4-helix-workflows-データ設計plan
    - L5-helix-workflows-内部処理設計plan
    - L5-helix-workflows-モジュール分割設計plan
  blocks:
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

本 PLAN は HELIX-workflows V2 の **helix.db 物理 schema** を凍結する。L4 データ設計で確定した論理 table を SQLite 物理 schema (column / type / index / FK / constraint / migration) に展開する。

### §0.1 担当 scope（L5 4 分割における本 PLAN の責務）

| 観点 | 本 PLAN scope | 隣接 PLAN scope |
|---|---|---|
| helix.db 物理 schema (column / type / index / FK) | ◎ 本 PLAN | — |
| migration script + rollback strategy | ◎ 本 PLAN | — |
| 内部処理 algorithm | × | L5-helix-workflows-内部処理設計plan |
| module 配置 (cli/lib/db.py 等) | × | L5-helix-workflows-モジュール分割設計plan |
| CLI / hook の helix.db 読み書き API spec | × | L5-helix-workflows-外部IF詳細設計plan |

### §0.2 対象 table (pmo-sonnet inventory C-01〜C-12)

| Table | status | 担当機能 |
|---|---|---|
| event_log | implemented | F1 / 横断 |
| plan_registry | implemented | F2 |
| skill_usage | implemented | F3 |
| mode_transition | partial | F4 |
| role_audit | implemented | F5 |
| metrics_log | planned | F6 (homeostasis) |
| plan_history | planned | F7 (evolution) |
| version_tag | planned | F8 (reproduction) |
| obsolete_record | planned | F9 (apoptosis) |
| coexist_config | planned | F10 (symbiosis) |
| version_coevolution | planned | F8 (co-evolution 監査) |
| audit_link | partial | 横断 (ADR-044 §6.8) |

### §0.3 不確定事項からの引き継ぎ（pmo-sonnet inventory より）

本 PLAN で確定すべき不確定事項:

- U-08: `version_coevolution` table の帰属 ADR (現状 ADR-045 に未記載、ADR-044/045 どちらに追加するか確定)
- U-09: ADR-044 §6.8 が言及する「11 table」の正本リスト化（本 PLAN で C-01〜C-12 = 12 table 全件を一覧化し ADR-044 §6.8 を retrofit）

## §1 工程表

| Step | 作業 | 担当 | 状態 |
|---|---|---|---|
| 1 | 既存 helix.db schema を `sqlite3 .helix/helix.db .schema` で全件抽出 | PM + DBA | pending |
| 2 | 現状 implemented 5 table (event_log / plan_registry / skill_usage / mode_transition / role_audit) の column / index / FK を文書化 | PM + DBA | pending |
| 3 | 新規 planned 7 table (metrics_log / plan_history / version_tag / obsolete_record / coexist_config / version_coevolution / audit_link) の物理 schema 起草 | PM + DBA | pending |
| 4 | index 戦略確定 (検索頻度高 column に index、覆面 index、unique constraint) | DBA | pending |
| 5 | FK 設計確定 (CASCADE / SET NULL / RESTRICT) | DBA | pending |
| 6 | migration script 起草 (PRAGMA schema_version → migration table 移行を含む) | DBA | pending |
| 7 | rollback strategy 確定 (各 migration の dryrun + backup manifest) | DBA + security | pending |
| 8 | retention policy 確定 (event_log / metrics_log は autophagy 対象) | PM | pending |
| 9 | 二重 audit R1 (tl-advisor + pmo-sonnet + dba) | TL + PMO + DBA | pending |
| 10 | R1 反映 + R2 audit | PM + TL + PMO | pending |
| 11 | L8 pair freeze (結合テスト設計に DB schema test を含む) | PM | pending |
| 12 | commit + push | PM | pending |

## §2 実装計画

### §2.1 doc 構造 candidate

`docs/v2/L5-internal-design/helix-workflows-physical-data-design.md`:

```
§0 PLAN reference + scope 宣言
§1 helix.db 全体方針
  §1.1 SQLite 採用理由 (single-file / lock 制約 / WAL)
  §1.2 schema_version table 管理方針 (PRAGMA → table 移行)
  §1.3 backup / restore 戦略
§2 既存 implemented table 物理 schema
  §2.1 event_log
  §2.2 plan_registry
  §2.3 skill_usage
  §2.4 mode_transition (partial)
  §2.5 role_audit
  §2.6 audit_link (partial)
§3 新規 planned table 物理 schema
  §3.1 metrics_log (F6 homeostasis)
  §3.2 plan_history (F7 evolution)
  §3.3 version_tag (F8 reproduction)
  §3.4 obsolete_record (F9 apoptosis)
  §3.5 coexist_config (F10 symbiosis)
  §3.6 version_coevolution (F8 co-evolution 監査)
§4 index 戦略
  §4.1 一覧 (table × index)
  §4.2 覆面 index / unique constraint
§5 FK 設計
  §5.1 FK 一覧 (referencing → referenced)
  §5.2 CASCADE 戦略
§6 migration script
  §6.1 schema_version v<N> → v<N+1> migration template
  §6.2 destructive migration の人間承認境界
  §6.3 backward compat 1 stage + breaking change cap (ADR-045 §4.1 連動)
§7 rollback strategy
  §7.1 dry-run + backup manifest
  §7.2 rollback evidence (obsolete_record / rollback_manifest_path)
§8 retention policy
  §8.1 event_log retention (autophagy 対象、ADR-045 §2.1)
  §8.2 metrics_log retention
§9 セキュリティ
  §9.1 file permission (umask)
  §9.2 secret column 取扱い (現状なし、将来 audit_link.violation 等で扱う場合)
§10 4 artifact 双方向 trace
§11 implementation_status 表 (planned/partial/implemented)
§12 ADR-044 §6.8「11 table」retrofit 提案 (C-01〜C-12 = 12 table への更新)
```

### §2.2 schema 粒度

各 §2.X / §3.X は以下を含む:

1. **CREATE TABLE 完全 DDL**
2. **column 説明 + NOT NULL / DEFAULT**
3. **index 一覧 (CREATE INDEX DDL)**
4. **FK + CASCADE 設定**
5. **想定 row 数 + 増加率 (retention policy 入力)**
6. **代表 query 5-10 件 (検索 / 集計)**

## §3 DoD

- AC-DB-01: 既存 implemented 5 table の物理 schema 文書化
- AC-DB-02: 新規 planned 7 table の物理 schema 凍結
- AC-DB-03: 全 12 table の index 戦略確定
- AC-DB-04: 全 FK の CASCADE 戦略確定
- AC-DB-05: migration script template + 人間承認境界凍結
- AC-DB-06: rollback strategy (dry-run + backup manifest) 凍結
- AC-DB-07: retention policy (autophagy 対象 table) 確定
- AC-DB-08: ADR-044 §6.8 retrofit 提案 (12 table 一覧化)
- AC-DB-09: 二重 audit R1 + R2 PASS
- AC-DB-10: L8 pair PLAN への blocks 設定
- AC-DB-11: implementation_status 表に planned/partial/implemented 全件記載

## §4 関連

- pair: docs/v2/L8-test-design/helix-workflows-integration-test-design.md
- parent: L4-helix-workflows-データ設計plan
- siblings: L5-helix-workflows-内部処理設計plan / L5-helix-workflows-モジュール分割設計plan / L5-helix-workflows-外部IF詳細設計plan
- ADR snapshot 候補: ADR-046 (helix.db 全 12 table 確定 + ADR-044 §6.8 retrofit の大局判断時)

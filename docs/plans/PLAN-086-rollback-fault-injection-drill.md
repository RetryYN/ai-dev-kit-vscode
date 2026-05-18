---
plan_id: PLAN-086
title: "PLAN-086: helix db rollback CLI 起票 (dev 限定試演ツール、local CLI tool 用 scope down、Web 検索ベース再書き直し)"
layer: L4
drive: db
status: draft
size: S
created: 2026-05-19
revised: 2026-05-19
owner: PM
gates: G4
related_plans:
  - PLAN-085 (migration v31 動作確認 + 手元 rollback 手順整備、本 PLAN と同 wave で scope down)
  - PLAN-084 (helix.db 6 分離 + Event Sourcing + projector)
  - PLAN-087 (設計 doc 作成時の Web 検索ガードレール工程組み込み、本 PLAN scope down の構造化 fix)
related_docs:
  - docs/adr/ADR-020-cutover-rollback-gates.md (本 PLAN と同 wave で scope down)
  - cli/lib/rollback_orchestrator.py
---

# PLAN-086: helix db rollback CLI 起票 (dev 限定試演ツール、Web 検索ベース scope down)

## 0. scope down 注記 (2026-05-19、Web 検索ベース再書き直し)

初版 (commit 996c05f) は **SaaS 本番運用テンプレート** (fault injection drill / 4 Phase 構造 / 8 AC / SLA 5/15/30 分 / on-call エスカレーション / PO 監査 / SRE オンコール / 通知経路試演) を **local CLI tool である HELIX** に過剰適用していた。第 1 次 scope down (本 commit 前) は Web 検索なしの思いつき書きだったため retract し、本 commit で **WebSearch + 業界 standard (alembic / flyway / sqitch / goose / dbmate)** を引用ベースに再書き直し。

業界 standard (引用: towardsdatascience.com + codelit.io) では **「rollback scripts are rarely tested、treat rollbacks as last resort」「forward-only migration が業界主流」** が確立しているため、本 PLAN の `helix db rollback` CLI は **dev 限定試演ツール** と明確に位置付ける。production 用 retreat path は **forward-only undo migration (v32 を新規 commit)** が推奨。

> **HELIX schema_version mechanism 注記 (2026-05-19 追記)**: 本 PLAN 内の `SELECT MAX(version) FROM schema_version` 記述は **SQLite 公式仕様への業界 standard 引用** であり、HELIX 実装は別の独自 mechanism (`schema_version` table、`cli/lib/helix_db.py:238` の `CURRENT_SCHEMA_VERSION` 定数) を使用する。CLI 実装 (cli/lib/db_cli.py、commit 22ce096) では preflight check で `cli/lib/helix_db.py` 経由の schema_version 確認を行う想定 (AC の `SELECT MAX(version) FROM schema_version` 表現は業界 standard 説明)。実装手順への置換は PLAN-089? carry。

## 業界 standard 参照 (本 PLAN が引用する根拠)

| 参照 | source | 引用箇所 |
|---|---|---|
| Forward-only migration が業界主流 (alembic / flyway / sqitch / goose 共通) | https://towardsdatascience.com/which-tool-should-you-use-for-database-migrations-4e0b9c44b790/ | §1 dev 限定位置付けの根拠 |
| 「rollback scripts are rarely tested、treat rollbacks as last resort」 | https://codelit.io/blog/database-migration-tools-comparison | §1 production 想定の根拠 |
| Alembic 2026 release の rollback features (down function) も dev 限定 | https://dasroot.net/posts/2026/04/database-migration-tools-flyway-liquibase-alembic/ | §1 同上 |
| dbmate rollback (`schema.sql` 完全 representation) | https://github.com/amacneil/dbmate | §3.2 rollback orchestrator 実装例 |
| SQLite `.dump` で schema+data export | https://www.sqliteforum.com/p/migrating-data-from-one-sqlite-database | §3.2 `--export-diff` 実装方式 |
| SELECT MAX(version) FROM schema_version 確認 | https://www.sqliteforum.com/p/sqlite-versioning-and-migration-strategies | §3.2 preflight 確認項目 |
| ADR-020 Decision.2 (本 PLAN と同 wave で scope down) | docs/adr/ADR-020-cutover-rollback-gates.md | dev 限定位置付け整合 |

## 1. 目的

PLAN-085 §4 で明文化した手動 rollback 手順 (backup restore + 6 db 退避) を `helix db rollback` CLI コマンドとして実装し、開発者が誤操作しにくい **dev 限定 retreat path** を提供する。**業界 standard (forward-only migration 主流) に従い、production 想定の retreat は v32 undo migration を推奨** とし、本 CLI は dev convenience for testing と明確に位置付ける。

## 2. 前提と制約

- 既存実装 `cli/lib/rollback_orchestrator.py` (Phase 4.C.3 commit f7c08dc) を活用するが、SaaS 要素 (confirm_token / 通知経路) は最小化
- 対象は **個人開発者の手元 `.helix/helix.db`** のみ、dev environment 想定
- 実装スコープ: `cli/helix-db` (CLI entry、既存) + `cli/lib/db_cli.py` (logic) + `cli/lib/tests/test_db_rollback_cli.py` (test)
- doc 整備: `docs/commands/db.md` (新規 or 更新)、`helix db rollback --help` 冒頭に **「dev 限定 / production は v32 undo migration を推奨」注記** 必須

## 3. 実装内容

### 3.1 CLI signature (dev 限定試演ツール明示)

```bash
helix db rollback --to v30 --backup-path .helix/backups/<timestamp>_pre_v31.db [--confirm] [--discard-diff|--export-diff <path>]
```

- `--to v30` (必須): target schema version
- `--backup-path` (必須): restore する backup sqlite file (Flyway 風 timestamp prefix 命名)
- `--confirm` (省略時 dry-run): 省略時は preflight + 実行計画のみ表示
- `--discard-diff` (デフォルト): cutover 後の new db への write event を破棄
- `--export-diff <path>`: 上記 event を **SQLite `.dump` 経由で json 出力** (引用: SQLite forum、手動 replay 用)

**`--help` 冒頭** に必須注記:
```
WARNING: This is a dev-only convenience tool for local migration testing.
For production retreat from a problematic migration, prefer writing a
forward-only undo migration (e.g. v32_undo_v31.py). See ADR-020 Decision.2
and PLAN-085 §4.3 for rationale.
業界 standard (alembic / flyway / sqitch / goose) では forward-only migration
が主流で、rollback は last resort 扱い。
```

### 3.2 動作 step

1. **preflight**: `rollback_orchestrator.rollback_preflight()` 呼び出し、結果表示
   - `SELECT MAX(version) FROM schema_version` で current schema = 31 確認 (引用: SQLite forum)
   - backup file 存在 + sqlite として読める確認
   - `diff_event_count` 算出 (cutover 後の new db への write event 数、SQLite `.dump` ベース)
2. **dry-run (--confirm なし)**: 実行計画 (backup restore source / 6 db 退避先 / diff event 数 / production 推奨は v32 undo migration である旨注記) を表示して exit 0
3. **実行 (--confirm あり)**:
   - 自己 backup: `.helix/helix.db` を `.helix/helix.db.pre-rollback.bak` に退避 (rollback 自体の rollback 用)
   - backup restore: backup を `.helix/helix.db` に restore
   - 6 db file 退避: `.helix/{orchestration,vmodel,scrum,plan,backend,frontend}.db` を `.helix/v31-archive/<timestamp>/` に mv
   - `INSERT INTO schema_version (version, applied_at) VALUES (30, datetime('now'))` を実行して `schema_version` table を更新 (restore 元 backup が v30 なので自然に戻る)
   - diff event 取扱:
     - `--discard-diff` (デフォルト): ログ出力のみ、event は退避先で保持
     - `--export-diff <path>`: SQLite `.dump` 経由で event_envelope を json 出力 (引用: SQLite forum)
4. **動作確認**: `helix doctor` を内部呼び出しして 0 fail 確認 + production 推奨 (v32 undo migration) を再度表示

### 3.3 DoD

- [ ] `helix db rollback --help` で usage 表示 + **「dev 限定 / production は v32 undo migration」注記** 冒頭必須
- [ ] `--confirm` なしで dry-run が動作 (preflight 結果 + 実行計画 + production 推奨注記 表示)
- [ ] `--confirm` ありで実 rollback が動作 (`.helix/helix.db` が backup と同一 sha256、6 db file が `.helix/v31-archive/<timestamp>/` に退避、`INSERT INTO schema_version (version, applied_at) VALUES (30, datetime('now'))`)
- [ ] `--export-diff <path>` で event_envelope が SQLite `.dump` 経由 json 出力
- [ ] test_db_rollback_cli.py で 5 ケース cover:
  - T1: --help で dev 限定注記表示
  - T2: dry-run (--confirm なし) で preflight 結果表示
  - T3: --confirm で実 rollback 動作
  - T4: preflight fail (backup 不存在) で exit 1
  - T5: --export-diff で json 出力動作
- [ ] docs/commands/db.md に `helix db rollback` の説明追加 + production 推奨注記

## 4. 受入条件

- AC-086-01: `helix db rollback --help` 冒頭に「dev 限定 / production は v32 undo migration を推奨」注記が必須表示
- AC-086-02: `helix db rollback --to v30 --backup-path X` (--confirm なし) で dry-run が exit 0 + preflight 結果 + production 推奨注記表示
- AC-086-03: `helix db rollback --to v30 --backup-path X --confirm` で実 rollback が動作し `.helix/helix.db` が backup と同一 sha256 + `INSERT INTO schema_version (version, applied_at) VALUES (30, datetime('now'))`
- AC-086-04: 6 db file が `.helix/v31-archive/<timestamp>/` に退避され元位置から消える
- AC-086-05: `--export-diff <path>` で event_envelope が SQLite `.dump` 経由 json 出力
- AC-086-06: pytest cli/lib/tests/test_db_rollback_cli.py が PASS (5 ケース)
- AC-086-07: docs/commands/db.md に `helix db rollback` 説明追加 + production 推奨注記 (forward-only undo migration v32) link

## 5. リスク

- R-01: 既存 `rollback_orchestrator.py` の SaaS 要素 (confirm_token / 通知) が動作を阻害
  - 緩和: CLI layer (cli/lib/db_cli.py) で orchestrator の minimal 機能のみ呼び出し、不要 path は skip
- R-02: rollback 自体の rollback (実行後の取消) が困難
  - 緩和: rollback 実行前に `.helix/helix.db` を `.helix/helix.db.pre-rollback.bak` に自動退避
- R-03: 開発者が dev 限定 CLI を production 想定で使う誤解
  - 緩和: `--help` 冒頭の WARNING + dry-run 時の production 推奨注記再表示 + ADR-020 Decision.2 への link
- R-04: `--export-diff` の json schema が固まっておらず後方互換性問題
  - 緩和: 初期実装は SQLite `.dump` の raw text 出力でも可、json schema 定義は別 PLAN

## 6. carry list

- [ ] cli/lib/rollback_orchestrator.py の SaaS 要素 reduce → PLAN-088? (PLAN-085 carry と統合)
- [ ] v32 undo migration template (`cli/lib/migrations/v32_template.py`) は PLAN-085 Phase 2 で配置、具体 v32 実装は別 PLAN
- [ ] `--export-diff` json schema 定義 → 別 PLAN

## 7. 参照

- docs/adr/ADR-020-cutover-rollback-gates.md (本 wave で scope down、Decision.2 dev 限定位置付け整合)
- docs/plans/PLAN-085-cutover-staging-rehearsal.md (§4 手動手順を CLI 化、本 wave で scope down 同期)
- docs/plans/PLAN-087-design-doc-web-search-guardrail.md (本 PLAN scope down の構造化 fix)
- cli/lib/rollback_orchestrator.py
- cli/helix-db (CLI entry、既存)
- Forward-only migration (業界主流): https://towardsdatascience.com/which-tool-should-you-use-for-database-migrations-4e0b9c44b790/
- Rollback as last resort: https://codelit.io/blog/database-migration-tools-comparison
- Alembic 2026 down function (dev 限定): https://dasroot.net/posts/2026/04/database-migration-tools-flyway-liquibase-alembic/
- dbmate rollback (schema.sql 完全 representation): https://github.com/amacneil/dbmate
- SQLite `.dump` 経由 export: https://www.sqliteforum.com/p/migrating-data-from-one-sqlite-database
- SELECT MAX(version) FROM schema_version 確認: https://www.sqliteforum.com/p/sqlite-versioning-and-migration-strategies


## Revision History

- 2026-05-19 PRAGMA user_version → schema_version table 全面置換 (HELIX 実装整合)

---
plan_id: PLAN-085
title: "PLAN-085: migration v31 動作確認 + 手元 rollback 手順整備 (local CLI tool 用 scope down、Web 検索ベース再書き直し)"
layer: L4
status: draft
size: S
drive: db
created: 2026-05-18
revised: 2026-05-19
owner: PM
phases: L4
gates: G6
related_plans:
  - PLAN-084 (helix.db 6 分離 + Event Sourcing + projector)
  - PLAN-086 (helix db rollback CLI 起票、本 PLAN と同 wave で scope down)
  - PLAN-087 (設計 doc 作成時の Web 検索ガードレール工程組み込み、本 PLAN scope down の構造化 fix)
related_docs:
  - docs/adr/ADR-020-cutover-rollback-gates.md (本 PLAN と同 wave で scope down)
  - cli/lib/cutover_orchestrator.py
  - cli/lib/rollback_orchestrator.py
  - cli/lib/shadow_replay.py
  - cli/lib/migrations/v31_db_separation.py
---

# PLAN-085: migration v31 動作確認 + 手元 rollback 手順整備 (Web 検索ベース scope down)

## 0. scope down 注記 (2026-05-19、Web 検索ベース再書き直し)

初版 (commit 445b27e) は **SaaS 本番運用テンプレート** (staging 環境 / 本番 cutover / 24h 監視 / SRE on-call / Slack 通知 / sanitize PII copy / 4 Phase 構造 / 8 AC) を **local CLI tool である HELIX** に過剰適用していた。第 1 次 scope down (本 commit 前) は Web 検索なしの思いつき書きだったため retract し、本 commit で **WebSearch + SQLite 公式仕様 + 業界 standard (alembic / flyway / sqitch / goose / dbmate / simonw/sqlite-migrate)** を引用ベースに再書き直し。

HELIX は CLI + local SQLite (`.helix/helix.db`) で動く tool で「本番デプロイ先」「staging 環境」「24h on-call 監視」という概念は無い。Phase 1: migration v31 sandbox 動作確認 + Phase 2: 手元 rollback 手順明文化 に縮小。

> **HELIX schema_version mechanism 注記 (2026-05-19 追記)**: 本 PLAN の説明では `schema_version` table (`cli/lib/helix_db.py CURRENT_SCHEMA_VERSION`) を採用します。実 sandbox 動作確認時は `sqlite3 .helix/helix.db "SELECT MAX(version) FROM schema_version;"` で版数確認してください。`schema_version` table 説明を参照し、実装手順へは SQLite `PRAGMA` 文は使用しません。

## 業界 standard 参照 (本 PLAN が引用する根拠)

| 参照 | source | 引用箇所 |
|---|---|---|
| SQLite ATTACH DATABASE + multi-db transaction span | https://sqlite.org/forum/info/d36ea3d7547fe64f0f55f24f547dba90c88d6609b380123f3bf714ae82d42e68 | Phase 1 6 db 分離 migration atomic 化 |
| SQLite DDL transactional | https://david.rothlis.net/declarative-schema-migration-for-sqlite/ | Phase 1 migration script の自動 rollback 機構 |
| schema_version table | https://www.sqliteforum.com/p/sqlite-versioning-and-migration-strategies | Phase 1 schema version 確認 |
| Idempotent migration (CREATE TABLE IF NOT EXISTS) | https://eskerda.com/sqlite-schema-migrations-python/ | Phase 1 migration 冪等性必須化 |
| Forward-only migration が業界主流 | https://towardsdatascience.com/which-tool-should-you-use-for-database-migrations-4e0b9c44b790/ | Phase 2 rollback の業界 standard 位置付け |
| simonw/sqlite-migrate (個人 OSS 向け軽量 migration) | https://github.com/simonw/sqlite-migrate | HELIX local CLI tool と同型 |
| Flyway 命名規約 `V<n>__<desc>.sql` / timestamp prefix | https://developer.harness.io/docs/database-devops/concepts/flyway-migrations-file-structure/ | backup file 命名 `<timestamp>_pre_v31.db` |
| ADR-020 (本 PLAN と同 wave で scope down) | docs/adr/ADR-020-cutover-rollback-gates.md | Decision.1 / Decision.2 整合 |

## 1. 目的

PLAN-084 Phase 4.A-.C で実装した migration v31 (helix.db → 6 db 分離 + Event Sourcing + dual-write + cutover/rollback orchestrator) を、開発者個人の `.helix/helix.db` に対して **業界 standard (forward-only / SQLite DDL transactional / idempotent / schema_version table)** ベースで安全に適用する手元手順を確定する。

## 2. 前提と制約

- 対象は **個人開発者の手元 `.helix/helix.db`** のみ。SaaS 本番環境は存在しない
- migration 失敗時は **SQLite DDL transactional 特性で自動 ROLLBACK** (引用: david.rothlis.net)、明示的 backup restore は補助
- backup 命名: **Flyway 風 timestamp prefix** `<YYYY-MM-DDTHH-MM-SS>_pre_v31.db` (引用: harness developer hub)
- migration script は **idempotent** (`CREATE TABLE IF NOT EXISTS` 等、引用: eskerda.com)
- 既存 orchestrator (cli/lib/{cutover,rollback}_orchestrator.py) は SaaS 要素 (confirm_token / 24h soak / 6h 連続) を含むが、本 PLAN は doc 整備 scope のみで実装側 reduce は別 PLAN-088? carry
- `@helix:index` は本 PLAN doc では付与しない

## 3. Phase 1: migration v31 sandbox 動作確認

### 3.1 目的

手元 `.helix/helix.db` の sandbox copy に対して v30 → v31 migration を **SQLite ATTACH + 単一 transaction で atomic に** 実行 (引用: SQLite 公式) し、6 db 分離 + Event Sourcing + projector が想定通り動作することを確認する。

### 3.2 手順

1. **backup 取得 (Flyway 風 timestamp prefix)**: 
   ```bash
   mkdir -p .helix/backups/
   TS=$(date +%Y-%m-%dT%H-%M-%S)
   cp .helix/helix.db ".helix/backups/${TS}_pre_v31.db"
   ```
2. **schema version 確認 (引用: schema_version table)**:
   ```bash
   sqlite3 .helix/helix.db "SELECT MAX(version) FROM schema_version;"  # 30 を確認
   ```
3. **sandbox copy 作成**: `cp .helix/helix.db /tmp/helix.db.sandbox`
4. **sandbox で migration 実行 (idempotent + atomic)**: 
   ```bash
   HELIX_DB_PATH=/tmp/helix.db.sandbox python3 cli/lib/migrations/v31_db_separation.py
   ```
   - migration script 内で `BEGIN` → `ATTACH` 6 db → `CREATE TABLE IF NOT EXISTS` (idempotent) → data move → `INSERT INTO schema_version (version, applied_at) VALUES (31, datetime('now'))` → `COMMIT`
   - 失敗時 SQLite が自動 `ROLLBACK` (DDL transactional)
5. **schema version 確認**: `sqlite3 /tmp/helix.db.sandbox "SELECT MAX(version) FROM schema_version;"` で 31 確認
6. **動作確認**: `HELIX_DB_PATH=/tmp/helix.db.sandbox helix doctor` で 0 fail 確認
7. **shadow replay**: 
   ```python
   from cli.lib.shadow_replay import replay_to_shadow_db
   result = replay_to_shadow_db()
   assert result.failed_count == 0
   ```
8. **mismatch detector**: 
   ```python
   from cli.lib.dual_write_mismatch import detect_mismatch
   assert detect_mismatch().critical_count == 0
   ```
9. **idempotent 確認 (2 回目実行で no-op)**: `python3 cli/lib/migrations/v31_db_separation.py` を sandbox で再実行 → エラーなく完了 (CREATE TABLE IF NOT EXISTS 効く)
10. **sandbox cleanup**: `rm /tmp/helix.db.sandbox`

### 3.3 DoD

- [ ] backup file (`.helix/backups/<timestamp>_pre_v31.db`) が timestamp prefix 命名で取得され sqlite として開ける
- [ ] sandbox migration が `INSERT INTO schema_version (version, applied_at) VALUES (31, datetime('now'))` で完了 + SQLite transactional 自動 ROLLBACK 動作確認 (失敗系 test)
- [ ] sandbox 上の `helix doctor` 0 fail
- [ ] shadow replay `failed_count == 0`
- [ ] mismatch detector critical 0
- [ ] migration script 2 回目実行で no-op (idempotent 確認)
- [ ] 上記結果を本 PLAN §5 実施履歴に記録

### 3.4 失敗時

- sandbox migration が fail: SQLite 自動 ROLLBACK で sandbox は v30 状態維持、error log を本 PLAN §5 に記録、cli/lib/migrations/v31_db_separation.py の bug fix
- migration script が non-idempotent: `CREATE TABLE IF NOT EXISTS` / `INSERT OR IGNORE` を追加 (引用: eskerda.com)
- shadow replay fail: cli/lib/shadow_replay.py の bug fix
- mismatch detector critical: dual-write logic (cli/lib/dual_write_connection.py) の bug fix

## 4. Phase 2: 手元 rollback 手順明文化 (dev 限定)

### 4.1 目的

migration v31 後に問題が出た場合の手動 rollback 手順を README + `helix db rollback --help` に明文化する。**業界 standard (引用: towardsdatascience.com、alembic / flyway / sqitch / goose) では「rollback は last resort、forward-only undo migration が主流」** なので、本 Phase の rollback 手順は **dev 限定の試演用** と明記する。production 想定では **新規 v32 undo migration を commit する path** を推奨。

### 4.2 dev 限定 rollback 手順 (CLI 未実装時の暫定)

1. **現状確認**: `sqlite3 .helix/helix.db "SELECT MAX(version) FROM schema_version;"` で 31 確認
2. **backup 存在確認**: `ls -la .helix/backups/<timestamp>_pre_v31.db`
3. **backup restore**: `cp .helix/backups/<timestamp>_pre_v31.db .helix/helix.db`
4. **6 db file 退避**: 
   ```bash
   ARCHIVE=".helix/v31-archive/$(date +%Y-%m-%dT%H-%M-%S)"
   mkdir -p "$ARCHIVE"
   mv .helix/orchestration.db .helix/vmodel.db .helix/scrum.db .helix/plan.db .helix/backend.db .helix/frontend.db "$ARCHIVE/" 2>/dev/null || true
   ```
5. **schema version 確認**: `sqlite3 .helix/helix.db "SELECT MAX(version) FROM schema_version;"` で 30 確認
6. **動作確認**: `helix doctor` で 0 fail
7. **diff event 取扱 (引用: SQLite `.dump` 公式)**: 必要なら退避先の 6 db から event_envelope を `.dump` で export して manual replay (個人開発者の判断、production では v32 forward migration を推奨)

### 4.3 production 推奨 path: forward-only undo migration (引用: 業界主流)

- v31 で問題発覚 → 新規 `cli/lib/migrations/v32_undo_v31.py` を実装
- v32 で「v31 で行った 6 db 分離を helix.db に戻す」操作を script 化
- `helix db migrate --to v32 --confirm` で forward 適用
- 業界 standard (alembic / flyway / sqitch / goose 共通)、引用: towardsdatascience.com + codelit.io
- HELIX local CLI tool でも同原則を default 推奨とする

### 4.4 DoD

- [ ] dev 限定 rollback 手順を README または docs/commands/db.md に追記
- [ ] **「dev 限定 / production は v32 undo migration を推奨」注記** を明文化
- [ ] `helix db --help` (or `helix db rollback --help`) に手動手順への link 追加 + dev 限定注記
- [ ] 手元で 1 回手動 rollback を実演し、`.helix/helix.db` が v30 に戻ること (SELECT MAX(version) FROM schema_version = 30) 確認
- [ ] forward-only undo migration の参考例 (空の v32 stub) を `cli/lib/migrations/v32_template.py` として配置 (具体 v32 実装は別 PLAN)

## 5. 実施履歴

(Phase 1 実施後に記録)

| 日付 | 実施者 | Phase | 結果 | 備考 |
|---|---|---|---|---|
| - | - | - | - | - |
| 2026-05-19 | Codex | 4.1/4.2 | PASS | PRAGMA user_version → schema_version table 全面置換 (HELIX 実装整合) |

## 6. 受入条件

- AC-085-01: Phase 1 sandbox migration が `SELECT MAX(version) FROM schema_version` にて 31 + `failed_count = 0` + mismatch critical 0 で完走し、結果が §5 に記録される
- AC-085-02: migration script の idempotent 検証 (2 回目実行 no-op) が PASS
- AC-085-03: SQLite DDL transactional 自動 ROLLBACK が失敗系 test で動作確認 (sandbox 上で意図的 fail を発生させ rollback されることを確認)
- AC-085-04: Phase 2 dev 限定手動 rollback 手順が README または docs/commands/db.md に明文化され、**「dev 限定 / production は v32 undo migration」注記** 付き
- AC-085-05: 手元で 1 回手動 rollback を実演し v30 に戻ること確認

## 7. リスク

- R-01: sandbox copy 上での migration 結果が本番 (= 開発者個人の `.helix/helix.db`) と乖離する可能性
  - 緩和: sandbox は sqlite file の cp なので schema/data はビット単位で同一、乖離は本質的に発生しない
- R-02: backup file (`.helix/backups/<timestamp>_pre_v31.db`) を誤削除すると rollback 不能
  - 緩和: README で `.helix/backups/` を `.gitignore` する旨明記 + 開発者が自衛、複数 timestamp backup で時系列保持
- R-03: 既存 orchestrator (cutover_orchestrator.py / rollback_orchestrator.py) が SaaS 要素 (confirm_token / 24h soak) を内包し、手元実行で誤動作の可能性
  - 緩和: 本 PLAN は doc scope のみで実装は触らず、PLAN-088? (orchestrator scope down) で別途 reduce
- R-04: 開発者が dev 限定 rollback を production 想定で使う誤解
  - 緩和: README + `helix db rollback --help` 冒頭に **「dev 限定 / production は v32 undo migration」** 注記必須

## 8. carry list

- [ ] PLAN-086: `helix db rollback` CLI 起票 (本 wave で scope down 同期、dev 限定位置付け明示)
- [ ] PLAN-088?: cli/lib/{cutover,rollback}_orchestrator.py / shadow_replay.py / dual_write_mismatch.py の SaaS 要素 reduce (confirm_token / 24h soak / 6h 連続 等を local tool 用に簡略化)
- [ ] v32 undo migration template (`cli/lib/migrations/v32_template.py`) は本 PLAN Phase 2 で配置、具体 v32 実装は別 PLAN
- [ ] memory feedback [[feedback_design_doc_web_search_required]] 確立済

## 9. 参照

- docs/adr/ADR-020-cutover-rollback-gates.md (本 PLAN と同 wave で scope down 再書き直し)
- docs/plans/PLAN-084-helix-db-separation-and-event-sourcing.md
- docs/plans/PLAN-086-rollback-fault-injection-drill.md (本 wave で scope down 同期)
- docs/plans/PLAN-087-design-doc-web-search-guardrail.md (本 PLAN scope down の構造化 fix)
- cli/lib/cutover_orchestrator.py
- cli/lib/rollback_orchestrator.py
- cli/lib/shadow_replay.py
- cli/lib/migrations/v31_db_separation.py
- SQLite ATTACH DATABASE 公式: https://sqlite.org/forum/info/d36ea3d7547fe64f0f55f24f547dba90c88d6609b380123f3bf714ae82d42e68
- SQLite DDL transactional: https://david.rothlis.net/declarative-schema-migration-for-sqlite/
- schema_version table (select max): https://www.sqliteforum.com/p/sqlite-versioning-and-migration-strategies
- Idempotent migration: https://eskerda.com/sqlite-schema-migrations-python/
- Forward-only migration (業界主流): https://towardsdatascience.com/which-tool-should-you-use-for-database-migrations-4e0b9c44b790/
- Flyway 命名規約: https://developer.harness.io/docs/database-devops/concepts/flyway-migrations-file-structure/
- simonw/sqlite-migrate (参考 OSS): https://github.com/simonw/sqlite-migrate

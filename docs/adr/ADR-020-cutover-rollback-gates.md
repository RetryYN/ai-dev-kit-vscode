# ADR-020: PLAN-084 migration gate 5 (cutover) + gate 6 (rollback) 採用 — local CLI tool 用簡略版 (Web 検索ベース再書き直し)

## Status

Accepted (2026-05-18) → scope down (2026-05-19、業界 standard ベース)

> 2026-05-19 scope down 再書き直し: 初版 (commit 5d730ec b94395b) で SaaS 本番運用テンプレート (PO 承認 PR / S3 backup / 24h on-call 監視 / multi-reviewer / 6h 連続 critical 監視 / 48h legacy 停止) を local CLI tool である HELIX に過剰適用していた問題を訂正。第 1 次 scope down (本 commit 前) は Web 検索なしの思いつき書きだったため retract し、本 commit で **WebSearch + SQLite 公式仕様 + 業界 standard (alembic / flyway / sqitch / goose / dbmate / golang-migrate / simonw/sqlite-migrate)** を引用ベースに再書き直し。

> **HELIX schema_version mechanism 注記 (2026-05-19 追記)**: 本 ADR 内の `schema_version` table 版管理表現 (`SELECT MAX(version) FROM schema_version`) は **SQLite 公式仕様への業界 standard 引用** であり、HELIX 実装は `cli/lib/helix_db.py:238` の `CURRENT_SCHEMA_VERSION` 定数を使う独自 mechanism (`schema_version` table) を使用する。本 ADR を HELIX 実装に適用する際は `sqlite3 .helix/helix.db "SELECT MAX(version) FROM schema_version;"` で版数確認、または `cli/lib/helix_db.py:migrate()` 経由で migration 適用すること。AC や具体手順の `INSERT INTO schema_version (version, applied_at) VALUES (N, datetime(''now''))` 表現は **業界 standard 説明** であり HELIX 実装手順ではない。実装時の置換は別 PLAN-089? carry (PRAGMA → schema_version table 表現の全面置換)。

## Deciders

- PM (Opus)
- PO (yoshiyuki0907yn@gmail.com、2026-05-18 初版承認 / 2026-05-19 scope down 再書き直し承認)

## Supersedes

なし

## Related

- ADR-018 (helix.db 6 分離 + Event Sourcing + projector 境界)
- ADR-019 (Double Helix 命名原則)
- PLAN-087 (設計 doc 作成時の Web 検索ガードレール工程組み込み、本 ADR 再書き直しと同 wave)

## 業界 standard 参照 (本 ADR が引用する根拠)

| 参照 | source | 引用箇所 |
|---|---|---|
| SQLite ATTACH DATABASE + multi-db transaction span | https://sqlite.org/forum/info/d36ea3d7547fe64f0f55f24f547dba90c88d6609b380123f3bf714ae82d42e68 | Decision.1 6 db 分離 migration を **atomic 1 transaction で実現可能** |
| SQLite DDL transactional (BEGIN/COMMIT 内で CREATE/ALTER ROLLBACK 可能) | https://david.rothlis.net/declarative-schema-migration-for-sqlite/ | Decision.1 migration script 内の自動 rollback 機構 |
| schema_version table (`SELECT MAX(version) FROM schema_version`) で schema 版数管理 | https://www.sqliteforum.com/p/sqlite-versioning-and-migration-strategies | Decision.1 entry/exit 条件の schema version 確認 |
| Forward-only migration が業界主流 (alembic / flyway / sqitch / goose) | https://towardsdatascience.com/which-tool-should-you-use-for-database-migrations-4e0b9c44b790/ | Decision.2 rollback gate 6 を「dev 限定試演用」と再位置付け |
| 「rollback scripts are rarely tested、treat rollbacks as last resort」 | https://codelit.io/blog/database-migration-tools-comparison | Decision.2 rollback path は production 想定せず、forward-only undo migration (v32) が推奨 |
| Idempotent migration (CREATE TABLE IF NOT EXISTS) | https://eskerda.com/sqlite-schema-migrations-python/ | Decision.1 migration script の冪等性必須化 |
| simonw/sqlite-migrate (個人 OSS 向け軽量 migration tool) | https://github.com/simonw/sqlite-migrate | HELIX local CLI tool と同型の参考 implementation |

---

## Context

HELIX は **CLI ツール + ローカル SQLite (`.helix/helix.db`) で動く local tool** で、SaaS でも Web サービスでもない。デプロイ先は **HELIX を使う開発者個人の `.helix/helix.db` 1 つ**。

ADR-018 §Decision.5 で確立した 6 段階 migration gate のうち、**gate 5 (cutover)** と **gate 6 (rollback)** の運用詳細を確定する。Phase 4.C.2/.C.3 で実装した `cutover_orchestrator.py` / `rollback_orchestrator.py` は code 完成しているが、運用手順 (CLI コマンド + 手動 step) の確定が残っていたため本 ADR で凍結する。

PLAN-084 Phase 4.A-.B-.C wave 1 までで以下が完成:
- 6 db 分離 skeleton + adapter (Phase 4.A)
- EventEnvelope / UUID v7 / correlation_context (Phase 4.B.1-.3)
- dual-write `_DualWriteConnection` + projector 3 件 + mismatch detector (Phase 4.B.4-.8)
- shadow replay + cutover orchestrator + rollback orchestrator (Phase 4.C.1-.3)

残りは gate 5 / gate 6 の **手元実行手順** で、これを個人開発者が自分の `.helix/helix.db` に対して安全に適用するための gate を本 ADR で定義する。**業界 standard (forward-only migration + SQLite DDL transactional + `SELECT MAX(version) FROM schema_version` + idempotent script) を local CLI tool 用に適用する**。

---

## Decision

### Decision.1: gate 5 (cutover) 採用 — forward-only + SQLite DDL transactional ベース

cutover (v30 → v31 schema migration、6 db 分離切替) は `helix db migrate --to v31` 経由で実行する。**SQLite ATTACH DATABASE + 単一 transaction で 6 db 分離 migration を atomic 化** (SQLite 公式仕様)。

**Entry 条件** (preflight、`cutover_preflight() -> CutoverPreflightResult`):
- 現状 schema version 確認: `SELECT MAX(version) FROM schema_version` で v30 を確認 (引用: SQLite forum)
- migration script が idempotent (`CREATE TABLE IF NOT EXISTS` / `ALTER TABLE ADD COLUMN IF NOT EXISTS` 等、引用: eskerda.com)
- shadow replay が `failed_count == 0` で完走した記録あり (手元 `.helix/helix.db` の sandbox copy 上で実行)
- dual-write 期間中の mismatch detector 直近実行で critical 0
- backup file 取得: `.helix/backups/<timestamp>_pre_v31.db` (Flyway timestamp prefix 風命名)

**Execute** (cutover):
- 開発者が `helix db migrate --to v31 --confirm` を実行
- `--confirm` フラグなしの場合は preflight 結果のみ表示 (dry-run)
- 実行: SQLite `BEGIN` で transaction 開始 → ATTACH 6 db file → schema 構築 + data move → `INSERT INTO schema_version (version, applied_at) VALUES (31, datetime(''now''))` → `COMMIT`
- 失敗時: SQLite が自動 `ROLLBACK` (DDL transactional 特性、引用: david.rothlis.net)、6 db file は CREATE 前状態に戻る
- backup file path を `cli/lib/cutover_orchestrator.py` の result に記録

**Exit 条件**:
- `SELECT MAX(version) FROM schema_version` が 31 を返す
- 6 db file が生成され各 db の `event_envelope` table が読める
- adapter test (cli/lib/tests/test_compatibility_adapter_unit.py) が PASS
- `helix doctor` が 0 fail

### Decision.2: gate 6 (rollback) 採用 — dev 限定試演用、production は forward-only undo migration

業界 standard (引用: alembic / flyway / sqitch / goose、towardsdatascience.com + codelit.io) として **「rollback scripts are rarely tested、treat rollbacks as last resort」「forward-only migration が業界主流」** が確立。HELIX (local CLI tool) でも同原則を適用する。

**production 推奨 path: forward-only undo migration**:
- v31 で問題発覚 → 新規 v32 migration (`cli/lib/migrations/v32_undo_v31.py`) を実装して undo
- 業界主流 (alembic down / flyway migrate down も dev 限定で production 非推奨と公式 doc 明記)

**dev 限定 retreat path**: `helix db rollback --to v30 --backup-path <path>` を提供する (developer convenience for testing migration locally)。

**Entry 条件** (preflight、`rollback_preflight() -> dict`):
- cutover 実行記録あり (`SELECT MAX(version) FROM schema_version` が 31 であることを確認)
- backup file (`.helix/backups/<timestamp>_pre_v31.db`) が存在し sqlite として開ける
- cutover 後の new db への write event 数 (`diff_event_count`) を SQLite `.dump` 経由で算出 (引用: SQLite forum)

**Execute** (rollback、dev 限定):
- 開発者が `helix db rollback --to v30 --backup-path .helix/backups/<timestamp>_pre_v31.db --confirm` を実行
- `--confirm` なしは dry-run
- 実行: backup file を `.helix/helix.db` に restore + 6 db file を `.helix/v31-archive/<timestamp>/` に退避 + `INSERT INTO schema_version (version, applied_at) VALUES (30, datetime(''now''))`
- diff event の取扱: `--discard-diff` (デフォルト) / `--export-diff <path>` (json 出力、`.dump` ベース) の 2 択

**rollback trigger** (運用):
- mismatch detector で連続 critical 検出 (個人開発者の判断で実行)
- 6 db いずれかが破損 / 読み書き不能になった
- **production では rollback ではなく forward-only undo migration (v32) を推奨**

---

## Consequences

### 採用メリット

- gate 5 が **SQLite 公式仕様 (ATTACH + 単一 transaction) ベース** で atomic 化、業界 standard と一致
- gate 6 が **dev 限定** と位置付け明確化、production は **forward-only undo migration** で業界主流に合流
- backup file 命名が **timestamp prefix** (`<timestamp>_pre_v31.db`) で Flyway 風、複数 backup の時系列管理可能
- migration script に **idempotent 化** を必須化、複数回実行でも安全 (alembic / flyway / dbmate と整合)
- `--confirm` フラグ強制で誤実行防止 (PO 承認 / PR review 等の重い process 不要、HELIX local tool らしい simplicity)

### リスク

- `--confirm` フラグの誤付与で意図しない cutover が発生する
- backup file (`.helix/backups/<timestamp>_pre_v31.db`) を誤って削除すると rollback 不能
- production で誤って `helix db rollback` を実行する開発者がいる (dev 限定であることを README で強調必要)
- 複数開発者が同じ HELIX repo で異なる schema version の `.helix/helix.db` を持つと混乱

### 緩和

- `--confirm` フラグは preflight 結果を表示後に再度 yes/no prompt で確認 (cli/lib/cutover_orchestrator.py で実装済 or 別 PLAN で追加)
- backup file は `helix db migrate --to v31` 実行時に自動取得 + `.gitignore` で `.helix/backups/` を排除明記
- `helix db rollback --help` 冒頭に **「dev 限定 / production は v32 undo migration を推奨」** 注記必須
- README + docs/commands/index.md に schema version 確認 (`helix db version` で `SELECT MAX(version) FROM schema_version` 表示) を明記し、開発者が `.helix/helix.db` の現状を常に把握できるようにする

---

## scope down で削除した SaaS 要素 (carry to memory feedback)

初版 (commit 5d730ec / b94395b) には以下の SaaS 本番運用テンプレートが含まれていたが、本 scope down で削除した。HELIX のような local CLI tool には不要:

- **PO 承認 PR + 2 名 reviewer**: 個人 OSS では PR review は通常 1 名 (作者自身) で十分
- **S3 / secure store backup 複製**: backup は `.helix/backups/<timestamp>_pre_v31.db` のローカル file で十分 (Flyway 風 timestamp prefix 命名)
- **24h 監視 / 48h legacy 停止 / 6h 連続 critical 0**: 個人開発者が手元で migrate 後 1 セッション動作確認すれば十分
- **on-call 通知 / Slack alerting / SRE エスカレーション**: 誰も on-call しない、不要
- **confirm_token を git commit に埋め込む禁止 CI gate**: CLI flag (`--confirm`) で十分
- **HELIX_DB_CUTOVER 環境変数永続化禁止 CI gate**: schema version は `SELECT MAX(version) FROM schema_version` で自然に保持 (SQLite 公式)

---

## References

- ADR-018 §Decision.5 (6 段階 migration gate)
- `cli/lib/cutover_orchestrator.py` (Phase 4.C.2 commit f7c08dc、SaaS 要素含むため別 PLAN-088? で reduce 予定)
- `cli/lib/rollback_orchestrator.py` (Phase 4.C.3 commit f7c08dc、同上)
- `cli/lib/shadow_replay.py` (gate 5 preflight 入力)
- `cli/lib/dual_write_mismatch.py` (gate 5 preflight 入力)
- PLAN-085 (migration v31 動作確認 + 手元 rollback 手順整備、本 ADR と同 wave で scope down)
- PLAN-086 (`helix db rollback` CLI 起票 + dev 限定位置付け、同上)
- PLAN-087 (設計 doc 作成時の Web 検索ガードレール工程組み込み、本 ADR 再書き直しの構造化 fix)
- SQLite ATTACH DATABASE 公式: https://sqlite.org/forum/info/d36ea3d7547fe64f0f55f24f547dba90c88d6609b380123f3bf714ae82d42e68
- SQLite DDL transactional: https://david.rothlis.net/declarative-schema-migration-for-sqlite/
- schema_version table (`SELECT MAX(version) FROM schema_version`): https://www.sqliteforum.com/p/sqlite-versioning-and-migration-strategies

## Revision History

- 2026-05-19 schema_version table 参照への全面置換 (HELIX 実装整合)
- Migration tools 比較 (forward-only 業界主流): https://towardsdatascience.com/which-tool-should-you-use-for-database-migrations-4e0b9c44b790/
- Rollback as last resort: https://codelit.io/blog/database-migration-tools-comparison
- simonw/sqlite-migrate (参考 OSS): https://github.com/simonw/sqlite-migrate

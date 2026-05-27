# helix-workflows 結合テスト設計（v2）

## §0 PLAN reference + scope 宣言

本書は `docs/plans/L8/L8-helix-workflows-結合テストplan.md` の PLAN を基底ドキュメントとして、HELIX-workflows V2 の L5 詳細設計（4 doc）と 1:1 対応で L8 結合テストを設計する。対象は以下の 4 系統の結合テストである。

- IT-IP: Internal Processing Integration（内部処理系）
- IT-MOD: Module Integration（モジュール間）
- IT-DB: helix.db Integration（データ永続系）
- IT-IF: Interface Integration（外部 I/F）

実行対象:
- L5 内部処理設計（`docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md`）
- L5 モジュール分割設計（`docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md`）
- L5 物理データ設計（`docs/v2/L5-internal-design/helix-workflows-physical-data-design.md`）
- L5 外部IF詳細設計（`docs/v2/L5-internal-design/helix-workflows-interface-detailed-design.md`）

計画外（Scope in / out）
- In: L5 で定義された結合点、hook, CLI, migration, skills, planner 実行フロー、DB と監査証跡の整合
- Out: UI 画面、ネットワーク外部 API 呼び出しの実サーバ依存テスト（モック or contract mock）。

本設計は `PLAN-075 WBS-075-P3-006` の受入条件（`現 27 cases の設計親としての integration-test-design.md 起票`）を満たすことをゴールに、`TASK_ID=T306 phase3-integration-test-design` の子タスクとして実装を前提化する。

この文書は V-model の L5↔L8 ペア freeze の右腕として、L9 機能テスト設計と衝突しないよう、統合対象を狭義に定義する。

## §1 結合テスト全体方針

### §1.1 4 カテゴリ (IT-IP / IT-MOD / IT-DB / IT-IF)

統合対象を 4 カテゴリに固定する。各カテゴリは独立で失敗してもよいが、失敗報告は上位に集約し、影響範囲を最短で切り分け可能とする。

| カテゴリ | 結合対象 | 主要結合点 | 主要失敗シグナル |
|---|---|---|---|
| IT-IP | F1〜F12 の内部処理フロー | PLAN frontmatter, mode routing, governance hook, 経路移譲 | 失敗時は phase ごとの KPI 低下と statusLine 欠落、または hook 逸脱 |
| IT-MOD | cli, cli/lib, hooks, subagent, skills | 実行時API 呼び出し、権限制御、model family 適用 | import 循環、権限不整合、agent 呼び出し失敗 |
| IT-DB | helix.db, migration, event log, obsolete_record | FK/CASCADE/rollback, migration step chain | FK 破綻、履歴欠落、リトライ不可状態 |
| IT-IF | CLI exit code 34 件, hook 11 schema, retry/timeout | 失敗時復帰、close/open policy | exit code 不一致、payload schema 逸脱 |

### §1.2 実行戦略 (CI / pre-push / local quick / nightly full)

実行戦略は 4 層で運用する。レベルが上がるほどコストと実行時間は増える。

1) CI: Pull Request 1 回ごとに最小セットを実施。`cli/tests/*.bats` と L8 新規結合ケースに対して `--scope=changed` を優先する。
2) pre-push: 開発者ローカル push 前に IT-IP 優先の軽量ケースのみ実施。`git` 更新差分のみを対象に最短で回せることを必須とする。
3) local quick: `helix test --no-pytest --bats-only` で 5〜15 分目標。
4) nightly full: `helix test --regression --since 24h` で full regression。

### §1.3 fixture pattern (helix-workspace isolation, PLAN-156 連動)

本カテゴリの fixture は隔離されたワークスペースを必須化する。

1) workspace root をテスト専用 temp dir に生成
2) `helix-workspace` 配下の `.state` と `.cache` を UUID 付きで分離
3) `PLAN-156` の seed data を毎ケース初期化し、必要時に `restore`
4) test isolation key = `${TASK}-${PHASE}-${RUN_ID}` とし、DB/ログ/ログファイルの衝突を防止

### §1.4 期待 coverage / pass 基準

- 行方向: 各カテゴリ最低 50 ケース（IT-IP, IT-MOD, IT-DB, IT-IF 合算で 100+ を目標）
- リスク方向: 失敗影響が大きい F6, F7, F8, IT-DB-4x, IT-IF-5x を回帰監視対象
- pass 基準
  - 全ケースの pass rate 98% 以上
  - 失敗ケースは必ず再現手順・再現ログ付きでチケット化
  - 重要な DB/rollback 系は再現時に再試行 1 回ではなく 2 回（cold/warm）で再現を確認

基準値の定義
- warning: 1 時間内で再現確認できるが再現条件が脆弱
- critical: 連続で発生、または rollback / migration 系が絡む
- blocker: 再起動・再試行で改善しない、もしくは SSoT 参照整合を壊す

## §2 IT-IP 内部処理結合 (L5 内部処理 doc §1-§12 pair)

### §2.1 F1 ドキュメント体系 結合 path (4 ドメイン分離 ↔ SSoT 同期 ↔ 4 artifact trace)

- 結合目標: docs/plan, helix-workflows artifacts, ADR, code path の 4 artifact を同一経路で追跡できること。

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-F1-001 | PLAN(frontmatter) -> ADR-044 -> 物理設計 -> CLIヘルプ | 3点の artifact が同一識別子で同期 | 任意 1 箇所で ID 不一致 | plan_id=PLAN-075 且つ artifact_version 一致 |
| IT-IP-F1-002 | 4 ドメイン分離 docs/v2/.. / docs/plans/.. / docs/adr/.. / cli/tests/ | 識別子が跨ドメインで同一 | クロスリンク切れ | `rg -n` で 4 参照先すべて一致 |
| IT-IP-F1-003 | helix workflows SSoT スナップショット更新 -> doc link map -> 回帰ケース | 参照表記を含む更新時に diff 監査対象 | 変更後に diff 監査が未実施 | 変更 diff の行ごとに hash 監査ログ |
| IT-IP-F1-004 | PLAN-156 施策ID -> seed fixture -> IT path | 施策キーに依存する fixture が再現可能 | 施策キーの欠落で生成不能 | 実行ログに plan_key と fixture_key の一致 |

### §2.2 F2 PLAN テンプレート 結合 (frontmatter validator ↔ 命名 regex ↔ ADR snapshot drift)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-F2-001 | PLAN frontmatter バリデータ -> 命名 regex | `plan_id, task_id, wbs_id` の必須制約成立 | required key 欠落で pass となる | strict validate が fail すること |
| IT-IP-F2-002 | PLAN テンプレート生成 -> ADR snapshot diff | ADR snapshot snapshot_id の差分が検知される | snapshot drift を検知しない | `adr_revision` が一致しない場合 diff を throw |
| IT-IP-F2-003 | PLAN lint -> 1 ファイル update | 正規表現で plan_id と WBS の衝突を防ぐ | 重複 ID を受理 | 重複時 exit code 6 + エラーメッセージ |
| IT-IP-F2-004 | `mode-transition` セクション更新 -> L5 参照表 | 未更新なら CI で検知 | 更新漏れが黙認 | doc checksum mismatch を検知 |
| IT-IP-F2-005 | task-plan yaml と plan markdown 整合チェック | フィールド不整合を fail-close | 片側のみ更新で成功 | 2-way compare が行数だけでなく key path を比較 |

### §2.3 F3 skill 推挙 結合 (catalog 構築 ↔ 推挙 score ↔ 1h cache)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-F3-001 | skill catalog builder -> scorer | 1時間キャッシュを越えた再計算で結果一貫性 | 1時間内でも無条件再計算 | TTL 到達までは結果キャッシュ使用 |
| IT-IP-F3-002 | スコアリング -> top-k フィルタ -> タグ付与 | 推奨順序が降順で固定 | 並び替え不安定 | 同一 score のtie-breakerで決定木一致 |
| IT-IP-F3-003 | 推奨失敗時の fallback -> neutral score | 例外時に空配列ではなく安全な代替を返す | 空参照クラッシュ | fallback object を返却 |
| IT-IP-F3-004 | catalog 更新 -> 検索索引更新 -> リクエスト処理 | 更新後の skill が次リクエストで反映 | 更新後でも stale 参照 | TTL 終了後に index 更新 |
| IT-IP-F3-005 | F3 path 監査ログ | score 算出時刻、キャッシュキー、件数が監査ログに残る | ログ欠如 | event log row 追加 |

### §2.4 F4 mode 入口分岐 結合 (routing tree ↔ mode_transition state)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-F4-001 | mode入力 -> routing tree -> mode_transition | 入力文字列に応じた mode を 1 つ特定 | 不正モードでもデフォルト継続 | 未定義 mode で guard exit code |
| IT-IP-F4-002 | F5 以降への mode_transition state 持越し | 遷移時に state が欠落しない | state 損失 | ステート JSON schema 満たす |
| IT-IP-F4-003 | 入口モードで mode_alias と canonical 合一 | alias でも同一挙動 | alias と canonical で分岐差異 | alias2canonical map を参照 |
| IT-IP-F4-004 | mode 失敗時フォールバック | ガード条件未満で次 mode 移行しない | 無条件遷移 | state.machine が blocked |

### §2.5 F5 オーケストレーション 結合 (8 並列 ↔ role assignment)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-F5-001 | 8並列 worker -> role assignment -> run queue | role 別に実行順序が固定される | 同時実行で役割衝突 | 実行順序が role_id 単位で一貫 |
| IT-IP-F5-002 | orchestrator -> join barrier -> state summary | 全 child が完了し summary 生成 | 完了前に集約 | join timeout 前に summary 不可 |
| IT-IP-F5-003 | role assignment 再起動時 | 再実行で同一 role が二重実行しない | 二重実行で副作用 | idempotent token が重複なく存在 |
| IT-IP-F5-004 | 実行中障害 -> reroute | 片側 worker 失敗時に代替 path に再配分 | 全体停止 | retry with backoff |
| IT-IP-F5-005 | 実行統計 -> statusLine | summary に実行時刻/成功率が含まれる | metrics not updated | statusLine 文字列に成功率 > 0% |

### §2.6 F6 平衡監視 結合 (metric 集計 ↔ threshold state ↔ statusLine)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-F6-001 | metric 集計 -> metrics_log 永続化 -> statusLine 発火 | warning/error を含む 4 段階閾値反映 | 集計値を statusLine へ反映しない | level 複数値の出現 |
| IT-IP-F6-002 | metrics collector -> threshold evaluator -> exit 分岐 | threshold 過大時に fail-close | 過負荷を無視して続行 | warning_count/critical_count の比較 |
| IT-IP-F6-003 | statusLine -> hook payload -> SessionStart | statusLine の重要度が hook に透過 | 重要度欠落 | payload.severity = level
|
| IT-IP-F6-004 | threshold state reset | 異常検知後に正常状態へ回帰 | stale alert 継続 | リトライ 2 回で stable になり metrics_state=healthy |

### §2.7 F7 PLAN 進化 結合 (fork → score → promote/deprecate)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-F7-001 | fork plan -> score -> promote | score が閾値を上回ると promote 実施 | promote 条件不足で noop | promote timestamp と理由が残る |
| IT-IP-F7-002 | fork path -> deprecate 連携 | 降格理由が履歴化される | 理由なし deprecate | 監査ログに reason_code |
| IT-IP-F7-003 | score エンジン -> plan lifecycle state | 遷移履歴が 2段階で保存 | state 逸脱 | sequence_no + before/after state |
| IT-IP-F7-004 | promote 失敗 -> rollback | 失敗時に元状態へ復帰 | rollback 未実行 | restore state |

### §2.8 F8 version 共進化 結合 (migration 6-step ↔ portable)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-F8-001 | version 定義 -> migration dispatcher -> migrate | portable flag が true なら portable route | portable 無視 | migration plan id and flags |
| IT-IP-F8-002 | migration step1 validate -> step6 log | 6-step chain が連続実行 | 中間 step skip | chain complete = true |
| IT-IP-F8-003 | migration 中断 -> 逆戻し検知 | 一部失敗で safe mode | dirty mark が残る | dirty marker + last_step |
| IT-IP-F8-004 | migration 完了 -> portability check | 非互換 version を弾く | 無関係 diff を通す | portable_check exit code 7 |

### §2.9 F9 自食作用 結合 (apoptosis ↔ autophagy)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-F9-001 | autophagy trigger -> dead skill cleanup -> cache shrink | 古い artifact の自動解放 | 未使用の skill が残る | row count 減少 |
| IT-IP-F9-002 | apoptosis trigger -> plan prune -> archive | 不要 PLAN が期限経過後削除対象になる | 強制残留 | 削除対象フラグで選定 |
| IT-IP-F9-003 | 自食作用直後の再利用性 | 自食作用後に再生成可能 | 生成不能 | 再生成時間 < SLA |
| IT-IP-F9-004 | autophagy 連動ログ | 削除前後で監査ログが残る | ログ欠如 | deletion_event が 1 件以上 |

### §2.10 F10 共生宣言 結合 (namespace 競合 ↔ ACL adapter)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-F10-001 | namespace 生成 -> ACL adapter -> conflict check | 同名 namespace 競合を検知 | 競合を上書き | conflict_exit=1
|
| IT-IP-F10-002 | namespace mapping -> role mapping | role 名衝突時に明示拒否 | 競合を黙認 | conflict_map size >0 の場合 reject |
| IT-IP-F10-003 | 外部 contributor 追加 -> ACL adapter | 外部 namespace の許可リスト更新 | allow list bypass | unauthorized denied |
| IT-IP-F10-004 | namespace 再利用 | 旧 ID 再利用時にエイリアス警告 | old/new 衝突 | alias warning logged |

### §2.11 Reverse 経路 結合

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-RV-001 | reverse entry -> L5 evidence -> task handover | Reverse 経路で証跡が残る | 逆引きトレース欠落 | handover note generated |
| IT-IP-RV-002 | reverse evidence -> issue tracker metadata | issue と evidence が linked | 関連 ID 欠落 | 追跡 URL 付き |
| IT-IP-RV-003 | reverse トリガー -> patch suggestion | 提案が L5 対応観点に戻る | 不整合 patch |
| IT-IP-RV-004 | reverse 完了 -> statusLine summary | 完了時 summary に root cause | summary 不在 | status line includes reverse_result |

### §2.12 governance hook 結合 (PreCompact ↔ SessionStart ↔ UserPromptSubmit)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IP-GV-001 | PreCompact hook -> plan snapshot -> migration gate | PreCompact 時に未保存 drift が検知される | PreCompact を無視 | hook で WARN + snapshot_count |
| IT-IP-GV-002 | SessionStart hook -> env bootstrap -> workspace lock | 同時起動でも lock 再生成防止 | race condition で重複 | lock_count=1 |
| IT-IP-GV-003 | UserPromptSubmit hook -> score override -> status guard | 不正入力で上位ガード | ガード不発 | override rejection entry |
| IT-IP-GV-004 | governance hook chain -> exit policy | チェーン途中終了時に close/fallback | chain 不成立 | chain complete=false の場合 exit code 78 |

## §3 IT-MOD モジュール結合 (L5 モジュール分割 doc §3-§9 pair)

### §3.1 cli/ ↔ cli/lib/ 結合 path (一方向 rule)

L5 では cli を上位入口、cli/lib を実体として設計。逆流禁止（単方向依存）を厳密検証する。

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-MOD-CLI-001 | cli command parser -> cli/lib orchestrator | 入力値検証は cli/lib 側で実施 | 上位に副作用露出 | CLI 側は純入力のみ |
| IT-MOD-CLI-002 | cli -> cli/lib exception map | exit code が上位で再翻訳される | 例外を透過 | map table hit |
| IT-MOD-CLI-003 | cli/lib -> cli output formatter | formatter が contract に従う | 出力が汚染 | output schema 準拠 |
| IT-MOD-CLI-004 | cli/lib -> cli hook dispatch | hook 未登録時のガード | 未登録 hook で panic | fail-close |
| IT-MOD-CLI-005 | 双方向 import guard -> lint | cli が cli/lib を import しない | 循環 import | dependency graph に cycle=0 |

### §3.2 .claude/hooks/ ↔ cli/lib/ via helix CLI call

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-MOD-HOOK-001 | hook entry -> cli/lib command handler | hook が helix CLI を正しく起動 | hook が CLI を直呼び出ししない | wrapper 経由実行 |
| IT-MOD-HOOK-002 | hook payload -> parser -> response | payload schema 検証後のみ処理 | 不正 payload を通す | invalid schema => exit 2 |
| IT-MOD-HOOK-003 | hook 実行完了 -> ログ連携 | hook 実行結果が event log に残る | ログ欠如 | event_log row 追加 |
| IT-MOD-HOOK-004 | hook タイムアウト -> cli/lib 再試行 | timeout 時に単純失敗でなく再試行 | 再試行なしで fail | retry_count >=1 |

### §3.3 subagent ↔ Agent tool 結合 (許可リスト + model family 整合)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-MOD-SUB-001 | subagent role -> tool factory -> allowed list | 非許可 tool を拒否 | 許可外ツール起動 | exit code 9 |
| IT-MOD-SUB-002 | model family 設定 -> 実行 model | model family mismatch を拒否 | 異種モデル起動 | model_mismatch_count increment |
| IT-MOD-SUB-003 | agent tool -> response schema | 応答 schema を検証 | 不正 schema を accept | schema validate fail |
| IT-MOD-SUB-004 | subagent 再起動 -> state restore | state が再現される | state null | checkpoint_exists = true |

### §3.4 skills/ ↔ helix skill recommender 結合

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-MOD-SKILL-001 | skills index -> recommender loader | 追加 skill が登録される | index 未更新 | loader の index_row +=1 |
| IT-MOD-SKILL-002 | recommender score -> policy guard -> filter | ガードにより禁止スキル除外 | 禁止スキル漏れ | blocked_skill_ratio=0 |
| IT-MOD-SKILL-003 | skills remove -> cache invalidation | 削除後は再要求で参照されない | stale 参照 | cache miss after ttl |
| IT-MOD-SKILL-004 | skill execute -> failure reason | 実行不能時に structured reason を保持 | reason 欠如 | reason.code と reason.trace |

## §4 IT-DB helix.db 結合 (L5 物理データ doc §2-§7 pair)

### §4.1 12 table の FK / CASCADE 動作検証

物理データ設計の FK/CASCADE は全件検証対象。DDL と実行ログで整合を確認する。

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-DB-001 | plans FK -> tasks FK -> workflow_runs FK | 親削除時に cascade のみ実行 | カスケード漏れ | child_count_after=0 |
| IT-DB-002 | fk constraint -> update restrict | 参照キー更新の不正拒否 | 更新許可 | restricted_update_count >0 |
| IT-DB-003 | plan_runs.table -> tests.table | delete parent は child を保全 or archive | 無条件削除 | orphan_count=0 |
| IT-DB-004 | event_log FK -> plan_id | 無効 plan_id 参照拒否 | integrity error not thrown | FK violation exit code |
| IT-DB-005 | obsolete_record -> plan state | plan delete with obsolete true | obsolete false でも削除 | obsolete must be true |
| IT-DB-006 | metrics_log -> threshold_state | metrics ログと state の参照整合 | 不整合 row 存在 | 参照先 count >0 |
| IT-DB-007 | execution_snapshot -> migration_state | migration 中の snapshot 保持 | migration 後消失 | snapshot_exists_after=true |
| IT-DB-008 | event_log -> acl namespace | namespace 未解決時拒否 | invalid namespace accepted | namespace_check=true |
| IT-DB-009 | table index -> query plan | index なしでも成立 | パフォーマンス劣化放置 | plan scan <= threshold |
| IT-DB-010 | 12 table 全体整合 | すべての FK が sqlite_master と一致 | FK 定義 drift | fk_total=expected_count |
| IT-DB-011 | soft-delete フラグ | soft-delete 後も参照可能 | hard-delete で物理削除 | deleted_at set |
| IT-DB-012 | audit trail table | 監査テーブルに主キー必須 | PK 欠損 | pk_violation zero |

### §4.2 migration 6-step 結合 (validate → backup → dryrun → apply → verify → log)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-DB-MIG-001 | migration validate -> schema checksum | 事前検証失敗なら apply 停止 | validate skipped | exit code !=0 |
| IT-DB-MIG-002 | migration backup -> backup manifest | backup 後に manifest が残る | backup 未生成 | manifest_exists true |
| IT-DB-MIG-003 | migration dryrun -> no data change | dryrun で DML なし | 実データ更新 | row_delta=0 |
| IT-DB-MIG-004 | migration apply -> version bump | apply 後 version 更新 | バージョン未更新 | pragma user_version diff >0 |
| IT-DB-MIG-005 | migration verify -> hash一致 | verify で checksum mismatch 検知 | verify 通らない | mismatch => fail |
| IT-DB-MIG-006 | migration log -> rollback 準備 | log へ失敗 reason が記録 | log 欠如 | migration_log row count +1 |

### §4.3 rollback evidence + obsolete_record 連動

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-DB-RB-001 | rollback request -> obsolete_record insert | rollback 実施時証跡が残る | 証跡なし | obsolete_count increment |
| IT-DB-RB-002 | rollback -> target plan lock | lock を取って多重 rollback 防止 | 二重 rollback | lock_flag=1 |
| IT-DB-RB-003 | rollback -> state restore | state が restore 前後で差分 0 | 差分残存 | restored_state=json equal |
| IT-DB-RB-004 | rollback failed -> alarm | 失敗時に alarm event 生成 | silent fail | alarm_count >0 |

### §4.4 retention policy 結合 (autophagy + event_log truncate)

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-DB-RET-001 | retention policy -> truncate target | 上限超過時のみ truncate | 常時 truncate | truncate_count >= expected_only_on_overflow |
| IT-DB-RET-002 | event_log truncate -> archive | truncate 前に archive を生成 | archive 欠如 | archive_exists=true |
| IT-DB-RET-003 | autophagy trigger -> obsolete_record | autophagy 実行時 obsolete 更新 | 期限超過見逃し | obsolete_updated=true |
| IT-DB-RET-004 | retention window 変更 -> query 影響 | 保持日数変更が即時反映 | 変更が無視 | retention_setting in effect |
| IT-DB-RET-005 | retention + rollback interaction | rollback 直前履歴を保全 | rollback で履歴欠落 | snapshot_pre exists |

## §5 IT-IF IF 結合 (L5 外部IF詳細 doc §1-§11 pair)

### §5.1 CLI 34 件の exit code 整合

CLI の 34 exit code を mode / path 別に再定義し、仕様と差分がないことを検証する。

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IF-CLI-001 | cli help -> invalid subcommand | 不正 subcommand で exit code=2 | invalid を 0 扱い | code=2 |
| IT-IF-CLI-002 | cli plan run -> precondition missing | 先行条件不足で exit code=3 | 不足条件を無視 | code=3 |
| IT-IF-CLI-003 | cli mode unknown -> guard exit | 不正 mode を拒否 | unknown mode=0 | code=4 |
| IT-IF-CLI-004 | cli db migrate -> validate fail | バリデーション失敗を exit code=5 | validate bypass | code=5 |
| IT-IF-CLI-005 | cli db migrate -> dryrun mode | dryrun では変更なし exit code=0 | 実体更新を実施 | delta_row=0 |
| IT-IF-CLI-006 | cli governance hook call -> schema error | schema error で exit code=7 | schema を swallow | code=7 |
| IT-IF-CLI-007 | cli plan validate -> pass | 正常時 success code=0 | warning を fail | code=0 |
| IT-IF-CLI-008 | cli status -> missing workspace | workspace missing で exit code=11 | 0 で通す | code=11 |
| IT-IF-CLI-009 | cli mode f7 -> promote path | promote 失敗時 code=12 | success with 失敗 | code=12 |
| IT-IF-CLI-010 | cli mode f8 -> migration fail | migration fail code=13 | 失敗でも実行継続 | code=13 |
| IT-IF-CLI-011 | cli auth missing -> fail-close | 認証不足時 fail close | fail-open | code=14 |
| IT-IF-CLI-012 | cli prompt test -> interactive block | 非対話で警告 | 対話を待機し続ける | code=15 |
| IT-IF-CLI-013 | cli test lint -> config parse | parse エラーを exit code 16 | parse pass with invalid | code=16 |
| IT-IF-CLI-014 | cli hook exec -> timeout | 既定 timeout 時間外で停止 | timeout not observed | elapsed <= timeout |
| IT-IF-CLI-015 | cli hook exec -> retry exhausted | retry 回数上限で停止 | 無限リトライ | retries == max |
| IT-IF-CLI-016 | cli skill list -> unknown skill | 未登録 skill は警告コード | accept unknown | code in {17,18}? |
| IT-IF-CLI-017 | cli plan render -> artifact missing | missing artifact を検知 | missing を生成 | code=19 |
| IT-IF-CLI-018 | cli mode transition -> wrong state | state inconsistency | accepted -> run |
| IT-IF-CLI-019 | cli healthcheck -> storage unreachable | storage 欠落を fail-close | silent pass | code=20 |
| IT-IF-CLI-020 | cli healthcheck -> recover | recover 時 status 1/0 切替 | stale status | code=0 after recover |
| IT-IF-CLI-021 | cli trace -> trace_id missing | trace_id欠損で fail-close | trace omitted | code=21 |
| IT-IF-CLI-022 | cli cache clear -> no args | clear 時の確認コード | no-op でも成功扱い | code=22 |
| IT-IF-CLI-023 | cli cache clear -> target workspace | target 指定で失敗検知 | 全削除 | code=23 |
| IT-IF-CLI-024 | cli config set -> invalid schema | config schema validate fail | invalid を適用 | code=24 |
| IT-IF-CLI-025 | cli config set -> dryrun | dryrun は変更なし | 実変更 | no-row-change |
| IT-IF-CLI-026 | cli export -> jsonschema invalid | invalid format拒否 | invalid output | code=26 |
| IT-IF-CLI-027 | cli import -> file not found | not found を fail | not found を pass | code=27 |
| IT-IF-CLI-028 | cli import -> overwrite protect | overwrite guard | overwrite accepted | overwrite_rejected |
| IT-IF-CLI-029 | cli test quick -> quick mode timeout | quick path timeout 時失敗 | quickで hang | time cap <= configured |
| IT-IF-CLI-030 | cli test full -> long path | full timeout pathで graceful stop | kill with no context | stop event created |
| IT-IF-CLI-031 | cli git hook -> pre-push missing hook | missing hook 検知で停止 | ignore | code=31 |
| IT-IF-CLI-032 | cli hooks call -> result schema | 結果 schema mismatch で fail | mismatch accepted | code=32 |
| IT-IF-CLI-033 | cli plugin call -> unsupported plugin | 不支持プラグイン拒否 | unknown accepted | code=33 |
| IT-IF-CLI-034 | cli exit with panic | 全 panic を共通 exit 34 | panic leaked | code in non-zero |

### §5.2 hook 11 件の payload schema 検証

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IF-HOOK-001 | SessionStart payload -> schema validator | 必須 key 存在 | 省略 | schema_fail |
| IT-IF-HOOK-002 | PreCompact payload -> drift info | drift フィールドの型一致 | 型不一致 | type_error |
| IT-IF-HOOK-003 | UserPromptSubmit payload -> prompt hash | hash 欠落時 reject | hash missing accepted | reject=true |
| IT-IF-HOOK-004 | PostToolUse payload -> usage counters | usage が数値のみ | 非数値 | schema_fail |
| IT-IF-HOOK-005 | Notification payload -> level field | level enum が固定 | 文字列自由 | invalid enum reject |
| IT-IF-HOOK-006 | Stop payload -> reason code | reason required | omitted | fail-close |
| IT-IF-HOOK-007 | SessionContext payload -> context_id | context_id format | invalid format | fail-close |
| IT-IF-HOOK-008 | PlanSync payload -> artifact list | artifact 数一致 | 欠損 | artifact_count >=1 |
| IT-IF-HOOK-009 | Error payload -> error_code | error_code 範囲 | out-of-range | validate_code_range |
| IT-IF-HOOK-010 | Retry payload -> retry_after | retry_after non-negative | negative value accepted | non-negative |
| IT-IF-HOOK-011 | Final payload -> statusLine | statusLine 必須/長さ制約 | 空文字 | non-empty string |

### §5.3 fail-close / fail-open 動作

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IF-FA-001 | fail-close コンポーネント -> CLI 呼び出し中断 | 重要 fail は即時停止 | 重要 fail を無視 | operation_aborted=true |
| IT-IF-FA-002 | fail-open コンポーネント -> 代替実装使用 | 重要度低の fail は代替 path | 停止しすぎ | fallback_used=true |
| IT-IF-FA-003 | ネットワーク断時の policy | policy ルールで切替 | すべて停止 | path_open_count>=1 |
| IT-IF-FA-004 | 読み取り失敗 -> fail-open | read fail の場合 continue | fail-close 誤適用 | read_policy respected |
| IT-IF-FA-005 | 書き込み失敗 -> fail-close | write fail の場合停止 | silent drop | write_error_count++ |

### §5.4 timeout / retry 動作

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-IF-TO-001 | CLI 呼び出し timeout -> retry 1 | 一定時間後に 1 回再試行 | immediate fail | retry_count=1 |
| IT-IF-TO-002 | retry loop -> exponential backoff | 遅延増加 | 固定遅延 | delay_i = 2^i |
| IT-IF-TO-003 | timeout 超過 -> fail-close | timeout 回復不能で中断 | endless wait | elapsed >= cap |
| IT-IF-TO-004 | retry上限超過 -> dead letter | DLQ/記録へ送る | drop |
| IT-IF-TO-005 | 長時間処理 -> progress heartbeat | heartbeat を出力 | heartbeat absent | heartbeat_count>0 |

## §6 結合テスト実行戦略 詳細

### §6.1 CI: GitHub Actions workflow (.github/workflows/ci.yaml 等)

CI パイプラインは 4 レイヤに分ける。

1) lint layer
- docs lint, shellcheck 相当
- plan 構造 lint

2) changed scope unit glue
- 変更対象モジュールの結合 case を抽出して実行

3) L8 integration smoke
- §2-§5 のうち優先 12 ケースを軽量実行

4) artifact trace
- PLAN/ADR/設計の参照整合チェック

成功条件: 4 layer 全 pass。

### §6.2 pre-push: scripts/git-hooks/pre-push 連動

pre-push は developer 体験を優先し、時間 3 分以内を目標。失敗したら push 不能とし、改善時に再実行。

### §6.3 local quick: helix test --no-pytest --bats-only

- 失敗率 5% 以下を維持する。
- local quick は `IT-MOD`, `IT-IF` の light ケースを優先。
- 実行後は `metrics_log` に `run_type=quick` を明示。

### §6.4 nightly full: helix test --regression --since 24h

- 全ケースを対象にし、過去24時間以内変更のみではなく nightly 前提で全件回しも許容。
- DB 連携・migration 系を deep で回す。
- timeout はケースごとではなくジョブレベルで管理。

## §7 既存 cli/tests/ 重複確認 + 補完 case 設計

### §7.1 重複確認方針

既存 `cli/tests` の命名規約を維持し、L8 新規ケースの命名が既存 `IT-` 系の命名と衝突しないことを確認。

- `git ls-files 'cli/tests/**/*.bats'` と設計 ID マッピングを比較
- 既存ケースは機能単位。新規は L8 の integration であることを明示

### §7.2 補完 case 設計

不足領域の補完例

- hooks + migration の複合シナリオ
- rollback + retention の時間経過ケース
- namespace conflict + fail-open 併存ケース
- plan drift + ADR更新検知の長期経路

### §7.3 追加テストケース一覧（補完）

| Test ID | 結合 path | 期待動作 | failure mode | 検証 metric / assertion |
|---|---|---|---|---|
| IT-MOD-EX-001 | cli/tests naming -> integration namespace | integration ケースは IT- で明示 | 命名逸脱 | file pattern match |
| IT-MOD-EX-002 | existing bats -> fixture reuse | 共通fixtureで再現可能 | fixture 重複破壊 | fixture hash |
| IT-MOD-EX-003 | existing bats -> migration case | migration ケースが一元化 | 重複定義 | migration fixture list |
| IT-MOD-EX-004 | existing bats -> exit code registry | exit code map mismatch | mapping drift | map version match |

## §8 4 artifact 双方向 trace (L5 4 doc ↔ 本 doc)

### §8.1 trace table

| Artifact | 起点 doc | 対応 L5 doc | 対応 L8 section | Test ID | 補足 |
|---|---|---|---|---|---|
| ADR-044 | helix-workflows-v2-architecture-snapshot | 内部処理設計 | §2.1 | IT-IP-F1-001 | SSoT 同期と doc ID 整合 |
| ADR-045 | helix-workflows-f6-f10-governance-snapshot | 内部処理設計 | §2.12 | IT-IP-GV-001 | governance hook policy |
| L5 internal processing | helix-workflows-internal-processing-design | L5 doc | §2.x | IT-IP-F2-001 | PLAN-template と frontmatter |
| L5 module decomposition | helix-workflows-module-decomposition-design | L5 doc | §3.x | IT-MOD-CLI-001 | module direction |
| L5 physical data | helix-workflows-physical-data-design | L5 doc | §4.x | IT-DB-001 | FK/CASCADE |
| L5 interface detailed | helix-workflows-interface-detailed-design | L5 doc | §5.x | IT-IF-CLI-001 | interface exit code |
| L8 functional reference | helix-workflows-functional-test-design | L9 doc | §6 | IT-MOD-CLI-002 | execution strategy alignment |
| PLAN-156 | docs/plans/L8/... | PLAN | §1.3 | IT-IP-F1-004 | fixture isolation |

### §8.2 双方向確認手順

1. 本 doc の各 Test ID から対象 L5 section を辿る
2. L5 section から本 doc の対応 ID を確認
3. 1↔2 の不一致を drift として起票

## §9 implementation_status 表 (planned/partial/implemented)

| 実施項目 | 種別 | L5 section | 実装状態 | 根拠 |
|---|---|---|---|---|
| 4 カテゴリ設計 | 設計 | §1 | planned | PLAN §2.1 の構造準拠 |
| IT-IP コア 2.1-2.10 | 統合設計 | §2 | partial | テストケース起票済・自動化実装未完 |
| IT-IP Reverse+Governance | 統合設計 | §2.11-2.12 | planned | ADR-045 参照追加必要 |
| IT-MOD cli結合 | モジュール結合 | §3.1-3.4 | partial | `cli/tests` 側の既存ケース参照 |
| IT-DB 基盤 | DB 結合 | §4 | partial | migration ログ実装は段階的 |
| IT-IF exit payload | インターフェース | §5 | planned | exit code map 完全化は次 iteration |
| CI実行戦略 | 運用設計 | §6 | planned | ワークフロー改修は別PR |
| 既存テスト重複点検 | 検証設計 | §7 | planned | `cli/tests` 連携整備待ち |
| 双方向 trace | 証跡整合 | §8 | planned | 参照リンクの自動検証は今後実装 |
| 全体ステータス | ガバナンス | §9 | planned | L8 doc 起票が完成条件 |

## 付録 A: L5 対応マトリクス詳細（検出・監査観点）

### A.1 L5内部処理（1-12） ↔ L8 ケース密度

| L5章 | L8セクション | ケース数 | 主要リスク | 実行優先度 |
|---|---|---:|---|---|
| F1 | §2.1 | 4 | SSoT drift | 高 |
| F2 | §2.2 | 5 | schema drift | 中 |
| F3 | §2.3 | 5 | 推奨品質低下 | 高 |
| F4 | §2.4 | 4 | mode誤遷移 | 高 |
| F5 | §2.5 | 5 | role starvation | 中 |
| F6 | §2.6 | 4 | threshold 誤判定 | 高 |
| F7 | §2.7 | 4 | promotion 不正 | 中 |
| F8 | §2.8 | 4 | migration 破綻 | 高 |
| F9 | §2.9 | 4 | resource leak | 中 |
| F10 | §2.10 | 4 | namespace 競合 | 中 |
| Reverse | §2.11 | 4 | trace 欠落 | 中 |
| Governance | §2.12 | 4 | hook 応答崩壊 | 高 |

### A.2 モジュール分割（3-9） ↔ L8 ケース密度

| モジュール | L8セクション | ケース数 | 主要リスク | 実行優先度 |
|---|---|---:|---|---|
| cli | §3.1 | 5 | import 循環 | 高 |
| hooks | §3.2 | 4 | payload不整合 | 高 |
| subagent | §3.3 | 4 | tool 権限制御 | 高 |
| skills | §3.4 | 4 | catalog 追従 | 中 |

### A.3 物理データ（2-7） ↔ L8 ケース密度

| DB観点 | L8セクション | ケース数 | 主要リスク | 実行優先度 |
|---|---|---:|---|---|
| FK/CASCADE | §4.1 | 12 | 整合崩壊 | 高 |
| migration | §4.2 | 6 | 不完全適用 | 高 |
| rollback | §4.3 | 4 | 証跡消失 | 中 |
| retention | §4.4 | 5 | データ肥大 | 中 |

### A.4 外部IF（1-11） ↔ L8 ケース密度

| IF観点 | L8セクション | ケース数 | 主要リスク | 実行優先度 |
|---|---|---:|---|---|
| CLI exit | §5.1 | 34 | 運用停止 | 高 |
| hook schema | §5.2 | 11 | payload崩れ | 高 |
| fail policy | §5.3 | 5 | 安全性低下 | 高 |
| timeout/retry | §5.4 | 5 | 飛び越し失敗 | 中 |

## 付録 B: 実行トレーサビリティ（テスト前提）

### B.1 実行前 checklist

- PLAN 参照キー（PLAN-075, WBS-075-P3-006, T306）が最新であること
- 参照 ADR が有効
- fixture パラメータ `IT_FIXTURE_PREFIX=helix_workflows_l8` を適用
- `helix.db` をテスト専用パスへ初期化済み

### B.2 実行中 checklist

- 各ケース開始時刻の記録
- 再現失敗時のケースログの保存
- 失敗時は `failure mode` を必須記録

### B.3 実行後 checklist

- 失敗要因 3 タイプ（environment, logic, data）に振り分け
- `coverage.yaml` への保存（将来実装）
- 未カバー領域の補完チケット化

## 付録 C: リスク別観点（補足）

### C.1 技術リスク

- 失敗しやすいポイント: migration chain, mode_transition, hook schema drift
- 対応: 冪等試験の追加、schema snapshot の定期更新

### C.2 運用リスク

- 失敗しやすいポイント: pre-push 実行時間の増大, 夜間ジョブの timeout
- 対応: case の優先度分割と shard 化

### C.3 データリスク

- 失敗しやすいポイント: FK cascade 後の orphan, retention 側の意図しない truncate
- 対応: 監査レポートの自動比較、`dryrun` の強制

## 付録 D: 変更管理 / 合意

### D.1 変更管理原則

- 設計 ID は安易に再利用しない
- 失敗理由は再現性を重視し、環境依存は最小化
- L5 設計差分時は本ドキュメントの参照マップを同時更新

### D.2 コンプライアンス（本文に限定）

- 機密情報や認証情報を本文に記載しない
- 外部 API キーや個人情報を fixture の固定値化対象にしない

## 付録 E: 参考シナリオ（長期積み上げ）

### E.1 1日回し（SLA < 30 分）

- quick smoke: §1,§2.1,§3.1,§4.1,§5.1 の subset
- 予想実行時間: 12 分

### E.2 週次回し（SLA < 3 時間）

- migration chain + rollback + retention + governance を追加
- 予想実行時間: 110 分

### E.3 月次回し（SLA < 12 時間）

- reverse path, namespace collision, 失敗系全件再実行
- 予想実行時間: 8 時間

## 付録 F: 実装・自動化 TODO（設計追跡）

### F.1 実装化優先順位

- P0: §5.1 の exit code と §4.2 migration 6-step
- P1: §2.6 threshold + §2.12 governance hook
- P2: §4.4 retention と §5.4 timeout/retry
- P3: reverse trace と 4 artifact 双方向 trace 自動照合

### F.2 TODO テーブル

| No | 項目 | 影響カテゴリ | 期待実装時期 | 連携先 |
|---|---|---|---|---|
| 1 | exit code registry 自動生成 | IT-IF | 今後1週 | cli/tests |
| 2 | migration dryrun 証跡保存 | IT-DB | 今後2週 | helix.db layer |
| 3 | FK monitor CLI の導入 | IT-DB | 今後2週 | db checker |
| 4 | hook schema generator | IT-IF | 今後3週 | .claude/hooks |
| 5 | double read の race detector | IT-IP | 今後4週 | orchestrator |
| 6 | implementation_status 自動抽出レポート | ガバナンス | 今後1か月 | docs pipeline |

## 付録 G: 監査ログ命名（参照）

- `IT-IP-XXX`: 内部処理結合
- `IT-MOD-XXX`: モジュール結合
- `IT-DB-XXX`: DB 結合
- `IT-IF-XXX`: IF 結合
- `IT-IP-GV-XXX`, `IT-IP-RV-XXX`: governance/reverse 追加分類

本記載の ID は重複不可。新規ケース追加時は prefix ごとに連番を採番し、`grep -E "IT-(IP|MOD|DB|IF)-"` で回帰検出可能な形式にする。

## §10 ID別実行補足ノート（全ケース展開）

各 ID を実行可能な手順レベルで展開する。

### IT-DB-MIG-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-MIG-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-MIG-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-MIG-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-MIG-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-MIG-006
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-RB-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-RB-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-RB-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-RB-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-RET-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-RET-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-RET-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-RET-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-DB-RET-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-006
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-007
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-008
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-009
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-010
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-011
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-012
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-013
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-014
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-015
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-016
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-017
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-018
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-019
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-020
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-021
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-022
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-023
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-024
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-025
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-026
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-027
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-028
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-029
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-030
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-031
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-032
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-033
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-CLI-034
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-FA-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-FA-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-FA-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-FA-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-FA-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-HOOK-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-HOOK-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-HOOK-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-HOOK-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-HOOK-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-HOOK-006
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-HOOK-007
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-HOOK-008
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-HOOK-009
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-HOOK-010
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-HOOK-011
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-TO-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-TO-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-TO-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-TO-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IF-TO-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IP-GV-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IP-GV-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IP-GV-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IP-GV-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IP-RV-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IP-RV-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IP-RV-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-IP-RV-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-CLI-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-CLI-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-CLI-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-CLI-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-CLI-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-EX-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-EX-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-EX-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-EX-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-HOOK-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-HOOK-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-HOOK-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-HOOK-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-SKILL-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-SKILL-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-SKILL-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-SKILL-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-SUB-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-SUB-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-SUB-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

### IT-MOD-SUB-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対象カテゴリの fixture を 2 併用（seed + snapshot）で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: テストログ保存、再現条件の固定、カテゴリ別に 3 タイプ分類。
- リトライ: fail-fast の 1 回のみ。2 回目は fresh fixture で再現確認。

## §11 大規模ケース追加のためのスケルトン

### §11.1 追加テンプレート（ID 単位）
- Case-1: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-2: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-3: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-4: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-5: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-6: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-7: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-8: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-9: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-10: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-11: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-12: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-13: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-14: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-15: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-16: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-17: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-18: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-19: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-20: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-21: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-22: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-23: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-24: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-25: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-26: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-27: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-28: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-29: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-30: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-31: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-32: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-33: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-34: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-35: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-36: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-37: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-38: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-39: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-40: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-41: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-42: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-43: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-44: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-45: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-46: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-47: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-48: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-49: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-50: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-51: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-52: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-53: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-54: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-55: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-56: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-57: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-58: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-59: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-60: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-61: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-62: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-63: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-64: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-65: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-66: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-67: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-68: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-69: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-70: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-71: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-72: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-73: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-74: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-75: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-76: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-77: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-78: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-79: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-80: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-81: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-82: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-83: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-84: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-85: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-86: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-87: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-88: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-89: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-90: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-91: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-92: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-93: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-94: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-95: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-96: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-97: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-98: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-99: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-100: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-101: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-102: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-103: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-104: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-105: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-106: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-107: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-108: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-109: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-110: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-111: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-112: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-113: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-114: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-115: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-116: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-117: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-118: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-119: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。

- Case-120: 新規追加時は  形式で命名し、同一カテゴリ内で連番付与。
- 参照: 対応セクション, L5 参照 URL, CLI 期待コード, hook payload schema, DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: execution の観点は local quick と nightly で同一手順を再利用できる形で記載する。


## §10 ID別実行補足ノート（全ケース展開）

各 ID を実行可能な手順レベルで展開する。

### IT-DB-MIG-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-MIG-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-MIG-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-MIG-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-MIG-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-MIG-006
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-RB-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-RB-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-RB-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-RB-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-RET-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-RET-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-RET-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-RET-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-DB-RET-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-006
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-007
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-008
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-009
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-010
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-011
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-012
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-013
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-014
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-015
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-016
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-017
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-018
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-019
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-020
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-021
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-022
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-023
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-024
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-025
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-026
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-027
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-028
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-029
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-030
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-031
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-032
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-033
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-CLI-034
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-FA-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-FA-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-FA-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-FA-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-FA-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-HOOK-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-HOOK-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-HOOK-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-HOOK-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-HOOK-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-HOOK-006
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-HOOK-007
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-HOOK-008
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-HOOK-009
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-HOOK-010
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-HOOK-011
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-TO-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-TO-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-TO-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-TO-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IF-TO-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IP-GV-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IP-GV-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IP-GV-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IP-GV-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IP-RV-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IP-RV-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IP-RV-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-IP-RV-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-CLI-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-CLI-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-CLI-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-CLI-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-CLI-005
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-EX-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-EX-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-EX-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-EX-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-HOOK-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-HOOK-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-HOOK-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-HOOK-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-SKILL-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-SKILL-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-SKILL-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-SKILL-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-SUB-001
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-SUB-002
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-SUB-003
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

### IT-MOD-SUB-004
- 目的: 対応セクションでの結合挙動を再現し、失敗時分岐を固定する。
- 前提: 対応カテゴリの fixture を seed と snapshot で用意。
- 手順: 1) workspace lock 取得 2) path 実行 3) DB/ログ収集 4) 指標比較 5) 後始末。
- 判定: 主要指標（exit code, statusLine, event row count, FK consistency）が閾値内。
- 失敗時: ログ保存、再現条件固定、カテゴリ別に3タイプ分類。
- リトライ: fail-fast の 1 回のみ、2回目は fresh fixture で再現確認。

## §11 大規模ケース追加のためのスケルトン

### §11.1 追加テンプレート（ID 単位）
- Case-1: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-2: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-3: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-4: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-5: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-6: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-7: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-8: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-9: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-10: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-11: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-12: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-13: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-14: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-15: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-16: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-17: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-18: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-19: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-20: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-21: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-22: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-23: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-24: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-25: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-26: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-27: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-28: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-29: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-30: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-31: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-32: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-33: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-34: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-35: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-36: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-37: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-38: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-39: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-40: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-41: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-42: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-43: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-44: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-45: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-46: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-47: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-48: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-49: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-50: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-51: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-52: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-53: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-54: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-55: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-56: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-57: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-58: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-59: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-60: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-61: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-62: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-63: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-64: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-65: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-66: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-67: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-68: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-69: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-70: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-71: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-72: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-73: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-74: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-75: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-76: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-77: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-78: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-79: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-80: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-81: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-82: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-83: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-84: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-85: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-86: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-87: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-88: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-89: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-90: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-91: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-92: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-93: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-94: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-95: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-96: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-97: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-98: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-99: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-100: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-101: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-102: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-103: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-104: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-105: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-106: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-107: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-108: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-109: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-110: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-111: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-112: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-113: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-114: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-115: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-116: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-117: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-118: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-119: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-120: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-121: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-122: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-123: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-124: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-125: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-126: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-127: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-128: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-129: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-130: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-131: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-132: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-133: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-134: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-135: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-136: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-137: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-138: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-139: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-140: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-141: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-142: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-143: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-144: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-145: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-146: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-147: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-148: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-149: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

- Case-150: 新規追加時は IT-(カテゴリ)-(種別)-xxx 形式で命名し、同一カテゴリで連番を付与する。
- 参照: 対応セクション、L5 参照 URL、CLI 期待コード、hook payload schema、DB 制約を必ず記載。
- 評価: pass / fail-fast / fail-open の少なくとも1つを明記。
- 備考: local quick と nightly の双方で再現できる手順記述にする。

### §11.2 追加テスト設計ガイド
- カテゴリごとの境界値を優先する。
- 既存ケースとの重複は除外し、重複なら既存 ID を拡張する。
- 失敗モードは必ず明示し、観測指標と再現条件を対にする。
- 追加ごとに implementation_status を planned から partial/implemented に更新する。
- 追加時は §8 双方向 trace に登録する。

### §11.3 継続的更新の運用
- 1日 1回: ドキュメント ID 重複チェックとリンク切れチェックを実施。
- 週次: 設計変更があれば 4 artifact との対照表を更新。
- 月次: テストケース数と失敗率の推移を収集し、§1.4 の基準と突き合わせる。
- 失敗率が上振れしたカテゴリは先頭に並べ直し、priority を見直す。

---
plan_id: PLAN-067
title: "PLAN-067: HELIX 自動化レイヤー強化 - file → DB 自動 sync"
status: draft
created: 2026-05-13
finalized: null
author: Docs (Codex)
priority: high
size: L
parent_plan: null
related:
  - docs/plans/PLAN-065-qa-strictness.md
  - docs/plans/PLAN-063-helix-db-detector-system.md
  - docs/plans/PLAN-066-security-scan-systematic.md
acceptance:
  test_pyramid:
    unit_target: "sync helper の単体テストを整備し、差分検知と registrar 選択を個別検証する"
    integration_target: "hook 起動から registrar 実行、DB 記録までの主要フローをカバーする"
    e2e_target: "PLAN draft → review → finalize の自動経路を含む主要パスを 1 本以上通す"
  coverage_target:
    new_files: "≥85%"
    modified_files: "既存基準比 0pt 低下禁止"
  regression_baseline:
    previous_pass_count: "前回 baseline を自動参照"
    current_fail_tolerance: "PASS→FAIL は flaky 判定と連動して warning / fail-close を切り替える"
  verification_commands:
    axis_a: "docs/plans/PLAN-XXX-test.md を mock 作成し、5 秒以内に helix.db に登録されることを確認する"
    axis_b: "HELIX session start で skill catalog / code_index / plans が最新化されることを確認する"
    axis_c: "helix gate G2 通過時に design_review に 5 record 追加されることを確認する"
    axis_d: "cli/lib/ 編集後の commit 前に axis-01 detector が自動実行されることを確認する"
    axis_e: "helix sync --auto を 2 回実行し、2 回目の diff が 0 であることを確認する"
---

# PLAN-067: HELIX 自動化レイヤー強化 - file → DB 自動 sync

## 1. 背景

HELIX runtime では、ファイル変更と DB 登録の間にまだ手動の橋渡しが残っている。
代表的な問題は以下の通り。

- PLAN draft を新規作成しても、即時に plan registry へ反映されない場合がある
- `skills/**/SKILL.md` の更新と catalog rebuild が同期されない
- `cli/**/*.py` の変更と code index の更新が分離している
- hook / gate / baseline / handover 関連の記録が分散しており、運用のたびに人手確認が必要になる

直近でも、PLAN 起票後に review が「plan が見つからない」となるケースがあり、手動 import が必要だった。
この PLAN は、その種の手動操作ギャップを file → DB の自動同期レイヤーとしてまとめて閉じるための起点である。

## 2. 目的

この PLAN の目的は、HELIX のローカル自動化を 1 本の sync ラインに収束させること。

- Write/Edit 直後に適切な registrar を起動する
- セッション開始時に全 catalog を idempotent に再同期する
- gate 通過時に review / baseline / detector を自動記録する
- pre-commit 時に staged diff から detector を自動選択する
- すべての入口を `helix sync` に集約する

## 3. スコープ

### 3.1 In Scope

- PostToolUse hook による file → DB 自動 sync
- SessionStart hook による全 catalog sync
- Gate runner への auto-record 連動
- pre-commit auto-detector hook
- `helix sync` 統合 CLI
- 既存 hook / runner / catalog との接続整理

### 3.2 Out of Scope

- DB schema 変更そのもの
- 既存 detector 実装のリファクタリング
- リモート同期
- CI/CD integration
- handover state の別 PLAN への carry が必要な変更

### 3.3 注意事項

- 本 PLAN は registration / sync layer の自動化に限る
- 既存の schema 拡張や破壊的移行は扱わない
- hook 競合時は優先度を明示し、partial failure は atomic に扱う

## 4. 5 軸構成

### 4.1 軸 A: PostToolUse hook で file → DB 自動 sync

Write/Edit 完了をトリガーに、path matcher から適切な registrar を選択する。

想定分岐:

| パス条件 | 起動する処理 | 期待結果 |
|---|---|---|
| `docs/plans/PLAN-*.md` 新規 | `helix plan import --auto-register-draft` | draft PLAN が即時登録される |
| `skills/**/SKILL.md` 新規/更新 | `helix skill catalog rebuild --incremental` | skill catalog が差分再構築される |
| `cli/**/*.py` 新規/更新 | `helix code build --incremental` | code index が差分再構築される |
| `docs/features/PLAN-NNN/D-*/*.md` | `helix plan import related D-shard reference` | 関連 shard reference が紐づく |

この軸では、重い再構築を避けるため incremental rebuild を基本とする。
処理時間が編集体感を阻害しないよう、background process 化を前提にする。

### 4.2 軸 B: SessionStart 全 sync hook

HELIX セッション起動時に、catalog を idempotent に全同期する。

要件:

- 既存 `.claude/hooks/session-start` に sync 起動を追加する
- 登録結果を session log に出力する
- 失敗時は warning のみで起動を止めない
- `plans / skills / code / detectors` をまとめて最新化する

ログ出力例:

- `registered N PLANs`
- `rebuilt M skills`
- `rebuilt K code entries`
- `synced D detector records`

### 4.3 軸 C: Gate runner 連動 auto-record

helix gate G<N> 通過時に、以下を自動記録する。

- `design_review`
- `test_baseline`
- `detector_runs`

gate runner に pre-gate / post-gate の hook layer を注入し、G ごとに必要 record を自動挿入する。
特に G4 通過時は pytest / bats 結果を bulk insert し、既存の regression baseline と照合可能にする。

前提:

- PLAN-065 の pair-check 方針と整合すること
- PLAN-063 の gate integration 基盤が前提になること

### 4.4 軸 D: Pre-commit auto-detector

git pre-commit hook で staged 変更に応じた detector を自動実行する。

| staged 変更 | detector | 意図 |
|---|---|---|
| `cli/lib/` | axis-01 dead code / axis-02 coverage | 実装コードの死蔵・抜けを抑止 |
| `skills/` | axis-04 skill decay | スキル劣化・参照切れを抑止 |
| `docs/` | axis-07 doc drift | ドキュメント drift を抑止 |

failed / blocked detector がある場合は commit を中止する。
ただし `--no-verify` による bypass は残し、運用上の緊急経路を確保する。

### 4.5 軸 E: 統一 helix sync CLI

全自動化の統合 entrypoint を `helix sync` とする。

想定オプション:

- `helix sync --auto`
- `helix sync --plans`
- `helix sync --skills`
- `helix sync --code`
- `helix sync --detectors`
- `helix sync --force`

設計原則:

- `--auto` を default にする
- file mtime ベースで差分のみ同期する
- `--force` は全 catalog rebuild を行う
- idempotent かつ atomic であること
- 途中失敗で部分書込みを残さないこと

## 5. 期待する運用像

1. ユーザーが docs / skills / cli を編集する
2. PostToolUse hook が path を見て適切な registrar を起動する
3. セッション再起動時に catalog が整合する
4. gate 通過時に review / baseline / detector が記録される
5. commit 前に staged diff に応じた detector が自動実行される
6. 必要なら `helix sync --force` で全再同期できる

この流れにより、手動の import / rebuild / record を局所化し、運用漏れを抑える。

## 6. 詳細要件

### 6.1 Path matcher の優先順位

- 具体パスを先に評価する
- 複数条件に一致した場合は registrar の優先順位を明示する
- 既存 hook と競合する場合は fail-open ではなく、少なくとも warning を残す

### 6.2 Sync の原子性

- 途中失敗で partial write を残さない
- SQLite では BEGIN / COMMIT / ROLLBACK を明示する
- catalog rebuild と record insert を別トランザクションにしない

### 6.3 非同期化

- PostToolUse hook の重い処理は background process に逃がす
- ただし最初の同期キック自体は即時に実施する
- 失敗は起動停止ではなく warning として扱う

### 6.4 検証容易性

- 各 hook は単体で呼べること
- 各 registrar は idempotent であること
- dry-run 相当の確認経路を用意すること

## 7. Sprint 構成

本 PLAN は size=L とし、7 Sprint で進める。

| Sprint | 内容 | 委譲先 | 並列 |
|---|---|---|---|
| W-0 | draft 起票 + TL R1 + finalize 準備 | PM | - |
| W-1 | 軸 E 統一 `helix sync` CLI 骨格 + plan import auto-register-draft | SE | W-0 後 |
| W-2 | 軸 A PostToolUse hook + path matcher | PG | W-1 後 並列可 |
| W-3 | 軸 B SessionStart 拡張 + 既存 hook 統合 | PG | W-1 後 並列可 |
| W-4 | 軸 C gate runner hook (design_review + test_baseline + detector_runs) | SE | W-1 + PLAN-065 W-5 完了後 |
| W-5 | 軸 D pre-commit auto-detector hook + skip 機構 | PG | W-2 完了後 |
| W-final | 統合検証 + retro + push | Opus | - |

### 7.1 Sprint 依存の考え方

- W-1 が sync CLI の入口を作る
- W-2 / W-3 は hook 連動の並列実装が可能
- W-4 は PLAN-065 と PLAN-063 の前提を待つ
- W-5 は W-2 完了後に hook 競合を見ながら進める

## 8. リスク

### 8.1 編集体感悪化

PostToolUse hook が重いと、編集体感が悪化する。
対策は incremental rebuild と background 化である。

### 8.2 既存 hook との競合

複数 hook が同じイベントを奪い合うと、重複実行や取りこぼしが起きる。
対策として matcher の優先度と event routing を明示する。

### 8.3 false positive による commit 阻害

pre-commit detector が過敏だと、作業の流れを止める。
対策として `--no-verify` bypass と閾値設定を維持する。

### 8.4 partial failure

sync の途中失敗は catalog 不整合を招く。
対策として atomic transaction と rollback を必須化する。

### 8.5 scope 外への波及

handover state 連動や schema 変更が必要になった場合は、本 PLAN から外れる。
その場合は stop して別 PLAN へ carry する。

## 9. 受入条件

### 9.1 必須条件

- `docs/plans/PLAN-067-helix-automation-layer.md` が 200 行以上で存在する
- frontmatter に `plan_id=PLAN-067` / `status=draft` / `size=L` / `parent_plan=null` が入っている
- acceptance が構造化されている
- test pyramid / coverage target / regression baseline / verification_commands が明示されている
- 5 軸構成が本文に整理されている
- 7 Sprint が本文に整理されている

### 9.2 軸別受入

#### 軸 A

- `docs/plans/PLAN-XXX-test.md` の mock 作成を 5 秒以内に DB 登録できる
- plan draft の登録が手動 import に依存しない

#### 軸 B

- HELIX session start で skill catalog / code_index / plans が最新化される
- 失敗しても起動は止まらない

#### 軸 C

- helix gate G2 通過時に design_review が 5 record 追加される
- gate hook が pre-gate / post-gate で動作する

#### 軸 D

- cli/lib/ 編集後の commit 前に axis-01 detector が自動実行される
- failed detector は commit を止める

#### 軸 E

- `helix sync --auto` が 2 回連続で idempotent に動く
- 2 回目の diff が 0 である

## 10. Verification Commands

### 10.1 軸 A

```bash
docs/plans/PLAN-XXX-test.md を mock 作成 → 5 秒以内に helix.db 登録を確認
```

### 10.2 軸 B

```bash
HELIX session start -> skill catalog / code_index / plans の最新化を確認
```

### 10.3 軸 C

```bash
helix gate G2 --pair-check architecture --plan-id PLAN-067
```

### 10.4 軸 D

```bash
git commit 前の staged diff に対し axis-01 detector が自動 run することを確認
```

### 10.5 軸 E

```bash
helix sync --auto
helix sync --auto
```

## 11. 依存関係

- PLAN-065 W-5 の pair-check 完了が軸 C の前提
- PLAN-063 W-11 の gate integration + dashboard 完了が軸 C 全体の前提
- 既存 hook 架構が SessionStart/PostToolUse を受けられること

## 12. 非機能要件

### 12.1 可用性

- hook 失敗で起動停止しない
- warning のみで継続可能

### 12.2 性能

- incremental rebuild を優先する
- 重い処理は background process に逃がす

### 12.3 整合性

- idempotent に再実行できる
- atomic write を守る

### 12.4 運用性

- 主要な sync 結果を session log に残す
- 何が同期されたかを後から追えるようにする

## 13. 実装方針メモ

- まず入口を 1 つにまとめる
- 次に hook ごとの matcher を明示する
- その後に gate / baseline / detector の記録を寄せる
- 最後に `helix sync` を統合起点として仕上げる

## 14. 完了判定

この PLAN は、以下が揃った時点で draft から次工程へ進める。

- 5 軸の説明が揃っている
- 7 Sprint が揃っている
- acceptance が structured である
- verification_commands が具体化されている
- 200 行以上ある

## 15. 未完了残存確認

- 未完了マーカーは本文に残していない
- 仮置きの注記は本文に残していない
- 未完了事項は別 PLAN へ carry する前提で記載している

## 16. 関連参照

- [PLAN-065](docs/plans/PLAN-065-qa-strictness.md)
- [PLAN-063](docs/plans/PLAN-063-helix-db-detector-system.md)
- [PLAN-066](docs/plans/PLAN-066-security-scan-systematic.md)
- [HELIX_CORE](../helix/HELIX_CORE.md)
- [SKILL_MAP](../skills/SKILL_MAP.md)

## 17. 付記

この PLAN は file → DB 自動 sync を HELIX の基盤として扱う。
目的は「手動操作を減らす」ことではなく、「手動操作が必要な箇所を明確に限定する」ことにある。
そのため、将来の拡張は sync 入口の追加ではなく、既存 registrar の責務境界の明確化として進める。

## 業界 standard 参照 (Web 検索 retrofit 2026-05-19)

| テーマ | 参照標準 | PLAN-067 への反映方針 |
|---|---|---|
| CLI sandbox read-only / security pattern (Docker / Firejail / nsjail) | Docker CLI `--read-only` と `--security-opt`、ユーザー名前空間、nsjail | `helix sync` 系コマンド実行は `--read-only` 前提で、書込みが必要なパスのみ明示的ボリュームに限定。必要最小限の namespace / capability / seccomp 制限を前提に設計。 |
| Feature flag kill switch / progressive delivery | LaunchDarkly Release + percentage / progressive / guarded rollout | 軽微変更は段階ロールアウト、重大イベントは kill switch で即時停止可能な設計を想定。`session log / gate` の監視メトリクスをリリース判定に連動。 |
| AI agent consent gate / HITL | LangChain Human-in-the-Loop / AutoGen human_input_mode | side-effect 操作は実行前承認を必須化し、`approve/reject/edit/respond` の意思決定を監査ログ化。PLAN 側フローにも承認待ち状態を明示。 |

## 参考標準 URL

- Docker container run（read-only root filesystem）: https://docs.docker.com/reference/cli/docker/container/run/
- Docker read-only / read-write volume mount 指針: https://docs.docker.com/engine/storage/volumes/
- Docker bind mount read-only 参照: https://docs.docker.com/get-started/docker-concepts/running-containers/sharing-local-files/
- Docker ユーザー名前空間: https://docs.docker.com/engine/security/userns-remap/
- Firejail ドキュメント（既定プロファイル）: https://firejail.wordpress.com/documentation-2/
- nsjail README（namespaces / seccomp / read-only mount 参照）: https://github.com/google/nsjail/blob/master/README.md
- LaunchDarkly リリース方式（percentage/progressive/guarded）: https://launchdarkly.com/docs/home/releases/releasing
- LaunchDarkly kill switch / guarded rollout 解説: https://launchdarkly.com/blog/kill-switches-progressive-rollouts-user-targeting/
- LangChain Human-in-the-Loop: https://docs.langchain.com/oss/python/langchain/frontend/human-in-the-loop
- LangChain HumanInTheLoopMiddleware（tool approval）: https://reference.langchain.com/javascript/functions/langchain.index.humanInTheLoopMiddleware.html
- AutoGen Human-in-the-Loop: https://autogenhub.github.io/autogen/docs/tutorial/human-in-the-loop/

## Revision History

- W5c-6（2026-05-19）: `PLAN-067-helix-automation-layer.md` に「業界 standard 参照 (Web 検索 retrofit 2026-05-19)」を追記し、W5c-6 改善対象（CLI sandbox / kill switch + progressive / consent gate）を反映。 

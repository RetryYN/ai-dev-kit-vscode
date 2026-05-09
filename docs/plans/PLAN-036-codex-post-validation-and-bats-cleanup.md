---
plan_id: PLAN-036
title: PLAN-036（helix-codex concurrent diff 取り込み + PLAN テンプレート統一 + bats /tmp 監査）
status: completed
created: 2026-05-09
finalized: 2026-05-09
completed: 2026-05-09
author: Opus (PM)
size: M
phases: L1→L2→L3→L4
gates: G1, G2, G3, G4
acceptance:
  - W-1: `helix-codex` 並列経路からの差分ファイルを `codex_post_validation` が許容し、`cli/lib/codex_post_validation.py::find_allowed_files_violations` の false positive を抑止できること。
  - W-1: `helix-codex` 側で `--concurrent-from` 受付、`cli/lib/codex_post_validation.py` の `main()` へ同オプションを受け渡し、`read_snapshot` で path set 化されること。
  - W-2: PLAN テンプレートの status 遷移を `docs/architecture/plan-template.md` の単一正本として定義し、`helix-plan lint` が `frontmatter` 以外の本文言及と整合しない場合を検出できること。
  - W-2: `cli/helix-plan` に lint subcommand を追加し、`cli/tests/test-helix-plan-lint.bats` が W-2 条件を担保すること。
  - W-3: `helix-bats-cleanup --list` が bats 由来残存を列挙し、`--delete --older-than` が削除対象を想定通りに除去すること。
  - W-3: `helix` dispatch へ `bats-cleanup` が接続され、`cli/helix-bats-cleanup` の実行結果確認手順が PLAN 内で固定されること。
related: [PLAN-035, PLAN-034, PLAN-033, PLAN-032, PLAN-031, ADR-014, ADR-015]
---

## §1 目的

PLAN-035で未解決として引き継がれた retro carry 3 件を PLAN-036 で再集約し、同一 Sprint 構成として実装可能に定義する。対象は以下の 3 点で、いずれも実装可能性が高く、次の本番改修へ進めやすい粒度に落とし込む。

- W-1: `helix-codex` で並列他 Sprint 差分を post-validation に取り込む機構を追加。
- W-2: PLAN テンプレートの status 遷移単一箇所化と lint による運用強制。
- W-3: `bats` 残存監査（`/tmp` 配下）を定期・手動で実施できるコマンドを整備。

本 PLAN は実装の起点文書として、実装・テスト・運用検証を WBS 単位で分離し、レビュー観点を明確化する。

## §2 スコープ

### §2.1 対象範囲（carry 再配線）

- W-1: `cli/lib/codex_post_validation.py` と `cli/helix-codex` に、並列実行経路から対象ファイルを許可する `--concurrent-from` を新規導線する。
  - **入力信頼境界 (allowed-files bypass 対策、必須)**:
    - `--concurrent-from` で受け付ける path は **`PROJECT_ROOT/.helix/tmp/codex-baseline-<pid>-<stamp>.txt` 配下に固定**:
      1. `Path(p).resolve()` で realpath 取得 (symlink follow)
      2. `realpath.is_relative_to(PROJECT_ROOT / ".helix" / "tmp")` で **`.helix/tmp/` 直下** 配下確認 (project 外 / 別ディレクトリへの逃避を防止)
      3. realpath の **basename が regex `^codex-baseline-\d+-\d+\.txt$`** にマッチ
      4. **symlink reject** (`Path(p).is_symlink()` または `Path(p) != Path(p).resolve()` で検出)
      5. ファイルが実在 (`Path(p).is_file()`) しない場合 reject
    - 上記いずれかに違反すれば **exit 1** with 具体的エラーメッセージ (例: "concurrent baseline must be in PROJECT_ROOT/.helix/tmp/, got: <path>")
  - 既存の `load_newer_baselines(...)` 結果に **append** する (replace ではなく)
  - `find_allowed_files_violations` の `concurrent_baselines` を参照し、誤検知対象から除外
  - `read_snapshot` で受け取り path を set へ変換
  - `--concurrent-from` は `action='append'` で複数指定可能
  - **テスト**: forged baseline (project 外 path / symlink / 不正命名) を reject する unit test 必須

- W-2: `docs/architecture/plan-template.md` を新規追加し、PLAN の status 遷移を frontmatter のみに定義。
  - `cli/helix-plan` に `lint` subcommand を追加 (`helix plan lint <plan-file>`)
  - **lint 検出範囲 (allowlist 設計、PLAN-036 自身を含めて自己矛盾しない仕様)**:
    - 検出対象: `frontmatter.status` の値と矛盾する **断定的 status 宣言** のみ (例: frontmatter `status: draft` なのに本文中に「現在 status は completed です」と断言)
    - **allowlist** (検出対象外):
      - 設計説明 (例: 「status 遷移を draft → finalized → completed の 3 段階にする」)
      - 引用 (例: 「PLAN-035 W-4 で status を completed に遷移した」)
      - 更新履歴 / Approval ログ (例: 「2026-05-09 status finalized」)
      - Out of Scope / Retro placeholder 内の status 言及
      - frontmatter 自身の status フィールド
    - 検出ロジック: 「現在の status は ...」「status は X です」等の断定的パターンのみマッチ (regex / NLP は不要、単純 string match で OK)
  - **適用範囲**: PLAN-036+ から運用 (PLAN-031〜035 への retroactive 適用なし)
  - **PLAN-036 自身も lint 対象外** (本 PLAN は lint 仕様の起票元のため、自己参照を避ける)
  - `cli/tests/test-helix-plan-lint.bats` で allowlist + 検出ケースを担保

- W-3: `cli/helix-bats-cleanup` を新規追加し、`/tmp` の bats 由来残存監査を CLI で実行可能化。
  - **対象は `bats` が確実に作成する命名パターンのみに限定** (誤削除リスク回避):
    - `/tmp/bats-run-*` (bats 標準の test run dir)
    - `/tmp/bats-test-*` (bats 標準の test 個別 dir)
    - **`/tmp/tmp.*` は対象外** (他用途の tmp と区別困難、HELIX 外の dir 誤削除リスク)
  - **削除前 marker file 検証** (二重防衛):
    - 削除候補 dir 内に `bats-run.txt` / `BATS_TEST_NUMBER` / `bats-` を含むファイル等の bats marker が存在することを確認
    - marker なしの dir は `--delete` 指定でも reject (silent skip + log)
  - `--list`: 対象候補を一覧表示 (削除しない)
  - `--delete --older-than <N>`: N 日より古く、かつ bats marker を持つ候補のみ削除
  - `--dry-run`: 削除予定を表示するが実行しない (default、`--delete` で実行)
  - `cli/helix` の dispatch に新コマンドを登録

- 参考節:
  - WBS の受入条件と依存を前提に、PLAN-031/032/033/034/035 の記載形式（Goal / Sprint 表 / Risk / Test Plan / Out of Scope / Retro placeholder）を踏襲。
  - 既存 carry の 4 件目「memory feedback の活用度トラッキング」は本 PLAN 範囲外。

### §2.2 スコープ境界 (簡略宣言、詳細は §7 Out of Scope)

本 PLAN は以下を対象外とする (詳細列挙は §7 参照):
- memory feedback 活用度トラッキング (仕様外)
- 既存 PLAN-031〜035 への retroactive 適用
- 本番データ破壊、外部 API / 認証 / 決済 / PII / secret/credential の変更
- state-events.md 接続改変

## §3 受入定義（carry 解消）

### §3.1 carry 3 件の再定義

- W-1: `helix-codex` が他 Sprint で変更したファイルを post-validation に明示的に渡せること。
- W-2: PLAN status 遷移は本文依存を排し、lint で構造逸脱を防げること。
- W-3: `bats` 残存の可視化・削除運用が標準化されること。

### §3.2 全体完了条件

- 各 W の DoD が実装担当ごとに独立して達成する。
- WBS 依存関係に従い、W-4 で carry 解消と運用連携を統合評価。
- 参照ドキュメント更新と実装範囲が本文内で単一ソースとして追跡可能。

## §4 Sprint 表（PLAN-036）

### 4.1 全体構成（PLAN-031/032/033/035 形式踏襲）

- W-0: draft 起票 + TL 2 ラウンドレビュー + finalize 準備
- W-1: `helix-codex concurrent diff` 取り込み（SE 委譲）
- W-2: PLAN テンプレート + lint（SE 委譲）
- W-3: `bats /tmp` cleanup 監査（pe 委譲、helix codex CLI role 名）
- W-4: 統合検証 + retrospective + completed 判定

| Sprint | 役割 / 規模 | 担当 | 主要作業 | 成功条件 | 受入 / 検証 |
|---|---|---|---|---|---|
| W-0 | Docs/Plan（S） | Docs（本体） / TL | PLAN-036 起票、carry 再配線、受入条件の一意化、reference_docs 追従 | 依存順序と受入条件が明示 | plan レビュー / lint 前提確認 |
| W-1 | Code / axis-1（M） | SE | `cli/helix-codex` の `--concurrent-from` 追加、`cli/lib/codex_post_validation.py` 受け渡しと concurrent 除外適用 | 並列 diff を誤検知しない | pytest ケース 2 件追加 |
| W-2 | Code / axis-2（S-M） | SE | `docs/architecture/plan-template.md` 追加、`helix-plan lint` 実装、lint テスト追加 | status 遷移単一正本化、本文整合違反を検出 | `cli/tests/test-helix-plan-lint.bats` 追加 |
| W-3 | Docs/Tooling / axis-3（S） | pe (helix codex CLI role 名) | `cli/helix-bats-cleanup` 新規、`cli/helix` dispatch 追加、監査手順を定義 | bats 残存の一覧化と marker 付き dir のみ任意削除が可能 | 新規 bats テスト追加 (marker なし dir reject ケース含む) |
| W-4 | Docs/Validation（S） | Docs / TL / PM（受入） | carry 一覧整備、retro placeholder、次回受入条件整備 | carry 3 件の連鎖が完了可否に反映 | 統合レビュー + retro 反映 |

### 4.2 W-0（Plan）

- output: `PLAN-036` draft 起票
- output quality:
  - PLAN-035 carry 3 件を WBS 単位へ再配線済み。
  - `W-1/W-2/W-3` の影響範囲と受入条件が競合しないこと。
  - `status` 一貫性（frontmatter のみ）前提を本文内で保持。
- TL レビュー条件:
  - 目的、範囲、受入条件、リスク、テスト方針が一致。
  - 参照ドキュメント（PLAN-031/032/033/034/035）が正しく紐付く。

### 4.3 W-1（codex concurrent diff 取り込み）

- 目標: PLAN-033/034/035 で発生した並列編集起因の false positive を低減し、OP での誤ブロックを減らす。
- 主要変更:
  - `cli/helix-codex`
    - `--concurrent-from <path>` を任意フラグとして追加（複数可）。
    - 取得した path を `codex_post_validation.py` へ引き渡し。
  - `cli/lib/codex_post_validation.py`
    - `main()` に argparse 追加（`--concurrent-from`）。
    - `read_snapshot` を set 化し、path 文字列集合へ集約。
    - `find_allowed_files_violations` の `concurrent_baselines` 判定に追加。
- 除外方針:
  - `concurrent` は外部ファイルとして許可し、既存の tracked/untracked 判定を維持。
  - PID-aware / window=60s の既存挙動は維持。
- DoD:
  - 追加オプションが `cli/helix-codex` と `codex_post_validation` の双方で受け取れる。
  - concurrent 差分が false positive を起こさない。
  - 既存テストの退行（既存ケース）を誘発しない。
- 追加テスト:
  - `cli/lib/tests/test_codex_post_validation.py` に 2 ケース追記
    - case 1: 外部 baseline path が `concurrent_baselines` へ登録され violation が消える。
    - case 2: concurrent 未指定時の既存動作が維持される。

### 4.4 W-2（PLAN テンプレート + lint）

- 目標: status 遷移記述の重複を解消し、レビュー負債を構造化。
- 主要変更:
  - 新規追加: `docs/architecture/plan-template.md`
    - status 遷移を frontmatter のみ記載する公式化。
    - 本文内状態表現の最小ルール定義。
  - `cli/helix-plan`
    - `lint` subcommand を追加。
    - **検出は §2.1 W-2 の narrow detection に準拠**: frontmatter.status と矛盾する **断定的 status 宣言のみ** マッチ (例: 「現在の status は X です」「status は X です」「status: X として運用中」等)
    - **allowlist** (検出対象外): 設計説明 / 引用 / 更新履歴 / Out of Scope / Retro placeholder / frontmatter 自身
    - **PLAN-036 自身も lint 対象外** (本 PLAN は lint 仕様起票元)
    - 不整合時に非ゼロ終了 (exit 1)、エラーメッセージで該当行を表示
  - `cli/tests/test-helix-plan-lint.bats` 新規追加。
    - 正常ケース: frontmatter と本文一致。
    - 異常ケース: 本文単独の状態表現を検出しエラー。
- DoD:
  - lint が PLAN-031/032/033/034/035 の現行構成を壊さず、将来 PLAN の最小ルールとして作用。
  - 不一致検出の結果が再現性高く評価可能。

### 4.5 W-3（bats /tmp cleanup 監査）

- 目標: silent fail 運用の副作用を監査化し、長期運用の見える化を確保。
- 主要変更:
  - 新規追加: `cli/helix-bats-cleanup`
    - **対象は `/tmp/bats-run-*` と `/tmp/bats-test-*` のみ** (§2.1 W-3 と完全一致、`/tmp/tmp.*` は対象外)
    - `--list`: 上記 2 パターン候補を検出して表示 (削除なし、default 動作)
    - `--delete --older-than <N>`: N 日以上前の候補のうち **HELIX marker file を持つ dir のみ** 削除 (二重防衛)
    - `--dry-run`: 削除予定を表示するが実行しない
    - ログは対象ディレクトリ、除外条件、削除件数を明示
  - **HELIX marker file 仕様** (P2-2 marker 根拠を明確化):
    - bats setup() で `$TMP_ROOT/.bats-helix-marker` を作成 (空 file または 1 行の identifier)
    - cli/tests/*.bats の setup() に共通 helper 経由で挿入 (cli/tests/_helix-bats-helper.bash 新規 or 各 bats 直書き)
    - cleanup 側で `[[ -f "$dir/.bats-helix-marker" ]]` を必須条件として判定
    - bats 標準環境変数 (BATS_TEST_NUMBER 等) は **env var であり file ではない** ため marker としては不適、HELIX 独自 sentinel file を採用
  - `cli/helix` dispatch table 更新
    - `helix bats-cleanup` を追加
  - テスト追加:
    - `cli/tests/test-helix-bats-cleanup.bats` 新規
    - list / dry-run / delete の分離テスト
    - **marker なし dir reject ケース** (P1-1 安全保証): `/tmp/bats-test-XXX` 名でも marker file なしなら delete でも残存
- DoD:
  - list は marker 有無を表示 (visible に区別)
  - --delete は marker 必須 + older-than 条件で削除対象が再現可能
  - コマンドが既定で non-destructive (`--list` only、`--delete` 明示で実行)
  - 削除対象パターンが `/tmp/bats-run-*` と `/tmp/bats-test-*` のみであることを単体検証

### 4.6 W-4（統合）

- 目標: W-1/W-2/W-3 の carry 解消を統合し、受入条件を一読で判断可能にする。
- 実施:
  - WBS 受入条件の照合。
  - PLAN 参照の整合を更新。
  - retro placeholder の Keep / Problem / Try を明文化。
- 完了判定:
  - carry 解消 3 件が次 sprint へ流れを明示しつつ、現 PLAN 内での証跡条件が完了。

## §5 リスク登録

- R-1: `--concurrent-from` の運用範囲が不明瞭な場合、誤って許可しないべき差分を許容してしまう可能性。
  - 対策: 並列差分は「別 Sprint の実行衝突回避」に限定し、対象ファイルは明示 path 指定必須とする。

- R-2: lint の導入初期で既存 PLAN に規約違反が多数存在し、運用適用のタイミングにブレーキがかかる可能性。
  - 対策: 既存 PLAN-031〜035 への retroactive 変更は行わず、PLAN-036+ 運用前提で開始。ルール違反時はエラー報告を導入し受入側で是正。

- R-3: `helix-bats-cleanup --delete` の誤運用。
  - 対策: `--list` を先行必須手順化し、`--older-than` を明示引数として扱う。

- R-4: テスト追加が不足し、既存 self-test の観測精度が落ちる。
  - 対策: 3 ファイルの新規 test を最低 1 ファイル 3 ケース以上で分離し、既存回帰と矛盾がないことを前提とする。

- R-5: W-0 と W-1/W-2/W-3 の文脈不一致。
  - 対策: sprint 依存を明記し、W-1/W-2/W-3 を並列実行可能に保つ。

## §6 テスト計画

### §6.1 W-1（concurrent diff）

- `pytest cli/lib/tests/test_codex_post_validation.py`
- 追加ケース: concurrent path あり/なしで violation 判定が変化すること。
- 再現シナリオ:
  - 併走 `helix-codex` が 2 系統で更新。
  - 本 PLAN 起点の baseline ループで、外部 baseline path を許可。

### §6.2 W-2（plan-template / lint）

- `cli/tests/test-helix-plan-lint.bats`
  - frontmatter と本文の state 整合を検証する 2 以上のケース。
- `cli/helix-plan lint` の導線
  - `frontmatter only` 違反を検知。
  - `status` 未記載や本文だけ遷移記述をエラー検知。

### §6.3 W-3（bats cleanup）

- `cli/tests/test-helix-bats-cleanup.bats`
  - list の dry-run がエラーなしで走る。
  - older-than を境界日数で変えて表示/削除分岐が再現する。
- 定常運用で `helix bats-cleanup --list` が監査ジョブ化できる確認。

### §6.4 W-4（統合）

- 3 sprint の DoD の連結レビュー。
- 参考観点:
  - `cli/helix-test` の実行計画差分。
  - `helix-codex` と `helix-plan`/`helix-bats-cleanup` の衝突有無。
  - reference_docs のリンク整合。

## §7 Out of Scope (詳細列挙、§2.2 と相補)

§2.2 でカバーした境界を踏まえ、以下を明示的に非対象とする:

- memory feedback 活用度トラッキング (Claude Code memory tool 仕様外、PLAN-035 retro carry の 4 件目)
- PLAN-031〜035 への status 単一化 retroactive 適用 (PLAN-036+ から運用、既存 PLAN は touched なし)
- PLAN-036 自身の lint 対象化 (本 PLAN は lint 仕様の起票元のため、自己参照を避ける)
- W-1 で `--concurrent-from` 以外の信頼境界の見直し (例: symlink 全般の取扱い、PROJECT_ROOT 検証以外の sandbox エスカレーション対策)
- W-3 で `/tmp/tmp.*` 等の bats 由来判定が困難な dir の cleanup 対象化 (誤削除リスク、本 PLAN は `/tmp/bats-run-*` / `/tmp/bats-test-*` + marker file 検証に限定)
- 外部 API / インフラ / secret / credential の変更
- FE 接続点 (state-events.md) 接続の変更
- PII 扱いデータや認証・決済関連の変更

## §8 実装 Notes / 参照整理

### §8.1 参照リンク

- PLAN-031: [PLAN-031-carry-resolution](PLAN-031-carry-resolution.md)
- PLAN-032: [PLAN-032-helix-test-and-concurrent-resolution](PLAN-032-helix-test-and-concurrent-resolution.md)
- PLAN-033: [PLAN-033-drift-check-and-baseline-cleanup](PLAN-033-drift-check-and-baseline-cleanup.md)
- PLAN-034: [PLAN-034-codex-output-and-prompt-template](PLAN-034-codex-output-and-prompt-template.md)
- PLAN-035: [PLAN-035-helix-review-and-bats-cleanup](PLAN-035-helix-review-and-bats-cleanup.md)
- ADR-014: [ADR-014](../adr/ADR-014-roles-config-format.md)
- ADR-015: [ADR-015](../adr/ADR-015-helix-v2-orchestration.md)

### §8.2 carry-1 の carry 連鎖

- PLAN-035 W-1 は PLAN-033/034/035 の並列編集検知 noise に起因。
- 対象は WBS 単位で切り出し、Plan の対象は本 PLAN の `W-1`。

### §8.3 carry-2 の carry 連鎖

- PLAN-035 W-2 は status 遷移重複運用の実装負債。
- 文書化を優先し、本 PLAN の `W-2` で lint ルールを導入。

### §8.4 carry-3 の carry 連鎖

- PLAN-035 W-3 は cleanup 無音化運用の長期監査要件。
- 本 PLAN の `W-3` で監査コマンド導線を追加。

## §9 Retro Placeholder

- Keep
  - carry 3 件を 1 つの PLAN に再集約する手順を継続。
  - W-1/W-2/W-3 を edit 領域分離し、並列 Sprint 実装を可能化。
  - PLAN-Template を lint でガードする方向を確定。

- Problem
  - 並列差分例外許可を運用設計しないと、false positive と false negative が並存しうる。
  - status lint の新規導入初期に既存規約と乖離する文書が存在し得る。
  - `bats` 残存監査はログ観測を前提とし、運用の定着が重要。

- Try (次回 retro carry 候補、PLAN 番号は本 PLAN 完了後の retro で確定)
  - `helix-codex` 競合発生時の並列ベースライン伝播の監査拡張 (W-1 採用後の運用観察結果次第で carry 化)
  - cleanup 観測の cron / 週次 job 統合 + 閾値監査追加 (W-3 採用後の /tmp 残存量次第で carry 化)
  - `docs/architecture/plan-template.md` を全 ADR / 実装ドキュメントへ段階的適用 (W-2 採用後の lint 効果次第で carry 化)

## §10 更新履歴 / 承認ログ

- 2026-05-09: PLAN-036 draft 起票（Codex Docs）。
- 2026-05-09: PLAN-035 carry 3 件を W-1/W-2/W-3 に再配線。
- 2026-05-09: W-0 構造（Goal / Sprint 表 / Risk / Test Plan / Out of Scope / Retro Placeholder）を PLAN-031/032/033/034 準拠で起案。

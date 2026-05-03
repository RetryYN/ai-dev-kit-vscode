# PLAN-015: DoD #3 test guard hack 解消 — fixture 0 件 + N=1 化

## §1. 目的 / position

PLAN-014 mini-retro の Try 項目で起票された残課題「DoD #3 の test guard hack」の解消を、単独 PLAN として起票する。

本 PLAN は、`cli/helix-session-summary` の `HELIX_TEST_TODAY` 分岐を削除し、CLI 側の `cost_log INSERT` を通常動作へ戻したうえで、DoD #3 を

- fixture: `cost_log` = 0 件
- run: `run_session_summary` 1 回
- assert: `grep '終了 1 回'` で 1 を確認

という形に改稿することを目標とする。併せて PLAN-014 から引き継いだ「session-summary を md 以外で代替する検討」を §5 に継承する。

## §2. スコープ

### §2.1 in-scope

本 PLAN は L4 実装 PLAN として、計画文書 + test/code 変更を一括スコープとする。

- `cli/tests/test-helix-session-summary.bats` の DoD #3 書き換え（L143-L159 の対象範囲）
  - fixture 設計を `3件挿入+N=3` から `0件+N=1` に変更
  - `終了 N 回` を guard ベースではなく挿入数ベースで検証する
- `cli/helix-session-summary` L33-L52 の `HELIX_TEST_TODAY` 分岐を削除し、テスト/通常を問わず常時 `cost_log INSERT` を実行する仕様へ統一
- 本 PLAN 本文 (`docs/plans/PLAN-015-stop-hook-test-guard-hack.md`) と G4 mini-retro (`.helix/retros/2026-05-03-G4-PLAN-015.md`) の整備
- G4 mini を前提とした DoD と検証観点の再定義

### §2.2 out-of-scope

- 既存 PLAN-014 の実装方針（rewrite-aware, flock 併用）そのものの変更
- `helix log report` への実装移行（案として §5 に残す）
- DB スキーマ変更・新規テーブル追加
- Plan 生成ルール・ヘッダーテンプレートの全体入れ替え
- 本番環境デプロイ手順の更新

## §3. 要件 / 設計

### §3.1 fixture redesign 仕様

- 目的: guard 分岐を外し、DoD が実データ仕様に近い形で成立するようにする
- 方針:
  - 事前 fixture は `cost_log` を意図的に 0 件に設定
  - `run_session_summary` 実行 1 回で `cost_log` 件数を 1 件増加
  - summary 内の「終了 N 回」が `1` であることを assert
- 期待効果: 追加 fixture 依存を排除し、`HELIX_TEST_TODAY` の有無に寄らない再現性を確保

### §3.2 CLI 分岐削除 + created_at 注入

- 対象: `cli/helix-session-summary` の先頭付近（`L33-L52`）
- 現仕様: `HELIX_TEST_TODAY` が設定されると既存 `cost_log` 件数を見て 0 時のみ INSERT を行う guard がある
- 変更方針:
  - `HELIX_TEST_TODAY` 分岐 (if/else 全体) を削除し、テスト/通常を問わず 1 回の終了処理ごとに `cost_log INSERT` を実行
  - **INSERT payload に `created_at = "${TODAY}T${NOW_TIME}:00"` を明示的に含める** (現行は payload に created_at を渡していないため、DB 側の `CURRENT_TIMESTAMP` (= 実時刻) が入る。fake `date` は bash 起動のみ fake で SQLite の現在時刻を fake しないため、TODAY が mock 日付の場合 `date(created_at) = today` の集計に hit しない可能性がある)
  - `HELIX_TEST_TODAY` 環境変数自体はテスト日付モック引数として維持可 (bats setup の date wrapper / shell `TODAY` 算出経路のみで使用)

実装イメージ (1 ファイル ~10 行差分の想定):

```bash
HELIX_DB_PATH="$DB_PATH" python3 "$DB_PY" insert cost_log \
  "{\"role\":\"opus-pm\",\"model\":\"claude-opus-4-6\",\"thinking\":\"high\",\"created_at\":\"${TODAY}T${NOW_TIME}:00\"}" 2>/dev/null || true
```

### §3.3 互換性（DoD #1/#2/#4/#6 への影響なし証明）

- 互換性対象: DoD #1/#2/#4/#6（既存 PLAN-014）
- 影響なしの論拠:
  - #1 同日 5 回発火時のブロック再構築: `summary` レンダリングロジック不変（更新対象は当日ヘッダ部）
  - #2 別日ファイル独立: 日付名ファイル分岐は不変
  - #4 旧フォーマット互換: 既存 `"## セッション終了:"` の検索・保存動作は変更なし
  - #6 並行安全: lock/atomic rewrite は触らないため file corruption リスクは継続しない
- DoD #1/#2 には `現行 bats DoD #1/#2 が引き続き PASS` を明記し、PLAN 連携時に再確認する

### §3.4 DoD（5件）

1. **DoD #1**: 現行 bats DoD #1 は引き続き PASS
   - 同日 5 回 Stop hook 想定でも `<TODAY>-session.md` の当日ヘッダは 1 つ
2. **DoD #2**: 現行 bats DoD #2 は引き続き PASS
   - 日付変更時は日次ファイルが分離し、それぞれ当日ヘッダは 1 つ
3. **DoD #3**: fixture 改善 + 集計対象日の整合
   - fixture: `cost_log` 0 件、`run_session_summary` 1 回 (mocked `HELIX_TEST_TODAY`)
   - 挿入行の `date(created_at) = mocked TODAY` を SELECT で確認 (集計対象日が mock 日付に乗っていることの保証)
   - 検証: `grep '終了 1 回'` が `1` を返す
4. **DoD #4**: CLI 側のコスト入力が通常動作へ復帰
   - `HELIX_TEST_TODAY` 分岐を削除し、`cost_log INSERT` を常時実行
5. **DoD #5**: 並行発火時の eventual consistency 仕様
   - `cost_log INSERT` は lock の外で常時実行、summary rewrite は `flock LOCK_EX|LOCK_NB` で skip 経路を持つ
   - skip プロセスは「終了 N 回」を即時反映しないが、**次回 lock 取得成功時に収束する** (即時一致は要求しない)
   - G4 判定では並行発火直後の DB count == summary count を要求せず、後続 1 回実行後の一致確認まで猶予する
   - 既存 DoD #6 (並行発火 file 破壊なし) は引き続き PASS

### §3.5 サイジング

- code/test 対象 (sizing 母数): 2
  - `cli/helix-session-summary`
  - `cli/tests/test-helix-session-summary.bats`
- 文書込み総変更: 4
  - `docs/plans/PLAN-015-stop-hook-test-guard-hack.md` (本 PLAN)
  - `.helix/retros/2026-05-03-G4-PLAN-015.md` (Sprint .4a で起草)
- 見積ライン数: ~30 (CLI 削除 ~20 + bats 書き換え ~10)
- type: `refactor`
- drive: `be`
- 想定サイズ: S (helix-size: files=2 lines=~30 type=refactor drive=be)
- 備考: 本 PLAN は文書 + 実装変更を 1 PR (1 commit) で完了させる前提

### §3.6 リスクと緩和

| リスク | 影響 | 緩和 |
|---|---|---|
| test guard 削除で DoD の定義が誤読される | 中 | PLAN 上で DoD #3 を式として明記し、fixture と assert の対応を固定化 |
| `HELIX_TEST_TODAY` の存在依存が暗黙残存 | 低 | 環境変数依存を docs 化し、日付モック用途のみ利用することを明確化 |
| テストが PLAN-014 の既存 DoD を回帰で破る懸念 | 中 | DoD #1/#2/#4 を本文に明示し、レビュー時に「既存テスト 1 組保持」を必須条件化 |
| 1 回の文言変更を起点に CLI 仕様理解の齟齬が発生 | 低 | §3.4/#4 で “常時 INSERT” の仕様に統一 |

## §4. 実装計画

### §4.1 Sprint

| Sprint | 内容 | 担当 |
|---|---|---|
| .1 | bats RED 化：DoD #3 を新仕様に置換 | Codex PG (`--thinking low`) |
| .2 | `cli/helix-session-summary` の `HELIX_TEST_TODAY` 分岐削除（1 ファイル 10 行未満想定） | Codex PG (`--thinking low`) |
| .2.5 | bats GREEN で DoD #3 の pass を確認 | Codex PG |
| .3 | helix test（shell / pytest / bats）再実行 | Codex QA（結果共有） |
| .4a | Retro 起草（`.helix/retros/2026-05-03-G4-PLAN-015.md`） | Codex docs |
| .4b | `handovers` 更新・commit（PLAN 側反映） | Opus |

### §4.2 G4 ゲート判定基準

- DoD #1〜#5 全て PASS（うち #1/#2/#6-既存 は PLAN-014 既存の継続 pass）
- `helix-codex review --uncommitted` の重大指摘なし
- 新規/既存の deferred-finding が P1/P2 に増えないこと
- テスト結果の再現性（fixture 0 件 + 1 回実行）をレビューコメントに添付
- 並行発火時の eventual consistency 仕様 (DoD #5) を retro に明文化

## §5. 後続候補

PLAN-014 §5 の「session-summary を md ではなく `helix log report` で代替」案を継続する。

- 目的: session-summary を再生成可能なレポート出力として統合し、md ファイル依存を段階的に排除する
- 想定効果: md 側の運用ノイズを抑制し、監査性を高める
- 受け皿: 別 PLAN（PLAN-016 以降）で検討

## 参考資料

- [`docs/plans/PLAN-014-stop-hook-idempotency.md`](docs/plans/PLAN-014-stop-hook-idempotency.md)
- [`.helix/retros/2026-05-03-G4-PLAN-014.md`](.helix/retros/2026-05-03-G4-PLAN-014.md)
- [`cli/helix-session-summary`](cli/helix-session-summary)
- [`cli/tests/test-helix-session-summary.bats`](cli/tests/test-helix-session-summary.bats)

## TODO 残存確認

- 本文内に未解決 TODO/FIXME は未記載（0 件）

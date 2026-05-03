# PLAN-014: Stop hook idempotency — session-summary 重複行抑制 (v1.1 reviewed)

## §1. 目的 / position

`Stop` hook (`cli/helix-session-summary`) は `.helix/session-summaries/<TODAY>-session.md` に毎回 append-only でセクションを追加する仕様になっている。Claude Code の Stop hook は短時間 (数十秒〜数分) に複数回発火するため、同日の summary ファイルに「セッション終了 + コスト記録」だけのほぼ同一セクションが大量に積み上がる現象が発生する (PLAN-013 セッションでは 1 日 58 件)。

実害:
- session-summary の信号対雑音比が悪化し、retro / G4 振り返り時の可読性が落ちる
- `git diff` のノイズが増え、毎セッション chore commit が必要になる (PLAN-013 終結セッション 33f7375 参照)
- file 末尾だけが本当に意味のある状態だが、視覚的に終端を判別しにくい

PLAN-014 は **当日内 Stop hook 出力の冪等化** を実装し、append-only から rewrite-aware (= 当日セクションは 1 つに集約) に切り替える。

参考: G4 retro `.helix/retros/2026-05-03-G4-PLAN-013.md` Try 列「Stop hook idempotency」を本 PLAN として起票。

## §2. スコープ

### §2.1 in-scope

- `cli/helix-session-summary` の出力ロジック改修
  - 当日のサマリブロックを 1 つだけ保持し、Stop hook 再発火時は当日ブロックを上書き
  - 別日の既存ブロックはそのまま保存
- 当日ブロック内の表現フォーマット
  - 「最終更新タイムスタンプ」+「当日内の終了回数」+「Hook イベント / ゲート実行 / コスト記録の当日合計」
  - 個別タイムスタンプの履歴は破棄 (DB 側 `cost_log` / `hook_events` に永続化されているため md 側で持つ意味は薄い)
- 既存ファイルへの破壊的変更なし
  - 過去日付のブロックは現状維持
  - migration スクリプトは不要 (今後の出力のみ idempotent 化)
- bats による idempotency 検証
  - 同日内 5 回連続発火で `grep -c '^## セッション終了' = 1` を確認
  - 別日 (date モック) で 2 ブロック存在することを確認

### §2.2 out-of-scope

- DB schema 変更 (`cost_log` / `hook_events` の構造は触らない)
- Stop hook 自体の置き換え (Stop → SessionEnd 等の移行は別議論)
- 他 hook (`PreToolUse` / `SessionStart` 等) の冪等化
- 過去サマリファイルの遡及圧縮 (`.helix/session-summaries/2026-04-* / 05-*` 既存ファイルは触らない)
- `helix log report` 系の rewrite (md の見え方とは独立)
- session-summary を別ファイルに分離する設計 (PLAN-014 では現行 1 ファイル運用のまま)

## §3. 要件 / 設計

### §3.1 idempotent rewrite 仕様

- 当日 (`TODAY=$(date +%Y-%m-%d)`) のセクションヘッダ: `## 2026-05-03 セッション (最終更新 HH:MM, 終了 N 回)` の 1 行に集約
- ブロック内訳:
  - 「Hook イベント」表 (今日合計、`COUNT(*) GROUP BY event_type`)
  - 「ゲート実行」表 (今日合計、`gate, result`)
  - 「コスト記録」表 (今日合計、`role, model`)
- 「終了 N 回」: `cost_log` の `role='opus-pm'` `date(created_at)=today` の row 数で算出
- 別日のブロックは追記された時点で凍結 (rewrite 対象外)

### §3.2 ファイル更新アルゴリズム (atomic rewrite)

1. `<TODAY>-session.md` を読み込み、当日ブロックの開始/終了行を検出
2. 当日ブロックがあれば該当範囲を切り出し、最新サマリで置換
3. なければ末尾に追記
4. 別日の既存セクションはそのまま保持
5. 書き出しは **atomic rewrite**:
   - 同一ディレクトリの一時ファイル (`<TODAY>-session.md.tmp.<pid>`) に新内容を `write + fsync`
   - `os.replace` (= `rename(2)` POSIX atomic) で本ファイルを置換
   - 失敗時は temp file を削除してエラー終了 (Stop hook の `blockOnFailure: false` を尊重)
6. **並行起動の排他制御**:
   - file-level の `flock(LOCK_EX | LOCK_NB)` を `<TODAY>-session.md.lock` に取り、取れなければ skip (= 他プロセスが書き込み中なら自分は書かない、次回 Stop hook で巻き戻る)
   - rewrite-aware の冪等性により、skip しても情報損失は発生しない

ブロック境界 (動的日付前提):
- 開始: 行頭 `^## ${TODAY} セッション` (例: `^## 2026-05-03 セッション`)
- 終了: 次の `^## ` 行 / EOF
- 旧フォーマット (`^## セッション終了: <DATE> <TIME>`) はマッチしないため破壊しない (互換性確保)

### §3.3 互換性

- 既存ファイルに古いフォーマット (`## セッション終了: 2026-05-03 06:48` 個別形式) が残っていても新フォーマットの当日ブロックを末尾に 1 つだけ書き、古いセクションは保存
- 翌日になったらその日の最初の Stop hook で新規ブロックを追加 (前日のブロックは凍結)

### §3.4 DoD

| # | 条件 | 検証方法 |
|---|---|---|
| 1 | 同日 5 回連続 Stop hook → `<TODAY>-session.md` 内で `grep -cE '^## [0-9]{4}-[0-9]{2}-[0-9]{2} セッション \(最終更新' = 1` | bats |
| 2 | 別日のブロックは保存される (date モック 2 日分): **`2026-05-03-session.md` と `2026-05-04-session.md` がそれぞれ独立に存在し、各ファイル内の当日ブロックは 1 つ** (= 日次 1 ファイル + ファイル内 1 ブロックの両条件) | bats |
| 3 | 当日ブロックの「終了 N 回」が cost_log の today 件数と一致 | bats / pytest |
| 4 | 既存サマリファイルに古いフォーマット (`^## セッション終了: <DATE> <TIME>`) があっても破壊しない (head 部分が一致するという互換性 assertion を独立に検証) | bats |
| 5 | helix test 全 PASS (shell / pytest / bats) | helix test |
| 6 | 並行起動 2 プロセスが同時に発火しても本ファイルが破壊されない (`os.replace` の atomic 性 + flock skip 経路) | bats (並行起動シミュレーション) |

### §3.5 サイジング

- size: S (helix-size: files=1 lines=~80 type=refactor drive=be)
- phases: L4 のみ
- ファイル: `cli/helix-session-summary` (1)
- テスト: `cli/tests/test-helix-session-summary.bats` (新規 or 既存に追加)
- 影響範囲: Stop hook 出力のみ (DB / 他 CLI 不変)

### §3.6 リスクと緩和

| リスク | 影響 | 緩和 |
|---|---|---|
| 既存ファイルが想定外フォーマット (手編集) で破壊 | M | rewrite 対象を「当日セクションのみ」に限定し、unknown header があれば追記モードに fallback |
| Hook timeout (現状 8s) を超過 | L | 単一ファイル read+rewrite は ms オーダー、計測で確認 |
| date 境界をまたぐ Stop hook (深夜跨ぎ) | L | header 行に日付を含めるため、`date` が変わった時点で別ブロック扱いになる |
| 並行 Stop hook 発火による file 破壊 (P2-1 by TL review) | M | atomic rewrite (`os.replace`) + `flock(LOCK_EX|LOCK_NB)` skip 経路、§3.2 と DoD #6 で凍結 |
| ファイル単位 vs ブロック単位の期待値混乱 (P2-2 by TL review) | L | DoD #2 で「日次 1 ファイル + ファイル内 1 ブロック」の両条件を凍結、§3.1 セクションヘッダで日付を含むことを明記 |

## §4. 実装計画

### §4.1 Sprint

| Sprint | 内容 | 担当 |
|---|---|---|
| .1 | bats スケルトン (DoD #1〜#4 の failing test) | Codex QA |
| .2 | `cli/helix-session-summary` rewrite ロジック実装 (atomic rewrite + flock) | Codex SE |
| .3 | helix test 全 PASS 確認 + DoD #1〜#6 検証 | Codex QA |
| .4a | retro 起草 (`.helix/retros/2026-05-03-G4-PLAN-014.md`) | Codex docs |
| .4b | retro レビュー + handover clear + commit | Opus |

> 担当原則: Opus = PM (レビュー / 統合判断 / finalize / handover 操作のみ)。実装・テスト・文書本文起草は Codex 各ロールへ委譲する。

### §4.2 G4 ゲート判定基準

- DoD #1〜#5 全て PASS
- helix-codex review --uncommitted で重大指摘なし
- accuracy_score 算定: deferred-finding が新規追加されないこと

## §5. 後続候補 (本 PLAN 範囲外)

- PLAN-015 候補 (PLAN-013 retro Try): deferred-findings 18 件 P2 burn-down + seed_promotable heuristic + cli-lib enforce
- session-summary を md ではなく `helix log report session --date <DATE>` でオンデマンド生成する案 (現行 md 廃止)

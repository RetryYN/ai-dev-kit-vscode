---
plan_id: PLAN-037
title: PLAN-037（helix-codex usage limit fallback + PLAN lint 拡張 + bats marker 一括適用）
status: completed
created: 2026-05-10
finalized: 2026-05-10
author: Opus (PM)
size: M
phases: L1→L2→L3→L4
gates: G1, G2, G3, G4
completed: 2026-05-10
acceptance:
  - W-0: PLAN-036 retro carry 4 件を PLAN-037 の Sprint 構成へ再配線し、相互依存と担当分離が明確であること。
  - W-1: `helix-codex` が usage limit 検知時に opt-in で role primary の自動 fallback を行えること。
  - W-23: PLAN lint が section 横断の重複検出と allowlist 最小化を扱えること。
  - W-4: 既存 `cli/tests/*.bats` へ `helix_bats_mark` を機械的に適用し、共通 helper の導線が揃うこと。
related: [PLAN-036, PLAN-035, PLAN-034, PLAN-033, PLAN-032, PLAN-031, ADR-014, ADR-015]
---

## §1 目的

PLAN-036 retro carry 4 件のうち、次 Sprint へ集約して処理すべき項目を PLAN-037 として起票する。

本 PLAN の狙いは、実装経路ごとの責務を分離したまま、以降のレビュー・検証・回帰防止を進めやすい状態へ整えることにある。

対象は次の 4 点である。

- W-1: `helix-codex` の primary model usage limit auto-fallback
- W-23: PLAN lint の拡張
- W-4: 既存 `cli/tests/*.bats` への `helix_bats_mark` 一括適用
- W-5: 統合検証と retro placeholder 更新

本 PLAN は draft 起票のみを目的とし、実装・TL レビュー・ハードな仕様変更は別 Sprint で扱う。

## §2 スコープ

### §2.1 対象範囲

- W-1 は `cli/helix-codex` を中心に、usage limit 到達時の fallback 経路を明示化する。
  - 既存の `--fallback-model` は別系統として維持する。
  - opt-in の環境変数でのみ動作させる。
  - fallback の発火と選択先は stderr で可視化する。
  - 参照元は `cli/config/models.yaml` の role 定義とする。

- W-23 は `cli/lib/plan_lint.py` と `cli/tests/test-helix-plan-lint.bats` を軸に、PLAN の書式と記述ルールを広げる。
  - 一つの W-N に対して複数箇所で同種説明が繰り返される場合を拾う。
  - 仕様起票元 PLAN の一部セクションだけを allowlist する。
  - frontmatter と本文の責務境界を保つ。

- W-4 は既存 bats 群の共通準備を整える作業 (機械的 sed ではなく Codex 委譲、§4.5 参照)。
  - `cli/tests/_helix-bats-helper.bash` を前提とする。
  - setup の共通化導線を各ファイルへ揃える。
  - 既存 **57 ファイル** (実 inventory) を対象に分類後、helper source 既存 1 ファイル + その他に応じた個別 Edit を実施。

### §2.2 スコープ境界 (簡略宣言、詳細は §7)

本 PLAN の境界は以下に短く要約する。詳細列挙と差分は §7 を参照:

- HELIX 内 (今回扱う): helix-codex auto-fallback / plan_lint 拡張 / 既存 bats helper 適用
- HELIX 外 (扱わない): 外部 API / 認証 / 決済 / PII / secret / state-events 再設計

## §3 受入定義

### §3.1 carry の再定義

- W-1 は usage limit 検知を人手介入なしで role chain へ渡せることを目標とする。
- W-23 は lint の警告範囲を広げつつ、過検出を抑えたまま運用できることを目標とする。
- W-4 は共通 helper の導線が既存 bats 全体に広がることを目標とする。

### §3.2 完了条件

- 各 W が独立に完了判定できる。
- 依存関係が Sprint 表から一読で分かる。
- 後続の TL レビューでそのまま検証可能な粒度になっている。

## §4 Sprint 表（PLAN-037）

### §4.1 全体構成

- W-0: draft 起票 + TL 2 ラウンドレビュー + finalize 準備
- W-1: `helix-codex` usage limit fallback
- W-23: PLAN lint 拡張
- W-4: bats marker 一括適用
- W-5: 統合検証 + retro placeholder + 完了判定

| Sprint | 役割 / 規模 | 担当 | 主要作業 | 成功条件 | 受入 / 検証 |
|---|---|---|---|---|---|
| W-0 | Docs/Plan（S） | Docs（本体） / TL | PLAN-037 起票、carry 再配線、節構成の整合 | 依存と担当軸が読み取れる | plan レビュー |
| W-1 | Code / axis-1（M） | SE | usage limit 検知、fallback chain、stderr ログの導線 | opt-in で自動切替できる | 新規 bats / 回帰確認 |
| W-23 | Code / axis-2（S-M） | SE | 重複検出と allowlist 最小化、lint 例外の整備 | 重複と例外の両立 | `cli/tests/test-helix-plan-lint.bats` |
| W-4 | Code / axis-3（M） | pg または se (Codex 委譲、Opus 直接 sed は採用しない) | 既存 57 bats を 4 区分に分類、target 区分のみに helper 追加 (実数は inventory 確定) | 全体で同一導線、skip 分類は touched なし | inventory file + git diff --stat 確認 |
| W-5 | Docs/Validation（S） | Docs / TL / PM | carry 反映、retro placeholder、次回着手条件 | 完了判定の材料が揃う | 統合レビュー |

### §4.2 W-0

- output: `PLAN-037` draft 起票
- quality:
  - carry 4 件の責務を分割したまま記録できること
  - 既存 PLAN 群との参照関係が壊れないこと
  - status は frontmatter にのみ置くこと
- review focus:
  - 目的と受入条件の対応
  - Sprint 表と §5 リスクの整合
  - 参照先 PLAN のリンク妥当性

### §4.3 W-1

- 目的: usage limit に達した `helix-codex` の実行を、中断ではなく別 role の primary model へ渡せるようにする。
- 実装の輪郭:
  - `cli/helix-codex` に検知処理を置く
  - `HELIX_CODEX_AUTO_FALLBACK=1` を起点にする
  - role chain は `cli/config/models.yaml` の役割定義に合わせる
  - stderr に fallback 先を明示する

- 既存 fallback との優先順位 (P1-1 解決、cli/helix-codex:651 default_fallback / line 1157 FALLBACK_MODEL との境界明確化):
  1. **layer 0**: `--fallback-model` 明示指定があればそれを最優先 (既存挙動維持)
  2. **layer 1**: `default_fallback` (models.yaml の role 別 fallback、既存挙動維持)
  3. **layer 2 (新規、本 PLAN W-1)**: 上記 2 つが exhausted (試行済 + 失敗) かつ `HELIX_CODEX_AUTO_FALLBACK=1` の場合のみ、別 role の primary model に切替
  4. layer 2 は usage limit 系 stderr (`hit your usage limit`) を捕捉した場合のみ発火
  5. `HELIX_CODEX_AUTO_FALLBACK=0` または未設定なら layer 2 は無効、従来経路を完全維持

- stderr 検知経路 (P1-2 解決、cli/helix-codex:1109-1124 stdout tee / line 1070 classify_codex_error が exit code のみであることへの対処):
  - `run_codex_once` で codex stderr を **process substitution `2> >(tee -a "$STDERR_FILE" >&2)`** で audit log に保存しつつ、**stderr fd を維持** して呼び出し元にも通常通り流す (Round 2 P1 反映: `>&2` を明記しないと Codex stderr が stdout 側へ流れる回帰を招く)
  - `classify_codex_error` を 2 引数化 (exit_code + stderr_file)、stderr に `hit your usage limit` を grep -q で検査
  - 検出時は `usage_limit` 種別を返す (新規)、auto-fallback 経路へ進む
  - pattern 大小文字差: `grep -qi 'hit your usage limit'` で case-insensitive、文言差吸収

- role chain 定義 (cli/config/models.yaml の roles を正本):
  - `pg primary fail` → `pe primary` 試行 → `se primary` 試行 → 諦めて exit 1
  - `pe primary fail` → `pg primary` → `se primary` → exit 1
  - `se primary fail` → `tl primary` → exit 1
  - `qa primary fail` → `se primary` → exit 1
  - `tl primary fail` → exit 1 (fallback なし、致命的なので Opus 介入が必要)

- DoD:
  - opt-in 以外では従来経路を変えない (回帰テスト)
  - usage limit 系メッセージだけを拾う (他の error は従来通り network/other 分類)
  - 既存 `--fallback-model` と挙動が干渉しない (layer 0 が最優先)
  - audit log (`.helix/audit/codex-runs/<ts>-<role>-stderr.log`) に stderr が保存される

- 追加検証 (新規 bats `cli/tests/test-helix-codex-auto-fallback.bats`、layer 順序を反映):
  - **layer 順序の前提**: 現行 `cli/helix-codex:651` で default_fallback が指定されると FALLBACK_MODEL に自動設定される。usage limit + AUTO_FALLBACK=1 のテストでは **まず layer 1 (default_fallback) が試行され、それでも失敗した場合に layer 2 が発火** する順序を再現する
  - mock codex で usage limit stderr (1 回目) → layer 1 fallback model で再試行 (2 回目) → layer 1 でも usage limit (3 回目で別 role primary 試行) という連鎖を mock で表現
  - mock codex で usage limit stderr + AUTO_FALLBACK=0 (default) → layer 1 までで止まる (従来通り exit 1)、layer 2 は発火しない
  - mock codex で usage limit 以外のエラー stderr + AUTO_FALLBACK=1 → layer 1 (default_fallback / FALLBACK_MODEL) を経由、layer 2 (role chain) は **試さない** (usage limit のみが trigger)
  - `--fallback-model` 明示 + usage limit + AUTO_FALLBACK=1 → layer 0 (--fallback-model) が最優先で、それ exhausted → layer 2 発火

### §4.4 W-23

- 目的: PLAN lint を、単一節の整合確認から section 横断の構造チェックへ広げる。
- 実装の輪郭:
  - `cli/lib/plan_lint.py` で重複検出の入力を増やす
  - similarity ベースの警告を追加する
  - allowlist を lint 仕様セクションに限定する
  - `cli/tests/test-helix-plan-lint.bats` で警告と除外の両方を固定する

- W-23-A 重複検出 (Round 2 P2-1 反映、日本語向け正規化を採用):
  - **検出単位**: 同一 W-N (例: W-1) について「影響範囲」「DoD」「Test Plan」が §2.1 と §4.x の両方に記述されている場合、文言の類似度を計算
  - **tokenization (日本語対応)**: 行頭 `-` / `*` / 数字 prefix 除去 → 記号 (英数字以外、句読点) 削除 → **文字 3-gram に分割** → set 化 (Round 2 P2 反映: 空白 split だと日本語文で 0.05〜0.17 程度しか出ず 0.6 閾値届かない、3-gram で実用的な類似度に)
  - **類似度**: Jaccard similarity on 3-gram set (`|A ∩ B| / |A ∪ B|`)
  - **閾値 (実測ベース、PLAN-031〜037 の重複済み箇所で実測して再校正)**:
    - 0.4 以上: warn (重複疑い)
    - 0.7 以上: warn 強調 (強い重複)
    - 実測校正: PLAN-037 W-1 § 2.1 vs §4.3 の DoD ペアで Jaccard 計算し閾値を最終確定 (W-23 実装時に Codex se が実施)
  - **比較対象ペア**: §2.1 W-N の bullet と §4.x W-N の同一概念見出し (DoD / 影響範囲 / Test Plan / 実装方針) の対応 bullet
  - **warn 出力形式**: `{plan_file}:{line_no}: WARN: W-{n} '{kind}' duplicated with §{n.m} (similarity={score})` (stderr、exit 0 維持)
  - **error にしない理由**: 重複は意図的な強調や crystal clear な仕様でも発生するため、error は過検出リスクが高い

- W-23-B allowlist 最小化 (Round 2 P2-2 反映、見出し regex を実形式に固定):
  - **現状 (plan_lint.py:140-142)**: PLAN-036 全体を skip
  - **新方針**: PLAN 全体 skip を **廃止**、§4.x.y の lint 仕様サブセクション (e.g. §4.4 配下の lint 検出パターン記述箇所) のみ skip
  - **見出し regex (実見出し形式に固定)**:
    - lint 仕様セクション開始: `^### §\d+\.\d+ W-\d+` (例: `### §4.4 W-23`、`### §4.4 W-23（lint 拡張）` 等)
    - 終了条件: 次の同レベル見出し `^### §\d+\.\d+` または上位見出し `^## ` の出現
    - サブセクション内のさらなる見出し `#### W-23-A` 等も配下スコープに含める
  - **判定フロー**: 「lint 仕様起票元 PLAN」と判定されたら (frontmatter で declared、または特定 marker comment) 、上記 regex で `### §X.Y W-N` 見出しを検出 → 終了条件まで配下 bullet を allowlist
  - **実装**: 現行 SKIP_SECTION_KEYWORDS を見出し階層 + 配下スコープ判定に拡張、PLAN-036 専用 skip を削除し、PLAN-036/PLAN-037 の `### §4.W-N` 配下のみ skip
  - **frontmatter marker 例**: `lint_self_reference: true` (PLAN-036/037 で declared、その他 PLAN は false)

- DoD:
  - 同一 W-N の多重説明を warn として拾える (Jaccard 0.6 閾値)
  - PLAN-036 / PLAN-037 の一般本文 (§2 §3 等) は通常 lint される (status 整合)
  - 既存の status lint を壊さない (regression 防止)
  - PLAN-031〜035 への retroactive 適用なし (運用は PLAN-036+)

- 追加検証:
  - W-23-A 完全一致 (Jaccard 1.0): warn (強調)
  - W-23-A 近似一致 (Jaccard 0.7-0.9): warn (通常)
  - W-23-A 無関係 (Jaccard < 0.6): 検出なし
  - W-23-B 仕様起票元 PLAN の §4.W-N 配下: skip
  - W-23-B 仕様起票元 PLAN の §2.1 / §3 / §5: 通常 lint 適用
  - 既存 status lint の 6 ケース (PLAN-036 W-2): 全て PASS 維持

### §4.5 W-4

- 目的: bats 群の共通準備を揃え、今後の追加作業を減らす。
- **実態 (P1 Round 2 反映、`git ls-files 'cli/tests/*.bats'` 実測)**: **57 ファイル**。grep 検証結果:
  - `mktemp -d` または `TMP_ROOT` を含むファイル: **54 ファイル** (主要 target 候補)
  - `HELIX_TEST_TMPDIR` を使用するファイル: subset (target-tmpdir-var として個別対応)
  - `_helix-bats-helper.bash` を既に source 済: **1 ファイル** のみ (PLAN-036 W-3 で導入、おそらく test-helix-bats-cleanup.bats)
  - tmp dir を全く作らないファイル: 残り (skip)
- 正確な分類は W-4-a inventory フェーズで実測する
- **方針 (機械的 sed → Codex 委譲に変更)**:
  - W-4-a (inventory + skip list): 全 57 ファイルを以下 4 区分に分類し `.helix/audit/plan-037-w4-inventory.txt` に出力
    - `target-tmp-root` (TMP_ROOT を mktemp で作成、helper 未 source): 主要対象
    - `target-tmpdir-var` (HELIX_TEST_TMPDIR 等の他変数を使用): 個別 helix_bats_mark "$HELIX_TEST_TMPDIR" で対応
    - `skip-no-tmp` (tmp dir を全く作らない、helper 不要): skip
    - `skip-already-marked` (helper 既に source 済、実測 1 ファイル): skip
  - W-4-b (実装): target-tmp-root / target-tmpdir-var の合計を Codex pg/se が個別 Edit で慎重対応 (実数は inventory で確定、仮見積では 50 件前後だが、実 inventory を正本とする)
  - **Opus 直接 sed は採用しない** (setup() 構造多様で誤適用リスク高、PLAN-035 W-2 は teardown の単一 pattern 置換で安全だったが、W-4 は setup() 内の variable-aware insertion で性質が異なる)
- 実装担当: Codex pg または se (Opus 直接ではなく、L3 設計に委譲)
- DoD:
  - W-4-a inventory 出力ファイル (`.helix/audit/plan-037-w4-inventory.txt` 等) で 57 ファイルが 4 区分に分類されている
  - target / target-tmpdir-var ~35 ファイルに helper source + helix_bats_mark 追加
  - skip-no-tmp / skip-already-marked ~22 ファイルは touch しない
  - bats 全 360 ファイル PASS (regression なし)
- 追加検証:
  - 各 target bats の setup 内に helper 読み込み行が存在
  - marker 登録位置が tmp root 生成後 (`mktemp -d` の直後 or `export TMP_ROOT=...` の直後)
  - skip-* に分類された bats が touched されていない (`git diff --stat` で確認)

### §4.6 W-5

- 目的: carry 4 件の完了条件を統合し、次 Sprint に引き継ぐ材料へ変える。
- 実施:
  - W-1/W-23/W-4 の受入条件を照合する
  - retro placeholder を更新する
  - 次段階の判定材料を整理する
- 完了判定:
  - 個別 W の成立可否が記録されている
  - 残件が次 Sprint へ自然に分かれる
  - ドキュメント参照が一意である

## §5 リスク登録

- R-1: usage limit の検知文字列が広すぎると、意図しない fallback を起こす可能性がある。
  - 対策: 既知の失敗文言に寄せて検出を絞る。

- R-2: role chain の fallback 先が不明瞭だと、想定外の role に流れる可能性がある。
  - 対策: `cli/config/models.yaml` を正として参照する。

- R-3: lint の拡張で警告が増えすぎると、レビューのノイズになる。
  - 対策: allowlist を狭く保ち、warn に留める。

- R-4: bats の機械的適用は差分量が大きく、setup 順序の崩れを招く。
  - 対策: helper 読み込みと marker 追加を分けて確認する。

- R-5: PLAN-037 自身が lint のテストケースになるため、自己矛盾が起こりやすい。
  - 対策: status の記述は frontmatter に限定し、本文では断定を避ける。

## §6 テスト計画

### §6.1 W-1

- usage limit 検知の分岐確認
- fallback 発火時の stderr 確認
- `--fallback-model` と独立であることの確認

### §6.2 W-23

- `cli/tests/test-helix-plan-lint.bats` の追加
- 完全一致と近似一致の warn 確認
- allowlist セクションの非検出確認

### §6.3 W-4

- 既存 bats **57 ファイル** (実 inventory: `git ls-files 'cli/tests/*.bats'`) のうち target 区分への helper 導線確認
- W-4-a inventory 出力 (`.helix/audit/plan-037-w4-inventory.txt`) で 4 区分が記録されていること
- setup 先頭周辺の挿入位置確認 (mktemp -d / TMP_ROOT export 直後)
- marker 登録が tmp root 生成後であることの確認
- skip-* 区分 (helper 既 source 1 ファイル + tmp 作らない bats) は touched なしで diff stat 確認

### §6.4 W-5

- carry 4 件の完了条件を照合
- retro placeholder 更新の妥当性を確認
- 次 Sprint への引継ぎ可否を判定

## §7 Out of Scope (差分のみ詳細列挙、§2.2 と重複させない)

§2.2 で「HELIX 外 (外部 API / 認証 / 決済 / PII / secret / state-events 再設計)」は宣言済。本節は **§2.2 で語っていない HELIX 内のスコープ境界** のみ列挙する:

- 既定の role policy の再設計 (cli/config/models.yaml の roles 構造 / primary 既定値変更は本 PLAN 範囲外、参照のみ)
- lint 規約の全面書き換え (W-23 は既存 status lint への拡張のみ、文書スタイル全面再定義は別 PLAN)
- bats の新規スイート設計 (W-4 は helper 適用のみ、新規 .bats ファイル追加は別 PLAN)
- 既存 PLAN-031〜035 への retroactive 適用 (W-23 lint allowlist の最小化は PLAN-036+ から運用)
- HELIX_CODEX_AUTO_FALLBACK の default 有効化 (default disable で opt-in、本 PLAN は default 切替を扱わない)
- `--fallback-model` 既存挙動の変更 (W-1 layer 0 として最優先維持、変更しない)

本節は「何をやらないか」を固定する役割に限定し、§2.2 と重複させない。

## §8 実装 Notes

- 参照ドキュメント:
  - [PLAN-031-carry-resolution](PLAN-031-carry-resolution.md)
  - [PLAN-032-helix-test-and-concurrent-resolution](PLAN-032-helix-test-and-concurrent-resolution.md)
  - [PLAN-033-drift-check-and-baseline-cleanup](PLAN-033-drift-check-and-baseline-cleanup.md)
  - [PLAN-034-codex-output-and-prompt-template](PLAN-034-codex-output-and-prompt-template.md)
  - [PLAN-035-helix-review-and-bats-cleanup](PLAN-035-helix-review-and-bats-cleanup.md)
  - [PLAN-036-codex-post-validation-and-bats-cleanup](PLAN-036-codex-post-validation-and-bats-cleanup.md)
- carry 配線:
  - PLAN-036 からの retro carry を W-1/W-23/W-4 に振り分ける
  - W-5 で統合判断へ戻す
- 補足:
  - 本 PLAN は状態遷移を frontmatter に集約する前提のテストケースでもある

## §9 Retro Placeholder

- Keep
  - carry を一つの PLAN に再集約してから Sprint 単位に分ける構成を維持する
  - 参照ドキュメントを plan ファイル側で追跡しやすくする
  - role / file axis を分けて並列衝突を抑える

- Problem
  - usage limit の実際の文言差で fallback 判定が揺れる可能性がある
  - lint の重複検出は閾値調整を誤るとノイズ化しやすい
  - bats の機械的適用は差分レビューが重くなる

- Try
  - まず既知 failure 文言を起点に検知条件を絞る
  - 重複検出は warn のみで始める
  - bats の適用結果をファイル単位で確認できる形にする

## §10 更新履歴 / 承認ログ

- 2026-05-10: draft 起票（Codex Docs）
- 2026-05-10: PLAN-036 retro carry 4 件を W-1/W-23/W-4/W-5 に再配線

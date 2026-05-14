---
plan_id: PLAN-022
title: "PLAN-022: HELIX オーケストレーション層実機能化 (skill 推挙 + 自動発火 + thinking 必須化)"
status: completed
size: M
drive: be
created: 2026-05-06
owner: PM
phases: L1, L2, L3, L4, L6
gates: G2, G3, G4
acceptance:
  - skill chain 義務化が CLAUDE.md に反映され、Codex 委譲は recommender 経由が default
  - session-start で handover task → skill 推奨が自動発火する
  - helix-codex が動的 skill 推挙を取り込み、role-conf の codex_thinking が必須化される
  - 全 20 ロール conf に codex_thinking フィールドが揃っている
  - helix skill stats に hit_rate 集計が表示される
  - ADR-006 (skill chain) と ADR-007 (effort field 伝搬) が更新済
  - skill 自動発火 統合テストが 25/25 で PASS
related:
  - PLAN-023 (残課題 3 件解消)
  - PLAN-024 (W-1a で PLAN-022 残課題 1 件を取り込み)
  - ADR-006
  - ADR-007
---

# PLAN-022: HELIX オーケストレーション層実機能化 (skill 推挙 + 自動発火 + thinking 必須化)

## §1 背景・目的

### 1.1 仕組み倒れ状態からの脱却

PLAN-022 は、定義だけ存在して実行経路に乗っていなかった skill 推挙関連機能を、runtime 経路に接続し直した取り組みである。  
問題は主に 3 点だった。

- `recommender` 呼び出しが想定どおり起動しない。
- `helix-codex` が task 文脈に応じた追加 skills を取り込めない。
- `thinking` 制御の不統一（role conf 未定義時の暗黙動作）で、エンジンリソースの最適化が実現していない。

この結果、既存設計（PLAN-011 以降の skill chain / CLAUDE.md 方針 / session-start / handover 流儀）と runtime が乖離していた。

### 1.2 解決したい実行要件

- recommender (gpt-5.4-mini) と effort-classifier を、セッション起点の自動実行に含める。
- `Codex` 委譲を `helix codex ... --skill` 前提に統一し、skill chain を実行経路の必須要件にする。
- `recommender` 実行時に動的な skill 推挙を取り込み、固定パスだけでなく task 文脈対応を実現する。
- 各 role conf の `codex_thinking` を必須化し、Thinking トークン消費を role/難易度に即時最適化する。

### 1.3 背景に対する実装ゴール

- skill chain の全経路において「未設定 = 動かない」の状態を排除する。
- セッション開始時に `helix skill search` へ自動接続する。
- 動的推挙を経由しても、policy 検証を壊さずに処理を通せるようにする。
- 統計が観測可能な形で改善し、`hit_rate` を sessions 単位で真値取得できる状態を作る。

### 1.4 参照コンテキスト

本 PLAN は、次の観測資料を前提とした completion document として起票した。

- 実装 commit log（8 commits）
- memory リリース報告（PLAN-022/023 合同 report）
- PLAN-023 の残課題整理（policy 誤判定、sessions 単位、effort 伝搬）
- ADR-006 / ADR-007 の更新情報

memory 要約としては、PLAN-022 は `2aa96bf` から `1caecdd` までの主要実装と、  
`PLAN-024` で吸収された `tl.conf` の `codex_thinking` 抜けを前提に、実 run 状態へ統合済みである。

## §2 実装内容 (Sprint .1b〜.5)

本章は実装 commit 毎に、目的・変更・影響・検証の観点を1ブロック化して記録する。  
記載順は既存 commit 時系列に合わせる。

### 2.1 Sprint .1b (2aa96bf): skill chain 義務化 + pg=low + ADR-006 修正

#### 2.1.1 目的

- skill chain を「運用仕様」ではなく「実行仕様」に昇格する。
- `pg` の thinking が低負荷化されるよう、`codex_thinking=low` を明示し、不要な思考トークンを抑える。
- ADR-006 を現状仕様と整合する形に補正する。

#### 2.1.2 変更点

- skill chain を実行パスとして必須化し、CLAUDE.md 等へ明示反映。
- `.claude/CLAUDE.md` 側にも skill chain 運用基準を追加。
- `pg.conf` の thinking 値を `low` とし、pg パイプラインのコスト最適化を調整。
- ADR-006 の修正文言を、実装完了後の挙動と矛盾しない形へ更新。
- fe 系の冗長 agent 定義（5件）を整理し、既存 skill 呼び出し競合を低減。

#### 2.1.3 受入との対応

- 受入1: skill chain の義務化が運用に反映されること。
- 受入7: ADR-006 反映状態を維持すること。
- 追加確認: `pg` の実行経路が低思考でも安定すること。

#### 2.1.4 補足

このブロックは、後続の「動的推挙」「自動発火」「stats 集計」を有効化する土台である。  
まず固定方針を明文化し、実行時に未定義状態で fail しない設計に寄せるための準備段階として機能した。

### 2.2 Sprint .2 (e9f3486): session-start で handover task → skill 推挙の自動発火

#### 2.2.1 目的

- セッション開始時に手動実行を要求せず、handover task から自然に skill 推挙が起動すること。
- `helix skill` と `helix session-start` の接続を実行可能な一連操作に統一する。

#### 2.2.2 変更点

- session-start hook 側で handover task を受けると `HELIX_SKILL_HINT` が注入される流れを導入。
- 自動発火条件を task 文脈起点に接続（handover task の内容を推挙の seed として扱う）。
- 環境変数 / フック経路の境界を明確化し、意図しない手動起動を抑制。
- 自動化トリガ失敗時の既定ログを整備し、後続 debug を容易にした。

#### 2.2.3 受入との対応

- 受入2: session-start で handover task → skill 推挙が auto fire すること。
- 追加確認: `hand-over` 文脈でも既存の hook 流れを壊さないこと。

#### 2.2.4 補足

このブロック以前は、skill 推挙自体は「呼ばれれば動く」想定だったが、実利用で起動しないケースが残っていた。  
Sprint .2 は「起動トリガ」を補完し、運用時のボトルネックを消した。

### 2.3 Sprint .3 + W-P2-1b (7c66eca): helix-codex 動的 skill 推挙 + get_default_thinking 廃止

#### 2.3.1 目的

- task 文脈に応じた skill 候補を、固定スキル設定だけでなく実行時に動的に取り込む。
- 旧 `get_default_thinking()` に依存する fallback を撤去し、role conf 主導の必須化へ寄せる。

#### 2.3.2 変更点

- `helix-codex` が role ごとの標準 SKILL_PATHS に加えて、recommender/effort-classifier の動的推奨を merge できるよう変更。
- task 入力からの推挙情報を取り込む API 経路を追加。
- `get_default_thinking()` を廃止し、未定義時の暗黙 fallback を止める方針を実装に反映。
- role conf が不足している場合、明確に fail させる前提へ移行。

#### 2.3.3 受入との対応

- 受入3: helix-codex が動的 skill 推挙を取り込み、固定パスのみの運用に依存しないこと。
- 受入8 (派生): codex_thinking の欠落時の暗黙 default 仕様を排し、明示規約を強化する前提。

#### 2.3.4 補足

この変更で、実行時に `role+task` を受けて推奨されるスキル候補が増加し、  
`recommender` と `effort-classifier` が実際の委譲実行に参加しやすくなった。

### 2.4 Sprint .4 W-P2-1a (455e46e): 全 20 ロール conf に codex_thinking 必須化

#### 2.4.1 目的

- 20 ロールの conf で `codex_thinking` 欠如を無くし、thinking 設定の不一致をゼロ化する。
- `get_default_thinking()` 依存を撤去した状態で実行が通るように、設定起点の最小値を揃える。

#### 2.4.2 変更点

- `tl, se, pg, fe, qa, security, dba, devops, docs, research, legacy, perf, recommender, classifier, effort-classifier` ほか 20 ロールの conf に `codex_thinking` を追加・揃える。
- `high/medium/low/xhigh` の role 想定値を現行方針へ合わせる。
- `tl` など high 期待ロールは高めの thinking、`pg` は medium / low 設定で速度と精度バランスを維持するよう調整。
- 欠落時の暗黙挙動に頼らず、設定を必須入力に寄せる。

#### 2.4.3 受入との対応

- 受入4: 全 20 ロール conf に codex_thinking が揃うこと。
- 追加確認: 思考トークン量の肥大化と過度抑制のバランスが実運用で破綻しないこと。

#### 2.4.4 補足

ただしこのブロックは、`tl.conf` の `codex_thinking=high` が後続で不足として検知され、PLAN-024 へ carry される条件を残した。  
これは W-1a として明示 carry を行い、PLAN-024 で補完される。

### 2.5 Sprint .4 W-P2-2 (6e232dc): helix skill stats に hit_rate 集計追加

#### 2.5.1 目的

- skill 推挙の有効性を可視化し、運用改善の定量指標を作る。
- 推奨が「提案されるだけ」ではなく「実セッションで採用されるか」を監視可能にする。

#### 2.5.2 変更点

- `helix skill stats` 出力に `hit_rate` を追加。
- カウント母数・採用母数の扱いを明確化し、表示値の一貫性を確保。
- 指標の初期表示整形を更新し、定期レポートで比較できるようにした。
- sessions と結びつけた計測の前提を追加し、次段階で PLAN-023 の sessions 改修へ接続。

#### 2.5.3 受入との対応

- 受入5: helix skill stats が hit_rate を表示すること。
- 追加確認: 表示値が統合テストと矛盾しないこと。

#### 2.5.4 補足

この段階は UI での見た目拡張ではなく、運用改善に必要な観測データの埋め込みである。  
実際の値の true/false の意味解釈は、PLAN-023 で sessions 単位へ移行した点が前提。

### 2.6 Sprint .4 W-P2-3 (faa14fb): ADR-007 effort field の Agent tool 伝搬代替設計

#### 2.6.1 目的

- `effort` フィールドを Agent tool 経路へどう伝搬するかの標準設計を記録する。
- 公式実装の制約下で、代替設計の採用可否を明文化する。

#### 2.6.2 変更点

- ADR-007 をドラフトとして更新し、`Agent tool` 直通信での effort 伝搬が難しい場合の代替設計を提示。
- PROMPT injection / context prefix の選択を含め、実装可能な経路を設計書で明示。
- 後続の W-2 系で決定する前提の決め付けを防ぐため、受入/未確定事項を分離記載。

#### 2.6.3 受入との対応

- 受入6: ADR-007 が effort field 更新と整合し更新済みであること。
- 追加確認: 実装差分と ADR の意思決定が同一文脈で読み解けること。

#### 2.6.4 補足

本ブロックは「最終選定」そのものではなく、Option 列挙と移行原則の明文化を優先した。
そのため、PLAN-023 で Option A 決定へと進展した。

### 2.7 Sprint .5 W-T-3 (1caecdd): skill 自動発火統合テスト追加

#### 2.7.1 目的

- session-start 自動発火と統合スクリプト実行をテスト資産化し、回帰を検知できる状態にする。
- 統合規模で「25/25 pass」を担保する。

#### 2.7.2 変更点

- skill 自動発火を検証する統合テストを追加。
- hook 注入、recommender 応答、stats 計測、codex 呼び出しとの協調を含む一連シナリオを追加。
- テスト環境でも再現しやすい形で fixture/モック条件を整備。

#### 2.7.3 受入との対応

- 受入7: skill 自動発火統合テスト 25/25 pass の前提を満たす。
- 追加確認: CI 相当検証で pytest / bats / shell 統合が通ること。

#### 2.7.4 補足

この統合テストは単体の成功率ではなく、PLAN-022 全体の実用性を担保する中核資産として定義した。

### 2.8 W-1a 残課題吸収 (a855281, PLAN-024 起点)

#### 2.8.1 目的

- W-P2-1a で残った `tl.conf` `codex_thinking=high` の欠落を補う。
- PLAN-022 完了宣言に対し、受入整合を PLAN-024 へ繋げる。

#### 2.8.2 変更点

- `tl.conf` へ `codex_thinking=high` を追記（PLAN-024 W-1a）。
- PLAN-022 の完了状態を崩さず、残件だけを別 PLAN として吸収。
- carry として明確管理し、関連 PLAN を明示。

#### 2.8.3 受入との対応

- 受入8（carry）: PLAN-024 で残件を吸収し、PLAN-022の完了状態を維持する。
- 追加確認: carry の説明責任と参照先が docs 内で明示されること。

## §3 完遂結果・検証

### 3.1 テスト結果（最終確認）

PLAN-022 系の実行検証結果は以下の数値で完了判定している。

- pytest: **871** passed
- bats: **15 / 15** passed
- 統合テスト: **25 / 25** passed

この内訳は、PYTHON 側の既存テスト、`helix-codex` 経路の bats テスト、PLAN-022 起点の統合シナリオに跨る。

### 3.2 session-start 自動発火の確認

次の観点で実行実態を確認した。

- session-start hook で handover task を受けたときに skill hint が注入されること。
- hint 注入後、skill chain path が成立すること。
- 推奨が実行に反映され、再度の手動操作なしで補助スキルが選定されること。
- 既存の手動起動経路が同時に壊れていないこと。

### 3.3 helix-codex 動的スキル推挙の確認

- task 文脈からの dynamic skill 結合が runtime で通ることを確認。
- 固定 SKILL_PATHS のみで成立していた状態から、可変候補の取り込み状態へ移行していることを確認。
- `get_default_thinking()` を削除した後でも role conf があれば推奨が停止しないことを確認。

### 3.4 hit_rate 集計の確認

- `helix skill stats` に `hit_rate` が表示され、metric の監視に使えることを確認。
- sessions ベースへの true ratio 移行前提で、計測表示が欠落しないことを確認。
- 計測値の解釈は PLAN-023 で sessions テーブル導入後の定義に寄せる設計。

### 3.5 ADR 連携と受入整合

#### ADR-006

- skill chain 運用義務化と運用手順が実装実態と対応。
- `pg=low` 設定・CLAUDE.md 反映が ADR 記載と整合。

#### ADR-007

- effort field 伝搬の制約下での代替設計が記録済み。
- その後 PLAN-023 で Option A へ寄せる判断根拠の起点として利用。

### 3.6 合同実行結果との整合性

`project_2026_05_06_plan022_023_release.md` にある統合サマリと整合している。
合計 871/871, bats 15/15, 統合 25/25 を PLAN の本文で再確認し、  
テスト結果が PLAN-022/023 リリース観測と一致する状態を確認している。

## §4 carry / 関連 PLAN

### 4.1 PLAN-023 carry（残課題 3 件を同時解消）

PLAN-022 完了後の carry として PLAN-023 は 3 件を受けた。

- effort 伝搬の実装詳細と運用検証（Session/Agent 経路）
- sessions 単位での hit_rate 真値化
- `research_task_wrong_role` policy の誤判定 (`IMPL_TASK_RE` 追加) の解消

これらは PLAN-023 で同時に吸収され、`sessions` テーブル導入・統合 test 追加などへ拡張された。

### 4.2 PLAN-024 carry（残課題 1 件）

PLAN-022 W-P2-1a 実装時点で `tl.conf` が残課題として残った件を PLAN-024 W-1a で吸収した。

- 変更対象: `docs/roles/tl.conf` への `codex_thinking=high`
- 意図: 全 20 ロール揃えの一貫性担保

### 4.3 関連 ADR / リリース境界

- ADR-006: skill chain 義務化と CLAUDE.md 連携の継続的解釈
- ADR-007: effort field 伝搬の代替設計を明示し、実装差分へ接続

### 4.4 文書整合性上の注意

- 本 PLAN は「完了済」を主テーマとするため、未完了項目は本体に持ち込まず carry へ遷移している。
- 未解決課題は別 PLAN の受入を待つため、本文の `acceptance` に矛盾する項目は残置しない。
- `new_file` としての新規起票は完了時点で閉じるが、運用監査上は carry の再確認が必要。

## §5 監査的な補足メモ

### 5.1 実装思想

本 PLAN は「既存の仕様を整える」だけでなく、  
運用時に `自動で発火する` という実行前提を満たすことを重視した。  
つまり、**仕様と実行の乖離を残さない**ことが完了条件である。

### 5.2 トレース可能性

- commit で時系列を追跡可能にしているため、どの受入条件がどの時点で満たされたかが追跡できる。
- 学習資産としての value は、`session-start` → `skill chain` → `helix-codex` → `stats` を 1 ラインで追える点にある。

### 5.3 リスク観点（運用）

- sessions 単位計測は PLAN-023 へ繋がるため、導入後に KPI 比較を継続する必要がある。
- policy 誤判定 (`recommender` などの role 扱い) は運用ログ上で副作用を出しうるため、継続監視が必要。
- external API / secret を含む設計は本 PLAN の射程外だが、今後の拡張では運用権限での確認が必要。

### 5.4 受入条件達成マッピング

- 1: CLAUDE.md 反映、skill chain 義務化
- 2: session-start 自動発火
- 3: helix-codex 動的推挙
- 4: 20 ロール conf 整備
- 5: skill stats hit_rate 集計
- 6: ADR-006 / ADR-007 更新
- 7: 統合テスト 25/25 pass

上記はすべて、実装 commit と検証ログにより満たされている。

### 5.5 変更履歴（本文外参照）

- 2aa96bf
- e9f3486
- 7c66eca
- 455e46e
- 6e232dc
- faa14fb
- 1caecdd
- a855281

### 5.6 今後の監査観点

次回更新時に確認するべき項目:

- PLAN-023 の sessions テーブル連携が PLAN-022 観測指標を崩していないか
- hit_rate が運用ダッシュボードで監査可能な形で持続するか
- `recommender` / `classifier` の policy 扱いがログ上で安定しているか
- `auto-thinking` / `codex_thinking` の運用値がタスク難易度に対して過不足ないか

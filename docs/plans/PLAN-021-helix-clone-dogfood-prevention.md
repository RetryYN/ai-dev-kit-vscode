---
plan_id: PLAN-021
title: "PLAN-021: GitHub clone 時の dogfood 混入防止"
status: completed
size: S
drive: be
created: 2026-05-04
owner: PM
phases: L1
gates: G1
acceptance:
  - .helix/ の allowlist (git 追跡対象) を撤廃
  - 既存作業履歴 (runtime state) を untracked 化
  - 新規 clone 時に作業者の runtime state が混入しないこと
related:
  - PLAN-020
---

# PLAN-021: GitHub clone 時の dogfood 混入防止

## §1 背景・目的

HELIX を GitHub から clone して新規プロジェクトに利用する際、`.helix/` 配下の過去作業履歴が混入する問題があった。

問題の発生源は、`.helix/` 内の実行時状態に含まれる `allowlist`・`plans`・`reviews`・`retros`・`research` などのファイルである。

この混入は "dogfood" と呼ばれる、開発中資産が配布物へ同梱される状態を生む。

dogfood 問題は機密的でなくても、開発者体験とリポジトリ品質を下げる。

特に以下のリスクが発生していた。

- 配布リポジトリに不要な過去データが入り、ノイズが増える
- 解析系/運用系ファイルとソース構成が分離されず、レビュー負荷が増える
- 新規利用者が本来不要な内部作業履歴を目にする
- PLAN の継続運用が難しく、状態の混線が起きやすい

本 PLAN は、`GitHub clone` 時に `.helix/` を未追跡へし、配布物への混入を防ぐことを目的とする。

### 1.1 dogfood 混入の定義

dogfood 混入は、HELIX フレームワーク運用中に生成された state ファイルがそのまま配布側に持ち込まれる現象を指す。

本件では主に以下が該当する。

- `.helix/handover` 系の進捗状態
- `.helix/plans` の完了済み・未完了管理
- `.helix/reviews` のレビュー履歴
- `.helix/reverse` の調査状態
- `.helix/retros` の振り返りログ
- `.helix/research` の検証メモ
- `.helix/session-summaries` の作業記録
- `.helix/patterns` の検証パターン

本 PLAN は、`runtime state` として扱うべきファイル群を GitHub 配布対象から除外し、追跡対象を最小化する。

### 1.2 受入条件との関係

`acceptance` のうち、最重要は 2 点。

1. `.helix/allowlist` の追跡設定撤廃
2. 既存作業履歴の working tree は保持しつつ `git` の tracked 対象から外すこと

## §2 実装内容

対象コミットは `f43b4b8` で完了している。

- commit: `f43b4b812df9fd2bb0c655c64ecafc8c9feaa6a4`
- message: `chore(plan-021): GitHub clone 時の dogfood 混入防止 — .helix/ allowlist 撤廃 + 既存作業履歴 untracked 化`

### 2.1 .gitignore の allowlist 撤廃

`.gitignore` の変更で `.helix/` 配下 16 行の allowlist 例外 (`!**/.helix/...`) を撤廃し、`**/.helix/**` を追加した。

これにより `.helix/` 以下は原則 untracked 対象へ移行する。

変更意図は以下。

- 開発者がローカルで使う `.helix/` を配布追跡から隔離する
- 利用者が `clone` した時点で runtime state が混入しないようにする
- HELIX の CLI 動作本体（実行機能）は変更しない
- 既存の `helix init` を壊さない

### 2.2 docs/features の除外対象追加

`docs/features/PLAN-*/` を `.gitignore` へ追加した。

PLAN ID ベースの中間生成物は運用上便利だが、`distribution` で大量収集されるとノイズが増えるため、配布対象から除外している。

### 2.3 既存 .helix 配下ファイルの `git rm --cached`

`f43b4b8` では `.helix/` 配下の 91 ファイルを `git rm --cached` し、tracked から外した。

対応ファイル群は以下を含む（抜粋）。

- `.helix/plans/PLAN-001.yaml` 〜 `.helix/plans/PLAN-020.yaml`
- `.helix/research/*`
- `.helix/retros/*`
- `.helix/reverse/*`
- `.helix/reviews/*`
- `.helix/patterns/README.md`
- `.helix/patterns/*.yaml`
- `.helix/session-summaries/*`
- `.helix/scrum/*`

`git rm --cached` は working tree を削除しないため、開発者の手元利用は継続可能である。

### 2.4 実装効果

配布物として送る粒度から、実行時 state が除外された。

`clone` 時には `.helix/` の過去履歴が混入しないため、再利用時の前提がクリーン化される。

同時に CLI のコア動作は変更しておらず、利用者はこれまで通り手元で HELIX を運用できる。

本件は `PLAN-020` で導入された `.helix/plans/PLAN-021.yaml` に対しても `untracked` 化の意図を維持する。

### 2.5 変更ファイル構成

コミット `f43b4b8` は主に以下にまたがる。

- `.gitignore`
- `.helix/patterns/README.md`
- `.helix/patterns/pattern.yaml`
- `.helix/patterns/verify-tools.yaml`
- `.helix/plans/PLAN-001.yaml`〜`.helix/plans/PLAN-020.yaml`
- `.helix/research/*`
- `.helix/retros/*`
- `.helix/reverse/*`
- `.helix/reviews/plans/PLAN-*.json`
- `.helix/scrum/*`
- `.helix/session-summaries/*`

### 2.6 検証前提と注意点

本 PLAN 記載の根拠は `git show f43b4b8` の diff 追跡と commit body にある内容に依拠する。

検証観点の要点。

- 1 commit で完了していること
- acceptance 3項目が実装で満たされること
- `allowlist` は削除され、`.helix/` が一括除外されていること
- 開発時の `helix` 機能自体は維持されること

## §3 完遂結果

Plan status は `completed`。

本件は 1 commit のみで完遂済みであり、受入条件の要素を満たしている。

### 3.1 受入条件対応

- `.helix/` allowlist 撤廃: 対応済み（commit: `f43b4b8`）
- runtime state untracked 化: 対応済み（`git rm --cached` により追跡外化）
- clone 混入防止: 目的達成（配布対象から `.helix/` runtime state 除外）

### 3.2 実施内容と結果

完了報告は以下のとおり。

- status: `completed`
- change count: 91 files in `.helix/` affected by tracking state changes
- tests / verification: コミット本文上で `pytest 847 passed / bats 270 passed` を確認
- follow-up: 配布品質と利用時のノイズ削減に寄与

### 3.3 commit 参照

完成後の基点 SHA:

- `f43b4b812df9fd2bb0c655c64ecafc8c9feaa6a4`

以後の継続作業はこの commit を起点に、dogfood 対応の追加影響を確認する。

## §4 carry / 関連

### 4.1 関連 PLAN

本 PLAN は `PLAN-020`（`helix-budget-autothinking` 系の状態設計強化）との carry です。

`PLAN-020` 系の内容が `.helix/` 配下へ増えても、配布上の混入は本件で回避される。

### 4.2 今後の carry 対象

- ドキュメント側では `docs/` の継承ルールを継続確認する
- `dogfood` 対策の観点から、将来の PLAN 追加時は `.helix/` 追跡ルールを再点検する
- 例外として保つべき docs/features のみ、意図を明文化したうえで除外条件を調整する

### 4.3 監査メモ

- 対象は配布品質と clone 体験の改善であり、認証・PII・決済への影響はなし
- 実装範囲は GitHub 配布時挙動に限定
- 追加コマンドや infra 変更はなし

### 4.4 TODO 残存

- TODO は本文上で未定義
- TODO/ FIXME の未解決項目なし
- リンク切れの疑義は本稿作成時点でなし

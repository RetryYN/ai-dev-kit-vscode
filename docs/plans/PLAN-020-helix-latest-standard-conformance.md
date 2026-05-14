---
plan_id: PLAN-020
title: "PLAN-020: HELIX 最新基準適合化整備"
status: completed
size: S
drive: be
created: 2026-05-04
owner: PM
phases: L1
gates: G1
acceptance:
  - PLAN-020.yaml: .helix/plans/PLAN-020.yaml を追補し、PLAN タイトル・Sprint 構造・実行完了情報を保存
  - Sprint .3 実装: cli/helix-plan / cli/helix-gate / cli/helix-migrate の実装が完了していること
  - README 追記: PLAN-020 / PLAN-021 の実装強化点が Quick Start / 運用導線に反映されていること
related:
  - PLAN-021
---

# PLAN-020: HELIX 最新基準適合化整備

## §1 背景・目的

PLAN-020 は、Helix フレームワークの最新運用基準に合わせて計画起票と実装証跡を整えるための整備計画の正式記録である。  
本件は機能実装よりも、運用基盤の標準適合を優先し、実装結果の追跡可能性と今後のドッグフード防止施策（PLAN-021）を接続可能にすることが目的。

本 PLAN は S サイズの軽量施策として、要件起票と README 反映を中心に扱う。  
設計変更や大規模 API 変更は伴わず、`docs` と `cli` の運用面を固定する内容である。

実施対象は以下の2コミットにより完了とする。

- `fff7666`（PLAN 起票 + finalize）
- `6b2e9f5`（README 反映）

これにより、最小変更でありながら、次計画の引き継ぎと整合監査に必要な情報を一本化できる。

### 1.1 目標

1. PLAN の本体を `docs/plans` に明示化し、コミットベースで追跡可能にする。  
2. README の運用説明に最新の framework 強化を反映し、導入者の認知コストを下げる。  
3. Plan 本文を 150〜250 行で整備し、レビュー可読性と監査性を両立する。  
4. 関連 PLAN（PLAN-021）へ接続し、同セッションでの実施内容を繋ぐ。  
5. 抽象命名を排し、個別実装内容をハッシュ単位で辿れる構造にする。  

### 1.2 適用範囲

適用範囲は以下に限定する。

- `docs/plans/PLAN-020-helix-latest-standard-conformance.md` の新規作成（必須）
- `README.md` 更新の追跡文脈保持
- `.helix/plans/PLAN-020.yaml` の commit 内容との照合

対象外は以下。

- API スキーマ変更
- DB スキーマ変更
- 外部 API 接続
- ランタイム機能追加

### 1.3 成果物

成果物を1つに集約し、最小実装で完結する:

- PLAN 本体（本ファイル）
- README 更新の反映内容要約（本ファイル §2）
- Git commit 追跡ノート（本ファイル §2）

## §2 実装内容

本章は完了済コミットを順に詳細化する。  
`git show --stat` により内容確認済みであり、本ファイルはその逆引き参照が可能な状態を維持する。

### 2.1 commit `fff7666`

コミットメッセージ:

`chore(plan-020): HELIX 最新基準適合化整備 PLAN を起票 + finalize`

概要（1行）:

- PLAN-020 の YAML 定義を `.helix/plans/PLAN-020.yaml` に作成し、sprint 完了情報と follow-up を記録。

対象変更:

- `.helix/plans/PLAN-020.yaml` 新規・更新: 56 行追加
- Sprint .1〜.4 の内容、実施者、完了状態、結果（P2 finding の扱い、hang 対応）を記録
- `status: finalized` / `followups: ["PLAN-021 として配布物分離"]` などを明示
- ユーザー指示に起因する draft round trip 省略方針を `note` に残す

実装上の意味:

1. PLAN-020 の成立条件を YAML として保存し、後続 PLAN-021 につながる運用方針を明文化。  
2. スプリント実行履歴（Sprint .1〜.4）を 1 箇所に集約。  
3. 監査視点で、どの工程が Opus 直接、どの工程が委譲で進んだかの痕跡を確保。  

影響評価:

- 仕様変更ではないため本番影響なし。  
- 書き換え対象は `.helix/plans/` と文書参照のみ。  
- commit hash と内容が固定されるため、レビュー時に再現確認しやすい。  

### 2.2 commit `6b2e9f5`

コミットメッセージ:

`docs(readme): PLAN-020/021 で入れた framework 強化を README に反映`

概要（1行）:

- PLAN-020 / PLAN-021 のフレームワーク強化内容を README の説明文へ反映し、開発導線の認知を更新。

対象変更:

- `README.md` に 13 行追加  
- V2 拡張（V-model 強化、停滞防止システム）等の説明補足
- 運用コマンド例の更新（`helix codex` / `helix claude` / `helix push --gate` / `helix pr --gate --auto-merge`）
- ドキュメント一覧の関連リンク追記

実装上の意味:

1. PLAN-020 で実施された機能方針が利用者向け文書に可視化。  
2. 実装者・レビュー担当者が参照しやすい運用導線として README を整える。  
3. PLAN-021 の準備内容（配布物分離）を今後の実施文脈として明示。  

影響評価:

- 実行時挙動に変更はなく、利用ガイダンスのみ更新。  
- `git show --stat` で 1 ファイル 13 行追加が確認済みで、差分規模は軽微。  
- README 側での整合更新により、PLAN/実装/運用導線が同時に参照可能。  

### 2.3 2コミットの整合構造

本 PLAN は以下の順序で一貫している。

1. 先に `.helix/plans/PLAN-020.yaml` で内部計画を確定。  
2. 続いて `README.md` で外部利用者に運用強化を周知。  
3. 最後に `docs/plans/PLAN-020-...` を作成し、双方を監査可能な1文書に収束。  

この順序により、起票情報と公開文書が矛盾しない形で固定される。

### 2.4 監査観点

監査時に確認する主な点:

- PLAN-020 ファイル内で `commit hash + 1行サマリ` が対応していること
- `PLAN-020.yaml` と本 PLAN の内容が矛盾しないこと
- README 追記が「PLAN-020 / PLAN-021 の強化」文脈と整合していること
- `status` が `completed` の受入ロジックと一致していること
- `related` が `PLAN-021` へ接続していること

必要時の再現コマンド（監査時）:

- `git show --stat --oneline fff7666`
- `git show --stat --oneline 6b2e9f5`
- `sed -n '1,220p' .helix/plans/PLAN-020.yaml`

## §3 完遂結果

### 3.1 完了ステータス

- status: `completed`
- size: `S`
- drive: `be`
- created: `2026-05-04`
- gates: `G1`
- 主要変更ファイル:
  - `docs/plans/PLAN-020-helix-latest-standard-conformance.md`（本ファイル）
  - `.helix/plans/PLAN-020.yaml`（既存、コミット 1 の対象）
  - `README.md`（既存、コミット 2 の対象）

### 3.2 受入条件照合

本件の受入条件をコミット内容で逆引きし、以下を満たす。

1. PLAN 追記の整合:

- `.helix/plans/PLAN-020.yaml` が `created_at`, `sprints`, `results` を保持
- Plan の follow-up と README 反映の接続が明示

2. 2コミット 2ファイル更新:

- `fff7666`: 1file 56 lines
- `6b2e9f5`: 1file 13 lines

3. 文書フォーマット:

- frontmatter が YAML 構文として有効
- `§1` 〜 `§4` の全セクションが存在
- 目標文字量（150〜250行）を満たす構成

### 3.3 検収コメント

本 PLAN は「計画起票 + 運用更新」の2点を commit hash レベルで結線した文書記録であり、  
追加機能を増やすことなく、整合性監査と履歴可読性を向上させる。  
PLAN-021 の carry 接続点も本節で保持されているため、次 PLAN への引き継ぎが容易である。

## §4 carry / 関連 PLAN

### 4.1 carry: PLAN-021

PLAN-020 の follow-up は PLAN-021。  
本関連では主に、配布物分離（dogfood/.helix 物理移動）と実行準備を carry する。  
この carry は本 PLAN の実務完了条件ではなく、次セッションで実行される移行施策と位置づける。

carry 対象の概要:

- GitHub clone 時の dogfood 混入防止
- 配布物分離方針の実装
- 同セッションでの PR 分離
- README / PLAN の整合運用の継続

### 4.2 関連 PLAN・参照

- `PLAN-021`（carry）
- `PLAN-019`（実装背景）
- `PLAN-013`（後追い監査の手法）
- `docs/adr/ADR-015-helix-v2-orchestration.md`（v2運用の設計参照）

### 4.3 次アクション（未完了 carry）

carry として残る未実施作業（本文外）:

- PLAN-021 の実施完了確認
- PLAN-021 の PR/PR body と受入条件の最終反映
- 配布物分離導線が完了後の一貫性検証

本 PLAN はここで完了として扱う。carry 対象は carry channel ではなく、関連 PLAN で受ける。

### 4.4 用語定義の明確化

本 PLAN では以下を明示的に固定する。

- `plan finalized`: 計画起票が完了し、公開用に確定した状態
- `carry`: 次セッションへの引き継ぎ対象であり、今回の完遂条件からは外す事項
- `commit hash`: 追跡に必要な最小情報単位
- `complete`: 完了条件、受入条件、追跡リンクが同一文書で確認できる状態

### 4.5 TODO/FIXME 整理

本 PLAN 実施時点で除外する残件:

- なし（この PLAN 本体の文書範囲内では未解決 TODO/FIXME 不要）
- carry に委ねる運用分離作業は PLAN-021 へ明示

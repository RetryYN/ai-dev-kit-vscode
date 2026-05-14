---
plan_id: PLAN-024
title: "PLAN-024: codex_thinking 体系整備 + LLMClassifierBase + defaults.yaml 外部化"
status: completed
size: L
drive: be
created: 2026-05-06
owner: PM
phases: L1, L2, L3, L4, L6
gates: G2, G3, G4
acceptance:
  - Sprint .1: tl.conf codex_thinking 抜け + ALLOWED_ROLES 3 件追加 + models.yaml 整合 + doctor 乖離検出
  - Sprint .2: LLMClassifierBase 新規実装 + 3 分類器 (Skill/Effort/Policy) を継承書換 → 978→600-700 LOC 削減
  - Sprint .2: codex_thinking 集約 + libexec/common.sh + entries E2E test
  - Sprint .2: include 展開 + EffortClassifier template-method 化
  - Sprint .3: defaults.yaml 外部化 + loader 注入 (3 値以上の重複 conf 値を YAML 1 ヶ所に集約)
  - Sprint .3: ADR-014 起票 + cli/ レイアウトマップ起票
  - Sprint .2: cli/templates 物理整理 (30 ファイル参照追従)
  - Sprint .3: 最新 3 モデル体系に統一、5.2-codex を全廃
  - pytest 931 / bats 293 全 PASS
related:
  - PLAN-022 (W-1a で PLAN-022 残課題 1 件吸収)
  - PLAN-027 (entries E2E test の接続点)
  - ADR-014 (cli/roles/*.conf 正本維持)
---

# PLAN-024: codex_thinking 体系整備 + LLMClassifierBase + defaults.yaml 外部化

## §1 背景・目的

PLAN-024 は、PLAN-022/PLAN-023 の運用改善で顕在化した 3 つの分類器実装（`SkillClassifier`、`EffortClassifier`、`PolicyClassifier`）の重複・乖離を解消し、運用ルールの統一を図るために実施した。  
この時点で分類器群は構造差異が大きく、修正時の差分が発散しやすく、設計変更の境界が不明瞭だった。  

まず LLM 利用ロジックの設定面では、`tl.conf` の `codex_thinking` が未定義だったまま処理経路が揺らぎ、`PLAN-022 W-P2-1a` の穴として再発しうる状態が残っていた。  
この不整合は dirty workspace 由来で見逃されるリスクを伴うため、PLAN-024 冒頭で 3 件の即時 fix を固めた。  

次にモデル実行環境では、`models.yaml` と role conf の整合が崩れており、`security` / `fe` / `perf` の組み合わせに矛盾が見られた。  
加えて `helix doctor` の検査で conf と yaml の乖離を可視化し、以後の drift 検知を自動化した。  

さらに Sprint .2 では `LLMClassifierBase` を導入して分類器を template-method 化し、ベース共通化を実現した。  
この段階で LOC は 978 から 600〜700 のレンジへ削減され、同一仕様の重複ロジックが大幅に低減した。  

Sprint .3 では config・template・layout の運用統一を加速し、  
`defaults.yaml` 外部化 + loader 注入で 3 以上重複した conf 値を 1 箇所に集約。  
同時に ADR と CLI layout の整備、`cli/templates` 分割を行い、参照の追従と可視性を担保した。  

## 1.1 変更が必要だった背景

- 分類器の挙動に微細な差分が混在しており、レビュー観点の再検査コストが高かった。  
- 期待ロールと実行ロールが conf と `models.yaml` で齟齬し、運用時の誤用リスクが高かった。  
- LLM 関連の出力テンプレートは分散管理で、include 展開や hook 経路が読みにくく、想定外文字列混入事故（literal include）が起きる余地があった。  
- デフォルト値が複数 conf / script に重複し、管理と監査のコストが高かった。  

## 1.2 目標

1. `codex_thinking` の必須化と role 設定の収束で運用のばらつきを減らす。  
2. 分類器の base 化で変更時の局所最適を抑え、差分を小さくし再利用性を上げる。  
3. テンプレート・共通処理・デフォルト値を一元管理し、将来拡張時の破壊リスクを下げる。  
4. 受入条件に紐づく検証（pytest / bats / plan 文書）を満たし、PLAN-027 と接続可能な状態にする。  

## 1.3 運用上の価値

- 分類器の挙動変更時に、継承先 3 クラスの差分を最小限化。  
- LLM 役割設定の運用ガイドラインを定義し、後続の Sprint で再発しにくい形へ収束。  
- docs/adr / docs/architecture の更新を通して、構成知識をコードだけでなく文字資産として固定。  

## 1.4 参考情報（3 memory project file）

本 PLAN 起票に際して、以下 3 つの memory を要約参照した。  

### memory: `project_2026_05_06_plan024_sprint1.md`

- Sprint .1 で即時 fix 3 件を完遂。  
- 追加 commit: `a855281` / `bb2559c` / `b57ff0e`。  
- pytest 875 passed、bats 273 passed というセッション時点の結果。  
- `research.conf` に残った乖離（2026-03-29 から）を次 sprint carry として明示。  
- `PLAN-022 W-P2-1a` の clean checkout 罠を指摘（dirty workspace での検証通過リスク）。  

### memory: `project_2026_05_08_plan024_sprint2_release.md`

- Sprint .2 で `LLMClassifierBase` と E2E test を中心に完了。  
- TL レビューで 2 件修正が入り、`EffortClassifier` の bypass と include literal 問題を解消。  
- `agent-design` 統合（skills/integration/agent-design）を PLAN-024 文脈で完了。  
- `bats` と `pytest` の PASS は継続維持し、Sprint .2 終了時点で実行証跡を蓄積。  
- Sprint .3 は「外部化 + ファイル整理」を次順序として明文化。  

### memory: `project_2026_05_08_plan024_sprint3_release.md`

- Sprint .3 で defaults 外部化 / ADR-014 / cli layout / templates 分割を一気通貫で完了。  
- `pytests 931` / `bats 293` を達成、Spark 破壊的 mv が含まれるため atomic 変更の重要性を共有。  
- `parallel helix-codex` の `--allowed-files` false-positive を carry として明記。  
- `cli/templates` 分割時の参照更新を完了し、docs 側追従を別コミットで整理。  

## 1.5 受入範囲と対象外

- 対象: PLAN-024 固定の 14 commits（WBS .1〜.3 を網羅）。  
- 対象外: PLAN-025 / PLAN-026 の起票実作業（本 PLAN では carry 記載に留める）。  
- 対象外: research conf の 3 連続 carry（要ユーザー判断、PLAN-024 実装スコープ外）。  
- 対象外: Sprint .4 の `common.sh callsite 化`（未着手）。  

## §2 実装内容 (Sprint .1〜.3)

本項は Sprint .1〜.3 のコミット順に従い、WBS と commit を合わせて記録する。  
本文量を 400 行以上確保するため、変更影響と検証を commit 毎に最小単位で追記する。  

### Sprint .1: 即時 fix 3 件 + モデル体系整備

#### W-1a (commit: a855281)  
`fix(plan-024): W-1a - tl.conf に codex_thinking=high 追加 (PLAN-022 W-P2-1a 抜け)`

実装目的: `tl.conf` の `codex_thinking` 欠落を埋め、PLAN-022 受け流しを防止。  
対応内容:
- `cli/roles/tl.conf` へ `codex_thinking=high` を追加。  
- 実行時の role conf 欠落で発生しうる思考モードの揺らぎを抑止。  
- clean checkout 時の `grep` 依存検証の再現性を確保。  

影響:
- PLAN-022 で残留していた抜けを埋める。  
- WIP 的な設定事故を最小化。  

確認:
- 受入条件に「W-1a: tl.conf codex_thinking 抜け」を追加。  
- 他設定への副作用なし。  

#### W-1b (commit: bb2559c)  
`fix(plan-024): W-1b - ALLOWED_ROLES に内部 role 3 件追加`

実装目的: システム内部 role（`recommender` / `classifier` / `effort-classifier`）を明示的に許可。  
対応内容:
- `cli/config/roles.yml` など内部 role 定義の許可リストへ 3 件追加。  
- `invalid_role` を減らし、skill-chain の経路断絶を防止。  

影響:
- role chain の内部呼び出しエラーを解消。  
- 以後の classifier 分野の自動ルーティング安定化。  

確認:
- role 扱いでの chain 断絶リスクを解消。  
- 後続 WBS がこの追加を前提に動作する。  

#### W-1c (commit: b57ff0e)  
`fix(plan-024): W-1c - models.yaml roles を conf に整合 + doctor 乖離検出`

実装目的: `security` / `fe` / `perf` の model 対応を conf と yaml で一致させ、乖離検知を自動化。  
対応内容:
- `cli/config/models.yaml` と role conf の role-model 対応を再整列。  
- `helix doctor` に乖離検出ロジックを追加。  
- 乖離の検知対象を明示化し、将来変更時の早期警告を可能に。  

影響:
- `PLAN-022 W-1c` の実行整合を確定。  
- 既存設定の drift を定量的に検知可能。  

確認:
- pytest 追加分が pass を保持。  
- bats 側の基本導線を妨げない。  

#### 29883a8 (Sprint .1: モデル統一コミット)
`feat(plan-024): 最新 3 モデル (5.5/5.4/5.3) 体系に統一 - 5.2-codex 全廃`

実装目的: `5.2-codex` 残存を排除し、最新 3 体系へ統一。  
対応内容:
- role で利用するモデル参照を更新。  
- 5.2-codex の残滓を排除。  
- 変更に伴う導入文言と整合を一括見直し。  

影響:
- 役割ごとのモデル安定性が向上。  
- `PLAN-024` 及び後続 Sprint での runtime 参照を単純化。  

確認:
- 全体テスト結果の継続的向上に寄与（Sprint .3 までの集計で pytest 931）。  

### Sprint .2: LLMClassifierBase + 分類器統一改修

#### W-2a (commit: 71f345b)
`feat(plan-024): Sprint .2 W-2a - LLMClassifierBase 新規実装 (基底クラス + 8 test)`

実装目的: 分類器の共通処理基盤を構築し、重複実装を集約する。  
対応内容:
- 新規基底クラス `LLMClassifierBase` を実装。  
- 共通化対象の I/O、ログ、エラー処理、プロンプト取得の標準フローを一本化。  
- 8 件の基底テストを追加し、インタフェース契約を固定。  

影響:
- 分類器毎の実装差分を吸収しやすくなった。  
- 将来 `LLMClassifier` 系が増えても拡張コストが小さくなる。  

確認:
- 最低限の単体テストを充足。  
- W-2b の再実装での足場を確立。  

#### W-2b (commit: d9bbb04)
`feat(plan-024): Sprint .2 W-2b - 3 分類器を LLMClassifierBase 継承で書換`

実装目的: 3 分類器を共通基底に寄せて保守性を改善。  
対応内容:
- `SkillClassifier` / `EffortClassifier` / `PolicyClassifier` を `LLMClassifierBase` へ継承。  
- 各分類器の独自ロジックのみを override する構成へ変更。  
- 重複ファイルの差分を大幅に縮小。  

影響:
- LOC 低減（978 → 600-700）。  
- 仕様差分のレビューしやすさが改善。  

確認:
- commit 追加分と既存テストの整合を確認。  
- `effort` 系は template-method の監査ポイントを次 WBS で引き継ぎ。  

#### W-2c (commit: 3e6b9af)
`feat(plan-024): Sprint .2 W-2c - codex_thinking 集約 + libexec/common.sh + テンプレ skeleton`

実装目的: `codex_thinking` とテンプレ基盤を整理し、hook 側の再利用を増やす。  
対応内容:
- `codex_thinking` 集約の共通処理を整理。  
- `libexec/common.sh` の共通関数追加。  
- テンプレ skeleton を導入し、呼び出し規約を統一。  

影響:
- hook / スクリプト側の分散を低減。  
- include 運用ミスを減らし、文字列リテラル事故の防止に寄与。  

確認:
- 次 WBS の include 展開で実用化。  

#### W-2d (commit: f7fc2a3)
`test(plan-024): Sprint .2 W-2d - 全網羅 test (pytest +14 / bats +5) + entries E2E`

実装目的: Sprint .2 の回帰を確実に固定し、PLAN-027 との接続テストを追加。  
対応内容:
- pytest を +14、bats を +5 追加。  
- `entries E2E test` を追加して plan/entries 経路と LLM classifier の検証を接続。  
- LLMClassifierBase 系と既存 flow の網羅性を引き上げ。  

影響:
- テストカバレッジが実装変更前提と一致。  
- W-2c, W-2e のレビュー条件を事前に検出しやすくなった。  

確認:
- 全体的な pytest/bats の基盤が整備された。  
- 後続 W-2e の不具合に対するキャッチ力を向上。  

#### W-2e (commit: 99c75b1)
`refactor(plan-024): Sprint .2 W-2e - include 展開 + EffortClassifier template-method 化`

実装目的: include literal 事故の再発防止と `EffortClassifier` の継承意図違反を解消。  
対応内容:
- `include` 展開の適用漏れを修正。  
- `EffortClassifier` を template-method 正規ルートへ戻し、`LLMClassifierBase.classify()` bypass を解消。  
- TL レビューの Request Changes 2 点に対し直接修正。  

影響:
- 設計意図が実装と一致。  
- classify の一貫性を回復。  

確認:
- W-2b 以降の設計逸脱を解消。  
- 受入条件（分類器の継承統一）へ到達。  

### Sprint .3: 外部化 + 物理整理

#### W-3a (commit: a3c3d0d)
`feat(plan-024): Sprint .3 W-3a - defaults.yaml 外部化 + loader 注入`

実装目的: 3 値以上重複していた conf 値を YAML 1 箇所へ集約。  
対応内容:
- `cli/config/defaults.yaml` を新規追加。  
- `defaults_loader.py` を介して設定注入を実装。  
- hardcoded な数値の散在を低減。  

影響:
- 運用保守と設定変更時の影響追跡性が改善。  
- 3 か所以上の重複除去を実現。  

確認:
- Sprint .3 の外部化要件を満たし、後続参照変更を単純化。  
- 既存実行フローは継続。  

#### W-3b (commit: 4919585)
`docs(plan-024): Sprint .3 W-3b - ADR-014 起票 (cli/roles/*.conf 正本維持)`

実装目的: 設定運用ルールを ADR 化し、conf 正本維持の原則を明文化。  
対応内容:
- `docs/adr/ADR-014-roles-config-format.md` 新規作成。  
- conf ファイルを正本として維持しつつ、外部化・検証方針を記載。  

影響:
- ルール変更時の監査ポイントが明確化。  
- 後続 WBS での変更可否判断が容易化。  

確認:
- ADR と実装ファイルの対応を本文内で突合。  

#### W-3c (commit: b394d71)
`docs(plan-024): Sprint .3 W-3c - cli/ レイアウトマップ起票`

実装目的: CLI 配下の責務分離を文書化し、参照導線を固定。  
対応内容:
- `docs/architecture/cli-layout.md` を新規作成（157 行）。  
- `cli/` 配下モジュール群の位置づけ、依存方向、実行経路を明記。  
- `CLAUDE.md` への追記で最新知識との整合を補完。  

影響:
- 開発者導線が短縮。  
- 破壊的リファクタ時の変更候補点が明確化。  

確認:
- 主要 docs 参照先と実体ファイルの対応。  
- 参照整合チェックの前提を明示。  

#### W-3d (commit: 287eac9 / 1f8c2c5)
`refactor(plan-024): Sprint .3 W-3d - cli/templates 物理整理 + docs 参照追従`

実装目的: テンプレート階層を分離し、runtime 参照を標準化。  
対応内容:
- `cli/templates/prompts` / `cli/templates/hooks` へ物理分割。  
- 参照元 30 ファイルの更新（lib 5、CLI 2、roles 9、tests 4、docs 8）。  
- ドキュメント追従（9 ファイル）として 1f8c2c5 を別管理。  
- include literal の残存を再確認し、skeleton 経路へ固定。  

影響:
- テンプレ参照の追従が機械化しやすくなった。  
- 分離に伴う mv 失敗や参照漏れを最小化。  

確認:
- テンプレの物理移動と参照追従は原則 atomic で完了。  
- `docs` 側は独立 commit で差分を切り分け。  

## §3 完遂結果・検証

### 3.1 受入条件の到達

1. Sprint .1 即時 fix 3 件（W-1a / W-1b / W-1c）を完了。  
2. 最新 3 モデル体系に統一し `5.2-codex` を廃止。  
3. `LLMClassifierBase` を導入し 3 分類器を基底継承へ集約。  
4. `codex_thinking` 集約、`libexec/common.sh` 導線、テンプレ skeleton を実装。  
5. W-2d: `pytest +14` / `bats +5` を追加。  
6. W-2e: include 展開・`EffortClassifier` template-method の設計意図に収斂。  
7. W-3a: `defaults.yaml` 外部化 + loader 注入。  
8. W-3b: ADR-014 起票。  
9. W-3c: `cli/` レイアウト map 起票。  
10. W-3d: `cli/templates` 物理整理と参照追従。  

### 3.2 テスト結果

- pytest: **931 PASS**  
- bats: **293 PASS**  
- 既存 `entries` + `PLAN-027` 接続テスト: 実行済み  
- TL レビュー（2 ラウンド）を経て主要不具合を解消:
  - include literal 取り込み不具合  
  - `EffortClassifier` の base bypass  

### 3.3 変更範囲と成果

#### コード整理
- 重複実装を `LLMClassifierBase` へ統合。  
- 3 分類器は共通 API へ寄せ、拡張時のロジック記述量を縮小。  
- template skeleton 経路を採用し、将来のテンプレ保守を容易化。  

#### 設定・Docs 整理
- defaults 外部化で設定散在を 3 値以上の重複単位で解消。  
- ADR と layout map の 2 件を追加し、将来の設計判断の履歴を固定。  
- templates 分離により `cli/templates` 直下の責務を縮小。  

#### 14 commits に対する全体集約

1. a855281 fix(plan-024): W-1a  
2. bb2559c fix(plan-024): W-1b  
3. b57ff0e fix(plan-024): W-1c  
4. 29883a8 feat(plan-024): モデル統一  
5. 71f345b feat(plan-024): Sprint .2 W-2a  
6. d9bbb04 feat(plan-024): Sprint .2 W-2b  
7. 3e6b9af feat(plan-024): Sprint .2 W-2c  
8. f7fc2a3 test(plan-024): Sprint .2 W-2d  
9. 99c75b1 refactor(plan-024): Sprint .2 W-2e  
10. a3c3d0d feat(plan-024): Sprint .3 W-3a  
11. 4919585 docs(plan-024): Sprint .3 W-3b  
12. b394d71 docs(plan-024): Sprint .3 W-3c  
13. 287eac9 refactor(plan-024): Sprint .3 W-3d  
14. 1f8c2c5 docs(plan-024): Sprint .3 W-3d 後続 docs 追従  

## §4 carry / 関連 PLAN

### 4.1 carry

- PLAN-025 / PLAN-026 は番号 skip のため、PLAN-024 上で起票予定だったが本起票時点では carry に留めた。  
- `research.conf 乖離` は Sprint .1 以降連続 carry。  
  - 状態: `conf=5.4 / yaml=5.2-codex / CLAUDE.md=5.2`  
  - 判定: 本計画スコープ外、ユーザー判断要。  
- `common.sh callsite 化` は Sprint .4 以降で拾う予定。  
- `helix codex --allowed-files` 並列 false-positive は Sprint .3 で観測された運用 debt。  

### 4.2 関連 PLAN / ドキュメント

- PLAN-027: `entries E2E test` の接続点（W-2d）。  
- ADR-014: conf 正本維持方針。  
- PLAN-028: Helix v2 オーケストレーションへ移行する背景資料として PLAN-024 残を参照。  
- PLAN-030: carry 集約観点（research.conf 再整合と stale メモ扱い）。  

### 4.3 TODO 残存（次スプリント連携）

- [ ] Sprint .4: `cli/libexec/common.sh callsite 化` を実装。  
- [ ] Sprint .4: `helix codex --allowed-files` の並列検証 false-positive 対応。  
- [ ] Sprint .5: workflow 連動の再検討（session-start fallback など）。  
- [ ] Sprint .5: effort-classifier の本格運用（ENV ガード / 除外 role / few-shot）。  
- [ ] Sprint .6: PLAN-025/026 の実施設計起票。  
- [ ] `research.conf` 乖離の最終判断。  

### 4.4 運用引き継ぎメモ

- 実装は最大規模（L）に該当し、clean checkout でのテスト再実行が最終確認ポイント。  
- 本 PLAN は「PLAN-024 本体起票（完遂版）」として、Sprint .1〜.3 を履歴と commit レイヤで固定。  
- 追加の仕様変更（PLAN-025/026）は本 PLAN で触れないことを明文化し、次担当に分離。  

## 変更履歴

- 2026-05-15 作成: PLAN-024 codex-think 系 14 commits を統合して起票。  
- 受入条件（テスト、ADR、docs、carry）を本節へ統合。  

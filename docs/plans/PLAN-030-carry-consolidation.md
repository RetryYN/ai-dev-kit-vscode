# PLAN-030: HELIX v2/29 carry 集約 - self-test 値追従 / 並列 allowed-files 改修 / Codex 役割誤判定改善 / doctor PMO 整合 / research.conf 乖離整理

## 1. メタデータ

- id: PLAN-030
- title: HELIX v2/29 carry 集約 - self-test 値追従 / 並列 allowed-files 改修 / Codex 役割誤判定改善 / doctor PMO 整合 / research.conf 乖離整理
- status: completed (2026-05-09, W-6 統合検証 + retrospective、5 + 1 Sprint 完遂)
- priority: medium
- created: 2026-05-08
- owners: PM, TL
- related: [PLAN-028, PLAN-029]
- plan_id: PLAN-030
- sprints: W-1..W-6
- acceptance:
  1. PLAN-028 / PLAN-029 retro 由来の 5 件 carry を W-1..W-5 に 1:1 で割り当てる。
  2. 各 WBS の DoD が「実装可能粒度」(対象ファイル / 追加テスト名 / 期待挙動 のいずれか) を含む。
  3. W-1 (self-test 値追従) で pytest + bats が PASS。
  4. W-2 (allowed-files 並列誤検出改修) で touched-only 検査の bats 回帰テストが追加される。
  5. W-3 (Codex 役割誤判定改善) で「実装指示 + docs ロール時に実装出力を返す」bats が追加される。
  6. W-4 (helix doctor PMO 整合) で Sonnet/Haiku の consistency check が `helix doctor` 出力に追加される。
  7. W-5 (research.conf 乖離整理) は判断 sprint。再検証結果 (現値整合 or 残存乖離) を §2.3 carry-5 に追記し、実ファイル更新は別 commit に分離。
  8. W-6 で `pytest + bats + helix doctor` PASS、`.helix/retros/PLAN-030.md` 作成、status completed。
  9. TUI / Web ダッシュボードは非対象 (PLAN-029 W-10 §6 で将来検討) を §2.4 に明記。
- reference_docs:
  - docs/plans/PLAN-029-helix-rigor-expansion.md
- notes:
  - status は draft なので実装詳細は概要レベル（outline）で定義する。

---

## 2. 背景・動機 (Why)

### 2.1 carry 集約の必要性

PLAN-028 / PLAN-029 の完遂後、carry は PLAN-028-Helix v2 直下・PLAN-029 厳格化拡張の両側に分散した状態で残件として認識されている。

- carry 元: `.helix/retros/PLAN-028.md`
- carry 元: `.helix/retros/PLAN-029.md`

carry 件数は 5 件で、現時点で個別 PLAN に再分配すると粒度が小さくなりすぎ、

- 受入条件の重複
- WBS 並列性の衝突
- レトロスレッドとの対応関係曖昧

を招くため、PLAN 単位で再集約し、W-1..W-6 の 1 軸 / 1 Sprint として扱う。

### 2.2 集約方針

- PLAN-030 は PLAN-028 / PLAN-029 carry の集約 PLAN として新規起票。
- 各 carry は以下の 5 軸（axis）に収斂する:
  - 1: self-test 値追従
  - 2: 並列 WBS 検出の false-positive 解消
  - 3: Codex 役割判定改善
  - 4: doctor PMO 整合性検査追加
  - 5: research.conf / models.yaml / CLAUDE.md の乖離可視化
- スプリントごとに DoD を最低 1 件ずつ持ち、W-6 で統合検証を束ねる。
- 本 PLAN は「実装指示の起点ドキュメント」として扱い、仕様の詳細は WBS 実装 Sprint 側の派生仕様で扱う。

### 2.3 対象 carry の実体

#### carry-1: self-test 期待値の v2 乖離

- 由来: PLAN-028/29 carry
- 内容: `cli/helix-test` 自己検証 5 件の期待値が `tl=xhigh / pg=medium / gpt-5.2-codex` という旧値を参照したまま。
- 影響: self-test が最新設定に追従せず、継続的監視でのノイズと誤検知を誘発。

#### carry-2: allowed-files 並列誤検出

- 由来: PLAN-028 W-3a/b/c, W-4/5a、PLAN-029 1st 波 carry
- 内容: post-validation が git 全木を参照し、並列 WBS 実行時に「想定外ファイル」を想定誤検知。
- 影響: false-positive が exit=1 を誘発し、マルチWBSの収束を遅延。

#### carry-3: Codex 役割判定ミス

- 由来: PLAN-028 W-1/W-5a/W-6/W-9、PLAN-029 W-9/W-4/W-10 carry
- 内容: docs / TL ロールが実装指示プロンプトを「レビュー」と誤分類し、出力テンプレートが逆流。
- 影響: 実装指示が実処理に至らず、ヒューマン手戻りが増加。

#### carry-4: doctor PMO role consistency 整合不足

- 由来: PLAN-029 W-2/W-3 carry
- 内容: `[ロール設定] role config consistency` は PMO の Sonnet/Haiku と `models.yaml` / `claude.yaml` の整合を十分検出していない。
- 影響: 実行時ロール起因のズレを放置しやすく、role 切替の説明責任が曖昧。

#### carry-5: research.conf 乖離 (履歴乖離の再検証)

- 由来: PLAN-024 carry の継続線として 2026-05-06 〜 2026-05-08 にかけて memory に「research.conf=5.4 / models.yaml=5.2-codex / CLAUDE.md=5.2」と記録されてきた。
- 現状 (2026-05-08 W-0 時点で再確認): `cli/roles/research.conf` の `codex_model=gpt-5.5`、`cli/config/models.yaml` の `research: gpt-5.5` で **両者は整合**。PLAN-028 W-2 (cli/roles + models.yaml v2 役割再配置) で実質的に解消された可能性が高い。
- W-5 の役割: memory 記録上の三重乖離を再検証し、`resolved` (既に整合) か `partial` (CLAUDE.md / docs 側に残存) かを判定する判断 sprint。実ファイル更新は別 commit に分離。
- 影響: 本 carry は仕様変更ではなく **memory / docs 側の表記更新** に縮退する見込み。

##### W-5 判定 (2026-05-09 完了)

- **判定: resolved (両ソース整合済)**
- 検証範囲:
  - `cli/roles/research.conf:1` = `codex_model=gpt-5.5` ✓
  - `cli/config/models.yaml:14` = `research: gpt-5.5` ✓
  - `CLAUDE.md` / `AGENTS.md` / `helix/HELIX_CORE.md` に research.conf 関連の記述なし (古い乖離記録は反映されていない)
- 結論: PLAN-024 Sprint .1 (2026-05-06) 起源の三重乖離 (research.conf=5.4 / models.yaml=5.2-codex / CLAUDE.md=5.2) は **PLAN-028 W-2 (cli/roles + models.yaml v2 役割再配置) で実質的に解消**された。memory 側の古い記録 (`project_2026_05_06_plan024_sprint1.md` 等) のみが stale。
- 後処理: 別 commit で memory carry 記述の整理 (Opus 直接更新)。実装 / 設定変更は不要。

#### 除外 carry: raw claude shim HELIX_CLAUDE_INTERNAL guard

- 出典: `.helix/retros/PLAN-028.md:58` の Try「raw claude shim の HELIX_CLAUDE_INTERNAL guard 強化テスト」。
- 扱い: **out-of-scope** (PLAN-028 retro Try として記録済、PLAN-030 carry 5 件には含まない)。本軸は guard テスト追加であり PLAN-030 集約 5 軸とは性質が異なるため、PLAN-031 候補または `helix-claude` 改修 PR で別途扱う。

### 2.4 非対象

- PLAN-029 W-10 §6 の TUI / Web ダッシュボードは本 PLAN の実装対象外 (ユーザー指示で **明示的に非対象**)。
- 監査の優先は「carry の収束 + テスト安定化 + 仕様一致」に限定し、可視化 UI は次計画に残す。
- raw claude shim guard 強化テスト (上記) も非対象。

---

## 3. 収束 5 軸の対応設計（Draft）

以下は各 WBS が 1 軸を受け持つ設計方針。詳細実装は carry を起点に必要な commit で補完。

### Axis 1 (W-1): helix-test self-test 5 件 v2 値追従

#### 方針

- `cli/helix-test` の self-test 5 件で旧期待値を v2 値へ更新。
- 真値ソースは `cli/config/models.yaml` とし、`models.yaml` 変更時の再調整基準を明確化。
- 変更差分は自己テスト観点で最小化し、他モジュールへの副作用を避ける。

#### 成果像

- テストケース数 5 件全てが v2 値を検証対象に採用。
- `pytest` + `bats` で green を確認可能。
- carry 由来: PLAN-028/029 共通 carry の 1st class 解消。

### Axis 2 (W-2): helix-codex --allowed-files 並列誤検出改修

#### 方針

- post-validation で git working tree 全体を見ない。
- 起動時の `git status` 差分 snapshot を保存し、`allowed-files` が触れたファイルのみを監査対象に限定。
- 並列 WBS 実行でも自己 deliverable 以外を想定外扱いしない。

#### 成果像

- `self`/`touched file` スコープに対してのみ検知が走る。
- 新規の false-positive ケースを持つ回帰テストを追加。
- carry 由来: PLAN-028 W-3a/b/c, W-4/5a + PLAN-029 1st 波 6 反映。

### Axis 3 (W-3): Codex 役割判定（実装/レビュー）改善

#### 方針

- `helix-codex --role` 起点プロンプトへ `[タスク種別] 実装/レビュー/設計` の注入を必須化。
- docs system prompt へ「実装指示 (`[タスク種別] 実装`) なら review template に送らず **文書実装を直接実行する**」条件を追加。
- TL system prompt へ「実装指示でも **コード実装は行わず**、review template にも送らず、`delegate_to: <role>` / `blocked` / `route` のいずれかを返す」条件を追加 (ROLE_MAP / tl.conf 整合)。
- 役割注入を先頭シグナルとして扱い、分類誤差を抑える。

#### 成果像

- `実装指示プロンプト + docsロール` が review template に流れず実装出力になる。
- キャリアとして、レビュー呼び出しと実装呼び出しの分離を明示。
- carry 由来: PLAN-028 および PLAN-029 での繰り返し carry。

### Axis 4 (W-4): helix doctor の PMO 整合チェック追加

#### 方針

- `[ロール設定] role config consistency` 監査に `pmo_sonnet` / `pmo_haiku` 比較を追加。
- source of truth を `models.yaml` と `claude.yaml` の対応キーとして扱う。
- 不整合時は warn 扱いで出力し、運用判断を明確化。

#### 成果像

- `helix doctor` に PMO 整合チェックカテゴリが追加。
- 不一致検知時に明示的な警告を返却。
- carry 由来: PLAN-029 W-2/W-3。

### Axis 5 (W-5): research.conf 乖離整理（判断 sprint）

#### 方針

- ここは実装 sprint ではなく判断 sprint とし、PM・ユーザー合意の意思決定材料を整理。
- 本 Sprint では以下を整理し PR 素案を残す。
  - 乖離ファイル（`research.conf`, `models.yaml`, `CLAUDE.md`）の現状値
  - 差分の根拠（起点 / 更新履歴 / 利用箇所）
  - 決定時の rollback 影響
- 最終統一値は PM (Opus) とユーザーが別コミュニケーションで決定。

#### 成果像

- 本 PLAN 側で判断資料を 1 ファイルに集約。
- 実値確定後、別 PR で 3 ファイル統一に着手。
- carry 由来: PLAN-024 と引き継がれた連続 carry。

---

## 4. Sprint 計画（W-1..W-6）

- 原則: 1 Sprint = 1 軸の carry 解消。
- W-1..W-5 は axis 担当、W-6 が統合レビュー。
- Sprint 間依存は W-5（判断）を除き並列実施可能とするが、最小依存で順次検証を行う。

### W-1: self-test 5 件 v2 値追従

- 対象 carry: carry-1
- 依存: なし（v2 参照値の確定が先）
- ターゲット: `cli/helix-test`
- DoD（要約）:
  - self-test 自己検証 5 件が `cli/config/models.yaml` の v2 値と一致
  - `pytest` と `bats` が両方 pass
  - carry-1 が完了状態として記録
- 関連 retro 出典: PLAN-028, PLAN-029

### W-2: allowed-files 並列誤検出改修

- 対象 carry: carry-2
- 依存: なし (W-1 と独立)
- ターゲット: `cli/helix-codex` (post-validation `--allowed-files` 検査ロジック)
- DoD:
  - 起動時 snapshot 保存先: `.helix/tmp/codex-baseline-<pid>-<timestamp>.txt`
  - snapshot 内容 (現行 cli/helix-codex の dirty file 検出と同じ 3 集合の和):
    1. `git diff --name-only` (unstaged tracked changes)
    2. `git diff --name-only --cached` (staged changes)
    3. `git ls-files --others --exclude-standard` (untracked but not ignored)
  - baseline dirty files の扱い: 起動時の上記和集合に含まれるファイルは「並列他 WBS 由来」として post-validation 対象外
  - touched-only 判定: post-validation 終了時にも同じ 3 集合を取得し、**baseline を除外した集合**のみが検査対象。allowed-files に含まれない場合のみ exit 1
  - 安全性保証: 既存の untracked 新規作成 reject (allowed-files 外への新規 untracked ファイル作成) は維持。baseline dirty untracked のみ除外する
  - 追加テスト: `cli/tests/test_helix_codex_allowed_files.bats`
    - case-1: 並列 helix-codex 2 プロセス同時実行で他 WBS の tracked 変更が exit 1 を引き起こさない (false-positive reproducer)
    - case-2: allowed-files 外への新規 untracked ファイル作成は **引き続き reject** (guard 維持)
    - case-3: baseline に既に存在した untracked ファイルへの touch は除外される
  - 追加 pytest: `cli/lib/tests/test_codex_post_validation.py` で baseline 除外ロジックの単体テスト (3 集合の和、baseline 除外、allowed-files 突合)
- 関連 retro 出典: PLAN-028 W-3a/b/c, W-4/5a / PLAN-029 1st 波 6 並列 carry

### W-3: Codex 役割判定改善

- 対象 carry: carry-3
- 依存: なし (W-2 と独立)
- ターゲット:
  - `cli/templates/prompts/role-prefix.md` (新規 or 既存 prefix template)
  - `cli/roles/docs.conf` の system prompt セクション (docs は文書実装担当、実装出力 OK)
  - `cli/roles/tl.conf` の system prompt セクション (TL は設計/レビュー/ゲート判定担当、実装は SE/PE へ委譲または blocked/route)
  - `cli/helix-codex` の `--task` 前段に `[タスク種別]` 自動注入 + `review_template_path` の条件付き注入ロジック

- 役割契約 (重要、ROLE_MAP.md / tl.conf / docs.conf に整合させる):
  - **docs role**: `[タスク種別] 実装` を受けたら **文書実装を直接出力**する (apply_patch / Edit OK)。これは docs の正規責務。
  - **TL role**: `[タスク種別] 実装` を受けても **コード実装は行わない**。代わりに以下のいずれかを返す:
    1. SE / PE / docs へ委譲 (`delegate_to: <role>` を含む)
    2. `blocked` (実装前提が不足: 設計未決、契約未凍結 等)
    3. `route` (本タスクは TL 役割範囲外: docs に振るべき等)
  - **共通**: `[タスク種別] レビュー` の場合のみ review_template を適用し verdict を返す。

- DoD:
  - `helix codex --role <role> --task "..."` で task 冒頭に `[タスク種別]` がない場合、自動推定 (実装指示動詞: 作成/書き出し/起票/Edit/Write/実装/追加 等 → 実装、レビュー/評価/検証/監査 等 → レビュー) して prefix 注入
  - `[タスク種別] レビュー` 以外 (= 実装/設計/調査 等) では `review_template_path` を **prompt に注入しない** (review template 誤適用の根本抑止)
  - docs system prompt に「`[タスク種別] 実装` 時は文書実装を直接出力」明記
  - tl system prompt に「`[タスク種別] 実装` 時は委譲/blocked/route のいずれかを返し、コード実装はしない」明記
  - 順方向テスト 1: `cli/tests/test_codex_role_intent.bats` で「`[タスク種別] 実装` + docs role → 文書実装出力 (apply_patch / Edit / 新規ファイルパス) が含まれる」検証
  - 順方向テスト 2: 同 bats で「`[タスク種別] 実装` + tl role → `delegate_to` または `blocked` または `route` のいずれかが含まれ、apply_patch / Edit を **含まない**」検証
  - 逆方向テスト: 同 bats で「`[タスク種別] レビュー` + docs/tl role → verdict のみ返り、apply_patch / Edit を含まない」検証 (review template 誤流入防止)
  - review_template_path 抑止テスト: pytest で「`[タスク種別] 実装` 時に prompt 内に review_template の文字列が含まれない」を assert
- 関連 retro 出典: PLAN-028 W-1/W-5a/W-6/W-9 / PLAN-029 W-9/W-4/W-10

### W-4: helix doctor の PMO 整合チェック追加

- 対象 carry: carry-4
- 依存: W-3（推奨）
- ターゲット: `helix doctor` の role consistency 監査
- DoD（要約）:
  - PMO Sonnet / Haiku の consistency check を追加
  - 不一致時 warn ログを出力
  - 監査 docs へ出典を残す
- 関連 retro 出典: PLAN-029 W-2/W-3 carry

### W-5: research.conf 乖離整理

- 対象 carry: carry-5（判断 sprint）
- 依存: W-4（推奨、doctor 判定文脈）
- ターゲット: 仕様・運用調整用資料
- DoD（要約）:
  - PM (Opus) とユーザーが決定可能な材料（乖離表・影響）を記録
  - 値確定方針（採用案 A/B/C）を文書化
  - 実ファイル更新は次 Sprint（別 commit）に切り出す
- 関連 retro 出典: PLAN-024 継承 carry, PLAN-029 carry 参照情報

### W-6: 統合検証 + retrospective + status completed

- 対象 carry: carry 全体の統合（carry-1〜carry-5）
- 依存: W-1..W-5
- ターゲット: `helix doctor`, `pytest`, `bats`, `.helix/retros/PLAN-030.md`
- DoD（要約）:
  - `pytest + bats` の PASS
  - `helix doctor` の PASS（warn は既知 carry 5 を除外条件明示）
  - `PLAN-030` ステータス completed に更新
  - `.helix/retros/PLAN-030.md` 作成（gitignore 管轄）
- 関連 retro 出典: PLAN-029 W-12 完了パターン

---

## 5. 受入条件 / Definition of Done

### 5.1 共通受入条件（各 axis 適用）

- 5 つの carry が carry 出典を明示され、PLAN-028/29 retro と追跡可能。
- 各 WBS の DoD が明確で、未完了 carry は W-6 でまとめて残件管理。
- carry 再発の最小化を意図した根拠（what/why/how）を記載。
- ダッシュボード非対象の明記が受入前提であること。
- 受入評価は 5 軸評価観点（density / depth / breadth / accuracy / maintainability）で 1.0 〜 5.0 スケールを提示。

### 5.2 PLAN 完了条件

- W-1: self-test 5 件が v2 値追従し、pytest+bats pass。
- W-2: parallel allowed-files が self touched-only 検査に移行し回帰テスト追加。
- W-3: Codex 役割判定の分岐誤判定を抑止し、bats で実装出力を検証。
- W-4: `helix doctor` に PMO consistency チェック項目を追加。
- W-5: research.conf 乖離整理の判断材料が揃い、PM/ユーザー合意を待機。
- W-6: `pytest+bats+helix doctor` が PASS、`.helix/retros/PLAN-030.md` 作成、status completed。
- W-6 後、PLAN-030 で受入判定（必要時は WBS 別 PR 分割）。

### 5.3 5 軸受入評価テンプレ

- density: carry 全体の要件抽出漏れがないかを確認
- depth: 各 carry の根因・対策・検証が1段階ではなく実行可能レベルで書かれているか
- breadth: PLAN-028/029 両系の carry 連結と関連 carry の見落としがないか
- accuracy: 参照先（models.yaml / retro / command）との整合が取れているか
- maintainability: WBS 増やす場合でも axis を軸に追跡しやすい構造か

---

## 6. 関連リンク

- [PLAN-028-helix-v2-orchestration.md](PLAN-028-helix-v2-orchestration.md)
- [PLAN-029-helix-rigor-expansion.md](PLAN-029-helix-rigor-expansion.md)
- [ADR-014: roles-config-format](../adr/ADR-014-roles-config-format.md)
- [ADR-015: helix-v2-orchestration](../adr/ADR-015-helix-v2-orchestration.md)
- [cli/helix-test](../../cli/helix-test)
- [cli/helix-codex](../../cli/helix-codex)
- [cli/helix-doctor](../../cli/helix-doctor)
- [cli/config/models.yaml](../../cli/config/models.yaml)
- [cli/roles/research.conf](../../cli/roles/research.conf)
- carry 出典: `.helix/retros/PLAN-028.md` / `.helix/retros/PLAN-029.md` (gitignored、ローカル監査用)
- 関連 memory: `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/project_2026_05_08_overnight_completion.md`


# matrix-weak-cell-plan

- 最終更新: 2026-05-14
- タスク: `audit-summary.md` §3 の 5 層 × 3 問題 matrix に基づく最弱セル top-3 の補強計画
- 参照: [`docs/v2/A-audit/audit-summary.md`](/home/tenni/ai-dev-kit-vscode/docs/v2/A-audit/audit-summary.md), [`docs/v2/A-audit/capability-matrix.md`](/home/tenni/ai-dev-kit-vscode/docs/v2/A-audit/capability-matrix.md)

## 0. 事前確認（Top-3の採用方針）

1. `audit-summary.md §3` の弱点表では、weakest top-3 は以下のとおりである。
   1. PM × スパゲッティ防止
   2. Command × スパゲッティ防止
   3. Verify × 契約漏れ防止
2. タスク入力にある TL audit 助言（PM × 契約漏れ、Skill × 契約漏れ、Orchestration × スパゲッティ防止）は、`audit-summary.md §3` の Top-3 と一致しないため、本設計では `audit-summary.md` の現時点順位を優先採用する。
3. ただし、タスク入力の推定も設計上のリスクとして §4 で共通課題として吸収し、Phase 5 の remediation へ接続する。
4. 本ドキュメントは 300-500 行の実装方針ドキュメントとして、各セルを 100 行以上で詳細化する。

## 1. 監査証跡マッピング（セル定義）

- Phase 2-5 のうち、Phase 2 は観測点整備、Phase 3 は契約連携、Phase 4 は検証自動化、Phase 5 は運用継続改善という前提で計画を立てる。
- 重点は「機能しているが薄い」状態から「fail-close できる」状態への移行であり、実装負荷より接続密度の改善を優先する。
- 共通の評価軸: 
  - 現状を定量化（能力不足点）
  - capability の「何ができて、何ができないか」を可視化
  - Phase と ownership を明確化
  - KPI を 0.5 増分または明確目標値で定義
- 用語:
  - capability: 実行可能性を持つ機能＋運用接続。
  - dead routing: 委譲ルートが無限ループ化、重複、または不適切な role 宛への再試行。
  - writer disconnect: 契約・検知結果・ゲート結果の DB/レポート反映不足。

---

## 2. §1 セル 1: PM × スパゲッティ防止

### 2.1 現状 capability 詳細（何ができるか / 何ができないか）

1. できること
   1. `PLAN / WBS / handover` のルールを通じて、実装禁止領域や承認フローの骨格を強制できる。
   2. `PMO` 経路（PMO Sonnet/Haiku）とエスカレーション記録を通して、進行停止条件を示せる。
   3. `helix codex --approved` などで実装承認前提を要求できる。
   4. `blocked / ready_for_review` などの状態遷移は行える。
   5. 一部手順で `handover` メタデータの有無が判定可能。
2. できないこと
   1. PM が見るべき構造 debt（重複, dead, relation graph degradation）の「最上位 TOP」を自動生成できない。
   2. PM 向けサマリーの標準フォーマットがなく、意思決定の比較可能性が低い。
   3. 「どの委譲がどの phase に悪影響か」を自動採点できない。
   4. `PM 視点の契約漏れ診断` と `PM 判断支援指標` が疎結合。
   5. 進行中の構造問題を phase 進捗に反映するループが限定的。
   6. ドリフト（docs/drift, contract drift, plan drift）を一枚のカードに圧縮しない。
   7. PM の意思決定負荷を 1 行で把握できる KPI 面がない。
   8. 重大度の高い構造欠陥の再発率を継続追跡できない。

### 2.2 不足箇所

1. PM 用の debt index（構造 / 委譲 / 契約）を作る入口が不足。
2. PM 用の「構造健康度」を表現する `dashboard` かつ `phase tie-in` が不足。
3. top debt の自動ランキングがないため、PM が優先順位を経験則に依存して決定している。
4. `handover` で更新された問題を `task-plan` や `PLAN` への反映が遅延。
5. `PM向け契約漏れ検知` の自動エスカレーション条件が不足。
6. 監査レポートが散在し、PM が最終判断で参照する anchor が不統一。
7. `DR-001`, `DR-004`, `DR-005`, `DR-007`, `DR-020` の横断影響を同時表示できない。

### 2.3 V2 で追加すべき capability（具体 CLI / detector / skill）

1. CLI: `helix pm-health`（新規）
   1. `hnd_* debt` と `detector verdict` の集約（PM view の 1 スライス）
   2. `plan_id` / `wbs_id` / `reference_docs` の到達率を可視化
   3. phase 毎の滞留時間上位を Top-5 表示
   4. `structure debt`, `delegation debt`, `contract debt` を合成スコア化
2. detector: `axis-pm-structure`（新規）
   1. top debt の算定ルールを定義（重複ファイル、dead skill call、長尺保留事項、未対応 carry）
   2. `PM` 受け取り用 verdict（PASS / WARN / BLOCK）を付与
   3. `contract drift` と同一エントリ内で関連づけ
   4. 判定結果を DB へ writer する
3. skill: `helix:docs:documentation` と `helix:workflow:dependency-map` 連動 skill chain
   1. PM に必要な要約を 1 ページ化
   2. 変化点（前週比/前 phase 比）を抽出
   3. 再発率の推移を説明文付きで出力
4. skill: `helix:project-management` の PMO 導線
   1. 優先順位決定の説明テンプレート（何を優先するか、理由）
   2. `PMo` からの確認要求を最小化する structured question set
   3. 受け入れ時に検証結果を添付する自動テンプレート

### 2.4 既存 capability の流用度

1. 高流用（そのまま拡張）
   1. `helix CODEX_TL_MODE.md` の role 分担規則（ガード条件として再利用）
   2. handover blocker/ready_for_review の状態遷移
   3. `task-plan` の acceptance 条件情報
2. 中流用（一部改修）
   1. `helix code find` の検索結果を PM debt 抽出の input 化
   2. audit 由来の Top-10 指標を `summary` へ統合
   3. verify 実行ログの要約を PM 向けに reframe
3. 低流用（再設計）
   1. PM KPI の数値化ロジック
   2. 契約影響の優先度算定ロジック
   3. 構造問題を phase 進行へ直接接続するルート

### 2.5 Phase 紐付け

1. Phase 2
   1. debt スキーマの定義（PM debt model v1）
   2. 既存 handover / plan / matrix から入力 mapping 設計
2. Phase 3
   1. PM dashboard の最小表現（top debt + 主要未解決）実装
   2. `PM × スパゲッティ防止` 用 detector を gating path に接続
3. Phase 4
   1. PM summary がゲート/レビュー時に必須出力として添付される運用確立
   2. dead routing 検知→ escalation ルールを実装
4. Phase 5
   1. KPI トレンド可視化を plan 進捗と連動
   2. PM 意思決定の再現性を 1 クエリで検索可能化

### 2.6 実装 sketch（Phase 2-5）

1. Phase 2: 設計
   1. PM debt のデータモデルを確定
   2. `PM` 関連検知ルールの重み付け定義
   3. 既存指標（handever blocker、phase 遅延）を取り込み
2. Phase 3: 初期実装
   1. CLI `helix pm-health --summary --phase 2` を追加
   2. 主要指標（構造 debt、委譲失敗、契約影響）を 1 画面で返す
   3. DR-004, DR-007, DR-020 の横断対応ルートを実装
4. Phase 4: 検証接続
   1. `axis-pm-structure` を検証フローに入れた後 gate fail / block のトリガを検証
   2. レポートを docs/summary と plan 行として writer 化
   3. PM への通知文言を安定化（再現性あるメッセージフォーマット）
5. Phase 5: 運用化
   1. 週次トレンドレポートの自動生成
   2. PM review での確認テンプレートを固定
   3. 期初比較、期末比較、Phase 切り替え時の影響度比較を確立

---

## 3. §2 セル 2: Command × スパゲッティ防止

### 3.1 現状 capability 詳細（何ができるか / 何ができないか）

1. できること
   1. `helix gate`, `helix sync` 企画、`pre-commit` hook、`SessionStart` / `PostToolUse` などの検証入口が存在。
   2. raw CLI 逸脱対策、role 制御、consent/approved ガードが存在。
   3. PLAN 起点を崩さないための運用規則が文書化され、拒否/許可の初期分岐がある。
   4. `verify/*.sh` や `bats` による基本検証ルートがある。
   5. `cli` 下の command 実装が複数あるため選択肢は豊富。
2. できないこと
   1. 編集前後の検知→sync→gate→review の一本化が不十分。
   2. `file edit -> static check -> contract update -> detector` の順が command ごとに揺れる。
   3. dead code/重複 command の可視化が弱く、運用上の負債が積み上がる。
   4. plan/skill/verify の3層をまたぐ統一された command トランザクションがない。
   5. pre-commit 側の実施と SessionStart 側の実施タイムラインが一致しない。
   6. Plan-067 由来 `helix sync --auto` が未完により自動統合入口が不在。
   7. `command` レベルで何が実施されたかの監査ログが分散している。
   8. コマンド名・alias・prefix の drift が一部残存しており discoverability が低い。

### 3.2 不足箇所

1. コマンドチェーンの最短閉ループが存在しない。
2. 編集トリガ時に必要なチェック群の同時実行ルールがない。
3. `command failure` の分類と再試行経路が統一されていない。
4. 企画→実装→検証で同一 ID を保持しきれず、原因追跡が困難。
5. command 層の品質ゲートが `phase` ごとに散在し、共通運用基準が弱い。
6. 再実行性（idempotency）に関するルールが command 単位で未統一。

### 3.3 V2 で追加すべき capability（具体 CLI / detector / skill）

1. CLI: `helix pipeline --auto`（新規）
   1. `file edit` 入力を受けて `detector run -> contract update -> gate -> sync` を 1 トランザクション化。
   2. 失敗時に再試行 strategy（fast retry / full retry / manual）を提示。
   3. 実行結果を `command_workflow_log` テーブルへ writer。
2. CLI: `helix command-audit`（補強）
   1. dead code / unused alias / command 名衝突を検出。
   2. phase 別の命名規約・prefix 合否をチェック。
   3. `docs` と `cli` の対応欠落を報告。
3. detector: `axis-comm-sync`（新規）
   1. 編集から gate までの時間差を監視し遅延閾値超過を検知。
   2. 同一 commit/pipeline で sync 未実施を block。
   3. command chain deadlock（route A->B->A）検知。
4. skill: `workflow/quality-lv5` / `tools/ai-coding` 連携
   1. command レイヤの品質規約テンプレートを適用。
   2. 重複 path から候補のリファクタリングスキルへ自動案内。
5. skill: `ops / dev-setup` の組み合わせ
   1. hook 設定の最小セットを提示。
   2. pre-commit / post-tool で実行する checkset を role 別に最適化。

### 3.4 既存 capability の流用度

1. 高流用
   1. `helix gate` の既存検証群（fail-close 前提）
   2. hook フレームワーク（SessionStart/PostToolUse）
   3. `PLAN-067` の仕様断片
2. 中流用
   1. 既存 alias/command 構成から新 auto pipeline への接続
   2. pre-commit の既存 lint/test スクリプトを再利用
   2. 既知の禁止コマンド検知ロジックを統合
3. 低流用
   1. command failure から phase 影響評価への map
   2. command-level telemetry を PM/Verify へ再配線

### 3.5 Phase 紐付け

1. Phase 2
   1. command pipeline 仕様（入力/出力/失敗時挙動）を確定
   2. 監査ログキー（operation id）を導入
2. Phase 3
   1. `pipeline --auto` のプロトタイプを導入し、主要コマンドを接続
   2. `axisl-comm-sync` を実行可能化
3. Phase 4
   1. `helix gate` に command chain 完走率指標を追加
   2. `pipeline` 実行失敗時の escalator（再実行 or escalate）を固める
4. Phase 5
   1. 重複コマンド削減レポートの導線化
   2. command debt の推移を月次で評価

### 3.6 実装 sketch（Phase 2-5）

1. Phase 2: 事前設計
   1. `command_workflow_log` の最小 schema を定義
   2. 編集イベントから gate 完了までのステップモデルを確定
   3. plan 参照の参照先を正規化
2. Phase 3: 実装
   1. `helix pipeline --auto --path <git-path>` を追加
   2. command 実行時に detector + contract + gate を順序実行
   3. dead routing の最小検知ロジックを実装
3. Phase 4: 検証
   1. `verify/*.sh` への組み込みテスト追加
   2. 失敗シナリオ（pre-commit 先行、後追い、skip）をシミュレーション
   3. レポートに command chain の完走率/異常率を追加
4. Phase 5: 定着化
   1. `command debt` の目標値（例: 4 週間で 30% 削減）を設定
   2. 事故再発率に基づく guard policy を改善
   3. phase 遷移時の承認者向け確認票を固定フォーマット化

---

## 4. §3 セル 3: Verify × 契約漏れ防止

### 4.1 現状 capability 詳細（何ができるか / 何ができないか）

1. できること
   1. `PLAN`/`API`/`DB` のドリフト検知（axis-07, axis-08, axis-12）をある程度担える。
   2. `verify` と `detector` が存在し、コア5 layer coverage の基盤を形成。
   3. `helix gate --pair-check` のようなペアリング検証は使える。
   4. `contract_registry` が API 契約の基本運用をサポート。
   5. `pair-check` の思想はある。
2. できないこと
   1. FE 契約、handover 契約、docs-to-impl contracts の統合 coverage が不足。
   2. contract break の severity を `PM`/`Orchestration` へ自動再ルーティングできない。
   3. `design review writer` が不十分で、検証結果が phase の実行に連動しにくい。
   4. `contract_entries` の対象拡張（実装計画 / テスト設計 / 運用契約）が未完。
   5. `detector verdict` の多言語化・整合化・再現レポートが薄い。
   6. `schema` と `runtime artifacts` の接続不一致が起きても即 fail しにくい。
   7. 仕様逸脱が検知されても remediation までの道筋が断続的。

### 4.2 不足箇所

1. 契約種別（D-API, D-DB, D-CONTRACT, FE契約, Handover契約, Docs契約）の横断モデルがない。
2. verify の判定に phase と receiver（PM/SE/QA）を紐づけるルールが不足。
3. contract break 時の routing policy の定義不足。
4. テスト観点の欠如（dynamic scenario / 実行系 drift）で、静的検証に偏る。
5. `contract` と `metric` の writer 接続が弱い。

### 4.3 V2 で追加すべき capability（具体 CLI / detector / skill）

1. CLI: `helix contract-bundle check`（新規）
   1. D-API / D-CONTRACT / D-DB / D-STATE / Handover contract を束ねて検証。
   2. contract break の分類と影響範囲を出力。
   3. 受入フェーズで必須出力を定義。
2. CLI: `helix contract-impact route`（補助）
   1. breaking change を検知した場合、対象 role と次アクションを提示。
   2. TL/PM への escalte を自動付与。
   3. `reference-doc` 未指定時の fail-close を補助。
3. detector: `axis-verify-contract-matrix`
   1. 15セル matrix の契約漏れを phase別に再評価。
   2. FE/Docs/Handover の欠落時に contract score を低下。
   3. score を `debt` として writer。
4. skill: `workflow/api-contract` + `workflow/design-doc` + `project/db`
   1. 契約変更時の影響箇所をテンプレ化。
   2. FR-ID 連結と pair-check の接続。
   3. 契約破壊を検知した場合の最小修正計画を提示。
5. skill: `verification` / `testing`
   1. scenario-level contract test set を追加。
   2. DR-019 / DR-011 系再発防止テストを追加。

### 4.4 既存 capability の流用度

1. 高流用
   1. `contract_registry` と axis-07/12
   2. `helix gate` の既存判定ロジック
   3. DR ベースの監査分類
2. 中流用
   1. `pair-check` 構造を FE/Docs/Handover まで拡張
   2. verify ドリフトの score 計算関数を再利用
   3. existing detector の severity 定義を契約種別用に再編
3. 低流用
   1. contract bundle のデータモデル
   2. 契約種別の route policy

### 4.5 Phase 紐付け

1. Phase 2
   1. 契約種別拡張の最小スキーマを定義
   2. contract score の定義（数値化）を明示
2. Phase 3
   1. `helix contract-bundle check` の v1 を追加
   2. FE/handover docs の対象を contract 検証範囲に加える
3. Phase 4
   1. gate と verify に contract bundle を接続
   2. 重大度高の contract break で自動 escalate を義務化
4. Phase 5
   1. 契約漏れ率の月次推移トラッキング
   2. `debt` 解消率をレビュー時評価に反映

### 4.6 実装 sketch（Phase 2-5）

1. Phase 2: 事前整備
   1. 契約種別の正規化モデルを採択
   2. 既存 D-API/D-DB/D-CONTRACT との突合ルールを定義
2. Phase 3: 実装
   1. `contract-bundle` コマンドを追加し、既存 registry と接続
   2. contract score の export を writer に接続
   3. contract break の受け取り先を rule 化
3. Phase 4: 検証
   1. 代表シナリオ（契約破壊, 参照欠如, docs drift）を scenario test 化
   2. pair-check と contract score の整合テスト
4. Phase 5: 運用最適化
   1. 契約漏れ修復のチケット自動生成
   2. PR レビュー時の contract チェックリスト自動添付
   3. 監査 evidence の更新手順を固定化

---

## 5. §4 セル間共通課題（3セル共通）

1. source-of-truth 不一致
   1. PM, command, verify の観点で参照先が揺れ、1 つの事象に対し 2-3 のレイヤが別結論を出しやすい。
   2. PLAN/WBS / docs / DB の接続元が明示されると同時に、更新ルートも固定化する必要。
2. writer 接続不足
   1. 検知→判定→修正というループがあるものの、検知結果が DB/plan/PM summary に一元 writer されない。
   2. `task-plan` への反映、handover への反映、検証ログ反映が分断。
3. routing と escalation 関係の断絶
   1. どの役割がどの severity を受け持つかが明確でない。
   2. 委譲失敗時に次アクションへ遷移しにくく、死循環が起きやすい。
4. phase スライスの欠落
   1. phase 横断 KPI がなければ、Phase 2 で改善した効果が Phase 4 で効いているか確認できない。
   2. KPI の更新責任が分散している。
5. ドキュメント drift の補足が不足
   1. `audit-summary` で指摘したドキュメント drift が runtime の判断入力になる前に stale 化。
   2. 技術文書の更新サイクルと実装サイクルが別で、同一イベントに対する同期が取れない。

共通対策の結論

- 3セルで共通して `PM view`, `command pipeline`, `contract bundle` の 3 つを最小セットとして実装する。
- これにより source-of-truth 不一致と writer 欠損を同時解消し、dead routing を減らす。

---

## 6. §5 V2 phase ロードマップ

| セル | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|---|---|---|---|---|
| セル1: PM × スパゲッティ防止 | PM debt schema 定義、handever / plan / matrix 指標 mapping、`axis-pm-structure` 草案 | `helix pm-health` MVP、top debt 表示、構造指標の定量化、PM 向けサマリ雛形 | PM 要約を gate / review に必須添付、dead routing への escalation 自動化、改善率トラッキング | PM 意思決定再現レポート、週次 debt トレンド、Phase 遷移ガード更新 |
| セル2: Command × スパゲッティ防止 | command_workflow_log 設計、pipeline ステップ定義、失敗時アクション表定義 | `helix pipeline --auto` + `axis-comm-sync` PoC、コマンド連携テスト開始 | pipeline/verify 連結、重複・dead routing 検知の CI 導通、sync 未実施時の block 運用 | command debt 指標の可視化、コマンド整理の継続的推奨、運用マニュアル確定 |
| セル3: Verify × 契約漏れ防止 | 契約種別スキーマ整備（D-API/D-DB/D-CONTRACT/FE/Docs/Handover）、score 定義 | `helix contract-bundle check` PoC、contract impact routing、pair-check 拡張 | gate 連携・自動エスカレーション運用、scenario contract test 導通 | 契約漏れ率レポートの月次運用、契約 drift 指標の継続改善 |

---

## 7. §6 KPI（V2 後の健全度目標値）

1. セル1（PM × スパゲッティ防止）
   1. 現状想定: 健全度 4/10
   2. V2 後目標: 8/10（+4）
   2. 補助 KPI
      1. PM 週次レポート作成時間: 120 分 → 45 分（約 62% 削減）
      2. 構造 debt 再発率: 30% → 10%（66% 削減）
      3. PM 未解決 blocker 平均滞留日数: 5.0 日 → 1.8 日
      4. Top debt 反映遅延: 1.5 週間 → 2 日以内
2. セル2（Command × スパゲッティ防止）
   1. 現状想定: 健全度 5/10
   2. V2 後目標: 9/10（+4）
   2. 補助 KPI
      1. 編集後 1 事件検知完了率: 60% → 95%
      2. pre-commit と session hook の順不同不一致: 40% → 5%
      3. command dead routing 検知数: 月次 15 件 → 2 件
      4. 再実行失敗率: 18% → 4%
3. セル3（Verify × 契約漏れ防止）
   1. 現状想定: 健全度 4/10
   2. V2 後目標: 8.5/10（+4.5）
   2. 補助 KPI
      1. 契約漏れ検知のカバレッジ: 52% → 90%
      2. 契約 break 発見リードタイム: 48 時間 → 4 時間
      3. FE/Handover/docs 契約の検証抜け: 5 件/四半期 → 1 件未満
      4. contract score 継続改善率: 60% → 85%

4. 全体横断 KPI（共通）
   1. 15 セルの中央値健全度: 3.9/10 → 8.6/10
   2. 重複・dead・未接続由来の再作業率: 27% → 8%
   3. `top-3` 再発率: 3 セル中 2 セルが 2 週間で再発 → 2 ヶ月で 0 セル再発

---

## 8. 補足: 実装/運用の整合チェック

1. `audit-summary.md §3` の Top-3 を採用し、セル詳細は 3 件を優先。
2. `capability-matrix.md` の現状分類（PM / Command / Verify 各スパゲッティ・契約関連）と矛盾しない形でスコープを固定。
3. 与えられた TL 助言は共通課題 §4 の「source-of-truth/ writer」の前提化で吸収。
4. 追加提案の機能は既存能力の再接続が中心であり、全件「新規機能より再統合」を優先。


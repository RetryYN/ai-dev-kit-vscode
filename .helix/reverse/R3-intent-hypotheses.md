# R3 Intent Hypotheses: HELIX CLI フレームワーク

> 生成日: 2026-04-05
> 対象: ~/ai-dev-kit-vscode (HELIX CLI v3)
> 手法: R0/R1/R2 の証拠から要件仮説を逆引き復元（Reverse HELIX R3）
> ステータス: PO 検証待ち

---

## 1. プロダクトビジョン仮説

### 1.1 HELIX は何のために存在するか

**仮説**: HELIX は「AI コーディングエージェント（Claude Code / Codex CLI）を使ったソフトウェア開発において、人間の開発チームが長年かけて獲得してきたプロセス品質を、AI にも強制的に適用する」ためのフレームワークである。

根拠:
- 7 段階のゲートシステム（G0.5〜G7）が fail-close で実装されている（R0: helix-gate 691行、R2: ADR-003）
- 12 ロールによる委譲（TL/SE/PG/FE/QA/Security 等）は人間の開発チームの役割分担を模倣している（R0: cli/roles/ 12ファイル）
- L1〜L8 のフェーズは SDLC（ソフトウェア開発ライフサイクル）の完全なカバレッジである（R2: 1.3 3つの開発モード）
- pre-commit hook によるフェーズガード（R2: ADR-009）は「AI が手順を飛ばす」ことを物理的に防止する
- 成果物対照表（Deliverable Matrix）は「ドキュメントを書かずにコードだけ書く」ことを防ぐ（R2: ADR-006）

**要約**: HELIX の存在意義は「AI に開発プロセスの規律を与える」こと。AI は速いが雑になりがちなコーディングを、ゲート・フェーズ・ロール・成果物チェックで制御する。

### 1.2 誰が使うのか（ペルソナ）

**主ペルソナ: AI オーケストレーター（PM ロール）**
- Claude Code（Opus）が PM として HELIX CLI を操作する
- タスクサイジング → フェーズスキップ判定 → ゲート通過 → Codex への委譲を自律的に実行
- 根拠: CLAUDE.md の「Opus = オーケストレーター + フロント設計」定義、helix-codex の 12 ロール委譲構造

**副ペルソナ: 人間の開発者/PO**
- `helix status` で進捗確認、`helix log feedback` で品質フィードバック
- ゲート判定（G1: PM+PO）で意思決定に参加
- `helix scrum decide` で仮説の採否を判定
- 根拠: feedback テーブルの user_score フィールド、PO 検証が必要な RG3 ゲート

**第三ペルソナ: Codex（実装エージェント）**
- helix-codex 経由でスキル注入付きタスクを受け取り、実装を実行する
- 根拠: helix-codex の prompt_construction（system_prompt + スキルパス + タスク内容）

### 1.3 競合/代替手段との違い

| 側面 | HELIX | Cursor / Windsurf 等 | 素の Claude Code / Codex |
|------|-------|----------------------|------------------------|
| プロセス制御 | ゲート駆動の fail-close 品質保証 | なし（ユーザー任せ） | なし |
| ロール分離 | 12 ロール × モデル最適配置 | 単一モデル | 単一モデル |
| 成果物管理 | Deliverable Matrix で網羅性保証 | なし | なし |
| 学習・改善 | SQLite ログ + recipe 生成 + 昇格 | なし | なし |
| 既存コード対応 | Reverse モード（R0〜R4） | 部分的（コード解析） | なし |
| 検証駆動 | Scrum モード（仮説→PoC→検証） | なし | なし |

**差別化仮説**: HELIX の最大の差別化は「プロセスの形式化」にある。他のツールが「AI にコードを書かせる」ことに注力するのに対し、HELIX は「AI にプロセスを守らせる」ことに注力している。

---

## 2. 機能要件仮説

### 2.1 コアワークフロー要件

| ID | 仮説要件 | 根拠（R0/R1 の該当箇所） | 確信度 |
|----|---------|------------------------|--------|
| REQ-F-001 | ゲート駆動の品質保証: 全フェーズ遷移にゲート通過を強制する | R0: helix-gate 691行、R1: G0.5〜G7 の 7 ゲート定義、state-machine.yaml の prereqs チェーン | 高 |
| REQ-F-002 | fail-close ゲート判定: mandatory チェック 1 件でも失敗すればゲート FAIL | R1: helix-gate の exit_codes（0=pass, 1=fail）、R2: ADR-003 | 高 |
| REQ-F-003 | 3 層チェック体系: static（シェルコマンド）+ AI（Codex レビュー）+ deliverable（成果物存在）でゲートを構成 | R1: gate-checks.yaml の static/ai 二層構造 + deliverable_gate.py | 高 |
| REQ-F-004 | ゲート invalidation カスケード: 上流ゲートの変更時に下流ゲートを自動無効化 | R1: state-machine.yaml の on_invalidate 定義、R2: 3.2 遷移ルール | 高 |
| REQ-F-005 | タスクサイジングとフェーズスキップの自動判定: S/M/L の 3 軸評価 + タスク種別でスキップ可能フェーズを自動決定 | R0: helix-size 409行、R1: sizing_logic（files/lines/api_db の 3 軸） | 高 |
| REQ-F-006 | L4 マイクロスプリント: 実装フェーズを .1a〜.5 の 6 ステップに分割し段階的に品質を上げる | R0: helix-sprint 505行、R1: sprint_steps 定義 + step_names | 高 |
| REQ-F-007 | 5 種類の駆動タイプ対応: be/fe/db/fullstack/agent でフェーズ内容を最適化 | R1: helix-size の drive_types、R2: 3.1 phase.yaml の sprint.drive | 高 |
| REQ-F-008 | fullstack ツインスプリント: BE と FE を並行実装（Phase A）し、結合テスト（Phase B）で統合 | R1: helix-sprint の fullstack tracks（be/fe/contract）、sprint.phase A/B | 中 |
| REQ-F-009 | プロジェクト初期化の自動化: テンプレートコピー + Git hooks + フレームワーク自動検出 + Claude settings マージ | R0: helix-init 284行、R1: side_effects 17項目 | 高 |
| REQ-F-010 | 設計提案のレビューフロー: draft → TL review → approve/reject → finalize の 3 段階 | R0: helix-plan 601行、R1: 設計レビューフロー | 高 |

### 2.2 AI エージェント委譲要件

| ID | 仮説要件 | 根拠（R0/R1 の該当箇所） | 確信度 |
|----|---------|------------------------|--------|
| REQ-F-011 | ロールベースのモデル最適配置: 12 ロール × モデル（5.4/5.3/5.3-spark）の対応表で最適なモデルを自動選択 | R0: cli/roles/ 12ファイル、R1: helix-codex の thinking_defaults | 高 |
| REQ-F-012 | スキル注入付き委譲: ロール別にスキル SKILL.md をプロンプトに自動注入し、専門知識を付与 | R1: helix-codex の prompt_construction、R0: skills/ 55+ スキル | 高 |
| REQ-F-013 | スキルオーバーレイ: プロジェクト固有スキル > グローバルスキルの優先度で解決 | R1: helix-codex の skills overlay 検索順（project/skills/generated → project/skills → global skills/） | 中 |
| REQ-F-014 | Codex 実行のリトライとコスト記録: 失敗時 2 回リトライ + cost_log テーブルにコスト記録 | R0: helix-codex 314行（MAX_RETRY=2）、R1: cost_log テーブル | 高 |
| REQ-F-015 | セキュリティガード: ロール名バリデーション + パストラバーサル防止 + 未検証スキル警告 | R1: helix-codex の security セクション（realpath + ensure_within_dir） | 高 |

### 2.3 Task OS 要件

| ID | 仮説要件 | 根拠（R0/R1 の該当箇所） | 確信度 |
|----|---------|------------------------|--------|
| REQ-F-016 | タスクカタログ体系: 63 タスク × 27 アクション型 × 295 アクションの 2 層構造で作業を標準化 | R0: helix-task 773行、task-catalog.yaml 47KB | 高 |
| REQ-F-017 | PM タスク選択 + TL レビュー: PM がタスクを選択し TL が自動レビューするワークフロー | R1: helix-task plan の side_effects（task_selections → tl レビュー） | 高 |
| REQ-F-018 | observe による品質検証: アクション型ごとの expect_keywords でログ内容を keyword 照合し品質を定量評価 | R1: helix-task observe（action-types.yaml の keyword 照合） | 高 |
| REQ-F-019 | タスク実行のログ永続化: task_runs → action_logs → observations の 3 層でトレーサビリティを確保 | R0: helix_db.py 844行（19テーブル）、R1: FK チェーン | 高 |

### 2.4 学習・改善要件

| ID | 仮説要件 | 根拠（R0/R1 の該当箇所） | 確信度 |
|----|---------|------------------------|--------|
| REQ-F-020 | 成功パターンの recipe 化: 成功タスクのアクション列を分析し再利用可能な recipe を自動生成 | R0: learning_engine.py 2000行、R1: analyze_success → save_recipe | 高 |
| REQ-F-021 | グローバル recipe 共有: プロジェクト横断で recipe を global.db に同期し、他プロジェクトで再利用可能にする | R0: global_store.py 611行（~/.helix/global.db） | 中 |
| REQ-F-022 | recipe の Builder 昇格: 実績ある recipe を SKILL.md / verify スクリプト / タスク定義に昇格する | R0: helix-promote 431行、R1: promotion_records テーブル | 中 |
| REQ-F-023 | フィードバックループ: ユーザーの correction/praise/suggestion/complaint を記録し品質改善に反映 | R0: helix-log 122行、R1: feedback テーブル（feedback_type/category/impact） | 高 |
| REQ-F-024 | レトロスペクティブ: G2/G4/L8 通過時にミニレトロを自動生成し振り返りを強制 | R0: helix-retro 60行、R1: retro_items テーブル | 高 |

### 2.5 Reverse / Scrum 要件

| ID | 仮説要件 | 根拠（R0/R1 の該当箇所） | 確信度 |
|----|---------|------------------------|--------|
| REQ-F-025 | 既存コードの設計復元: R0（証拠収集）→ R1（契約抽出）→ R2（設計復元）→ R3（要件仮説）→ R4（差分分析）の 5 段階パイプライン | R0: helix-reverse 244行、R1: stage_outputs（R0〜R4 の成果物定義） | 高 |
| REQ-F-026 | Reverse → Forward 接続: R4 完了後に Forward HELIX の適切なフェーズ（L1/L2/L3/L4）に自動接続 | R1: helix-mode の transition_constraints（reverse_to_forward: reverse.status == completed） | 中 |
| REQ-F-027 | 検証駆動開発（Scrum モード）: 仮説バックログ → スプリント計画 → PoC → 検証 → 判定のサイクル | R0: helix-scrum 497行、R1: 8 サブコマンド定義 | 高 |
| REQ-F-028 | 仮説の confirmed/rejected/pivot 判定: 検証結果に基づき仮説の採否を明示的に記録 | R1: helix-scrum decide（--confirmed/--rejected/--pivot）、backlog.yaml 更新 | 高 |

### 2.6 成果物管理・可視化要件

| ID | 仮説要件 | 根拠（R0/R1 の該当箇所） | 確信度 |
|----|---------|------------------------|--------|
| REQ-F-029 | 成果物対照表（Deliverable Matrix）: フェーズ × 駆動タイプで必要な成果物を網羅的に定義 | R0: helix-matrix 250行 + matrix_compiler.py 1435行、R2: ADR-006 | 高 |
| REQ-F-030 | 成果物の自動検知: ファイル存在 + 10 バイト以上で成果物状態を自動更新し、空ファイルの形式的通過を防止 | R1: matrix_compiler の auto_detect_state、R2: MIN_ARTIFACT_BYTES = 10 | 高 |
| REQ-F-031 | 成果物状態の 5 段階管理: pending/in_progress/done/waived/not_applicable | R1: VALID_STATE_STATUSES 定義 | 高 |
| REQ-F-032 | プロジェクト状態の一覧表示: フェーズ・ゲート・スプリント・DB 統計・次のアクション提案を統合表示 | R0: helix-status 247行、R1: output_sections 7項目 | 高 |

### 2.7 品質保証・フック要件

| ID | 仮説要件 | 根拠（R0/R1 の該当箇所） | 確信度 |
|----|---------|------------------------|--------|
| REQ-F-033 | フェーズガード（pre-commit hook）: 現在フェーズで許可されないレイヤーのファイル変更をブロック | R0: phase_guard.py 366行、R2: ADR-009 | 高 |
| REQ-F-034 | 凍結違反の自動検知と下流 invalidation: 設計凍結後の変更を検出し下流ゲートを自動無効化 | R0: freeze_checker.py 351行、R1: helix-hook の 3_freeze_violation | 高 |
| REQ-F-035 | PostToolUse フック: Claude Code の Edit/Write 操作後に 9 種類のチェックを自動実行 | R0: helix-hook 478行、R1: checks_executed 9項目 | 高 |
| REQ-F-036 | OWASP セキュリティチェック: SQL インジェクション・XSS・秘密情報ハードコード・Bearer トークン混入を自動検出 | R2: 5.3 セキュリティチェック（G4 mandatory 5項目） | 高 |
| REQ-F-037 | CLAUDE.md テンプレート強制: 新規作成時に必須セクション（技術スタック/コーディング規約/コマンド/HELIX ワークフロー）を含むことを強制 | R1: PreToolUse_Write フック（permissionDecision: deny） | 高 |

### 2.8 その他の機能要件

| ID | 仮説要件 | 根拠（R0/R1 の該当箇所） | 確信度 |
|----|---------|------------------------|--------|
| REQ-F-038 | 中断・復帰管理（IIP/CC）: 進行中タスクの中断と安全な復帰を管理 | R0: helix-interrupt 890行、R1: interrupts テーブル | 中 |
| REQ-F-039 | 技術負債台帳: 技術負債を構造的に管理（登録/優先度/解決）| R0: helix-debt 128行、R0: debt_items テーブル | 高 |
| REQ-F-040 | 自己ベンチマーク: 期間別メトリクス集計による自己診断 | R0: helix-bench 132行、bench_snapshots テーブル | 中 |
| REQ-F-041 | エージェントチーム実行: 複数エージェントの協調実行（strategy に応じた parallel/sequential） | R0: helix-team 97行 + team_runner.py 248行、teams/*.yaml テンプレート | 中 |
| REQ-F-042 | PR 自動生成: ゲート結果からプルリクエストテンプレートを自動生成 | R0: helix-pr 171行、gh CLI 依存 | 高 |
| REQ-F-043 | Builder System: テンプレートメソッドパターンで成果物生成を抽象化し、再現性と追跡性を確保 | R0: cli/lib/builders/ 14モジュール 2655行、R2: ADR-008 | 中 |
| REQ-F-044 | 要件トレーサビリティ: 要件 → 実装 → テストのマッピングを DB で管理 | R0: requirements + req_impl_map + req_test_map + req_changes テーブル | 中 |
| REQ-F-045 | JSON Schema バリデーション: phase.yaml/matrix.yaml/doc-map.yaml/gate-checks.yaml の構造検証 | R0: cli/schemas/ 5ファイル、R1: schema_validator.py | 高 |

---

## 3. 非機能要件仮説

### 3.1 性能/スケーラビリティ

| ID | 仮説要件 | 根拠 | 確信度 |
|----|---------|------|--------|
| NFR-001 | YAML 読み書きの排他制御: 並行プロセスによる phase.yaml 破損を防止 | R1: yaml_parser.py の write_yaml_safe（fcntl.LOCK_EX + atomic rename） | 高 |
| NFR-002 | SQLite WAL モードによる並行読み書き: ログ記録とレポート生成の並行実行を許容 | R0: helix_db.py（PRAGMA journal_mode=WAL, busy_timeout=5000） | 高 |
| NFR-003 | PostToolUse フックの低レイテンシ: ファイルハッシュベースキャッシュ（TTL 5秒）で繰り返し呼び出しを高速化 | R1: helix-hook の caching セクション（/tmp/helix-hook-cache/） | 高 |
| NFR-004 | コスト記録のバックグラウンド実行: Codex 実行のクリティカルパスにコスト記録を入れない | R1: helix-codex の side_effects（cost_log 記録がバックグラウンド） | 中 |
| NFR-005 | matrix compile の増分更新: auto-detect でファイル存在チェックのみの軽量更新と、compile でフルビルドを使い分け | R1: matrix_compiler の compile vs auto-detect | 中 |

### 3.2 セキュリティ

| ID | 仮説要件 | 根拠 | 確信度 |
|----|---------|------|--------|
| NFR-006 | ロール名インジェクション防止: ^[a-z0-9_-]+$ のバリデーションでコマンドインジェクションを防止 | R1: helix-codex の security セクション | 高 |
| NFR-007 | パストラバーサル防止: realpath + ensure_within_dir でスキルファイル読み込みのディレクトリ外アクセスを遮断 | R1: helix-codex の security セクション | 高 |
| NFR-008 | 秘密情報のリダクション: learning_engine.py が recipe 生成時に password/token/secret/bearer 等をマスク | R1: learning_engine の redaction_tokens 14パターン | 高 |
| NFR-009 | .gitignore による秘密情報保護: helix init 時に .env/.env.*/*.pem/*.key/credentials.json を自動追加 | R1: helix-init の side_effects（.gitignore 更新） | 高 |
| NFR-010 | 4 段階セキュリティゲート: G2（脅威分析）→ G4（OWASP）→ G6（最終セキュリティ）→ G7（デプロイ前）で段階的に検証 | R2: 5.3 セキュリティチェック | 高 |
| NFR-011 | テーブル名の SQL インジェクション防止: ^[A-Za-z_][A-Za-z0-9_]*$ でテーブル名をバリデーション | R1: helix_db の insert_row バリデーション | 高 |

### 3.3 拡張性

| ID | 仮説要件 | 根拠 | 確信度 |
|----|---------|------|--------|
| NFR-012 | スキルの追加容易性: SKILL.md を配置するだけで新しい専門知識を AI に付与可能 | R0: skills/ 55+ スキル、helix-codex のスキルオーバーレイ構造 | 高 |
| NFR-013 | ゲートチェックの宣言的定義: gate-checks.yaml に static/ai チェックを追加するだけでゲート強化可能 | R1: gate_checks_yaml のチェック構造（cmd + level） | 高 |
| NFR-014 | 駆動タイプの拡張性: config.yaml の default_drive + matrix の drive 定義で新しい駆動タイプに対応可能 | R1: ALLOWED_DRIVES 5種、matrix_compiler の駆動タイプ処理 | 中 |
| NFR-015 | ロールの追加容易性: roles/<name>.conf を追加するだけで新ロールを定義可能 | R0: cli/roles/ 12ファイル、R1: helix-codex の conf 読み込みロジック | 高 |
| NFR-016 | DB スキーマの進化: schema_version テーブル + migrate 関数でスキーマをバージョン管理 | R0: schema_version v1→v4、R1: helix_db の migrate 関数 | 高 |
| NFR-017 | テンプレートのバージョン管理: helix_template_version でテンプレートの互換性を管理 | R1: HELIX_TEMPLATE_VERSION = 3（matrix_compiler） | 中 |

### 3.4 保守性

| ID | 仮説要件 | 根拠 | 確信度 |
|----|---------|------|--------|
| NFR-018 | 外部依存の最小化: Python 標準ライブラリのみ使用（PyYAML/requests 等不要） | R2: ADR-001（yaml_parser.py 独自実装）、R0: external_apis（python3 標準ライブラリのみ） | 高 |
| NFR-019 | 自己テスト体系: 75 テスト（Python unit 43 + verify 32）+ helix-test 42 ケースでリグレッション防止 | R2: 5.1 テスト体系 | 高 |
| NFR-020 | 7 層検証（verify-all）: 構造・スキーマ・テスト・DB 整合性等を 1 コマンドで全層検証 | R0: helix-verify-all 194行 | 中 |
| NFR-021 | デバッグ支援: trace/inspect/replay/doctor の 4 モードで環境診断・フェーズ検査 | R0: helix-debug 387行 | 中 |
| NFR-022 | 日本語ファースト: 全出力・スキル・CLI は日本語標準 | R1: config.yaml の lang: ja、MEMORY.md の「日本語ファースト」 | 高 |

---

## 4. 設計意図仮説

### 4.1 なぜ Bash + Python か

**仮説**: 「透明性と安全性の二層分離」を意図した設計判断。

- **Bash 層（CLI コマンド 32本、約11,900行）**: ユーザー（= AI エージェント）に見える操作インターフェース。シェルスクリプトはパイプライン・exec・環境変数の操作が直感的で、AI にとっても理解しやすい。`helix gate G2` のようなコマンドは、AI がそのまま実行できる透明性がある
- **Python 層（lib 15本、約8,400行）**: 状態管理・DB・バリデーション・コンパイルなど、データ整合性が重要な処理。排他ロック（fcntl）、atomic rename、JSON Schema バリデーション、SQL パラメタライズドクエリなど、安全性が必要な処理を Python の型安全性とライブラリで実装

**代替案の推定と棄却理由**:
- 全て Python: CLI のオーケストレーション（exec 委譲、パイプ、環境変数）が冗長になる。AI エージェントが直接実行しにくい
- 全て Bash: SQLite 操作、YAML パース、JSON Schema バリデーションが困難。エラーハンドリングが脆弱になる
- Node.js / Go: 外部依存が増える。Python は Python 3.10+ が多くの環境で利用可能

### 4.2 なぜ SQLite + YAML の二重管理か

**仮説**: 「人間可読の状態 + 機械可読のログ」の用途分離を意図。

| 側面 | YAML（phase.yaml 等） | SQLite（helix.db） |
|------|-------------------|--------------------|
| 用途 | 現在の状態（フェーズ・ゲート・スプリント） | 履歴ログ（タスク実行・評価・フィードバック） |
| 読者 | 人間（エディタで直接確認）、AI（cat で読める） | 集計クエリ（SQL）、レポート出力 |
| 書き手 | 少数のコマンド（gate/sprint/size/mode） | ほぼ全コマンド（ログ記録） |
| サイズ | 小（数KB） | 大（成長し続ける） |
| 可搬性 | git 管理可能 | .gitignore 対象 |

- YAML は「今どこにいるか」を示すダッシュボード。人間が `cat .helix/phase.yaml` で即座に状態を確認できる
- SQLite は「何をしてきたか」を示す履歴。`helix log report quality` で集計し、recipe 生成の入力になる
- phase.yaml が git 管理対象なのは、プロジェクトの状態をチーム共有するため。helix.db はローカルのログなので git 管理対象外

### 4.3 なぜテンプレートコピー方式か

**仮説**: 「初期化の確定性 + プロジェクト別カスタマイズ」を両立する設計。

- `helix init` は `cli/templates/` から `.helix/` にファイルをコピーする（シンボリックリンクではない）
- コピー後はプロジェクト側で自由に編集可能（gate-checks.yaml のチェック追加、config.yaml の設定変更等）
- テンプレートのバージョン管理（helix_template_version）で、将来のテンプレート更新時にマイグレーション可能

**代替案の推定と棄却理由**:
- シンボリックリンク: プロジェクト別カスタマイズができない。フレームワーク更新時に全プロジェクトが一斉に影響を受ける
- 動的生成（on-the-fly）: 毎回生成するとゲートチェックの安定性が損なわれる。gate-checks.yaml の内容が実行のたびに変わると再現性がない
- オーバーライド方式（基底 + プロジェクト差分）: matrix_compiler が部分的にこの方式を採用しているが（rules/*.yaml から gate-checks.yaml を生成）、全面採用は複雑性が増す

### 4.4 なぜ 3 モード（Forward / Reverse / Scrum）か

**仮説**: 「ソフトウェア開発の 3 つの典型的な開始点」をそれぞれ専用のワークフローで支援する意図。

| モード | 開始点 | 典型シナリオ |
|--------|--------|-------------|
| **Forward** | 要件がある + コードがない | 新規開発、機能追加 |
| **Reverse** | コードがある + 設計書がない | レガシーシステムの引き継ぎ、技術負債の可視化 |
| **Scrum** | 仮説がある + 正解がわからない | PoC、技術選定、新しいアプローチの検証 |

- 3 モードは 1 つの `phase.yaml` で共存する（R2: ADR-007）。これは「プロジェクトのライフサイクルの中でモードを切り替える」ユースケースを想定している
  - 例: Reverse（R0→R4）で既存コードを理解 → Forward（L1→L8）で改善を実装
  - 例: Scrum で PoC → confirmed 仮説を Forward で本実装
- モード切替は `helix mode` で明示的に行うが、`helix reverse R0` / `helix scrum init` で自動切替もされる。これは「最初の操作で暗黙的にモードが決まる」直感的な UX を意図している

### 4.5 なぜ 12 ロールか

**仮説**: 「人間の開発チームの役割分担を忠実に再現し、単一 AI の万能利用を回避する」意図。

- 各ロールは異なるモデル（5.4/5.3/5.3-spark）と異なる思考レベル（xhigh/high/medium/low）を持つ。これは「タスクの性質に合ったモデルとコスト最適化」の両立を意図
- TL（設計・レビュー）と PG（実装）を分離することで、「実装者が自分の設計をレビューする」問題を構造的に防止
- Security ロールの独立は、セキュリティチェックを「他の作業の副次的チェック」ではなく「専任の責務」として扱うため
- 12 ロールの分化は、LLM の特性（広く浅い知識 vs 深い専門知識のトレードオフ）に対応する。スキル注入で専門知識を補完する

### 4.6 なぜ fail-close ゲートか

**仮説**: 「品質ゲートの形骸化防止」が最優先の設計意図。

- AI エージェントは人間と異なり「面倒だから省略する」動機を持たないが、「ゲートの意図を理解せず形式的に通過する」リスクがある
- fail-close（1 件の mandatory 失敗でゲート全体が FAIL）は、この「形式的通過」を物理的に不可能にする
- advisory レベルの存在は「完全な硬直化を避ける」安全弁。将来 mandatory に昇格させるかどうかを判断するための観察期間として機能
- ゲートの invalidation カスケード（G2 変更 → G3〜G7 自動無効化）は「上流の変更が下流の品質保証を無効にする」現実を反映。手動リセット（--undo）の存在は、誤った invalidation からの復帰手段

### 4.7 なぜ recipe + 昇格システムか

**仮説**: 「AI の実行経験を組織知として蓄積し、フレームワーク自体を進化させる」フィードバックループの意図。

```
実行 → ログ(SQLite) → 分析(learning_engine) → recipe(.helix/recipes/)
  → 検索(discover) → 再利用 → 評価 → 昇格(promote)
  → SKILL.md / verify スクリプト / タスク定義 として定着
```

- recipe はプロジェクトローカル（.helix/recipes/）とグローバル（~/.helix/global.db）の 2 層で管理。これは「プロジェクト固有の知見」と「汎用的なパターン」を区別する意図
- promote（昇格）は recipe を正式なフレームワーク成果物に変換する。これにより「良いパターンがフレームワークの一部になる」進化メカニズムを実現
- この仕組み全体は「AI が繰り返し同じ失敗をしない」ための学習基盤

---

## 5. PO 検証待ち項目

以下は R0〜R2 の実装証拠だけでは確認できず、プロダクトオーナー（PO）への確認が必要な項目。

### 5.1 ビジョン・戦略レベル

| # | 検証項目 | 仮説 | 確認理由 |
|---|---------|------|---------|
| PO-001 | HELIX の最終的な利用形態 | 個人開発者向けの OSS ツール | 商用製品/SaaS 化の意図があるか、チーム利用を想定しているかで、マルチテナント・認証・課金機能の要否が変わる |
| PO-002 | 対象ユーザーの AI リテラシー水準 | AI コーディングに習熟した開発者 | 初心者向けのガイド・チュートリアルの必要性を判断するため |
| PO-003 | 日本語ファーストの意図と国際化計画 | 日本の開発者が主ターゲット。config.yaml の lang: ja がデフォルト | 英語圏への展開計画があるか。あるなら i18n の優先度が上がる |
| PO-004 | Claude Code 専用か、他の AI コーディングツールも対象か | Claude Code + Codex CLI の 2 ツール専用 | 将来的に Cursor / Windsurf / Cline 等への対応を想定するかで、フック・プラグイン設計が変わる |

### 5.2 機能優先度レベル

| # | 検証項目 | 仮説 | 確認理由 |
|---|---------|------|---------|
| PO-005 | Builder System の本番利用状況 | 設計構想段階で、本格利用はまだ先 | R2: TD-007 で「未接続」と指摘。開発優先度と段階的統合計画の確認が必要 |
| PO-006 | fullstack 駆動タイプの Phase B（結合）の自動化優先度 | 手動運用でしのげている | R2: TD-008 で「自動化が薄い」と指摘。実際に fullstack 案件の頻度と痛みの大きさを確認 |
| PO-007 | RGC（Reverse Gap Closure）の実装計画 | CLI 未実装。手動実施 | MEMORY.md に「CLI 未実装」と明記。Reverse 利用頻度と RGC の手動運用コストを確認 |
| PO-008 | エージェントチーム実行（helix-team）の利用状況 | 実験的機能 | team_runner.py は 248 行と比較的小さい。実運用での利用頻度と課題を確認 |
| PO-009 | helix-interrupt（890行）の利用頻度と IIP/CC 分類の妥当性 | 割り込み管理は重要だが利用頻度は低い | R0: unknowns に「分類アルゴリズムの仕様文書なし」。実際の利用パターンを確認 |

### 5.3 品質・技術レベル

| # | 検証項目 | 仮説 | 確認理由 |
|---|---------|------|---------|
| PO-010 | テストカバレッジの目標水準 | 主要モジュールにユニットテストがあればよい | R2: TD-004 で matrix_compiler.py/deliverable_gate.py 等にユニットテストなし。テスト追加の優先度を判断 |
| PO-011 | PyYAML 完全排除の優先度 | 排除方針は維持するが 1 箇所の残存は許容 | R2: TD-001 で gate-checks.yaml パースに PyYAML 残存。完全排除のコストと便益を確認 |
| PO-012 | recipe 自動昇格の閾値基準 | 手動昇格（helix promote）のみ | R0: unknowns に「自動昇格の閾値が文書化されていない」。自動昇格の導入計画を確認 |
| PO-013 | SQLite FK 制約の enforce 方針 | アプリケーション層で保証（PRAGMA foreign_keys = ON は未設定） | R0: potential_risks に記載。FK enforce による既存データへの影響を確認 |

### 5.4 運用レベル

| # | 検証項目 | 仮説 | 確認理由 |
|---|---------|------|---------|
| PO-014 | helix.db のバックアップ・ローテーション方針 | 特に方針なし（ローカルログ） | DB が成長し続けるため、長期運用での容量と性能への影響を確認 |
| PO-015 | global.db の recipe 蓄積上限 | 上限なし | 大量の recipe が蓄積された場合の検索性能と管理方法を確認 |
| PO-016 | Codex CLI のバージョン固定方針 | 最新を追従 | Codex のバージョンアップによる breaking change への対応方針を確認 |
| PO-017 | HELIX 自体のバージョニングとリリース方針 | 特に定まっていない | helix_template_version = 3、schema_version = 4 はあるが、フレームワーク全体のバージョンがない |

---

## 付録: 証拠追跡マトリクス

| 要件 ID | R0 該当セクション | R1 該当セクション | R2 該当セクション |
|---------|-----------------|-----------------|-----------------|
| REQ-F-001〜004 | modules.cli_commands.helix-gate | cli_commands.helix-gate | ADR-003, 5.2 |
| REQ-F-005 | modules.cli_commands.helix-size | cli_commands.helix-size | 3.1 |
| REQ-F-006〜008 | modules.cli_commands.helix-sprint | cli_commands.helix-sprint | 3.1, 1.3 |
| REQ-F-009 | modules.cli_commands.helix-init | cli_commands.helix-init | 2.3 |
| REQ-F-010 | modules.cli_commands.helix-plan | -- | -- |
| REQ-F-011〜015 | modules.cli_commands.helix-codex | cli_commands.helix-codex | ADR-004 |
| REQ-F-016〜019 | modules.cli_commands.helix-task | cli_commands.helix-task | ADR-010 |
| REQ-F-020〜024 | modules.lib_modules.learning_engine | python_libraries.learning_engine | ADR-005 |
| REQ-F-025〜028 | modules.cli_commands.helix-reverse/scrum | cli_commands.helix-reverse/scrum | ADR-007, 1.3 |
| REQ-F-029〜032 | modules.cli_commands.helix-matrix/status | python_libraries.matrix_compiler | ADR-006 |
| REQ-F-033〜037 | modules.lib_modules.phase_guard/freeze_checker | hooks.PostToolUse/PreToolUse | ADR-009, 5.3 |
| REQ-F-038〜045 | modules.cli_commands (各種) | (各種) | (各種) |
| NFR-001〜005 | modules.lib_modules | python_libraries | -- |
| NFR-006〜011 | modules.lib_modules/cli_commands | cli_commands/python_libraries | 5.3 |
| NFR-012〜017 | config_files.templates/schemas/roles | templates | ADR-001,004,006 |
| NFR-018〜022 | external_apis | -- | 5.1, 6 |

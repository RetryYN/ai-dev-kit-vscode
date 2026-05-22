# HELIX コマンド索引

HELIX CLI は「全体管理」「プロジェクト管理」「AI 管理 harness」「Reverse / Scrum / 検証」「学習・再利用」「補助・運用」の 6 領域で使い分ける。

## 1. HELIX 全体管理

| コマンド | 役割 |
|---|---|
| `helix asset` | 画像 asset preset 生成 |
| `helix init` | `.helix/` とプロジェクト設定を初期化し、meta-phase pattern 契約テンプレートを配置 |
| `helix status` | 現在 phase / gate / next action を表示 |
| `helix dashboard` | 静的な読み取り専用 snapshot を表示（Dashboard 構想管理の対象外） |
| `helix mode` | forward / reverse / scrum の mode 切替 |
| `helix doctor` | 環境診断・修復 |
| `helix migrate` | `.helix/` テンプレート追従 |
| `helix db` | helix.db migration / rollback / dev-sandbox 試演 (PLAN-086) |
| `helix commands` | route / help / docs と主要 workflow 連携契約の同期検証 |
| `helix setup` | 初期化検証・修復コンポーネント |
| `helix test` | shell / pytest / bats のセルフテスト |
| `helix test-debug` | debug 有効のセルフテスト |
| `helix debug` | トレース等のデバッグ補助 |
| `helix bench` | プロジェクトメトリクス表示 |

## 2. HELIX プロジェクト管理

| コマンド | 役割 |
|---|---|
| `helix size` | size / drive / phase skip 判定 |
| `helix plan` | 設計計画 draft / review / finalize |
| `helix research` | L2 / L3 設計向けの調査テーマ生成と dry-run |
| `helix meta-phase` | PLAN-006 L1 メタ工程の pattern 契約検証 |
| `helix matrix` | 成果物対照表と gate-checks の生成 |
| `helix gate` | G0.5-G11 のゲート検証 |
| `helix gate-api-check` | D-API と実装 endpoint の整合検証 |
| `helix vmodel` | V-model semantics 表示・検証 (drive/layer/test/pair) |
| `helix readiness` | readiness exit と deferred finding 管理 |
| `helix sprint` | L4 マイクロスプリント |
| `helix task` | タスク OS |
| `helix interrupt` | IIP / CC の開始・適用・再開・履歴集計 |
| `helix handover` | Opus / Codex handover |
| `helix pr` | PR 自動生成 + 6 ゲート機械検証 (`--gate` / `--auto-merge`) |
| `helix retro` | ミニレトロ |
| `helix debt` | 技術負債管理 |
| `helix drift-check` | D-API / D-CONTRACT / D-DB drift 検知 |
| `helix bats-cleanup` | bats 由来 /tmp 残存 dir の監査・削除 (HELIX marker file 必須) |
| `helix push` | 6 ゲート機械検証 + git push 自動許可 (停滞防止) |

## 3. Codex / Claude Code 管理 harness

| コマンド | 役割 |
|---|---|
| `helix codex` | Codex CLI へ role/task 委譲 |
| `helix claude` | Claude Code 用 plan/task prompt 生成 |
| `helix team` | 複数 role のチーム委譲 |
| `helix review` | Codex レビュー |
| `helix skill` | スキル検索・参照 |
| `helix budget` | Claude/Codex の消費・モデル推奨 |
| `helix agent` | agent slot 一覧/release/stats/fire-mandatory/audit (PLAN-082) |
| `helix hook` | PostToolUse hook |
| `helix check-claudemd` | PreToolUse hook |
| `helix context` | AGENTS / CLAUDE / hook / memory の強制導線検査と context bundle 生成 |
| `helix session-start` | SessionStart hook |
| `helix session-summary` | Stop hook |

詳細: [ai-harness.md](ai-harness.md)

## 4. Reverse / Scrum / 検証

| コマンド | 役割 |
|---|---|
| `helix reverse` | 既存コード・設計資産から Reverse HELIX。詳細: [reverse.md](reverse.md) |
| `helix scrum` | 仮説検証、PoC、verify、Forward 接続。詳細: [scrum.md](scrum.md) |
| `helix verify-all` | verify/ 配下の全検証 |
| `helix verify-agent` | 検証ツール候補 harvest / design / drift cross-check |

## 5. 学習・再利用

| コマンド | 役割 |
|---|---|
| `helix log` | SQLite ログ・評価・session report |
| `helix recipe` | recipe learn / promote / discover / list の正規入口 |
| `helix learn` | 旧 recipe learn 入口 |
| `helix promote` | 旧 recipe promote 入口 |
| `helix discover` | 旧 recipe discover 入口 |
| `helix builder` | 成果物 builder |
| `helix code` | code index 検索・重複検出・統計 |
| `helix entry` | entries/links 中央 DB の CRUD + N 軸 coverage (PLAN-027) |
| `helix audit` | A1 audit decisions 同期・検証 |

## 6. 補助・運用

| コマンド | 役割 |
|---|---|
| `helix scheduler` | 定期実行スケジュール（run-due 時に stale running を自動復旧） |
| `helix job` | 非同期ジョブキュー（worker 起動時に stale running を自動復旧） |
| `helix lock` | DB lock 管理 |
| `helix observe` | イベント・メトリクス観測 |

## 7. プロダクト企画・イノベーション

| コマンド | 役割 |
|---|---|
| `helix innovation` | PdM Tech/Marketing 翻案 + 統合 + L1 接続 (G0.5 前後) |

## 典型導線

| やりたいこと | 最短導線 |
|---|---|
| 新規機能を正攻法で進める | `size` → `plan` → `matrix` → `gate` → `sprint` → `test` |
| Codex / Claude Code を管理して使う | `plan` / `task` → `codex` or `claude` → `review` → `handover` |
| AI 強制導線と memory の穴を確認する | `context check` → `context bundle` → `session-start` |
| 要件が曖昧なものを検証する | `scrum init` → `scrum backlog add` → `scrum poc` → `scrum verify` |
| 既存コードから設計を復元する | `reverse <type> R0` → `R1` → `R2` → `R3` → `R4` → `rgc` |
| 成功パターンを再利用する | `log` → `recipe learn` → `recipe promote` → `builder` |
| 状態を眺めて次を決める | `status` → `dashboard` → `readiness` → `debt` |

## 入口判定

| 状況 | 使う入口 |
|---|---|
| 要件・設計・契約が明確 | Forward HELIX (`size` → `plan` → `gate` → `sprint`) |
| 既存コードや設計資産を逆引きしたい | `reverse` |
| 要件や実現性が未確定 | `scrum` |
| 実装中に設計ギャップや要件変更が出た | `interrupt` |
| セッションや担当者をまたいで継続する | `handover` |

# HELIX (HELIX Engineering Lifecycle for AI eXecution)

AI 駆動開発フレームワーク。PM (Opus) が PMO (Sonnet/Haiku) / TL (GPT-5.5) / SE (GPT-5.4) / PE (Codex 5.3-spark/5.3) / 推挙 (GPT-5.4-mini) に分業委譲し、Forward (L1-L11) / Reverse (R0-R4) / Scrum (S0-S4) の各フローで開発を進める CLI ハーネスです。

## Quick Start

```bash
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git
cd ai-dev-kit-vscode
bash setup.sh
./cli/helix init
./cli/helix doctor
./cli/helix size --files 5 --lines 200
./cli/helix codex --role tl --task "PLAN-029 の設計を確認"
./cli/helix claude --role pmo --model sonnet --task "現状を要約" --execute
```

ホスト環境への導入は `setup.sh`、各プロジェクトへの HELIX 適用は `helix init`、テンプレ追従は `helix migrate` を使います。

## ロール × モデル (v2)

| ロール | 主モデル | 主責務 |
|---|---|---|
| PM | Opus | 要件、優先度、受入判断 |
| PMO | Sonnet / Haiku | 状況把握、軽作業、調査支援 |
| TL | GPT-5.5 | 設計、レビュー、ゲート判定 |
| SE | GPT-5.4 | 難易度の高い実装、契約判断、リファクタリング |
| PE | GPT-5.3-codex-spark / GPT-5.3-codex | 速度重視の実装、定型修正 |
| Recommender | GPT-5.4-mini | スキル推挙、軽量分類 |
| pdm-tech-innovation | Opus | 技術思想翻案、技術検討の早期提案 |
| pdm-marketing-innovation | Opus | 海外マーケ知見翻案と GTM 仮説 |
| pdm-innovation-manager | Opus | PdM 統合、意思決定、L1 接続 |

正本は `cli/config/models.yaml` と `cli/roles/*.conf` です。

## V2 Phase 2 拡張 (2026-05-15)

### V-model 強化

- `helix vmodel show <drive> <layer>`
- `helix gate --subgate functional_freeze --drive <DRIVE>`
- 詳細: [docs/operations/v2-operations-guide.md](docs/operations/v2-operations-guide.md)

### 停滞防止システム

- `helix push --gate` (6 ゲート機械検証 + auto-push)
- `helix pr --gate --auto-merge`
- 詳細: [docs/operations/stop-prevention.md](docs/operations/stop-prevention.md)

### PdM Innovation team

- `/innovation-tech`, `/innovation-marketing`, `/innovation-synthesize`
- 詳細: [docs/operations/pdm-innovation-workflow.md](docs/operations/pdm-innovation-workflow.md)

### PMO 9 ロール

- 詳細: [docs/operations/pmo-roster.md](docs/operations/pmo-roster.md)

## フロー概要

- Forward HELIX: `L1 -> L2 -> L3 -> L4 -> L5 -> L6 -> L7 -> L8 -> L9 -> L10 -> L11`
- Reverse HELIX: `R0 -> R1 -> R2 -> R3 -> R4 -> Forward -> RGC`
- Scrum HELIX: `S0 -> S1 -> S2 -> S3 -> S4`
- Gate: `G0.5/G1/G1.5/G1R/G2-G11` で設計、実装、検証、運用学習を fail-close 管理

## 主要ディレクトリ

- `cli/`: HELIX CLI、本体スクリプト、SQLite helper、テスト
- `skills/`: 100+ の HELIX スキルカタログと参照資料
- `docs/architecture/`: アーキテクチャ図、責務マップ、全体設計
- `docs/adr/`: Architecture Decision Records
- `docs/plans/`: PLAN-NNN 仕様書
- `docs/research/`: Web / GitHub / 先行事例の調査記録
- `docs/runbook/`: 障害対応、運用導線、復旧手順

## 主要コマンド

| コマンド | 用途 |
|---|---|
| `helix init` | プロジェクト初期化 |
| `helix doctor` | 環境整合チェック |
| `helix size` | タスクサイジング |
| `helix plan` | 設計計画の draft / review / finalize |
| `helix codex` | Codex 委譲 (TL / SE / PE / security / research など) |
| `helix claude` | Claude Code 委譲 (PMO Sonnet / Haiku) |
| `helix gate G1..G11` | フェーズゲート判定 |
| `helix sprint` | L4 マイクロスプリント管理 |
| `helix scrum` | 仮説検証フロー |
| `helix reverse R0-R4` | Reverse HELIX |
| `helix research --layer L1-L3` | レイヤ単位の調査起票 |
| `helix plan --mini` | mini-PLAN 作成 |
| `helix handover --mode` | PM <-> TL 引継ぎ |
| `helix code` | コードカタログ検索 |
| `helix skill` | スキル推挙、参照 |
| `helix budget` | モデルとコスト管理 |
| `helix test` | pytest / bats / shell テスト実行 |

全コマンドの索引は [docs/commands/index.md](docs/commands/index.md) を参照してください。

## 運用導線

### 1. ホストへ HELIX を導入

```bash
bash setup.sh
```

### 2. プロジェクトを HELIX 管理下に置く

```bash
helix init
helix doctor
```

### 3. タスクを設計し、実装へ委譲する

```bash
helix size --files 10 --lines 300 --api --drive be
helix plan draft --title "認証 API"
helix plan review --id PLAN-001
helix plan finalize --id PLAN-001
helix codex --role se --task "PLAN-001 の L4 実装" --approved
helix review --uncommitted
```

## ドキュメント

- [docs/plans/PLAN-028-helix-v2-orchestration.md](docs/plans/PLAN-028-helix-v2-orchestration.md): HELIX v2 orchestration
- [docs/plans/PLAN-029-helix-rigor-expansion.md](docs/plans/PLAN-029-helix-rigor-expansion.md): HELIX 11 軸厳格化拡張
- [docs/architecture/](docs/architecture/): 全体設計と責務整理
- [docs/adr/](docs/adr/): 設計判断記録
- [docs/runbook/README.md](docs/runbook/README.md): 運用 runbook 一覧

## 開発とテスト

```bash
python3 -m pip install --user -r requirements-dev.txt
python3 -m pytest cli/lib/tests/ -q --tb=short
./cli/helix test --no-pytest --bats-only
```

Codex / Claude Code の利用ルールは `AGENTS.md`、`CLAUDE.md`、`docs/commands/ai-harness.md` を正本とします。

## License

MIT

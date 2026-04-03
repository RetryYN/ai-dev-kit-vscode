# HELIX — AI エージェント制御開発システム

> 開発における OpenClaw。AI エージェントを効果的にシステマティックに制御する。

## 特徴

- **フェーズ制御**: L1-L8 + Phase Guard ですっ飛ばし防止
- **ゲート強制**: 成果物が揃わないと次に進めない
- **成果物駆動**: Deliverable Matrix で設計と実装を 1:1 対応
- **自己改善**: Learning Engine で成功/失敗パターンを蓄積・昇格
- **マルチモデル制御**: TL/SE/PG/FE の役割別委譲（thinking level 最適化）
- **5 駆動タイプ**: be/fe/db/fullstack/agent
- **55 スキル**: 開発・ライティング・デザイン・ブラウザ操作
- **8 ビルダー**: エージェント開発の検証済みパーツ
- **日本語ファースト**: 日本の開発水準底上げ

## セットアップ

```bash
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode
bash ~/ai-dev-kit-vscode/setup.sh
```

これだけで以下が自動設定される:

| 対象 | 処理 |
|------|------|
| 依存チェック | python3, bash 4+, git, sqlite3 CLI, codex CLI |
| Claude Code | `~/.claude/CLAUDE.md` に @import 追記 + `settings.json` に hooks マージ |
| Codex CLI | スキル symlink + `~/.codex/AGENTS.md` コピー（codex がある場合のみ） |

何度実行しても安全（冪等）。アンインストール: `bash ~/ai-dev-kit-vscode/setup.sh --uninstall`

## クイックスタート

```bash
# 1. プロジェクト初期化
helix init

# 2. タスクサイジング
helix size --files 10 --lines 300 --api --type new-feature --drive be

# 3. 成果物対照表の有効化
helix matrix init && helix matrix compile

# 4. 設計提案（TL レビュー付き）
helix plan draft --title "ユーザー認証 API"
helix plan review --id PLAN-001
helix plan finalize --id PLAN-001

# 5. 実装（Codex 委譲）
helix codex --role se --task "ユーザー認証の実装"

# 6. ゲート検証
helix gate G4

# 7. PR 作成
helix pr
```

## CLI コマンド一覧（26 本）

### 基本

| コマンド | 説明 |
|---------|------|
| `helix init` | プロジェクト初期化（.helix/ + CLAUDE.md） |
| `helix size` | タスクサイジング + フェーズスキップ判定 |
| `helix status` | プロジェクト状態表示（次アクションガイド付き） |
| `helix test` | 全ツールのセルフテスト |
| `helix verify-all` | verify/ の全検証スクリプト実行 |
| `helix debug` | デバッグユーティリティ |

### フェーズ管理

| コマンド | 説明 |
|---------|------|
| `helix gate <G2-G7>` | ゲート自動検証（deliverable + static + AI） |
| `helix sprint` | L4 マイクロスプリント管理（Twin Track 対応） |
| `helix plan` | 設計提案（draft → TL review → finalize） |
| `helix interrupt` | 追加設計モード（IIP/CC 自動分類） |
| `helix pr` | ゲート結果から PR 自動生成（リリースノート付き） |

### 成果物管理

| コマンド | 説明 |
|---------|------|
| `helix matrix` | 成果物対照表（init/compile/validate/status） |

### AI 委譲

| コマンド | 説明 |
|---------|------|
| `helix codex --role <role> --task "..."` | Codex ロール別委譲（12 ロール） |

--thinking オプション:

| ロール | デフォルト思考レベル |
|--------|-------------------|
| tl/security/legacy | xhigh |
| se/fe/qa/perf | high |
| pg/dba/devops | medium |
| docs/research | low |

### 学習・改善

| コマンド | 説明 |
|---------|------|
| `helix learn` | 成功パターンの分析・recipe 生成 |
| `helix promote` | recipe → スキル/スクリプトに昇格 |
| `helix discover` | グローバルからパターン検索 |

### ビルダー

| コマンド | 説明 |
|---------|------|
| `helix builder list` | 利用可能なビルダー一覧 |
| `helix builder <type> generate` | ビルダーでアーティファクト生成 |

8 種: json-converter, verify-script, agent-loop, task, workflow, agent-pipeline, agent-skill, sub-agent

### その他

| コマンド | 説明 |
|---------|------|
| `helix reverse <R0-R4>` | Reverse HELIX（既存コード→設計復元） |
| `helix scrum` | 検証駆動開発（PoC → verify） |
| `helix task` | タスクオペレーティングシステム |
| `helix log` | SQLite ログ・評価システム |

## スキル（55 本、9 カテゴリ）

| カテゴリ | スキル数 | 主な内容 |
|---------|---------|---------|
| workflow/ | 18 | プロジェクト管理・設計・検証・デプロイ |
| common/ | 12 | コーディング・レビュー・テスト・セキュリティ |
| project/ | 3 | UI・API・DB |
| advanced/ | 6 | 技術選定・i18n・レガシー・マイグレーション |
| tools/ | 2 | AI コーディング・IDE ツール |
| integration/ | 1 | エージェントチーム |
| writing/ | 5 | 日本語品質・ストーリー・プレゼン・SNS |
| design-tools/ | 5 | 図表・Web デザイン・PPTX・画像 |
| automation/ | 3 | サイトマッピング・ブラウザ操作・フロー最適化 |

## 駆動タイプ（5 種）

| タイプ | 起点 | 典型プロジェクト |
|-------|------|----------------|
| be | API/ロジック | 業務系、SaaS バックエンド |
| fe | デザイン/UX | LP、ダッシュボード |
| db | スキーマ/データ | マスタ管理、データ基盤 |
| fullstack | BE+FE 同時 | SaaS、EC、管理画面+API |
| agent | ツール/プロンプト | AI アプリ、自動化 |

## ガバナンス 4 層

1. **サンドボックス**: 実行環境分離（workspace-write / read-only）
2. **ガードレール**: Phase Guard + Deliverable Gate + Plan Review
3. **モニタリング**: Advisory Hook + Freeze-break 検知
4. **監査**: SQLite ログ + ミニレトロ + Learning Engine

## ADR（設計判断記録）

- ADR-001: Deliverable Matrix as Source of Truth
- ADR-002: Builder System Foundations
- ADR-003: Learning Engine

## ライセンス

MIT

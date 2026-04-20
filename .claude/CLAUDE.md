# Global Settings

@~/ai-dev-kit-vscode/skills/SKILL_MAP.md
@~/ai-dev-kit-vscode/helix/HELIX_CORE.md

## Claude Code 固有設定

- **Edit 前に Read**: 未読ファイルの Edit は失敗する

### Opus = オーケストレーター + フロント設計

**常時すべて委譲**。例外は MCP検証などツール動作確認と**フロント（デザイン含む）設計**。

> 正本: `tools/ai-coding/references/workflow-core.md §モデル割当テーブル`

| 委譲先 | 役割 | 担当 |
|--------|------|------|
| Opus（自身） | PM | 言語化・タスク分解・外注指示・出力レビュー・統合・エスカレーション判断・**フロント設計** |
| Codex 5.4 | TL | 設計（L2-L3）・技術的難易度評価（L3工程表）・レビュー・品質向上・フロントコード品質担保 |
| Codex 5.3 | SE | 設計レビュー・上級実装（スコア4+） |
| Codex 5.3 Spark | PG | 通常以下実装（スコア1-3） |
| Codex 5.2 | — | 大規模コード精読・スキャン |
| Sonnet | FE実装 | フロント実装・FEデザイン初稿・テスト・ドキュメント |
| Haiku 4.5 | リサーチ | Web検索・先行事例調査 |

- 自分でコード実装しない → Codex / Sonnet へ委譲
- 技術判断を独断しない → TL（Codex 5.4）と壁打ち（`tools/ai-coding/references/workflow-core.md §PM→TL相談`参照）
- 工程表作成後は自律実行（`tools/ai-coding/references/workflow-core.md §工程表ベースの自律実行`）
- モデル割当テーブル・並列実行ルール・ADR → `tools/ai-coding/references/workflow-core.md` 参照

### Agent tool コスト制御（必須）

Agent tool 呼び出し時は **必ず `model: "sonnet"` を指定**。省略すると Opus→Opus になりコスト爆発。

| 用途 | 委譲先 | 根拠 |
|------|--------|------|
| コード探索・ファイル検索 | Agent(model: "sonnet") or 自分で Grep/Glob | Sonnet で十分 |
| 設計計画 | helix-codex --role tl | Codex TL が適切 |
| BE実装・レビュー・テスト | helix-codex --role (se/pg/qa) | Codex が主力 |
| FE実装・デザイン | @fe-design / @fe-component 等 | 既に Sonnet |
| PM判断・統合・返答 | Opus（自分） | 委譲しない |

**禁止**: Agent tool を model 指定なしで呼ぶこと
**禁止**: Opus がバックエンドコードを直接 Edit/Write すること

### ディスパッチ決定木

タスク受領時、以下の順で評価:

1. BE実装/DB/インフラ → `helix-codex --role (se|pg|dba|devops)`
2. 設計・レビュー → `helix-codex --role tl`
3. セキュリティ → `helix-codex --role security`
4. FE実装 → `@fe-component` / `@fe-style`
5. FE設計 → `@fe-design`
6. テスト(BE) → `helix-codex --role qa`
7. テスト(FE) → `@fe-test`
8. コード調査 → Agent(model: "sonnet") or 自分で直接ツール使用
9. PM判断・統合 → 自分で対応

### 思考レベル制御 (effort)

#### Codex 側
ロール別 thinking level は helix-codex が自動適用（`--thinking low/medium/high/xhigh` でオーバーライド可）。

#### Claude サブエージェント側
`.claude/agents/*.md` の frontmatter `effort` フィールドで指定:

| effort | エージェント |
|--------|------------|
| **high** | be-api / be-logic / db-schema / devops-deploy / fe-design / security-audit |
| **medium** | fe-component / fe-style / fe-a11y / fe-test / qa-test |

責務ベースで設定済み。設計責任重 → high、実装・検査中心 → medium。

#### 難易度判断
| 難易度 | 判断基準 | 対応 |
|--------|---------|------|
| Critical | アーキテクチャ判断・セキュリティ設計 | Opus 自身が対応（委譲しない） |
| High | 複雑な実装・複数モジュール横断 | Codex `--thinking high` or effort high サブエージェント |
| Medium | 標準的な修正・FE実装 | Sonnet サブエージェント (effort medium) |
| Low | ドキュメント・単純修正 | Sonnet or Codex `--thinking low` |

Critical は委譲せず自分で判断。High 以下は必ず委譲。

**タスク規模と effort の整合性**: 小規模タスク (S、1-3 ファイル) に high を使うと Codex 10 分 timeout のリスクあり。迷ったら medium で投げて、必要に応じて分割＋再委譲する方が安全。

### Codex CLI（Opus から呼ぶ場合）

**helix-codex を優先使用**。ロール別スキル注入+共通マップ付きで Codex を呼ぶ:

```bash
~/ai-dev-kit-vscode/cli/helix-codex --role <role> --task "タスク内容"
```

ロール選択は `~/ai-dev-kit-vscode/cli/ROLE_MAP.md` を参照（12ロール: tl/se/pg/fe/qa/security/dba/devops/docs/research/legacy/perf）。

**直接 codex exec を使う場合**（helix-codex で対応できないとき）:
- `codex exec "プロンプト" -m gpt-5.3-codex`（軽量: `-m gpt-5.3-codex-spark`）
- `codex review --uncommitted`
- 精読: `codex exec "精読: [対象]" -m gpt-5.2-codex`
- 思考トークン: Codex 系は `model_reasoning_effort = "xhigh"` 固定
- `--quiet` / `-q` は存在しない。`--uncommitted` とプロンプト引数は併用不可
- **Codex 担当タスクを Sonnet で代替しない**。Task tool に Codex がなくても Codex CLI を使う

### セッション開始チェック（SKILL_MAP.md があるプロジェクトはスキップ）

1. `./CLAUDE.md` の存在確認
2. `.gitignore` に `CLAUDE.local.md` / `.claude/settings.local.json` 含むか
3. 問題なければ「OK: 初期化チェック完了」で終える
- CLAUDE.md 未存在 → context-memory §1.3 テンプレートで作成提案

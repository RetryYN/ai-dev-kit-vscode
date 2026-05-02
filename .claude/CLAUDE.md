# Global Settings

@~/ai-dev-kit-vscode/skills/SKILL_MAP.md
@~/ai-dev-kit-vscode/helix/HELIX_CORE.md

## Claude Code 固有設定

- **Edit 前に Read**: 未読ファイルの Edit は失敗する

### Opus = オーケストレーター + フロント設計

**常時すべて委譲**。例外は MCP検証などツール動作確認と**フロント（デザイン含む）設計**。

> 正本: `skills/tools/ai-coding/references/workflow-core.md §モデル割当テーブル`

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
- 技術判断を独断しない → TL（Codex 5.4）と壁打ち（`skills/tools/ai-coding/references/workflow-core.md §PM→TL相談`参照）
- 工程表作成後は自律実行（`skills/tools/ai-coding/references/workflow-core.md §工程表ベースの自律実行`）
- モデル割当テーブル・並列実行ルール・ADR → `skills/tools/ai-coding/references/workflow-core.md` 参照

### 並列実行ルール（必須）

依存関係がないタスクは **必ず並列** で投入。直列にしない。

判定（1 つでも該当 → 直列、全て NO → 並列）:
- 編集対象ファイルが衝突する
- 後段が前段の出力 (成果物 / レビュー結果) を入力にする
- 共有状態 (helix.db / phase.yaml / handover の同フィールド) を同時更新する

実装:
- 同一メッセージで複数の Bash/Agent 呼び出し (`run_in_background: true` を活用)
- 完了通知が来た順にレビュー → コミット。一斉待ち合わせ不要
- どちらが先に終わってもよい場合は独立に進行・独立にコミット
- 並列投入前に「衝突するファイル」「後段依存」を 1 行で書き出して根拠を残す

例: BE 実装 (Codex SE) ∥ FE 実装 (@fe-component) ∥ docs 起草 (Codex docs) / 異なる Sprint で独立ファイル群を編集する Codex 同時投入 / 完了済み Sprint の commit と次 Sprint の委譲を並走

**禁止**: 依存関係がないのに「念のため」「順番にやれば確実」を理由に直列化すること

### Agent tool コスト制御（必須）

Agent tool 呼び出し時は **必ず `model: "sonnet"` を指定**。省略すると Opus→Opus になりコスト爆発。

| 用途 | 委譲先 | 根拠 |
|------|--------|------|
| コード探索 (1 回の Grep/Glob/Read で完結) | 自分で直接 (Bash/Read) | オーバーヘッド回避 |
| コード探索 (2 ステップ以上、複数ファイル横断) | Agent(model: "sonnet", subagent_type: "Explore") | Opus context 保護 |
| 長文 Read (≥100 行 / review.json / PLAN.md 全体) | Agent(model: "sonnet") + 要約受領 | Opus トークン削減 |
| 設計計画 | helix-codex --role tl | Codex TL が適切 |
| BE実装・レビュー・テスト | helix-codex --role (se/pg/qa) | Codex が主力 |
| FE実装・デザイン | @fe-design / @fe-component 等 | 既に Sonnet |
| PM判断・統合・返答 | Opus（自分） | 委譲しない |
| ドキュメント本文起草 (>100 行) | helix-codex --role docs | PM は要件提示と finalize のみ |

#### 委譲必須の判定基準（厳格化、2026-05-03 改訂）

以下のいずれかに該当 → **Opus 自身でやらず Sonnet/Codex 委譲を必須化**:

- 同一タスクで Read 合計が 200 行を超える見込み
- Grep / Glob が 3 回以上必要
- 同じファイルを複数視点で見る (構造把握 + 詳細確認 等)
- 長文ドキュメント (PLAN.md / review.json / SKILL.md / CURRENT.md) の全体 Read

**Opus が直接 Read してよい範囲**:
- handover status / phase.yaml / 単発短ファイル (< 100 行)
- Edit 直前の対象ファイル冒頭〜該当箇所のみ
- ユーザーから明示指定された 1 ファイル

**禁止**: Agent tool を model 指定なしで呼ぶこと
**禁止**: Opus がバックエンドコードを直接 Edit/Write すること
**禁止**: Opus が「自分でやった方が早い」を理由に委譲基準を超えた直接実行をすること

#### Budget 可視化（Opus 残使用量の把握）

セッション開始時 / 委譲判断に迷ったら以下で残使用量を確認:

```bash
helix budget status              # Claude/Codex 両側の消費 % と枯渇予測
helix budget simulate --task "..." [--size M]  # classify + budget で最適モデル + thinking 提示
```

Opus 週間残量が少ない時は委譲を強化（探索・長文 Read を 100% Sonnet 委譲）。Codex 残量も合わせて確認。新タスク着手前に `helix budget simulate` で最適委譲先を機械判定するのが推奨運用。

### ディスパッチ決定木

タスク受領時、以下の順で評価:

1. BE実装/DB/インフラ → `helix-codex --role (se|pg|dba|devops)`
2. 設計・レビュー → `helix-codex --role tl`
3. セキュリティ → `helix-codex --role security`
4. FE実装 → `@fe-component` / `@fe-style`
5. FE設計 → `@fe-design`
6. テスト(BE) → `helix-codex --role qa`
7. テスト(FE) → `@fe-test`
8a. コード調査（単発・< 100 行 Read 1 回 / Grep 1 回で完結）→ 自分で直接ツール使用
8b. コード調査（複数ステップ・複数ファイル横断・長文 Read）→ Agent(model: "sonnet", subagent_type: "Explore")
8c. ドキュメント長文解析（PLAN/review.json 全体）→ Agent(model: "sonnet") で要約受領
8d. ドキュメント本文起草（PLAN/SKILL.md > 100 行）→ `helix-codex --role docs`
9. PM判断・統合・finalize 判断 → 自分で対応

### 思考レベル制御 (effort)

#### Codex 側
ロール別 thinking level は helix-codex が自動適用（`--thinking low/medium/high/xhigh` でオーバーライド可）。

#### Claude サブエージェント側
`.claude/agents/*.md` の frontmatter `effort` フィールドで指定:

| effort | エージェント |
|--------|------------|
| **high** | be-api / be-logic / code-reviewer / db-schema / devops-deploy / fe-design / security-audit |
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

### BE 実装時の Handover ファイル維持

Claude Code セッション上限対策。BE 実装中または切れが近いときに `.helix/handover/CURRENT.json` を維持し、
ユーザーが Codex CLI チャットで「続き」と言うだけで BE 実装を継続できる状態を保つ。

**いつ使うか**:
- L4 で BE 実装に入るとき (dump)
- BE 実装中の区切り (update)
- セッション切れが近いと感じたとき (update --owner codex)
- FE 設計 / PM 判断 / 契約変更時は使わない (BE 実装スコープのみ)

**運用フロー**:
1. 初期化:
   ```
   helix handover dump --task-id <ID> --task-title "..." \
     --files "path1,path2" --tests "pytest tests/..." \
     --next "1. ... 2. ... 3. ..."
   ```
2. 実装の区切りごとに更新:
   - ファイル完成: `helix handover update --complete <path> --complete-note "..."`
   - 詰まったとき: `helix handover update --blocker "..."`
   - 解決時: `helix handover update --unblock "..."`
   - 文脈メモ: `helix handover update --note "..."`
3. Codex に引き渡す直前:
   `helix handover update --owner codex --note "Opus セッション終了、Codex に継続依頼"`

**完了時** (Codex が `ready_for_review` に遷移して戻してきたら):
- Opus セッションで内容レビュー
- 問題なければ `helix handover clear --reason completed`
- 修正必要なら `helix handover update --status in_progress --owner opus`

**Codex → Opus 復帰** (Codex セッションから Opus が作業を引き継ぐとき):
- `helix handover resume [--note "..."]` を実行
- `.helix/handover/RESUME.md` が生成される (base↔current HEAD の diff stat + 変更ファイル + Opus 向けレビューチェックリスト)
- owner=opus, status=in_progress に自動遷移 (ready_for_review / blocked / in_progress から許可)
- RESUME.md のチェックリストに沿って diff をレビュー → 完了なら `helix handover clear --reason completed`

**Codex からエスカレーションされたとき** (`.helix/handover/ESCALATION.md` がある):
- ESCALATION.md を Read して判断
- 必要なら設計・契約を更新
- 再開するなら `helix handover update --status in_progress --owner opus` して Next Action を書き直す
- 放棄するなら `helix handover clear --reason abandoned --force`

### セッション開始チェック（SKILL_MAP.md があるプロジェクトはスキップ）

1. `./CLAUDE.md` の存在確認
2. `.gitignore` に `CLAUDE.local.md` / `.claude/settings.local.json` 含むか
3. `.helix/handover/ESCALATION.md` が存在するか (あれば Read して状況把握)
4. 問題なければ「OK: 初期化チェック完了」で終える
- CLAUDE.md 未存在 → context-memory §1.3 テンプレートで作成提案

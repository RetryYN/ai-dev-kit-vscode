<!-- helix_template_version: 4 -->
# HELIX

@./skills/SKILL_MAP.md
@./helix/HELIX_CORE.md
@./helix/CODEX_TL_MODE.md

## 概要
HELIX は、AI エージェントを `plan` / `task` / `role` / `gate` / `handover` で制御する開発フロー・CLI・スキル群のリポジトリ。

## 技術スタック
- Frontend: なし。CLI とドキュメント中心
- Backend: Bash CLI + Python helper modules
- DB: SQLite (`.helix/helix.db` などの project-local runtime state)
- インフラ: Git hooks、Claude Code hooks、Codex CLI、Bats、pytest

## アーキテクチャ
- `cli/`: `helix` ルーターとサブコマンド実装
- `cli/lib/`: Python helper、SQLite access、learning / routing utilities
- `cli/templates/`: `helix init` が配布する project template
- `helix/`: HELIX core policy、Codex TL mode、ユーザー向け設定例
- `skills/`: HELIX skill と skill map
- `docs/commands/`: CLI 利用導線の正本
- `.claude/`: Claude Code hook / command / agent runtime 設定
- 詳細レイアウトマップ: [docs/architecture/cli-layout.md](docs/architecture/cli-layout.md)

## コーディング規約
- 既存 CLI の Bash/Python 分担に合わせる。単純な CLI glue は Bash、状態集計や構造化処理は Python helper に寄せる。
- 実装前に対象ファイルを Read して、既存パターンへ合わせる。
- 変更範囲は要件に必要なファイルへ限定する。runtime state やユーザー未コミット変更を巻き戻さない。
- Codex / Claude Code は API 直叩きではなく、契約プラン + CLI / hook を HELIX が管理する前提で扱う。
- テストなしの完了宣言は禁止。Bash 変更は `bash -n`、Python 変更は `python3 -m py_compile`、CLI 変更は Bats / pytest を必要範囲で実行する。

## コミット規約
- 1 commit = 1 PLAN または 1 トピック。独立した責務 (例: 機械的 refactor + 新規ドキュメント追加 + 表記統一) を 1 commit に混ぜない。
- 大型 commit (>30 ファイル または +1500 行) は責務単位で分割する。分割を躊躇するときは、commit メッセージ body に「なぜ 1 commit にまとめたか」を明記する。
- `scope` はドメイン名 (例: `session-summary`, `code-catalog`, `helix-codex`) を 1 つに絞る。複数ファイル名のカンマ列挙 (`scope1,scope2`) は禁止。複数モジュールに跨る変更は本文 body に列記する。
- prefix は `feat / fix / chore / docs / test / refactor`。コード変更を伴わない PLAN ドキュメント更新は `docs(plan-NNN):` を使う。
- 自動生成物 (Stop hook によるセッション記録、Codex agent local state など) は手動 commit に取り込まない。`.gitignore` で除外するか、`git add` で対象を明示する。

## ディレクトリ構造
```text
cli/
  helix
  helix-*
  lib/
  tests/
docs/
  commands/
helix/
skills/
.claude/
```

## コマンド
- CLI help: `cli/helix help`
- 全体テスト: `cli/helix test`
- shell 回帰: `cli/helix test --no-pytest --bats-only`
- Python 回帰: `python3 -m pytest cli/lib/tests/ -q --tb=short`
- Claude Code prompt 生成: `cli/helix claude --role <role> --task "..." --dry-run`
- Codex 委譲: `helix codex --role <role> --task "..."`

## 禁止事項
- API key、secret、PII、credential を `CLAUDE.md` / `AGENTS.md` / skill / docs に書かない。
- 認証、認可、決済、PII、ライセンス、本番影響、destructive data operation は人間確認なしに仕様確定しない。
- 外部 provider SDK や認証情報を前提にした fallback を HELIX の通常導線として追加しない。
- `.helix/` runtime state、`.claude/settings.local.json`、`.codex` などのローカル副産物をドキュメント目的で追跡対象にしない。

## HELIX ワークフロー
- タスク受領時は `helix/HELIX_CORE.md`、`skills/SKILL_MAP.md`、`helix/CODEX_TL_MODE.md` を確認する。
- `.helix/handover/CURRENT.json` がある場合は `helix handover status --json` を確認し、stale でなければ Next Action に従う。
- Forward: `size` -> `plan` -> `matrix` -> `gate` -> `sprint` -> `test`
- Reverse: `reverse <type> R0` -> `R1` -> `R2` -> `R3` -> `R4` -> `rgc`
- Scrum: `scrum init` -> `backlog` -> `plan` -> `poc` -> `verify` -> `decide`
- AI harness: `plan` / `task` の文脈を `codex` / `claude` / `team` / `review` / `handover` で管理する。

詳細は [docs/commands/index.md](docs/commands/index.md) と [docs/commands/ai-harness.md](docs/commands/ai-harness.md) を参照。

## Codex との対応
Codex CLI 向けの正本は [AGENTS.md](AGENTS.md)。プロジェクト知識はこの `CLAUDE.md` と揃え、Codex 固有の TL 動作・検証・handover ルールは `AGENTS.md` に寄せる。

## モデル割当（真実は `cli/config/models.yaml`）

| 委譲先 | ロール | 主な担当 |
|--------|------|---------|
| Opus (自身) | PM | チャットのみ。言語化・タスク分解・統合・エスカレーション判断。コード編集禁止 |
| Codex 5.5 | TL | 設計・技術判断・レビュー・高度実装・検証 |
| Codex 5.3-codex-spark | PE | 単機能実装・速度重視実装 |
| Codex 5.4 | SE | 契約・複雑実装・リファクタリング |
| Codex 5.3 | Security / DBA / DevOps / Perf | セキュリティ監査・DB・インフラ・性能 |
| Codex 5.4-mini | Recommender / Classifier | スキル推挙・タスク分類 |
| Sonnet | PMO（判断伴う） | 構造化チェック、ドキュメント状況把握（read-only） |
| Haiku 4.5 | PMO（軽作業） | Web 検索・`docs/**` 限定軽作業（read-write） |

- ドキュメントと実装が乖離した場合は **実装 (`cli/config/models.yaml`) を正** とする。本表は周知用。
- ロール定義の正本は [cli/ROLE_MAP.md](cli/ROLE_MAP.md)。

## Agent tool 完全禁止（v2）

特定指定付きの Agent tool 呼び出しを含む実行は原則禁止。PMO の read-only・軽作業は `helix claude --role pmo --execute` 経由に統一する。

実行例:

```bash
helix claude --role pmo --model sonnet --task "docs チェック" --execute
helix claude --role pmo --model haiku --task "docs minor fix" --execute
```

- 委譲必須の判定基準:
  - 同一タスクで Read 合計が 200 行を超える見込み
  - Grep / Glob が 3 回以上必要
  - 同じファイルを複数視点で見る
  - 長文ドキュメント (PLAN.md / review.json / SKILL.md / CURRENT.md) の全体 Read
- Opus 直接 Read してよい範囲: handover status / phase.yaml / 単発短ファイル (< 100 行) / Edit 直前の対象箇所 / ユーザー明示指定の 1 ファイル
- **禁止**: Agent tool を model 指定なしで呼ぶ / Opus がバックエンドコードを直接 Edit/Write する / 「自分でやった方が早い」を理由に委譲基準を超える

## 並列実行ルール（必須）

依存関係がないタスクは **必ず並列** で投入。直列にしない。

判定（1 つでも該当 → 直列、全て NO → 並列）:
- 編集対象ファイルが衝突する
- 後段が前段の出力を入力にする
- 共有状態 (helix.db / phase.yaml / handover の同フィールド) を同時更新する

並列投入前に「衝突するファイル」「後段依存」を 1 行で書き出して根拠を残す。

## タスク受領時の skill 推挙呼び出し (必須)

新規タスク受領時、実装着手前に必ず以下を実行する:

1. `helix skill chain "<タスク記述>"` を呼び、上位スキルと推奨 agent を確認する
2. 推挙された skill / agent に従って委譲先を決定し、Opus 自身が直接実装しない原則を優先する
3. skip する場合は、自明な小修正または既知 skill のみ使用である理由を会話または final report に記録する

これは PLAN-022 で確立されたランタイム原則である。skill 推挙は gpt-5.4-mini 経由で 1 時間キャッシュされるため、コスト負担はほぼない。

## 委譲 Codex のコミット禁止

`helix codex` / `codex exec` で呼ぶ **委譲 Codex** は `git add` / `git commit` / `git push` を一切しない。Opus (PM) が成果物検証後に commit する。チャット (TL モード) Codex は対象外。

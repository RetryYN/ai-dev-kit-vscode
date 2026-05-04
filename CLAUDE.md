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

## コーディング規約
- 既存 CLI の Bash/Python 分担に合わせる。単純な CLI glue は Bash、状態集計や構造化処理は Python helper に寄せる。
- 実装前に対象ファイルを Read して、既存パターンへ合わせる。
- 変更範囲は要件に必要なファイルへ限定する。runtime state やユーザー未コミット変更を巻き戻さない。
- Codex / Claude Code は API 直叩きではなく、契約プラン + CLI / hook を HELIX が管理する前提で扱う。
- テストなしの完了宣言は禁止。Bash 変更は `bash -n`、Python 変更は `python3 -m py_compile`、CLI 変更は Bats / pytest を必要範囲で実行する。

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

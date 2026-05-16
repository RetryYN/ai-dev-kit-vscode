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
| Sonnet | PMO（判断伴う） | 構造化チェック、ドキュメント状況把握（read-only）。`.claude/agents/pmo-sonnet` (sonnet) 経由 |
| Haiku 4.5 | PMO（軽作業） | Web 検索・`docs/**` 限定軽作業（read-write）。`.claude/agents/pmo-haiku` (haiku) 経由 |

- ドキュメントと実装が乖離した場合は **実装 (`cli/config/models.yaml`) を正** とする。本表は周知用。
- ロール定義の正本は [cli/ROLE_MAP.md](cli/ROLE_MAP.md)。

## Advisor 召喚ルール（運用）

チャット PM (Opus / Sonnet いずれも) と実装担当が **大局判断 / 技術選択で迷ったとき** は、自前で結論を出す前にアドバイザーを召喚する。最終判断は呼び出し側 (PM またはユーザー) が下す。

| アドバイザー | model | 召喚コマンド | 召喚タイミング |
|---|---|---|---|
| **pm-advisor** | claude-opus-4-7 (read-only) | `helix claude --role pm-advisor --execute --task "..."` | スコープ / 優先度 / 大局リスク / HELIX フェーズ整合 / 委譲先選択 で迷う |
| **tl-advisor** | gpt-5.5 high (read-only) | `helix codex --role tl-advisor --task "..."` | 設計選択 / 契約・API 妥当性 / テスト戦略 / リファクタ判断 で迷う |

運用原則:
- **PM が Sonnet で動いているチャット** では、難判断に当たったら必ず pm-advisor (Opus) に相談する。Sonnet 単独で大局判断を確定させない
- **PM が Opus でも**、自分の判断に確信が持てない技術判断は tl-advisor を呼んで反論を取る (adversarial check)
- 実装担当 (Sonnet / Codex) は契約や設計で迷ったら tl-advisor、スコープで迷ったら pm-advisor を呼ぶ
- アドバイザーは read-only。コード編集や状態変更は行わない (構造化助言のみ返す)
- 呼び出した task / 助言内容は会話または final report に残し、判断トレースを失わない

## Agent tool は PMO + PdM 限定許可（v2.2、2026-05-15 改訂）

PMO subagent (`pmo-sonnet` / `pmo-haiku`) と PdM subagent (`pdm-tech-innovation` / `pdm-marketing-innovation` / `pdm-innovation-manager`) のみ許可。
それ以外の subagent (`be-api` / `be-logic` / `db-schema` / `qa-test` / `security-audit` / `code-reviewer` / `devops-deploy`) は引き続き禁止する。Codex 委譲または Opus 直接で対応する。

判定:
- PMO subagent OK: `Agent({ subagent_type: "pmo-sonnet", ... })` または `pmo-haiku`
- 他 subagent 禁止: 過去 v2 規約継続。Codex / Opus 直接で対応
- 判断基準は変更なし: 同一タスク Read 200+ 行 / Grep 3+ / 複数視点 / 長文 doc 全体 Read で委譲必須

| 活用領域 | Agent | 補足 |
|---|---|---|
| HELIX 内目星付け (skills/templates/cli 軽量検索) | Agent({subagent_type: "pmo-helix-scout"}) | 候補列挙 |
| project 内目星付け (code/docs 軽量検索) | Agent({subagent_type: "pmo-project-scout"}) | 候補列挙 |
| 海外技術思想翻案 (G0.5 前後) | Agent({subagent_type: "pdm-tech-innovation"}) | 翻案 |
| 海外マーケ思想翻案 (G0.5 前後) | Agent({subagent_type: "pdm-marketing-innovation"}) | 翻案 |
| PdM 統合・新方向性策定 (L1 接続) | Agent({subagent_type: "pdm-innovation-manager"}) | 統合判断 |
| OSS/plugin 探索・転用判断 | Agent({subagent_type: "pmo-tech-fork"}) | 外部 GitHub 探索 |
| 設計手法/概念の外部精読 | Agent({subagent_type: "pmo-tech-docs"}) | 外部 doc 精読 |
| 最新 Tech 動向 sweep (週次想定) | Agent({subagent_type: "pmo-tech-news"}) | 時事収集 |
| HELIX framework 内資産探索 (skills/templates/cli/docs) | Agent({subagent_type: "pmo-helix-explorer"}) | 詳細探索 |
| 現在 project 内資産探索 (code/docs/config) | Agent({subagent_type: "pmo-project-explorer"}) | 設計整合 |

PMO subagent (pmo-sonnet / pmo-haiku) の使い分け:
- pmo-sonnet: 判断伴う read-only / docs/PLAN 構造化チェック / 長文解析
- pmo-haiku: Web 検索目星付け（初期 sweep） / docs/** 軽修正 / コスト重視軽作業

helix-claude --role pmo は deprecated。新規呼び出しは `Agent({subagent_type: "pmo-sonnet"})` または `Agent({subagent_type: "pmo-haiku"})` 推奨。既存 dispatch は段階的に移行。

委譲必須の判定基準 (変更なし):
- 同一タスクで Read 合計が 200 行を超える見込み
- Grep / Glob が 3 回以上必要
- 同じファイルを複数視点で見る
- 長文ドキュメント (PLAN.md / review.json / SKILL.md / CURRENT.md) の全体 Read

Opus 直接 Read してよい範囲:
- handover status / phase.yaml / 単発短ファイル (< 100 行)
- Edit 直前の対象箇所
- ユーザー明示指定の 1 ファイル

**禁止**: PMO 以外の subagent 呼び出し / Opus がバックエンドコード直接 Edit / 「自分でやった方が早い」を理由とする委譲基準超え

## 並列実行ルール（必須、default 上限 8 並列）

依存関係がないタスクは **必ず並列** で投入。直列にしない。**default 上限 = 8 並列**、これを下回る運用 (1-2 並列で済ます) は怠慢として禁止する。

判定（1 つでも該当 → 直列、全て NO → 並列）:
- 編集対象ファイルが衝突する
- 後段が前段の出力を入力にする
- 共有状態 (helix.db / phase.yaml / handover の同フィールド) を同時更新する

並列投入前に「衝突するファイル」「後段依存」を 1 行で書き出して根拠を残す。

### 8 並列達成のための構成パターン
- **Codex 委譲 N 並列 + Opus 軽量タスク並行**: ファイル衝突しない範囲で最大化
- **subagent (pmo-sonnet) + Codex pg/se 同時投入**: pmo は read-only/docs、Codex は code 実装
- **前段 task 走行中の独立 followup 並走**: TL spine 凍結待ち / E2E test 待ち中でも独立タスクは並走
- **prompt 作成は Write 並列で先行**: Codex 投入の事前に N 個の prompt file を並列 Write、その後一括投入

8 並列に達しないとき、必ず「依存判定で何件直列必須か」「8 まで埋められない理由」を会話に書き出す。出さずに 1-2 並列で済ませるのは禁止。

## V-model 設計⇔テスト対応原則 (2026-05-17 確立、PLAN-075)

設計とテスト設計は **同じ文書に書く** (V-model 1:1 対応)。テスト設計を独立ドキュメント化することは V-model 違反。

| HELIX 層 | 設計成果物 | 含むべきテスト設計 |
|---|---|---|
| L1 要件定義 | 要件 / 受入条件 | **受入テスト設計** |
| L2 全体設計 | CONCEPT / ADR / visual-design | **総合テスト設計 (E2E / システム)** |
| L3 詳細設計 | D-API / D-DB / D-CONTRACT | **結合テスト設計** |
| L3-L4 機能設計 | endpoint / 関数 input/output schema、境界値 | **単体テスト設計** |

詳細: `helix/HELIX_CORE.md §設計⇔テスト対応`。

**禁止**: 単体テスト設計を独立ドキュメント (`docs/v2/L4-test-design/PLAN-XXX-unit-test-design.md`) に切り出すこと

## subagent 工程マッピング (2026-05-17、PLAN-076)

subagent 14 種を 2 分類:

- **mandatory by phase (10 種)**: pdm-* / pmo-tech-fork/docs/explorer/scout/sonnet。工程で必須、`helix agent fire-mandatory --phase Lx` で一括投入、helix.db で audit、G2-G4 で lint
- **on-demand by judgment (4 種)**: pmo-haiku / pmo-tech-news / pm-advisor / tl-advisor。判断に応じて任意、`helix agent suggest`

詳細: `helix/HELIX_CORE.md §工程別 subagent 起動マップ`。

## Sprint Plan 標準構造 (2026-05-17、PLAN-077)

L4 実装中の Sprint Plan は標準 8 ステップに固定化:

- Step 1-3: Entry / 着手前調査 / 実装
- **Step 4-6 (mandatory in sprint)**: 機械チェック (py_compile / lint) + テスト起動 (該当 test / 全回帰) + レビュー (セルフ / pmo-sonnet)
- Step 7-8: commit + Exit 条件確認

Sprint Exit 前に mandatory 全通過必須、`helix sprint complete --auto-check` で機械化。詳細: `helix/HELIX_CORE.md §Sprint Plan 標準構造`。

## ScheduleWakeup 運用ルール (task-notification 信用、2026-05-16 確立)

`Bash(run_in_background: true)` で投入した command は **harness が完了時に task-notification を自動送信** する。ScheduleWakeup を併用するな:

- `run_in_background: true` の結果待ち → **ScheduleWakeup 不要**。task-notification 自動通知を信用して他の作業を進める
- 並行タスクが無くなったら turn を終え、harness が完了通知で自動再開させる
- ScheduleWakeup は **harness 追跡外の外部状態 polling 専用** (GitHub Actions / CI / リモートデプロイ監視 / 別 process が書き出すファイルの polling)
- 上記以外で ScheduleWakeup を使うのは禁止 (cache miss + cost + 「動いてない」印象 の三重損失)

## タスク受領時の skill 推挙呼び出し (必須)

新規タスク受領時、実装着手前に必ず以下を実行する:

1. `helix skill chain "<タスク記述>"` を呼び、上位スキルと推奨 agent を確認する
2. 推挙された skill / agent に従って委譲先を決定し、Opus 自身が直接実装しない原則を優先する
3. skip する場合は、自明な小修正または既知 skill のみ使用である理由を会話または final report に記録する

これは PLAN-022 で確立されたランタイム原則である。skill 推挙は gpt-5.4-mini 経由で 1 時間キャッシュされるため、コスト負担はほぼない。

## 委譲 Codex のコミット禁止

`helix codex` / `codex exec` で呼ぶ **委譲 Codex** は `git add` / `git commit` / `git push` を一切しない。Opus (PM) が成果物検証後に commit する。チャット (TL モード) Codex は対象外。

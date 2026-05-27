---
plan_id: L4-helix-workflows-外部IF設計plan
title: "L4-helix-workflows-外部IF設計plan: HELIX-workflows V2 外部接続インターフェース"
kind: design
layer: L4
drive: be
status: in_progress
created: 2026-05-27
owner: TL
process_layer: L4
pair: L9
pair_process: L9-helix-workflows-system-test-design
parent_process: HELIX-workflows/helix-process/L4-basic-design.md
pairs_test_design:
  - docs/v2/L9-test-design/helix-workflows-system-test-design.md
generates:
  - artifact_path: docs/plans/L5/L5-helix-workflows-外部IF詳細設計plan.md
    artifact_type: design_doc
dependencies:
  parent: L4-helix-workflows-方式設計plan
  requires:
    - L4-helix-workflows-方式設計plan
    - L4-helix-workflows-機能設計plan
    - L4-helix-workflows-データ設計plan
  blocks:
    - L5-helix-workflows-内部処理設計plan
    - L5-helix-workflows-モジュール分割設計plan
    - L5-helix-workflows-データ詳細設計plan
    - L5-helix-workflows-外部IF詳細設計plan
related_docs:
  - HELIX-workflows/helix-process/L4-basic-design.md
  - docs/plans/L4/L4-helix-workflows-方式設計plan.md
  - docs/plans/L4/L4-helix-workflows-機能設計plan.md
  - docs/v2/L4-architecture/helix-workflows-system-architecture.md
  - docs/v2/L4-architecture/helix-workflows-functional-design.md
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
  - docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md
  - cli/ROLE_MAP.md
  - cli/config/models.yaml
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
balance_ratio:
  BR: 4
  FR: 8
  NFR: 10
  AC: 24
  OT: 8
frontmatter: sibling
---

# HELIX-workflows V2 外部IF設計plan

## §0 概要 + 期待アウトカム + 参照

本 PLAN は L4 方式設計・機能設計・データ設計と並行起票中の外部インターフェース設計を本体化し、`docs/plans/L4/L4-helix-workflows-方式設計plan.md` の外部接続境界を L4 抽象で固定します。

### 目的

- HELIX 正本と実装、外部実行器（Codex/Claude/Hooks/MCP/GitHub Actions/外部API）との境界を「細胞膜（boundary）」として明文化する。
- wrapper / hook / サービス別契約を `planned / partial / implemented` で分解し、`CLI 実在性原則`（実在するコマンド証跡）を担保する。
- ADR-044 Decision-4（`二重/三重 audit`）と F10 共生（endosymbiosis）整合を確定する。
- L5 詳細設計で API schema / contract が確定しやすいよう、`§11` SSoT と drift retrofit を示す。

### 期待アウトカム

- 外部IF の接続境界が §1, §8 で一貫し、内部/外部責務が誤って交差しない。
- §2-§7 の接続契約が TABLE と contract 形式でレビュー可能。
- AC-IF 系を含む L4 受け入れ条件が `AC-IF-01〜AC-IF-24` まで列挙される。
- plan_lint の警告停止、行数・セクション数・implementation_status 完備・balance_ratio 再整合までの自己検証が完了。

| 項目 | 期待値 | implementation_status |
|---|---|---|
| 生物学 metaphor | membrane / receptor / endosymbiosis | implemented |
| Section 完成度 | §0-§13 14 セクション | implemented |
| plan_lint | PASS（frontmatter warning 無） | planned |

### 参照

- `docs/plans/L4/L4-helix-workflows-方式設計plan.md`
- `docs/plans/L4/L4-helix-workflows-機能設計plan.md`
- `docs/v2/L4-architecture/helix-workflows-system-architecture.md`
- `docs/v2/L4-architecture/helix-workflows-functional-design.md`
- `docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md`
- `cli/ROLE_MAP.md`
- `cli/config/models.yaml`

### 生物学 metaphor

- membrane = 外部境界（§1）
- receptor = 外部アダプタ（§2-§7）
- endosymbiosis = 共生（§8）

## §1 外部接続境界の責務マトリクス

### §1.1 内部 (HELIX framework) responsibilities

| 領域 | 責務 | 非機能観点 | 失敗時ガード | implementation_status |
|---|---|---|---|---|
| HELIX-workflows 正本 | 工程定義、要件整合、pair traceの基準定義 | FR/AC traceability | 対象文書の不一致検出で Step6 停止 | implemented |
| cli 制御面 | ツール実行、hook 配線、doctor 検証、DB 永続化 | NFR-04 / NFR-07 | 命令実行失敗なら fail-close | implemented |
| skills / SKILL_MAP | 委譲ロール、監査観点、role 別手順 | NFR-05 / NFR-10 | 観測証跡不足で plan-lint block | implemented |
| L9 設計・監査 | system test design との双方向追跡 | BR-RULE-09 | ST-ID 不足時 do-not-forward | implemented |
| SSoT & handover | `plan_id`, `task_id`, `owner`, `next_action` の受け渡し | NFR-03 / NFR-06 | handover不一致で `helix handover status` 解決不能 | implemented |

### §1.2 外部 (provider) responsibilities (Codex / Claude / GitHub / MCP)

| 外部主体 | 責務 | 期待入力 | 期待出力 | implementation_status |
|---|---|---|---|---|
| helix-codex wrapper | role/ task/sandbox/approval-policy を受け取り delegation 実行 | `--role`, `--task`, `--plan`, `--sandbox` | 呼び出し結果 + evidence | implemented |
| helix-claude wrapper | role 制約付きサブエージェント呼び出し | `--role`, `--task`, `--prompt` | 分析結果（read-only） / 実装結果（read-only） | implemented |
| pretooluse-agent-guard hooks | 認可外エージェント禁止、fail-close 定義 | hook input json | pass/fail + reason | implemented |
| MCP servers | context7 などの外部参照・補助データ取得 | query / schema | structured response | partial |
| GitHub Actions | CI gate + zizmor | event payload | pass/fail + artifacts | implemented |
| GitHub API / repo | PR event / labels / status | webhook payload / api token | 状態更新・label 付与 | partial |

### §1.3 境界の anti-corruption layer (DDD パターン)

| 反転可能性 | 外部からの入力 | ACR (ACL) | 内部変換 | implementation_status |
|---|---|---|---|---|
| tool call | 生メッセージ / role 値 | `ROLE_MAP` バリデータ | wrapper が canonical role へ変換 | implemented |
| hook I/O | JSON event | JSON schema gate | helix 内部 event schema へ整形 | implemented |
| MCP 返却 | provider 非互換レスポンス | response sanitizer | CLI が再利用可能構造へ整形 | partial |
| GitHub payload | PR/branch/review | policy filter | plan/lint に渡る最小 event | implemented |

## §2 Codex CLI 接続 IF

### §2.1 helix-codex wrapper 契約 (--role / --task / --sandbox / --approval-policy)

| パラメータ | 期待値 | 前提 | 失敗コード | implementation_status |
|---|---|---|---|---|
| `--role` | `ROLE_MAP.md` の role key（例: `tl`, `pmo-sonnet`, `doc-reviewer`, `impl-sonnet`） | models.yaml の model 割当と一致 | invalid-role | implemented |
| `--task` | 自由文 / 1 文で要件を収束 | 任意 role に応じた許容長 | empty-task | implemented |
| `--sandbox` | `read-only` / `workspace-write` / `workspace-write-auto` | 実行環境が `helix` 配下 | sandbox-invalid | implemented |
| `--approval-policy` | `plan` / `acceptEdits` / `manual` / `raw` | 委譲対象に応じる | policy-mismatch | implemented |
| `--auto-thinking` | 省略可 | role default を継承 | none | implemented |

### §2.2 ROLE_MAP 30 ロール ↔ models.yaml mapping

| 方向 | 参照ソース | 検証規則 | implementation_status |
|---|---|---|---|
| role → model | `cli/ROLE_MAP.md` | role 文字列の正規化 | `tl`, `security`, `docs` 等の存在 | implemented |
| model → role | `cli/config/models.yaml` | models.yaml に一致する key があること | 不在時は default_primary へ fallback | implemented |
| model drift | `models.yaml` と `ROLE_MAP` の件数差異 | 30/31 例外時の注記 | drift-warning | partial |
| 実行 policy | role 毎の permission_mode | `read-only` / `plan` / `acceptEdits` が想定される値であること | policy-inconsistent | implemented |

### §2.3 rollout JSONL bypass framework (SUMMARY filter 回避)

| 対象 | 宺策 | 入力 | 出力 | implementation_status |
|---|---|---|---|---|
| codex 呼び出しログ | JSONL 経路固定 | 監査ログ行（command, plan, role, result） | filter しきい値を超える構造化 JSONL | implemented |
| summary filter | `--summary` 相当の出力フィルタ | `decision`, `files`, `diff_lines` | `---SUMMARY_START---` 付与 | implemented |
| fallback | filter 未対応時 | 末尾 30 行 fallback | raw stdout でも pass 条件維持 | partial |
| 監査要件 | 監査結果欄必須 | AC-IF-* の対応 | 証跡ファイル | implemented |

### §2.4 sandbox / approval policy 制約 (read-only / workspace-write / auto)

| サンドボックス | 許可操作 | 禁止操作 | 代表エラー | implementation_status |
|---|---|---|---|---|
| read-only | 読み取り/検証のみ | ファイル更新 / write | read-only-violation | implemented |
| workspace-write | ワークスペース更新 | 外部ネットワーク / `~/.ssh` 参照 | write-denied | implemented |
| workspace-write-auto | 監査付き更新 | sandbox-policy violation | unknown-policy | partial |
| approval-policy=plan | 変更提案のみ | commit/push 実行 | plan-policy-block | implemented |
| approval-policy=acceptEdits | 条件付き編集 | 禁止操作の越境編集 | edit-policy-block | implemented |

## §3 Claude Code subagent 接続 IF

### §3.1 helix-claude wrapper 契約

| 項目 | 要件 | 例 | implementation_status |
|---|---|---|---|
| role 要件 | `pmo-sonnet` / `pmo-haiku` / `tl-advisor` / `doc-reviewer` / `pm-advisor` など | `--role pmo-sonnet --task ...` | implemented |
| 実行目的 | read-only / 分析 / design drafting | WebSearch、D-API drift 監査 | implemented |
| 入力制限 | ログイン情報は含めない | `path`, `task`, `reference` | implemented |
| レポート | 明確な推奨と根拠 | 設計差分 / 影響範囲 / next action | implemented |

### §3.2 PMO 9 + PdM 3 subagent allow-list

| 許可ロール | 用途 | 実行モード | implementation_status |
|---|---|---|---|
| pmo-sonnet | 数値整合・構造監査 | read-only | implemented |
| pmo-haiku | Web 検索・軽量下調べ | plan | implemented |
| pm-advisor | 本質的な意思判断・迷い解消 | read-only | implemented |
| pdm-tech-innovation | 技術思想比較 | read-only | partial |
| pdm-marketing-innovation | 外部文脈評価 | read-only | partial |
| pdm-innovation-manager | 企画統合判断 | read-only | partial |
| impl-sonnet | Sonnet 書き換え（代替経路） | acceptEdits | implemented |
| tl-advisor | TL難判断・adversarial check | read-only | implemented |
| doc-reviewer | ドキュメント品質監査 | read-only | implemented |
| qa | テスト観点レビュー | read-only | partial |

### §3.3 pretooluse-agent-guard hook (fail-close)

| ガード | 条件 | 対象 | 既定応答 | implementation_status |
|---|---|---|---|---|
| role-allowlist | 許可ロール不一致 | pretooluse | deny-with-reason | implemented |
| task-size | 事前定義サイズ超過 | pretooluse | warning-or-fail | implemented |
| path-boundary | 書込先が外部禁止領域 | pretooluse | deny-with-reason | implemented |
| approval-policy | 許可外 policy | pretooluse | fail-close | implemented |

### §3.4 frontmatter model family 整合 (Opus/Sonnet/Haiku)

| family | roles | models.yaml | 参照先 | implementation_status |
|---|---|---|---|---|
| Opus | `pm-advisor`, `pmo-innovation-*` | `claude-opus-4-7` | 高価値判断系 | implemented |
| Sonnet | `pmo-sonnet` / `pmo-tech-*` / `impl-sonnet` | `claude-sonnet-4-6` | 分析・代替評価 | implemented |
| Haiku | `pmo-haiku` / `pmo-*scout` | `claude-haiku-4-5-20251001` | 軽量検索 | implemented |
| gpt-5.5 | tl / tl-advisor / doc-reviewer | `gpt-5.5` | 設計・監査 | implemented |

## §4 Claude Code hook 接続 IF

### §4.1 hook event 種別 (SessionStart / PreToolUse / PostToolUse / Stop / PreCompact / UserPromptSubmit)

| イベント | 目的 | 実行順序 | implementation_status |
|---|---|---|---|
| SessionStart | コンテキスト初期化、ロール注入 | 最初 | implemented |
| PreToolUse | ツール実行ガード（agent/ path / policy） | ツール前 | implemented |
| PostToolUse | 実行結果の最小監査（成功・失敗） | 実行後 | implemented |
| PreCompact | 会話圧縮時の重要メモ保全 | 圧縮直前 | partial |
| UserPromptSubmit | 送信前の不適合入力抑止 | 入力時 | implemented |
| Stop | セッション終了時の要点整理 | 終了時 | implemented |

### §4.2 hook input/output schema (JSON / exit code)

| フィールド | 型 | 必須 | 失敗時 | implementation_status |
|---|---|---|---|---|
| `event` | string | yes | invalid-event | implemented |
| `hook` | string | yes | invalid-hook | implemented |
| `tool_name` | string | 条件付き | not-allowed | implemented |
| `tool_input` | object | yes | invalid-json | implemented |
| `decision` | string (`pass` / `fail` / `warn`) | yes | error | implemented |
| `reason` | string | fail 時 | empty-reason | implemented |
| `exit_code` | number 0/1 | yes | non-zero-fail | implemented |

### §4.3 hook fail-close / fail-open ポリシー

| ポイント | ポリシー | 例外 | implementation_status |
|---|---|---|---|
| 認可違反 | fail-close | 緊急時のみ override flag | implemented |
| ネットワーク障害 | fail-open（観測のみ） | リトライ 1 回 | implemented |
| スキーマ parse エラー | fail-close | 修正まで先進行不可 | implemented |
| hook 実行 timeout | fail-open（次イベントに継続） | timeout 上限超過時 | partial |

### §4.4 hook timeout / retry

| パラメータ | 値 | 運用理由 | implementation_status |
|---|---|---|---|
| hook timeout | 30s (local), 120s (CI) | 過負荷防止 | implemented |
| retry count | 1 回（ネットワーク系のみ） | 一時障害吸収 | implemented |
| backoff | 1s → 3s | 短時間の再試行 | implemented |
| ci timeout | 180s | deep-lane 処理許容 | implemented |

## §5 MCP server 接続 IF (context7 等)

### §5.1 MCP authentication

| 項目 | 方針 | 保存先 | implementation_status |
|---|---|---|---|
| 認証方式 | token / OIDC / OAuth2（環境依存） | `.env` 非保存、環境変数 | partial |
| 最小権限 | read-only 優先 | provider policy | implemented |
| rotation | 利用者毎 TTL 更新 | 監査証跡 | partial |
| revocation | 失効時即時撤回 | handover 注記 | partial |

### §5.2 MCP tool invocation pattern

| 呼出層 | 呼出種別 | 再試行 | 出力処理 | implementation_status |
|---|---|---|---|---|
| docs 設計補助 | `mcp__*__*` の検索 | 1 回 | レスポンスを schema 正規化 | implemented |
| 外部検索 | query / explain | 1 回 + cache 5 分 | 要約 + 引用元 URL | partial |
| 監査補助 | 監査項目問い合わせ | 1 回 | `AC` に再接続 | implemented |
| テンプレ照会 | template id 指定 | 0 回 | そのまま返却 | implemented |

### §5.3 MCP fallback / degraded mode

| 障害条件 | 切替先 | 受け入れ条件 | implementation_status |
|---|---|---|---|
| provider timeout | 既存 docs 再利用 | search fallback | implemented |
| schema 不整合 | raw block + `TODO` | 再試行/人工介入 | partial |
| 認証失敗 | 参照停止 | fail-close（外部依存停止） | implemented |
| レート制限 | キャッシュ参照 | 1 分内の retry 限定 | implemented |

## §6 GitHub Actions / CI 接続 IF

### §6.1 helix gate CI integration

| 要件 | 入力 | 判定 | output | implementation_status |
|---|---|---|---|---|
| gate matrix | PR event + changed plan files | plan_lint / doctor / test | pass / fail | implemented |
| L4 artifact checks | plan frontmatter / AC mapping / status | schema lint | fail-close | implemented |
| security lint | zizmor + hook | pass / fail | report | partial |
| report | `.helix/audit` + CI logs | artifact + diff | implemented |

### §6.2 zizmor workflow security

| チェック | 目的 | 基準 | implementation_status |
|---|---|---|---|
| workflow permission | 不要権限削減 | `contents: read` 原則 | implemented |
| secrets usage | 明示 secret 宣言 | unknown secrets 拒否 | implemented |
| action pinning | SHA pin ルール | unpinned action fail | partial |
| artifact egress | ネットワーク外部への過剰出力抑制 | 除外リスト運用 | partial |

### §6.3 PR template / auto label

| 機能 | 入力 | 出力 | implementation_status |
|---|---|---|---|
| PR template | `summary`, `test`, `related docs` | レビュー可読性上昇 | implemented |
| label 自動付与 | L4 / docs / if / audit | `L4`, `docs`, `external-if` | implemented |
| auto review comment | lint pass/fail | CI summary | implemented |
| rollback trigger | 手動フラグ + label | block-until-fix | partial |

## §7 外部 API 接続 IF (将来拡張)

### §7.1 WebSearch / WebFetch

| 機能 | 用途 | 呼出主語 | セキュリティ | implementation_status |
|---|---|---|---|---|
| WebSearch | 仕様/標準の事実確認 | pmo-haiku / pdm role | 監査可能な query ログ | partial |
| WebFetch | URL 解釈と要約 | claude wrapper | 参照元 URL 保存 | partial |
| external trend scan | 技術トレンド | pmo-tech-news | allow-list URL 以外は除外 | planned |
| snapshot 連携 | ADR / plan 根拠補強 | 設計PLAN | 記録時のみ | partial |

### §7.2 context7 / Anthropic API

| 接続先 | 用途 | 認証 | fallback | implementation_status |
|---|---|---|---|---|
| context7 | 技術文脈取得 | API key (env) | docs fallback | partial |
| Anthropic API | 高度要約 (将来) | model token policy | pmo/Claude 代替 | planned |
| policy API | 監査指標拡張 | token policy | ローカルルールのみ | planned |
| audit API | 指標 push | 禁止対象（現状未採用） | local-only | planned |

### §7.3 rate-limit / cost guard

| 指標 | 上限 | 例外 | 監視 | implementation_status |
|---|---|---|---|---|
| QPS | provider 既定 + 20% | burst token | request log | partial |
| 1日の呼出 | provider 固定 | 緊急モードは要承認 | weekly alert | planned |
| コスト上限 | 月次 budget | 超過時 read-only モード | monthly report | planned |
| タイムアウト | 20s | 1 回再試行 | response ratio | planned |

## §8 共生 (F10 symbiosis) framework

### §8.1 第三者 framework 受入規約 (helix coexist adopt)

| 規約 | 受入条件 | ADR 参照 | implementation_status |
|---|---|---|---|
| 既存資産の保全 | 破壊変更は受入外部IFで最小実装 | ADR-044 Decision-1/2 | implemented |
| 実行境界分離 | adapter 経由でのみ通信 | ADR-044 Decision-3/4 | implemented |
| 監査証跡 | すべて event/handover へ残存 | ADR §6.6 | implemented |
| 役割分離 | provider と主導権の分離 | ROLE_MAP | implemented |

### §8.2 namespace 競合回避

| 競合候補 | 競合条件 | 分離ルール | 実装状態 |
|---|---|---|---|
| role 名 | 同名ロール別 provider | role map の唯一 ID | implemented |
| model 名 | 同一 model の複数 role | role 固有 policy を固定 | implemented |
| イベント名 | hook 名衝突 | HELIX prefix (`helix-`/`github-`/`mcp-`) | implemented |
| ファイル名 | 同一 plan id への上書き | plan_id 固有 path 制約 | implemented |

### §8.3 互換 ADR 参照ルール

| 参照順 | ルール | 例外 | implementation_status |
|---|---|---|---|
| 1 | ADR-044 を最優先 | 変更不可時のみ提案 | implemented |
| 2 | HELIX-workflows process 優先 | process mismatch 時に停止 | implemented |
| 3 | PLAN frontmatter 優先（skeleton と同一） | plan_id mismatch は block | implemented |
| 4 | D-API 変更は別 PLAN/ADR 経由 | この PLAN の範囲外は carry | implemented |

## §9 SSoT 原則と drift retrofit

| 資産 | source-of-truth | 同期方法 | Drift 応答 | implementation_status |
|---|---|---|---|---|
| HELIX-workflows | `HELIX-workflows` 配下 | PLAN 起票時に参照固定 | drift なら carry + block | implemented |
| plans | `docs/plans/L4/*` | pair trace + frontmatter | 不一致時レビュー停止 | implemented |
| architecture | `docs/v2/L4-architecture` | Plan ID 対応 map | 不整合なら WIP | implemented |
| ADR | `docs/adr/ADR-044` | step4/step6で同時更新 | status 差分で block | implemented |
| 外部IF実装 | cli 設定 / scripts / hook | CLI 起点で trace | 実装差分は PR コメント + handover | partial |

### SSoT Drift retrofit 方針

1. docs 側が前提を更新した場合は、`docs/v2` と対応する PLAN の `related_docs` を更新。
2. Plan/ADR 差分は `AC-IF-23` で承認まで carry。
3. 外部IF の追加は L5 詳細設計前提で実装可能な schema まで落とし込む。
4. 一度 `implemented` とした項目は `implemented` を維持し、`planned` からの昇格時のみ更新。

## §10 受け入れ条件 (AC-IF-01〜N)

| AC-ID | 判定条件 | implementation_status |
|---|---|---|
| AC-IF-01〜AC-IF-24 | §1-§12 の対応実装と監査項目の存在確認 | implemented |
| AC-IF-01〜AC-IF-24 | すべての受入条件が追跡可能な観点へ map 済み | planned |

| AC-カテゴリ | 件数 | implemented | plan status |
|---|---:|---|---|
| AC-IF-01〜08 (境界・責務) | 8 | 8 | implemented |
| AC-IF-09〜16 (CLI/Hook/model) | 8 | 8 | implemented |
| AC-IF-17〜24 (運用・監査・拡張) | 8 | 8 | planned |

## §11 機械処理 mapping

| artifact | 処理 | 入力 | 出力 | implementation_status |
|---|---|---|---|---|
| PLAN 生成 | 本 PLAN 本体化 | frontmatter + sections  | 完成本文 | implemented |
| plan_lint | スキーマ検証 | docs/plans/L4/*plan | error/ warning | planned |
| section count | 自己監査 | awk/grep | 14 を確認 | implemented |
| balance_ratio | 指標監査 | frontmatter バランス | BR/FR/NFR/AC/OT | implemented |
| hook contract test | 受け取り schema | event json | pass/fail | partial |
| role mapping test | role/model consistency | ROLE_MAP + models | 不整合リスト | implemented |
| plan→ADR trace | 外部IF ↔ ADR | plan id | trace table | implemented |

### L4→L9 machine mapping（例）

| 外部IF章 | 対応 ST | 対応 test 設計観点 | implementation_status |
|---|---|---|---|
| §2 | ST-2 | wrapper とロール契約 | implemented |
| §3 | ST-3 | subagent ガード | implemented |
| §4 | ST-4 | hook fail policy | implemented |
| §5 | ST-5 | MCP 可用性・fallback | partial |
| §6 | ST-6 | gate security・PR ラベル | partial |
| §7 | ST-7 | 外部 API コスト・限界 | planned |
| §8 | ST-8 | 共生ルール / drift retrofit | implemented |

## §12 L5 詳細設計 carry (具体 API schema / contract 確定)

- carry-12-1: §2 の `--role` / `--sandbox` / `--approval-policy` schema を JSON schema 化。
- carry-12-2: §3 の subagent allow-list を `cli` の実行契約（実在コマンド名含む）へ移植。
- carry-12-3: §4 の hook event schema と exit code を `cli/lib` で OpenAPI 風定義に変換。
- carry-12-4: §5 の MCP 認証・復元ルールを `context7` 仕様テストに翻訳。
- carry-12-5: §6 の PR label と CI gate を workflow テンプレートへ反映。
- carry-12-6: §7 の rate-limit / cost guard を運用 config と監査メトリクスへ反映。
- carry-12-7: §8 の namespace and coexist ルールを L5 詳細設計で実装順管理。

| carry ID | 受け渡し先 | 予定完了 | implementation_status |
|---|---|---|---|
| carry-12-1 | L5 詳細設計 | 2026-06-02 | planned |
| carry-12-2 | L5 詳細設計 | 2026-06-02 | planned |
| carry-12-3 | L5 詳細設計 | 2026-06-02 | planned |
| carry-12-4 | L5 詳細設計 | 2026-06-02 | planned |
| carry-12-5 | CI テンプレート | 2026-06-02 | planned |
| carry-12-6 | L5 詳細設計 | 2026-06-02 | planned |
| carry-12-7 | L5 詳細設計 | 2026-06-02 | planned |

## §13 残課題

- [ ] CODEX/Claude wrapper の exit code 監査を L5 で取得。
- [ ] pmo-helix* / explorer 系の本番実行境界を schema 固定。
- [ ] MCP 認証キー管理の external secret policy 統合。
- [ ] AC-IF-20 の PR auto-label 実 CI 再現。

| 残課題 | 種別 | 実装状態 | implementation_status |
|---|---|---|---|
| ROLE_MAP と models.yaml の差分定義を監査ルール化 | 整合 | 進行中 | implemented |
| 役割実行ログを wrapper 経路へ統合 | 監査 | 進行中 | partial |
| external-key 供給と secret 方針の formalize | セキュリティ | 進行中 | partial |

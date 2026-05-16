# HELIX Core — 共通開発フロー定義

> Claude Code / Codex CLI 共通。ツール固有設定は各ツールの設定ファイルに記載。
> 正本: SKILL_MAP.md §正本宣言 参照

---

## 応答言語

- 日本語で応答する

## スキル

- `~/ai-dev-kit-vscode/skills/` に配置
- triggers 該当時は自発的に Read。全スキル一括読み込み禁止
- コンテキスト管理: `context-memory` スキル参照

## モデル割当（真実は `cli/config/models.yaml`）

| ロール | モデル | thinking |
|------|--------|--------|
| PM | Opus (Claude Code) | — |
| PMO Sonnet | claude-sonnet-4-6 | medium |
| PMO Haiku | claude-haiku-4-5-20251001 | low |
| TL | gpt-5.5 | high |
| SE | gpt-5.4 | high |
| PE | gpt-5.3-codex-spark / gpt-5.3-codex | low-medium |

## タスク受領

1. サイジング S/M/L（SKILL_MAP.md §タスクサイジング）
2. フェーズスキップ決定（SKILL_MAP.md §フェーズスキップ決定木）
3. ゲート判定（`skills/tools/ai-coding/references/gate-policy.md §ゲート一覧`）
4. 該当スキルを Read（SKILL_MAP.md オーケストレーションフローの `→` 右のスキル名を参照）
4.5 実装着手前 (L4 entry): `helix code find "<keyword>"` で既存実装の流用候補を確認する
  - 公開 API / 再利用候補は `--bucket coverage_eligible`（default）で確認
  - private helper の再利用/PoC seed 探索は `--bucket private_helper` を併用する
  - 非公開 → 公開昇格候補（seed candidate）を `--seed-promotable true` で抽出する
4.6 v2 ディスパッチ: タスク性質で必須委譲先を優先決定
- BE 実装/DB/インフラ: `helix codex --role se`
- 設計・レビュー・デバッグ: `helix codex --role tl`
- 速度重視単機能実装: `helix codex --role pg`
- 状況把握 / docs チェック: `helix claude --role pmo --model sonnet --execute`
- 軽文書チェック / docs/**: `helix claude --role pmo --model haiku --execute --allow-paths "docs/**"`
4.7 スキル推奨: `helix skill chain "<タスク記述>"` を任意で実施。skip 理由がある場合は会話または final report に記録する（例: 自明な小修正、既知 skill のみ使用 等）

L4 implementation / build / G4 補足（PLAN-013）:
- L4 entry: `helix code find`、`helix code stats --uncovered --bucket coverage_eligible` を使って既存資産を確認する
- L4 implementation: 新規 public symbol は `coverage_eligible`、`_` 始まり helper は `private_helper` に分類する
- L4 build: `helix code build` で catalog を再生成し、`bucket` / `symbol_line` / metadata を自動付与する
- G4: `helix code stats --uncovered --scope core5 --bucket coverage_eligible --fail-under 80` を走らせて coverage gate を判断する
5. 実行開始
6. ミニレトロ: G2/G4/L8 通過時（`skills/tools/ai-coding/references/gate-policy.md §ミニレトロ`）
7. readiness exit 条件確認 → 該当スキル Read

> **Reverse モード**: 既存コードからの設計復元は SKILL_MAP.md §Phase R / `workflow/reverse-analysis/SKILL.md` を参照。Forward とは別のサイジング・ゲート体系（R0→R4→Forward→RGC）を使用。
> ※ RGC（Reverse Gap Closure）は `helix reverse rgc` で実装済み。R4 Gap Register から集計を表示する。

## 設計提案

- ユーザーへの技術提案前に `helix plan draft → review → finalize` を実施
- TL approve なしで finalize 不可
- 詳細は `workflow-core.md §設計提案レビュー` 参照

## Advisor 召喚（PM / TL 難判断）

チャット PM (Opus / Sonnet 問わず) と実装担当が大局判断・技術選択で迷ったとき、自前で結論を出す前にアドバイザーを呼ぶ。アドバイザーは read-only で構造化助言のみ返し、最終判断は呼び出し側が下す。

- `helix claude --role pm-advisor --execute --task "..."` — PM 級判断 (スコープ / 優先度 / 大局リスク / フェーズ整合 / 委譲先) を Opus 4.7 に相談
- `helix codex --role tl-advisor --task "..."` — TL 級判断 (設計 / 契約 / 技術選択 / テスト戦略 / リファクタ) を gpt-5.5 high に相談

運用原則:
- PM が Sonnet で動くチャットでは難判断を Sonnet 単独で確定させず、必ず pm-advisor (Opus) に相談する
- PM が Opus でも技術判断の adversarial check として tl-advisor を呼ぶ運用は推奨
- 実装担当 (Sonnet / Codex) は契約・設計で迷えば tl-advisor、スコープで迷えば pm-advisor を呼ぶ
- 呼び出した task / 助言内容は会話または final report に残し、判断トレースを保つ

## 工程表・承認・委譲

- 実装は L3 工程表、`.helix/task-plan.yaml`、handover Next Action の該当行を正とする。
- 工程表がある場合、`plan_id`、`task_id` または `WBS ID`、`L4 Sprint`、依存、受入条件、reference_docs を確認してから L4 に入る。
- 計画・実装順・整理案をユーザーへ提示した場合、明示承認があるまでファイル編集・依存追加・外部状態変更へ進まない。
- 工程表外の変更が必要になった場合は、先に工程表更新またはユーザー確認へ戻る。
- TL は工程表の role に応じて `helix codex`、`helix claude --dry-run`、`helix team`、`helix review` を使い、使えない場合は理由を証跡化する。

## 設計⇔テスト対応 (V-model 原則、2026-05-17 確立 / 訂正)

V-model の基本原則として、設計フェーズの各層と検証 (テスト) フェーズの各層は 1:1 対応する。ただし **4 つの artifact は別々の文書として存在** し、双方向 trace で繋ぐ。同じ文書に統合してはいけない (設計と実装コードが別物なのと同様、テスト設計とテストコードも別物)。

### 4 artifact 構造

```
設計 (D-API EXT §3.X 等)  ←─対応関係─→  テスト設計 (test-design/*.md)
        ↓ 実装                                    ↓ 実装
実装コード (routes/*.py)   ←─対応関係─→  テストコード (test_*.py)
```

| Artifact | 担当層 | 例 |
|---|---|---|
| **① 設計** | 機能設計 / 詳細設計 / 全体設計 | D-API EXT §3.X (機能設計) / CONCEPT.md (全体設計) |
| **② 実装コード** | コード成果物 | cli/lib/http_api/routes/*.py |
| **③ テスト設計** | 単体/結合/総合テスト設計 | docs/v2/L4-test-design/PLAN-074-unit-test-design.md |
| **④ テストコード** | テスト成果物 | cli/lib/tests/test_*.py |

### 4 層 ⇔ 4 artifact 対応

| HELIX 層 | ① 設計 | ③ 対応するテスト設計 | ④ テスト実装フェーズ |
|---|---|---|---|
| L1 要件定義 | 要件 / 受入条件 | **受入テスト設計** | L8 受入 |
| L2 全体設計 | CONCEPT / ADR | **総合テスト設計** | L6 統合検証 |
| L3 詳細設計 | D-API / D-DB | **結合テスト設計** | L4 結合テスト実装 |
| L3-L4 機能設計 | endpoint / 関数 schema | **単体テスト設計** | L4 単体テスト実装 |

### 双方向 trace ルール

各 artifact は対応関係を明示する:

- **設計 → 実装コード**: 設計に「実装ファイル: X.py」明示
- **実装コード → 設計**: コード docstring に「契約: D-API EXT §3.X」明示
- **設計 → テスト設計**: 設計に「テスト設計ファイル: docs/v2/L4-test-design/PLAN-XXX-*-design.md」明示
- **テスト設計 → 設計**: テスト設計に「対象設計: D-API EXT §3.X」明示
- **テスト設計 → テストコード**: テスト設計に「テスト実装ファイル: test_*.py」明示
- **テストコード → テスト設計**: テスト docstring に「DoD 検証: PLAN-XXX-*-design.md U-XXX-001〜N」明示

### 違反例 (してはいけない)

- ① 設計と ② 実装コードを同じ文書に書く (例: D-API EXT 内にコード本体を埋め込む)
- ① 設計と ③ テスト設計を同じ文書に書く (例: D-API EXT 内に test case 列挙を埋め込む)
- ③ テスト設計と ④ テストコードを同じ文書に書く (例: test ファイル先頭で長文 docstring に case 設計を書く)
- 4 artifact のいずれかが他の artifact への双方向 reference を欠く

### 既存 PLAN の retrofit

PLAN-075 (V-model 4 artifact 双方向 trace framework 強化) の Phase 3-4 で既存 PLAN を retrofit。helix doctor / G2-G4 ゲートで「4 artifact 全件 + 双方向 trace」を fail-close 化 (Phase 5)。

## 工程別 subagent 起動マップ (PLAN-076、2026-05-17 確立)

subagent は **性格** で 2 分類し、扱い (lint / 強制化 / trace) を分ける。

### ① 工程明示的サブエージェント (mandatory by phase) — 10 種

HELIX 工程で **必須** 組み込み。skip は理由要求、helix doctor / G2-G4 で「呼ばれていない → fail」自動 lint 対象 (PLAN-076 Phase 5 で fail-close 化予定)。

| Subagent | 必須工程 | 役割 |
|---|---|---|
| pdm-tech-innovation | G0.5 | 海外技術思想翻案 |
| pdm-marketing-innovation | G0.5 | 海外マーケ思想翻案 |
| pdm-innovation-manager | G0.5 / L1 接続 | 統合判断 |
| pmo-tech-fork | L2 entry (OSS 採用判断時) | OSS 探索 |
| pmo-tech-docs | L2 entry (設計手法精読時) | 外部 doc 精読 |
| pmo-helix-explorer | L2-L4 entry | HELIX 内資産探索 |
| pmo-project-explorer | L3-L4 entry | project 内資産探索 |
| pmo-project-scout | L4 entry | 軽量目星 |
| pmo-helix-scout | L2-L4 entry | HELIX 内軽量目星 |
| pmo-sonnet | G2/G4/L8 review | 判断伴う read-only |

### ② 実行選択サブエージェント (on-demand by judgment) — 4 種

工程に縛られず、判断に応じて任意起動。free will、lint 対象外。

| Subagent | 起動タイミング | 役割 |
|---|---|---|
| pmo-haiku | 軽 Web 検索 / docs/** 軽修正 | Web 検索目星 |
| pmo-tech-news | 週次定期 sweep | 最新 tech 動向 |
| pm-advisor | PM 級難判断時 | adversarial check |
| tl-advisor | TL 級難判断時 | adversarial check |

### 設計上の意味

| 観点 | mandatory (10 種) | on-demand (4 種) |
|---|---|---|
| trace 対象 | 必須 (helix.db audit) | 任意 |
| 強制化 | lint / ゲート fail-close | なし |
| CLI | `helix agent fire-mandatory --phase L2` | `helix agent suggest --task "..."` |
| 記録 | 呼ばれない → carry note 必須 | 呼んだ場合のみ会話記録 |

詳細: PLAN-076 (subagent 工程マッピング framework)。

## Sprint Plan 標準構造 (PLAN-077、2026-05-17 確立)

L4 実装中の Sprint Plan が毎回フリーハンドにならず、機械チェック / テスト起動 / レビューが Sprint 内必須ステップとして固定化される。

### Sprint .X 標準 8 ステップ

```
Step 1: Entry 条件確認          (前 Sprint 完遂 / dependency)
Step 2: 実装着手前               (helix code find / pmo-project-scout)
Step 3: 実装                    (Codex 委譲 or Opus 直接)
Step 4: ★機械チェック (mandatory in sprint):
        - py_compile (Python) / bash -n (bash)
        - shellcheck / markdownlint / yamllint
        - helix code stats / helix doctor
Step 5: ★テスト起動 (mandatory in sprint):
        - 単体テスト (該当範囲、即時)
        - 結合テスト (該当範囲)
        - 全回帰 (Sprint Exit 前、helix test)
Step 6: ★レビュー (mandatory in sprint):
        - セルフレビュー
        - pmo-sonnet review (G2/G4 時)
        - tl-advisor (on-demand、adversarial check)
Step 7: commit + carry note
Step 8: Exit 条件確認 (DoD)
```

### 2 分類

| ステップ性格 | mandatory in sprint | on-demand in sprint |
|---|---|---|
| 対象 | py_compile / 該当 test / 全回帰 / セルフレビュー / pmo-sonnet review (G2/G4) | security audit / perf test / coverage report / tl-advisor |
| 発火 | Sprint Exit 前に必ず | 必要時のみ |
| lint | 不在 → carry note 強制 | なし |
| CLI | `helix sprint complete --auto-check` | `helix sprint addon <check>` |

詳細: PLAN-077 (Sprint Plan 標準化 framework)。

## readiness と carry rule

PLAN-004 v5 と PLAN-009 v3 の方針として、L1-L11 を進める際は以下を適用する。

- 各 L の entry/exit 条件に readiness を明示し、未充足時は前段へ差戻す。
- 各ゲート（特に G1-G11）は readiness exit 判定に接続し、未達成は carry/passed 制御に反映する。
- IIP/deferral の評価は下記で統一する。

P0: gate stop（即修正）
P1: gate stop もしくは carry（PM 承認）
P2: 次 L 開始まで carry（deferred-finding として debt に記録）
P3: 任意 carry

deferred-finding は次の品質評価に反映し、accuracy_score から減点される（数値は共通で carry レベルにより重み付け）。

## Phase 4 Run (L9-L11)

PLAN-009 v3 の 4 フェーズ拡張に合わせ、Run 工程を追加する。

### L9: デプロイ検証

- デプロイ準備、ロールバック手順、smoke test、監視初期確認、初回復旧手順を検証する。

### L10: 観測

- リリース後の SLO/SLI、アラート、エラー率、外部依存の観測を完了し、未解決重大事象を確認する。

### L11: 運用学習

- postmortem と改善施策をまとめ、次サイクルの state/events へフィードバックし、運用引継ぎ資料へ反映する。

### 連携ゲート

- G9（デプロイ安定性）
- G10（観測完了）
- G11（運用学習完了）
- 本番運用対象では Run 工程必須。PoC や検証寄りのタスクは本番影響がなければ任意 skip。

## 状態管理の二層構造

| 層 | ファイル | 役割 | 参照元 |
|----|---------|------|--------|
| 宣言的状態 | `.helix/phase.yaml` | 現在のフェーズ・ゲート通過状況・凍結フラグ | 15スクリプト |
| イベントログ | `.helix/helix.db` (SQLite) | タスク実行履歴・hook 発火・フィードバック・学習 | 18+スクリプト |

- phase.yaml は YAML で人間が読める。手動リセット可能
- helix.db はイベント蓄積のみ。`helix log report` で可視化

## 原則

- **エスカレーション**: 本番影響・認証・決済・個人情報・ライセンス → 必ず人間に確認
- **ファイル作成前**: 既存リソース確認 → 重複なら作成しない

# HELIX Skill Map

## 概要

HELIXフレームワーク用スキルの一覧と分類。

## 正本宣言

このファイルは HELIX フレームワークの現行運用仕様の正本です（最終検証: 2026-02-12）

- **正本の構成**: SKILL_MAP.md（本ファイル）+ `~/.claude/CLAUDE.md` + 各 `SKILL.md`
- **アーカイブ資料**: `docs/archive/v-model-reference-cycle-v2.md`（参考・設計思想理解用のみ）
- **検証状態**: 企画書との整合性検証完了（重大差異2件を解決済み）
- **検証レポート**: `docs/proposals/spec-implementation-verification-2026-02-12.md`
- **矛盾時の優先順位**: 実装（本ファイル群）> アーカイブ資料

## オーケストレーションフロー

全タスクはこのフローに沿って実行する。各フェーズで `→` の右に示すスキルを Read してから作業する。

```
【企画】人間が要件提示
  ↓ → requirements-handover, estimation
【L1 要件定義】Opus: 要件を構造化、Haiku 4.5: 引継書に転記
  ↓ ★事前調査ゲート（MUST条件該当時: Haiku 4.5 が調査→調査メモ作成）
  ↓ → design-doc, api, db, security, visual-design（方針のみ）
【L2 設計】Codex 5.3: 設計書作成（FE/BE/DB）+ ビジュアル方針決定
  ↓ ★adversarial-review（セキュリティゲート条件該当時 or ADR作成時 → 自動発火）
  ↓ ★ミニレトロ（設計凍結後: 設計判断の妥当性振り返り）
  ↓ → api-contract                         ← codex exec -m gpt-5.4（設計レビュー）
【L2.5 API契約】Codex 5.3: OpenAPI仕様生成、型↔API↔DB整合性検証
  ↓ → dependency-map                       ← codex exec -m gpt-5.4（API契約レビュー）
【L3 依存関係】Codex 5.3: 依存マップ生成 → 実装順序決定
  ↓ → estimation §8-10
【L4 工程表】Codex 5.3: 工程表作成（難易度スコア・モデル割当・オーケストレーション込み）
  ↓ ★事前調査ゲート（実装.1 通過条件に調査メモ存在を追加）
  ↓ → ai-coding §4                         ← codex review（既存）
【L4.5 実装】Opus: 工程表に従いディスパッチ（自分で実装しない）
  │ Codex 5.4 → レビュー・品質アップ・トラブルシュート
  │ Codex 5.3 → 実装メイン（設計→実装の一気通貫）
  │ Codex 5.3 Spark → 軽量実装・軽微修正
  │ Codex 5.2 → 大規模コード精読・スキャン
  │ Sonnet → テスト・ドキュメント（実装禁止）
  │ Haiku 4.5 → リサーチ特化
  │ ★ 実装.2: codex review（軽量）/ 実装.5: codex review（フル品質）
  ↓ → visual-design                        ← codex review --uncommitted
【L4.7 Visual Refinement】実装済みUIへのビジュアルデザイン適用・調整
  │ 対象: 配色・余白・タイポグラフィ・構図・視線誘導
  │ V0（見た目のみ）→ そのまま検証へ
  │ V1（UI構造変更）→ L4.5に差し戻し → L4.7再実行
  │ V2（契約影響）→ L2まで差し戻し
  ↓ ★ミニレトロ（実装凍結後: 実装の学び・工数乖離記録）
  ↓ → verification, testing, quality-lv5   ← codex review --uncommitted
【検証】並列: L2/L2.5/L3/L4.5/L4.7 検証（各レイヤー最大5ループ）
  ↓ → deploy, infrastructure, observability-sre
【L5 デプロイ】L5.1 準備（セキュリティスキャン + 環境構成 + 条件付き人間承認）
  │ L5.2 実行（ステージング確認 → 本番デプロイ → ヘルスチェック）
  │ L5.3 安定性（SLO基準 → observability-sre §7 劣化レベル表で判定）
  │ ★ 人間承認: 初回デプロイ / 認証・決済・PII / 破壊的DBマイグレ / 外部API変更 / エラーバジェット75%超 / インフラ構成変更
  ↓ → verification §14
【L6 受入】要件引継書 ↔ 最終成果物の突合
  ↓ ★ミニレトロ（終端: プロジェクト全体振り返り）
  ↓
【人間】成果物確認 → 本番リリース承認
```

**フェーズ間ルール:**
- 各フェーズ完了前に次フェーズに進まない
- 検証不合格 → レイヤー内ループ（5回）→ 上位層エスカレ → 人間
- Opus は自分で実装しない。全タスクをモデル割当表に従って委譲する（設計・実装はCodex 5.3/5.3 Spark、レビュー・品質はCodex 5.4、精読はCodex 5.2、テスト・ドキュメントはSonnet）
- L2-L4 フェーズは Codex 5.3 が作成 + Codex 5.4 がレビュー。実装フェーズは難易度スコアで Codex 5.3/5.3 Spark を分ける。5.4 はレビュー・品質アップ専任。5.2 は大規模精読タスク種別で分岐
- 小〜中規模タスクは全フェーズを踏む必要はない（下記の決定木に従う）
- **Codex レビュー義務化**: フェーズ遷移時に Codex レビューを必須とする（フロー図の `←` 参照）
  - コード差分 → `codex review --uncommitted`（L4.5→L4.7, L4.7→検証）— Codex 5.4
  - 設計書・仕様書 → `codex exec "レビュー"`（L2→L2.5, L2.5→L3）— Codex 5.4
  - 実装フェーズ内: 実装.2（軽量: Critical/High のみ）+ 実装.5（フル品質）— Codex 5.4
  - **5.4 ボトルネック緩和**: 低リスク案件（サイジング S + セキュリティゲート非該当）は Codex 5.3 が一次レビュー可。高リスク案件は 5.4 必須
- **ミニレトロ（マイルストーン基準）**: フェーズスキップに対応した振り返り（フロー図の `★ミニレトロ` 参照）
  - 設計凍結後 / 実装凍結後 / 終端フェーズ後にミニKPT（Keep/Problem/Try）を実施
  - Try は owner + due 必須（空文化防止）。重大リスク発見時のみ blocking Issue 化
  - 詳細: `ai-coding/references/layer-interface.md §ミニレトロ`
- **事前調査ゲート（Web検索強制）**: 設計・実装前に先行事例を調査（フロー図の `★事前調査ゲート` 参照）
  - L1→L2 間、実装.1 の通過条件として事前調査を必須化（MUST条件該当時）
  - 通過条件: 「検索した」ではなく「調査メモが存在する」こと
  - Context7 MCP を優先使用。機密情報の外部検索持ち出し禁止
  - 詳細: `ai-coding/references/layer-interface.md §事前調査ゲート` / `ai-coding §8`
- **作業前コード調査（実装.1a 必須）**: 実装.1 を .1a（コード調査）+ .1b（変更計画）に内部分割
  - .1a: 変更対象ファイルの Read 完了 / 依存関係列挙 / テスト現状確認 / 規約把握
  - .1a の `impact_analysis` を .1b の必須入力とする（未読のまま計画を立てない）
  - 詳細: `ai-coding/references/implementation-gate.md §実装.1`
- **IIP（実装内割り込みプロトコル）**: 実装中の前提崩壊・想定外トラブル対応
  - `interrupted` ステータスで `failed`（既知前提内ミス）と分離。リトライカウント外
  - 影響度: P0（ゲート内修正）/ P1（実装.1差戻し）/ P2（逆流ループ移送）/ P3（人間エスカレ直行）
  - 詳細: `ai-coding/references/implementation-gate.md §IIP` / `ai-coding/references/layer-interface.md §IIP`
- **L5 ゲート構造**: L5.1（準備）→ L5.2（実行）→ L5.3（安定性）の3段階ゲート
  - L5.1: セキュリティスキャン合格（critical 0件絶対 + high 新規追加0件）+ 環境構成確認 + 条件付き人間承認
  - L5.2: ステージング確認 → 本番デプロイ → ヘルスチェック
  - L5.3: SLO 基準での本番安定性確認（observability-sre §7 劣化レベル表が唯一の権威源）
  - 失敗時: IIP パターン踏襲（P0 ゲート内 / P1 検証差戻し / P2 L4.5差戻し / P3 人間エスカレ）
  - 詳細: `ai-coding/references/layer-interface.md §L5 内部ゲート`
- **L5 と V-L6 の責務境界**: L5 = デプロイ結果の SLO 達成確認、V-L6 = 運用体制の充足性検証。V-L6 は検証フェーズで実施済みであり、L5 の開始前提として参照する
- **adversarial-review（対立的レビュー）**: 高リスク設計判断の反証検証（フロー図の `★adversarial-review` 参照）
  - 自動発火: セキュリティゲート条件該当時（認証・決済・PII・外部API・インフラ構成変更）/ ADR 作成時
  - 任意発火: PM が「後戻りコストが高い」と判断した設計判断
  - スキップ: サイジング S / 既存ルールの機械的適用 / 同一テーマ実施済み
  - 責務分離: TL壁打ち（1案検証・低コスト）< codex review（品質チェック・中コスト）< adversarial-review（反証・高コスト）
  - 詳細: `workflow/adversarial-review/SKILL.md`

## タスクサイジング

タスク受領時に以下の3軸で S/M/L を判定する。3軸のうち**最大のサイズ**を採用。

| 軸 | S (Small) | M (Medium) | L (Large) |
|----|-----------|------------|-----------|
| ファイル数 | 1-3 | 4-10 | 11+ |
| 変更行数（見積） | ~100行 | 101-500行 | 501行+ |
| API/DB変更 | なし | 片方 | 両方 |

## フェーズスキップ決定木

```
タスク受領 → サイジング（上記）
│
[★ セキュリティゲートチェック: 上記の強制条件に該当するか確認]
[  → 該当あり: 通常判定 + 該当ゲートにスキップ不可フラグ付与]
[  → 該当なし: 通常判定のみ]
│
├─ S（小規模）
│   ├─ バグ修正 / リファクタリング → 【L4.5 実装】のみ
│   ├─ 新規小機能（単一画面・単一API等）→ 【L2 設計】→【L4.5 実装】→【検証】
│   ├─ 外部公開UI変更 → 【L2 設計】→【L4.5 実装】→【L4.7】→【検証】
│   └─ ドキュメント / 設定変更 → 【L4.5 実装】のみ
│
├─ M（中規模）
│   ├─ API変更なし（UI変更あり）→ 【L2 設計】→【L4.5 実装】→【L4.7】→【検証】
│   ├─ API変更なし・DB変更なし（BE/infraのみ）→ 【L2 設計】→【L4.5 実装】→【検証】
│   ├─ API変更なし・DB変更あり → 【L2 設計】→【L4.5 実装】→【検証】（※L2設計書でDB↔型整合を確認）
│   ├─ API変更あり → 【L2 設計】→【L2.5 API契約】→【L4.5 実装】→【L4.7】→【検証】
│   └─ 新規モジュール → 【L1 要件】→【L2 設計】→【L2.5】→【L4.5 実装】→【L4.7】→【検証】
│
│   ※ L2.5 スキップ時は L2 設計書の該当セクションを reference_docs に代替使用
│
└─ L（大規模）
    └─ フルフロー: 【L1】→【L2】→【L2.5】→【L3】→【L4】→【L4.5 実装】→【L4.7】→【検証】→【L5 デプロイ】→【L6 受入】
    └─ 純バックエンド: 【L1】→【L2】→【L2.5】→【L3】→【L4】→【L4.5 実装】→【検証】→【L5 デプロイ】→【L6 受入】
```

**セキュリティゲート強制条件**（サイズに関わらず該当ゲートのスキップ不可）:

通常のサイジング判定（S/M/L）は維持するが、以下の条件に該当する場合は該当ゲートを強制する:

| 条件 | 強制ゲート |
|------|----------|
| 外部API連携（新規/変更） | 事前調査ゲート必須 + L2.5 API契約レビュー必須 |
| 認証・認可ロジックの変更 | L2 セキュリティ設計レビュー必須 + 実装.3 セキュリティチェック必須 |
| 課金・決済関連 | L2 設計承認（PO）必須 + 実装.3 セキュリティチェック必須 |
| 個人情報の取り扱い変更 | L2 設計承認（PO）必須 |
| 複数リポジトリ / チームに影響 | L3 依存マップ必須 |

※ 決定木でスキップ判定された場合でも、上記に該当するゲートはスキップ不可

## フェーズ別 I/O サマリー

各フェーズの入出力と読み込むスキル。詳細は `ai-coding/references/orchestration-workflow.md` を参照。
階層間の遷移条件・ゲート判定・差し戻しルールは `ai-coding/references/layer-interface.md` を参照。

| フェーズ | 入力 | 出力 | スキル |
|---------|------|------|--------|
| L1 要件 | ユーザー要求 | 要件リスト + 仮定一覧 | requirements-handover, estimation |
| L2 設計 | 要件リスト | 設計書（画面/API/DB） | design-doc, api, db, security |
| L2.5 API契約 | 設計書 | OpenAPI仕様 + 型定義 | api-contract |
| L3 依存関係 | 設計書 + API仕様 | 依存マップ + 実装順序 | dependency-map |
| L4 工程表 | 依存マップ | 工程表（ID/タスク/難易度/担当/スキル） | estimation §8-10 |
| L4.5 実装 | 工程表 + 設計書 | 実装コード + テスト | ai-coding §4 |
| L4.7 Visual Refinement | 実装コード + L2ビジュアル方針 | デザイン適用済みコード | visual-design |
| 検証 | デザイン適用済みコード | 検証レポート（L2-L4.7各層） | verification, testing, quality-lv5 |
| L5 デプロイ | 検証済みコード + 検証レポート（V-L5/V-L6 pass） | デプロイ結果 + 本番安定性レポート | deploy, infrastructure, observability-sre |
| L6 受入 | 要件リスト + 最終成果物 | 受入判定 | verification §14 |

## スキル群配置

### 要件検証スキル群
| スキル | パス | 説明 |
|--------|------|------|
| project-management | workflow/project-management | プロジェクト計画・進捗管理 |
| dev-policy | workflow/dev-policy | 開発方針策定 |
| estimation | workflow/estimation | 見積もり |
| tech-selection | advanced/tech-selection | 技術選定 |
| requirements-handover | workflow/requirements-handover | 要件未定義・引継ぎ |
| compliance | workflow/compliance | コンプライアンス・規制対応 |

### 設計検証スキル群
| スキル | パス | 説明 |
|--------|------|------|
| design-doc | workflow/design-doc | 設計書作成 |
| visual-design | common/visual-design | ビジュアルデザイン基礎（構図・配色・タイポグラフィ・余白・視線誘導） |
| design | common/design | UI/UXデザイン |
| ui | project/ui | UI設計 |
| db | project/db | DB設計 |
| coding | common/coding | コーディング規約 |
| refactoring | common/refactoring | リファクタリング |
| documentation | common/documentation | ドキュメント作成 |
| security | common/security | セキュリティ |
| i18n | advanced/i18n | 多言語対応 |

### API整合性スキル群 ★
| スキル | パス | 説明 |
|--------|------|------|
| api-contract | workflow/api-contract | APIコントラクト検証（L2.5作業スキル） |

### APIコントラクトスキル群
| スキル | パス | 説明 |
|--------|------|------|
| api | project/api | API設計 |
| external-api | advanced/external-api | 外部API連携 |
| ai-integration | advanced/ai-integration | AI統合 |

### 依存関係スキル群
| スキル | パス | 説明 |
|--------|------|------|
| dependency-map | workflow/dependency-map | 依存関係検証 |
| migration | advanced/migration | システム移行 |
| legacy | advanced/legacy | レガシーコード対応 |

### テスト検証スキル群
| スキル | パス | 説明 |
|--------|------|------|
| testing | common/testing | テスト作成 |
| quality-lv5 | workflow/quality-lv5 | テスト品質検証 |
| error-fix | common/error-fix | エラー修正 |
| performance | common/performance | パフォーマンス |
| code-review | common/code-review | コードレビュー |

### 運用検証スキル群
| スキル | パス | 説明 |
|--------|------|------|
| infrastructure | common/infrastructure | インフラ構築 |
| deploy | workflow/deploy | デプロイ・リリース |
| dev-setup | workflow/dev-setup | 開発環境構築 |
| incident | workflow/incident | 障害対応 |
| observability-sre | workflow/observability-sre | 監視・可観測性・SRE |
| postmortem | workflow/postmortem | インシデント振り返り |
| ide-tools | tools/ide-tools | IDE/AIツール・MCP |

### 横断スキル群
| スキル | パス | 説明 |
|--------|------|------|
| git | common/git | Git運用 |
| verification | workflow/verification | L1-L6検証 |
| adversarial-review | workflow/adversarial-review | AI対立的レビュー |
| context-memory | workflow/context-memory | AIコンテキスト・メモリ管理 |
| ai-coding | tools/ai-coding | AIコーディング |
| agent-teams | integration/agent-teams | Agent Teams 協調設計・レビュー |

## カテゴリ別スキル数

| カテゴリ | スキル数 |
|---------|---------|
| common | 12 |
| workflow | 17 |
| project | 3 |
| advanced | 6 |
| tools | 2 |
| integration | 1 |
| **合計** | **41** |

## 補完関係のスキルペア

| ペア | 関係性 |
|------|--------|
| testing / quality-lv5 | テスト作成 / テスト品質測定 |
| api / api-contract | API設計 / APIコントラクト検証 |
| design-doc / documentation | 設計書作成 / 一般ドキュメント |
| visual-design / design | ビジュアルデザイン基礎 / UI/UX心理学・ブランディング |
| visual-design / ui | ビジュアルデザイン理論 / UI実装 |
| design / ui | UI/UXデザイン / UI特化実装 |
| incident / postmortem | 障害対応 / 振り返り・再発防止 |
| observability-sre / infrastructure | 監視設計 / インフラ構築 |
| security / compliance | セキュリティ実装 / 規制対応 |
| agent-teams / adversarial-review | マルチエージェント検証 / 単一エージェント対立レビュー |
| agent-teams / ai-coding §4 | Agent Teams 協調 / Sub-agents 階層 |

## 廃止済みスキル

| スキル | 理由 |
|--------|------|
| architecture | 40%プレースホルダー → design-doc/designで代替 |
| orchestrator | 投機的CLI参照 → integration/agent-teams + tools/ai-codingで代替 |
| codex | 投機的+重複大 → ide-tools/ai-codingで代替 |
| vscode-plugins | ide-tools/references/ に統合 |

## メンテナンス指針

1. **スキル追加時**: SKILL_MAP.md を更新
2. **500行ルール**: 超える場合は references/ に分割
3. **重複防止**: 追加前に既存スキルとの重複を確認
4. **HELIXフォーマット**: metadata.helix_layer を必ず設定
5. **description品質**: 「〇〇関連タスク時に使用」は禁止。具体的な用途と提供内容を記載
6. **廃止スキル検出**: 追加・変更時に `rg -wn "orchestrator|architecture|codex|vscode-plugins" skills/` で廃止スキル名への参照残存を確認

# HELIX Skill Map

## 概要

HELIXフレームワーク用スキルの一覧と分類。

## オーケストレーションフロー

全タスクはこのフローに沿って実行する。各フェーズで `→` の右に示すスキルを Read してから作業する。

```
【企画】人間が要件提示
  ↓ → requirements-handover, estimation
【L1 要件定義】Opus: 要件を構造化、Haiku: 引継書に転記
  ↓ → design-doc, api, db, security
【L2 設計】Codex 5.3: 設計書作成（FE/BE/DB）
  ↓ → api-contract
【L2.5 API契約】Codex 5.3: OpenAPI仕様生成、型↔API↔DB整合性検証
  ↓ → dependency-map
【L3 依存関係】Codex 5.3: 依存マップ生成 → 実装順序決定
  ↓ → estimation §8-10
【L4 工程表】Codex 5.3: 工程表作成（難易度スコア・モデル割当・オーケストレーション込み）
  ↓ → ai-coding §4
【実装】Opus: 工程表に従いディスパッチ（自分で実装しない）
  │ Codex 5.3 → 設計→実装（一気通貫）
  │ Sonnet   → テスト・ドキュメント
  │ Codex 5.2 → 軽微修正
  │ Haiku    → 調査
  ↓ → verification, testing, quality-lv5
【検証】並列: L2/L2.5/L3/L4 検証（各レイヤー最大5ループ）
  ↓ → deploy, infrastructure, observability-sre
【L5 デプロイ】セキュリティスキャン + パフォーマンステスト
  ↓ → verification §14
【受入】要件引継書 ↔ 最終成果物の突合
  ↓
【人間】成果物確認 → 本番リリース承認
```

**フェーズ間ルール:**
- 各フェーズ完了前に次フェーズに進まない
- 検証不合格 → レイヤー内ループ（5回）→ 上位層エスカレ → 人間
- Opus は自分で実装しない（CLAUDE.md 外注ルール参照）
- L2-L4 フェーズは Codex 5.3 固定。実装フェーズのみ難易度スコアで 5.2/5.3 を分ける（CLAUDE.md §モデル割当）
- 小〜中規模タスクは全フェーズを踏む必要はない（下記の決定木に従う）

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
├─ S（小規模）
│   ├─ バグ修正 / リファクタリング → 【実装】のみ
│   ├─ 新規小機能（単一画面・単一API等）→ 【L2 設計】→【実装】→【検証】
│   └─ ドキュメント / 設定変更 → 【実装】のみ
│
├─ M（中規模）
│   ├─ API変更なし → 【L2 設計】→【実装】→【検証】
│   ├─ API変更あり → 【L2 設計】→【L2.5 API契約】→【実装】→【検証】
│   └─ 新規モジュール → 【L1 要件】→【L2 設計】→【L2.5】→【実装】→【検証】
│
└─ L（大規模）
    └─ フルフロー: 【L1】→【L2】→【L2.5】→【L3】→【L4】→【実装】→【検証】→【L5】→【受入】
```

**スキップ不可条件**（サイズに関わらずフルフロー強制）:
- 外部API連携の新規追加
- 認証・認可ロジックの変更
- 課金・決済関連
- 個人情報の取り扱い変更
- 複数リポジトリ / チームに影響

## フェーズ別 I/O サマリー

各フェーズの入出力と読み込むスキル。詳細は `ai-coding/references/orchestration-workflow.md` を参照。

| フェーズ | 入力 | 出力 | スキル |
|---------|------|------|--------|
| L1 要件 | ユーザー要求 | 要件リスト + 仮定一覧 | requirements-handover, estimation |
| L2 設計 | 要件リスト | 設計書（画面/API/DB） | design-doc, api, db, security |
| L2.5 API契約 | 設計書 | OpenAPI仕様 + 型定義 | api-contract |
| L3 依存関係 | 設計書 + API仕様 | 依存マップ + 実装順序 | dependency-map |
| L4 工程表 | 依存マップ | 工程表（ID/タスク/難易度/担当/スキル） | estimation §8-10 |
| 実装 | 工程表 + 設計書 | 実装コード + テスト | ai-coding §4 |
| 検証 | 実装コード | 検証レポート（L2-L5各層） | verification, testing, quality-lv5 |
| L5 デプロイ | 検証済みコード | デプロイ結果 | deploy, infrastructure |
| 受入 | 要件リスト + 最終成果物 | 受入判定 | verification §14 |

## レイヤー別スキル配置

### L1: 要件検証レイヤー
| スキル | パス | 説明 |
|--------|------|------|
| project-management | workflow/project-management | プロジェクト計画・進捗管理 |
| dev-policy | workflow/dev-policy | 開発方針策定 |
| estimation | workflow/estimation | 見積もり |
| tech-selection | advanced/tech-selection | 技術選定 |
| requirements-handover | workflow/requirements-handover | 要件未定義・引継ぎ |
| compliance | workflow/compliance | コンプライアンス・規制対応 |

### L2: 設計検証レイヤー
| スキル | パス | 説明 |
|--------|------|------|
| design-doc | workflow/design-doc | 設計書作成 |
| design | common/design | UI/UXデザイン |
| ui | project/ui | UI設計 |
| db | project/db | DB設計 |
| coding | common/coding | コーディング規約 |
| refactoring | common/refactoring | リファクタリング |
| documentation | common/documentation | ドキュメント作成 |
| security | common/security | セキュリティ |
| i18n | advanced/i18n | 多言語対応 |

### L2.5: API整合性レイヤー ★
| スキル | パス | 説明 |
|--------|------|------|
| api-contract | workflow/api-contract | APIコントラクト検証（L2.5作業スキル） |

### L3: APIコントラクトレイヤー
| スキル | パス | 説明 |
|--------|------|------|
| api | project/api | API設計 |
| external-api | advanced/external-api | 外部API連携 |
| ai-integration | advanced/ai-integration | AI統合 |

### L4: 依存関係レイヤー
| スキル | パス | 説明 |
|--------|------|------|
| dependency-map | workflow/dependency-map | 依存関係検証 |
| migration | advanced/migration | システム移行 |
| legacy | advanced/legacy | レガシーコード対応 |

### L5: テスト検証レイヤー
| スキル | パス | 説明 |
|--------|------|------|
| testing | common/testing | テスト作成 |
| quality-lv5 | workflow/quality-lv5 | テスト品質検証 |
| error-fix | common/error-fix | エラー修正 |
| performance | common/performance | パフォーマンス |
| code-review | common/code-review | コードレビュー |

### L6: 運用検証レイヤー
| スキル | パス | 説明 |
|--------|------|------|
| infrastructure | common/infrastructure | インフラ構築 |
| deploy | workflow/deploy | デプロイ・リリース |
| dev-setup | workflow/dev-setup | 開発環境構築 |
| incident | workflow/incident | 障害対応 |
| observability-sre | workflow/observability-sre | 監視・可観測性・SRE |
| postmortem | workflow/postmortem | インシデント振り返り |
| ide-tools | tools/ide-tools | IDE/AIツール・MCP |

### All Layers（横断）
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
| common | 11 |
| workflow | 17 |
| project | 3 |
| advanced | 6 |
| tools | 2 |
| integration | 1 |
| **合計** | **40** |

## 補完関係のスキルペア

| ペア | 関係性 |
|------|--------|
| testing / quality-lv5 | テスト作成 / テスト品質測定 |
| api / api-contract | API設計 / APIコントラクト検証 |
| design-doc / documentation | 設計書作成 / 一般ドキュメント |
| design / ui | システム設計 / UI特化設計 |
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

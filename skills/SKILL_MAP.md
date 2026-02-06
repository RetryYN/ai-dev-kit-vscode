# HELIX Skill Map

## 概要

HELIXフレームワーク用スキルの一覧と分類。

## レイヤー別スキル配置

### L1: 要件検証レイヤー
| スキル | パス | 説明 |
|--------|------|------|
| project-management | workflow/project-management | プロジェクト計画・進捗管理 |
| dev-policy | workflow/dev-policy | 開発方針策定 |
| estimation | workflow/estimation | 見積もり |
| tech-selection | advanced/tech-selection | 技術選定 |
| requirements-handover | workflow/requirements-handover | 要件未定義・引継ぎ |
| compliance | workflow/compliance | コンプライアンス・規制対応 **[NEW-P2]** |

### L2: 設計検証レイヤー
| スキル | パス | 説明 |
|--------|------|------|
| design-doc | workflow/design-doc | 設計書作成 |
| architecture | project/architecture | アーキテクチャ設計 |
| design | common/design | 基本設計 |
| ui | project/ui | UI設計 |
| db | project/db | DB設計 |
| coding | common/coding | コーディング規約 |
| refactoring | common/refactoring | リファクタリング |
| documentation | common/documentation | ドキュメント作成 |
| security | common/security | セキュリティ |
| i18n | advanced/i18n | 多言語対応 |

### L3: APIコントラクトレイヤー
| スキル | パス | 説明 |
|--------|------|------|
| api | project/api | API設計 |
| api-contract | workflow/api-contract | APIコントラクト検証 **[NEW]** |
| external-api | advanced/external-api | 外部API連携 |
| ai-integration | advanced/ai-integration | AI統合 |

### L4: 依存関係レイヤー
| スキル | パス | 説明 |
|--------|------|------|
| dependency-map | workflow/dependency-map | 依存関係検証 **[NEW]** |
| migration | advanced/migration | システム移行 |
| legacy | advanced/legacy | レガシーコード対応 |

### L5: テスト検証レイヤー
| スキル | パス | 説明 |
|--------|------|------|
| testing | common/testing | テスト作成 |
| quality-lv5 | workflow/quality-lv5 | テスト品質検証 **[NEW]** |
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
| observability-sre | workflow/observability-sre | 監視・可観測性・SRE **[NEW-P2]** |
| postmortem | workflow/postmortem | インシデント振り返り **[NEW-P2]** |
| ide-tools | tools/ide-tools | IDE/AIツール |
| vscode-plugins | tools/vscode-plugins | VSCodeプラグイン |

### All Layers（横断）
| スキル | パス | 説明 |
|--------|------|------|
| git | common/git | Git運用 |
| verification | workflow/verification | L1-L6検証 |
| adversarial-review | workflow/adversarial-review | AI対立的レビュー |
| context-memory | workflow/context-memory | AIコンテキスト・メモリ管理 **[NEW-P2]** |
| orchestrator | integration/orchestrator | マルチエージェント |
| codex | integration/codex | Codex 5.3連携 |
| ai-coding | tools/ai-coding | AIコーディング |

## カテゴリ別スキル数

| カテゴリ | スキル数 |
|---------|---------|
| common | 11 |
| workflow | 18 |
| project | 4 |
| advanced | 6 |
| integration | 2 |
| tools | 3 |
| **合計** | **44** |

## 新規追加スキル（P1）

1. **api-contract** - APIコントラクト検証（L3）
2. **verification** - L1-L6検証レイヤー（all）
3. **requirements-handover** - 要件未定義・引継ぎ（L1）
4. **dependency-map** - 依存関係検証（L4）
5. **quality-lv5** - テスト品質検証（L5）

## 新規追加スキル（P2）

1. **observability-sre** - 監視・可観測性・SRE（L6）
2. **compliance** - コンプライアンス・規制対応（L1）
3. **context-memory** - AIコンテキスト・メモリ管理（all）
4. **postmortem** - インシデント振り返り（L6）

## 補完関係のスキルペア

| ペア | 関係性 |
|------|--------|
| testing / quality-lv5 | テスト作成 / テスト品質測定 |
| api / api-contract | API設計 / APIコントラクト検証 |
| design-doc / documentation | 設計書作成 / 一般ドキュメント |
| ide-tools / vscode-plugins | AIツール比較 / VSCode拡張設定 |
| design / ui | システム設計 / UI特化設計 |
| incident / postmortem | 障害対応 / 振り返り・再発防止 |
| observability-sre / infrastructure | 監視設計 / インフラ構築 |
| security / compliance | セキュリティ実装 / 規制対応 |

## 廃止検討スキル

現時点で廃止推奨のスキルはなし。tools/* カテゴリは開発環境構築時に有用であり維持。

## メンテナンス指針

1. **スキル追加時**: SKILL_MAP.md を更新
2. **500行ルール**: 超える場合は references/ に分割
3. **重複防止**: 追加前に既存スキルとの重複を確認
4. **HELIXフォーマット**: metadata.helix_layer を必ず設定

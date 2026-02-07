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

### L3: APIコントラクトレイヤー
| スキル | パス | 説明 |
|--------|------|------|
| api | project/api | API設計 |
| api-contract | workflow/api-contract | APIコントラクト検証 |
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

## カテゴリ別スキル数

| カテゴリ | スキル数 |
|---------|---------|
| common | 11 |
| workflow | 17 |
| project | 3 |
| advanced | 6 |
| tools | 2 |
| **合計** | **39** |

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

## 廃止済みスキル

| スキル | 理由 |
|--------|------|
| architecture | 40%プレースホルダー → design-doc/designで代替 |
| orchestrator | 投機的CLI参照 → ide-tools/ai-codingで代替 |
| codex | 投機的+重複大 → ide-tools/ai-codingで代替 |
| vscode-plugins | ide-tools/references/ に統合 |

## メンテナンス指針

1. **スキル追加時**: SKILL_MAP.md を更新
2. **500行ルール**: 超える場合は references/ に分割
3. **重複防止**: 追加前に既存スキルとの重複を確認
4. **HELIXフォーマット**: metadata.helix_layer を必ず設定
5. **description品質**: 「〇〇関連タスク時に使用」は禁止。具体的な用途と提供内容を記載

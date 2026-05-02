# .helix/patterns/

> HELIX のチーム共有固定ルール群を保持するディレクトリ。
> .gitignore からは allowlist で除外対象から外している。

## 配置ファイル

| ファイル | 正本 PLAN | 用途 |
|---|---|---|
| `pattern.yaml` | PLAN-006 §3.3 | ドキュメント駆動メタフェーズの pattern 適用ルール (固定 + llm-suggest) |
| `verify-tools.yaml` | PLAN-010 §3.1.1 | 検証ツール選定の固定ルールソース (harvest 最優先) |

## 運用原則

- pattern.yaml / verify-tools.yaml は **チーム共通の固定ルール** であり、Git で追跡する。
- プロジェクト固有の調整は `.helix/research/<id>/` に研究レポートとして保存する (gitignore 対象)。
- pattern engine / verify-agent はまず本ディレクトリの固定ルールを最優先で評価する。
- llm-suggest や WebSearch 由来の動的提案は固定ルールに対する補助として扱う。

## schema 正本

各 yaml の最小 schema は対応 PLAN を参照すること:

- pattern.yaml: PLAN-006 §3.3.1 / §3.3.2 / §3.3 scope の phase / gate / subphase 契約
- verify-tools.yaml: PLAN-010 §3.1.1 (template + schema + fallback)

## 作成タスク

- pattern.yaml: PLAN-006 Sprint L2 で実装 (現状は本 README + template)
- verify-tools.yaml: PLAN-010 Sprint L1 で実装 (現状は本 README + template)

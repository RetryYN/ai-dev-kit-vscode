# agent-skills vendor vs core 判断詳細化（PM 仕様案）

最終更新: 2026-05-14

作成: Docs（テクニカルライター）

対象: `agent-skills-vendor-plan` 判定（Phase 1）

関連: `docs/v2/A-audit/folder-structure-audit.md §6` / `docs/v2/A-audit/audit-summary.md §6` / `docs/v2/A-audit/skill-quality-audit.md`

---

## 1. 目的

`skills/agent-skills/` を現状維持のまま継続するか、上流との分離（vendor 化）と HELIX 独自 skill の core 化を組み合わせるかを、PM 承認用に判断しやすい形で提示する。

本書は、実装ではなく判断・準備向けの文書であり、物理移動は PM 承認後に実施する。

## 2. 現状整理（監査入力の要約）

### 2.1 事実（監査結果）

- `skills/agent-skills/` は現在 23 技能。
- 内訳は `上流由来 19 + HELIX 独自 4（system-design-sizing / technical-writing / mock-driven-development / helix-scrum）`。
- 現在は `skills/{category}/` と同列で管理され、以下の課題が顕在化:
  - 上流更新取り込み手順の定義欠如
  - HELIX 独自 4 と上流 19 の境界不明瞭
  - カタログ上の「上流由来 / HELIX 独自」表示が曖昧
- `skills/SKILL_MAP.md` の 2026-04-22 追記では「`agent-skills` 25 skill」の整理経緯が記録されており、カテゴリの混在が設計上の懸念として認識されている。

### 2.2 監査上の示唆

- `folder-structure-audit.md` §6 は `skills/agent-skills` を **PM top-3** のうち 2 位に挙げ、構造統合判断が Phase 2 進行前提となっている。
- `audit-summary.md` §4 は同テーマを DR-010 系として扱い、選択肢のうち「部分分離+上流追跡」を高めに扱う方向性が示されている。
- `skill-quality-audit.md` では frontmatter 不整合の集中が見られる領域として `agent-skills` が挙がっており、上流 19 / HELIX独自 4 の管理境界を明確化する設計が重要。

## 3. 用語定義（判断前提）

### 3.1 vendor 定義

- 第三者資産を別取り込みとして扱い、原本管理（upstream）と差分適用を明示する。
- 選択肢としてはサブモジュール化・別フォルダ化・vendor フラグ付けなど、物理分離または概念分離の両方を含む。

### 3.2 core 定義

- HELIX が継続的に保守する実装資産。リリースや契約決定の一次責任を持つ。
- 上流更新を取り込む前提で変化し、HELIX 仕様として統合される。

### 3.3 HELIX 独自 4 のコア化

- `system-design-sizing`, `technical-writing`, `mock-driven-development`, `helix-scrum` を `skills/workflow/`、`skills/common/`、`skills/tools/` 等の既存カテゴリへ移す。
- `agent-skills` は upstream 由来の境界群として扱う。

## 4. 比較前提（評価軸）

本判定は以下 4 軸で比較する。

1. **上流追跡性**
2. **構造シンプル性**
3. **ライセンス/出典の追跡性**
4. **catalog / skill 使用統計の再計測難度**

加えて、.claude-plugin 市場・ marketplace（`docs/agent-skills/README.md` の手順）を含めた配布・更新影響も追記する。

## 5. 選択肢比較（4案）

| 選択肢 | 概要 | メリット | デメリット | 上流追跡 | 構造シンプル性 | ライセンス追跡 | 実装コスト | .claude-plugin 影響 | 推奨度 |
|---|---|---|---|---:|---:|---:|---:|---|---|
| (a) 完全 vendor 化 | `skills/agent-skills/` を upstream submodule 化し、HELIX 独自 4 を core へ移動 | 上流差分取り込みが最短経路で機械化できる | submodule 運用コスト、差分当て作業が増える。日本語ローカライズ差分の維持が必要 | 5 | 3 | 5 | 4 | 5 | 中 |
| (b) 部分 vendor 化（推奨） | 上流 19 を `vendor/agent-skills-upstream/` read-only で保持し、HELIX 独自 4 を core へ移動。差分は `patches/` 管理 | 上流追跡と統合運用のバランスが取りやすい | patch 運用の管理負荷 | 5 | 4 | 5 | 3 | 4 | **高** |
| (c) 現状維持 + metadata 管理 | 物理移動なし。SKILL.md に `upstream: addyosmani/agent-skills` または `upstream: helix` を明示 | 実行コストが最も低い | 上流取り込みは基本 manual | 2 | 5 | 3 | 1 | 2 | 中 |
| (d) 完全 core 化 | 全 23 を HELIX core として吸収 | 単純な見た目構造、運用ルールが簡素 | upstream 更新不能、由来情報の消失 | 1 | 5 | 2 | 2 | 2 | 低 |

## 6. 推奨判断

**(b) 部分 vendor 化**を推奨する。

判断理由:

1. 上流追跡を維持しながら、HELIX 独自 4 を明確に core 化できる。
2. `skills/SKILL_MAP.md` の履歴と整合する「上流 19 / HELIX 独自4」境界を明示可能。
3. 完全 submodule 化に比べ、導入時の運用破壊を抑えやすい。
4. 現状維持案より、skill カタログの用途別運用が明確化し、PM 監査観点で説明可能。

## 7. 推奨案の実装 step（PM 向け詳細）

### Step 1: 取得形態の固定（構想）

- `vendor/agent-skills-upstream/` を新設。
- 取り込み元を `addyosmani/agent-skills`（MIT）に固定。
- 将来更新時の `git submodule` 更新または fetch pin 方針を決める。

実施成果物:

- 取得手順（`skills/agent-skills` からの抽出手順
- pin 方針（SHA/タグの固定、更新頻度、レビュー担当）

### Step 2: patch 管理の規約化

- `skills/agent-skills/` 配下に残る差分を `patches/` に統合。
- 差分対象:
  - 日本語化
  - HELIX 連携（`references/` / `hooks/` / `.claude-plugin` 参照の補正）
  - HELIX での実運用補助文言

実施成果物:

- `patches/agent-skills/` 方針（ファイル名規約、差分適用順、revert 手順）
- 差分品質基準（README / metadata / hook 参照）

### Step 3: `skills/agent-skills/` を symlink / 参照再構成

- `skills/agent-skills/` は upstream mirror または wrapper（運用方式）として再構成。
- 上流 19 と HELIX 独自 4 を明確に分離。
- 既存 import / catalog 参照は最短で壊れない形で維持。

実施成果物:

- symlink 方針（or shim policy）
- 呼び出し先変換マップ（`agent-skills/<skill>` → `vendor/*` or `workflow/*`）

### Step 4: HELIX 独自 4 の core 移設

- `system-design-sizing`：既存カテゴリへ昇格（L2-L3 主体）
- `technical-writing`：`skills/common/` 相当への昇格（L2-L8）
- `mock-driven-development`：`skills/workflow/` or `skills/advanced/` 親脈で昇格
- `helix-scrum`：既存 `workflow/agile`/`workflow/` 連携カテゴリへ吸収または新設

実施成果物:

- `SKILL_MAP.md` 更新（旧位置と新位置の追跡）
- 既存 ID 変更時の alias 定義（catalog backward compatibility）

### Step 5: SKILL_MAP / catalog 同期

- `skills/SKILL_MAP.md` を更新し、所属変更・upstream由来フラグを明示。
- `helix skill catalog rebuild` による catalog 再生成（`skills/*/SKILL.md` と前提ブロックの整合確認）。

実施成果物:

- 更新後 SKILL_MAP diff
- catalog 再生成結果の確認ログ（`skill_usage` スキーマ非接続時の注記含む）

### Step 6: marketplace / plugin 経路の検証

- `.claude-plugin/` 経路に対する影響を確認。
- `docs/agent-skills/README.md` のインストール手順との整合を再確認。
- 既存ユーザ install に影響が出る場合は告知文言を追加。

実施成果物:

- install smoke test（README手順、plugin install、既存コマンド再現）
- 変更時の既知制約リスト（再起動/再インストール要否）

## 8. Step 6 以降の実装ロック条件

推奨案を PM 承認後に進める前提で、次を満たす条件を採用する。

1. ライセンス情報（MIT）と upstream 版 metadata の整合を明文化。
2. submodule / vendor 方式を採る場合の更新フロー（更新担当・レビュー担当・差分衝突時のロールバック）を明示。
3. カタログ/検索/marketplace への影響を段階テストで検証。

該当条件が満たされない場合は物理移動を停止し、文書上の「pending」に留保する。

## 9. 影響範囲（実行可視化）

- **直結ファイル**: `skills/SKILL_MAP.md`, `.claude-plugin/*`, `skills/**`, `docs/agent-skills/README.md`, `docs/agent-skills/skill-anatomy.md`, `docs/v2/C-followup/*`
- **間接影響**: `helix skill catalog rebuild` 結果、`skill_usage` 集計、`helix skill chain` 推奨結果
- **運用影響**:
  - 既存ユーザーの `addon/plugin` 更新ルート
  - 新規導線向けの `agent-skills` 解決順
  - 監査時の audit-summary 追記

## 10. 比較結果の要約（PM 決裁向け）

- **採択推奨**: (b)
- **採択しない場合の懸念**:
  - (c) のみ採択なら、短期は低コストでも中長期で上流 drift が増加
  - (d) は統一感は出るが、規約起点（上流/ライセンス/更新経路）が失われ監査再開時の追跡が困難
- **運用上の制約**:
  - 物理移動は read-only 承認済みの実装タスクでのみ実施
  - 現在は判断文書として完成し、実装は別承認フェーズで実施

## 11. ガバナンス要件（監査とレビュー）

### 11.1 ドキュメント更新ルール

- `skills/agent-skills/` と `.claude-plugin/` の境界変更は `docs/v2/C-followup` に反映。
- `agent-skills-vendor-plan.md` は判定更新が生じた場合に追記。

### 11.2 証跡要件

- 変更前後の catalog 差分
- `SKILL_MAP.md` の行差分
- marketplace/README 手順の検証ログ

### 11.3 運用上の監査コスト

- メリット: 上流 19 と HELIX 独自 4 の境界が固定化されるため、将来の監査時コストが低下。
- デメリット: `patches/` 管理と更新衝突吸収の運用負荷は増える。

## 12. 受け入れ条件（この判断案の完了条件）

- PM が (b) を承認し、`vendor/` 方針を含む実装タスクに移行する。
- 承認後に、`skills/SKILL_MAP.md` と catalog 再生成を実施できる。
- `.claude-plugin` / `docs/agent-skills` の更新が同居できることを確認する。

## 13. リスク・未解決事項

- `docs/agent-skills/README.md` の marketplace 手順と、本体で採用する vendor 方式との差分吸収が必要。
- upstream の更新速度次第で、`patches/` の継続的メンテが人力化する。
- symlink / submodule 運用時の環境依存（CI とローカル）差異。

## 14. 参照リンク

- `docs/v2/A-audit/skill-quality-audit.md`
- `docs/v2/A-audit/folder-structure-audit.md`
- `docs/v2/A-audit/audit-summary.md`
- `skills/SKILL_MAP.md`
- `docs/agent-skills/README.md`
- `docs/commands/index.md`
- `docs/commands/ai-harness.md`
- `helix/HELIX_CORE.md`
- `helix/CODEX_TL_MODE.md`


---
name: ai-coding
description: AIツール活用で構造化プロンプトテンプレート・マルチエージェント人事配置戦略・出力レビューチェックリストを提供
metadata:
  helix_layer: all
  triggers:
    - AIコーディング支援時
    - プロンプト最適化時
  verification:
    - "AI生成コード: lint + type-check 0 errors"
    - "AI生成コード: 既存テスト全通過"
    - "プロンプトにコンテキスト（ファイルパス・仕様）含む"
compatibility:
  claude: true
  codex: true
---

# AIコーディングスキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- AIツールを使った開発時
- プロンプト作成時
- AI出力のレビュー時

---

## 1. AIコーディングの原則

### 基本姿勢

```
AIは「ジュニア開発者」と考える:
- 指示は具体的に
- 出力は必ず確認
- 全体設計は人間が行う
- 細部の実装をAIに任せる
```

### やるべきこと

```
✅ 明確な指示を出す
✅ コンテキストを十分に与える
✅ 出力をレビューする
✅ テストで検証する
✅ 段階的にタスクを進める
```

### やってはいけないこと

```
❌ 出力を鵜呑みにする
❌ 曖昧な指示で期待する
❌ 一度に大量のタスクを依頼
❌ レビューなしでマージ
❌ テストなしでデプロイ
```

---

## 2. 効果的なプロンプト

→ 詳細は `references/prompt-templates.md` を参照（構造化プロンプト・テンプレート・良い例/悪い例）

---

## 3. コンテキスト管理

### 効果的なコンテキスト

```markdown
# プロジェクト概要
このプロジェクトは〇〇のためのWebアプリです。

# 技術スタック
- Frontend: Next.js 14, TypeScript, Tailwind
- Backend: FastAPI, Python 3.12
- DB: PostgreSQL 16, Prisma
- Auth: JWT + Refresh Token

# ディレクトリ構造
src/
├── app/          # Next.js App Router
├── components/   # Reactコンポーネント
├── lib/          # ユーティリティ
└── api/          # APIクライアント

# コーディング規約
- 型は厳格に（anyは禁止）
- 関数は20行以内
- テストは必須
```

### コンテキストの与え方

```
1. CLAUDE.md に基本情報を記載
2. タスクごとに関連ファイルを @mention
3. 必要な仕様を都度提供
4. 前提知識は省略せず明示
```

---

## 4. マルチエージェント戦略

### エージェント人事配置

> モデル割当・ロール別責務の詳細は `references/workflow-core.md §モデル割当テーブル` を参照。

### フェーズ別フロー

```
【設計】Opus が言語化 → Codex 5.4 がレビュー → 合意
            ↓ ← codex exec -m gpt-5.4（設計レビュー）: G2（設計凍結）
            ↓ ← codex exec -m gpt-5.4（API契約レビュー）: G3（実装着手 / API契約レビュー）
【実装】Codex 5.3 が設計から実装まで一気通貫で実行
            │ ← codex review（軽量: Critical/High のみ）: 実装.2（5.4 レビュー）
            │ ← codex review（フル品質）: 実装.5（5.4 レビュー）
            ↓ ← codex review --uncommitted: G4（実装凍結）
【品質アップ】Codex 5.4 がリファクタ・清書・FEデザイン清書
【ビジュアル】visual-design に基づくデザイン適用・調整
            ↓ ← codex review --uncommitted: G5（デザイン凍結）
【修正】エラー少 → Codex 5.3 Spark / エラー多 → Codex 5.3 → さらに多発は 5.4
            ↓
【テスト】Sonnet がテストコード作成・実行
            ↓
【ドキュメント】Sonnet が設計書・仕様書を実装結果に合わせて更新
            ↓
【調査】Haiku 4.5 が随時、情報収集・下調べを担当
```

### 実装フェーズ内ゲート（implementation-gate: 実装.1〜.5）（必須・スキップ不可）

#### 位置づけ（本文 / references の切り分け）
- この節は「実装フェーズは必ず implementation-gate（実装.1〜.5）で進める」ことだけを規定する（運用の宣言と入口）。
- **実装.1〜.5 の定義（目的/通過条件/失敗時アクション/推奨出力フォーマット）は `references/implementation-gate.md` を正**とし、本文では繰り返さない（仕様の単一ソース化）。
- **タスク配送・I/O 仕様・引継ぎプロトコル**は `references/orchestration-workflow.md` の責務（本節では扱わない）。
- **階層間ゲート（L1〜L4 間の遷移/ゲート判定/差し戻し）**は `references/layer-interface.md` の責務（本節では扱わない）。

#### 5階層概要（実装.1〜.5）
| ゲート | 目的（要約） | 詳細 |
|---|---|---|
| 実装.1 | コード調査（.1a）+ 変更計画（.1b）：既存コードを読んでから計画を固定 | `references/implementation-gate.md` |
| 実装.2 | 最小実装（動作を通すための骨格を先に作る） | `references/implementation-gate.md` |
| 実装.3 | 安全性・互換性（破壊変更や回帰を潰す） | `references/implementation-gate.md` |
| 実装.4 | テスト・検証（テストで仕様を固定） | `references/implementation-gate.md` |
| 実装.5 | 仕上げ（レビュー観点とドキュメント整合） | `references/implementation-gate.md` |

#### 強制フロー（ゲートは順番固定）
- 実装作業は **実装.1 → .2 → .3 → .4 → .5** の順に進める（**スキップ不可 / 先送り不可**）。
- 各ゲート完了時は、ゲート状態（gate_status）として `passed | failed | blocked | interrupted` を明示して返す（フォーマット詳細は `references/implementation-gate.md`）。
- `passed | failed | blocked | interrupted` は **ゲート判定の status** であり、工程表タスクの status（オーケストレーター管理）と混同しない。
- `failed` は原則「同一ゲート内で修正して再判定」。`blocked` は「前提不足/仕様不明」として停止し、オーケストレーターへ報告する（配送・ステータス運用は `references/orchestration-workflow.md`）。
- `interrupted` は「前提崩壊/範囲再定義（IIP発動）」。**リトライカウントに含めない**。影響度分類（P0〜P3）は `references/implementation-gate.md` の IIP セクションに従う。
- 実装中に上位層（例: L2/L3）へ戻す必要が出た場合の **判断トリガー（いつ戻すか）** は `references/layer-interface.md` に従う（本節では規定しない）。
- 上位層へ差し戻す場合の **手順（何を添えて誰に返すか）** は `references/layer-interface.md` に従う（本節では規定しない）。

#### TodoWrite 強制（5ゲートをチェックリスト化）
- 実装タスクを受けたら、必ず次の **5 行を TodoWrite（チェックリスト）として先に書く**（「やること」の欠落防止）。
- 進捗更新は **ゲートごとに即時反映**し、まとめて更新しない（未完了ゲートが残ったまま完了扱いにしない）。
- すでに同等の「実装.1〜.5」チェックリストが存在する場合は **二重に書かず既存を採用**し、それを更新する（二重管理防止）。
- ユーザー/運用制約で TodoWrite（チェックリスト先出し）が禁止・拒否された場合は **実装開始せず status: blocked** として理由を返す（強制フロー崩壊防止）。
- チェックリストは **ゲート進捗（☑=passed）** にのみ使い、`failed/blocked` 等の status をチェック項目名に混ぜない（ゲート/タスクstatus混同防止）。

- [ ] 実装.1: コード調査（.1a）+ 変更計画（.1b）
- [ ] 実装.2: 最小実装（骨格を通し、残件を列挙）
- [ ] 実装.3: 安全性・互換性（回帰/破壊変更/リスク潰し）
- [ ] 実装.4: テスト・検証（テスト or 手順で仕様固定）
- [ ] 実装.5: 仕上げ（レビュー観点 + ドキュメント整合）

### 呼び出し方

```bash
# Codex 5.4: 設計レビュー・コードレビュー・品質アップ・トラブルシュート
codex exec "レビュー: X feature の設計書" -m gpt-5.4
codex review --uncommitted      # コードレビュー

# Codex 5.3: 実装メイン（スコア4+）
codex exec "Implement X feature based on design docs" -m gpt-5.3-codex

# Codex 5.3 Spark: 軽量実装・軽微修正
codex exec "Fix lint errors in src/..." -m gpt-5.3-codex-spark

# Codex 5.2: 大規模コード精読・スキャン
codex exec "精読: src/ 配下の認証関連コードを列挙" -m gpt-5.2-codex

# Sonnet: テスト・ドキュメント
Task(model: "sonnet", prompt: "Write tests for ...")
Task(model: "sonnet", prompt: "Update design-doc with ...")

# Haiku 4.5: リサーチ
Task(model: "haiku", prompt: "Search for ... and summarize")
```

### 使い分けの判断基準

```
タスクの種類は？
├── 設計を詰める → Opus（言語化）+ Codex 5.4（エンジニアレビュー）
├── 設計書・仕様書をレビューする → Codex 5.4（codex exec "レビュー"）
├── コード実装（スコア4+）→ Codex 5.3（codex exec -m gpt-5.3-codex）
├── 軽量実装・軽微修正（スコア1-3）→ Codex 5.3 Spark（codex exec -m gpt-5.3-codex-spark）
│   └── エラー多発 → Codex 5.3 にエスカレ → さらに多発なら 5.4
├── 大規模コード精読・スキャン → Codex 5.2（codex exec -m gpt-5.2-codex）
├── コードをレビューする → Codex 5.4（codex review --uncommitted）
│   └── 低リスク（S + セキュリティゲート非該当）→ Codex 5.3 が一次レビュー可
├── 品質アップ（リファクタ・清書）→ Codex 5.4（codex exec -m gpt-5.4）
├── トラブルシューティング → Codex 5.4（常に。1Mコンテキストで最強）
├── プラン・方針を壁打ちする → Codex 5.4（codex exec "TL壁打ち"）
├── FEデザイン → Sonnet（初稿）→ Codex 5.4（清書）
├── テストを書く → Sonnet（Task tool）
├── ドキュメントを更新する → Sonnet（Task tool）
├── リサーチ → Haiku 4.5（Task tool。Web検索・先行事例調査特化）
└── ビジネス判断 → Opus（自分）
```

### トークン配分

```
Opus:   10%（言語化・ビジネス判断）
Codex 5.4:  20%（設計レビュー・コードレビュー・品質アップ・トラブルシュート）
Codex 5.3:  35%（実装メイン）
Codex 5.3 Spark:  10%（軽量実装・軽微修正）
Codex 5.2:  5%（大規模コード精読・スキャン）
Sonnet: 15%（テスト・ドキュメント）
Haiku 4.5:  5%（リサーチ）

効果:
- Codex 5.3 が設計→実装を一気通貫 + Codex 5.4 がレビュー・品質アップ → 実装速度と品質の両立
- 修正サイクルが 3-5回 → 1-2回 に削減
- Sonnet はテスト・ドキュメントに専念 → 品質向上
```

### 複数エージェント協調（Agent Teams）

```
Sub-agents（上記）= 親子関係。実装の並列化に最適。
Agent Teams = 対等関係。設計の多角検証に最適。

判断:
- 実装タスク → Codex 5.4 / Codex 5.3（このセクション）
- 設計検証・アーキテクチャ決定 → Agent Teams
```

→ 詳細は `skills/integration/agent-teams/SKILL.md` を参照

### サブエージェント構成設定

工程表の各タスクに対して、スキル付与・ツール制限・思考トークンを事前設定する。

```
設定項目:
  スキル付与 — タスク種別からキーワードベースで自動推論
  ツール制限 — 最小権限の原則（読み取り専用タスクはEdit/Write/Bash禁止）
  思考トークン — 難易度スコアから自動設定（0-3→なし, 4-7→low, 8-10→medium, 11-14→high）
```

→ 詳細は `references/subagent-config.md` を参照

### オーケストレーション・ディスパッチ

Opus はオーケストレーターとして工程表を読み、タスクをサブエージェントに配送する。

```
ディスパッチフロー:
  1. 工程表の現在行を読み取る
  2. 前提工程の完了を確認（未完了→スキップ or ブロッカー報告）
  3. タスク種別からサブエージェントを選定（上記 subagent-config 参照）
  4. 入力を整形して Task tool で配送
  5. 出力を検証（status: completed/failed/blocked/partial）
  6. 次タスクの入力に変換して継続

Opus の自作業禁止（CLAUDE.md 参照）:
  - コード実装 → Codex 5.3 / Codex 5.3 Spark（常時委譲）
  - レビュー・品質アップ → Codex 5.4（常時委譲）
  - 大規模精読 → Codex 5.2（常時委譲）
  - テスト・ドキュメント → Sonnet（常時委譲）
  - 調査・検索 → Haiku 4.5（常時委譲）
  - 唯一の例外: MCP検証などツール動作確認と**フロント（デザイン含む）設計**のみ自分で実行可
```

→ 詳細は `references/orchestration-workflow.md` を参照

---

## 5. AIの出力レビュー

### 必ず確認すること

```
□ コードが動くか（実行確認）
□ 意図した動作か（仕様確認）
□ セキュリティリスクはないか
□ パフォーマンス問題はないか
□ 既存コードとの整合性
□ テストは十分か
```

### よくある問題

| 問題 | 対策 |
|------|------|
| 存在しないライブラリを使用 | インポートを確認 |
| 古いAPI/構文を使用 | ドキュメントと照合 |
| エラーハンドリング不足 | 異常系を追加指示 |
| 型が緩い（any多用） | 厳格な型を指示 |
| テスト不十分 | カバレッジ確認 |
| セキュリティ考慮不足 | セキュリティ観点を指示 |

### レビューチェックリスト

→ 詳細は `references/review-checklist.md` を参照

---

## 6. ツール別Tips・学習と改善

→ 詳細は `references/tool-tips.md` を参照（Claude Code / Copilot / Cursor Tips + プロンプト改善サイクル）

---

## 7. 事前調査・検索ルール（強制）

### 事前調査の強制条件

以下に該当する場合、設計（L2）・実装（L4）前に**必ず事前調査を実施**する。
詳細なゲート定義は `references/layer-interface.md §事前調査ゲート` を参照。

| 条件 | レベル |
|------|--------|
| 外部API連携（新規/変更） | **MUST** |
| 認証・認可ロジック | **MUST** |
| 新規ライブラリ/フレームワーク導入 | **MUST** |
| 技術選定（ADR対象） | **MUST** |
| メジャーアップグレード | **MUST** |
| 公開API/DB契約変更 | **MUST** |
| 決済・PII・法令影響 | **MUST** |
| 高負荷/並行性/移行（migration） | SHOULD |
| 純粋な内部リファクタリング/バグ修正 | 不要 |

### 検索の優先ソース（権威順）

| 優先度 | ソース | 信頼性 | ツール |
|--------|--------|--------|--------|
| 1 | 公式ドキュメント / RFC | 最高 | **Context7 MCP 優先** |
| 2 | GitHub Issues/Discussions（公式リポジトリ） | 高 | WebSearch / gh CLI |
| 3 | 技術ブログ（Qiita, Zenn, dev.to） | 中（要クロスチェック） | WebSearch |
| 4 | Stack Overflow | 中（回答の鮮度を確認） | WebSearch |

### 調査レポートフォーマット

```yaml
research_report:
  topic: "調査対象"
  date: "YYYY-MM-DD"
  sources:
    - url: "URL"
      summary: "1行要約"
      relevance: high/medium/low
  conclusion: "設計/実装への影響"
  adoption: "採用/不採用の理由"
  risks: ["発見したリスク"]
```

**通過条件**: 「検索した」ではなく「調査メモが存在する」こと
**記録先**: `docs/research/YYYY-MM-DD-{topic}.md`

### 制約

- **機密情報の外部検索持ち出し禁止**: 検索クエリに社内固有名・APIキー・顧客データを含めない
- **オフライン/検索不可時**: status: blocked として PM に報告（人間判断で代替手段を決定）

### 検索不要なケース

```
❌ 検索不要
- 基本的な構文
- 安定したライブラリの基本使用法
- プロジェクト内のコード
- 純粋な内部リファクタリング/バグ修正
```

### 検索指示の出し方

```
「〇〇について、2026年の最新情報を検索して実装して」
「〇〇の公式ドキュメントを確認して」（→ Context7 MCP を優先使用）
「〇〇のセキュリティベストプラクティスを検索して適用して」
```

---

## チェックリスト

### AI活用前

```
[ ] タスクの明確化
[ ] 必要なコンテキスト整理
[ ] 期待する出力の明確化
```

### AI活用中

```
[ ] 段階的に進める
[ ] 中間確認を行う
[ ] 軌道修正する
```

### AI活用後

```
[ ] 出力をレビュー
[ ] 動作確認
[ ] テスト実行
[ ] セキュリティ確認
```

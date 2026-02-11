---
name: context-memory
description: CLAUDE.md運用を含むAIコンテキスト管理・知識永続化の運用手順を提供
metadata:
  helix_layer: all
  triggers:
    - CLAUDE.md設計時
    - AIセッション管理時
    - コンテキスト最適化時
    - プロジェクト知識管理時
  verification:
    - "CLAUDE.md存在: CLAUDE.md or .claude/CLAUDE.md いずれかが存在する"
    - "CLAUDE.local.md: .gitignore に記載済み"
    - "セッション再開（初回免除）: MEMORY.md に前回の知見 1件以上 記載済み"
compatibility:
  claude: true
  codex: true
---

# コンテキスト・メモリスキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- CLAUDE.md / AGENTS.md の設計・改善時
- AIセッション間での知識引継ぎ設計時
- コンテキストウィンドウ最適化時
- プロジェクト知識ベース構築時

---

## 1. CLAUDE.md設計

### 1.1 設定の読み込み階層

#### settings 優先度（高→低）

| # | 種別 | パス | 用途 |
|---|------|------|------|
| 1 | Managed | `/etc/claude-code/managed-settings.json` | 組織ポリシー強制（IT管理者） |
| 2 | CLI引数 | `claude --flag` | セッション限りの一時上書き |
| 3 | Local | `.claude/settings.local.json` | 個人のマシン固有設定（gitignore） |
| 4 | Project | `.claude/settings.json` | チーム共有のプロジェクト設定 |
| 5 | User | `~/.claude/settings.json` | 個人の全プロジェクト共通設定 |

原則: **より限定的なスコープが優先**。Project で `deny` なら User の `allow` は無効。

#### CLAUDE.md の6種類

| # | 種別 | パス | 共有 | 読み込み |
|---|------|------|------|----------|
| 1 | Managed | `/etc/claude-code/CLAUDE.md` | 組織全体 | 常時（override不可） |
| 2 | Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | チーム（git管理） | 常時 |
| 3 | Rules | `./.claude/rules/*.md` | チーム（git管理） | 常時（モジュラー） |
| 4 | User | `~/.claude/CLAUDE.md` | 個人 | 常時 |
| 5 | Local | `./CLAUDE.local.md` | 個人（gitignore） | 常時 |
| 6 | Auto | `~/.claude/projects/<id>/memory/` | 個人 | MEMORY.md先頭200行のみ |

#### 探索ルール

```
■ 上方向再帰探索
  cwd → 親ディレクトリ → ... → ルート
  見つかった全ての CLAUDE.md / CLAUDE.local.md を読み込む
  例: foo/bar/ で起動 → foo/bar/CLAUDE.md と foo/CLAUDE.md 両方

■ 子ディレクトリ遅延読み込み
  cwd より下のCLAUDE.md は起動時に読み込まない
  AIがそのディレクトリのファイルにアクセスした時点で読み込み

■ @import 構文
  @path/to/file.md で外部ファイルを取り込み可能
  最大5ホップまで再帰（循環参照防止）
  相対パス（インポート元基準）/ 絶対パス / ~ パス 対応

■ モジュラールール (.claude/rules/)
  トピック別にファイル分割 → 全て自動読み込み
  paths フロントマターで適用範囲を glob 指定可能
```

### 1.2 設計指針

#### 階層ごとの役割分担

```
Managed policy    → セキュリティ・コンプライアンス（組織強制）
User CLAUDE.md    → 個人の好み（言語、回答スタイル、ショートカット）
Project CLAUDE.md → 技術スタック、チーム規約、ビルドコマンド
rules/*.md        → トピック別ルール（testing.md, security.md 等）
CLAUDE.local.md   → 個人のプロジェクト固有設定（gitignore対象）
Auto memory       → セッション中の学習（AIが自動管理）
```

#### 効果的な分割パターン

```
■ ディレクトリ階層
  CLAUDE.md（ルート）
  ├── 全体方針、技術スタック
  └── ディレクトリごとのCLAUDE.md
      ├── src/api/CLAUDE.md（API固有ルール）
      ├── src/components/CLAUDE.md（UI固有ルール）
      └── tests/CLAUDE.md（テスト規約）

■ rules/ 活用
  .claude/rules/
  ├── coding-style.md    ← 命名・フォーマット
  ├── testing.md         ← テスト規約
  ├── security.md        ← セキュリティルール
  └── review.md          ← レビュー基準

■ 更新タイミング
  - 新規ライブラリ導入時
  - アーキテクチャ変更時
  - 頻繁なAIミスの発見時（禁止事項に追加）
  - チーム規約変更時
```

#### アンチパターン

```
❌ 個人設定をProject CLAUDE.mdに記述 → CLAUDE.local.md へ
❌ 全階層で同じ内容を重複記述 → 上位階層で一度だけ定義
❌ 500行超えの巨大CLAUDE.md → references/ や @import で分割
❌ @import 4段以上のネスト → 構造を見直し
❌ 曖昧な指示（"Format properly"） → 具体的に（"2-space indent"）
```

### 1.3 構造テンプレート

```markdown
# プロジェクト名

## 概要
一文でプロジェクトを説明（例: "Next.js + Stripe のECアプリ"）

## 技術スタック
- Frontend: ...
- Backend: ...
- DB: ...
- インフラ: ...

## アーキテクチャ
主要コンポーネントと役割

## コーディング規約
- 命名: camelCase / snake_case
- テスト: 必須
- 型: strict

## ディレクトリ構造
src/
├── ...

## コマンド
- ビルド: `npm run build`
- テスト: `npm test`
- lint: `npm run lint`

## 禁止事項
- any型の使用
- console.log残し
- 未使用import

## ワークフロー
- タスクサイジング: SKILL_MAP.md §タスクサイジング 参照
- フェーズスキップ: SKILL_MAP.md §フェーズスキップ決定木 参照
- ディスパッチ: ai-coding/references/orchestration-workflow.md 参照
- サブエージェント: ai-coding/references/subagent-config.md 参照
```

### 1.4 Codex CLI（AGENTS.md）差分

```
このリポジトリでは CLAUDE.md -> AGENTS.md の symlink + sync-agents で同期。
基本は同一内容で運用し、以下の差分だけ意識する。
```

| 項目 | Claude Code | Codex CLI |
|------|-------------|-----------|
| 指示ファイル | `CLAUDE.md` | `AGENTS.md` |
| 個人上書き | `CLAUDE.local.md` | `AGENTS.override.md` |
| モジュラールール | `.claude/rules/*.md` | なし |
| 設定ファイル | `settings.json`（JSON） | `config.toml`（TOML） |
| サイズ制限 | トークン制限（実質） | `project_doc_max_bytes`（32KiB） |

```
実務ルール:
- "指示内容" は AGENTS.md（= CLAUDE.md と同文）に寄せる
- "実行ポリシー"（サンドボックス、承認、出力形式）は config.toml に寄せる
- 個人差分は AGENTS.override.md（gitignore推奨）
- Codex には rules/ や @import がないため、500行超えは references/ で対処
```

---

## 2. コンテキストウィンドウ管理

### トークン配分戦略

```
200Kコンテキストの推奨配分:

┌─────────────────────────────────────┐
│ System Prompt / CLAUDE.md  ~10K    │
├─────────────────────────────────────┤
│ スキルファイル             ~20K     │
├─────────────────────────────────────┤
│ 参照コード                ~50K     │
├─────────────────────────────────────┤
│ 会話履歴                  ~70K     │
├─────────────────────────────────────┤
│ 出力余裕                  ~50K     │
└─────────────────────────────────────┘

原則:
- 合計使用量は150K以内に抑える
- 出力用に50K以上確保
- 不要なコンテキストは除外
```

### コンテキスト圧縮テクニック

```
1. サマリゼーション
   長い会話履歴 → 要約に置換

2. 選択的ロード
   全スキル読み込み ❌
   必要なスキルのみ ✅

3. 段階的開示
   概要 → 必要に応じて詳細
   500行ルール → references/ に分割

4. コード参照の最適化
   ファイル全体 ❌
   関連部分のみ ✅
```

---

## 3. セッション間メモリ

### メモリ永続化戦略

```
┌──────────────────────────────────────┐
│  Session Memory（揮発性）             │
│  ├─ 現在のタスクコンテキスト          │
│  ├─ 会話履歴                          │
│  └─ 一時的な作業状態                  │
├──────────────────────────────────────┤
│  Project Memory（永続性）             │
│  ├─ CLAUDE.md（プロジェクト知識）     │
│  ├─ .claude/memory/（学習記録）       │
│  ├─ スキルファイル（定型知識）         │
│  └─ TODO.md / CHANGELOG              │
├──────────────────────────────────────┤
│  Global Memory（組織知識）            │
│  ├─ ~/.claude/CLAUDE.md              │
│  ├─ ~/.claude/memory/                │
│  └─ 共有テンプレート                  │
└──────────────────────────────────────┘
```

### auto memory 活用

```
.claude/memory/MEMORY.md 活用パターン:

1. デバッグ知見の記録
   - 遭遇したエラーと解決方法
   - プロジェクト固有のハマりポイント

2. アーキテクチャ判断の記録
   - 選択した設計とその理由
   - 却下した代替案とその理由

3. パターン・規約の記録
   - プロジェクト固有のパターン
   - チーム規約の補足

記録例:
## デバッグ知見
- prisma: `prisma generate` 忘れで型エラー
- next.js: App Router の Server Component では useState 使えない
```

### MEMORY.md 制限事項

```
制限:
- MEMORY.md は先頭200行のみがシステムプロンプトに読み込まれる
  （200行を超えた分は切り捨て）
- 簡潔に記述し、行数を節約する
- 詳細な記録はトピック別ファイル（debugging.md 等）に分離
- トピックファイルはAIが必要時にオンデマンドで読む
```

### コンテキスト汚染検知

長時間セッションでコンテキストが汚染されると、重要な決定事項を「忘れる」。以下を実践する:

```
検知パターン（5種）:
  critical: 決定事項無視 / 要件逸脱
  major:    設計方針逸脱
  warning:  同一質問繰り返し / 同一ミス繰り返し

対策:
  - アクション前の回帰チェック（決定・制約・却下済みとの整合確認）
  - 10ターン/30分毎の自動リマインダー
  - 実装開始前・エラー3回連続後の決定事項回帰テスト
```

→ 詳細は `references/context-pollution.md` を参照

---

## 4. マルチエージェントでの知識共有

### エージェント間コンテキスト分離

```
Opus（PM）
  コンテキスト:
  - プロジェクト概要
  - タスク全体像
  - 各エージェントの進捗サマリー
  ※ 実装詳細は持たない

Codex（実装者）
  コンテキスト:
  - 担当タスクの仕様
  - 関連コード
  - テスト要件
  ※ 他タスクの詳細は持たない

Haiku 4.5（軽作業）
  コンテキスト:
  - 修正対象ファイル
  - 修正指示
  ※ 最小限のコンテキスト
```

### 引き継ぎプロトコル

```markdown
# タスク引き継ぎテンプレート

## 完了事項
- 実装したもの
- テスト結果

## 未完了事項
- 残タスク
- 既知の問題

## 判断事項
- 選択した方針とその理由
- 保留中の判断

## 参照ファイル
- 変更したファイル一覧
- 関連ドキュメント
```

---

## 5. 知識ベースの構築

### プロジェクト知識の階層

```
Level 1: 即時参照（CLAUDE.md）
  - 技術スタック、コマンド、規約
  - 常に読み込まれる

Level 2: タスク参照（スキルファイル）
  - タスク種別ごとの手順・チェックリスト
  - トリガー条件で読み込み

Level 3: 詳細参照（references/）
  - 詳細な実装例、料金表
  - 必要に応じて参照

Level 4: 履歴参照（memory/）
  - 過去の判断、デバッグ知見
  - AIが自動的に蓄積・参照
```

### ナレッジグラフ的管理

```
skills/
├── SKILL_MAP.md        ← 全体マップ（エントリポイント）
├── common/
│   ├── testing/
│   │   ├── SKILL.md    ← テスト基本
│   │   └── → quality-lv5 と補完関係
│   └── ...
├── workflow/
│   ├── quality-lv5/
│   │   ├── SKILL.md    ← テスト品質
│   │   └── → testing と補完関係
│   └── ...
└── references/
    └── 詳細ドキュメント
```

### ナレッジ蓄積パイプライン

開発中に得た知見を構造化して蓄積し、後続タスク・プロジェクトで再利用する。

```
収集タイミング: エラー解決後 / 手戻り時 / 検証パス時 / 人間指摘時 / 新ライブラリ時
分類: error_patterns / solution_patterns / architecture_decisions / domain_knowledge / tooling
記録基準: 類似ケース未存在 AND 解決3ターン以上（人間指摘は即記録）
スキル化: 同一カテゴリ3件以上 + cross_project + proven → スキル候補提案
```

→ 詳細は `references/knowledge-pipeline.md` を参照

---

## チェックリスト

### CLAUDE.md 設計時

```
□ プロジェクト概要が一文で説明できるか
□ 技術スタックが網羅されているか
□ コマンド一覧があるか
□ 禁止事項が明記されているか
□ ディレクトリ構造が記載されているか
```

### コンテキスト最適化時

```
□ トークン配分は適切か
□ 不要なコンテキストは除外されているか
□ 500行ルールを遵守しているか
□ references/ への分割は適切か
```

### メモリ運用時

```
□ MEMORY.md に重要な知見を記録しているか
□ セッション間で知識が引き継がれているか
□ 古い/誤った情報が更新されているか
□ 引き継ぎテンプレートを使用しているか
```

### CLAUDE.md 階層設計時

```
□ 個人設定は CLAUDE.local.md に分離しているか
□ .claude/rules/*.md でトピック別に分割しているか
□ @import のネスト深度は5以内か
□ 各 CLAUDE.md は 500行以内か
□ MEMORY.md は 200行以内か
□ .gitignore に CLAUDE.local.md と settings.local.json が含まれているか
□ 子ディレクトリの CLAUDE.md は遅延読み込みを前提としているか
```

### セッション引継ぎ時

```
□ 完了事項を記録しているか（実装したもの・テスト結果）
□ 未完了事項を記録しているか（残タスク・既知の問題）
□ 判断事項を記録しているか（選択した方針と理由・保留中の判断）
□ 変更ファイル一覧を記録しているか
□ 決定事項との整合性を確認したか（既存の決定に反する変更がないか）
□ 却下済みアプローチを再提案していないか
```

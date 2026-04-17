---
name: web-search
description: Tavily MCP を wrap した Web 検索スキル。ドキュメント検索・一次情報収集に使う
metadata:
  helix_layer: L1
  triggers:
    - G1R 事前調査時
    - R0 証拠収集時
    - 競合調査時
    - ライブラリ比較時
    - 技術動向確認時
  verification:
    - "検索結果に一次情報 URL を 2件以上含む"
    - "出典ごとに信頼度 (公式/個人/二次) を注記"
  attribution: tavily-mcp (MIT) — https://github.com/tavily-ai/tavily-mcp
compatibility:
  claude: true
  codex: true
---

# Web Search スキル

## 使用タイミング

このスキルは、一次情報を短時間で収集し、根拠付きで判断したい場面で利用する。

- G1R の事前調査（設計着手前の根拠収集）
- R0 の証拠収集（既存挙動の事実確認）
- 競合調査（機能差分、価格、公開仕様）
- ライブラリ比較（公式ドキュメント、リリースノート）
- 技術動向確認（仕様変更、非推奨化、移行ガイド）

### 使うべき情報源

- 公式ドキュメント
- 公式 GitHub リポジトリ
- 標準化団体・仕様策定組織
- ベンダー公式ブログ（一次発信）

### 後回しにする情報源

- 引用元不明のまとめ記事
- 二次転載のみのニュース
- 作成日が古く更新履歴のない個人記事

---

## 入出力契約

### 入力

- 調査目的: 何を判断するための検索か
- 検索クエリ: 具体語 + 制約語（例: version, migration, breaking change）
- 期間条件: 必要に応じて直近日付を指定
- 出力粒度: 箇条書き要約 / 詳細比較 / 根拠一覧

### 出力

- 要約: 調査結果の結論（2-5行）
- 根拠一覧: URL、タイトル、取得日、該当箇所要約
- 信頼度注記: 各出典に `公式` / `個人` / `二次` を付与
- 未確定事項: 根拠不足で断定できない点

### 出力フォーマット例

```markdown
結論:
- OAuth 2.1 への移行時は implicit flow 廃止前提で設計する。

根拠:
1. https://example.com/spec
   - 種別: 公式
   - 要点: implicit flow 非推奨の明記あり
2. https://github.com/org/repo/releases/tag/v2.0.0
   - 種別: 公式
   - 要点: v2.0.0 で互換性破壊変更を告知

未確定事項:
- 既存顧客テナントの段階移行方式は公開情報に記載なし
```

---

## 呼び出し例

### 例1: ライブラリ比較

- 目的: A/B ライブラリの長期運用性を比較
- クエリ例:
  - `<library A> maintenance policy official`
  - `<library B> security advisory`
  - `<library A> vs <library B> migration guide`

### 例2: Reverse 調査

- 目的: R0 で既存システムの外部依存仕様を確認
- クエリ例:
  - `<service name> api rate limit official`
  - `<service name> deprecation notice`

### 例3: 技術動向確認

- 目的: 近時の仕様変更有無を確認
- クエリ例:
  - `<technology> release notes 2025 2026`
  - `<technology> breaking changes`

---

## TAVILY_API_KEY 設定

Tavily MCP を利用するには API キーが必要。

1. Tavily 側で API キーを発行する
2. 実行環境に `TAVILY_API_KEY` を設定する
3. キーはハードコードしない（環境変数のみ）
4. ログ・出力にキー値を含めない

```bash
export TAVILY_API_KEY="<your_api_key>"
```

セキュリティ上、`.env` や秘密情報管理基盤での保管を優先する。

---

## native WebSearch fallback 指示

Tavily MCP が利用できない場合は、ネイティブ `WebSearch` を使用して調査を継続する。

- fallback 発動条件:
  - MCP 接続エラー
  - 認証エラー
  - レート制限で再試行不能
- fallback 実施時の必須事項:
  - クエリを同等粒度で再実行
  - 一次情報 URL 2件以上を確保
  - Tavily 不使用理由を出力末尾に明記

### fallback 記載例

```markdown
補足:
- Tavily MCP は認証エラーのため未使用。
- native WebSearch で同一クエリを再実行し、一次情報を収集。
```

---

## 出典明示ルール

全ての主張は、可能な限り URL を添えて根拠化する。

- 仕様・API 挙動: 公式ドキュメントを優先
- 破壊的変更: 公式リリースノートを優先
- 運用制約: ベンダー公式ステータス/FAQ を確認
- 個人記事を使う場合: 補助根拠として扱い、断定根拠にしない

### 信頼度ラベル

- `公式`: ベンダー公式、標準仕様、公式 GitHub
- `個人`: 個人ブログ、個人ノート、非公式解説
- `二次`: まとめサイト、転載記事、ニュース集約

### 最低基準

- URL を 2件以上提示
- 可能なら同一論点を別ソースで相互確認
- 日付と版数（version）を併記


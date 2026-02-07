# コンテキスト汚染検知・回復

> 出典: docs/archive/v-model-reference-cycle-v2.md §コンテキスト汚染と記憶喪失対策

## 記憶喪失の兆候パターン

| パターン | 検知方法 | 重要度 |
|----------|----------|--------|
| repeated_question | 過去10ターン内に同一質問（類似度>0.9） | warning |
| decision_ignored | 決定済み事項（decisions.md）と矛盾する提案 | critical |
| requirement_drift | 要件引継書にない機能の実装提案 | critical |
| repeated_mistake | 過去に指摘された問題と同一パターンの再発 | warning |
| design_deviation | 設計書の方針と異なるアーキテクチャ提案 | major |

## 回帰チェックポイント

アクション実行前に以下を確認する:

```
1. 決定事項との整合性チェック
   → decisions.md の変更禁止項目と矛盾しないか
   → 矛盾検出時: severity=critical → 即停止・確認

2. 制約条件チェック
   → constraints.md の制約に違反しないか
   → 違反検出時: severity=critical → 即停止・確認

3. 却下済みアプローチの再提案チェック
   → rejected-approaches.md のパターンと類似しないか
   → 類似検出時: severity=warning → 理由付きで警告
```

## 自動リマインダートリガー

| トリガー | 内容 | 形式 |
|----------|------|------|
| 10ターン毎 | decisions.md + constraints.md の要約 | コンテキストリマインダー |
| 30分毎 | 直近の重要決定 + 残タスク | 定期チェックポイント |
| 実装開始前 | 要件の該当セクション + 設計書の制約 | 実装開始前確認 |
| エラー3回連続後 | 関連する過去の解決策 + 制約の再確認 | エラー連続発生警告 |
| コンテキスト80%到達 | 重要情報のサマリー + 圧縮提案 | コンテキスト上限警告 |

## 回帰テスト（決定事項の再確認）

以下のタイミングで決定事項の回帰テストを実行:
- **実装開始前**（必須）
- **10ターン毎**（定期）
- **エラー3回連続後**（異常検知時）

テスト内容:
```
各決定事項について:
  1. コンテキスト内に言及があるか → なし: FORGOTTEN → リマインダー注入
  2. 矛盾する記述がないか → あり: CONTRADICTED → 即座に停止・確認
```

## 永続化すべきファイル構成

```
.claude/memory/
├── decisions.md          # 決定事項（変更禁止/条件付き/AI判断/決定ログ）
├── constraints.md        # 制約条件（技術的・ビジネス的）
├── glossary.md           # 用語定義
├── gotchas.md            # プロジェクト固有の注意点
├── rejected-approaches.md # 却下されたアプローチと理由
├── session-handover.md   # セッション引継ぎ情報
└── tech-rationales.yaml  # 技術理由レジストリ
```

## セッション引継ぎプロトコル

### 旧セッション終了時
1. 未完了タスクの記録
2. 本セッションでの決定事項を decisions.md#決定ログ に追記
3. 却下したアプローチを rejected-approaches.md に追記
4. session-handover.md 更新（状態サマリー・申し送り・注意点）

### 新セッション開始時
1. memory/ 配下の全ファイルをコンテキストにロード
2. session-handover.md の申し送りを確認
3. 工程表から現在の状態を確認
4. 「前セッションからの引継ぎ確認」を出力

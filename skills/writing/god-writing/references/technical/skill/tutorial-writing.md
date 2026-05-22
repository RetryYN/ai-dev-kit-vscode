skill_id: technical/skill/tutorial-writing
category: technical
type: skill
dependencies:
  - technical/knowledge/technical-writing-basics
  - technical/skill/documentation-writing

chunks:
  - chunk_id: summary
    content: |
      学習目的のチュートリアル作成技法。
      読者が新しいスキル・知識を習得できる
      段階的な学習コンテンツの設計スキル。

  - chunk_id: tutorial-vs-howto
    tags: [チュートリアル, ハウツー, 違い]
    content: |
      チュートリアルとハウツーの違い：
      チュートリアル：
      - 学習が目的
      - 理解を深める
      - 順を追って進める
      - 「なぜ」も説明
      ハウツー：
      - タスク完了が目的
      - 効率重視
      - 必要な部分だけ見る
      - 「どうやって」に集中
      チュートリアルは「教育」、ハウツーは「参照」。

  - chunk_id: learning-objectives
    tags: [学習目標, ゴール, 目的]
    content: |
      学習目標の設定：
      チュートリアル完了時に何ができるようになるか。
      書き方：
      「このチュートリアルを完了すると、あなたは：
      - 〇〇の基本概念を理解できます
      - △△を設定できます
      - □□を作成できます」
      明確な目標があると：
      - 読者がモチベーションを持てる
      - 内容がブレない
      - 達成感が生まれる

  - chunk_id: prerequisites
    tags: [前提条件, 準備, 必要知識]
    content: |
      前提条件の明示：
      始める前に必要なもの。
      種類：
      - 知識：「JavaScriptの基本知識」
      - 環境：「Node.js v18以上」
      - アカウント：「〇〇のアカウント」
      - 時間：「所要時間：約30分」
      例：
      「## 前提条件
      - HTML/CSSの基本知識
      - テキストエディタ
      - モダンブラウザ（Chrome推奨）
      - 所要時間：約20分」

  - chunk_id: progressive-structure
    tags: [段階的, 構成, ステップ]
    content: |
      段階的な構成：
      簡単→複雑へ順を追って。
      構成例：
      1. はじめに（目標、前提条件）
      2. 環境準備
      3. 基本的な使い方（最小構成）
      4. 機能を追加（段階的に複雑化）
      5. 応用・カスタマイズ
      6. 次のステップ
      各ステップで「動く状態」を確認。

  - chunk_id: explanation-balance
    tags: [説明, バランス, 理解]
    content: |
      説明と手順のバランス：
      手順だけでなく「なぜ」も説明。
      悪例：
      「1. npm install を実行する」
      良例：
      「1. 必要なパッケージをインストールします。
      このコマンドは package.json に記載された
      依存関係を全てダウンロードします。
      `npm install`」
      理解が伴うと応用が効く。

  - chunk_id: code-walkthrough
    tags: [コード, 解説, ウォークスルー]
    content: |
      コードの解説方法：
      コードブロック + 説明の組み合わせ。
      形式：
      ```javascript
      // ユーザーデータを取得
      const user = await getUser(id);
      // 名前を表示
      console.log(user.name);
      ```
      解説：
      - `getUser(id)` でAPIからデータを取得
      - `await` で非同期処理の完了を待つ
      - 取得したデータの`name`を表示
      コメント + 本文説明の両方で。

  - chunk_id: checkpoints
    tags: [チェックポイント, 確認, 進捗]
    content: |
      チェックポイントの設置：
      「ここまでの確認」を適宜入れる。
      例：
      「## ここまでの確認
      この時点で、以下が完了しているはずです：
      - ✓ プロジェクトが作成されている
      - ✓ http://localhost:3000 でページが表示される
      うまくいかない場合は、〇〇を確認してください。」
      読者が迷子にならないように。

  - chunk_id: common-mistakes
    tags: [よくある間違い, 注意, エラー]
    content: |
      よくある間違いへの対処：
      読者がハマりやすいポイントを先に示す。
      形式：
      「⚠️ 注意
      〇〇の場合、△△のエラーが出ることがあります。
      その場合は、□□を確認してください。」
      「💡 ヒント
      うまくいかない場合は、〇〇を試してみてください。」
      先回りでトラブルを防ぐ。

  - chunk_id: checklist
    tags: [チェックリスト, 確認]
    content: |
      チュートリアル作成チェックリスト：
      □ 学習目標は明確か
      □ 前提条件は明示したか
      □ 段階的に難易度が上がるか
      □ 各ステップで動く状態を確認できるか
      □ 「なぜ」の説明があるか
      □ コードは解説付きか
      □ チェックポイントはあるか
      □ よくある間違いに触れているか
      □ 次のステップを示しているか

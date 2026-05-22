> 目的: GPT Image 2を使ったSEO記事用図解作成の6ステップワークフロー。6種の図解タイプ別プロンプトテンプレート・16 ref images活用・Thinking mode応用・チェックリストを提供する。
> このreferenceは skills/design-tools/gpt-image/SKILL.md §5.2 から呼ばれる

skill_id: design/gpt-image/skill/diagram-creation
category: design
type: skill
dependencies:
  - design/gpt-image/skill/prompt-engineering
  - design/gemini-image/knowledge/diagram-types
  - design/gemini-image/knowledge/design-principles

chunks:
  - chunk_id: summary
    content: |
      GPT Image 2を使ったSEO記事用図解作成ワークフロー。
      構造化プロンプトで複雑な図解も高精度に生成。
      多言語テキスト~99%精度と16 reference imagesのstyle anchor活用。
      Thinking modeで複雑な多要素layoutのcoherent生成が可能。
      各図解タイプ別のテンプレートと実践例を提供。

  - chunk_id: workflow-overview
    tags: [ワークフロー, 全体像, プロセス]
    content: |
      図解作成ワークフロー（6ステップ）：
      1. コンテンツ分析：図解化する内容を特定
      2. 図解タイプ選定：最適な形式を選択
      3. 情報構造化：要素・ラベル・関係を整理
      4. プロンプト構築：構造化プロンプト作成
      5. 生成＆改善：生成→編集で精度向上
      6. 最終処理：サイズ調整、最適化
      所要時間目安：5〜15分/図解

  - chunk_id: step1-content-analysis
    tags: [分析, コンテンツ, 抽出]
    content: |
      ステップ1：コンテンツ分析
      図解化すべき箇所を特定：
      - 手順・プロセスの説明
      - 比較・対比している部分
      - 構造・関係性の説明
      - 数値・統計データ
      抽出すべき情報：
      □ 主題（何についての図解か）
      □ 要素（含まれる項目、3〜7個が理想）
      □ ラベル（各要素の名称、10字以内）
      □ 関係性（順序、比較、包含）
      □ 強調点（特に重要な部分）

  - chunk_id: step2-type-selection
    tags: [選定, タイプ, 判断]
    content: |
      ステップ2：図解タイプ選定
      クイック判断フロー：
      順序・流れあり→フローチャート
      複数を比較→比較表
      ランク・優先度→階層図/ピラミッド
      時間軸あり→タイムライン
      項目列挙→リスト型
      数値データ→グラフ・チャート
      概念の関係→ベン図/関係図
      2軸分類→マトリクス
      GPT Image 2の強み：
      - 複雑なインフォグラフィック（Thinking modeでlayout計画）
      - テキスト密度の高い図解（多言語テキスト~99%精度）
      - マルチパネル構成
      - brand asset一貫性（16 ref imagesのstyle anchor）

  - chunk_id: step3-information-structure
    tags: [情報設計, 構造, 整理]
    content: |
      ステップ3：情報構造化
      プロンプト用に整理する形式：
      ```
      Elements:
      1. [要素名]: [簡潔な説明]
      2. [要素名]: [簡潔な説明]
      3. [要素名]: [簡潔な説明]
      
      Relationships:
      - [要素1] → [要素2]
      - [要素A] vs [要素B]
      
      Emphasis:
      - Highlight [重要要素]
      ```
      この形式でまとめておくと
      プロンプトにそのまま使える。

  - chunk_id: flowchart-prompt
    tags: [フローチャート, プロンプト, テンプレート]
    content: |
      フローチャート用プロンプト：
      ```
      Create a professional flowchart diagram.
      
      Topic: [テーマ]
      
      Steps (in order):
      1. "[Step1名]"
      2. "[Step2名]"
      3. "[Step3名]"
      4. "[Step4名]"
      
      Layout: Horizontal flow, left to right
      Shapes: Rounded rectangles for each step
      Connectors: Arrows between steps
      
      Typography: Bold labels inside boxes,
      clear and readable
      Colors: [メイン色] boxes, white text,
      [アクセント色] arrows
      Background: White, clean
      
      Style: Professional infographic,
      consistent spacing, aligned elements.
      No extra decorations.
      ```

  - chunk_id: comparison-prompt
    tags: [比較表, プロンプト, テンプレート]
    content: |
      比較表用プロンプト：
      ```
      Create a comparison chart infographic.
      
      Comparing: "[Option A]" vs "[Option B]"
      
      Comparison criteria:
      - [項目1]: A=[値], B=[値]
      - [項目2]: A=[値], B=[値]
      - [項目3]: A=[値], B=[値]
      - [項目4]: A=[値], B=[値]
      
      Layout: Two columns, side by side
      Headers: Bold, large, at top of each column
      
      Use checkmarks (✓) for positive,
      X marks for negative where appropriate.
      
      Colors: [A用の色] for left column,
      [B用の色] for right column
      Typography: Clean sans-serif, high contrast
      
      Professional, balanced, easy to scan.
      ```

  - chunk_id: hierarchy-prompt
    tags: [階層図, プロンプト, テンプレート]
    content: |
      階層図/ピラミッド用プロンプト：
      ```
      Create a pyramid hierarchy diagram.
      
      Topic: [テーマ]
      
      Levels (top to bottom):
      Level 1 (top, smallest): "[最上位/最重要]"
      Level 2: "[次レベル]"
      Level 3: "[その次]"
      Level 4 (bottom, largest): "[基盤]"
      
      Layout: Traditional pyramid shape,
      wider at bottom, narrower at top
      
      Typography: Labels centered in each level,
      bold white text
      Colors: Gradient from [top色] at top
      to [bottom色] at bottom
      
      Style: Clean, modern, professional
      Background: White
      
      No 3D effects, flat design preferred.
      ```

  - chunk_id: timeline-prompt
    tags: [タイムライン, プロンプト, テンプレート]
    content: |
      タイムライン用プロンプト：
      ```
      Create a horizontal timeline infographic.
      
      Topic: [テーマ]
      
      Events (chronological):
      - [年/日付1]: "[イベント1]"
      - [年/日付2]: "[イベント2]"
      - [年/日付3]: "[イベント3]"
      - [年/日付4]: "[イベント4]"
      
      Layout: Horizontal line across center,
      events alternating above and below
      Markers: Circular nodes on the timeline
      
      Typography: Dates in bold,
      descriptions in regular weight
      Colors: [メイン色] for line and markers,
      [テキスト色] for text
      
      Style: Clean, modern, easy to follow
      Background: White or light gray
      
      Ensure all text is legible.
      ```

  - chunk_id: matrix-prompt
    tags: [マトリクス, プロンプト, テンプレート]
    content: |
      マトリクス/象限図用プロンプト：
      ```
      Create a 2x2 matrix diagram.
      
      Topic: [テーマ]
      
      Axes:
      - X-axis (horizontal): "[横軸の概念]"
        Left = Low, Right = High
      - Y-axis (vertical): "[縦軸の概念]"
        Bottom = Low, Top = High
      
      Quadrants:
      - Top-Right: "[名称]" - [説明]
      - Top-Left: "[名称]" - [説明]
      - Bottom-Right: "[名称]" - [説明]
      - Bottom-Left: "[名称]" - [説明]
      
      Layout: Clear grid lines, axis labels
      Colors: Different color for each quadrant
      Typography: Bold quadrant names,
      smaller descriptions
      
      Professional, analytical style.
      Clear axis labels on edges.
      ```

  - chunk_id: infographic-prompt
    tags: [インフォグラフィック, プロンプト, 複合]
    content: |
      複合インフォグラフィック用プロンプト：
      ```
      Create a professional infographic.
      
      Topic: "[メインタイトル]"
      
      Sections (top to bottom):
      
      Section 1 - Header:
      - Title: "[タイトル]"
      - Subtitle: "[サブタイトル]"
      
      Section 2 - Key Stats:
      - "[数値1]" with label "[説明1]"
      - "[数値2]" with label "[説明2]"
      - "[数値3]" with label "[説明3]"
      
      Section 3 - Process:
      - Steps: [Step1] → [Step2] → [Step3]
      
      Layout: Vertical scroll format,
      clear section divisions
      Colors: [メイン色], [サブ色], [アクセント色]
      Typography: Hierarchy with large headers,
      medium subheads, readable body
      
      Style: Modern, data-driven, professional
      Aspect ratio: Vertical (1024x1792 or similar)
      ```

  - chunk_id: step5-generation
    tags: [生成, 改善, 確認]
    content: |
      ステップ5：生成＆改善
      Codex CLI $imagegen skillでの起動（推奨）：
      ```
      codex run "$imagegen --model gpt-image-2-2026-04-21 \
        --size 1024x1024 \
        --quality high \
        --refs ./brand/diagram-*.png \
        --prompt 'Use reasoning to plan the layout. Create a [図解タイプ]...'"
      ```
      初回生成後のチェック：
      □ すべての要素が含まれているか
      □ テキストラベルは正確か（日本語はnative~99%）
      □ 流れ・関係性は明確か
      □ 読みやすいサイズか
      □ 色のコントラストは十分か
      □ brand assetとstyleが一致しているか（16 ref images使用時）
      編集プロンプト例（GPT Image 2の1 call edit）：
      ```
      Edit the diagram:
      
      CHANGE: Make labels larger and bolder.
      KEEP: Layout, colors, structure exactly as is.
      
      Do not alter element positions or relationships.
      ```
      GPT Image 2は前世代比2倍高速なので
      複数バリエーションを試しやすい。
      Thinking mode活用（複雑な多要素layout）：
      - "Use reasoning to plan the layout before generation." を先頭に追加
      - 複雑なインフォグラフィックでcoherent layout実現

  - chunk_id: editing-for-diagrams
    tags: [編集, 図解, 調整]
    content: |
      図解特有の編集プロンプト：
      要素追加：
      「CHANGE: Add icons next to each step.
      KEEP: Text, layout, colors unchanged.」
      間隔調整：
      「CHANGE: Increase spacing between elements.
      KEEP: All content and relationships.」
      強調追加：
      「CHANGE: Highlight step 3 with accent color.
      KEEP: Other elements exactly as is.」
      矢印改善：
      「CHANGE: Make arrows more prominent.
      KEEP: Boxes, text, positions unchanged.」
      テキスト修正：
      「CHANGE: Fix label to read "[正しいテキスト]".
      KEEP: Everything else identical.」

  - chunk_id: step6-finalization
    tags: [最終処理, 最適化, 出力]
    content: |
      ステップ6：最終処理
      サイズ調整：
      - 横長図解：1792×1024 → 記事幅に合わせて
      - 縦長図解：1024×1792 → 適切にトリミング
      - 正方形：1024×1024
      形式選択：
      - 図解はPNG推奨（シャープなライン）
      - WebP変換で軽量化
      最適化：
      - ファイルサイズ100KB以下目標
      - 必要に応じて再圧縮
      配置確認：
      - 記事内での見え方
      - モバイル表示での可読性

  - chunk_id: text-heavy-diagrams
    tags: [テキスト, 密度, インフォグラフィック, 多言語]
    content: |
      テキスト密度の高い図解（GPT Image 2の強み）：
      活用シーン：
      - 詳細なインフォグラフィック
      - チェックリスト型図解
      - 手順書・マニュアル
      - データ表・一覧
      - 多言語テキスト入り図解（日本語 / 中国語 / 韓国語 native対応）
      プロンプトのコツ：
      - すべてのテキストを明示的に記載
      - 階層構造を明確に（Header, Subhead, Body）
      - フォントサイズの相対関係を指定
      - 「legible」「readable」を強調
      - 日本語ラベルはそのまま記載可能（英語変換不要）
      例（英語）：
      「Ensure all text is perfectly legible,
      with clear hierarchy: large bold headers,
      medium subheadings, readable body text.」
      例（日本語 / GPT Image 2 native対応）：
      「Labels (EXACT, verbatim): "要件定義", "設計", "実装", "検証"
      Typography: bold Japanese sans-serif, high contrast.
      ~99% typography accuracy for Japanese labels.」
      重要：固有名詞・brand nameは生成後に再確認推奨

  - chunk_id: multi-panel-diagrams
    tags: [マルチパネル, 複数, 構成]
    content: |
      マルチパネル構成（GPT Image 1.5の強み）：
      用途：
      - Before/After比較
      - ステップバイステップ図解
      - 複数シナリオの提示
      プロンプト例：
      ```
      Create a 3-panel infographic.
      
      Panel 1 (left): [内容1]
      Panel 2 (center): [内容2]
      Panel 3 (right): [内容3]
      
      Layout: Three equal columns,
      clear dividers between panels
      Each panel has its own header
      
      Consistent style across all panels.
      ```
      番号付けやラベルで
      パネル間の関係を明示。

  - chunk_id: troubleshooting
    tags: [トラブル, 問題解決, 対処]
    content: |
      よくある問題と対処：
      問題：要素が欠けている
      →プロンプトで明示的にリスト化
      問題：テキストが読めない
      →「bold」「large」「high contrast」追加
      問題：日本語ラベルが崩れる（GPT Image 2は~99%対応）
      →固有名詞・brand nameは生成後に再確認
      →"~99% typography accuracy for Japanese text." を追加
      問題：関係性が不明確
      →「arrows」「connectors」「flow」を指定
      問題：バランスが悪い
      →「aligned」「consistent spacing」を追加
      →複雑layoutは "Use reasoning to plan the layout" (Thinking mode)を追加
      問題：複雑すぎて崩れる
      →Thinking mode活用（subscription限定）またはシンプルな図解に分割
      問題：brand styleと一致しない
      →--refs ./brand/diagram-*.png で16 ref imagesをstyle anchorとして渡す
      問題：4K出力が不安定
      →4KはbetaのためAPIは2K（--size 2048x...）でstable推奨

  - chunk_id: checklist
    tags: [チェックリスト, 確認, 完了]
    content: |
      図解作成チェックリスト：
      準備：
      □ 図解化する内容を特定
      □ 最適な図解タイプを選択
      □ 要素とラベルを構造化
      プロンプト：
      □ 構造化テンプレート使用
      □ すべての要素をリスト化
      □ テキストを明示的に記載
      □ レイアウト・色を具体的に指定
      生成：
      □ すべての要素が含まれているか
      □ テキストは正確か
      □ 可読性は十分か
      最終：
      □ 適切なサイズに調整
      □ PNG/WebP形式で出力
      □ alt属性テキストを準備

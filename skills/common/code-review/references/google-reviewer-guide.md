> 目的: Google Engineering Practices (https://google.github.io/eng-practices/) の reviewer guide を判断基準とした、HELIX L7 / G7 コードレビューの「レビュアー視点」運用 reference。承認可否 (LGTM / LGTM with nits / Changes requested) 判定、Blocking / Nit / Optional のコメントラベル付け、健全性 (code health) を基準とした完璧主義回避を集約。

# Google Engineering Practices: Code Review Reviewer Guide (HELIX 統合版)

レビュアーとして差分 (CL / PR) を評価し、承認可否と改善コメントを返すための reference。
出典: [Google Engineering Practices Documentation - Code Review](https://google.github.io/eng-practices/review/) (Apache License 2.0)。
HELIX format に統合し、関連 skill / 関連 gate / 関連 PLAN への cross-reference を追加。

---

## 0. 用語

- **CL**: 1 つの自己完結した変更 (PR / patch / change と同義)。
- **LGTM**: "Looks Good to Me"。承認の意思表示。
- **Nit**: 修正は望ましいが、承認をブロックしない軽微な指摘。

---

## 1. 最上位原則 (The Standard)

レビューの可否は、ただ 1 つの基準で判断する。

> **このCLは、適用後にコードベースの「全体的な健全性 (code health)」を確実に向上させるか。**

これが満たされるなら、**CL が完璧でなくても承認する**。完璧な CL は存在しない。
レビュアーの仕事は「自分が書いたであろう理想のコード」を要求することではなく、
「現状より確実に良くなる変更」を前に進めることである。

- 健全性を **向上させる** CL → 多少の改善余地があっても承認してよい (改善は Nit で残す)。
- 健全性を **悪化させる** CL → 原則として承認しない。**唯一の例外は緊急対応 (emergency)** であり、その場合も後追いの是正を前提とする。
- 「より良い案がある」だけでは差し戻し理由にならない。差し戻すのは「このまま入れると健全性が下がる／向上が不確実」な場合に限る。

### メンターシップ

承認をブロックしない範囲で、より良い書き方を `Nit:` として共有してよい。
ただし学習機会の提供と、CL を止めることは別物。前者で CL を止めない。

---

## 2. レビューの観点 (優先順位順)

上から順に重い。上位の問題を未解決のまま下位の指摘に時間を使わない。

1. **設計 (Design) — 最重要**
   - このコードはここに置くべきか。既存システムと統合は適切か。
   - 今このタイミングで導入すべき機能か (過不足)。
2. **機能性 (Functionality)**
   - 作者の意図どおり動くか。意図はユーザー (エンドユーザー・将来の開発者) にとって妥当か。
   - エッジケース・並行処理・例外パスを考慮しているか。
3. **複雑性 (Complexity)**
   - 必要以上に複雑ではないか。読んだ人がすぐ理解できるか。
   - **YAGNI**: 「将来必要かも」で入れた汎用化・抽象化は過剰設計として指摘する。
4. **テスト (Tests)**
   - 変更に見合うテストがあるか。テスト自体が正しく、壊れたら確実に落ちるか。
   - テストは複雑すぎないか (テストのテストが要るようなら設計を見直す)。
5. **命名 (Naming)**
   - 変数・関数・クラスは「何であり何をするか」を過不足なく伝えているか。
6. **コメント (Comments)**
   - コメントは「**なぜ** そうなっているか」を説明しているか。
   - 「**何を** しているか」をコメントで補うコードは、コード側を直すべきサイン。
   - 将来削除予定・TODO 等は理由とともに明記されているか。
7. **スタイル (Style)**
   - スタイルガイドに準拠しているか。**ガイドに無い個人的な好みは `Nit:` として出し、ブロックしない。**
   - 整形・空白・命名規約など機械判定可能なものは、原則 linter / formatter に委ね、人間の指摘から外す。
8. **一貫性 (Consistency)**
   - 既存コードベースの慣習と整合しているか (既存が明確に劣る場合を除く)。
9. **ドキュメント (Documentation)**
   - 挙動・運用・ビルド手順等が変わるなら、対応するドキュメントも更新されているか。

### 横断ルール

- **すべての行を見る (Every line)**: 人が書いた全行に目を通す。例外 = 自動生成物・大量データファイル等はスキャンに留めてよい。
- **文脈で見る (Context)**: 差分だけでなく、そのファイル全体・周辺システムへの影響を見る。
- **良い点も言う (Praise)**: 優れた設計・きれいな処理は明示的に評価する。指摘専用機にしない。

---

## 3. レビューの進め方 (手順)

1. **まず全体像を取る**: CL 説明文・目的・設計意図を読む。説明が不十分なら、その時点で差し戻してよい。
2. **設計の妥当性を最初に判断する**: 根本設計に問題があるなら、詳細を読む前にそれを伝える (詳細指摘に時間を費やしてから設計を否定するのは作者・自分双方の浪費)。
3. **主要部分 → 残り** を論理的な順序で読む。
4. 観点 (§2) の優先順位順に、見つけた事項を分類して記録する。

---

## 4. コメント規約

- **礼儀正しく、理由を添える**。批判の対象は「コード」であって人ではない。
- **指示か、問題提起か** を使い分ける。明確な誤りは直接指摘し、設計判断が絡むものは「ここはこういう懸念がある」と問題を提示し、解決を作者に委ねる。
- 各コメントには重要度ラベルを付ける:
  - `[Blocking]`: 承認をブロックする。健全性を下げる／向上が不確実な事項。
  - `Nit:`: 直してほしいが **ブロックしない**。
  - `Optional:` / `FYI:`: 任意・参考。
- ラベルの無い指摘は Blocking 扱いにしない。曖昧な「気になる」で CL を止めない。

---

## 5. 判定とアウトプット形式

レビュー結果は必ず次の 3 値のいずれかで返す。

- **LGTM**: そのまま承認。
- **LGTM with nits**: 承認するが Nit の対応を推奨 (作者判断で適用可、再レビュー不要)。
- **Changes requested**: Blocking 事項があり、是正後の再レビューが必要。

判定ロジック:

```
Blocking 事項が1件以上ある        → Changes requested
Blocking 0件 かつ Nit/Optional あり → LGTM with nits
Blocking 0件 かつ 指摘なし          → LGTM
```

出力テンプレート (このフォーマットで返すこと):

```
## レビュー結果: <LGTM | LGTM with nits | Changes requested>

### 判定理由
<最上位原則に照らした 1〜3 行の総括。「健全性を向上させるか」への回答を明記>

### Blocking (要対応)
- [設計] <該当箇所>: <問題と理由>
- [テスト] <該当箇所>: <問題と理由>
(無ければ "なし")

### Nit / Optional (任意)
- Nit: <該当箇所>: <改善提案>

### 良い点
- <評価できる設計・実装>
```

---

## 6. レビュー速度

- **1 営業日以内** に応答する。完全なレビューが終わらなくても、まず一次応答を返す。
- 作業を抱え込んで CL を滞留させない。レビューは割り込み可能なタスクとして扱う。
- 大きな CL は「分割してほしい」と依頼してよい (小さい CL ほど速く・正確にレビューできる)。

---

## 7. 対立の解決 (Pushback)

- 判断は **事実とデータ** に基づく。職位・声の大きさで決めない。
- 作者の反論が正しければ、即座に受け入れて承認する (「自分の指摘を通す」ことが目的ではない)。
- 議論が技術的に行き詰まったら、当人同士で抱え込まず、対面 / 同期での議論や TL・該当領域の有識者へのエスカレーションを行う。**ただし CL を放置しない**。
- 礼節を保つ。相手の能力ではなく、コードと設計判断について話す。

---

## 8. 適用範囲の注意

- 本 reference は **レビュアー側** の判断基準。変更を作成する側 (CL author) の作法は別 skill (`agent-skills/code-review-and-quality` 5 軸レビュー or `workflow/adversarial-review`) に分離する。
- スタイル・整形・命名規約など機械判定可能な事項は、本 reference で人手レビューするより linter / formatter / CI に寄せ、本 reference は設計・複雑性・テスト・健全性の判断に集中する。

---

## HELIX 連携

### 関連 skill

- `skills/common/code-review/SKILL.md`: HELIX L7 / G7 連携の base skill (本 reference の親 skill)
- `skills/agent-skills/code-review-and-quality/SKILL.md`: addyosmani/agent-skills (MIT) 由来の 5 軸 review (Correctness / Readability / Architecture / Security / Performance)
- `skills/workflow/adversarial-review/SKILL.md`: G2/G4/G6 ゲート前の adversarial check
- `skills/common/security/SKILL.md`: §2 の Security (4 番目観点) を具体化する OWASP/秘密情報チェック

### 関連 gate

- **G7 実装完了ゲート**: 本 reference の判定ルール (LGTM / LGTM with nits / Changes requested) を **mandatory in sprint** のレビュー step (PLAN-077 Sprint 標準 8 ステップ Step 6) に適用
- **G11 RC 判定ゲート**: 統合 PR の最終 review 時に本 reference の出力テンプレートを使う

### HELIX 独自拡張

- **エスカレーション境界**: 本番影響・認証・決済・PII・ライセンスを含む CL は、Blocking 0 件でも `helix codex --role tl-advisor` または `helix claude --role pm-advisor` への adversarial check を必須化 ([CLAUDE.md §Advisor 召喚ルール](../../../CLAUDE.md#advisor-召喚ルール運用))
- **Codex 委譲レビュー**: `helix codex --role tl` で commit/PR レビューを委譲する場合、本 reference の出力テンプレートを prompt で明示
- **PLAN trace**: review 結果は handover ESCALATION.md / handover note に「review_blocking / review_nits / review_praise」として記録 (PLAN-077 carry note pattern)

### 関連 ADR / PLAN

- ADR-009 (hook-strategy): pre-commit hook と本 reference の human review の使い分け
- PLAN-077 (Sprint Plan 標準構造): Step 6 「レビュー」の判定基準として本 reference を参照
- PLAN-100 (V2 phase4 overhaul): code review framework の position 整理

---

## License

Original guide: [Google Engineering Practices](https://google.github.io/eng-practices/) — Apache License 2.0。
HELIX 統合版 (本 file): HELIX repository license に準拠。Apache 2.0 のクレジット表示と改変通知を含む。

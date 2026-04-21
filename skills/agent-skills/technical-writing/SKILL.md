---
name: technical-writing
description: Google Technical Writing の原則 (短い文・能動態・用語一貫性・読み手設定・箇条書き・段落構成) を適用し、設計書・API ドキュメント・README・SKILL.md・ADR の品質を底上げする。日本語・英語ドキュメント執筆時、PR 説明・リリースノート作成時に使う。
helix_layer: [L2, L3, L7]
helix_gate: [G2, G4, G6]
codex_role: docs
tier: 1
upstream: https://developers.google.com/tech-writing (Google, CC-BY)
---

# Technical Writing (テクニカルライティング)

## Overview
このスキルは、Google Technical Writing コースで示される原則を HELIX の文書作成に適用する。
目的は、短く明確で、読み手が行動しやすいドキュメントを安定して作ること。
README、API 仕様、設計書、ADR、SKILL.md、PR 説明、リリースノートまで同じ品質基準で整える。

## When to Use
次のようなタスクで発火する。

- 設計書を新規作成するとき (D-ARCH、D-API、D-DB、D-CONTRACT など)
- API ドキュメントを更新するとき (契約変更、レスポンス更新、エラー仕様追加)
- README を初期作成または全面改訂するとき
- `SKILL.md` を追加するとき、または既存スキルを再構成するとき
- ADR を作成し、判断理由を将来に残すとき
- PR 説明で変更点・影響範囲・検証結果を簡潔に伝えるとき
- リリースノートで利用者影響を明確に伝えるとき
- エラーメッセージや運用手順書を読みやすく統一するとき

次のケースでは適用優先度を下げる。

- 純粋なコード実装のみで、文書更新が発生しない小変更
- 一時的なメモや個人下書き (公開前に本スキルへ戻す)
- 自動生成物をそのまま保管するだけのケース (公開文書化しない)

次のケースでは他スキルを主とし、本スキルを補助で使う。

- API 契約の厳密性検証が主題: `api-contract`
- 設計成果物の構造定義が主題: `design-doc`
- 文書以外の実装工程が主題: `spec-driven-development`

## Core Principles (核原則)

| 原則 | 具体ルール | 日本語適用例 / 英語適用例 |
|---|---|---|
| Words (用語一貫性) | 同じ概念に同じ語を使う。略語は初出で展開。用語集への参照を置く。 | JP: 「負荷分散装置 (Load Balancer)」を初出で定義し、以後は「Load Balancer」に統一。 EN: Define "SLA (Service Level Agreement)" once and use "SLA" consistently. |
| Active voice (能動態) | 可能な限り主語を明示し、行為者を前に置く。受動態を必要最小限にする。 | JP: 「設定は更新される」ではなく「CLI が設定を更新する」。 EN: "The server returns 200" instead of "200 is returned." |
| Clear sentences | 1 文 1 主張を原則化。曖昧語を削除。指示語の参照先を明示。 | JP: 「この処理」は避け「トークン更新処理」と書く。 EN: Replace "this" with "the retry policy". |
| Short sentences | 長文を分割し、従属節を減らす。接続語を最小化。 | JP: 100 字超の文を 2 文以上に分ける。 EN: Split sentences longer than ~80 characters when possible. |
| Lists and tables | 順序不要は箇条書き、順序必須は番号、比較は表を使う。 | JP: 手順は番号付き 1..n。 EN: Use table for option comparison (latency, cost, risk). |
| Paragraphs | 1 段落 1 トピック。冒頭文に要点を書く。補足は後ろに置く。 | JP: 段落先頭で「この節は認証方式を説明する」。 EN: First sentence states the paragraph intent. |
| Audience | 読み手の既知・未知・目的を明確化してから書く。 | JP: 「対象: 新規参画エンジニア」。 EN: "Audience: backend engineers new to this service." |
| Documents (冒頭で要点) | 冒頭 2-3 文で Objective/Summary/TL;DR を示す。長文は分割。 | JP: 先頭に「何を変えるか・なぜか・影響」を記述。 EN: Start with scope, non-goals, and key outcomes. |
| Self-editing | 書いた後に必ず自己編集。音読、時間を置く、LLM レビューを最低 1 回。 | JP: 音読して語尾重複を修正。 EN: Ask LLM to detect ambiguity and passive overuse. |

## Writing Process (執筆フロー)

### Step 1: Audience 設定

- 誰が読むかを明示する
- 読み手がすでに知っている前提知識を列挙する
- 読み手が学習したいことを 3 件以内で列挙する
- 読み手の業務コンテキスト (開発、運用、レビュー、意思決定) を記録する

記述テンプレート:

```markdown
Audience
- Primary: バックエンド開発者
- Secondary: QA, SRE

Known
- REST API 基本
- JWT の概念

Need to learn
- 本 API の認証フロー
- エラーコードの使い分け
- 破壊的変更の扱い
```

### Step 2: Documents 骨格

- 冒頭に Objective / Summary / TL;DR を 2-3 文で置く
- スコープ (含む) と非スコープ (含まない) を分ける
- 前提条件 (環境、権限、依存) を明記する
- 長文は H2/H3 に分割し、必要なら別ファイルに分離する

推奨順序:

1. Objective
2. Summary
3. Scope / Non-goals
4. Prerequisites
5. Main Content
6. Verification

### Step 3: Paragraphs / Sentences 執筆

- 1 段落 1 トピックを厳守する
- 1 文 1 アイデアを優先する
- 能動態を過半数にする
- 曖昧な指示語を具体語に置換する
- 箇条書きの並列構造を揃える

変換ルール例:

- NG: 「この機能は、設定が不十分な場合にエラーが返される。」
- OK: 「API は、設定が不十分な場合に `CONFIG_INVALID` を返す。」

### Step 4: Self-editing

- 音読して引っかかる箇所を修正する
- 可能なら一晩寝かせて再読する
- LLM に編集観点を与えてレビューさせる
- 最後にチェックリストで検証する

LLM 依頼プロンプト例:

```markdown
次の文章を technical writing 観点でレビューしてください。
観点:
1. 能動態比率
2. 1文の長さ
3. 曖昧な代名詞
4. 用語一貫性
5. 冒頭要約の明確性

問題箇所を行単位で示し、改善案を短文で提案してください。
```

## Sentence-Level Rules (文レベルのルール)

短文化の戦略を適用する。

- 1 文 1 アイデアに分解する
- 並列構造を使うときは文法形を揃える
- 従属節が長い場合は独立文に分割する
- 接続詞を減らし、論理関係は段落構成で示す
- 省略語や代名詞で文を短くしすぎない

能動態変換の例:

- 日本語
  - Passive: 「トークンはサーバーによって更新される」
  - Active: 「サーバーがトークンを更新する」
- 英語
  - Passive: "The request is validated by the gateway."
  - Active: "The gateway validates the request."

曖昧な代名詞を除去する。

- NG: 「これを設定した後、それを適用する」
- OK: 「`retry_count` を設定した後、`deploy` コマンドを実行する」

- NG: "This improves it."
- OK: "This cache policy reduces API latency by 20%."

避ける語尾・語感:

- 「〜的な」「〜みたいな」「〜などなど」
- 「適切に」「必要に応じて」だけで終わる文
- 主語のない手順文

## Word-Level Rules (語彙レベル)

専門用語は初出で定義する。

- 形式: 日本語訳 + 英語原語 + 役割
- 例: 「負荷分散装置 (Load Balancer): 複数サーバーへトラフィックを分散する装置」

略語・頭字語は初出で展開する。

- 例: `SLA = Service Level Agreement`
- 例: `SLO = Service Level Objective`
- 例: `RTO = Recovery Time Objective`

同じ概念に同じ単語を使う。

- NG: サーバ / サーバー / server が混在
- OK: 「サーバー」に統一し、英語表記が必要な箇所だけ `(server)` を併記

シノニムを避ける対象:

- ユーザー / 利用者 / エンドユーザー
- 失敗 / エラー / 異常
- 設定 / コンフィグ / 構成

日本語表記のバランスを調整する。

- カタカナ語を連続させすぎない
- 漢字が密集した場合はひらがなを挟む
- ひらがな連続で意味が曖昧なら漢字化する
- 文書全体で表記揺れ辞書を管理する

用語辞書テンプレート:

```markdown
| 用語 | 定義 | 使用ルール |
|---|---|---|
| サーバー | API を提供する実行環境 | 「サーバー」で統一。server はコード内のみ。 |
| デプロイ | 変更を環境へ反映する操作 | release と混同しない。 |
| 障害 | 期待機能を満たさない継続状態 | 一時エラーと区別して使う。 |
```

## Lists & Tables (箇条書き・表)

箇条書き (bulleted) を使う条件:

- 順序が不要な集合
- 注意点や前提条件の列挙
- 複数オプションの並列提示

番号付き (numbered) を使う条件:

- 実行順序がある手順
- 失敗時の分岐があるオペレーション
- 再現手順や検証シナリオ

表 (table) を使う条件:

- 属性比較
- 対応関係の一覧
- 用語定義と運用ルールの対応

並列構造の必須化ルール:

- 文頭が動詞なら全項目を動詞で揃える
- 文頭が名詞なら全項目を名詞で揃える
- 体言止めと述語終止を混在させない

例 (NG → OK):

- NG
  - 監視設定を追加する
  - アラート閾値
  - Runbook を更新した
- OK
  - 監視設定を追加する
  - アラート閾値を定義する
  - Runbook を更新する

## Documents-Level Rules (文書レベル)

冒頭で要点を示す。

- 最初の 2-3 文で「何を」「なぜ」「影響」を書く
- 意思決定文書は「結論」を先に置く
- 手順文書は「完了状態」を先に置く

スコープと前提条件を明確に分離する。

- Scope: この文書が扱う範囲
- Non-goals: 扱わない範囲
- Prerequisites: 読者が先に満たす条件

大規模文書の分割ルール:

- 100 行を超える H2 セクションは別ファイル分割を検討する
- 200 行を超える単一ファイルは索引を追加する
- 300 行を超える場合は章単位の分離を原則化する

図表キャプションで文脈を補う。

- 図の目的を 1 文で示す
- どこを見るべきかを 1 文で示す
- 読み手が次に取る行動を 1 文で示す

キャプション例:

- 「図 2 は認証フローの分岐を示す。失敗時は右側の `401` 系列を参照する。実装時はステップ 3 のミドルウェア設定を優先する。」

## Self-Editing Techniques (自己編集)

音読で不自然さを検出する。

- 句読点が多すぎる文を分割する
- 語尾の連続 (です/ます/する) を調整する
- 意味が飛ぶ箇所に接続語や主語を追加する

一晩寝かせてから再読する。

- 当日の勢いで書いた前提漏れを発見しやすい
- 読み手視点に戻りやすい
- 重複説明を削りやすい

LLM (Claude / ChatGPT) に編集依頼する。

- 指摘観点を固定してレビューさせる
- 修正案だけでなく理由を出させる
- 採用しない提案は根拠を明記する

同僚レビューでセルフレビューを代替できる。

- 最低 1 名のレビューを推奨する
- 観点チェックリストを添付する
- レビュー反映ログを残す

自己編集チェック例:

- [ ] 受動態が連続していない
- [ ] 代名詞が具体語に置換されている
- [ ] 用語定義へのリンクがある
- [ ] 要点が冒頭 2-3 文にある

## HELIX 連携

対象ドキュメント種別:

- L1 要件書
- L2 設計書 (`D-ARCH`, `D-API` など)
- L3 API 契約 (`D-CONTRACT`)
- L7 リリースノート

併用推奨スキル:

- [`documentation-and-adrs`](../documentation-and-adrs/SKILL.md)
- [`spec-driven-development`](../spec-driven-development/SKILL.md)
- [`planning-and-task-breakdown`](../planning-and-task-breakdown/SKILL.md)

`helix skill search` で発火しやすいタスク例:

- 「API ドキュメントを書く」
- 「リリースノートを作る」
- 「SKILL.md を追加する」
- 「README を整理する」
- 「ADR を更新する」

ゲートとの関係:

- G2: 設計文書の明確性・一貫性を担保する
- G4: 実装結果と文書差分の整合を確認する
- G6: RC 判定時に運用・利用者向け文書の完成度を確認する

## Japanese Writing Additional Rules (日本語執筆追加ルール)

能動態を優先する。

- 「〜される」を見つけたら「〜する」に変換できるか検討する
- 行為者が不明な場合は主語を補う

カタカナ表記を統一する。

- 「サーバー」か「サーバ」かを文書冒頭で決める
- 「ユーザー」か「ユーザ」も同様に固定する

句読点の運用を安定させる。

- 1 文の「、」は 2-3 個までを目安にする
- 「。」で文を閉じる前に 1 主張か確認する

漢字・ひらがなの比率を意識する。

- 漢字は 30-40% を目安にし、読みにくい密度を避ける
- 難読語が続く場合は言い換えを優先する

専門用語の和訳併記を行う。

- 例: 「負荷分散装置 (Load Balancer)」
- 例: 「継続的インテグレーション (Continuous Integration)」

日本語文体の推奨:

- 常体と敬体を混在させない
- 文書単位で「です・ます」または「である」を固定する
- 箇条書き終端の句点有無を統一する

## Common Rationalizations (よくある言い訳)

| 言い訳 | 実態 |
|---|---|
| 「英語のほうが短く書ける」 | 読み手が日本人主体なら日本語が正解。短さより読み手の認知負荷を優先する。 |
| 「専門家向けだから用語定義は不要」 | 専門家でも分野外は初心者になる。初出定義で認識齟齬を防ぐ。 |
| 「後で推敲すれば良い」 | 未推敲文書はそのまま残り負債化する。書いた直後に self-edit を実施する。 |
| 「実装が先で文書は最後でいい」 | 文書が遅れるとレビューと運用移管が止まる。最小版を先に置き段階更新する。 |
| 「LLM が書いたから品質は十分」 | 生成文は表記揺れと事実誤認を含む。人間が検証しない限り品質は保証できない。 |

## Red Flags

次の兆候がある場合、このスキルは十分に適用されていない。

- 1 文が 80 字超 (英語) / 100 字超 (日本語)
- 能動態と受動態が同じ段落で無秩序に混在している
- `this`、`it`、`それ`、`そのような` が連続している
- 文書冒頭に要点 (Objective / Summary / TL;DR) がない
- 箇条書きの並列構造が崩れている
- 同じ概念に複数の語を使っている (サーバ / サーバー / server)
- 初出用語の定義がなく、略語だけが先行している
- セクション順序が目的に対して不自然で、読み手が迷子になる

## Verification

- [ ] 冒頭に要点 (Objective / Summary / TL;DR) が 2-3 文で書かれている
- [ ] 読み手 (Audience) が明示されている
- [ ] 用語・略語が初出で定義されている
- [ ] 1 文の長さが目安以内 (英語 80 字 / 日本語 100 字)
- [ ] 能動態が過半数を占める
- [ ] 箇条書き・表の並列構造が揃っている
- [ ] Self-editing を 1 回以上実施した (音読 or LLM レビュー or 一晩置く)
- [ ] 出典: https://developers.google.com/tech-writing を参照

補助確認:

- [ ] `documentation-and-adrs` との整合を確認した
- [ ] `spec-driven-development` の成果物粒度と矛盾しない
- [ ] `planning-and-task-breakdown` のタスク分解と文書構成が対応している
- [ ] Google Technical Writing の方針を直接転載せず要約で記述した

出典とライセンス配慮:

- Source: https://developers.google.com/tech-writing
- License note: Google Technical Writing materials are provided under CC-BY 4.0.
- This skill summarizes principles and adds HELIX-specific operational guidance.

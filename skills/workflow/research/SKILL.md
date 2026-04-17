---
name: research
description: G1R 事前調査ゲートで発火する調査スキル。一次情報収集から research_report 作成までを標準化する
metadata:
  helix_layer: L1
  triggers:
    - G1R 事前調査時
    - 技術選定前の調査時
    - ライブラリ比較時
    - 未知領域着手時
  verification:
    - "research_report が docs/research/ に .md で存在"
    - "一次情報 URL ≥3件"
    - "adoption (採用/不採用の理由) が明記"
compatibility:
  claude: true
  codex: true
---

# Research スキル（G1R 事前調査）

## 目的

G1R（事前調査ゲート）で必要な調査を、
一次情報に基づいて短時間で再現可能な形にする。

本スキルの成果物は `research_report` であり、
L2 設計または L4 実装に接続できる入力を作る。

---

## 使用タイミング

以下のいずれかに該当したら適用する。

- 外部 API 連携の新規導入・更新
- 認証/認可方式の比較
- 新フレームワーク/新ライブラリの採用判断
- 法令/規約/運用要件で誤認リスクがある領域
- 既存知見が薄い未知領域

該当しない場合は、
「事前調査: スキップ（理由: ...）」を記録して次へ進む。

---

## 保存先規定（正本）

`research_report` の正本フォーマットは **`.md`**。

- 保存先: `docs/research/YYYY-MM-DD-{topic}.md`
- 本文内に YAML ブロックを含める
- `.yaml` 単独ファイルは作成しない

`layer-interface.md`（research_report 仕様）に準拠する。

---

## research_report テンプレート（.md + YAML block）

```text
# Research Report: {topic}

~~~yaml
research_report:
  topic: "{topic}"
  date: "YYYY-MM-DD"
  scope:
    in_scope:
      - "今回の調査対象"
    out_of_scope:
      - "今回は扱わない範囲"
  sources:
    - url: "https://official.example.com/docs/..."
      type: "official|rfc|repo-issue|blog|community"
      summary: "1行要約"
      relevance: "high|medium|low"
  findings:
    - "重要な発見"
  adoption:
    decision: "adopt|reject|defer"
    reason:
      - "採用/不採用の理由1"
      - "採用/不採用の理由2"
  risks:
    - "残存リスク"
  open_blockers: []
  next_action:
    - "次アクション"
~~~

## Notes

- 設計/実装への影響
- 代替案
- 未解決事項
```

最小要件:

- 一次情報 URL を 3 件以上
- `adoption` を必ず明記
- `open_blockers` が空でない場合は G1R fail 扱い

---

## 一次情報優先度

優先順位（高→低）:

1. 公式ドキュメント / RFC / 仕様書
2. 公式 GitHub リポジトリ（Issue / Discussion / Release note）
3. 技術ブログ（Qiita / Zenn / dev.to 等、要クロスチェック）
4. コミュニティ QA（Stack Overflow 等、鮮度確認）

運用ルール:

- 低優先情報のみで結論を確定しない
- 仕様差分は公式ソースで必ず再確認する
- 引用 URL は消えにくい恒久リンクを優先する

---

## tools/web-search 連携

`tools/web-search` は公開情報の網羅収集に使う。

推奨フロー:

1. クエリを分解（仕様/制約/既知障害/移行）
2. 公式ドメイン優先で探索
3. 候補 URL を research_report に一次メモ
4. 一次情報のみで結論を再構成

注意:

- 機密情報（顧客名、内部 URL、秘密情報）を検索語に含めない
- オフライン等で検索不可の場合は `status: blocked` を明記

---

## tools/ai-search の使い分け

`tools/ai-search` は「要約・比較・論点整理」に使う。

使い分け指針:

- 収集（事実取得）: `tools/web-search`
- 整理（比較/要約）: `tools/ai-search`

禁止事項:

- `tools/ai-search` の要約だけで採用判断しない
- 元 URL 未確認の主張を最終結論に使わない

---

## エスカレーション基準

以下は人間確認にエスカレーションする。

- 本番影響が大きい採用判断
- 認証・決済・個人情報・ライセンスの解釈
- 一次情報同士で矛盾し、結論が収束しない
- 開発期限内に `open_blockers` を解消できない

エスカレーション時の提出物:

- research_report
- 判断保留ポイント
- 推奨案（A/B）とトレードオフ

---

## G1R 判定チェック（実務用）

- research_report が `docs/research/` 配下に `.md` で存在する
- 一次情報 URL が 3 件以上ある
- `adoption` に採用/不採用の理由がある
- `open_blockers` が 0 件、またはエスカレーション済み

---

## 最小実行手順（10-20分版）

1. topic と調査範囲を 3 行で定義
2. 公式情報を 3-5 件収集
3. 代替案を 2 案に絞る
4. `adoption` と `risks` を記述
5. `docs/research/YYYY-MM-DD-{topic}.md` に保存

完了条件は「検索した」ではなく、
「再利用可能な research_report が残っている」こと。

> 目的: L3-L4 で「schema を LLM 生成段階から強制する手段 (Structured Outputs / Tool Use / Constrained Decoding) をどれにするか」で迷うときに開く。後段バリデーション依存を排除する判断軸。

# [08] 前段の生成制約

## 前提となるスキル

- [07] スキーマ導出

## 適用判定

- スキーマを生成段階から強制する時
- LLMの出力を確実に構造化する時
- 後段バリデーションの負担を軽減する時

## 担当する判断

導出したスキーマを、LLMの生成段階で強制する手段を選択・実装する。

## 中核原則

スキーマは「出力後に検証する」だけでなく「生成段階で縛る」のが原則。確率的生成そのものをスキーマに従わせることで、後段バリデーションは「念のための二重チェック」に責務が縮退する。

「JSONで返してください」のような自然言語指示だけに頼らない。生成段階での型強制機構を必ず使う。

## 判断軸

### 軸1：どの強制機構を使うか

```
使用するLLMプロバイダ・機構は？
├── OpenAI → Structured Outputs（response_format）
├── Anthropic → Tool Use（tools定義のスキーマ）
├── Google Gemini → Response Schema
├── ローカルLLM → Constrained Decoding（Outlines / LM-format-enforcer等）
└── フレームワーク経由 → Instructor / BAML / DSPy
```

### 軸2：Function Calling か Structured Output か

```
タスクの性質は？
├── 単一の構造化出力が欲しい → Structured Output
├── 外部ツール呼び出しと統合したい → Function Calling / Tool Use
└── 複数の出力候補を選ばせたい → Function Calling（複数tool定義）
```

### 軸3：制約の厳密度

```
スキーマ違反時の挙動は？
├── 厳密モード（strict）→ スキーマ違反時にエラー
└── 寛容モード → スキーマ違反時に最善努力で生成
```

厳密モードを推奨。寛容モードは前段制約として弱く、後段バリデーション依存になる。

## 主要な実装パターン

### パターン1：OpenAI Structured Outputs

```python
from openai import OpenAI
from pydantic import BaseModel

class PREPOutput(BaseModel):
    point: str
    reason: str
    examples: list[str]
    conclusion: str

client = OpenAI()
response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[...],
    response_format=PREPOutput,
)
```

### パターン2：Anthropic Tool Use

```python
import anthropic

tools = [{
    "name": "submit_prep_output",
    "description": "PREP法に従った出力を提出する",
    "input_schema": {
        "type": "object",
        "properties": {
            "point": {"type": "string"},
            "reason": {"type": "string"},
            "examples": {"type": "array", "items": {"type": "string"}},
            "conclusion": {"type": "string"}
        },
        "required": ["point", "reason", "examples", "conclusion"]
    }
}]

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-4-7",
    tools=tools,
    tool_choice={"type": "tool", "name": "submit_prep_output"},
    messages=[...]
)
```

### パターン3：Instructor（フレームワーク）

```python
import instructor
from openai import OpenAI

client = instructor.from_openai(OpenAI())
result = client.chat.completions.create(
    model="gpt-4o",
    response_model=PREPOutput,
    messages=[...]
)
```

## 適用手順

1. スキル07で定義したスキーマを確認
2. 使用するLLMプロバイダに応じた強制機構を選択
3. Function Calling か Structured Output かを判定
4. スキーマを強制機構が要求する形式に変換
5. 厳密モードで設定
6. 失敗時のリトライ戦略を決定
7. 実装に組み込み

## ハーネスエンジニアリングとしての位置づけ

このスキルが扱うのは、業界で「ハーネスエンジニアリング」と呼ばれている領域そのもの。LLMという確率的コンポーネントを、型契約で囲んで決定論的なシステムの構成要素として扱うための装具。

ハーネスは外部から型を被せているように見えて、実は LLM 内部の型呼び出しと、外部の型契約を一致させる作業をしている。両者が一致した時、出力が安定する。

## アンチパターン

- 「JSONで返してください」のような自然言語指示だけに頼っている
- Structured Outputs / Function Calling が使えるのに使っていない
- 寛容モードで運用し、後段バリデーション依存になっている
- スキーマを変換せず、生成段階で縛っていない
- リトライ戦略を持たず、1回失敗したらそのまま落としている

## 成果物

- 生成段階でスキーマを強制する実装
- リトライ戦略
- 失敗時のフォールバック方針

これが揃えば、スキル09（後段の責務分離）に進める。

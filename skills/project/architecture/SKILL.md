---
name: architecture
description: architecture関連タスク時に使用
---

# アーキテクチャスキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- 新機能設計時
- 構造変更時
- サービス追加時

---

## システム構成

```
{{SYSTEM_DIAGRAM}}

例:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  Database   │
│  (Next.js)  │     │  (FastAPI)  │     │ (PostgreSQL)│
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## ディレクトリ構造

```
{{PROJECT_ROOT}}/
├── backend/
│   ├── app/
│   │   ├── api/          # APIエンドポイント
│   │   ├── models/       # DBモデル
│   │   ├── services/     # ビジネスロジック
│   │   ├── schemas/      # Pydantic schemas
│   │   └── core/         # 設定、共通
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js App Router
│   │   ├── components/   # UIコンポーネント
│   │   ├── hooks/        # カスタムフック
│   │   ├── services/     # API呼び出し
│   │   └── types/        # 型定義
│   └── tests/
│
└── docs/
```

---

## レイヤー構成

```
┌─────────────────────────────────────────┐
│  Presentation (API / UI)                │
├─────────────────────────────────────────┤
│  Application (Services / Use Cases)     │
├─────────────────────────────────────────┤
│  Domain (Models / Business Logic)       │
├─────────────────────────────────────────┤
│  Infrastructure (DB / External APIs)    │
└─────────────────────────────────────────┘
```

### 依存関係ルール

```
上位 → 下位 のみ依存可
下位 → 上位 は禁止

✅ Service → Model
❌ Model → Service
```

---

## 主要サービス

| サービス | パス | 責務 |
|---------|------|------|
| {{SERVICE_1}} | `{{PATH_1}}` | {{DESCRIPTION_1}} |
| {{SERVICE_2}} | `{{PATH_2}}` | {{DESCRIPTION_2}} |
| {{SERVICE_3}} | `{{PATH_3}}` | {{DESCRIPTION_3}} |

---

## サービス実装ルール

### 新規サービス追加時

```
1. 既存サービスで代替できないか確認
2. 単一責任を満たす設計
3. インターフェース定義
4. 実装
5. テスト追加
6. ドキュメント更新
```

### 禁止事項

```
❌ サービス間の循環依存
❌ サービス内での直接DB操作（Repository経由）
❌ サービス内での直接外部API呼び出し（Client経由）
```

---

## 設計判断記録

### ADR (Architecture Decision Record)

```markdown
## ADR-XXX: {{タイトル}}

### Status
Accepted / Deprecated / Superseded

### Context
- 背景・課題

### Decision
- 決定内容

### Consequences
- 結果・影響
```

### 記録場所

`/docs/adr/` に保存

---

## 拡張ポイント

| 機能追加 | 変更箇所 |
|---------|---------|
| 新規API | `api/` + `services/` + `schemas/` |
| 新規画面 | `app/` + `components/` |
| 新規DB | `models/` + migrations |
| 外部連携 | `services/external/` |

---
name: i18n
description: i18n関連タスク時に使用
metadata:
  helix_layer: L2
  triggers:
    - 多言語対応時
    - ローカライゼーション時
    - 翻訳管理時
  verification:
    - 翻訳キー網羅
    - 言語切替動作確認
compatibility:
  claude: true
  codex: true
---

# 多言語対応（i18n）スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- 多言語対応実装時
- タイムゾーン対応時
- グローバル展開時

---

## 1. i18n基礎

### 用語

| 用語 | 説明 |
|------|------|
| i18n | Internationalization（国際化） |
| l10n | Localization（地域化） |
| Locale | 言語＋地域の組み合わせ（ja-JP, en-US） |
| Translation | 翻訳テキスト |

### Locale形式

```
言語コード-地域コード
例:
- ja-JP: 日本語（日本）
- en-US: 英語（アメリカ）
- en-GB: 英語（イギリス）
- zh-CN: 中国語（簡体字）
- zh-TW: 中国語（繁体字）
```

---

## 2. フロントエンド i18n

### Next.js + next-intl

```typescript
// messages/ja.json
{
  "common": {
    "submit": "送信",
    "cancel": "キャンセル",
    "loading": "読み込み中..."
  },
  "auth": {
    "login": "ログイン",
    "logout": "ログアウト",
    "welcome": "{name}さん、ようこそ"
  },
  "errors": {
    "required": "{field}は必須です",
    "invalid_email": "メールアドレスの形式が正しくありません"
  }
}

// messages/en.json
{
  "common": {
    "submit": "Submit",
    "cancel": "Cancel",
    "loading": "Loading..."
  },
  "auth": {
    "login": "Log in",
    "logout": "Log out",
    "welcome": "Welcome, {name}"
  },
  "errors": {
    "required": "{field} is required",
    "invalid_email": "Invalid email format"
  }
}
```

```typescript
// app/[locale]/layout.tsx
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';

export default async function LocaleLayout({
  children,
  params: { locale }
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

```typescript
// コンポーネントでの使用
'use client';
import { useTranslations } from 'next-intl';

export function LoginForm() {
  const t = useTranslations('auth');
  
  return (
    <form>
      <button type="submit">{t('login')}</button>
      <p>{t('welcome', { name: 'John' })}</p>
    </form>
  );
}
```

### React i18next

```typescript
// i18n/config.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      ja: { translation: require('./locales/ja.json') },
      en: { translation: require('./locales/en.json') },
    },
    lng: 'ja',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

// コンポーネント
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t, i18n } = useTranslation();
  
  return (
    <div>
      <p>{t('common.submit')}</p>
      <button onClick={() => i18n.changeLanguage('en')}>
        English
      </button>
    </div>
  );
}
```

---

## 3. バックエンド i18n

### FastAPI

```python
# i18n/translations.py
from pathlib import Path
import json

class Translator:
    def __init__(self):
        self.translations = {}
        self._load_translations()
    
    def _load_translations(self):
        locales_dir = Path(__file__).parent / "locales"
        for file in locales_dir.glob("*.json"):
            locale = file.stem
            with open(file, encoding="utf-8") as f:
                self.translations[locale] = json.load(f)
    
    def get(self, key: str, locale: str = "ja", **kwargs) -> str:
        """翻訳テキストを取得"""
        keys = key.split(".")
        value = self.translations.get(locale, self.translations["en"])
        
        for k in keys:
            value = value.get(k, key)
            if isinstance(value, str):
                break
        
        # プレースホルダー置換
        if kwargs:
            value = value.format(**kwargs)
        
        return value

translator = Translator()

# 使用例
from fastapi import Request, Depends

def get_locale(request: Request) -> str:
    """Accept-Languageヘッダーからlocaleを取得"""
    accept_language = request.headers.get("Accept-Language", "ja")
    return accept_language.split(",")[0].split("-")[0]

@app.get("/api/greeting")
async def greeting(locale: str = Depends(get_locale)):
    return {"message": translator.get("common.welcome", locale)}
```

### エラーメッセージの多言語化

```python
# エラー定義
class AppError(Exception):
    def __init__(self, code: str, locale: str = "ja", **kwargs):
        self.code = code
        self.message = translator.get(f"errors.{code}", locale, **kwargs)
        super().__init__(self.message)

# 使用
raise AppError("user_not_found", locale="en")
# → "User not found"

raise AppError("validation_failed", locale="ja", field="メールアドレス")
# → "メールアドレスの検証に失敗しました"
```

---

## 4. 日付・時刻の国際化

### タイムゾーン対応

```python
from datetime import datetime
from zoneinfo import ZoneInfo

# UTC で保存
utc_now = datetime.now(ZoneInfo("UTC"))

# 表示時にローカルタイムゾーンに変換
def to_local_time(dt: datetime, timezone: str) -> datetime:
    return dt.astimezone(ZoneInfo(timezone))

# 例
utc_time = datetime(2025, 1, 15, 10, 0, 0, tzinfo=ZoneInfo("UTC"))
tokyo_time = to_local_time(utc_time, "Asia/Tokyo")  # 2025-01-15 19:00:00
la_time = to_local_time(utc_time, "America/Los_Angeles")  # 2025-01-15 02:00:00
```

### 日付フォーマット

```typescript
// JavaScript Intl API
const date = new Date('2025-01-15');

// 日本語
new Intl.DateTimeFormat('ja-JP', {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
}).format(date);
// → "2025年1月15日"

// 英語（アメリカ）
new Intl.DateTimeFormat('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
}).format(date);
// → "January 15, 2025"

// 相対時間
const rtf = new Intl.RelativeTimeFormat('ja', { numeric: 'auto' });
rtf.format(-1, 'day');  // → "昨日"
rtf.format(2, 'hour');  // → "2時間後"
```

---

## 5. 数値・通貨の国際化

### 数値フォーマット

```typescript
// 数値
new Intl.NumberFormat('ja-JP').format(1234567.89);
// → "1,234,567.89"

new Intl.NumberFormat('de-DE').format(1234567.89);
// → "1.234.567,89"

// パーセント
new Intl.NumberFormat('ja-JP', { style: 'percent' }).format(0.25);
// → "25%"
```

### 通貨フォーマット

```typescript
// 日本円
new Intl.NumberFormat('ja-JP', {
  style: 'currency',
  currency: 'JPY'
}).format(1234);
// → "￥1,234"

// 米ドル
new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD'
}).format(1234.56);
// → "$1,234.56"

// ユーロ
new Intl.NumberFormat('de-DE', {
  style: 'currency',
  currency: 'EUR'
}).format(1234.56);
// → "1.234,56 €"
```

---


---

## 詳細ガイド

以下は references/management.md を参照:
- 翻訳管理（翻訳キー命名、翻訳ワークフロー）
- 実装チェックリスト
- 注意点（RTL対応、テスト等）

---

## チェックリスト

### 実装前

```
[ ] 対応言語を決定
[ ] 翻訳フローを決定
[ ] ライブラリ選定
```

### 実装中

```
[ ] 全文字列を外部化
[ ] 日付・数値をロケール対応
[ ] 言語切り替え実装
```

### リリース前

```
[ ] 全言語でUIテスト
[ ] 翻訳漏れチェック
[ ] 長いテキストのレイアウト確認
```

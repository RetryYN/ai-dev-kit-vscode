> 目的: 多言語運用の翻訳管理とキー設計を整備する際の実務ガイドとして参照。

## 6. 翻訳管理

### 翻訳ファイル構成

```
locales/
├── ja/
│   ├── common.json
│   ├── auth.json
│   ├── errors.json
│   └── products.json
├── en/
│   ├── common.json
│   ├── auth.json
│   ├── errors.json
│   └── products.json
└── zh/
    └── ...
```

### 翻訳キーの命名規則

```
推奨:
✅ auth.login_button → "ログイン"
✅ errors.email_invalid → "メールアドレスが無効です"
✅ products.add_to_cart → "カートに追加"

避ける:
❌ button1 → 意味不明
❌ loginButtonText → キャメルケース混在
❌ ログインボタン → 日本語キー
```

### 翻訳漏れ検出

```typescript
// 未翻訳キーを検出するスクリプト
import ja from './locales/ja.json';
import en from './locales/en.json';

function findMissingKeys(source: object, target: object, path = ''): string[] {
  const missing: string[] = [];
  
  for (const key of Object.keys(source)) {
    const currentPath = path ? `${path}.${key}` : key;
    
    if (!(key in target)) {
      missing.push(currentPath);
    } else if (typeof source[key] === 'object') {
      missing.push(...findMissingKeys(source[key], target[key], currentPath));
    }
  }
  
  return missing;
}

// jaにあってenにないキー
const missingInEn = findMissingKeys(ja, en);
console.log('Missing in EN:', missingInEn);
```

---

## 7. 実装チェックリスト

### 文字列

```
[ ] ハードコードされた文字列がない
[ ] 翻訳キーが意味のある名前
[ ] プレースホルダーを使用（文字列結合しない）
[ ] 複数形対応（必要な言語）
```

### 日付・時刻

```
[ ] DBはUTCで保存
[ ] タイムゾーン情報を保持
[ ] 表示時にローカルタイムゾーンに変換
[ ] 日付フォーマットがロケール対応
```

### 数値・通貨

```
[ ] 数値フォーマットがロケール対応
[ ] 通貨コードを明示
[ ] 小数点・桁区切りがロケール対応
```

### UI/UX

```
[ ] 言語切り替えUIがある
[ ] 翻訳テキストの長さを考慮（ドイツ語は長い）
[ ] RTL言語対応（アラビア語、ヘブライ語）
[ ] フォントが多言語対応
```

---

## 8. 注意点

### よくある問題

```
❌ 文字列結合
// Bad
const message = "Hello, " + name + "!";

// Good
const message = t('greeting', { name });

❌ 日付フォーマットのハードコード
// Bad
const formatted = `${date.getMonth() + 1}/${date.getDate()}`;

// Good
const formatted = new Intl.DateTimeFormat(locale).format(date);

❌ タイムゾーン無視
// Bad
new Date().toISOString();  // ローカルタイムとUTCの混同

// Good
new Date().toISOString();  // 常にUTCと認識
```

### テスト

```typescript
// 各ロケールでのテスト
describe('DateFormatter', () => {
  test.each([
    ['ja-JP', '2025年1月15日'],
    ['en-US', 'January 15, 2025'],
    ['de-DE', '15. Januar 2025'],
  ])('formats date for %s', (locale, expected) => {
    const date = new Date('2025-01-15');
    expect(formatDate(date, locale)).toBe(expected);
  });
});
```

---


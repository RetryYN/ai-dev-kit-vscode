# ツール別Tips・学習と改善
> 目的: ツール別Tips・学習と改善 の要点を把握し、設計・実装判断を行う際のクイックリファレンスとして参照

> 出典: ai-coding/SKILL.md §6, §7

## ツール別Tips

### Claude Code

```bash
# 効果的なコマンド
claude                    # 起動
claude --chrome           # ブラウザ連携

# 効果的な指示
> @src/api/users.ts この関数をリファクタリングして
> テストを追加して。カバレッジ80%以上で。
> 実装前に設計を説明して

# 迷走防止
> 完了条件: 〇〇が〇〇になること
> 確認方法: curl で〇〇を実行
```

### GitHub Copilot

```typescript
// コメントで誘導
// ユーザー認証関数
// 引数: email, password
// 戻り値: User | null
// エラー時: throw AuthError
async function authenticateUser(email: string, password: string): Promise<User | null> {
  // ← ここでTab
}

// テスト生成
// @test authenticateUser
// 正常系: 有効な認証情報で成功
// 異常系: 無効なパスワードでnull
// 異常系: 存在しないユーザーでnull
```

### Cursor Composer

```
# 範囲選択して指示
Cmd + K → 選択範囲

指示例:
- 「この関数をasync/awaitに変換」
- 「エラーハンドリングを追加」
- 「TypeScriptの型を追加」
- 「テストを生成」
```

## 学習と改善

### プロンプト改善サイクル

```
1. プロンプトを書く
2. 出力を評価
3. 問題点を特定
4. プロンプトを改善
5. 繰り返し
```

### 効果的だったプロンプトの記録

```markdown
## プロンプト集

### API実装（成功率高）
「{{endpoint}} を実装して。
入力: {{input}}
出力: {{output}}
エラー: {{errors}}
テストも書いて。」

### バグ修正（成功率高）
「エラー: {{error}}
ファイル: {{file}}
再現: {{steps}}
原因を特定して修正して。」
```

# Security Guidelines For Prompt Context Files

この文書は、`CLAUDE.md`、`SKILL.md`、`references/*.md`、および関連する補助ドキュメントに何を書いてよいかを定義する。

## 書いてよいもの

- 公開可能な設計方針、アーキテクチャ概要、コーディング規約
- 実行コマンド、ビルド手順、テスト手順
- ダミー値だと明示された設定キー名や環境変数名
- 社内情報を含まない URL、サンプル payload、抽象化したログ

## 書いてはいけないもの

- API キー、アクセストークン、Bearer トークンの実値
- 顧客や社員のメールアドレス、電話番号、郵便番号、住所
- 社内専用 URL、VPN 内ホスト名、未公開リポジトリ URL
- 秘密鍵、証明書、接続文字列、認証ヘッダ付きログ
- 実運用の `.env` 内容や認証済み CLI 出力の貼り付け

## 良い例と悪い例

良い例:

- `OPENAI_API_KEY` のような環境変数名だけを書く
- `https://service[.]corp[.]example` のように無害化して説明する
- `user+masked(at)example.com` のように可逆でない形に崩す
- `Bearer <redacted>` や `<private-key-path>` のように構造だけ示す

悪い例:

- キー全文、トークン全文、署名付き URL をそのまま貼る
- 本人特定可能な連絡先をレビュー用メモに残す
- 社内 Wiki や監視 URL を平文のまま `references/` に置く
- PEM ブロックや証明書本文を Markdown に貼り付ける

## `CLAUDE.local.md` の使い方

- `CLAUDE.local.md` は Git 管理外のローカル補助ファイルとして使う
- 置くべきものは、個人用メモ、端末依存のパス、手元だけで有効な作業メモ
- 可能なら secret の実値ではなく、参照先だけを書く
- 実値が必要でも短期間で削除し、ローテーション可能な値だけに限定する

## Memory との使い分け

- `~/.claude/projects/.../memory` には、長期に保持したい非機密の判断履歴や運用知識を書く
- 再利用価値が高いが公開できる情報だけを残す
- secret、PII、社内 URL、認証状態付きの観測結果は memory に保存しない
- 永続化前に「そのまま第三者へ共有して問題ないか」で判定する

## 社内 URL・メール・秘密鍵の扱い

- 社内 URL は平文で書かず、必要時は無害化した表記か説明文に置き換える
- メールアドレスは担当グループ名やロール名で代替し、個人アドレスを避ける
- 秘密鍵や証明書本文はファイルパスや Secret Manager 名で参照し、本文を複写しない
- ログ共有時はヘッダ、Cookie、クエリ文字列、接続先を必ずマスクする

## Git hooks

- `pre-commit` は staged 内容から secret らしい文字列を検知して commit を停止する
- `pre-push` は `CLAUDE.md`、`SKILL.md`、`references/*.md` の差分を見て secret と PII を検知する
- 警告を回避する標準手段は `--no-verify` だけとし、例外はレビュー記録を残す
- このリポジトリでは `bash scripts/install-git-hooks.sh` で hook を再導入できる

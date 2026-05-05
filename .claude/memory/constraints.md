# Constraints

- secret、PII、credential、API key を memory / docs / rules に書かない。
- 本番影響、認証、認可、決済、PII、ライセンス、外部 API / infrastructure / env 変更は人間確認なしに仕様確定しない。
- `.claude/agent-memory/` は runtime memory として Git 追跡しない。
- memory は短く保つ。長い履歴は docs/memory または該当 PLAN / retro に分離する。

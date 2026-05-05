# Rejected Approaches

- raw `codex exec` を通常導線として許可すること。
  - 理由: HELIX discipline、plan-only guard、approved guard、allowed-files guard が効かない。
- 「LLM への強い文言」だけで自動発火・工程遵守を保証すること。
  - 理由: 忘却やコンテキスト汚染で破られるため、hook / wrapper / gate の機械ガードが必要。

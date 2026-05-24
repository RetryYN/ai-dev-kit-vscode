# L7 scrum-to-discovery rename test design

## Scope

- 対象設計: [docs/v2/L7-design/L7-scrum-to-discovery-rename-design.md](../L7-design/L7-scrum-to-discovery-rename-design.md)
- 対象 PLAN: [docs/plans/L7/L7-scrum-to-discovery-renameplan.md](../../plans/L7/L7-scrum-to-discovery-renameplan.md)
- テスト実装: `cli/lib/tests/test_helix_discovery_alias.py`
- テスト実装: `cli/tests/helix-discovery.bats`

## Cases

- D1: `helix discovery` が 12 subcommand すべてで `--help` を返す。
- D2: `helix scrum` alias の stdout は `helix discovery` と一致する。
- D3: deprecated warning は stderr のみに出力され、stdout を汚染しない。
- D4: `HELIX_SUPPRESS_LEGACY_WARN=1` で warning を抑止できる。
- D5: `skills/agent-skills/helix-discovery/SKILL.md` が存在する。
- D6: `skills/agent-skills/helix-scrum/SKILL.md` に legacy note が存在する。
- D7: router/help/docs が `discovery` を公開し、`scrum` を alias として残す。

## Verification Mapping

- `cli/lib/tests/test_helix_discovery_alias.py`
  - D5, D6, router/shim existence
- `cli/tests/helix-discovery.bats`
  - D1, D2, D3, D4, D7

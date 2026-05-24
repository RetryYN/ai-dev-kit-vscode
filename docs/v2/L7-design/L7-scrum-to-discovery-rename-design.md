# L7 scrum-to-discovery rename design

## Scope

- 対象設計: [docs/plans/L7/L7-scrum-to-discovery-renameplan.md](../../plans/L7/L7-scrum-to-discovery-renameplan.md)
- parent_design: `HELIX-workflows/helix-process/discovery-workflow.md`
- テスト設計: [docs/v2/L7-test-design/L7-scrum-to-discovery-rename-test-design.md](../L7-test-design/L7-scrum-to-discovery-rename-test-design.md)

## Decision

- `cli/helix-discovery` を Discovery 正本 CLI として追加する。
- `cli/helix-scrum` は deprecated alias shim とし、stderr に warning を出して `helix-discovery` へ exec 転送する。
- runtime state path は Stage 1 では `.helix/scrum/` を維持し、`.helix/discovery/` への移行は後続 PLAN に送る。
- `helix discovery` を router/help/docs に登録し、`helix scrum` は alias として残す。

## Implementation

- 実装ファイル: `cli/helix-discovery`
- 実装ファイル: `cli/helix-scrum`
- 実装ファイル: `cli/helix`
- 実装ファイル: `cli/lib/command_mapper.py`
- 実装ファイル: `cli/helix-size`
- 実装ファイル: `cli/helix-mode`
- 実装ファイル: `skills/agent-skills/helix-discovery/SKILL.md`

## Compatibility

- `HELIX_SUPPRESS_LEGACY_WARN=1` で alias warning を抑止できる。
- `helix scrum` の既存呼び出しは継続動作する。
- `helix discovery` の user-facing help は Discovery 名義へ統一する。

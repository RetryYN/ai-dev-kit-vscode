# L7 scrum-to-discovery migration enum design

## Scope

- 対象 PLAN: [docs/plans/L7/L7-scrum-to-discovery-migration-enumplan.md](../../plans/L7/L7-scrum-to-discovery-migration-enumplan.md)
- parent_design: `HELIX-workflows/helix-process/discovery-workflow.md`
- テスト設計: [docs/v2/L7-test-design/L7-scrum-to-discovery-migration-enum-test-design.md](../L7-test-design/L7-scrum-to-discovery-migration-enum-test-design.md)

## Decisions

- runtime dir は Stage 3 以降に `.helix/scrum/` から `.helix/discovery/` へ移行し、`helix discovery migrate` で明示実行できる。
- `cli/lib/discovery_migrate.py` は data movement のみを担当し、manifest 検証、lock、idempotent skip、merge strategy を提供する。
- `cli/lib/discovery_compat.py` は `HELIX_DISCOVERY_COMPAT_STAGE`、`drive: scrum` の legacy compat、S-phase から D-phase への表示変換を担当する。
- `helix scrum` は Stage 1 では warning なし、Stage 2 以降で deprecated warning、Stage 4 では removal stub message を返す。
- Discovery の canonical mode / drive は `discovery` に統一し、`scrum` は read/write compat に限定する。
- DB state `S0-S3` は保持し、CLI 表示だけを `D0-D4` に変換する。`D4` は `decide_result=confirmed` から派生表示する。

## Implementation

- 実装ファイル: `cli/lib/discovery_compat.py`
- 実装ファイル: `cli/lib/discovery_migrate.py`
- 実装ファイル: `cli/helix-discovery`
- 実装ファイル: `cli/helix-scrum`
- 実装ファイル: `cli/helix-size`
- 実装ファイル: `cli/helix-mode`
- 実装ファイル: `cli/helix-doctor`
- 実装ファイル: `cli/lib/plan_validator.py`
- 実装ファイル: `cli/lib/command_mapper.py`
- 実装ファイル: `cli/lib/session_start_helpers.py`

## Trace

- ① 設計 → ② 実装: 上記ファイル群
- ① 設計 → ③ テスト設計: `docs/v2/L7-test-design/L7-scrum-to-discovery-migration-enum-test-design.md`
- ② 実装 → ① 設計: `cli/lib/discovery_compat.py`, `cli/lib/discovery_migrate.py`
- ③ テスト設計 → ④ テストコード: `cli/lib/tests/test_discovery_compat.py`, `cli/lib/tests/test_discovery_migrate.py`, `cli/tests/helix-discovery.bats`

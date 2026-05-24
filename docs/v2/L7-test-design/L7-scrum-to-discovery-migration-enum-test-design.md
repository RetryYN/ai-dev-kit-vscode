# L7 scrum-to-discovery migration enum test design

## Scope

- 対象設計: [docs/v2/L7-design/L7-scrum-to-discovery-migration-enum-design.md](../L7-design/L7-scrum-to-discovery-migration-enum-design.md)
- 対象 PLAN: [docs/plans/L7/L7-scrum-to-discovery-migration-enumplan.md](../../plans/L7/L7-scrum-to-discovery-migration-enumplan.md)
- テスト実装: `cli/lib/tests/test_discovery_compat.py`
- テスト実装: `cli/lib/tests/test_discovery_migrate.py`
- テスト実装: `cli/lib/tests/test_plan_validator.py`
- テスト実装: `cli/lib/tests/test_helix_doctor_phase_mode.py`
- テスト実装: `cli/lib/tests/test_command_mapper.py`
- テスト実装: `cli/tests/helix-discovery.bats`

## Cases

- MT-001: `HELIX_DISCOVERY_COMPAT_STAGE` の default は 1。
- MT-002: config の `discovery.compat_stage` を読める。
- MT-003: env が config より優先される。
- MT-004: 不正 stage 値は fail-close する。
- MT-005: `S0-S3` が `D0-D4` 表示へ変換される。
- MT-006: `D4` は DB write 用 phase として拒否される。
- MT-007: manifest 生成が相対 path / hash / size を記録する。
- MT-008: `helix discovery migrate --dry-run` が copy plan を返す。
- MT-009: 正常 migrate が dst / manifest / README.deprecated を生成する。
- MT-010: manifest hash 一致時は idempotent skip する。
- MT-011: conflict + merge strategy 未指定は手動介入要求で abort する。
- MT-012: symlink を含む src は fail-close する。
- MT-013: `drive: discovery` は validator で warning なし。
- MT-014: `drive: scrum` は validator で deprecated warning を返す。
- MT-015: doctor は `mode=discovery` + `D-phase` を pass 扱いする。
- MT-016: command mapper は `D0-D4` alias を公開する。
- MT-017: `helix scrum` alias は Stage 1 で warning なし、Stage 2 で warning あり。
- MT-018: `helix discovery migrate --dry-run` が `.helix/scrum` → `.helix/discovery` を表示する。

## Verification Mapping

- `cli/lib/tests/test_discovery_compat.py`
  - MT-001, MT-002, MT-003, MT-004, MT-005, MT-006
- `cli/lib/tests/test_discovery_migrate.py`
  - MT-007, MT-009, MT-010, MT-011, MT-012
- `cli/lib/tests/test_plan_validator.py`
  - MT-013, MT-014
- `cli/lib/tests/test_helix_doctor_phase_mode.py`
  - MT-015
- `cli/lib/tests/test_command_mapper.py`
  - MT-016
- `cli/tests/helix-discovery.bats`
  - MT-017, MT-018

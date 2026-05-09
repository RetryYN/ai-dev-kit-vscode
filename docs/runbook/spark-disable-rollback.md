# Runbook: HELIX_DISABLE_SPARK Rollback

## Scope

Temporary operational switch for `cli/helix-codex` on `pg` and `docs` roles while `gpt-5.3-codex-spark` usage-limit pressure remains active.

## Effective Window

- Enable with `HELIX_DISABLE_SPARK=1`.
- Re-evaluate on or after `2026-05-13`.
- This runbook only covers runtime switching. It does not change `cli/config/models.yaml`.

## Preflight

1. Confirm current pressure is resolved by checking the most recent `helix-codex` audit logs and operator reports.
2. Run `bash -n cli/helix-codex`.
3. Run `bats cli/tests/test_helix_codex_footer.bats cli/tests/test-helix-codex-auto-fallback.bats`.

## Rollback Steps

1. Remove `HELIX_DISABLE_SPARK=1` from the invoking shell, CI job, wrapper script, or local `.envrc`.
2. Dry-run the affected roles:
   - `./cli/helix-codex --role pg --task "rollback smoke" --dry-run`
   - `./cli/helix-codex --role docs --task "rollback smoke" --dry-run`
3. Confirm both dry-runs resolve `Model:     gpt-5.3-codex-spark`.
4. Run one usage-limit smoke path with `HELIX_CODEX_AUTO_FALLBACK=1` and confirm the primary attempt is spark again.

## Verification

- `HELIX_DISABLE_SPARK` unset: `pg` and `docs` return to `gpt-5.3-codex-spark`.
- `HELIX_MODEL_OVERRIDE` and `--fallback-model` still win over default resolution.
- Summary stdout filtering remains unchanged after rollback.

## Notes

- If usage-limit failures return before or after `2026-05-13`, re-enable `HELIX_DISABLE_SPARK=1` and reopen a dedicated PLAN instead of editing `models.yaml` ad hoc.

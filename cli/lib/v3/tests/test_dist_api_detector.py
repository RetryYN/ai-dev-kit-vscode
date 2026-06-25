from __future__ import annotations

from cli.lib.v3.detectors.core import (
    DistApiInput,
    ManifestRow,
    analyze_dist_api,
    load_dist_api_input,
)


def test_fn_det_14_valid_manifest_ok():
    inp = DistApiInput(
        manifest_present=True,
        rows=(ManifestRow("common", "@~/.helix/core/helix/HELIX_CORE.md", "common\t@~/.helix/core/helix/HELIX_CORE.md"),),
    )
    assert analyze_dist_api(inp).ok is True


def test_fn_det_14_invalid_scope_and_path_flagged():
    inp = DistApiInput(
        manifest_present=True,
        rows=(
            ManifestRow("bogus", "@~/.helix/core/x", "bogus\t@~/.helix/core/x"),
            ManifestRow("common", "relative/bad/path", "common\trelative/bad/path"),
        ),
    )
    res = analyze_dist_api(inp)
    assert res.ok is False
    assert len(res.invalid_rows) == 2


def test_fn_det_14_missing_manifest_is_absence():
    res = analyze_dist_api(DistApiInput(manifest_present=False, rows=()))
    assert res.ok is False
    assert res.missing_manifest is True


def test_fn_det_14_real_repo_manifest_is_valid():
    # 実 repo の helix/core-manifest.tsv は 5 行・全 valid → ok
    import sqlite3

    res = analyze_dist_api(load_dist_api_input(sqlite3.connect(":memory:")))
    assert res.ok is True

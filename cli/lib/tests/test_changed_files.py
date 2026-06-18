from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import changed_files as changed_files_module


def test_changed_files_prefers_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: WI-B changed-files helper は HELIX_CHANGED_FILES を最優先する。"""

    def _unexpected_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("git should not run when HELIX_CHANGED_FILES is set")

    monkeypatch.setenv("HELIX_CHANGED_FILES", "a.py\nb.sh  c.py")
    monkeypatch.setattr(changed_files_module.subprocess, "run", _unexpected_run)

    payload = changed_files_module.changed_files()

    assert payload == {
        "files": ["a.py", "b.sh", "c.py"],
        "source_status": "available_nonempty",
    }


def test_changed_files_uses_git_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: WI-B changed-files helper は env 未設定時に git diff fallback を使う。"""

    def _fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        assert command[:4] == ["git", "diff", "--name-only", "origin/main..HEAD"]
        return subprocess.CompletedProcess(command, 0, stdout="cli/a.py\ncli/b.sh\n", stderr="")

    monkeypatch.delenv("HELIX_CHANGED_FILES", raising=False)
    monkeypatch.setattr(changed_files_module, "_default_upstream", lambda: "origin/main")
    monkeypatch.setattr(changed_files_module.subprocess, "run", _fake_run)

    payload = changed_files_module.changed_files()

    assert payload == {
        "files": ["cli/a.py", "cli/b.sh"],
        "source_status": "available_nonempty",
    }


def test_changed_files_distinguishes_empty_from_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: WI-B changed-files helper は empty と unavailable を分離する。"""

    monkeypatch.delenv("HELIX_CHANGED_FILES", raising=False)
    monkeypatch.setattr(changed_files_module, "_default_upstream", lambda: "origin/main")

    def _empty_run(command, **kwargs):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(changed_files_module.subprocess, "run", _empty_run)
    assert changed_files_module.changed_files() == {
        "files": [],
        "source_status": "available_empty",
    }

    def _failing_run(command, **kwargs):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(command, 128, stdout="", stderr="fatal")

    monkeypatch.setattr(changed_files_module.subprocess, "run", _failing_run)
    assert changed_files_module.changed_files() == {
        "files": [],
        "source_status": "unavailable",
    }


def test_changed_files_returns_unavailable_on_resolution_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: WI-B changed-files helper は upstream 解決例外でも unavailable を返す。"""

    monkeypatch.delenv("HELIX_CHANGED_FILES", raising=False)
    monkeypatch.setattr(
        changed_files_module,
        "_default_upstream",
        lambda: (_ for _ in ()).throw(RuntimeError("branch resolution failed")),
    )

    payload = changed_files_module.changed_files()

    assert payload == {
        "files": [],
        "source_status": "unavailable",
    }


def test_changed_files_returns_unavailable_on_subprocess_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: WI-B changed-files helper は git 実行例外でも unavailable を返す。"""

    def _raising_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise subprocess.TimeoutExpired(cmd="git diff", timeout=1)

    monkeypatch.delenv("HELIX_CHANGED_FILES", raising=False)
    monkeypatch.setattr(changed_files_module, "_default_upstream", lambda: "origin/main")
    monkeypatch.setattr(changed_files_module.subprocess, "run", _raising_run)

    payload = changed_files_module.changed_files()

    assert payload == {
        "files": [],
        "source_status": "unavailable",
    }


def test_select_test_targets_maps_cli_lib_module_to_matching_pytests(tmp_path: Path) -> None:
    """DoD 検証: WI-B selector は cli/lib/<mod>.py を対応 pytest glob へ写像する。"""

    tests_dir = tmp_path / "cli" / "lib" / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_push_gate.py").write_text("", encoding="utf-8")
    (tests_dir / "test_push_gate_contract.py").write_text("", encoding="utf-8")

    selector = changed_files_module.select_test_targets(
        ["cli/lib/push_gate.py"],
        repo_root=tmp_path,
    )

    assert selector == {
        "pytest_targets": [
            "cli/lib/tests/test_push_gate.py",
            "cli/lib/tests/test_push_gate_contract.py",
        ],
        "bats_targets": [],
        "has_code_changes": True,
        "unmapped_code_files": [],
    }


def test_select_test_targets_maps_direct_test_files(tmp_path: Path) -> None:
    """DoD 検証: WI-B selector は pytest/bats の直接変更を自分自身へ写像する。"""

    selector = changed_files_module.select_test_targets(
        [
            "cli/lib/tests/test_push_gate.py",
            "cli/tests/helix-push.bats",
        ],
        repo_root=tmp_path,
    )

    assert selector == {
        "pytest_targets": ["cli/lib/tests/test_push_gate.py"],
        "bats_targets": ["cli/tests/helix-push.bats"],
        "has_code_changes": True,
        "unmapped_code_files": [],
    }


def test_select_test_targets_maps_cli_script_to_matching_bats(tmp_path: Path) -> None:
    """DoD 検証: WI-B selector は cli script を対応 bats へ best-effort で写像する。"""

    tests_dir = tmp_path / "cli" / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "helix-push.bats").write_text("", encoding="utf-8")
    (tests_dir / "test-helix-push-smoke.bats").write_text("", encoding="utf-8")

    selector = changed_files_module.select_test_targets(
        ["cli/helix-push"],
        repo_root=tmp_path,
    )

    assert selector == {
        "pytest_targets": [],
        "bats_targets": [
            "cli/tests/helix-push.bats",
            "cli/tests/test-helix-push-smoke.bats",
        ],
        "has_code_changes": True,
        "unmapped_code_files": [],
    }


def test_select_test_targets_flags_unmapped_code_for_full_fallback(tmp_path: Path) -> None:
    """DoD 検証: WI-B selector はマップ不能 code 変更を skip せず full fallback 用に返す。"""

    selector = changed_files_module.select_test_targets(
        ["cli/lib/unknown_module.py"],
        repo_root=tmp_path,
    )

    assert selector == {
        "pytest_targets": [],
        "bats_targets": [],
        "has_code_changes": True,
        "unmapped_code_files": ["cli/lib/unknown_module.py"],
    }


def test_select_test_targets_keeps_non_code_docs_light(tmp_path: Path) -> None:
    """DoD 検証: WI-B selector は docs/plans/audit のみ変更時を non-code 扱いにする。"""

    selector = changed_files_module.select_test_targets(
        [
            "docs/plans/add-feature/add-feature-2026-06-18-push-gate-test-tiering.md",
            "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml",
        ],
        repo_root=tmp_path,
    )

    assert selector == {
        "pytest_targets": [],
        "bats_targets": [],
        "has_code_changes": False,
        "unmapped_code_files": [],
    }

import os
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "cli" / "helix-debt"


def _run(args: list[str], tmp_path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HELIX_HOME"] = str(REPO_ROOT)
    env["HELIX_PROJECT_ROOT"] = str(tmp_path)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _register_path(tmp_path: Path) -> Path:
    return tmp_path / ".helix" / "debt-register.yaml"


def _parse_items(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("  - id:"):
            if current is not None:
                items.append(current)
            current = {"id": line.split(":", 1)[1].strip().strip('"')}
            continue
        if current is None or not line.startswith("    ") or ":" not in line:
            continue
        key, value = line.strip().split(":", 1)
        current[key] = value.strip().strip('"')
    if current is not None:
        items.append(current)
    return items


def test_add_basic(tmp_path: Path) -> None:
    result = _run(["add", "--title", "basic task"], tmp_path)
    assert result.returncode == 0

    items = _parse_items(_register_path(tmp_path).read_text(encoding="utf-8"))
    assert len(items) == 1
    assert re.fullmatch(r"\d+", items[0]["id"])
    assert items[0]["title"] == "basic task"
    assert items[0]["priority"] == "medium"


def test_add_with_new_options(tmp_path: Path) -> None:
    result = _run(
        [
            "add",
            "--title",
            "options task",
            "--priority",
            "high",
            "--category",
            "mock-driven",
            "--impact",
            "high",
            "--effort",
            "M",
            "--owner",
            "TL",
            "--target-sprint",
            "L6",
            "--source",
            "spec.md",
        ],
        tmp_path,
    )
    assert result.returncode == 0

    items = _parse_items(_register_path(tmp_path).read_text(encoding="utf-8"))
    assert len(items) == 1
    assert items[0]["category"] == "mock-driven"
    assert items[0]["impact"] == "high"
    assert items[0]["effort"] == "M"
    assert items[0]["owner"] == "TL"
    assert items[0]["target_sprint"] == "L6"
    assert items[0]["source"] == "spec.md"


def test_add_with_string_id(tmp_path: Path) -> None:
    result = _run(["add", "--title", "string id task", "--id", "MOCK-TEST"], tmp_path)
    assert result.returncode == 0

    items = _parse_items(_register_path(tmp_path).read_text(encoding="utf-8"))
    assert len(items) == 1
    assert items[0]["id"] == "MOCK-TEST"


def test_add_duplicate_id_skip(tmp_path: Path) -> None:
    first = _run(["add", "--title", "dup target", "--id", "MOCK-TEST"], tmp_path)
    second = _run(["add", "--title", "dup target 2", "--id", "MOCK-TEST"], tmp_path)

    assert first.returncode == 0
    assert second.returncode == 0
    assert "[skip] id=MOCK-TEST は登録済み" in second.stderr

    items = _parse_items(_register_path(tmp_path).read_text(encoding="utf-8"))
    assert len(items) == 1
    assert items[0]["title"] == "dup target"


def test_resolve_string_id(tmp_path: Path) -> None:
    create = _run(["add", "--title", "resolve target", "--id", "MOCK-TEST"], tmp_path)
    assert create.returncode == 0

    resolve = _run(["resolve", "--id", "MOCK-TEST"], tmp_path)
    assert resolve.returncode == 0

    items = _parse_items(_register_path(tmp_path).read_text(encoding="utf-8"))
    assert len(items) == 1
    assert items[0]["status"] == "resolved"
    assert items[0]["resolved_at"] != ""


def test_list_backwards_compat(tmp_path: Path) -> None:
    register = _register_path(tmp_path)
    register.parent.mkdir(parents=True, exist_ok=True)
    register.write_text(
        "\n".join(
            [
                "items:",
                "  - id: 1",
                '    title: "legacy item"',
                "    priority: low",
                '    source: ""',
                "    status: open",
                '    created_at: "2026-01-01T00:00:00"',
                '    resolved_at: ""',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = _run(["list"], tmp_path)
    assert result.returncode == 0
    assert "#1 low" in result.stdout
    assert "legacy item" in result.stdout

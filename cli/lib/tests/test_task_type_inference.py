import py_compile
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import task_type_inference


MODULE_PATH = LIB_DIR / "task_type_inference.py"


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_detect_task_type_from_implementation_verb() -> None:
    assert task_type_inference.detect_task_type("README を作成してください") == "実装"


def test_detect_task_type_from_review_verb() -> None:
    assert task_type_inference.detect_task_type("この変更をレビューしてください") == "レビュー"


def test_detect_task_type_from_design_verb() -> None:
    assert task_type_inference.detect_task_type("API 設計を検討してください") == "設計"


def test_detect_task_type_from_investigation_verb() -> None:
    assert task_type_inference.detect_task_type("認証周りを調査してください") == "調査"


def test_detect_task_type_returns_unknown_when_no_keyword_matches() -> None:
    assert task_type_inference.detect_task_type("今日はよろしくお願いします") == "不明"


def test_detect_task_type_respects_explicit_marker() -> None:
    task = "[タスク種別] **実装**\nこの変更をレビューしてください"
    assert task_type_inference.detect_task_type(task) == "実装"
    assert task_type_inference.ensure_task_type_prefix(task) == task


def test_should_include_review_template_only_for_review() -> None:
    assert task_type_inference.should_include_review_template("レビュー") is True
    for task_type in ("実装", "設計", "調査", "不明"):
        assert task_type_inference.should_include_review_template(task_type) is False

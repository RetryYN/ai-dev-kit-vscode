from pathlib import Path
import sys


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import transcript_summary


def test_summarize_basic(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.txt"
    transcript.write_text("user: continue PLAN-099\nassistant: next action is heartbeat poc\n", encoding="utf-8")

    result = transcript_summary.summarize_transcript(transcript)

    assert "continue PLAN-099" in result
    assert "heartbeat poc" in result


def test_filter_api_key() -> None:
    text = "api_key=sk-1234567890ABCDE token=secret-token"

    result = transcript_summary.filter_secrets(text)

    assert "[REDACTED:api_key]" in result
    assert "[REDACTED:token]" in result
    assert "sk-1234567890ABCDE" not in result
    assert "secret-token" not in result


def test_filter_email() -> None:
    text = "contact qa@example.com for details"

    result = transcript_summary.filter_secrets(text)

    assert result == "contact [REDACTED:email] for details"


def test_max_chars(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.txt"
    transcript.write_text("alpha beta gamma delta epsilon", encoding="utf-8")

    result = transcript_summary.summarize_transcript(transcript, max_chars=12)

    assert len(result) == 12
    assert result.endswith("…")

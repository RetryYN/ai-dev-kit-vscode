from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    subject: str
    missing: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "severity": self.severity,
            "subject": self.subject,
            "missing": list(self.missing),
        }


Loader = Callable[[sqlite3.Connection], object]
Analyzer = Callable[[object], Any]
Messenger = Callable[[Any], list[Finding]]


@dataclass(frozen=True)
class DetectorSpec:
    detector_id: str
    source_kind: str
    severity: str
    load: Loader
    analyze: Analyzer
    messages: Messenger


@dataclass(frozen=True)
class DoctorResult:
    ok: bool
    findings: tuple[Finding, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "findings": [finding.as_dict() for finding in self.findings],
        }


def _default_detectors() -> tuple[DetectorSpec, ...]:
    from .core import CORE_DETECTORS

    return CORE_DETECTORS


def _coerce_detectors(detectors: Iterable[DetectorSpec] | None) -> tuple[DetectorSpec, ...]:
    if detectors is None:
        return _default_detectors()
    return tuple(detectors)


def run_doctor(
    db: sqlite3.Connection,
    detectors: Iterable[DetectorSpec] | None = None,
    baselines: dict[str, frozenset[str]] | None = None,
) -> DoctorResult:
    """全 detector を ok=AND で実行。baselines(C5)が与えられた detector は、baseline に含まれる
    finding を grandfather し、**baseline 外の新規 finding のみ**で ok を落とす(既知 debt は緑のまま、
    regression のみ赤)。baselines 無しは従来通り(absence=ok=false)。"""
    baselines = baselines or {}
    findings: list[Finding] = []
    overall_ok = True

    for detector in _coerce_detectors(detectors):
        try:
            loaded = detector.load(db)
            result = detector.analyze(loaded)
            messages = detector.messages(result)
            findings.extend(messages)
            if detector.severity != "hard":
                continue
            baseline = baselines.get(detector.detector_id)
            if baseline is not None:
                # C5 ratchet: baseline 外 subject の新規 finding のみ fail
                if any(message.subject not in baseline for message in messages):
                    overall_ok = False
            elif not bool(getattr(result, "ok", False)):
                overall_ok = False
        except Exception as exc:
            overall_ok = False
            findings.append(
                Finding(
                    id=detector.detector_id,
                    severity=detector.severity,
                    subject=detector.detector_id,
                    missing=(str(exc),),
                )
            )

    return DoctorResult(ok=overall_ok, findings=tuple(findings))

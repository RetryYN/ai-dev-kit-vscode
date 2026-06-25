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
) -> DoctorResult:
    findings: list[Finding] = []
    overall_ok = True

    for detector in _coerce_detectors(detectors):
        try:
            loaded = detector.load(db)
            result = detector.analyze(loaded)
            findings.extend(detector.messages(result))
            if detector.severity == "hard" and not bool(getattr(result, "ok", False)):
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

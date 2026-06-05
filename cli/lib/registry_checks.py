from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from yaml_parser import parse_yaml


ALLOWED_MODES = {"advisory", "ratchet", "fail_close"}
ALLOWED_SEVERITIES = {"P0", "P1", "P2", "P3"}
PROMOTION_STATES = ("advisory", "ratchet", "fail_close")
PROMOTION_EVIDENCE_KEYS = (
    "baseline_clean",
    "full_audit_p0p1_zero",
    "changed_files_ratchet",
    "fp_zero_period",
    "perf_within_nfr",
)


class RegistryLoadError(Exception):
    pass


class ValidationError(Exception):
    pass


def _is_entry_mapping(value: Any) -> bool:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _require_text(raw: Any, field_name: str) -> str:
    value = str(raw or "").strip()
    if not value:
        raise ValidationError(f"missing required field: {field_name}")
    return value


def _normalize_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    value = str(raw).strip()
    return [value] if value else []


def _load_yaml_payload(text: str) -> Any:
    stripped = text.lstrip()
    if stripped.startswith("- "):
        indented = "\n".join(f"  {line}" if line else line for line in text.splitlines())
        wrapped = f"entries:\n{indented}\n"
        payload = parse_yaml(wrapped)
        return payload.get("entries", [])
    return parse_yaml(text)


def _extract_markdown_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("markdown frontmatter is required")

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index])

    raise ValueError("markdown frontmatter terminator is required")


def _coerce_entry_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif _is_entry_mapping(payload):
        if isinstance(payload.get("entries"), list):
            rows = payload["entries"]
        else:
            rows = [payload]
    else:
        raise ValueError("registry payload must be a mapping or list")

    if not rows:
        return []
    if not all(_is_entry_mapping(row) for row in rows):
        raise ValueError("registry entries must be mappings")
    return rows


def _json_safe(value: Any) -> Any:
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    return value


@dataclass(slots=True)
class RegistryEntry:
    id: str
    name: str
    domain: str
    status: str
    source_docs: list[str] = field(default_factory=list)
    traces: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def validate(cls, raw: dict[str, Any]) -> RegistryEntry:
        if not _is_entry_mapping(raw):
            raise ValidationError("registry entry must be a mapping")

        metadata = raw.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValidationError("metadata must be a mapping")

        return cls(
            id=_require_text(raw.get("id"), "id"),
            name=_require_text(raw.get("name"), "name"),
            domain=_require_text(raw.get("domain"), "domain"),
            status=_require_text(raw.get("status"), "status"),
            source_docs=_normalize_list(raw.get("source_docs")),
            traces=_normalize_list(raw.get("traces")),
            paths=_normalize_list(raw.get("paths")),
            patterns=_normalize_list(raw.get("patterns")),
            metadata=dict(metadata),
        )


class RegistryLoader:
    @classmethod
    def load(cls, source: str | Path) -> list[RegistryEntry]:
        path = Path(source).expanduser().resolve()
        suffix = path.suffix.lower()
        if suffix not in {".yaml", ".yml", ".md", ".markdown"}:
            raise RegistryLoadError(f"unsupported registry format: {path.suffix or '<none>'}")

        try:
            text = path.read_text(encoding="utf-8")
            if suffix in {".yaml", ".yml"}:
                payload = _load_yaml_payload(text)
            else:
                payload = _load_yaml_payload(_extract_markdown_frontmatter(text))
            return [RegistryEntry.validate(row) for row in _coerce_entry_rows(payload)]
        except (OSError, ValueError, ValidationError) as exc:
            raise RegistryLoadError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class Finding:
    severity: str
    kind: str
    entry_id: str
    path: str
    message: str
    remediation: str

    def __post_init__(self) -> None:
        if self.severity not in ALLOWED_SEVERITIES:
            raise ValueError(f"unsupported severity: {self.severity}")
        if not self.kind.strip():
            raise ValueError("kind must not be empty")

    def as_fingerprint(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.severity,
            self.kind,
            self.entry_id,
            self.path,
            self.message,
            self.remediation,
        )


class GatePolicy:
    @staticmethod
    def _baseline_fingerprints(baseline: Any) -> set[tuple[Any, ...]]:
        if baseline is None:
            return set()

        fingerprints: set[tuple[Any, ...]] = set()
        for item in baseline:
            if isinstance(item, Finding):
                fingerprints.add(item.as_fingerprint())
            elif isinstance(item, dict):
                fingerprint = (
                    item.get("severity"),
                    item.get("kind"),
                    item.get("entry_id"),
                    item.get("path"),
                    item.get("message"),
                    item.get("remediation"),
                )
                fingerprints.add(fingerprint)
            elif isinstance(item, (list, tuple)):
                fingerprints.add(tuple(item))
            else:
                fingerprints.add((item,))
        return fingerprints

    @classmethod
    def decide(cls, mode: str, findings: list[Finding], baseline: Any) -> int:
        if mode not in ALLOWED_MODES:
            raise ValueError(f"unsupported mode: {mode}")
        if mode == "advisory":
            return 0
        if mode == "fail_close":
            return int(any(finding.severity in {"P0", "P1"} for finding in findings))

        baseline_fingerprints = cls._baseline_fingerprints(baseline)
        has_new_finding = any(finding.as_fingerprint() not in baseline_fingerprints for finding in findings)
        return int(has_new_finding)

    @classmethod
    def promote(cls, state: str, evidence: dict[str, Any]) -> str:
        if state not in PROMOTION_STATES:
            raise ValueError(f"unsupported state: {state}")
        if state == "fail_close":
            return state

        next_state = PROMOTION_STATES[PROMOTION_STATES.index(state) + 1]
        requested_state = evidence.get("target_state") or evidence.get("target")
        if requested_state is not None:
            if requested_state not in PROMOTION_STATES:
                raise ValueError(f"unsupported target state: {requested_state}")
            if requested_state != next_state:
                raise ValueError(f"state promotion skip is not allowed: {state} -> {requested_state}")

        if not all(bool(evidence.get(key)) for key in PROMOTION_EVIDENCE_KEYS):
            return state
        return next_state


@dataclass(slots=True)
class DetectorReport:
    check_name: str
    domain: str
    mode: str
    findings: list[Finding]
    metrics: dict[str, Any]
    baseline: Any
    exit_policy: int

    @classmethod
    def build(
        cls,
        check_name: str,
        domain: str,
        mode: str,
        findings: list[Finding],
        metrics: dict[str, Any],
        baseline: Any,
    ) -> DetectorReport:
        if mode not in ALLOWED_MODES:
            raise ValueError(f"unsupported mode: {mode}")
        return cls(
            check_name=str(check_name),
            domain=str(domain),
            mode=mode,
            findings=list(findings),
            metrics=dict(metrics),
            baseline=baseline,
            exit_policy=GatePolicy.decide(mode, findings, baseline),
        )

    def _sorted_findings(self) -> list[Finding]:
        return sorted(
            self.findings,
            key=lambda finding: (
                finding.severity,
                finding.entry_id,
                finding.kind,
                finding.path,
                finding.message,
                finding.remediation,
            ),
        )

    def render(self, fmt: str) -> str:
        if fmt not in {"text", "json"}:
            raise ValueError(f"unsupported render format: {fmt}")

        findings = self._sorted_findings()
        if fmt == "json":
            payload = {
                "check_name": self.check_name,
                "domain": self.domain,
                "mode": self.mode,
                "exit_policy": self.exit_policy,
                "metrics": _json_safe(self.metrics),
                "baseline": _json_safe(self.baseline),
                "findings": [asdict(finding) for finding in findings],
            }
            return json.dumps(payload, ensure_ascii=False, sort_keys=True)

        lines = [
            f"check_name: {self.check_name}",
            f"domain: {self.domain}",
            f"mode: {self.mode}",
            f"exit_policy: {self.exit_policy}",
            f"findings: {len(findings)}",
        ]
        for finding in findings:
            lines.append(
                f"- {finding.severity} {finding.entry_id} {finding.kind} {finding.path}: "
                f"{finding.message} | remediation={finding.remediation}"
            )
        return "\n".join(lines)


__all__ = [
    "DetectorReport",
    "Finding",
    "GatePolicy",
    "RegistryEntry",
    "RegistryLoadError",
    "RegistryLoader",
    "ValidationError",
]

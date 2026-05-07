#!/usr/bin/env python3
"""Shared base class for HELIX LLM-backed classifiers."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import helix_db


logger = logging.getLogger(__name__)
_INCLUDE_PATTERN = re.compile(r"{{\s*include\s+([^{}]+?)\s*}}")


class CodexInvocationError(RuntimeError):
    """Raised when the Codex subprocess cannot produce a response."""


class CodexResponseError(RuntimeError):
    """Raised when a Codex response is not valid classifier JSON."""


class LLMClassifierBase:
    """Common TTL cache, Codex invocation, and evidence recording flow."""

    role: str = ""
    cache_ttl_sec: int = 3600
    classifier_name: str = ""
    codex_timeout_sec: int = 90

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else Path(helix_db.resolve_default_db_path())
        self.cache_dir = Path(".helix") / "cache" / self.classifier_name
        self._last_cache_key: str | None = None
        self._validate_config()

    def classify(self, query: str, context: dict | None = None) -> dict:
        """Run cache/rule/Codex classification flow and record the decision."""
        cache_key = self._cache_key(query, context)
        self._last_cache_key = cache_key
        cached = self._cache_lookup(cache_key)
        if cached is not None:
            cached = dict(cached)
            if "cached" in cached:
                cached["cached"] = True
            self._record_decision(query, cached, source="cache")
            return cached

        rule_result = self._classify_from_rules(query, context)
        if rule_result is not None:
            parsed = self._decorate_result(rule_result, llm_used=False)
            self._cache_store(cache_key, parsed)
            self._record_decision(query, parsed, source="rule")
            return parsed

        raw = self._invoke_codex(query, context)
        parsed = self._decorate_result(self._parse_response(raw), llm_used=True)
        record_source = str(parsed.pop("_record_source", "codex"))
        self._cache_store(cache_key, parsed)
        self._record_decision(query, parsed, source=record_source)
        return parsed

    def _validate_config(self) -> None:
        if not self.classifier_name:
            raise ValueError("classifier_name must be set by subclasses")
        if not self.role:
            raise ValueError("role must be set by subclasses")

    def _cache_key(self, query: str, context: dict | None) -> str:
        payload = {
            "classifier_name": self.classifier_name,
            "query": query,
            "context": context or {},
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _cache_lookup(self, key: str) -> dict | None:
        path = self.cache_dir / f"{key}.json"
        if not path.is_file():
            return None
        if time.time() - path.stat().st_mtime > self.cache_ttl_sec:
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return data if isinstance(data, dict) else None

    def _cache_store(self, key: str, value: dict) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / f"{key}.json"
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(path)

    def _invoke_codex(self, query: str, context: dict | None) -> str:
        prompt = self._build_prompt(query, context)
        cmd = ["codex", "exec", "-m", self.role, prompt]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.codex_timeout_sec,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise CodexInvocationError(f"codex exec timed out after {self.codex_timeout_sec}s") from exc
        except OSError as exc:
            raise CodexInvocationError(f"codex exec failed to start: {exc}") from exc

        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            detail = f": {stderr}" if stderr else ""
            raise CodexInvocationError(f"codex exec failed with exit={proc.returncode}{detail}")
        return proc.stdout or ""

    def _build_prompt(self, query: str, context: dict | None) -> str:
        payload = {
            "classifier": self.classifier_name,
            "query": query,
            "context": context or {},
        }
        return (
            "Classify the following HELIX input. Return JSON only.\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )

    def _render_prompt(self, template_path: Path, vars: dict[str, str]) -> str:
        """Render a prompt file with one-level relative include expansion."""
        template_path = Path(template_path).resolve()
        template = template_path.read_text(encoding="utf-8")

        def replace_include(match: re.Match[str]) -> str:
            include_path = (template_path.parent / match.group(1).strip()).resolve()
            if include_path == template_path:
                raise ValueError(f"prompt include cycle is not allowed: {include_path}")
            if not include_path.is_file():
                raise FileNotFoundError(include_path)
            return include_path.read_text(encoding="utf-8")

        rendered = _INCLUDE_PATTERN.sub(replace_include, template)
        for key, value in vars.items():
            rendered = rendered.replace("{{" + key + "}}", "" if value is None else str(value))
        return rendered

    def _classify_from_rules(self, query: str, context: dict | None) -> dict | None:
        return None

    def _decorate_result(self, parsed: dict, *, llm_used: bool) -> dict:
        return parsed

    def _parse_response(self, raw: str) -> dict:
        text = raw.strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = self._parse_embedded_json(text)
        if not isinstance(parsed, dict):
            raise CodexResponseError("Codex response must be a JSON object")
        return parsed

    def _parse_embedded_json(self, text: str) -> Any:
        first = text.find("{")
        last = text.rfind("}")
        if first == -1 or last == -1 or first >= last:
            raise CodexResponseError("Codex response did not contain a JSON object")
        try:
            return json.loads(text[first : last + 1])
        except json.JSONDecodeError as exc:
            raise CodexResponseError(f"Codex response JSON parse failed: {exc}") from exc

    def _record_decision(self, query: str, result: dict, source: str) -> None:
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        entry_id = f"{self.classifier_name}.{query_hash[:12]}"
        cache_key = self._last_cache_key or self._cache_key(query, None)
        metadata = {
            "query": query,
            "result": result,
            "source": source,
        }
        conn = None
        try:
            conn = helix_db.get_connection(self.db_path)
            ensure_schema = getattr(helix_db, "_ensure_schema", None)
            if callable(ensure_schema):
                ensure_schema(conn)
            conn.execute(
                """
                INSERT OR IGNORE INTO entries
                    (id, axis, stack, lifecycle, ref, agent_actor, metadata, updated_at)
                VALUES
                    (?, 'evidence', 'n/a', 'initial', ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    entry_id,
                    f"{self.classifier_name}/{cache_key}",
                    f"codex-{self.role}",
                    json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        except Exception as exc:  # pragma: no cover - warning-only safety net
            logger.warning("failed to record classifier decision: %s", exc)
        finally:
            if conn is not None:
                conn.close()

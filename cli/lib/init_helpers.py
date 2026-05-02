#!/usr/bin/env python3
"""Helpers for helix-init post-processing."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import yaml_parser


PHASE_PREREQ_GATES = {
    "L1": [],
    "L2": ["G0.5", "G1"],
    "L3": ["G0.5", "G1", "G2"],
    "L4": ["G0.5", "G1", "G2", "G3"],
    "L5": ["G0.5", "G1", "G2", "G3", "G4"],
    "L6": ["G0.5", "G1", "G2", "G3", "G4", "G5"],
    "L7": ["G0.5", "G1", "G2", "G3", "G4", "G5", "G6"],
    "L8": ["G0.5", "G1", "G2", "G3", "G4", "G5", "G6", "G7"],
    "L9": ["G0.5", "G1", "G2", "G3", "G4", "G5", "G6", "G7"],
    "L10": ["G0.5", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G9"],
    "L11": ["G0.5", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G9", "G10"],
}


def apply_start_phase(phase_yaml_path: Path, start_phase: str) -> None:
    """Mark prerequisite gates as skipped and update current_phase."""
    if start_phase not in PHASE_PREREQ_GATES:
        raise ValueError(f"unknown start phase: {start_phase}")
    if start_phase == "L1":
        return

    lock_fh = yaml_parser._lock_open(str(phase_yaml_path) + ".lock")
    try:
        text = phase_yaml_path.read_text(encoding="utf-8")
        data = yaml_parser.parse_yaml(text)
        yaml_parser.set_nested(data, "current_phase", start_phase)
        for gate in PHASE_PREREQ_GATES[start_phase]:
            yaml_parser.set_nested(data, f"gates.{gate}.status", "skipped")
        output = yaml_parser._build_output_with_header(text, data)
        tmp_path = phase_yaml_path.with_name(f"{phase_yaml_path.name}.tmp.{os.getpid()}")
        tmp_path.write_text(output, encoding="utf-8")
        os.replace(tmp_path, phase_yaml_path)
    finally:
        yaml_parser._lock_close(lock_fh)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="helix-init helper commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_parser = subparsers.add_parser("apply-start-phase")
    apply_parser.add_argument("--phase-file", required=True, type=Path)
    apply_parser.add_argument("--start-phase", required=True)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "apply-start-phase":
        apply_start_phase(args.phase_file, args.start_phase)
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

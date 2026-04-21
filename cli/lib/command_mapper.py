"""HELIX command mapping: layer/gate/category -> related command list."""
from __future__ import annotations

LAYER_COMMANDS = {
    "L1": ["helix-size"],
    "L2": ["helix-gate G2", "/spec"],
    "L3": ["helix-plan", "/sdd-plan"],
    "L4": ["helix-sprint", "/build", "helix-review", "helix-drift-check"],
    "L5": ["helix-gate G5"],
    "L6": ["helix-gate G6", "/test"],
    "L7": ["helix-pr", "/ship", "helix-gate G7"],
    "L8": ["helix-retro"],
    "R0": ["helix-reverse R0"],
    "R1": ["helix-reverse R1"],
    "R2": ["helix-reverse R2"],
    "R3": ["helix-reverse R3"],
    "R4": ["helix-reverse R4"],
    "S0": ["helix-scrum backlog"],
    "S1": ["helix-scrum plan"],
    "S2": ["helix-scrum poc"],
    "S3": ["helix-scrum verify"],
    "S4": ["helix-scrum decide"],
}

GATE_COMMANDS = {
    "G0.5": ["helix-gate G0.5"],
    "G1": ["helix-gate G1"],
    "G1.5": ["helix-gate G1.5"],
    "G1R": ["helix-gate G1R"],
    "G2": ["helix-gate G2", "/sdd-review"],
    "G3": ["helix-gate G3"],
    "G4": ["helix-gate G4", "/sdd-review", "/ship"],
    "G5": ["helix-gate G5"],
    "G6": ["helix-gate G6", "/ship"],
    "G7": ["helix-gate G7"],
}

CATEGORY_COMMANDS = {
    "common/security": ["security-audit"],
    "common/testing": ["qa-test"],
    "common/code-review": ["code-reviewer"],
    "project/api": ["helix-drift-check"],
    "project/db": ["helix-drift-check", "helix-migrate"],
    "project/fe-design": ["fe-design", "fe-component"],
    "workflow/deploy": ["helix-pr", "/ship"],
    "workflow/debt-register": ["helix-debt"],
    "workflow/reverse-analysis": ["helix-reverse"],
}


def derive_commands(skill_data: dict) -> list[str]:
    """Union explicit commands and derived commands with dedup (explicit first)."""
    metadata = skill_data.get("metadata", {}) or {}
    explicit = metadata.get("commands") or []
    if not isinstance(explicit, list):
        explicit = []
    explicit = [str(cmd) for cmd in explicit]

    derived: list[str] = []
    layers = metadata.get("helix_layer") or skill_data.get("helix_layer") or []
    if isinstance(layers, str):
        layers = [layers]
    for layer in layers or []:
        derived.extend(LAYER_COMMANDS.get(str(layer).strip(), []))

    gates = metadata.get("helix_gate") or []
    if isinstance(gates, str):
        gates = [gates]
    for gate in gates or []:
        derived.extend(GATE_COMMANDS.get(str(gate).strip(), []))

    skill_id = skill_data.get("id")
    if not skill_id and "category" in skill_data and "name" in skill_data:
        skill_id = f"{skill_data['category']}/{skill_data['name']}"
    derived.extend(CATEGORY_COMMANDS.get(str(skill_id or ""), []))

    seen: set[str] = set()
    result: list[str] = []
    for command in explicit + derived:
        if command not in seen:
            seen.add(command)
            result.append(command)
    return result

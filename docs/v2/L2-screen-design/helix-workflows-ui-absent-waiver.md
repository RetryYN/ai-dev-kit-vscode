---
doc_id: L2-HELIX-UI-ABSENT-WAIVER
title: "HELIX-workflows L2 UI absent waiver"
status: frozen
process_layer: L2
pairs_with: L10
applicability: not_applicable
reason: ui_absent
owner: TL
created: 2026-06-09
---

# HELIX-workflows L2 UI Absent Waiver

## Scope

HELIX-workflows itself is a CLI / workflow / skill / schema framework. It does not ship a product screen, interactive web UI, TUI, or visual mock in the current scope.

Therefore L2 screen design / frontend UI / wire mock is intentionally `not_applicable` for HELIX-workflows itself.

## Evidence

- L0 concept declares L2 / L10 skip for HELIX-workflows because the framework has no UI.
- `docs/v2/document-system-definition.md` requires an explicit N/A declaration instead of silent deletion.
- `VG-overview` must read this waiver before reporting `L2-L10: not_applicable(ui_absent)`.

## Unskip Conditions

L2 / L10 must be reopened if any of these become true:

1. HELIX publishes an official docs site or other web UI.
2. HELIX ships an interactive UI, TUI, visual mock, or dashboard.
3. A downstream project applies HELIX to a product with screens.

CLI help text, man-page style documentation, and command output formatting alone do not unskip L2 / L10.

## Pair Handling

| Pair | Status | Reason |
|---|---|---|
| L2 screen design | not_applicable | ui_absent |
| L10 frontend UX polish | not_applicable | L2 is not applicable |


#!/usr/bin/env bats

setup() {
  DOCS_FILE="${BATS_TEST_DIRNAME}/../../docs/architecture/helix-flexibility-constraint.md"
}

@test "docs: flexibility constraint document exists" {
  [ -f "${DOCS_FILE}" ]
}

@test "docs: include extensibility and constraint sections" {
  run grep -q "## 2. 拡張性軸" "${DOCS_FILE}"
  [ "$status" -eq 0 ]

  run grep -q "## 3. 制約性軸" "${DOCS_FILE}"
  [ "$status" -eq 0 ]
}

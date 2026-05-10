#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  TMP_ROOT="$(mktemp -d)"
  source "$BATS_TEST_DIRNAME/_helix-bats-helper.bash"
  helix_bats_mark "$TMP_ROOT"
  PROJECT_ROOT="$TMP_ROOT/project"
  HOME_DIR="$TMP_ROOT/home"
  mkdir -p "$PROJECT_ROOT" "$HOME_DIR"
  cd "$PROJECT_ROOT"
  git init >/dev/null 2>&1
  git config user.email "t@t"
  git config user.name "T"
  echo "# test" > README.md
  git add . && git commit -q -m "init"
  export HELIX_PROJECT_ROOT="$PROJECT_ROOT"
  export HOME="$HOME_DIR"
  "$HELIX_ROOT/cli/helix" init --project-name scrum-test >/dev/null
}

teardown() {
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}

@test "scrum backlog scaffold is fail-closed without HELIX未実装 wording" {
  "$HELIX_ROOT/cli/helix" scrum init >/dev/null

  run "$HELIX_ROOT/cli/helix" scrum backlog add \
    --id H001 \
    --title "検証サンプル" \
    --question "成立するか" \
    --acceptance "pass condition"

  [ "$status" -eq 0 ]
  script_path="$(find "$PROJECT_ROOT/verify" -type f -name 'h001-*.sh' | head -n 1)"
  [ -n "$script_path" ]
  grep -q "仮説固有の検証条件" "$script_path"
  ! grep -q "FAIL: 未実装" "$script_path"

  run bash "$script_path"
  [ "$status" -eq 1 ]
  [[ "$output" == *"hypothesis verification script has not been customized yet"* ]]
}

@test "scrum confirmed requires passing verification unless forced" {
  "$HELIX_ROOT/cli/helix" scrum init >/dev/null
  "$HELIX_ROOT/cli/helix" scrum backlog add \
    --id H001 \
    --title "Test" \
    --question "成立するか" \
    --acceptance "pass condition" >/dev/null

  run "$HELIX_ROOT/cli/helix" scrum decide --hypothesis H001 --confirmed
  [ "$status" -ne 0 ]
  [[ "$output" == *"検証成功が必要"* ]]

  cat > "$PROJECT_ROOT/verify/h001-test.sh" <<'SH'
#!/bin/bash
set -euo pipefail
echo pass
SH
  chmod +x "$PROJECT_ROOT/verify/h001-test.sh"

  run "$HELIX_ROOT/cli/helix" scrum decide --hypothesis H001 --confirmed
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASS: verify script passed"* ]]
  [[ "$output" == *".helix/tasks/scrum-H001-forward.md"* ]]
  [ -f "$PROJECT_ROOT/.helix/tasks/scrum-H001-forward.md" ]
  promotion_plan_id="$(python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" read "$PROJECT_ROOT/.helix/scrum/backlog.yaml" hypotheses.H001.promotion_plan_id)"
  [[ "$promotion_plan_id" == PLAN-* ]]
  [ -f "$PROJECT_ROOT/.helix/plans/${promotion_plan_id}.yaml" ]
}

@test "scrum review does not complete sprint when verification fails" {
  "$HELIX_ROOT/cli/helix" scrum init >/dev/null
  "$HELIX_ROOT/cli/helix" scrum backlog add \
    --id H001 \
    --title "Test" \
    --question "成立するか" \
    --acceptance "pass condition" >/dev/null
  "$HELIX_ROOT/cli/helix" scrum plan --goal "Goal" --hypotheses H001 >/dev/null

  run "$HELIX_ROOT/cli/helix" scrum review
  [ "$status" -ne 0 ]
  [[ "$output" == *"検証失敗のため sprint review を完了できません"* ]]

  sprint_status="$(python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" read "$PROJECT_ROOT/.helix/scrum/sprint.yaml" sprints.1.status)"
  [ "$sprint_status" = "active" ]
}

@test "scrum to forward mode counts dict based confirmed hypotheses" {
  "$HELIX_ROOT/cli/helix" scrum init >/dev/null
  "$HELIX_ROOT/cli/helix" scrum backlog add \
    --id H001 \
    --title "Test" \
    --question "成立するか" \
    --acceptance "pass condition" >/dev/null
  python3 "$HELIX_ROOT/cli/lib/yaml_parser.py" write "$PROJECT_ROOT/.helix/scrum/backlog.yaml" hypotheses.H001.status confirmed

  run "$HELIX_ROOT/cli/helix" mode forward
  [ "$status" -eq 0 ]
  [[ "$output" == *"scrum → forward"* ]]
  [[ "$output" != *"confirmed な仮説がありません"* ]]
}

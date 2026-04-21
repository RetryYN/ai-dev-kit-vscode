---
description: Run TDD workflow — write failing tests, implement, verify. For bugs, use the Prove-It pattern.
---

Invoke the agent-skills:test-driven-development skill.

For new features:
1. Write tests that describe the expected behavior (they should FAIL)
2. Implement the code to make them pass
3. Refactor while keeping tests green

For bug fixes (Prove-It pattern):
1. Write a test that reproduces the bug (must FAIL)
2. Confirm the test fails
3. Implement the fix
4. Confirm the test passes
5. Run the full test suite for regressions

For browser-related issues, also invoke agent-skills:browser-testing-with-devtools to verify with Chrome DevTools MCP.

## HELIX 連携
- HELIX フェーズ: L4.3 単体テスト / L6 統合検証
- HELIX CLI: `helix gate G4 --static-only` でドライラン検証 / `helix gate G6` で RC 判定
- UI テスト: browser-testing-with-devtools スキル併用
- 品質判定: quality-lv5 (HELIX 本体) でテストピラミッド比率チェック

# agent-skills references index
> 目的: agent-skills references index の要点を把握し、設計・実装判断を行う際のクイックリファレンスとして参照

`skills/agent-skills/references/` の用途と、HELIX 本体スキルとの関係を示す索引。

## 方針
- 本ディレクトリは「英語の即時参照チェックリスト/パターン集」を提供する。
- HELIX 本体（`skills/common/*`）は「日本語の詳細ガイド」を提供する。
- 重複時は本体優先。相補的な内容は注記付きで共存する。

## ファイル一覧
1. `accessibility-checklist.md`
   - 目的: WCAG 2.1 AA のクイックチェック
   - 関係: 詳細は `skills/common/visual-design/references/accessibility-design.md`
2. `performance-checklist.md`
   - 目的: Core Web Vitals と FE/BE 性能チェックの即時参照
   - 関係: 詳細は `skills/common/performance/SKILL.md`
3. `security-checklist.md`
   - 目的: OWASP 観点を含むセキュリティ実装前チェック
   - 関係: 詳細は `skills/common/security/SKILL.md`
4. `testing-patterns.md`
   - 目的: テスト実装パターン（AAA, mock, E2E）の即時参照
   - 関係: 詳細は `skills/common/testing/SKILL.md`
5. `orchestration-patterns.md`
   - 目的: ship skill 固有の persona 連携パターン整理
   - 関係: 本体に直接対応する同名リファレンスなし（独立）

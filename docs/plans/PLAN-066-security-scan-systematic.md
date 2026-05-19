---
plan_id: PLAN-066
title: "PLAN-066（security scan 体系化: G2/G4/G6 3 段階）"
status: draft
created: 2026-05-13
author: "Codex (Docs)"
priority: high
size: L
phases_affected: "docs/security/ (新規) / .helix/security/ (新規) / helix.db schema (security_findings, dep_vulnerabilities) / cli/roles/security.conf / cli/lib/scan wrappers"
parent_plan: PLAN-065
acceptance:
  g2_threat_model:
    verification_commands: { command: "test -f docs/security/G2-threat-model-PLAN-066.md && wc -l docs/security/G2-threat-model-PLAN-066.md", expected: "G2 用 threat-model 文書が作成され、実行可能な粒度で 200 行以上" }
  g4_static_scan:
    verification_commands: { command: "test -f .helix/security/G4-scan-$(git rev-parse --short HEAD).json", expected: "G4 static scan artifact が head sha ベースで出力される" }
  g6_dynamic_test:
    verification_commands: { command: "test -f .helix/security/G6-dynamic-$(git rev-parse --short HEAD).md", expected: "G6 dynamic security report が head sha ベースで出力される" }
  dependency_vulnerability:
    verification_commands: { command: "sqlite3 .helix/helix.db 'SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"dep_vulnerabilities\";'", expected: "dep_vulnerabilities テーブルが存在" }
  secret_scan:
    verification_commands: { command: "test -f .helix/security/secret-scan-config.yaml", expected: "pre-commit secret scan の許可 pattern 管理ファイルが存在" }
  regression_policy:
    verification_commands: { command: "helix plan lint docs/plans/PLAN-066-security-scan-systematic.md", expected: "frontmatter と acceptance 構造が plan lint を通過" }
finalized: null
---

# PLAN-066: security scan 体系化 - G2/G4/G6 3 段階

## §1 背景

現状の security role は単発レビュー中心で、設計・実装・RC の各ゲートに対して同じ基準で追跡されていない。
そのため、OWASP Top 10、認証認可、入力バリデーション、秘密情報、依存脆弱性の論点が、レビュー担当者の経験に依存しやすい。

本 PLAN では、security scan を 3 段階のゲート連動に分解し、さらに継続スキャンと秘密情報検出を別軸で運用する。
狙いは「単発で見る」から「ゲートと成果物に紐づけて追跡する」への移行である。

## §2 目的

- G2 で threat-model に基づく設計時 security review を標準化する
- G4 で static analysis を実装完了の判定材料にする
- G6 で dynamic security test を RC 判定に組み込む
- 依存脆弱性を weekly で継続監視する
- 秘密情報 scan を pre-commit hook に組み込む
- 各結果を helix.db と `.helix/security/` 配下に統一記録する

## §3 スコープ

### 3.1 含むもの

- security role のゲート連動化
- threat-model ベースの設計レビュー
- static analysis wrapper
- dynamic security test wrapper
- dependency vulnerability cron
- secret scan policy 管理
- DB schema 追加

### 3.2 含まないもの

- 人間が実施するペンテスト
- SIEM / SOC を含むセキュリティ監視運用
- インシデント対応自動化
- 本番環境の設定変更
- 認証基盤そのものの再設計

## §4 方針

### 4.1 3 段階ゲート

G2, G4, G6 のそれぞれに異なる security check を割り当て、同じ観点を重複実行しない。

- G2: 設計の脆弱性予測
- G4: 実装のコードレベル静的検査
- G6: 統合環境での動的検査

### 4.2 継続チェック

G2/G4/G6 に加えて、依存脆弱性と秘密情報 scan は継続運用として扱う。
これらは gate の一部ではあるが、実行タイミングと成果物の保存先を分離する。

## §5 5 軸の体系化

### 軸 A: G2 設計時 security review

L2 アーキテクチャ完了時に security role を threat-model SKILL で起動する。
入力は認証認可フロー、データ flow 図、外部境界、保存データの分類である。

想定チェック項目:

- 認証と認可の境界が明確か
- 重要操作に対する権限検証が抜けていないか
- 外部入力がどの境界を越えるか明示されているか
- 秘密情報やトークンの保存場所が定義されているか
- 監査ログの必要性が設計に反映されているか

出力:

- `docs/security/G2-threat-model-PLAN-066.md`

### 軸 B: G4 実装時 security scan

L4 実装完了時に static analysis を実行する。

対象ツール:

- `bandit` for Python
- `semgrep` for rule-based scan
- `safety` for Python dependency CVE

出力:

- `helix.db.security_findings`
- `.helix/security/G4-scan-<sha>.json`

判定方針:

- severity / confidence の閾値を持つ
- suppression は理由付きで記録する
- threshold を超えた場合は fail-close にする

### 軸 C: G6 RC 判定時 dynamic security test

統合検証時に DAST 相当の軽量テストを実行する。
目的は本番相当の脅威を網羅することではなく、典型的な攻撃面の回帰を早期に捕捉することにある。

対象 PoC:

- 認証 bypass
- SQL injection
- XSS

出力:

- `.helix/security/G6-dynamic-<sha>.md`

実行条件:

- staging 限定
- warned mode を既定にする
- 本番データ接続は禁止

### 軸 D: 依存脆弱性

weekly cron で `pip audit` / `npm audit` を実行する。

ルール:

- CVE >= 7.0 は warning
- CVE >= 9.0 は G4 fail-close
- 結果は `dep_vulnerabilities` に蓄積する

出力:

- `helix.db.dep_vulnerabilities`
- weekly report artifact

### 軸 E: 秘密情報 scan

pre-commit hook で secret scan を実行する。
gitleaks / trufflehog 相当の検出を前提にしつつ、許可済み pattern は設定ファイルで管理する。

出力:

- `.helix/security/secret-scan-config.yaml`

## §6 成果物一覧

| 軸 | 成果物 | 保存先 |
|---|---|---|
| G2 | threat-model review | `docs/security/G2-threat-model-PLAN-066.md` |
| G4 | static scan JSON | `.helix/security/G4-scan-<sha>.json` |
| G4 | findings table | `helix.db.security_findings` |
| G6 | dynamic security report | `.helix/security/G6-dynamic-<sha>.md` |
| D | dependency vulnerability table | `helix.db.dep_vulnerabilities` |
| E | secret scan config | `.helix/security/secret-scan-config.yaml` |

## §7 Sprint 構成

size = L, 8 Sprint 構成とする。

| Sprint | 内容 | 主担当 |
|---|---|---|
| W-0 | draft + TL R1 + finalize | Docs / TL |
| **W-1** | **helix.db schema v21: security_findings + dep_vulnerabilities (前提依存全 sprint の最優先)** | **DBA** |
| W-2 | 軸 A G2 threat-model integration | Security |
| W-3 | 軸 B G4 static scan wrapper (security_findings 利用) | Security / SE |
| W-4 | 軸 C G6 dynamic test wrapper (security_findings 利用) | Security / QA |
| W-5 | 軸 D 依存脆弱性 cron + table (dep_vulnerabilities 利用) | Security / DBA |
| W-6 | 軸 E 秘密情報 pre-commit hook | Security / DevOps |
| W-7 | gate 統合 + dashboard | TL / QA |
| W-final | 統合検証 + retro | TL / QA |

依存順序の根拠 (R1 P1 修正): W-3/W-4/W-5 はそれぞれ helix.db の security_findings / dep_vulnerabilities テーブルを INSERT 対象とするため、schema 作成 (W-1) を最優先する。W-1 完了後は W-2/W-3/W-4/W-5/W-6 が並列実行可能。

Sprint 間の依存:

- W-1 は W-0 完了後に開始
- W-2 は W-1 のレビュー基準が確定してから開始
- W-3 は W-2 の artifact 形式が確定してから開始
- W-6 は W-4 / W-5 のデータ定義が固まってから開始

## §8 リスク

### 8.1 静的解析 false positive 過多

問題:

- `bandit` / `semgrep` の rule が広すぎると、運用不能なノイズになる

対策:

- suppression 機構を理由付きで持つ
- severity threshold を導入する
- ルールセットを段階導入する

### 8.2 動的テストの本番影響

問題:

- DAST 相当の PoC は誤って本番に向くと危険

対策:

- staging 限定
- warned mode を標準にする
- 実行先の環境チェックを必須化する

### 8.3 依存脆弱性の誤検知と遅延

問題:

- `pip audit` / `npm audit` の結果が変動しやすい

対策:

- weekly baseline を保存する
- 重大度で運用ルールを分ける
- fail-close 条件は高 severity のみに絞る

### 8.4 secret scan の誤許可

問題:

- 許可 pattern が増えると見逃しが増える

対策:

- allowlist は最小化する
- 例外には PLAN ID と期限を付ける
- hook と CI の両方で再検査する

## §9 実装方針

### 9.1 ファイル分割の考え方

本 PLAN は大きいため、単一 PR ではなく段階的に入れる。
各 Sprint ごとに成果物と検証コマンドを固定し、レビュー時に差分を追跡しやすくする。

### 9.2 変更の優先順

1. 設計レビューの出力形式を固定する
2. static scan の artifact を確定する
3. dynamic security report の schema を確定する
4. DB schema を追加する
5. secret scan の設定を導入する
6. gate 統合と dashboard を接続する

### 9.3 運用上の原則

- security finding は gate と artifact の両方で追跡する
- fail-close は重大度に限定する
- suppression は理由と期限を必須にする
- 本番影響がある設定変更は別工程に切り出す

## §10 検証戦略

### 10.1 ユニット

- scan wrapper の入力正規化
- artifact path 解決
- severity 閾値判定
- suppression 解析
- config parsing

### 10.2 統合

- static scan 実行結果の DB 反映
- dynamic report の生成
- weekly cron の擬似実行
- pre-commit hook の実行確認

### 10.3 受入

- G2/G4/G6 の各 gate で成果物が追跡できる
- 重大指摘が gate に連動して fail-close になる
- secret scan と dependency scan が継続運用される

## §11 acceptance

本 PLAN の acceptance は PLAN-065 の W-3 template に準拠し、以下を満たす。

- `test_pyramid`: 各 scan tool に unit + integration test
- `coverage_target`: 新規 wrapper は `>=80%`
- `regression_baseline`: `security_findings` の前回比 0pt 低下禁止
- `verification_commands`: 実行コマンドを各成果物に明示

## §12 out of scope

- ペンテストを自動化して人間作業を置き換えること
- SIEM / SOC までを一つの PLAN に統合すること
- incident response の自動化
- 認証基盤の全面置換

## §13 next steps

1. G2 threat-model のテンプレートを確定する
2. static scan の artifact schema を確定する
3. dynamic test の warn / fail 条件を確定する
4. DB schema 追加の詳細設計へ進む
5. secret scan config の allowlist 方針を定義する

## 業界 standard 参照 (Web 検索 retrofit 2026-05-19)

- `brew doctor` / `brew help` / `brew deps` は環境健全性と依存関係の診断に使うコマンドとして扱い、事前診断の例外基準を明示する（Homebrew manpage / Troubleshooting: `brew doctor`, `--list-checks`） [docs.brew.sh/Manpage](https://docs.brew.sh/Manpage), [docs.brew.sh/Troubleshooting](https://docs.brew.sh/Troubleshooting)
- `npm doctor` は npm キャッシュ整合性や設定健全性検査に使う。`npm` の公式ドキュメントで `npm doctor` の確認手順が前提となる [npm Docs](https://docs.npmjs.com/cli/v10/commands/npm-doctor/)
- `flutter doctor` は Flutter 開発環境のツール連携確認、必要時は `-v` 併用で詳細化する（CLI リファレンス / セットアップガイド） [docs.flutter.dev/reference/flutter-cli](https://docs.flutter.dev/reference/flutter-cli), [docs.flutter.dev/get-started/install/windows/mobile](https://docs.flutter.dev/get-started/install/windows/mobile?tab=vscode)
- 静的解析 pre-flight では `shellcheck`（シェルスクリプト lint）、`hadolint`（Dockerfile + Bash in RUN、ShellCheck 基盤）を CI と pre-commit で運用する（公式ドキュメント） [shellcheck.net](https://www.shellcheck.net/), [hadolint.github.io/hadolint](https://hadolint.github.io/hadolint/), [pre-commit.com](https://pre-commit.com/)
- `pre-commit` は `.pre-commit-config.yaml` で hook を定義し、`pre-commit install` と `pre-commit run` を中心に導入〜運用する（既定 hook タイプ、スキップ制御、config 検証） [pre-commit.com](https://pre-commit.com/)
- Monorepo 診断は Bazel の `query --output graph`（依存関係可視化）と Nx の `affected`（影響範囲限定実行）／Turborepo の GraphQL/Turbo graph を比較し、PLAN 目的に合わせて採択する [Bazel query tutorial](https://bazel.build/tutorials/cpp-dependency), [Nx affected](https://nx.dev/ci/features/affected), [Turborepo run reference](https://turborepo.com/repo/docs/core-concepts/package-and-task-graph)

## Revision History

- 2026-05-19 W5c-5: PLAN-066 に industry standard 参照を Web 検索検証ベースで retrofit。`helix doctor` 系 / static-analysis / monorepo 診断観点を新規参照節として追加し、運用上の根拠リンクを明記。

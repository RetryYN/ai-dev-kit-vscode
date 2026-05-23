---
doc_id: ci-pr-workflow
title: "CI / GitHub 運用ワークフロー"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# CI / GitHub 運用ワークフロー

## 概要

HELIX のゲート・テストを GitHub の PR フローに接続する運用。重い検証はローカルで行い、CI はゲート証跡の検証と PR 許可ゲートに徹する。

## 既存の GitHub 構成

- workflows 7: ci（main の push/PR）、commitlint、security（zizmor）、ブランチ別4（feature / hotfix / poc / refactor）
- helix-pr: push gate の6ゲート検証を実行してから PR 作成（`--gate` / `--require-gates` / `--auto-merge`）
- pull_request_template.md / CODEOWNERS / dependabot.yml

## ブランチ × モード対応

| ブランチ | モード | pipeline |
|---|---|---|
| feature/** | Forward / Add-feature | feature.yml |
| hotfix/** | Incident | hotfix.yml |
| poc/** | Discovery | poc.yml |
| refactor/** | Refactor | refactor.yml |

Retrofit / Reverse / Research / Recovery は、性質に近いブランチ（feature / refactor 等）に相乗りするか、必要なら専用 pipeline を追加する。

## CI 戦略（役割分担）

| 層 | 実行内容 |
|---|---|
| ローカル（pre-push / helix-pr --gate） | HELIX 内部テスト212 ＋ 全ゲート（重い処理） |
| CI（GitHub Actions） | ゲート証跡（`.helix/phase.yaml`）の検証 ＋ commitlint ＋ security（zizmor）＋ 軽量 smoke |
| branch protection | CI の軽量チェックを必須化し PR 許可をゲート |

## PR 許可フロー

```
ローカルでゲート通過（helix-pr --gate）
   → ゲート証跡を生成
   → push
   → CI が証跡を検証（フルテストは再実行しない）
   → branch protection で PR 許可
```

## 設計方針

細かいテストは HELIX 内部（ローカル）でカバーし、CI はゲート証跡の検証と PR 許可ゲートに徹する。テストを CI で完全に省くのではなく「証跡検証」を残すことで、ローカルでゲートを通したことを CI が保証でき、PR 許可の根拠が保たれる。drive=fe の PR では FE detector の pass 証跡（fe-detector-spec.md）を必須化する。

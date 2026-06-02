# L0→L1 遷移規律（Planning to Requirements Transition Discipline）

> 本書は **Forward V モデル内の工程遷移規律**であり、新しい入口 workflow ではない（入口 workflow 表に入れない＝Forward の背骨を増やさない、tl-advisor 2026-06-03 Q2 判定）。L0 企画を L1 要求へ翻訳する際の owner・handoff・gate を定義する。
> 背景: 既存に L0 工程 / L1 工程 / G0.5 / `gate-planning` / `helix innovation` はあるが、「**L0 企画を PdM がどう L1 要求へ翻訳し、誰が owner で、何を gate するか**」の遷移規律が独立した正本として薄い（真の gap、ユーザー指摘 2026-06-03）。

## 1. 位置づけ
- L0（企画書）の確定 → **G0.5** → L1（要求定義）への遷移を担う。
- これは PdM（Product Manager）の登場シーンである。L0 のビジョン/企画を L1 の検証可能な要求へ翻訳する。

## 2. owner と role 分担
| role | 責務 | agent |
|---|---|---|
| **PdM（入力・翻案・統合）** | 海外技術/マーケ思想の翻案、企画→要求の翻訳案、市場/顧客/技術仮説の統合 | `pdm-tech-innovation` / `pdm-marketing-innovation` / `pdm-innovation-manager`（統合は manager） |
| **最終 owner（判定）** | 要求の採否・スコープ確定・G0.5 判定 | **PM / PO** |

- **recommended agent**: `pdm-innovation-manager`（L0→L1 遷移の統合担当）。PdM 3 agent は**入力生成・翻案・統合支援**であり判定主体ではない。最終 owner は PM/PO。
- PdM の提案は evidence として残す（BR-RULE-13 = L1/L3 要件定義時 PdM 提案 evidence 残置、既存）。

## 3. handoff items（L0 → L1）
G0.5 通過時に L0 から L1 へ引き渡す:
1. 確定した企画 concept（ビジョン・課題・価値仮説）
2. スコープ境界（何を作る/作らない、既存全洗い出し inventory = 機能要求に内包する範囲）
3. L1-IN-* 取り込み items（L0 で identified された要求候補）
4. **検証を第一級原則とするバトン** → L1 で検証戦略を起票する（[verification-strategy](../../docs/v2/L1-requirements/helix-workflows-verification-strategy.md)、tl-advisor Q1）
5. 採択/保留/見送りの判断記録（L0 §8 相当）

## 4. G0.5 exit 条件 / L1 受理条件
- **G0.5（PM/PO 判定）**: 企画 concept 確定 + スコープ境界明示 + PdM 提案 evidence 残置 + L1 handoff items 完備。
- **L1 受理条件**: handoff items を受領し、L1 要求定義（業務/機能/技術/非機能 + 運用テスト設計 pair + 検証戦略）の起票に着手できる状態。

## 5. workflow への組込（carry）
- `vmodel-semantics.yaml` の L0→L1 遷移に `pdm-innovation-manager` を **recommended agent** として登録（layer-context-injection で自動推挙）。
- これにより「工程に応じた推奨/必須 agent の発火」を workflow 自体に組み込む（[[workflow-self-evaluation]] の発火組込方針と整合）。

## 6. 正本同期
- 本書は遷移規律の正本。`HELIX-process-L0-L14.md` には L0→G0.5→L1 の遷移が存在する旨を短く参照する（重複させない）。
- 詳細工程は `L0-concept.md`（handoff 出力側）/ `L1-requirements.md`（受理側）に handoff items の対応を追記する（carry）。

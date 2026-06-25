# C5 — baseline-ratchet 契約（非後退昇格）

> keystone C5。base SSoT = [capture §2](../audit/2026-06-26-new-base-comprehensive-capture.md) / 実体 = clean harness `src/lint/oracle-test-trace-baseline.ts`（未 citation 89 件の shrink-only `ReadonlySet`）。
> V3 = Python。対応: REQ-RAT-01/02 / AT-V3-09 / NFR-V3-03。

## 1. 目的

detector を advisory→fail-close へ**非後退（縮小のみ可）で段階昇格**する。既存 debt を一度に潰せない現実（count-pin ripple / debt 移行）への安全弁。「全部 green になるまで昇格不可」という暗黙の障壁を、baseline 外の新規違反だけを fail-close にすることで解く。clean harness 実証: `oracle-test-trace-baseline` = 既知 debt 89 件を `ReadonlySet`、コメントに「**縮小のみ可** — 新規追加で穴を広げない」明記。

## 2. 契約（DbC）

```python
BASELINE[detector_id]: frozenset[str]   # 既知 debt の違反 id 集合（縮小のみ）
def ratchet(current_violations: set[str], baseline: frozenset[str]) -> dict:
    new = current_violations - baseline       # baseline 外 = 新規違反 → fail-close 対象
    return {"new": new, "regressed": bool(new)}   # 既知 debt（baseline 内）は advisory surface に留める
```

- **invariant-non-regression**: baseline の更新は **縮小方向のみ許可**（id を増やす変更＝ debt 追加を reject）。
- **invariant-new-only-fail**: detector が fail-close になるのは `current - baseline ≠ ∅` のときのみ。
- **ensures**: baseline が空に近づくほど detector は完全 fail-close へ近づく（昇格の単調性）。
- **requires**: baseline 初期 snapshot は再現可能な手順で生成（`--gate なし advisory で件数確認 → 凍結ファイル生成`）。
- **機械強制**: baseline は source 管理対象の `frozenset`（縮小方向は CI で **monotone-decrease assert** テストを付ける。件数増加 commit を red）。

## 3. 検証

- AT-V3-09: baseline を増やす変更 → ratchet が reject（CI red）。減らす → 通る。
- 単体: `new = current - baseline` の集合演算 / baseline 増加 commit の検出（縮小のみ許可）。

## 4. 運用（L1↔L14 pair）

OT-V3-04: baseline が縮小のみで推移していることを運用監視（debt 増加を検出）。昇格基準（advisory→fail-close 条件）は **1 ADR に集約**し detector ごとにバラさない。ADR が凍結する（TL P2）: ① baseline ファイル配置 / ② 初期 snapshot 生成コマンドの実体 / ③ ratchet 監視対象 detector。段階導入は ① anchor closure（実行 pass 証跡）→ ② detector allowlist（green のみ fail-close 昇格）→ ③ CI enforce の順（charter の段階導入と整合）。

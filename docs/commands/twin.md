# fullstack Twin Track ガイド

## fullstack 駆動タイプ

BE/FE を並行で進め、契約整合（D-CONTRACT）で結合するモード。

```bash
helix size --files 12 --lines 450 --api --ui --type new-feature --drive fullstack
```

## BE/FE 並行フロー

Phase A（並行実装）:

```bash
helix sprint status
helix sprint next --track be
helix sprint next --track fe
```

Phase B（結合）への昇格条件:

- `be.stage=.5`
- `fe.stage=.5`
- `contract.ci=pass`

## D-CONTRACT の書き方

配置例:

```text
docs/features/<scope-id>/D-CONTRACT/contract.yaml
```

最小例:

```yaml
contract:
  version: "1"
  api:
    - path: /api/v1/auth/login
      method: POST
  ui:
    - screen: login
      calls:
        - POST /api/v1/auth/login
```

## Phase A/B の遷移

- A: BE/FE トラックを独立で前進
- B: 結合検証（API契約・状態整合・E2E）

確認:

```bash
helix sprint status
```

`Phase: B` になれば結合フェーズへ移行済み。

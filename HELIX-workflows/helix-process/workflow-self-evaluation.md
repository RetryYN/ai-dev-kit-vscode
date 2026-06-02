# ワークフロー自己評価・反芻機構（Workflow Self-Evaluation & Rumination）

> workflow が**自身の実行**を評価し、skill / subagent / agent-team / command の「発火・有効性・不足」を継続記録して改善へ還す機構。ユーザー指摘（2026-06-03）「skill 発火率/タグ管理・agent/command 評価・発火のワークフロー組込・不足評価・反芻機構」を設計方向として正本化する。
> 位置づけ: これは検証の対象を「成果物」から「**workflow の実行そのもの**」へ広げる。[[verification-strategy]] の execution 版。Forward 内の closure 規律として組み込む（新入口 workflow にしない）。

## 1. 現状認識（正直な gap）
- **部分的に存在する資産**: `vmodel-semantics.yaml` + `layer-context-injection.md`（工程別 mandatory/recommended の agent/skill/command 注入）/ `learning-engine.md`（学習）/ `observability-metrics.md`（指標）/ `fe-detector-spec` / skill frontmatter の `helix_layer` tag / `helix skill search`・`chain`（推挙）。
- **弱い/欠落しているループ**: ①skill/agent/command の**発火率と有効性の系統的計測**は未実施（doctor の skill frontmatter audit は静的、発火実績の評価ではない）②発火結果（誤検出/truncate/不発/不足）を**fire-requirements として蓄積し vmodel-semantics の注入規則へ還す**閉ループが弱い ③「これがあったらよかった」= missing capability の記録機構がない。
- 本 session ではその proto を**手動**で実演した（drive-firing log + false-positive 教訓 → fire-requirements、[[reverse-2026-06-03-l1-l3-trace-hardening]] §4）。機構化が本書の目的。

## 2. 反芻機構の構成（Action / Phase closure に組み込む）
各 Action / Phase の closure event で次を生成する（retrospective）:

| 項目 | 内容 | 例（本 session） |
|---|---|---|
| **発火ログ** | 発火した skill/subagent/agent-team/command（recommended/mandatory 区別） | tl-advisor×4, pmo-tech-docs/fork, pmo-project-explorer, Codex se×2 |
| **有効性** | 有用 / 誤検出 / truncate / 不発 / コスト | explorer truncate×2(不発)、tech-docs(有用)、tl-advisor(有用だが誤前提汚染) |
| **不足（missing）** | 「これがあったら良かった」capability | trace-symmetry detector を**最初から**持っていれば false-positive 3 連発を防げた |
| **fire-requirements** | 次回いつ X を発火させるべきか（蓄積） | 決定的 read は explorer 非発火・PM 直接 / trace 判定前に ID universe 確定 / 検出は TL 前に自己 verify |

## 3. フィードバックループ（document ↔ workflow 循環の自己評価版）
```
workflow 実行 → closure で反芻（発火ログ/有効性/不足/fire-requirements）
  → fire-requirements を vmodel-semantics（layer-context-injection）の
     推奨/必須 注入規則へ反映
  → 次サイクルで適切な agent/skill/command が自動発火
  → learning-engine に発火率/有効性を蓄積、observability-metrics で可視化
  → （反復）
```

## 4. 評価対象と指標（carry, Phase2/3 で実体化）
- **skill**: 発火率（推挙→実使用）/ helix_layer tag 整合 / 有効性（使用後の手戻り率）。
- **subagent**: 発火数 / truncate 率（本 session で pmo-explorer・pmo-tech-fork が truncate=2 件 → 信頼性指標化候補）/ コスト（token）。
- **agent-team**: workflow 内での mandatory/recommended team の発火組込（vmodel-semantics 拡張）。
- **command**: 工程別 command の使用率 / 失敗率（helix code find が read-only sandbox で fallback する既知問題等）。
- **missing capability log**: 不足を起票候補（feature / detector / hook）へ routing。

## 5. workflow への発火組込（ユーザー要望の中核）
- 各工程（L0-L14）の mandatory/recommended な subagent/agent-team/skill/command を `vmodel-semantics.yaml` に定義し、layer-context-injection が現在地に応じて**自動発火**させる（一部実装済）。
- 反芻機構の評価結果でこの注入規則を継続更新する（= 発火の精度を自己改善）。
- 例: L0→L1 遷移で `pdm-innovation-manager` recommended（[[planning-to-requirements-transition]] §5）。

## 6. 観測済 改善点（本 session 2026-06-03、要件定義 input）
反芻機構の「不足評価」の実データ。L1/L3 要件定義の FR/NFR 候補として routing する（ユーザー「あったら要件定義で役立つ」）。

### command の改善点
| command | 観測事象 | 改善（要件候補） |
|---|---|---|
| `helix code find` | read-only sandbox で内部 recommender Codex session 作成失敗 → local fallback のみ（TL/Codex 各 run で再発） | nested Codex 不要な read-only fallback 経路 |
| `helix review --uncommitted` | read-only で nested review unsupported により skip | nested session 制約の解消 or 明示 degrade |
| `helix codex` | 大出力（最大 1.5MB）が SUMMARY 末尾しか stdout に出ず rollout JSONL bypass 要 | 詳細 verdict の surfacing 改善 |
| `helix doctor` | trace 対称 detector 未統合（`check_pair_trace_symmetry` 不在） | detector を doctor サブ command 化（Phase3） |
| refactor/retrofit/recovery | dedicated CLI 不在（doc 正本のみ） | 必要なら CLI 化判断（現状は意図的、carry） |

### subagent の改善点
| subagent | 観測事象 | 改善（要件候補） |
|---|---|---|
| pmo-project-explorer / pmo-tech-fork | 多 tool_uses 後に最終報告 truncate（本 session 2 件） | incremental output / agent-memory 保存強制 / tool_uses 上限 / truncate 検出と再取得 |
| （共通） | 決定的 read（件数/grep）は explorer 不向き、PM 直接が確実 | 発火要件: 判断を伴わない計測は explorer 非発火 |

### agent-team / skill の改善点
- vmodel-semantics の工程別 mandatory/recommended 発火が **workflow に自動組込されていない**（部分実装）→ layer-context-injection の自動発火 + 反芻による注入規則更新（§5）。
- agent-team の V-model 層別 auto-fire 未整備。
- skill **発火率・有効性の計測なし**（learning-engine / observability-metrics 未 engage）。helix_layer tag audit は静的のみ。

## 7. carry / 次段
- **Phase2/3**: 反芻 retrospective の closure 組込（PLAN closure event に retrospective schema 追加）/ skill 発火率・subagent truncate 率の計測（learning-engine / observability-metrics 接続）/ missing capability log → feature routing。
- detector の truncate 検出（subagent 信頼性）も観測対象に含める。
- 本機構は将来の検証（V2 全 Phase の workflow 改善）を見越した基盤（ユーザー「今後の検証を見越すとあるといい」）。

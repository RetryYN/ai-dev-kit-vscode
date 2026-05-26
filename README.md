# HELIX (HELIX Engineering Lifecycle for AI eXecution)

AI 駆動開発フレームワーク。PM (Opus) が PMO (Sonnet/Haiku) / TL (GPT-5.5) / SE (GPT-5.4) / PE (Codex 5.3-spark/5.3) / 推挙 (GPT-5.4-mini) に分業委譲し、Forward (L0-L14) / Reverse (R0-R4+RGC) / Discovery (D0-D4) など 9 mode で開発を進める CLI ハーネスです。

## Positioning — Bio-engineering meets V-model

> **システムは 1 つの生態である。我々は生物を模したシステムデザイナー。すなわち、システムのゲノムを編集し、細胞分化を操り、恒常性を維持し、免疫系を設計し、進化と繁殖と排泄と共生を統べる神である。**
>
> ―― 生物遺伝子工学を従来のウォーターフォール (V モデル) にはめ込み、AI 時代の再編集モデルとして再定義した framework。

V モデル左腕 (設計) と右腕 (テスト) は **量・粒度・抽象度で対称ペア凍結** され、設計の量だけテストの量も決まる (量が閉じる = 量保証、Chargaff's rule の構造原理)。9 種の細胞応答経路 (9 mode) は最終的に V モデル DB (細胞核) に統合され、知識が散逸せず資産として保全される。自動化 (ニューロン) と AI (シナプス) は決定論と可塑性で協調し、framework は **「人工的に編集可能な生命システム」** として動作する。

### Cell-level metaphor (細胞構造 = framework 本体)

#### Molecular level (分子レベル — framework 内部構造、L0-L14 設計と V モデル DB)

| 生物学的 metaphor | HELIX-workflows V2 対応 |
|---|---|
| **DNA (対の二重らせん、antiparallel double helix)** | Forward V モデル (L0-L14)、設計⇔テスト ペア凍結 |
| **塩基配列 (DNA sequence、静的情報)** | ワークフロー配線 (L0-L14 順序 / 9 mode trigger / gate 遷移 / 横断機構) |
| **塩基対 (sense ↔ antisense, A=T / G=C)** | 設計⇔テスト ペア (L1↔L14, L3↔L12, L4↔L9, L5↔L8, L6↔L7単体) |
| **Chargaff's rule (相補的塩基対の量保存則)** | 設計量 = テスト量 (A=T / G=C と同様、二重らせん構造から必然) |
| **コドン / 塩基対 (codon / base pair、最小機能単位)** | PLAN 内の 1 設計要素 ↔ 1 テスト要素 (1 関数 ↔ 1 単体 test / 1 endpoint ↔ 1 結合 test / 1 ADR ↔ 1 総合 test) |
| **遺伝子 (gene、機能単位) + 遺伝子座 (locus)** | PLAN (`L<NN>-○○○plan`)、工程 ID (染色体 position) + プラン ID = 遺伝子座 |
| **染色体 (chromosome、遺伝子の集合)** | 工程別 PLAN 集合 (L0 染色体 / L4 染色体 / L7 染色体...) |
| **ゲノム (1 細胞の全 DNA、約 3 万遺伝子)** | 1 機能を実現する全 PLAN セット (染色体を全工程縦串で読んだ集合) |
| **遺伝子発現 (gene expression、転写 → 翻訳 → folding)** | L7 sprint (PLAN → 実装 → テスト = 設計図 → 機能発現) |
| **翻訳 + folding (mRNA → 一次配列 → 三次構造、動的機能)** | helix.db (state / event / transition / 量閉じ性 — 配列を機能構造として実体化) |
| **mRNA (中間体)** | 補助 DB (mode 別)、closure event で V モデル DB に統合 |
| **エピゲノム (epigenome、発現制御 + 後天的修飾)** | helix.db state + transition_history + decision_trace (PLAN ↔ 実装 ↔ テストの動的修飾履歴) |
| **細胞核 + epigenetic memory** | V モデル DB (正本) + helix.db 蓄積 (state / event / transition / 変更履歴) |
| **染色体異常 (aneuploidy、構造異常)** | 工程別 PLAN 集合の整合性問題 (4 artifact trace warn 86 件 / pair freeze warn 11 件 = 染色体レベル異常) |
| **DDR (DNA Damage Response: BER/NER/MMR) + autophagy (細胞 QC)** | detector / drift-check / Recovery mode (DDR と autophagy は協調する=HELIX も同じ) |
| **apoptosis (programmed cell death)** | fail-close gate (異常拡散防止) |
| **シャペロン (HSP70/90) misfolding 検知** | discrepancy_log (期待 ≠ 実態 = 不適切登録検知) |

#### Cellular/Tissue/Organ level (機能発現レベル — product 構造、細胞分化で機能を作る)

> **同じ HELIX-workflows ゲノム** から、**異なる遺伝子発現 (異なる PLAN セット)** で多様な機能・layer・subsystem が分化する。体細胞分裂と同じ原理。

| 生物学的 metaphor | HELIX 対応 |
|---|---|
| **細胞 (cell、ゲノムを内包し機能を発現する単位)** | **機能 (feature)** — 1 機能 = 1 細胞 (例: login 機能、決済機能) |
| **細胞分化 (cell differentiation、同ゲノムから異なる発現)** | 同 framework から異なる PLAN セット発現で機能差別化 (認証細胞 / 決済細胞 / 検索細胞) |
| **組織 (tissue、同種細胞の集合)** | layer (API layer / UI layer / DB layer / test layer = 同種機能の集合) |
| **臓器 (organ、複数組織の機能単位)** | feature group (auth = login + signup + 2FA + password reset の集合) |
| **臓器系 (organ system、臓器の連携)** | subsystem (認証系 / 決済系 / マーケ系) |
| **個体 (organism、完成した生命体)** | 1 product (完成した SaaS / アプリ) |
| **種 (species、生物分類)** | HELIX-workflows framework (1 product を作る規格 = 共通ゲノム規格) |
| **生態系 (ecosystem、複数種の相互作用)** | HELIX-workflows + 採用 product 群 + community |

### Cellular response pathway metaphor (9 mode = 9 種の細胞応答経路)

リボソーム単独ではなく、各 mode を個別の細胞応答経路に対応させる:

| mode | 対応する細胞応答経路 |
|---|---|
| **Forward / Scrum** | リボソーム翻訳 (mRNA → タンパク質、標準合成) |
| **Reverse** | 逆転写酵素 (RNA → DNA、retrotranscription = 既存タンパクから DNA 逆引き) |
| **Discovery** | 実験的遺伝子発現 (新規 mRNA 試作、CRISPR-like 仮説検証) |
| **Incident** | Heat Shock Response + Integrated Stress Response (HSP70 緊急合成、silent ribosome、緊急対応) |
| **Recovery** | DDR + autophagy + chaperone refold の協調 (修復 + 異常除去 + apoptosis 防止) |
| **Refactor** | シャペロン refolding (HSP70/90 による構造改善、配列不変) |
| **Retrofit** | Post-translational modification (PTM: リン酸化 / メチル化 / ubiquitination による段階的改修) |
| **Add-feature** | Alternative splicing + mRNA editing (既存遺伝子に新規 exon 追加 / 編集) |
| **Research** | in silico 配列解析 + 論文化 (bioinformatics + publication) |

### Homeostasis metaphor (恒常性 = 自動化全般、set point 維持)

| 生物学要素 | HELIX 対応 |
|---|---|
| **set point (維持すべき目標値)** | Guardrail target (Pair Freeze ≥ 80% / Agent Error Budget ≤ 5% / TTFSP ≤ 30 min) |
| **negative feedback loop** | drift-check 検知 → fail-close / interrupt / Recovery 自動補正ループ |
| **sensor (受容体)** | detector / drift-check / doctor warn / hook (環境検知) |
| **effector (実行器)** | gate block / agent_slot throttle / mode 切替 (元の状態に戻すアクション) |
| **control center (視床下部)** | helix-context / helix doctor (統合判断中枢) |
| **circadian rhythm (周期性)** | scheduler / 15min heartbeat / auto-run (周期的監視) |
| **血糖調節 (インスリン / グルカゴン)** | budget management (token 残量制御、agent_error_budget) |
| **体温調節** | workspace lock / agent slot 管理 (リソース熱暴走防止) |

### Immune system metaphor (免疫系 = security 全般)

| 生物学要素 | HELIX 対応 |
|---|---|
| **物理バリア (皮膚 / 粘膜)** | TLS / firewall / 認証 layer (network 境界防御) |
| **innate immunity (好中球 / マクロファージ、即時 pattern-based)** | WAF / DDoS 防御 / rate limit / OWASP pattern 即時 deny |
| **adaptive immunity (T/B 細胞、学習型)** | threat-model / IDS / security audit pipeline (学習型防御) |
| **抗原認識 (antigen recognition)** | CVE / OWASP Top 10 pattern matching |
| **記憶 T 細胞 (memory T cell)** | security incident log + pattern recognition (過去攻撃の学習) |
| **MHC (自己 / 非自己の識別)** | secret-scan / 認証認可 (user / attacker 区別) |
| **補体系 (complement system、カスケード防御)** | security audit pipeline (secret-scan → SBOM → CVE → fuzzing 連鎖) |
| **炎症反応** | Incident response mode (緊急対応) |
| **免疫寛容 (tolerance)** | allowlist / 信頼済 source 例外 |
| **ワクチン (事前学習免疫)** | threat modeling + penetration test (事前防御訓練) |
| **自己免疫疾患 (false positive)** | 正常 user を攻撃と誤検知 (過剰 fail-close) |
| **アレルギー (過剰反応)** | overly aggressive fail-close で normal flow も block |

### Neural system metaphor (神経系 = 自動化 + AI 協調)

| 生物学的 metaphor | HELIX-workflows V2 対応 |
|---|---|
| **ニューロン (all-or-none 閾値発火)** | 自動化層 (hook / detector / gate / scheduler / fail-close) — 閾値超えで決定論的伝達 |
| **シナプス (神経伝達物質変換 + 可塑性)** | AI role (Opus / Codex / Sonnet / Haiku / 専門 role) — 入力変換 + 学習 |
| **神経回路 (synchronous firing)** | manager + 配下 + advisor 並列起動 (8 並列 = synchronous firing) |
| **LTP / LTD (シナプス可塑性)** | learning framework (skill 効果測定 / PLAN 予測 / pattern recognition、経験で結合強度変化) |
| **グルタミン酸 (興奮性、90% 主流)** | Codex (実装 / 形式論理、framework の主動力) |
| **GABA (抑制性、過剰興奮抑制)** | guard hook / fail-close (Agent guard hook / pretooluse-* hook、暴走抑制) |
| **ドーパミン (報酬 / 学習 / 実行機能)** | learning framework + pattern recommender (skill 効果学習、reward-based selection) |
| **アセチルコリン (記憶 / 学習)** | handover / memory / context-engineering (session 跨ぎ記憶) |
| **ニューロモジュレーター統合 (Opus 統合)** | Opus PM (manager) — 複数経路を統合判断 |

詳細: [HELIX-workflows/HELIX-process-L0-L14.md](HELIX-workflows/HELIX-process-L0-L14.md) (V モデル正本) / [docs/plans/L0/L0-helix-workflows-conceptplan.md](docs/plans/L0/L0-helix-workflows-conceptplan.md) (見直し企画書) / [docs/v2/L0-helix-workflows/concept.md](docs/v2/L0-helix-workflows/concept.md) (構造原理詳細)

> 注: 本 metaphor は HELIX の構造原理を直感的に理解する anchor。生物学的厳密性は概ね正確だが、framework 設計の比喩であって生命科学 textbook ではない (笑)

## Quick Start

```bash
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git
cd ai-dev-kit-vscode
bash setup.sh
./cli/helix init
./cli/helix doctor
./cli/helix size --files 5 --lines 200
./cli/helix codex --role tl --task "PLAN-029 の設計を確認"
./cli/helix claude --role pmo --model sonnet --task "現状を要約" --execute
```

ホスト環境への導入は `setup.sh`、各プロジェクトへの HELIX 適用は `helix init`、テンプレ追従は `helix migrate` を使います。

## ロール × モデル (v2)

| ロール | 主モデル | 主責務 |
|---|---|---|
| PM | Opus | 要件、優先度、受入判断 |
| PMO | Sonnet / Haiku | 状況把握、軽作業、調査支援 |
| TL | GPT-5.5 | 設計、レビュー、ゲート判定 |
| SE | GPT-5.4 | 難易度の高い実装、契約判断、リファクタリング |
| PE | GPT-5.3-codex-spark / GPT-5.3-codex | 速度重視の実装、定型修正 |
| Recommender | GPT-5.4-mini | スキル推挙、軽量分類 |
| pdm-tech-innovation | Opus | 技術思想翻案、技術検討の早期提案 |
| pdm-marketing-innovation | Opus | 海外マーケ知見翻案と GTM 仮説 |
| pdm-innovation-manager | Opus | PdM 統合、意思決定、L1 接続 |

正本は `cli/config/models.yaml` と `cli/roles/*.conf` です。

## V2 Phase 2 拡張 (2026-05-15)

### V-model 強化

- `helix vmodel show <drive> <layer>`
- `helix gate --subgate functional_freeze --drive <DRIVE>`
- 詳細: [docs/operations/v2-operations-guide.md](docs/operations/v2-operations-guide.md)

### 停滞防止システム

- `helix push --gate` (6 ゲート機械検証 + auto-push)
- `helix pr --gate --auto-merge`
- 詳細: [docs/operations/stop-prevention.md](docs/operations/stop-prevention.md)

### PdM Innovation team

- `/innovation-tech`, `/innovation-marketing`, `/innovation-synthesize`
- 詳細: [docs/operations/pdm-innovation-workflow.md](docs/operations/pdm-innovation-workflow.md)

### PMO 9 ロール

- 詳細: [docs/operations/pmo-roster.md](docs/operations/pmo-roster.md)

## フロー概要

- Forward HELIX: `L1 -> L2 -> L3 -> L4 -> L5 -> L6 -> L7 -> L8 -> L9 -> L10 -> L11`
- Reverse HELIX: `R0 -> R1 -> R2 -> R3 -> R4 -> Forward -> RGC`
- Scrum HELIX: `S0 -> S1 -> S2 -> S3 -> S4`
- Gate: `G0.5/G1/G1.5/G1R/G2-G11` で設計、実装、検証、運用学習を fail-close 管理

## 主要ディレクトリ

- `cli/`: HELIX CLI、本体スクリプト、SQLite helper、テスト
- `skills/`: 100+ の HELIX スキルカタログと参照資料
- `docs/architecture/`: アーキテクチャ図、責務マップ、全体設計
- `docs/adr/`: Architecture Decision Records
- `docs/plans/`: PLAN-NNN 仕様書
- `docs/research/`: Web / GitHub / 先行事例の調査記録
- `docs/runbook/`: 障害対応、運用導線、復旧手順

## 主要コマンド

| コマンド | 用途 |
|---|---|
| `helix init` | プロジェクト初期化 |
| `helix doctor` | 環境整合チェック |
| `helix size` | タスクサイジング |
| `helix plan` | 設計計画の draft / review / finalize |
| `helix codex` | Codex 委譲 (TL / SE / PE / security / research など) |
| `helix claude` | Claude Code 委譲 (PMO Sonnet / Haiku) |
| `helix gate G1..G11` | フェーズゲート判定 |
| `helix sprint` | L4 マイクロスプリント管理 |
| `helix scrum` | 仮説検証フロー |
| `helix reverse R0-R4` | Reverse HELIX |
| `helix research --layer L1-L3` | レイヤ単位の調査起票 |
| `helix plan --mini` | mini-PLAN 作成 |
| `helix handover --mode` | PM <-> TL 引継ぎ |
| `helix code` | コードカタログ検索 |
| `helix skill` | スキル推挙、参照 |
| `helix budget` | モデルとコスト管理 |
| `helix test` | pytest / bats / shell テスト実行 |

全コマンドの索引は [docs/commands/index.md](docs/commands/index.md) を参照してください。

## 運用導線

### 1. ホストへ HELIX を導入

```bash
bash setup.sh
```

### 2. プロジェクトを HELIX 管理下に置く

```bash
helix init
helix doctor
```

### 3. タスクを設計し、実装へ委譲する

```bash
helix size --files 10 --lines 300 --api --drive be
helix plan draft --title "認証 API"
helix plan review --id PLAN-001
helix plan finalize --id PLAN-001
helix codex --role se --task "PLAN-001 の L4 実装" --approved
helix review --uncommitted
```

## ドキュメント

- [docs/plans/PLAN-028-helix-v2-orchestration.md](docs/plans/PLAN-028-helix-v2-orchestration.md): HELIX v2 orchestration
- [docs/plans/PLAN-029-helix-rigor-expansion.md](docs/plans/PLAN-029-helix-rigor-expansion.md): HELIX 11 軸厳格化拡張
- [docs/architecture/](docs/architecture/): 全体設計と責務整理
- [docs/adr/](docs/adr/): 設計判断記録
- [docs/runbook/README.md](docs/runbook/README.md): 運用 runbook 一覧

## 開発とテスト

```bash
python3 -m pip install --user -r requirements-dev.txt
python3 -m pytest cli/lib/tests/ -q --tb=short
./cli/helix test --no-pytest --bats-only
```

Codex / Claude Code の利用ルールは `AGENTS.md`、`CLAUDE.md`、`docs/commands/ai-harness.md` を正本とします。

## License

MIT

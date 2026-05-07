# PLAN-029 厳格化拡張 — 先行事例調査 (2026-05-08)

## 調査概要
- 目的: HELIX の Sprint 厳格化、フェーズゲート、agent 2 段設計、Run 3 フェーズ、docs+helix.db 強化を支える先行事例を収集する。
- 範囲: Web / GitHub / 公式 docs / 著名技術ブログ / 書籍情報。一次ソースを優先し、公開日不明の公式 docs は「公開日不明」とした。
- 評価軸: HELIX 適合性、運用強制力、導入コスト、監査可能性、拡張性、制約性、AI agent への適用可能性。
- 不確実性: 2026 年時点の AI coding tool 比較は変化が速い。最新機能・価格・メンテナンス状態は採用直前に再確認が必要。

## A. Sprint-level rigorous review

### A.1 Cursor Bugbot / Bugbot Autofix
- URL: https://docs.cursor.com/en/bugbot
- 補助 URL: https://cursor.com/changelog/02-26-26/
- 出版元 / 公開日: Cursor docs / 公開日不明、Cursor changelog / 2026-02-26。
- 概要: Bugbot は PR diff を自動レビューし、バグ・セキュリティ・品質問題をコメントする。PR 更新ごとの自動実行とコメントによる手動実行を備える。
- メリット: Sprint 終了時の人間レビュー前に defect 候補を抽出できる。`.cursor/BUGBOT.md` でプロジェクト固有ルールを注入できる。
- デメリット: SaaS / GitHub App 依存があり、HELIX のローカル fail-close とは責務境界を分ける必要がある。
- 推奨度: 高。HELIX の L4.5 / G4 前レビューに「AI diff review + project rules」パターンとして採用。

### A.2 aider auto-lint / auto-test
- URL: https://aider.chat/docs/usage/lint-test.html
- 出版元 / 公開日: aider docs / 公開日不明。
- 概要: aider は AI 編集後に lint / test を自動実行し、失敗時に修正を試みる。`--lint-cmd`、`--test-cmd`、`--auto-test` で既存検証へ接続できる。
- メリット: AI 編集と検証を同一ループに閉じ込め、Sprint 中の小さな回帰を早期に発見できる。
- デメリット: 自動修正が検証コストを増やす可能性がある。コミット自動化は HELIX の no-commit 委譲規律と衝突しうる。
- 推奨度: 高。HELIX L4 `.2-.4` の「編集後必ず対象テスト」規律として抽象化する。

### A.3 GitHub protected branches / required status checks
- URL: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- 出版元 / 公開日: GitHub Docs / 公開日不明。
- 概要: protected branch は PR review、required status checks、conversation resolution、deployment success などを merge 条件にできる。
- メリット: pre-merge / pre-deploy gate を SCM 側で強制でき、HELIX の gate 結果と CI を接続しやすい。
- デメリット: GitHub 上の設定だけでは L1-L3 成果物の意味的整合までは保証できない。
- 推奨度: 高。HELIX gate の最終 enforcement layer として利用し、設計・契約 gate は HELIX 側で補完する。

## B. Phase gate enforcement

### B.1 Stage-Gate Discovery-to-Launch
- URL: https://www.stage-gate.com/about/stage-gate-innovation-performance-framework/discovery-to-launch-process/
- 補助 URL: https://www.stage-gate.com/blog/the-stage-gate-model-an-overview/
- 出版元 / 公開日: Stage-Gate International / overview は 2026 年初頭、Discovery-to-Launch は公開日不明。
- 概要: アイデアからローンチまでを stage と gate に分割し、各 gate で進行・停止・保留・差戻しを判断する。
- メリット: HELIX の L1-L11 を「成果物作成 stage」と「判定 gate」に明確分離する根拠になる。
- デメリット: そのまま導入すると重厚で、AI 駆動開発の短サイクルには過剰になりやすい。
- 推奨度: 高。gate 判定語彙と go/kill/hold/recycle 相当の状態管理だけ採用する。

### B.2 Disciplined Agile Delivery Inception / Transition
- URL: https://www.pmi.org/disciplined-agile/inception-goals
- 補助 URL: https://www.pmi.org/disciplined-agile/transition-goals
- 出版元 / 公開日: PMI Disciplined Agile / 公開日不明。
- 概要: DAD は Inception、Construction、Transition を明示し、初期方針・リリース準備・本番投入を段階化する。
- メリット: HELIX の L1-L3 と L9-L11 に相当する前後工程を正当化できる。
- デメリット: Agile 文脈では「phase」自体が忌避される場合があり、軽量性の説明が必要。
- 推奨度: 中高。Inception = L1-L3、Transition = Run 3 フェーズの参照モデルとして採用。

### B.3 Boehm Spiral Model
- URL: https://docs.edtechhub.org/lib/A29EGW7U
- 原典 URL: https://ieeexplore.ieee.org/document/59
- 出版元 / 公開日: IEEE Computer / 1988-05-01。
- 概要: Spiral model はリスク駆動で各 cycle の目的、代替案、制約、リスク評価、レビューを回す。
- メリット: HELIX の G1R / PoC / Scrum hypothesis validation を「不確実性を先に潰す」設計として説明できる。
- デメリット: 実装詳細ではなく process model なので、現代 CI/CD への翻訳が必要。
- 推奨度: 中高。高リスク変更時の G1.5/G1R 強制条件に採用。

## C. Multi-stage agent system 2-tier design

### C.1 LangGraph Supervisor
- URL: https://reference.langchain.com/javascript/modules/_langchain_langgraph-supervisor.html
- 出版元 / 公開日: LangChain reference / 公開日不明。
- 概要: supervisor が専門 agent を orchestration し、通信と委譲を制御する hierarchical multi-agent パターン。
- メリット: HELIX の TL / SE / QA / Research の役割分離と、上位制御層・実行層の分離に近い。
- デメリット: supervisor への集中はボトルネック化しうる。状態永続化・監査は別途必要。
- 推奨度: 高。HELIX v2 の harness layer と role execution layer の二層化に採用。

### C.2 Microsoft AutoGen Core / AgentChat / Extensions
- URL: https://microsoft.github.io/autogen/stable/index.html
- GitHub URL: https://github.com/microsoft/autogen
- 出版元 / 公開日: Microsoft / 公開日不明。GitHub README は 2026 年時点で maintenance mode と明記。
- 概要: Core はイベント駆動 runtime、AgentChat は高水準 multi-agent API、Extensions は provider / tool 統合を担う。
- メリット: infrastructure layer と application layer の責務分離が明確。HELIX の harness / role prompt / tool adapter 分離に有用。
- デメリット: AutoGen 本体は maintenance mode のため新規採用対象ではなく、設計参照に留めるべき。
- 推奨度: 中。設計パターンは採用、実装依存は避ける。

### C.3 CrewAI hierarchical process
- URL: https://docs.crewai.com/en/learn/hierarchical-process
- 出版元 / 公開日: CrewAI docs / 公開日不明。
- 概要: manager agent が task delegation、result validation、workflow coordination を担う hierarchical process。
- メリット: manager が成果を検証する点が HELIX gate owner と整合する。
- デメリット: CrewAI 固有の runtime・enterprise 機能に依存しやすい。
- 推奨度: 中高。manager validation の考え方を HELIX role delegation に取り込む。

## D. Scrum hypothesis validation

### D.1 Lean Startup Build-Measure-Learn
- URL: https://www.lean.org/lexicon-terms/lean-startup/
- 補助 URL: https://www.wired.com/story/the-upstart
- 出版元 / 公開日: Lean Enterprise Institute / 公開日不明、Wired / 2012 年前後。
- 概要: MVP と Build-Measure-Learn loop で仮説を検証し、validated learning によって pivot / persevere を判断する。
- メリット: HELIX Scrum の hypothesis backlog、PoC、verify、decide に直結する。
- デメリット: ビジネス検証の文脈が強く、技術 gate へ使う場合は成功指標を明示する必要がある。
- 推奨度: 高。Scrum 拡張の基本ループとして採用。

### D.2 SVPG continuous discovery / delivery
- URL: https://www.svpg.com/continuous-discovery/
- 補助 URL: https://www.svpg.com/discovery-delivery/
- 出版元 / 公開日: SVPG / 2012-10-24、2020-10-30。
- 概要: discovery と delivery を分断せず、プロダクトチームが継続的に学習と実装を並行する。
- メリット: HELIX の L1-L3 と L4 を完全分離せず、G1R / PoC / refinement を継続的に扱う根拠になる。
- デメリット: 厳格 gate と相性が悪く見えるため、gate は学習停止ではなく「次の投資判断」と定義する必要がある。
- 推奨度: 高。Scrum extension と L1-L3 re-entry ルールに採用。

### D.3 Scrum.org spikes / backlog refinement
- URL: https://www.scrum.org/resources/blog/product-backlog-refinement-explained-23
- 補助 URL: https://www.scrum.org/resources/frequently-asked-questions
- 出版元 / 公開日: Scrum.org / 2016-03-21、FAQ は公開日不明。
- 概要: spike は情報収集や技術調査を目的とする timeboxed activity とされ、Product Backlog refinement と強く関係する。
- メリット: HELIX の G1R / PoC sprint を「出荷物ではなく意思決定のための work」として扱える。
- デメリット: spike を乱用すると価値提供の代替物になる。
- 推奨度: 中高。timebox、明確な問い、終了条件を必須にして採用。

## E. L1-L3 design rigor

### E.1 Architecture Decision Records
- URL: https://github.com/phillduffy/architecture_decision_record
- 補助 URL: https://docs.edgexfoundry.org/4.0/design/adr/
- 出版元 / 公開日: GitHub README / 公開日不明、EdgeX Foundry docs / 公開日不明。
- 概要: ADR は重要な設計判断、文脈、代替案、結果を短い記録として残す。
- メリット: HELIX L2/G2 の「設計凍結」証跡として軽量かつ運用しやすい。
- デメリット: 記録だけでは enforcement にならない。drift check と結合する必要がある。
- 推奨度: 高。L2 の必須成果物または PLAN ごとの decision register として採用。

### E.2 C4 Model
- URL: https://c4model.com/
- 出版元 / 公開日: Simon Brown official site / 公開日不明。
- 概要: System Context、Container、Component、Code の階層で software architecture を可視化する。
- メリット: HELIX L1-L3 の抽象度を L1=Context、L2=Container、L3=Component/Contract に対応させやすい。
- デメリット: 図だけでは API / DB / state contract の完全性を保証しない。
- 推奨度: 高。L2 の最小 architecture map として採用。

### E.3 Thoughtworks Technology Radar
- URL: https://www.thoughtworks.com/en-us/radar
- 出版元 / 公開日: Thoughtworks / Vol.33、2026 年時点。
- 概要: 技術を Adopt / Trial / Assess / Hold の ring に分類し、チーム経験に基づく技術選定判断を共有する。
- メリット: HELIX の tech-selection に「採用・試行・評価・保留」の標準語彙を与える。
- デメリット: Thoughtworks の文脈に依存するため、HELIX 内部では独自基準と重み付けが必要。
- 推奨度: 中高。L2 tech selection matrix に ring 概念を採用。

## F. Reverse engineering review patterns

### F.1 Strangler Fig Application
- URL: https://martinfowler.com/bliki/StranglerFigApplication.html
- 補助 URL: https://martinfowler.com/bliki/OriginalStranglerFigApplication.html
- 出版元 / 公開日: Martin Fowler / 2024-08-22、original は 2004-06-29。
- 概要: 既存システムを一括置換せず、新旧を並走させながら段階的に置き換える modernization pattern。
- メリット: Reverse HELIX の R4 Gap & Routing から Forward HELIX へ接続する際の安全な移行戦略になる。
- デメリット: ルーティング境界、データ同期、観測を設計しないと複雑性が増える。
- 推奨度: 高。大規模 legacy 改修の基本 routing pattern として採用。

### F.2 AWS 7 Rs migration strategies
- URL: https://docs.aws.amazon.com/prescriptive-guidance/latest/large-migration-guide/migration-strategies.html
- 出版元 / 公開日: AWS Prescriptive Guidance / 公開日不明。
- 概要: Retire、Retain、Rehost、Relocate、Repurchase、Replatform、Refactor/Re-architect の移行戦略分類。
- メリット: Reverse R4 の gap を「保持・撤退・移設・再構築」などに分類する実務語彙になる。
- デメリット: Cloud migration 寄りであり、コード設計復元には追加分類が必要。
- 推奨度: 中高。R4 routing taxonomy の参照として採用。

### F.3 Working Effectively with Legacy Code / characterization tests
- URL: https://www.pearson.com/en-us/subject-catalog/p/working-effectively-with-legacy-code/P200000008984
- 補助 URL: https://www.infoq.com/news/2007/03/characterization-testing/
- 出版元 / 公開日: Pearson / 2004-09-22、InfoQ / 2007-03-31。
- 概要: Michael Feathers の legacy code 改修手法。現行挙動を characterization test で固定してから変更する。
- メリット: Reverse R1 observed contracts と characterization tests の直接的な根拠になる。
- デメリット: 既存挙動にバグが含まれる場合、それも固定してしまう危険がある。
- 推奨度: 高。Reverse R1/RG1 の test-first evidence として採用。

## G. 拡張性 × 制約性両立フレームワーク

### G.1 VS Code Extension API
- URL: https://code.visualstudio.com/api/extension-capabilities/overview
- 出版元 / 公開日: Microsoft VS Code docs / 2026-04-15 表示あり。
- 概要: contribution points と Extension Host によって拡張性を提供しつつ、DOM access や custom stylesheet を制限する。
- メリット: HELIX plugin / skill の「拡張点は開くが内部構造は隠す」設計に直結する。
- デメリット: API 設計と sandbox を用意しないと制約が形骸化する。
- 推奨度: 高。HELIX extension point policy の中核に採用。

### G.2 IntelliJ Platform extension points
- URL: https://plugins.jetbrains.com/docs/intellij/plugin-extensions.html
- 出版元 / 公開日: JetBrains / 公開日不明。
- 概要: plugin.xml の extension point と stateless extension 実装で IDE 機能を拡張する。
- メリット: extension point の契約、namespace、stateless 制約は HELIX skill/plugin 設計に有用。
- デメリット: Java / IntelliJ 固有の lifecycle はそのまま転用できない。
- 推奨度: 中高。拡張仕様の命名・状態制約・動的検証に採用。

### G.3 Eclipse extensions and extension points
- URL: https://help.eclipse.org/latest/topic/org.eclipse.pde.doc.user/concepts/extension.htm
- 出版元 / 公開日: Eclipse Foundation / 公開日不明。
- 概要: extension point を socket、extension を plug とする契約ベースの loose coupling。
- メリット: HELIX の skill / command / recipe / hook を extension point 化する説明モデルとして分かりやすい。
- デメリット: XML registry 型の重厚さは HELIX CLI には過剰。
- 推奨度: 中。概念モデルのみ採用。

## H. Agent system observability + 運用

### H.1 Langfuse
- URL: https://langfuse.com/docs
- GitHub URL: https://github.com/langfuse/langfuse
- 出版元 / 公開日: Langfuse docs / 公開日不明、GitHub README / 2026 年時点。
- 概要: LLM observability、prompt management、evaluation、metrics を備えた OSS LLM engineering platform。
- メリット: trace、cost、latency、eval、prompt version を同じ観測面に置ける。
- デメリット: 本格導入は ClickHouse 等の運用負荷を伴う。HELIX では軽量 SQLite との責務分離が必要。
- 推奨度: 高。helix.db の event schema と外部 export 方針の参照に採用。

### H.2 Arize Phoenix
- URL: https://arize.com/docs/phoenix
- 出版元 / 公開日: Arize AI / 公開日不明。
- 概要: OpenTelemetry / OpenInference ベースで AI app の tracing、evaluation、datasets、experiments を扱う OSS observability tool。
- メリット: agent run を traces / spans で見える化し、評価と実験を接続できる。
- デメリット: Phoenix と Arize AX は別製品であり、実装時には対象製品の確認が必要。
- 推奨度: 高。HELIX の agent trace schema と external OTEL export の参照に採用。

### H.3 OpenAI Agents SDK tracing / guardrails
- URL: https://openai.github.io/openai-agents-python/tracing/
- 補助 URL: https://openai.github.io/openai-agents-python/guardrails/
- 出版元 / 公開日: OpenAI Agents SDK docs / 公開日不明。
- 概要: agent run、LLM generation、tool call、handoff、guardrail を trace/span として記録し、guardrail tripwire で停止できる。
- メリット: HELIX の tool guard、handoff、gate failure を span として記録する設計に直結する。
- デメリット: Hosted tool / handoff など guardrail 適用境界に制約がある。
- 推奨度: 高。agent run の標準 event taxonomy として採用。

## I. helix.db / SQLite event log 設計

### I.1 Event Sourcing
- URL: https://www.martinfowler.com/eaaDev/EventSourcing.html
- 出版元 / 公開日: Martin Fowler / 2005-12-12。
- 概要: application state の変更をすべて event sequence として保存し、過去状態の再構築や調整に使う。
- メリット: helix.db を「現在状態の置き場」ではなく「実行履歴の証跡」として設計する根拠になる。
- デメリット: event replay、schema evolution、個人情報削除との相性に注意が必要。
- 推奨度: 高。helix.db の append-only action/event log 原則として採用。

### I.2 PostgreSQL audit trigger schema
- URL: https://wiki.postgresql.org/wiki/Audit_trigger
- 補助 URL: https://wiki.postgresql.org/wiki/Audit_trigger_91plus
- 出版元 / 公開日: PostgreSQL wiki / 公開日不明。
- 概要: schema/table/user/action/timestamp/original/new/query などを audit.logged_actions に保存する trigger 例。
- メリット: actor、action、target、before/after、timestamp の audit columns を helix.db に転用できる。
- デメリット: SELECT / DDL / superuser tampering は trigger では完全監査できない。
- 推奨度: 中高。SQLite event log の最低列設計に採用し、限界も明記する。

### I.3 DORA metrics automation
- URL: https://conf.researchr.org/details/icsme-2023/icsme-2023-papers/25/A-Framework-for-Automating-the-Measurement-of-DevOps-Research-and-Assessment-DORA-M
- 出版元 / 公開日: ICSME 2023 / 2023-10-04。
- 概要: DORA metrics を特定 deployment infrastructure に依存せず測定する framework の研究。
- メリット: HELIX の sprint / gate / deploy event を metrics DB として活用する方向性を支える。
- デメリット: DORA は delivery performance 指標であり、設計品質や agent 品質は別指標が必要。
- 推奨度: 中高。L4-L11 の flow metrics として採用。

## J. 設計デグレ防止 / 整合性チェック

### J.1 Architectural fitness functions
- URL: https://www.oreilly.com/library/view/building-evolutionary-architectures/9781491986356/
- 出版元 / 公開日: O'Reilly / 2017、2nd edition は 2022。
- 概要: architecture の望ましい特性を継続的に検証する fitness function として表現する。
- メリット: HELIX gate を単なる checklist ではなく、継続実行される design constraint test と定義できる。
- デメリット: fitness function の過剰化は開発速度を下げる。
- 推奨度: 高。G2/G3/G4/G6 の自動チェック設計に採用。

### J.2 ArchUnit
- URL: https://www.archunit.org/userguide/html/000_Index.html
- 出版元 / 公開日: ArchUnit docs / v1.4.1、2025-05-07 リリース表示あり。
- 概要: Java bytecode を解析し、package dependency、layer、cycle、PlantUML component diagram などを unit test として検証する。
- メリット: 「設計図とコードの整合」を test framework に載せる具体例。
- デメリット: Java 中心。HELIX では language-specific checker の一例に留める。
- 推奨度: 高。dependency-map / contract drift checker の参照実装として採用。

### J.3 dependency-cruiser
- URL: https://www.npmjs.com/package/dependency-cruiser
- GitHub rules URL: https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md
- 出版元 / 公開日: npm / 2026 年時点で v17.0.1、GitHub README / 公開日不明。
- 概要: JavaScript / TypeScript 依存関係を rule で検証し、違反を CI 出力や graph として可視化する。
- メリット: HELIX の frontend / CLI dependency gate に使いやすい。
- デメリット: 依存方向は検出できても、API 意味論や UX 契約までは検出できない。
- 推奨度: 中高。JS/TS 対象の G3/G4 dependency fitness function として採用。

## K. AI 駆動開発の 2026 年現在のベストプラクティス

### K.1 Claude Code best practices
- URL: https://code.claude.com/docs/en/best-practices
- 出版元 / 公開日: Anthropic / 公開日不明。
- 概要: agentic coding では context window 管理、checkpoint、resume、parallel sessions、autonomous mode の制約理解が重要とされる。
- メリット: HELIX の context discipline、handover、multi-agent 分担、rewind 相当の証跡設計に有用。
- デメリット: Claude Code 固有機能が多く、Codex / HELIX CLI では抽象化が必要。
- 推奨度: 高。session / handover / context budget rule に採用。

### K.2 OpenAI Codex CLI / Codex cloud
- URL: https://help.openai.com/en/articles/11096431-openai-codex-ci-getting-started
- 補助 URL: https://platform.openai.com/docs/codex
- 出版元 / 公開日: OpenAI Help Center / 2026 年時点で更新あり、OpenAI Platform docs / 公開日不明。
- 概要: Codex CLI は Suggest / Auto Edit / Full Auto の approval modes を持ち、Codex cloud は sandboxed cloud task と並列作業を提供する。
- メリット: HELIX の consent_mode、approved、sandbox、allowed_files の規律と対応しやすい。
- デメリット: full auto は安全境界の説明が必須。外部 cloud task は secret / repo permission の統制が必要。
- 推奨度: 高。approval mode と sandbox mode の設計語彙として採用。

### K.3 aider / OpenCode / OSS coding agents
- URL: https://github.com/aider-ai/aider
- 補助 URL: https://opencode.ai/
- 出版元 / 公開日: GitHub README / 2026 年時点、OpenCode official / 公開日不明。
- 概要: aider は repo map、lint/test、git integration を持つ terminal pair programming agent。OpenCode は LSP、多セッション、provider 選択、privacy を掲げる OSS agent。
- メリット: repo map、LSP、multi-session、local-first は HELIX の code index / role delegation と相性が良い。
- デメリット: OSS agent はメンテナンス状態が変動しやすい。OpenCode は同名プロジェクトの移行・アーカイブ情報が混在するため採用前確認が必要。
- 推奨度: 中高。機能トレンドとして採用し、依存先としては慎重に扱う。

## 統合観点 (HELIX への適用)

### 既存 HELIX framework との対応関係
- L1/G1: Lean Startup / SVPG / Scrum.org の hypothesis と refinement を使い、要件を「仮説 + 受入条件 + 検証指標」に固定する。
- G1R: Boehm Spiral、Scrum spikes、Thoughtworks hypothesis development を使い、不確実性が高い場合は調査 gate を必須化する。
- L2/G2: ADR、C4、Technology Radar を使い、方針・構成・技術選定を軽量だが凍結可能な成果物にする。
- L3/G3: Stage-Gate と fitness functions を使い、契約・依存・工程表を gateable artifacts として扱う。
- L4 Sprint: aider auto-test、Cursor Bugbot、GitHub required checks を使い、編集後検証・AI review・CI enforcement を分離する。
- L5-L8: design / integration / acceptance は DAD Transition と GitHub deployment checks に対応させる。
- L9-L11: DAD Transition、DORA、observability tools を使い、deploy readiness、watch、learning を Run phase として分離する。
- Reverse R0-R4: Feathers characterization tests、AWS 7 Rs、Strangler Fig を使い、証拠取得から routing までを段階化する。
- Agent harness: LangGraph Supervisor、AutoGen layered design、CrewAI manager validation を使い、infrastructure layer と execution layer を分ける。
- helix.db: Event Sourcing、audit trigger、OpenAI/Phoenix/Langfuse tracing を使い、append-only event log と trace/span schema を統合する。

### 取り入れるべきパターン Top 10
1. Project-specific AI review rules: Cursor Bugbot の `.cursor/BUGBOT.md` 相当を HELIX の `AGENTS.md` / skill / gate rules に対応させる。
2. Edit-test repair loop: aider の auto-lint / auto-test を L4 `.2-.4` の標準検証ループにする。
3. SCM enforcement: GitHub required checks を HELIX gate status の最終 merge enforcement に使う。
4. Gate state vocabulary: Stage-Gate の go / kill / hold / recycle を HELIX の passed / failed / blocked / interrupted / carry に対応させる。
5. Risk-first research gate: Boehm Spiral と spike を G1R / G1.5 の発火条件にする。
6. Two-tier agent architecture: supervisor / manager / core runtime と role execution を分離する。
7. ADR + C4 design freeze: L2 成果物を「判断記録 + 階層図 + 制約」に統一する。
8. Characterization-before-change: Reverse R1 で現行挙動 test を作ってから Forward へ接続する。
9. Extension point with constraints: VS Code / IntelliJ / Eclipse 型の拡張点契約と禁止事項を HELIX plugin / skill に導入する。
10. Trace/span + event sourcing: helix.db に actor、action、target、input/output hash、gate、span、result、timestamp を記録する。

### 取り入れない / 慎重なパターン
- SaaS 専用 AI review への全面依存: GitHub App や cloud agent は便利だが、secret / repo permission / network policy の統制が必要。
- 重厚な Stage-Gate の完全移植: AI 駆動開発の短サイクルを阻害する。状態語彙と gate 原則だけ採用する。
- AutoGen 本体への新規依存: 2026 年時点で maintenance mode とされるため、layered design の参照に留める。
- Spike の backlog 化乱用: Scrum.org が指摘する通り、busywork 化しやすい。問い、timebox、終了条件がない spike は禁止する。
- DORA だけで品質判断: delivery performance は測れるが、設計整合・agent 安全性・仕様忠実度は別指標が必要。
- In-database audit の過信: PostgreSQL audit trigger でも SELECT / DDL / superuser tampering は限界がある。HELIX では OS / Git / tool log と併用する。

### HELIX 独自で設計すべき空白領域
- AI agent 用 phase gate の標準 schema: 従来 gate は人間プロセス向けで、LLM tool call / handoff / prompt drift / context exhaustion を扱い切れない。
- docs + code + db の三者整合 gate: ADR / C4 / ArchUnit は個別にはあるが、HELIX の doc-map、contract、helix.db を一体で検証する既存標準は薄い。
- Role delegation audit: supervisor pattern はあるが、TL/SE/QA/Research の責任境界と allowed_files を監査する lightweight schema は HELIX 独自設計が必要。
- Design-later / visual-after-build の gate: 一般手法は discovery/delivery が中心で、HELIX の L5 Visual Refinement 後置を明確に扱う事例は少ない。
- Reverse to Forward routing: Strangler / 7Rs / characterization tests はあるが、R0-R4 から L1-L11 へ機械的に接続する gate system は HELIX 固有領域。

## ソース一覧
- Cursor Bugbot: https://docs.cursor.com/en/bugbot
- Cursor Bugbot Autofix: https://cursor.com/changelog/02-26-26/
- aider lint/test: https://aider.chat/docs/usage/lint-test.html
- GitHub protected branches: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- Stage-Gate Discovery-to-Launch: https://www.stage-gate.com/about/stage-gate-innovation-performance-framework/discovery-to-launch-process/
- Disciplined Agile Inception: https://www.pmi.org/disciplined-agile/inception-goals
- Disciplined Agile Transition: https://www.pmi.org/disciplined-agile/transition-goals
- Boehm Spiral Model metadata: https://docs.edtechhub.org/lib/A29EGW7U
- LangGraph Supervisor: https://reference.langchain.com/javascript/modules/_langchain_langgraph-supervisor.html
- AutoGen: https://microsoft.github.io/autogen/stable/index.html
- CrewAI hierarchical process: https://docs.crewai.com/en/learn/hierarchical-process
- SVPG continuous discovery: https://www.svpg.com/continuous-discovery/
- SVPG discovery-delivery: https://www.svpg.com/discovery-delivery/
- Lean Startup overview: https://www.lean.org/lexicon-terms/lean-startup/
- Scrum.org refinement/spikes: https://www.scrum.org/resources/blog/product-backlog-refinement-explained-23
- ADR templates: https://github.com/phillduffy/architecture_decision_record
- C4 Model: https://c4model.com/
- Thoughtworks Technology Radar: https://www.thoughtworks.com/en-us/radar
- Strangler Fig Application: https://martinfowler.com/bliki/StranglerFigApplication.html
- AWS 7 Rs: https://docs.aws.amazon.com/prescriptive-guidance/latest/large-migration-guide/migration-strategies.html
- Working Effectively with Legacy Code: https://www.pearson.com/en-us/subject-catalog/p/working-effectively-with-legacy-code/P200000008984
- VS Code Extension API: https://code.visualstudio.com/api/extension-capabilities/overview
- IntelliJ Plugin Extensions: https://plugins.jetbrains.com/docs/intellij/plugin-extensions.html
- Eclipse extension points: https://help.eclipse.org/latest/topic/org.eclipse.pde.doc.user/concepts/extension.htm
- Langfuse docs: https://langfuse.com/docs
- Arize Phoenix: https://arize.com/docs/phoenix
- OpenAI Agents tracing: https://openai.github.io/openai-agents-python/tracing/
- OpenAI Agents guardrails: https://openai.github.io/openai-agents-python/guardrails/
- Event Sourcing: https://www.martinfowler.com/eaaDev/EventSourcing.html
- PostgreSQL audit trigger: https://wiki.postgresql.org/wiki/Audit_trigger
- DORA metrics automation: https://conf.researchr.org/details/icsme-2023/icsme-2023-papers/25/A-Framework-for-Automating-the-Measurement-of-DevOps-Research-and-Assessment-DORA-M
- Building Evolutionary Architectures: https://www.oreilly.com/library/view/building-evolutionary-architectures/9781491986356/
- ArchUnit: https://www.archunit.org/userguide/html/000_Index.html
- dependency-cruiser: https://www.npmjs.com/package/dependency-cruiser
- Claude Code best practices: https://code.claude.com/docs/en/best-practices
- OpenAI Codex CLI: https://help.openai.com/en/articles/11096431-openai-codex-ci-getting-started
- OpenAI Codex cloud: https://platform.openai.com/docs/codex
- aider GitHub: https://github.com/aider-ai/aider
- OpenCode: https://opencode.ai/
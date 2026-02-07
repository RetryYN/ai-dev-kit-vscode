# Helix: AI-Driven Development Framework

**"DNA of AI-driven development" - 設計書を上回る開発を実現する多層検証フレームワーク**

---

## 概要

**Helix**は、Claude Code + Codex の密接連携により、**設計書水準以上の開発**を実現するAIエージェント駆動の開発フレームワークです。

企画書を渡すだけで、要件定義からデプロイまでエージェントが自律的に実行。V字モデルの多層検証ループにより、Frontend/Backend/DB間のズレや手戻りを最小化し、高品質なコードを継続的に生成します。

### 主な特徴

| 特徴 | 説明 |
|------|------|
| 🎯 **設計書を上回る開発** | 単なる要件充足ではなく、パフォーマンス・保守性・拡張性で設計を超える（Lv5基準） |
| 🤖 **完全エージェント駆動** | ユーザー負担は企画のみ。要件定義〜デプロイまで全自動 |
| 🔄 **多層検証ループ** | L1〜L5の独立した検証サイクルで問題を早期発見・自動修復 |
| 🔗 **API整合性保証** | Frontend/Backend/DB間の型・スキーマを自動検証（L2.5） |
| 📊 **数値ベース品質管理** | エージェントの自己申告を信用せず、すべて数値で検証 |
| 🚀 **Sonnet 5.0対応** | ワークフロー駆動のため、新モデルは即座に活用可能 |
| 💰 **コスト最適化** | Opus（スポット）、Codex（計画）、Sonnet（実装）、Haiku（軽量）の役割分担 |

---

## 競合比較

| ツール/フレームワーク | アプローチ | Helixとの違い |
|---------------------|-----------|--------------|
| **superpowers** (27.9k stars) | スキルコレクション + /plan コマンド | スキル提供。検証ループなし |
| **claude-flow** (11.4k stars) | マルチエージェントオーケストレーション | エージェント連携。多層検証なし |
| **skill-codex** | Codex CLI 連携 | CLI統合。品質保証機構なし |
| **SkillsMP** | 71,000+ スキルマーケットプレイス | スキル提供。フレームワークなし |
| **Helix** ★ | **多層検証ループ + エージェント駆動** | **L1〜L5検証 + API整合性保証 + 設計書超え基準** |

**Helixの独自性:**
- 他のツールは「スキルを提供」または「エージェントを連携」する
- **Helixは多層検証ループで品質を構造的に保証し、設計書を上回る開発を実現**

---

## ドキュメント戦略（Progressive Disclosure）

このフレームワーク文書は巨大。全体をコンテキストにロードするとトークンを圧迫する。必要な部分だけをロードする。

### 分割構成

```
helix/
├── HELIX.md                    # ★ エントリーポイント（常時ロード・500行以下）
│                               #   概要 + 目次 + クイックスタート + 参照リンク
├── core/                       # コア概念（必要時ロード）
│   ├── verification-layers.md  # L1-L5検証レイヤー詳細
│   ├── agent-roles.md          # エージェント人事配置
│   ├── workflow.md             # 基本ワークフロー
│   └── quality-levels.md       # Lv1-Lv5品質基準
├── operations/                 # 運用系（フェーズ毎にロード）
│   ├── planning.md             # 計画フェーズ（工程表、難易度判定）
│   ├── implementation.md       # 実装フェーズ（サブエージェント、スキル）
│   ├── verification.md         # 検証フェーズ（テスト、レビュー）
│   └── escalation.md           # エスカレーション規則
├── skills/                     # スキル管理
│   ├── skill-lifecycle.md      # スキル生成・改善フロー
│   ├── knowledge-accumulation.md # ナレッジ蓄積
│   └── skill-templates/        # スキルテンプレート
├── optimization/               # 最適化系（必要時のみ）
│   ├── model-allocation.md     # AIモデル割り当て最適化
│   ├── context-management.md   # コンテキスト汚染対策
│   └── cost-optimization.md    # コスト最適化
├── tools/                      # ツール・環境
│   ├── vscode-extensions.md    # VSCode拡張機能一覧
│   ├── project-structure.md    # プロジェクト構成
│   └── settings-templates/     # 設定テンプレート
└── references/                 # 参照資料
    ├── glossary.md             # 用語集
    ├── checklists.md           # 各種チェックリスト
    └── examples/               # 実例集
```

### HELIX.md（エントリーポイント）の構造

```markdown
# Helix Framework

## 概要（50行）
{フレームワークの目的・特徴・差別化ポイント}

## クイックスタート（30行）
{最小限の手順で動かす方法}

## コンテキストロードガイド（以下）
```

### コンテキストロードガイド

| 作業フェーズ | ロードすべきファイル | トークン目安 |
|-------------|---------------------|-------------|
| **初期セットアップ** | HELIX.md + core/workflow.md | ~2,000 |
| **計画フェーズ** | + operations/planning.md + core/agent-roles.md | ~4,000 |
| **実装フェーズ** | + operations/implementation.md + 該当スキル | ~3,500 |
| **検証フェーズ** | + operations/verification.md + core/verification-layers.md | ~4,000 |
| **トラブル時** | + optimization/context-management.md | ~2,000 |
| **最適化検討** | + optimization/model-allocation.md | ~3,000 |

### ロード優先度

```yaml
# コンテキスト予算配分（100%として）
context_budget:
  always_loaded:           # 常時ロード（20%）
    - HELIX.md             # エントリーポイント
    - memory/decisions.md  # 決定事項

  phase_specific:          # フェーズ別（50%）
    - 該当フェーズのドキュメント
    - 必要なスキルファイル

  on_demand:               # オンデマンド（20%）
    - トラブルシュート資料
    - 詳細リファレンス

  reserved:                # 予約（10%）
    - エラーメッセージ
    - 動的生成コンテンツ
```

### 自動ロード判定

```python
def determine_context_load(current_phase, task, issues):
    """フェーズとタスクから必要なドキュメントを判定"""

    load_list = ['helix/HELIX.md', '.claude/memory/decisions.md']  # 常時

    # フェーズ別
    phase_docs = {
        'planning': ['core/workflow.md', 'operations/planning.md', 'core/agent-roles.md'],
        'implementation': ['operations/implementation.md'],
        'verification': ['operations/verification.md', 'core/verification-layers.md'],
    }
    load_list.extend(phase_docs.get(current_phase, []))

    # タスク種別からスキル判定（SKILL_MAP.md でパス解決）
    required_skills = infer_skills_from_task(task)
    for skill in required_skills:
        path = resolve_skill_path(skill)  # SKILL_MAP.md → skills/{category}/{name}/SKILL.md
        load_list.append(path)

    # 問題発生時は追加ロード
    if issues.get('context_pollution'):
        load_list.append('optimization/context-management.md')
    if issues.get('repeated_errors'):
        load_list.append('references/checklists.md')

    # トークン予算チェック
    return trim_to_budget(load_list, max_tokens=8000)

def trim_to_budget(files, max_tokens):
    """予算内に収まるようにファイルリストを調整"""
    total = 0
    result = []
    for f in files:
        size = estimate_tokens(f)
        if total + size <= max_tokens:
            result.append(f)
            total += size
        else:
            # 圧縮版があれば代替
            compressed = f.replace('.md', '-compact.md')
            if exists(compressed):
                result.append(compressed)
                total += estimate_tokens(compressed)
    return result
```

### 圧縮版ドキュメント（-compact.md）

各ドキュメントには圧縮版を用意。トークン制限時に代替ロード。

```markdown
# verification-layers-compact.md（圧縮版）

## L1-L5 クイックリファレンス

| レイヤー | 検証内容 | 担当 | 判定基準 |
|---------|---------|------|----------|
| L1 | 要件充足 | Codex | 要件引継書との突合 |
| L2 | 設計整合性 | Codex | 設計書との整合 |
| L2.5 | API整合性 | Codex | Frontend/Backend/DB型一致 |
| L3 | 依存関係 | Codex | 循環依存なし |
| L4 | テスト | Sonnet+Codex | カバレッジ80%以上 |
| L5 | 本番検証 | Codex | Lv5基準クリア |

詳細 → @helix/core/verification-layers.md
```

### @参照による遅延ロード

```markdown
# 実装中のコンテキスト例

現在のタスク: T-001 認証モジュール実装

## ロード済み
- HELIX.md（常時）
- operations/implementation.md（フェーズ）
- skills/common/security/SKILL.md（タスク関連）

## 必要時に参照（未ロード）
詳細な検証基準が必要な場合: @helix/core/verification-layers.md
エスカレーション規則: @helix/operations/escalation.md
VSCode設定: @helix/tools/vscode-extensions.md

→ 必要になった時点で明示的に `@` 参照してロード
```

### ドキュメント更新時のルール

| ルール | 説明 |
|--------|------|
| **500行ルール** | 各ファイルは500行以下。超えたら分割 |
| **圧縮版同期** | 本体更新時に-compact.mdも更新 |
| **目次更新** | HELIX.mdの目次を常に最新に |
| **トークン計測** | 更新後にトークン数を記録 |
| **後方互換** | 参照リンクを壊さない |

### 現在のドキュメントからの移行

```
# 移行手順

1. 現在の v-model-reference-cycle-v2.md をセクション毎に分割
2. 各ファイルのトークン数を計測
3. 500行超えは更に分割
4. 圧縮版を作成
5. HELIX.md（エントリーポイント）を作成
6. 相互参照リンクを設定
7. 旧ファイルから新構成へのリダイレクト

# トークン目安（分割後）
HELIX.md:                    ~800 tokens
core/verification-layers.md: ~2,500 tokens
core/agent-roles.md:         ~1,500 tokens
operations/planning.md:      ~3,000 tokens
...
合計: ~25,000 tokens（現在の1/3程度に圧縮可能）
```

---

## AI自律駆動開発メソッド

Helixは2025-2026年のAgentic Development最新手法を取り入れた設計。

### 基本ワークフロー（4フェーズ）

```
┌─────────────────────────────────────────────────────────────────┐
│  Explore（調査）→ Plan（計画）→ Code（実装）→ Validate（検証） │
│                                                                 │
│  ・各フェーズ間でコンテキストをクリア                           │
│  ・Plan Modeで設計を固めてから実装                              │
│  ・Validateで不合格→該当フェーズに戻る                          │
└─────────────────────────────────────────────────────────────────┘
```

### AIツール使い分け方針

| ツール | 強み | Helixでの役割 |
|--------|------|--------------|
| **Claude Code** | CLI駆動、計画重視、段階的思考、複雑なワークフロー | **メイン**: 設計・検証・オーケストレーション |
| **Cursor** | GUI、リアルタイム差分、対話的反復 | 実装時の補助（並行利用可） |
| **Codex CLI** | 計画特化、バックグラウンド実行 | 計画フェーズ、並列タスク |
| **Cline** | VSCode統合、ファイル読込・コマンド実行 | 軽量タスク、クイック修正 |

### コンテキスト管理戦略

AI駆動開発でのコスト最適化とトークン効率化。

| 戦略 | 説明 | 実装方法 |
|------|------|----------|
| **セッション分割** | 長いスレッドを避け、こまめに新規セッション | フェーズ毎にセッション切替 |
| **ファイルネスト** | 関連ファイルをグループ化してツリー圧縮 | VSCode設定で自動適用 |
| **memory.md活用** | セッション間の継続性を外部ファイルで担保 | `.claude/memory/`に状態保存 |
| **@参照の活用** | 必要なファイルのみ明示的にコンテキスト追加 | `@src/auth.ts`形式で参照 |
| **Git Worktree** | 並列セッションでのコード分離 | タスク毎にworktree作成 |

### コンテキスト汚染と記憶喪失対策

長時間セッションでコンテキストが汚染されると、重要な決定事項を「忘れる」。これを検知・回復する仕組み。

#### 汚染の原因と症状

| 原因 | 症状 | 検知方法 |
|------|------|----------|
| **トークン制限** | 初期の要件・決定が切り捨て | 要件への言及が消える |
| **無関係情報蓄積** | 関連性の低い情報でコンテキスト占有 | タスク外の話題増加 |
| **長時間セッション** | 初期決定と矛盾する行動 | 同じ質問を繰り返す |
| **並列タスク混入** | 別タスクの情報が混ざる | 別プロジェクトの用語出現 |

#### 記憶喪失の兆候チェックリスト

```yaml
# 自動検知トリガー
memory_loss_indicators:
  # 同じ質問を再度している
  - pattern: "repeated_question"
    detection: "過去10ターン内に同一質問のembedding類似度 > 0.9"
    severity: warning

  # 以前決定したことを無視
  - pattern: "decision_ignored"
    detection: "決定済み事項（decisions.md）と矛盾する提案"
    severity: critical

  # 要件との不整合
  - pattern: "requirement_drift"
    detection: "要件引継書にない機能の実装提案"
    severity: critical

  # 同じミスの繰り返し
  - pattern: "repeated_mistake"
    detection: "過去に指摘された問題と同一パターンの再発"
    severity: warning

  # 設計方針の逸脱
  - pattern: "design_deviation"
    detection: "設計書の方針と異なるアーキテクチャ提案"
    severity: major
```

#### 永続化すべき重要情報

```
.claude/memory/
├── decisions.md          # 決定事項（変更禁止/条件付き変更可/AI判断/決定ログ）
├── decisions.yaml        # 決定ログ（YAML形式、機械処理用）
├── constraints.md        # 制約条件（技術的・ビジネス的）
├── glossary.md           # 用語定義（認識齟齬防止）
├── gotchas.md            # プロジェクト固有の注意点
├── rejected-approaches.md # 却下されたアプローチと理由
├── session-handover.md   # セッション引継ぎ情報
├── tech-rationales.yaml  # 技術理由レジストリ（例外承認用）
└── accountability.md     # 責任追跡ログ
```

##### decisions.md の構造

```markdown
# 決定事項レジストリ

## 変更禁止（人間承認済み）

| ID | 決定内容 | 理由 | 決定日 | 承認者 |
|----|---------|------|--------|--------|
| D-001 | JWT認証を採用 | マイクロサービス対応 | 2026-02-01 | @tenni |
| D-002 | PostgreSQL使用 | チーム経験値 | 2026-02-01 | @tenni |
| D-003 | モノレポ構成 | デプロイ簡素化 | 2026-02-02 | @tenni |

## 条件付き変更可

| ID | 決定内容 | 変更条件 | 決定日 |
|----|---------|----------|--------|
| D-010 | ORMはPrisma | パフォーマンス問題発生時は再検討可 | 2026-02-03 |

## AI判断（人間未承認）

| ID | 決定内容 | 根拠 | 要承認 |
|----|---------|------|--------|
| D-100 | バリデーションはZod | 型安全性 | 次回レビュー時 |

## 決定ログ（エージェント追記可）

**注意: 本セクションはエージェントが追記可能。decision_log_policy に準拠。**

| ID | Status | Severity | Decision | Rationale_IDs | Timestamp | Author | Review_Deadline | Expiry_Action |
|----|--------|----------|----------|---------------|-----------|--------|-----------------|---------------|
| DL-001 | confirmed | medium | APIレスポンス形式をJSON統一 | R-001 | 2026-02-06T10:00Z | agent:task-owner | 2026-02-09 | auto_confirm |
| DL-002 | provisional | low | ログフォーマットをJSON化 | R-002 | 2026-02-06T11:00Z | agent:task-owner | 2026-03-06 | auto_archive |
```

#### 回帰チェックポイント

```python
class ContextRegressionChecker:
    """コンテキスト汚染による記憶喪失を検知・回復"""

    def __init__(self, memory_dir):
        self.memory_dir = memory_dir
        self.decisions = self._load_decisions()
        self.constraints = self._load_constraints()
        self.turn_count = 0

    def check_before_action(self, proposed_action):
        """アクション実行前に回帰チェック"""
        violations = []

        # 1. 決定事項との整合性
        for decision in self.decisions:
            if self._conflicts_with(proposed_action, decision):
                violations.append({
                    'type': 'decision_conflict',
                    'decision_id': decision.id,
                    'detail': f"決定事項 {decision.id} と矛盾: {decision.content}",
                    'severity': 'critical',
                })

        # 2. 制約条件チェック
        for constraint in self.constraints:
            if self._violates(proposed_action, constraint):
                violations.append({
                    'type': 'constraint_violation',
                    'constraint': constraint.name,
                    'detail': f"制約違反: {constraint.description}",
                    'severity': 'critical',
                })

        # 3. 却下済みアプローチの再提案チェック
        rejected = self._load_rejected_approaches()
        for approach in rejected:
            if self._similar_to(proposed_action, approach):
                violations.append({
                    'type': 'rejected_approach_reused',
                    'approach': approach.name,
                    'detail': f"以前却下: {approach.reason}",
                    'severity': 'warning',
                })

        return violations

    def periodic_reminder(self):
        """定期的に重要情報をリマインド（10ターン毎）"""
        self.turn_count += 1
        if self.turn_count % 10 == 0:
            return self._generate_reminder()
        return None

    def _generate_reminder(self):
        """コンテキストリマインダー生成"""
        return f"""
## 🔄 コンテキストリマインダー（{self.turn_count}ターン経過）

### 変更禁止の決定事項
{self._format_critical_decisions()}

### 現在の制約
{self._format_constraints()}

### 直近の重要指摘
{self._format_recent_feedback()}

---
※ 上記に反する提案は禁止。疑問があれば確認してから行動。
"""

    def on_session_end(self):
        """セッション終了時に引継ぎ情報を保存"""
        handover = {
            'session_summary': self._summarize_session(),
            'decisions_made': self._get_session_decisions(),
            'open_questions': self._get_open_questions(),
            'next_actions': self._get_pending_actions(),
            'warnings': self._get_active_warnings(),
        }
        self._save_handover(handover)
```

#### 自動リマインダー注入

```yaml
# セッション中に自動注入されるリマインダー
reminder_triggers:
  # ターン数ベース
  - trigger: "every_10_turns"
    content: "decisions.md + constraints.md の要約"
    format: "## 🔄 コンテキストリマインダー"

  # 時間ベース
  - trigger: "every_30_minutes"
    content: "直近の重要決定 + 残タスク"
    format: "## ⏰ 定期チェックポイント"

  # イベントベース
  - trigger: "before_implementation_start"
    content: "要件引継書の該当セクション + 設計書の制約"
    format: "## 📋 実装開始前確認"

  - trigger: "after_error_3_consecutive"
    content: "関連する過去の解決策 + 制約の再確認"
    format: "## ⚠️ エラー連続発生 - コンテキスト確認"

  - trigger: "context_window_80_percent"
    content: "重要情報のサマリー + コンテキスト圧縮提案"
    format: "## 🔴 コンテキスト上限警告"
```

#### セッション分割時の引継ぎプロトコル

```
旧セッション終了時:
┌─────────────────────────────────────────────────────────────────┐
│ 1. 未完了タスクの記録                                            │
│ 2. 本セッションでの決定事項を decisions.md#決定ログ に追記       │
│ 3. 却下したアプローチを rejected-approaches.md に追記            │
│ 4. session-handover.md 更新                                     │
│    - 現在の状態サマリー                                          │
│    - 次セッションへの申し送り                                    │
│    - 注意すべきポイント                                          │
└─────────────────────────────────────────────────────────────────┘

新セッション開始時:
┌─────────────────────────────────────────────────────────────────┐
│ 1. memory/ 配下の全ファイルをコンテキストにロード                │
│ 2. session-handover.md の申し送りを確認                         │
│ 3. 工程表から現在の状態を確認                                    │
│ 4. 「前セッションからの引継ぎ確認」を出力                        │
└─────────────────────────────────────────────────────────────────┘
```

##### session-handover.md の例

```markdown
# セッション引継ぎ情報

## 前セッション終了: 2026-02-06 15:30

### 完了したこと
- T-001 認証モジュール実装 → L4検証パス
- T-002 UI部品作成 → 進行中（70%）

### 未完了・中断
- T-002: ボタンコンポーネントのa11y対応が残り
  - 理由: ARIA属性の仕様確認が必要だった
  - 次アクション: WAI-ARIAドキュメント確認後に再開

### 本セッションでの決定
- D-105: ボタンはRadix UIベースで統一（一貫性のため）

### 注意事項
- ⚠️ auth.tsの56行目にTODOあり（リフレッシュトークン有効期限）
- ⚠️ E2Eテストが1件Flaky（CI再実行で解決中）

### 次セッションへの申し送り
1. T-002のa11y対応を完了させる
2. T-003に着手する前にD-003（モノレポ構成）を再確認
3. Flakyテストの根本原因を調査する
```

#### 回帰テスト（決定事項の再確認）

```python
def run_decision_regression_test(decisions_file, current_context):
    """決定事項が現在のコンテキストで有効か確認"""

    results = []
    decisions = load_decisions(decisions_file)

    for decision in decisions:
        # 決定事項がコンテキストに存在するか
        if not mentioned_in_context(decision, current_context):
            results.append({
                'decision': decision.id,
                'status': 'FORGOTTEN',
                'action': 'リマインダー注入',
            })

        # 決定事項と矛盾する記述がないか
        contradictions = find_contradictions(decision, current_context)
        if contradictions:
            results.append({
                'decision': decision.id,
                'status': 'CONTRADICTED',
                'contradictions': contradictions,
                'action': '即座に停止・確認',
            })

    return results

# 実行タイミング
# - 実装開始前（必須）
# - 10ターン毎（定期）
# - エラー3回連続後（異常検知時）
```

### Web検索・調査方針

エージェントが情報収集を行う際のガイドライン。

#### 検索の優先順位

```
1. 公式ドキュメント（最優先）
   └ docs.*.com, *.dev/docs, README.md

2. 技術ブログ（実装例）
   └ Zenn, Qiita, Dev.to, Medium（技術カテゴリ）

3. GitHub（実際のコード）
   └ Issues, Discussions, ソースコード

4. Stack Overflow（トラブルシューティング）
   └ 高評価回答を優先

5. 公式以外のチュートリアル
   └ 複数ソースで検証
```

#### 検索クエリの構築

| 目的 | クエリパターン | 例 |
|------|--------------|-----|
| 最新情報 | `{技術} 2026 best practices` | `Next.js 2026 best practices` |
| 実装例 | `{技術} {機能} example code` | `FastAPI JWT authentication example` |
| 比較 | `{A} vs {B} comparison` | `Prisma vs Drizzle comparison` |
| トラブル | `{エラーメッセージ} solution` | `ECONNREFUSED solution` |
| 日本語 | `{技術} {機能} Zenn Qiita` | `React Server Components Zenn Qiita` |

#### 情報の検証ルール

| ルール | 説明 |
|--------|------|
| **鮮度確認** | 記事の日付を確認。2年以上前は要注意 |
| **複数ソース** | 重要な情報は2-3ソースで確認 |
| **公式優先** | 矛盾時は公式ドキュメントを採用 |
| **バージョン確認** | 使用バージョンと記事のバージョンを照合 |
| **コード検証** | コピペせず、プロジェクトに適合させる |

#### 調査結果の記録

調査で得た情報は `docs/research/` に記録し、後続タスクで参照可能にする。

```markdown
# docs/research/auth-strategy.md

## 調査日: 2026-02-06
## 調査者: Codex

### 調査目的
認証方式の選定（JWT vs Session）

### 参照ソース
1. [Auth0 Docs](https://auth0.com/docs) - JWT best practices
2. [Zenn記事](https://zenn.dev/xxx) - 実装例
3. [GitHub Issue](https://github.com/xxx) - 既知の問題

### 結論
JWT採用。理由: マイクロサービス対応、ステートレス

### 注意点
- リフレッシュトークンの実装必須
- トークン有効期限は15分推奨
```

### マルチエージェント協調

Helixでの複数エージェント並列実行パターン。

| パターン | 説明 | 使用場面 |
|----------|------|----------|
| **Git Worktree分離** | タスク毎にworktree作成、独立実行 | 並列機能開発 |
| **Plan Mode → 実装** | 設計を固めてから実装エージェント起動 | 複雑な機能 |
| **検証並列化** | L2/L3/L4検証を並列実行 | 検証フェーズ高速化 |
| **Headless実行** | `-p`オプションでバックグラウンド実行 | CI/CD統合 |

---

## コンセプト

OSI参照モデルのように各レイヤーが独立した対比サイクルを持ち、すべてのレイヤーでループ検証が回り続ける構造。上位レイヤーの基準を下位が参照し、各レイヤーは自レイヤーの左右対比で完結する。オーケストレーションは工程表に焼き込み、都度判断を排除する。手戻り回数を計画精度の評価軸とする。

**Sonnet 5.0対応・エージェント駆動・ユーザー負担は企画のみ**


## Helix参照モデル構造

```
L1  要件定義 ←──────────────────────→ 受入検証
L2    設計書 ←────────────────────→ 設計整合性検証
L2.5    API契約 ←──────────────→ API整合性検証 ★
L3       依存関係 ←──────────→ 依存関係検証
L4         工程表+水準 ←────→ テスト検証 ★拡張
L5           デプロイ計画 ←→ 本番検証 ★新設
                  実装（底）
```


## 処理フロー

### 全体フロー：企画書から本番リリースまで

```
┌─────────────────────────────────────────────────────────────────┐
│ 【人間】企画書提出（以降、人間は指摘があれば指摘。なければ待機） │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【L1】要件定義フェーズ                                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Opus: 企画書を構造化 → Haiku: 要件引継書に転記              │ │
│ │ Codex: 要件引継書の完全性チェック → 不備あれば Opus へ差し戻し│ │
│ └─────────────────────────────────────────────────────────────┘ │
│ 出力: requirements-handover.md                                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【L2】設計フェーズ                                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Codex: 要件引継書 → 設計書作成（Frontend/Backend/DB）       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ 出力: design/frontend.md, backend.md, database.md                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【L2.5】API契約定義フェーズ ★                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Codex: 設計書 → API契約書生成（OpenAPI仕様）                │ │
│ │ TypeScript型 ↔ OpenAPI ↔ DBスキーマの整合性を事前検証       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ 出力: api-contract.yaml                                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【L3】依存関係定義フェーズ                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Codex: 設計書 → 依存関係マップ生成 → 実装順序決定           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ 出力: dependency-map.md                                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【L4】工程表・テスト計画フェーズ                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Codex: 依存関係マップ → 工程表作成（オーケストレーション込み）│ │
│ │ Codex: テスト計画作成（Lv4.1〜4.4）                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ 出力: schedule.md, test-plan.md, hr-sheet.md                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【底】実装フェーズ                                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Orchestrator(Sonnet): 工程表を読んで配送                    │ │
│ │ Codex 5.3: 設計→実装を一気通貫で実行                       │ │
│ │ Sonnet 4.5: テストコード作成・実行                          │ │
│ │ Codex 5.2: 軽微なエラー修正（エラー多→5.3にエスカレーション）│ │
│ │ Haiku 4.5: 調査・下調べ                                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ 出力: 実装コード + テストコード                                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【検証フェーズ】各レイヤーで並行検証                              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ L2検証: 設計書 ↔ 実装コード整合性（Codex）                  │ │
│ │ L2.5検証: API契約 ↔ 実装（Frontend/Backend/DB）整合性（Codex）│ │
│ │ L3検証: 依存関係マップ ↔ 実装の接続状態（Codex）            │ │
│ │ L4検証: テスト実行（Sonnet 4.5）                              │ │
│ │   Lv4.1: 単体テスト                                          │ │
│ │   Lv4.2: 統合テスト                                          │ │
│ │   Lv4.3: API契約テスト                                       │ │
│ │   Lv4.4: E2Eテスト                                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ループ: 不合格 → 該当レイヤー内で修正 → 再検証                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │ 全テスト通過
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【L5】デプロイ・最終検証フェーズ ★                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Codex: デプロイ計画作成                                      │ │
│ │ Sonnet: ビルド実行 + セキュリティスキャン + パフォーマンステスト│ │
│ │ Codex: Lv5判定（設計書を上回るか）                           │ │
│ │   - パフォーマンス: 設計書の120%以上                         │ │
│ │   - セキュリティ: Critical/High脆弱性0件                     │ │
│ │   - 保守性・拡張性・ドキュメント: 定性評価                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ループ: 不合格 → 最適化 → 再検証                                │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Lv5達成
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【L1】受入検証フェーズ                                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Codex: 要件引継書 ↔ 最終成果物の突合                        │ │
│ │ 全要件項目の充足率を数値判定                                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ループ: 不合格 → 該当レイヤーへ差し戻し → 修正 → 再検証          │
└─────────────────────┬───────────────────────────────────────────┘
                      │ 受入検証合格
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【人間】成果物確認（指摘があれば指摘、なければ本番リリース承認）  │
└─────────────────────────────────────────────────────────────────┘
```

### 検証ループの詳細

各レイヤーは独立した検証ループを持ち、不合格時は自レイヤー内で修正を繰り返す：

```
┌──────────────────────────────────────────────────────────┐
│ レイヤー内検証ループ（例: L2.5 API整合性検証）           │
│                                                          │
│  設計書 → API契約書作成 → 実装突合 → 一致率判定         │
│     ↑                                        │           │
│     │                                        ↓           │
│     │                                     100%?          │
│     │                                        │           │
│     │                           No ←────────┘           │
│     └─ 不一致箇所明示 ← 修正指示                         │
│                                                          │
│  Yes → 次レイヤーへ                                      │
└──────────────────────────────────────────────────────────┘
```

### エスカレーションフロー

レイヤー内ループで解決不能な場合、上位レイヤーへエスカレーション：

```
L5 不合格 → L5内ループ（5回）→ 解決不能 → L4へエスカレーション
L4 不合格 → L4内ループ（5回）→ 解決不能 → L3へエスカレーション
L3 不合格 → L3内ループ（5回）→ 解決不能 → L2へエスカレーション
L2 不合格 → L2内ループ（5回）→ 解決不能 → L1へエスカレーション
L1 不合格 → L1内ループ（5回）→ 解決不能 → 人間へエスカレーション
```

**重要:** MVP判断、スコープ縮小は人間のみが行う。エージェントは自律的に品質向上を目指す。

### 人間へのエスカレーション形式

人間は基本的に「指摘」以外はしない。エージェントが報告し、人間は問題があれば指摘で返す。

```
┌─────────────────────────────────────────────────────────────────┐
│ 【エージェント → 人間】報告形式                                  │
├─────────────────────────────────────────────────────────────────┤
│ ■ 状況: [解決不能な問題の概要]                                   │
│ ■ 試行済み: [これまでに試した解決策]                             │
│ ■ 選択肢:                                                        │
│   A) [選択肢A] - [トレードオフ]                                  │
│   B) [選択肢B] - [トレードオフ]                                  │
│   C) スコープ縮小（MVP化）                                        │
│ ■ 推奨: [エージェントの推奨選択肢]                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【人間 → エージェント】応答形式（指摘のみ）                      │
├─────────────────────────────────────────────────────────────────┤
│ パターン1: 「Bで」（選択肢を指定）                               │
│ パターン2: 「○○を優先して」（方針を指摘）                       │
│ パターン3: 「MVPでいい」（スコープ縮小承認）                     │
│ パターン4: （無言）→ 推奨選択肢で続行                           │
└─────────────────────────────────────────────────────────────────┘
```

**人間の応答ルール:**
- 短い指摘のみ（詳細な指示は出さない）
- 選択肢から選ぶか、方針を一言で伝える
- 無言（一定時間応答なし）の場合、エージェントは推奨選択肢で続行
  - **ただし、Critical条件に該当する場合は無言でも続行禁止（下記参照）**

### 人間エスカレーション条件（明示化）

以下の条件に該当する場合、エージェントは**必ず**人間にエスカレーションする。自律判断で進行することは禁止。

**重要: Critical条件に該当するエスカレーションは、人間が無応答でも「推奨選択肢で続行」してはならない。明示的な承認を得るまで待機する。**

#### 即時エスカレーション（Critical）

| 条件 | 理由 | エスカレーション形式 |
|------|------|---------------------|
| **本番環境への影響** | データ損失・サービス停止リスク | 実行前に承認を得る |
| **外部API連携の新規追加** | コスト・契約・セキュリティ影響 | API選定の承認を得る |
| **認証・認可ロジックの変更** | セキュリティリスク | 設計承認を得る |
| **課金・決済関連** | 金銭的リスク | 実装前に承認を得る |
| **個人情報の取り扱い変更** | コンプライアンスリスク | 方針決定を仰ぐ |
| **ライセンス・著作権関連** | 法的リスク | 判断を仰ぐ |

#### 判断エスカレーション（Decision Required）

| 条件 | 理由 | エスカレーション形式 |
|------|------|---------------------|
| **MVPスコープの縮小** | ビジネス判断 | 選択肢を提示し承認を得る |
| **期限延長の必要性** | スケジュール影響 | 状況報告と選択肢提示 |
| **技術選定のトレードオフ** | 複数の妥当な選択肢 | 比較表を提示し判断を仰ぐ |
| **要件の解釈が曖昧** | ビジネス意図が複数解釈可能（※技術詳細の補完は「詳細未記載」として自律判断可） | 解釈案を提示し確認を得る |
| **スコープ曖昧な要件** | 要件かスコープ外か判断不能 | 対応方針を確認（※暗黙の前提・詳細未記載は自律判断可、下記プロトコル参照） |
| **コスト超過の見込み** | 予算影響 | 見積もりと代替案を提示 |

#### 進捗エスカレーション（Progress Alert）

| 条件 | 閾値 | エスカレーション形式 |
|------|------|---------------------|
| **同一タスクでのリトライ回数** | 5回以上 | 状況報告と支援要請 |
| **レイヤー間エスカレーション** | L1まで到達 | 根本原因と選択肢提示 |
| **想定外エラーの継続** | 3回連続 | エラー詳細と調査結果報告 |
| **進捗停滞** | 1タスク2時間以上 | ブロッカー報告 |

#### エスカレーション判定フロー

```python
def should_escalate(context) -> tuple[bool, str]:
    """エスカレーション必要性を判定"""

    # Critical: 即時エスカレーション
    critical_conditions = [
        ('production_impact', context.affects_production),
        ('external_api_new', context.adds_external_api),
        ('auth_change', context.modifies_auth),
        ('payment', context.involves_payment),
        ('pii_change', context.modifies_pii_handling),
        ('license_issue', context.has_license_concern),
    ]
    for name, condition in critical_conditions:
        if condition:
            return True, f"CRITICAL: {name}"

    # Decision Required: 判断エスカレーション
    if context.requires_scope_reduction:
        return True, "DECISION: MVP scope reduction"
    if context.deadline_at_risk:
        return True, "DECISION: deadline extension needed"
    if len(context.viable_tech_options) > 1 and context.significant_tradeoffs:
        return True, "DECISION: tech selection tradeoff"
    if context.ambiguous_requirements:
        return True, "DECISION: ambiguous requirements"
    if context.out_of_scope_candidate:
        return True, "DECISION: potentially out of scope"
    if context.estimated_cost > context.budget * 1.2:
        return True, "DECISION: cost overrun"

    # Progress Alert: 進捗エスカレーション
    if context.retry_count >= 5:
        return True, "PROGRESS: retry limit reached"
    if context.escalation_level == 'L1':
        return True, "PROGRESS: escalated to L1"
    if context.consecutive_errors >= 3:
        return True, "PROGRESS: consecutive errors"
    if context.task_duration_hours >= 2:
        return True, "PROGRESS: task stalled"

    return False, "No escalation needed"
```

#### エスカレーション禁止事項

エージェントは以下の判断を**絶対に**自律的に行ってはならない：

1. **本番デプロイの実行** - 必ず人間の最終承認を得る
2. **データベースのマイグレーション（本番）** - 必ず承認を得る
3. **外部サービスの契約・解約** - 人間が行う
4. **ユーザーへの直接連絡** - 人間が行う
5. **機密情報の外部送信** - 絶対禁止
6. **スコープの拡大** - 要件追加は人間のみ
7. **予算を超える決定** - 承認が必要


## 各レイヤー定義

### L1：要件レイヤー

| 項目 | 内容 |
|------|------|
| 左（計画） | 要件定義：ビジネス要件、機能要件、非機能要件の策定 |
| 右（検証） | 受入検証：最終成果物が要件を満たすか判定 |
| 左担当 | Opus（要件追加・変更時のみスポット召喚） |
| 右担当 | Codex |
| 入力 | 人間からの要求（自然言語） |
| 出力 | 要件引継書（後述） / 受入検証レポート |
| 検証基準 | 全要件項目に対する充足率（数値） |
| 不合格時 | L1内でループ（要件の再定義 or 成果物の差し戻し） |
| 参照関係 | L2以下の全レイヤーはL1を上位基準として参照 |
| 参照ドキュメント（左） | 人間からの要求原文 |
| 参照ドキュメント（右） | `requirements-handover.md` + 最終成果物 |

```
人間の要求 → Opus構造化 → 要件引継書 → ... → 成果物突合 → 充足率判定 → 未達 → 差し戻し → ...→ 合格
```

### L2：設計レイヤー

| 項目 | 内容 |
|------|------|
| 左（計画） | 設計書作成：アーキテクチャ、コンポーネント設計、I/F定義 |
| 右（検証） | 設計整合性検証：実装コードが設計書と一致するか判定 |
| 担当 | Codex（左右両方） |
| 入力 | L1の要件引継書 |
| 出力 | 設計書（セクション分割）/ 設計整合性レポート |
| 検証基準 | 設計書の各項目に対する実装一致率（数値） |
| 不合格時 | L2内でループ（設計修正 or 実装差し戻し） |
| 参照関係 | L1の要件引継書を上位基準として参照。L3以下はL2を参照 |
| 参照ドキュメント（左） | `requirements-handover.md` |
| 参照ドキュメント（右） | `requirements-handover.md` + `design/*.md` + 実装コード |

```
要件引継書 → 設計書作成 → 実装コード突合 → 一致率判定 → 未達 → 乖離箇所明示 → 再実装 → 再突合 → ...→ 合格
```

### L2.5：API整合性レイヤー ★新設

| 項目 | 内容 |
|------|------|
| 左（計画） | API契約定義：Frontend期待 ↔ Backend提供 ↔ DB Schema |
| 右（検証） | API整合性検証：3層間の型・エンドポイント・スキーマ一致判定 |
| 担当 | Codex（左右両方） |
| 入力 | L2の設計書（Frontend設計 + Backend設計 + DB設計） |
| 出力 | API契約書（OpenAPI仕様）/ API整合性レポート |
| 検証基準 | Frontend型 = Backend型 = DB型の一致率（数値）。目標100% |
| 検証項目 | ・TypeScript型定義 ↔ OpenAPI schema<br>・OpenAPI ↔ DBスキーマ（カラム型、NULL制約、デフォルト値等）<br>・エンドポイント存在確認<br>・リクエスト/レスポンス構造一致<br>・バリデーションルール一致 |
| 不合格時 | L2.5内でループ（契約再定義 or 各層の実装修正） |
| 参照関係 | L2の設計書を上位基準として参照。L3以下はL2.5を参照 |
| 参照ドキュメント（左） | `design/frontend.md` + `design/backend.md` + `design/database.md` |
| 参照ドキュメント（右） | `design/*.md` + `api-contract.yaml` (OpenAPI) + 実装コード + DBマイグレーション |

```
設計書 → API契約書作成（OpenAPI） → 実装突合（Frontend/Backend/DB） → 一致率判定 → 未達 → 不一致箇所明示 → 修正 → 再突合 → ...→ 合格
```

**重要:** このレイヤーがないと、Frontend/Backend/DB間のズレが実装後半まで発覚せず、大規模な手戻りが発生する。

#### API契約書のライフサイクル

| フェーズ | タイミング | 担当 | 内容 |
|---------|----------|------|------|
| **初回作成** | L2設計書完成後、実装開始前 | Codex | 設計書からOpenAPI仕様を生成。Frontend/Backend/DBの型定義を統一 |
| **実装中更新** | 実装フェーズ中、設計変更発生時 | Codex | 実装で判明した設計変更をAPI契約書に反映。3層の整合性を維持 |
| **検証時突合** | 各工程完了時 | Codex | 実装コードとAPI契約書を突合。不一致があれば契約書 or 実装を修正 |
| **最終確定** | L5（デプロイフェーズ）前 | Codex | 全実装完了後、API契約書を最終確定。本番環境にデプロイ |

**ポイント**:
- API契約書は「Single Source of Truth」として、実装前に作成し、実装中も継続的に更新
- 設計変更が発生した場合、まずAPI契約書を更新してから実装を変更
- 実装コードよりもAPI契約書を優先（契約駆動開発）

#### データフロー：3層間のデータ変換

API整合性検証の核心は、Frontend/Backend/DB間のデータ変換の整合性を保証すること。

```
┌─────────────────────────────────────────────────────────────────┐
│ リクエストフロー（Frontend → Backend → DB）                      │
└─────────────────────────────────────────────────────────────────┘

Frontend (TypeScript)
  ↓ 型定義: interface User { id: number; name: string; email: string }
  ↓ シリアライズ: JSON.stringify()
  │
  ├─→ HTTP Request (JSON)
  │     { "id": 1, "name": "Alice", "email": "alice@example.com" }
  │
  ↓
Backend API (OpenAPI Schema)
  ↓ バリデーション: OpenAPI schema validation
  ↓ スキーマ定義:
      type: object
      properties:
        id: { type: integer }
        name: { type: string }
        email: { type: string, format: email }
  ↓ デシリアライズ: JSON.parse() → 内部オブジェクト
  ↓ ORM マッピング
  │
  ├─→ SQL Query
  │     INSERT INTO users (id, name, email) VALUES (?, ?, ?)
  │
  ↓
Database (SQL Schema)
  ↓ スキーマ検証: カラム型チェック
      users TABLE:
        id: INTEGER PRIMARY KEY
        name: VARCHAR(255) NOT NULL
        email: VARCHAR(255) NOT NULL UNIQUE
  ↓ データ挿入


┌─────────────────────────────────────────────────────────────────┐
│ レスポンスフロー（DB → Backend → Frontend）                      │
└─────────────────────────────────────────────────────────────────┘

Database
  ↓ SELECT * FROM users WHERE id = ?
  ↓ 結果セット: { id: 1, name: "Alice", email: "alice@example.com" }
  │
  ↓
Backend API
  ↓ ORM → 内部オブジェクト
  ↓ OpenAPI レスポンススキーマ適用
  ↓ シリアライズ: JSON.stringify()
  │
  ├─→ HTTP Response (JSON)
  │     { "id": 1, "name": "Alice", "email": "alice@example.com" }
  │
  ↓
Frontend
  ↓ デシリアライズ: JSON.parse()
  ↓ 型アサーション: as User
  ↓ TypeScript型で利用: user.name
```

#### 内部アルゴリズム：API整合性検証

L2.5で実行される自動検証アルゴリズム。Codexが各層の定義を読み取り、一致率を数値判定する。

##### アルゴリズム1: 型マッピング検証

```python
def verify_type_mapping(frontend_types, openapi_schema, db_schema):
    """
    TypeScript型 ↔ OpenAPI ↔ DBスキーマの型整合性を検証
    """
    mismatches = []

    for entity in frontend_types:
        # 1. Frontend → OpenAPI 検証
        ts_type = frontend_types[entity]
        oa_schema = openapi_schema.get(entity)

        for field, ts_field_type in ts_type.items():
            oa_field_type = oa_schema['properties'].get(field)

            if not type_compatible(ts_field_type, oa_field_type):
                mismatches.append({
                    'layer': 'Frontend-OpenAPI',
                    'entity': entity,
                    'field': field,
                    'ts_type': ts_field_type,
                    'oa_type': oa_field_type
                })

        # 2. OpenAPI → DB 検証
        db_table = db_schema.get(entity)

        for field, oa_field_schema in oa_schema['properties'].items():
            db_column = db_table['columns'].get(field)

            if not schema_compatible(oa_field_schema, db_column):
                mismatches.append({
                    'layer': 'OpenAPI-DB',
                    'entity': entity,
                    'field': field,
                    'oa_schema': oa_field_schema,
                    'db_type': db_column['type']
                })

    # 一致率計算
    total_fields = count_total_fields(frontend_types)
    match_rate = (total_fields - len(mismatches)) / total_fields * 100

    return {
        'match_rate': match_rate,
        'mismatches': mismatches,
        'passed': match_rate == 100.0
    }


def type_compatible(ts_type, oa_type):
    """型互換性チェック"""
    type_mapping = {
        'number': ['integer', 'number'],
        'string': ['string'],
        'boolean': ['boolean'],
        'Date': ['string'],  # format: date-time
        'object': ['object'],
        'array': ['array']
    }

    return oa_type['type'] in type_mapping.get(ts_type, [])


def schema_compatible(oa_schema, db_column):
    """スキーマ互換性チェック"""
    schema_mapping = {
        'integer': ['INTEGER', 'BIGINT', 'INT'],
        'number': ['DECIMAL', 'FLOAT', 'DOUBLE'],
        'string': ['VARCHAR', 'TEXT', 'CHAR'],
        'boolean': ['BOOLEAN', 'TINYINT'],
    }

    oa_type = oa_schema['type']
    db_type = db_column['type'].upper()

    # 型チェック
    if db_type not in schema_mapping.get(oa_type, []):
        return False

    # NULL制約チェック
    oa_required = oa_schema.get('required', False)
    db_nullable = db_column.get('nullable', True)

    if oa_required and db_nullable:
        return False  # OpenAPIで必須なのにDBでNULL許可はNG

    return True
```

##### アルゴリズム2: エンドポイント整合性検証

```python
def verify_endpoint_consistency(frontend_api_calls, openapi_spec, backend_impl):
    """
    Frontend期待エンドポイント ↔ OpenAPI定義 ↔ Backend実装の整合性検証
    """
    mismatches = []

    for api_call in frontend_api_calls:
        # Frontend期待
        expected_method = api_call['method']
        expected_path = api_call['path']
        expected_request = api_call['request_type']
        expected_response = api_call['response_type']

        # OpenAPI定義チェック
        oa_endpoint = openapi_spec['paths'].get(expected_path, {}).get(expected_method.lower())

        if not oa_endpoint:
            mismatches.append({
                'type': 'missing_endpoint',
                'path': expected_path,
                'method': expected_method,
                'layer': 'OpenAPI'
            })
            continue

        # リクエスト型チェック
        oa_request = oa_endpoint.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema')
        if not schema_matches(expected_request, oa_request):
            mismatches.append({
                'type': 'request_mismatch',
                'path': expected_path,
                'expected': expected_request,
                'actual': oa_request
            })

        # レスポンス型チェック
        oa_response = oa_endpoint.get('responses', {}).get('200', {}).get('content', {}).get('application/json', {}).get('schema')
        if not schema_matches(expected_response, oa_response):
            mismatches.append({
                'type': 'response_mismatch',
                'path': expected_path,
                'expected': expected_response,
                'actual': oa_response
            })

        # Backend実装チェック
        backend_route = backend_impl.get_route(expected_method, expected_path)
        if not backend_route:
            mismatches.append({
                'type': 'missing_implementation',
                'path': expected_path,
                'method': expected_method,
                'layer': 'Backend'
            })

    # 一致率計算
    total_endpoints = len(frontend_api_calls)
    match_rate = (total_endpoints - len(mismatches)) / total_endpoints * 100

    return {
        'match_rate': match_rate,
        'mismatches': mismatches,
        'passed': match_rate == 100.0
    }
```

##### アルゴリズム3: バリデーションルール一致検証

```python
def verify_validation_rules(frontend_validation, openapi_validation, db_constraints):
    """
    Frontend/OpenAPI/DBのバリデーションルール整合性検証
    """
    mismatches = []

    for entity, rules in frontend_validation.items():
        for field, fe_rule in rules.items():
            # OpenAPIバリデーション
            oa_rule = openapi_validation.get(entity, {}).get(field, {})

            # DB制約
            db_constraint = db_constraints.get(entity, {}).get(field, {})

            # 必須チェック
            if fe_rule.get('required') != oa_rule.get('required'):
                mismatches.append({
                    'type': 'required_mismatch',
                    'entity': entity,
                    'field': field,
                    'frontend': fe_rule.get('required'),
                    'openapi': oa_rule.get('required')
                })

            # 最小/最大長チェック（文字列）
            if fe_rule.get('minLength') != oa_rule.get('minLength'):
                mismatches.append({
                    'type': 'minLength_mismatch',
                    'entity': entity,
                    'field': field,
                    'frontend': fe_rule.get('minLength'),
                    'openapi': oa_rule.get('minLength')
                })

            # 正規表現パターンチェック
            if fe_rule.get('pattern') != oa_rule.get('pattern'):
                mismatches.append({
                    'type': 'pattern_mismatch',
                    'entity': entity,
                    'field': field,
                    'frontend': fe_rule.get('pattern'),
                    'openapi': oa_rule.get('pattern')
                })

            # UNIQUE制約チェック
            if oa_rule.get('unique') != db_constraint.get('unique'):
                mismatches.append({
                    'type': 'unique_mismatch',
                    'entity': entity,
                    'field': field,
                    'openapi': oa_rule.get('unique'),
                    'db': db_constraint.get('unique')
                })

    # 一致率計算
    total_rules = count_total_rules(frontend_validation)
    match_rate = (total_rules - len(mismatches)) / total_rules * 100

    return {
        'match_rate': match_rate,
        'mismatches': mismatches,
        'passed': match_rate == 100.0
    }
```

##### 検証結果の出力

```markdown
# API整合性検証レポート（L2.5-report.md）

## 検証サマリー

| 検証項目 | 一致率 | 判定 |
|---------|-------|------|
| 型マッピング | 98.5% | ❌ 不合格 |
| エンドポイント整合性 | 100% | ✅ 合格 |
| バリデーションルール | 95.2% | ❌ 不合格 |
| **総合一致率** | **97.9%** | **❌ 不合格（目標100%）** |

## 不一致箇所詳細

### 型マッピング不一致

1. **User.createdAt**
   - Frontend: `Date`
   - OpenAPI: `string (format: date-time)` ✅
   - DB: `TIMESTAMP` ✅
   - **問題なし**

2. **User.age**
   - Frontend: `number`
   - OpenAPI: `integer` ✅
   - DB: `VARCHAR(10)` ❌ **不一致**
   - **修正要求**: DBスキーマを `INTEGER` に変更

### バリデーションルール不一致

1. **User.email**
   - Frontend: `required: true, pattern: /^[^@]+@[^@]+$/`
   - OpenAPI: `required: true, pattern: /^[^@]+@[^@]+$/` ✅
   - DB: `NOT NULL, UNIQUE` ✅
   - **問題なし**

2. **User.name**
   - Frontend: `required: true, minLength: 2`
   - OpenAPI: `required: true, minLength: 1` ❌ **不一致**
   - DB: `NOT NULL` ✅
   - **修正要求**: OpenAPI minLength を 2 に統一

## ネクストアクション

- [ ] User.age のDBスキーマを VARCHAR(10) → INTEGER に修正
- [ ] User.name の OpenAPI minLength を 1 → 2 に修正
- [ ] 修正後、L2.5検証を再実行
```

---

### L3：コントラクトレイヤー

| 項目 | 内容 |
|------|------|
| 左（計画） | API仕様定義：エンドポイント仕様、エラーコード体系、バージョニング戦略 |
| 右（検証） | コントラクト検証：API仕様の完全性、後方互換性、ドキュメント整合性 |
| 担当 | Codex（左右両方） |
| 入力 | L2.5のAPI契約書（型整合性確認済み） |
| 出力 | API仕様書（OpenAPI完全版）/ コントラクト検証レポート |
| 検証基準 | API仕様カバレッジ≥95%、エラーコード網羅率、後方互換性チェック |
| 不合格時 | L3内でループ（仕様追加 or 実装修正） |
| 参照関係 | L2.5のAPI契約書を上位基準として参照。L4はL3を参照 |
| 参照ドキュメント（左） | `api-contract.yaml` + `design/*.md` |
| 参照ドキュメント（右） | `api-contract.yaml` + 実装コード + エンドポイント一覧 |

```
API契約書（型整合済み） → API仕様定義（エンドポイント・エラーコード・バージョニング） → 仕様カバレッジ判定 → 未達 → 仕様追加 → 再検証 → ...→ 合格
```

### L4：依存関係レイヤー

| 項目 | 内容 |
|------|------|
| 左（計画） | 依存関係マップ生成：コンポーネント間の依存、実装順序決定 |
| 右（検証） | 依存関係検証：依存が正しく解決されているか、未接続がないか判定 |
| 担当 | Codex（左右両方） |
| 入力 | L3のAPI仕様書 + L2の設計書 |
| 出力 | 依存関係マップ / 依存関係検証レポート |
| 検証基準 | 全接続点の解決率（数値）、循環依存の有無、脆弱性0件（Critical/High） |
| 不合格時 | L4内でループ（依存関係の再設計 or 実装の接続修正） |
| 参照関係 | L3のAPI仕様書を上位基準として参照。L5はL4を参照 |
| 参照ドキュメント（左） | `design/*.md` |
| 参照ドキュメント（右） | `design/*.md` + `dependency-map.md` + 実装コード |

```
API仕様書+設計書 → 依存マップ生成 → 実装の接続状態突合 → 解決率判定 → 未達 → 未接続箇所明示 → 修正 → 再突合 → ...→ 合格
```

### L5：テスト検証レイヤー ★拡張

| 項目 | 内容 |
|------|------|
| 左（計画） | テスト計画＋工程表＋設計水準定義＋セキュリティポリシー |
| 右（検証） | テスト実行＋水準判定＋セキュリティスキャン＋パフォーマンステスト |
| 担当 | Codex（計画・検証）+ Sonnet（テスト実装・実行）+ Haiku（軽量テスト） |
| 入力 | L4の依存関係マップ + L2.5のAPI契約書 + L1の非機能要件 |
| 出力 | テスト計画書 / テスト結果レポート + 水準判定レポート + セキュリティスキャン結果 |
| 検証基準 | M4.1〜M4.5すべて通過、カバレッジ≥70%、Critical/High脆弱性0件 |
| テスト階層 | **M4.1: 単体テスト**（関数・メソッドレベル）<br>**M4.2: 統合テスト**（モジュール間連携）<br>**M4.3: API契約テスト**（Frontend ↔ Backend ↔ DB整合性）<br>**M4.4: E2Eテスト**（ユーザーシナリオ全体）<br>**M4.5: パフォーマンステスト**（負荷・レスポンスタイム基準達成） |
| 不合格時 | L5内でループ（テスト修正 or 実装修正 or 最適化） |
| 参照関係 | L4の依存関係マップ + L2.5のAPI契約書を参照 |
| 参照ドキュメント（左） | `dependency-map.md` + `api-contract.yaml` + `requirements-handover.md` |
| 参照ドキュメント（右） | `test-plan.md` + テスト結果 + セキュリティスキャン結果 + パフォーマンステスト結果 |

```
依存マップ+API契約 → テスト計画策定 → テスト実装 → テスト実行（M4.1→4.2→4.3→4.4→4.5） → セキュリティスキャン → 合格率判定 → 未達 → 修正 → 再実行 → ...→ 全テスト通過
```

### L6：運用検証レイヤー ★新設

| 項目 | 内容 |
|------|------|
| 左（計画） | 運用設計：デプロイ計画、可観測性設計、SLO/SLI定義、アラート設計 |
| 右（検証） | 運用検証：デプロイ成功、監視設定、アラート動作、ロールバック手順確認 |
| 担当 | Codex（計画・検証）+ Sonnet（実行） |
| 入力 | L5のテスト結果（全通過）+ L1の非機能要件 |
| 出力 | デプロイ計画書 + 運用手順書 / 運用検証レポート + M5判定 |
| 検証基準 | SLO定義3種以上、アラートルール≥1件、ビルド成功（エラー0件）、ドキュメント完備 |
| 検証項目 | ・ビルド成功（エラー0件、警告0件）<br>・デプロイ手順書・ロールバック手順<br>・SLO/SLI定義と監視設定<br>・アラート設定とエスカレーションパス<br>・本番環境ヘルスチェック<br>・コード品質（保守性・拡張性）<br>・ドキュメント完備<br>・**M5判定: 設計書を上回る**（最適化・保守性・拡張性・セキュリティ強化） |
| 不合格時 | L6内でループ（運用設定修正 or 実装最適化） |
| 参照関係 | L1の非機能要件 + L5のテスト結果を参照 |
| 参照ドキュメント（左） | `requirements-handover.md`（非機能要件）+ `deploy-plan.md` |
| 参照ドキュメント（右） | `deploy-plan.md` + ビルドログ + 監視設定 + アラート設定 + コード品質レポート |

```
テスト全通過 → デプロイ計画+運用設計 → ビルド → 監視・アラート設定 → 本番ヘルスチェック → M5判定（設計書を上回るか） → 未達 → 最適化 → 再検証 → ...→ 合格
```

### 底：実装レイヤー

| 項目 | 内容 |
|------|------|
| 実装担当 | Codex 5.3（設計→実装一気通貫）+ Sonnet（テスト・ドキュメント）+ Haiku（軽量タスク） |
| 入力 | L5テスト計画＋L2設計書＋L4依存関係マップ |
| 出力 | 実装コード・成果物 |
| 制約 | スコープ縮小禁止、MVP判断権は人間のみ、コード省略禁止 |
| 参照ドキュメント | `design/*.md`（該当セクションのみ）+ `dependency-map.md`（接続仕様）+ `requirements-handover.md`（受入条件の確認） |


## セキュリティ・コンプライアンス検証基準

L5検証において、セキュリティとコンプライアンスは**必須合格条件**。

### 脆弱性判定基準

| 重要度 | 判定 | 対応 |
|--------|------|------|
| **Critical** | **0件必須** | 即時修正、修正完了までL5不合格 |
| **High** | **0件必須** | 即時修正、修正完了までL5不合格 |
| **Medium** | 許容可能 | 理由記載必須、次スプリントで対応計画 |
| **Low** | 許容可能 | 記録のみ、対応優先度低 |

**重要: Critical/Highが1件でもあればL5不合格。Medium/Lowは許容理由を明記すれば合格可能。**

### セキュリティ検証チェックリスト

#### 必須項目（全プロジェクト共通）

| カテゴリ | 検証項目 | 判定基準 | 検証ツール |
|---------|---------|---------|-----------|
| **インジェクション** | SQLインジェクション | パラメータ化クエリ使用率100% | Snyk, Semgrep |
| | コマンドインジェクション | ユーザー入力のコマンド直接実行0件 | 静的解析 |
| | XSS | 出力エスケープ率100% | Snyk, ESLint |
| **認証・認可** | パスワード保存 | bcrypt/argon2でハッシュ化 | コードレビュー |
| | セッション管理 | httpOnly + secure + SameSite | 設定確認 |
| | 認可チェック | 全APIエンドポイントに認可あり | 網羅率100% |
| **データ保護** | 機密データ暗号化 | 保存時・通信時の暗号化 | 設定確認 |
| | PII取り扱い | 必要最小限の収集・適切な保管 | コードレビュー |
| | ログ出力 | 機密情報のログ出力なし | 静的解析 |
| **依存関係** | 既知の脆弱性 | High/Critical 0件 | npm audit, Dependabot |
| | ライセンス | 禁止ライセンス使用なし | license-checker |
| **設定** | シークレット管理 | ハードコード0件 | git-secrets, Gitleaks |
| | エラーメッセージ | スタックトレース非公開 | 動作確認 |
| | CORS | 必要最小限のオリジン許可 | 設定確認 |

#### プロジェクト種別ごとの追加項目

| 種別 | 追加検証項目 |
|------|------------|
| **Webアプリ** | CSP設定、CSRF対策、クリックジャッキング対策 |
| **API** | レート制限、入力バリデーション、API認証 |
| **モバイル** | 証明書ピンニング、安全なストレージ、難読化 |
| **金融系** | PCI DSS準拠、監査ログ、二要素認証 |
| **医療系** | HIPAA準拠、アクセス監査、データ最小化 |

### コンプライアンス検証

#### 法規制チェックリスト

| 規制 | 対象 | 検証項目 |
|------|------|---------|
| **GDPR** | EU向けサービス | 同意取得、データ削除機能、DPO連絡先 |
| **個人情報保護法** | 日本国内サービス | 利用目的明示、第三者提供制限 |
| **CCPA** | カリフォルニア居住者向け | オプトアウト機能、データアクセス |
| **特定電子メール法** | メール送信機能 | オプトイン、送信者表示、配信停止 |

#### ライセンスコンプライアンス

```yaml
# 許可ライセンス
allowed_licenses:
  - MIT
  - Apache-2.0
  - BSD-2-Clause
  - BSD-3-Clause
  - ISC
  - CC0-1.0

# 要確認ライセンス（法務確認後に使用可）
review_required:
  - LGPL-2.1
  - LGPL-3.0
  - MPL-2.0

# 禁止ライセンス（使用不可）
prohibited_licenses:
  - GPL-2.0
  - GPL-3.0
  - AGPL-3.0
  - SSPL-1.0
  - BSL-1.1
```

### セキュリティ検証フロー

```
L5検証開始
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. 自動スキャン実行                          │
│    - 依存関係脆弱性スキャン（npm audit）    │
│    - 静的解析（Semgrep, ESLint security）   │
│    - シークレット検出（Gitleaks）           │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 2. 結果判定                                  │
│    - Critical/High: 即座に修正必須          │
│    - Medium: 修正推奨（要判断）             │
│    - Low/Info: 記録のみ                     │
└─────────────────────────────────────────────┘
    │
    ▼ (Critical/High検出時)
┌─────────────────────────────────────────────┐
│ 3. 修正実施                                  │
│    - 依存関係更新                           │
│    - コード修正                             │
│    - 設定変更                               │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 4. 再スキャン                                │
│    - Critical/High 0件を確認               │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 5. コンプライアンスチェック                  │
│    - ライセンス確認                         │
│    - 法規制準拠確認                         │
└─────────────────────────────────────────────┘
    │
    ▼
    L5セキュリティ検証完了
```

### セキュリティレポート形式

```markdown
# セキュリティ検証レポート

## サマリー
- **検証日時**: YYYY-MM-DD HH:MM
- **プロジェクト**: [プロジェクト名]
- **検証結果**: PASS / FAIL

## 脆弱性スキャン結果

| 重要度 | 件数 | 対応状況 |
|--------|------|---------|
| Critical | 0 | - |
| High | 0 | - |
| Medium | 2 | 許容（理由記載） |
| Low | 5 | 記録のみ |

## 検証項目チェック

| 項目 | 結果 | 備考 |
|------|------|------|
| SQLインジェクション対策 | ✅ | ORM使用 |
| XSS対策 | ✅ | React自動エスケープ |
| 認証・認可 | ✅ | JWT + RBAC |
| シークレット管理 | ✅ | 環境変数使用 |
| 依存関係 | ✅ | Critical/High 0件 |
| ライセンス | ✅ | 禁止ライセンスなし |

## 残存リスク
- [Medium脆弱性の詳細と許容理由]
- [今後の対応予定]
```


## 運用フェーズ（L6：監視・インシデント対応）

L5（デプロイ）完了後の運用フェーズ。本番稼働中のシステムを監視し、インシデント発生時に対応する。

### L6の位置づけ

```
L1 → L2 → L2.5 → L3 → L4 → L5 → 【L6: 運用】
                                      │
                                      ├─ 監視
                                      ├─ インシデント対応
                                      ├─ 継続的改善
                                      └─ フィードバックループ → L1
```

### 監視項目

**注意: SLO閾値の詳細定義は「運用ポリシー > degradation_to_slo_map」を参照。本セクションはアラート設定の概要。**

#### システム監視

| 監視項目 | メトリクス | 閾値 | アラート | 劣化レベル参照 |
|---------|-----------|------|---------|---------------|
| **可用性** | Uptime | 99.0%未満 | Warning, 98.0%未満 Critical | medium/high/critical |
| **レスポンス** | P95 Latency | 800ms以上 Warning, 1500ms以上 Critical | medium/high/critical |
| **エラー率** | Error Rate | 2%以上 Warning, 5%以上 Critical | medium/high/critical |
| **リソース** | CPU/Memory | 80%以上 Warning, 95%以上 Critical | - |

#### ビジネス監視

| 監視項目 | メトリクス | 異常判定 |
|---------|-----------|---------|
| **トランザクション** | 成功率 | 通常の50%未満 |
| **ユーザーアクティビティ** | DAU/MAU | 前週比30%減 |
| **コンバージョン** | CVR | 前週比20%減 |

#### AIエージェント固有監視

| 監視項目 | メトリクス | 閾値 |
|---------|-----------|------|
| **タスク成功率** | Success Rate | 95%以下 |
| **リトライ率** | Retry Rate | 10%以上 |
| **コンテキスト使用率** | Context Usage | 90%以上 |
| **API コスト** | Daily Cost | 予算の120%以上 |

### インシデント対応フロー

```
アラート検知
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. 重要度判定                                │
│    - Critical: 即時対応（サービス停止）     │
│    - High: 30分以内（機能障害）             │
│    - Medium: 4時間以内（パフォーマンス劣化）│
│    - Low: 24時間以内（軽微な問題）          │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 2. 初動対応                                  │
│    - 影響範囲の特定                         │
│    - 暫定対応（ロールバック、スケールアウト）│
│    - ステークホルダーへの通知               │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 3. 原因調査                                  │
│    - ログ分析                               │
│    - メトリクス相関分析                     │
│    - 変更履歴確認                           │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 4. 恒久対応                                  │
│    - 根本原因の修正                         │
│    - テスト・検証                           │
│    - デプロイ（L5経由）                     │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 5. 振り返り（ポストモーテム）               │
│    - タイムライン整理                       │
│    - 教訓の抽出                             │
│    - 再発防止策の策定                       │
│    - ナレッジ蓄積（スキル化候補）           │
└─────────────────────────────────────────────┘
```

### インシデント重要度定義

| 重要度 | 影響 | 対応SLA | エスカレーション |
|--------|------|---------|-----------------|
| **Critical** | サービス全停止、データ損失リスク | 即時 | 即座に人間へ |
| **High** | 主要機能が使用不可 | 30分 | 15分で進展なければエスカレーション |
| **Medium** | 一部機能に障害、代替手段あり | 4時間 | 2時間で進展なければエスカレーション |
| **Low** | 軽微な問題、ユーザー影響小 | 24時間 | 通常対応 |

### 自動対応（Self-Healing）

AIエージェントが自動で対応可能なインシデント。

**注意: 以下の自動対応は「本番影響は実行前承認」の例外。理由:**
- **復旧行為**であり、新規デプロイではない
- **既知の正常状態**への復元（前回デプロイ時点）
- **デプロイ計画時に事前承認済み**（ロールバック手順は計画の一部）

| インシデント種別 | 自動対応 | 条件 | 承認ステータス |
|-----------------|---------|------|---------------|
| **メモリ不足** | ガベージコレクション、キャッシュクリア | 閾値超過 | 暗黙承認（非破壊） |
| **高負荷** | スケールアウト要求 | CPU/Memory 80%超 | 暗黙承認（追加リソース） |
| **API障害** | リトライ、フォールバック | 3回連続失敗 | 暗黙承認（代替経路） |
| **証明書期限切れ** | 自動更新（Let's Encrypt） | 30日前 | 暗黙承認（更新のみ） |
| **ディスク使用率** | ログローテーション、不要ファイル削除 | 80%超 | 暗黙承認（クリーンアップ） |

### ロールバック判断基準

**注意: 自動ロールバックはデプロイ計画で事前承認済み。エスカレーション条件「本番影響は実行前承認」の例外として扱う。ただし、実行後は即座に人間へ通知必須。**

| 条件 | 判断 | 実行者 | 通知 |
|------|------|--------|------|
| **エラー率 5%超過** | 即時ロールバック | 自動 | 実行後即通知 |
| **レスポンス 2倍以上劣化** | 即時ロールバック | 自動 | 実行後即通知 |
| **Critical アラート 3件以上** | ロールバック検討 | エージェント判断 | 判断前に通知 |
| **ユーザー報告 10件以上** | 人間判断でロールバック | 人間承認 | 承認待ち |

### ポストモーテムテンプレート

```markdown
# インシデントレポート: [インシデントID]

## 概要
- **発生日時**: YYYY-MM-DD HH:MM
- **検知日時**: YYYY-MM-DD HH:MM
- **解決日時**: YYYY-MM-DD HH:MM
- **影響範囲**: [影響を受けたユーザー数、機能]
- **重要度**: Critical / High / Medium / Low

## タイムライン
| 時刻 | イベント |
|------|---------|
| HH:MM | [最初の異常検知] |
| HH:MM | [初動対応開始] |
| HH:MM | [原因特定] |
| HH:MM | [修正デプロイ] |
| HH:MM | [サービス復旧確認] |

## 根本原因
[技術的な原因の詳細]

## 影響
- ユーザー影響: [具体的な影響内容]
- ビジネス影響: [売上、評判等への影響]

## 対応内容
### 暫定対応
[実施した暫定対応]

### 恒久対応
[実施した、または予定している恒久対応]

## 教訓
### うまくいったこと
- [良かった点]

### 改善すべきこと
- [課題点]

## 再発防止策
| 対策 | 担当 | 期限 | ステータス |
|------|------|------|-----------|
| [対策1] | - | - | 未着手 |
| [対策2] | - | - | 未着手 |

## ナレッジ化
- [ ] スキル化候補として登録
- [ ] 監視項目の追加
- [ ] ランブックの更新
```

### 継続的改善ループ

```
L6（運用）で収集した情報
    │
    ├─→ パフォーマンスデータ → L5へフィードバック（最適化）
    │
    ├─→ エラーパターン → スキル化（ナレッジ蓄積）
    │
    ├─→ ユーザーフィードバック → L1へフィードバック（要件追加）
    │
    └─→ セキュリティイベント → セキュリティスキル更新
```


## 要件引継書（Opus → Codex）

Opusが要件定義後にCodexへ引き継ぐための必須ドキュメント。Opusが端折ることを構造的に防止する。

### テンプレート

```markdown
# 要件引継書

## 1. 背景・目的
- なぜ作るのか（ビジネス上の理由）
- 何を解決するのか（課題）
- 成功の定義（定量的に）

## 2. 機能要件一覧
| ID | 機能名 | 概要 | 優先度 | 受入条件 |
|----|--------|------|--------|----------|
| F-001 | | | | |
| F-002 | | | | |

※ 各機能に受入条件を必ず記載。受入条件のない機能は不完全とみなす。

## 3. 非機能要件
| ID | カテゴリ | 要件 | 基準値 |
|----|----------|------|--------|
| NF-001 | パフォーマンス | | |
| NF-002 | セキュリティ | | |

## 4. スコープ外の明示
- やらないことを明記（Codexが勝手に拡張しないための境界線）

## 5. 制約条件
- 技術制約、予算制約、期限制約

## 6. 用語定義
- プロジェクト固有の用語（Codexが解釈を間違えないための辞書）

## 7. 人間の指摘を待つ未決事項
エージェントが自律的に判断できない事項のみリストアップ。人間が指摘で方針を示す。
指摘がなければエージェントは推奨案で続行。

| ID | 内容 | 推奨案 | 影響範囲 | 判断期限 |
|----|------|--------|----------|----------|
| TBD-001 | | | | |
```

### 引継書のルール
- 全セクション必須。空欄不可（未確定なら「未決：理由」と明記）
- 機能要件は受入条件がないと不完全。Codexはこれを検証基準として使用
- スコープ外の明示が漏れると、Codexが独自解釈で拡張するリスクあり
- Codexは引継書を受け取った時点で不備チェックを行い、不備があればOpusに差し戻す

### 要件未定義時のプロトコル

実装中に要件引継書に記載のない状況が発生した場合の対応プロトコル。

**注意: このプロトコルは「判断エスカレーション」の「スコープ曖昧な要件」を詳細化したもの。分類によって自律判断可/エスカレーション必須を判定する。**

#### 未定義要件の分類

**「詳細未記載」と「要件の解釈が曖昧」の違い:**
- **詳細未記載**: 技術的な実装詳細が不明（例: 日付フォーマット、エラーメッセージ文言、UIの色）→ 自律判断可
- **要件の解釈が曖昧**: ビジネス上の意図が複数解釈可能（例:「ユーザーフレンドリー」の定義、優先順位）→ エスカレーション必須

| 分類 | 定義 | 例 | 対応方針 |
|------|------|-----|---------|
| **暗黙の前提** | 業界標準・常識的期待値 | HTTPステータスコード、RESTful命名規則 | 標準的実装を採用し、記録のみ |
| **詳細未記載** | 要件は存在するが技術詳細が不明 | 日付フォーマット、ページネーション件数 | 設計判断で補完し、記録 |
| **スコープ曖昧** | 要件かスコープ外か不明 | 「将来的に対応」と書かれた機能 | 人間にエスカレーション |
| **矛盾・競合** | 複数要件が矛盾 | 「シンプルなUI」と「全機能をトップに配置」 | 人間にエスカレーション |
| **完全欠落** | 必要な要件が全く存在しない | エラー処理方針の記載なし | 人間にエスカレーション |

#### 対応フロー

```
要件不明確を検出
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. 分類判定                                  │
│    - 暗黙の前提か？ → 業界標準を調査        │
│    - 詳細未記載か？ → 設計文書から推測      │
│    - 上記以外 → エスカレーション            │
└─────────────────────────────────────────────┘
    │
    ▼ (暗黙の前提 or 詳細未記載)
┌─────────────────────────────────────────────┐
│ 2. 自律判断の実行                            │
│    - 標準的・保守的な選択を採用             │
│    - 判断根拠を記録                          │
│    - 後から変更可能な設計を選択             │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 3. 判断記録の作成                            │
│    decisions.md#AI判断 に以下を追記:        │
│    - 検出箇所                                │
│    - 判断内容                                │
│    - 採用理由                                │
│    - 代替案                                  │
│    - 変更時の影響範囲                        │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 4. 次回報告時に通知                          │
│    「以下の判断を自律的に行いました」        │
│    人間は問題あれば指摘、なければ続行       │
└─────────────────────────────────────────────┘
```

#### 自律判断の原則

| 原則 | 説明 |
|------|------|
| **保守的選択** | 冒険的な選択より安全な選択を優先 |
| **可逆性重視** | 後から変更しやすい設計を選択 |
| **最小実装** | 必要最小限の実装に留める（過剰実装禁止） |
| **標準準拠** | 独自方式より業界標準を採用 |
| **記録必須** | 全ての自律判断を記録 |

#### 判断記録テンプレート（decisions.md#AI判断 セクションに追記）

**注意: このテンプレートは decisions.md の「AI判断（人間未承認）」セクションに追記する。更新権限は decision_log_policy.scope.other_sections の agent_append_only に準拠。**

```markdown
## AI判断（人間未承認）

| ID | 決定内容 | 根拠 | 要承認 |
|----|---------|------|--------|
| D-[番号] | [採用した実装方針] | [理由要約] | [次回レビュー時] |

### D-[番号] 詳細

**検出箇所**: [ファイル:行 or 機能名]

**状況**:
[要件引継書に記載がなかった内容]

**判断**:
[採用した実装方針]

**根拠**:
- [理由1]
- [理由2]

**代替案**:
- [代替案A]: [不採用理由]
- [代替案B]: [不採用理由]

**変更時の影響**:
- 影響範囲: [ファイル/モジュール]
- 変更コスト: [低/中/高]
- 要確認: [特に確認すべき点]
```

#### エスカレーション判定

```python
def handle_undefined_requirement(situation) -> str:
    """未定義要件の対応方針を判定"""

    # 分類判定
    if is_industry_standard(situation):
        # 暗黙の前提：標準実装を採用
        decision = adopt_standard_practice(situation)
        log_decision(situation, decision, "industry_standard")
        return "PROCEED"

    if can_infer_from_design(situation):
        # 詳細未記載：設計から推測
        decision = infer_from_context(situation)
        if is_conservative(decision) and is_reversible(decision):
            log_decision(situation, decision, "inferred")
            return "PROCEED"

    # 以下はエスカレーション
    if is_scope_ambiguous(situation):
        return escalate("DECISION: scope clarification needed", situation)

    if has_conflicting_requirements(situation):
        return escalate("DECISION: requirement conflict", situation)

    if is_completely_missing(situation):
        return escalate("DECISION: missing requirement", situation)

    # デフォルト：エスカレーション
    return escalate("DECISION: cannot determine autonomously", situation)
```


## Opusの運用ルール

| タイミング | 動作 |
|------------|------|
| プロジェクト開始時 | 人間の要求を構造化・言語化。Codex 5.3と設計を詰める。合意後Codexに引き渡して退場 |
| 要件追加・変更時 | 人間の追加要求を受けて構造化。Codex 5.3と設計を再調整。Codexに再引渡しして退場 |
| それ以外 | 不在。Codex 5.3が実装・レビュー、Sonnetがテスト・ドキュメントを担当 |

Opusは常駐しない。呼ばれた時だけ来て、ユーザーの意図を言語化し、Codexとエンジニアリング視点で設計を詰めて去る外部コンサル。
- 書記完了後、OpusがHaikuの出力を最終チェックし、漏れがあれば追記指示


## 開発成熟度 (Maturity Level) 定義

> **命名規約**: M1-M5 は実装全体の成熟度。テスト品質の深さは quality-lv5 スキルの T1-T5 で別軸管理。

| M | 状態 | 検証内容 | 検証レイヤー |
|---|------|----------|-------------|
| M1 | インターフェース定義のみ | 型定義・関数シグネチャ | L2 |
| M2 | 依存関係解決済み | モジュール間接続 | L4 |
| M3 | ロジック実装済み | ビジネスロジック完成 | L2 |
| M4.1 | 単体テスト通過 | 各関数の動作検証 | L5 |
| M4.2 | 統合テスト通過 | モジュール間連携検証 | L5 |
| M4.3 | API契約テスト通過 | Frontend ↔ Backend ↔ DB整合性 | L2.5 |
| M4.4 | E2Eテスト通過 | ユーザーシナリオ全体 | L5 |
| M4.5 | パフォーマンステスト通過 | 負荷・レスポンスタイム基準達成 | L5 |
| **M5** | **設計書を上回る** | **最適化・保守性・拡張性・セキュリティ強化** | **L1, L6** |

### M5「設計書を上回る」の判定基準

設計書の要件を100%充足した上で、以下の観点で上回ること。

**改善率の定義**: 全実装コンポーネント（関数・クラス・モジュール）のうち、設計書記載の要件を上回る改善を行った割合

| 観点 | 参考値 | 測定方法 |
|------|--------|---------|
| **総合改善率** | 30%以上（参考） | 全コンポーネントのうち、何らかの改善を含む割合 |
| パフォーマンス改善 | 10%以上（参考） | 性能要件を上回る最適化を実施したコンポーネントの割合 |
| エラーハンドリング改善 | 20%以上（参考） | 想定外エラー対応・リトライ・詳細ログを追加したコンポーネントの割合 |
| 保守性改善 | 20%以上（参考） | コードの可読性・テスト容易性を向上させたコンポーネントの割合 |
| 拡張性改善 | 15%以上（参考） | インターフェース設計・DIパターンで拡張性を高めたコンポーネントの割合 |
| セキュリティ | Critical/High脆弱性0件（**必須**） | セキュリティスキャン結果 |
| ドキュメント | 100%完備（**必須**） | API仕様・実装メモの完備度 |

> **注**: 改善率の具体的な数値はプロジェクトの性質により調整可能。セキュリティとドキュメントのみ必須合格条件。

**判定ロジック**:
1. 設計書準拠率100%を確認（必須）
2. 改善項目の分類・記録を確認（各観点で改善有無を判定）
3. Critical/High脆弱性0件、ドキュメント100%を確認（必須）
4. すべて達成でM5合格


## 工程表のオーケストレーション記載

工程表はタスクの時間管理だけでなく、各工程の実行方法を含む。Sonnetはこれを読んで配送するだけ。

### 工程表テンプレート（各行）

```markdown
| 工程ID | タスク | 難易度 | 担当モデル | スキル | ツール | 禁止ツール | 思考トークン | 前提工程 | 参照ドキュメント | 検証レイヤー | 目標Lv | 期限 |
|--------|--------|-------|-----------|--------|--------|-----------|-------------|----------|-----------------|-------------|--------|------|
| T-001 | 認証モジュール実装 | 9点 | Sonnet | security, api-design | Read,Edit,Bash | - | high | なし | design/auth.md | L2, L3 | Lv5 | MM/DD |
| T-002 | UI部品作成 | 2点 | Haiku | ui-components | Read,Edit | Bash | - | T-001 | design/ui.md | L2 | Lv4.1 | MM/DD |
| T-003 | DB読み取りクエリ | 3点 | Haiku | db-readonly | Read,Bash | Edit,Write | - | T-001 | design/database.md | L2 | Lv4.1 | MM/DD |
| T-004 | L2検証 | 5点 | Codex | verification | Read,Grep,Glob | Edit | medium | T-001 | requirements-handover.md | - | - | MM/DD |
```

#### 列の説明

| 列 | 説明 | 設定者 |
|----|------|--------|
| **スキル** | サブエージェントに事前読み込みするスキル（カンマ区切り） | Codex（自動推論） |
| **ツール** | 許可するツール（allowlist）。未指定は全ツール許可 | Codex（自動推論） |
| **禁止ツール** | 禁止するツール（denylist）。安全性のため明示的に制限 | Codex（自動推論） |
| **思考トークン** | Extended Thinking設定。`-` / `low` / `medium` / `high` | Codex（難易度に基づき自動設定） |

参照ドキュメント列のルール：
- 実装工程：該当する設計セクション＋依存関係マップを必ず指定
- 検証工程：上位レイヤーの基準ドキュメント＋検証対象を必ず指定
- 参照先が未指定の工程は実行不可（Sonnetは参照先がない工程をスキップする）

### タスク難易度判定アルゴリズム

工程表作成時、Codexが各タスクの難易度を事前判定し、最適なモデルを割り当てる。

#### 難易度スコア算出

各タスクに対して以下の指標でスコアを算出：

| 指標 | 配点 | 判定基準 |
|------|------|---------|
| **規模** | 0-3点 | 0: ~50行, 1: 51-200行, 2: 201-500行, 3: 501行以上 |
| **品質要件** | 0-3点 | 0: Lv3まで, 1: Lv4.1-4.2, 2: Lv4.3-4.4, 3: Lv5 |
| **技術難易度** | 0-3点 | 0: 定型処理, 1: ライブラリ利用, 2: 複雑ロジック, 3: アルゴリズム設計 |
| **依存関係数** | 0-3点 | 0: 0-2個, 1: 3-5個, 2: 6-10個, 3: 11個以上 |
| **API整合性** | 0-2点 | 0: なし, 1: 1層統合, 2: 3層統合（Frontend/Backend/DB） |

**総合難易度スコア** = 規模 + 品質要件 + 技術難易度 + 依存関係数 + API整合性 (最大14点)

#### モデル割り当てルール

| 難易度スコア | 担当モデル | 理由 |
|-------------|-----------|------|
| 0-3点 | Haiku | 軽量・定型タスク（UI部品、データ転記、単純CRUD） |
| 4-7点 | Sonnet | 標準実装タスク（ビジネスロジック、統合処理） |
| 8-10点 | Sonnet + Codex補助 | 高難度タスク（複雑ロジック、アルゴリズム設計） |
| 11-14点 | Sonnet（Opus初期設計） | 最高難度タスク（アーキテクチャ設計、高度な最適化） |

### リスク評価・優先度決定ルール

難易度スコアに加え、リスク評価を行い、タスクの優先度を決定する。

#### リスクスコア算出

| リスク要因 | 配点 | 判定基準 |
|-----------|------|---------|
| **影響範囲** | 0-3点 | 0: 単一ファイル, 1: 単一モジュール, 2: 複数モジュール, 3: システム全体 |
| **データリスク** | 0-3点 | 0: なし, 1: 参照のみ, 2: 更新あり, 3: 削除・破壊的変更あり |
| **外部依存** | 0-2点 | 0: なし, 1: 内部API, 2: 外部API・サードパーティ |
| **セキュリティ関連** | 0-3点 | 0: なし, 1: 認証周辺, 2: 認可・権限, 3: 決済・機密情報 |
| **可逆性** | 0-2点 | 0: 完全可逆, 1: 部分可逆, 2: 不可逆 |

**リスクスコア** = 影響範囲 + データリスク + 外部依存 + セキュリティ関連 + 可逆性 (最大13点)

#### リスクレベル分類

| リスクスコア | レベル | 対応 |
|-------------|--------|------|
| 0-3点 | **Low** | 通常実行 |
| 4-6点 | **Medium** | コードレビュー必須 |
| 7-9点 | **High** | 段階的実装 + 追加テスト |
| 10-13点 | **Critical** | 人間承認必須 + ロールバック計画 |

#### 優先度マトリクス

難易度とリスクを組み合わせて優先度を決定。

```
              リスク
              Low    Medium   High    Critical
         ┌─────────────────────────────────────┐
難易度    │                                     │
Low      │   P4      P3       P2        P1     │
(0-3)    │  (後回し) (通常)   (優先)    (最優先) │
         │                                     │
Medium   │   P3      P3       P2        P1     │
(4-7)    │  (通常)  (通常)   (優先)    (最優先) │
         │                                     │
High     │   P2      P2       P1        P1     │
(8-10)   │  (優先)  (優先)  (最優先)  (最優先) │
         │                                     │
Max      │   P1      P1       P1        P1     │
(11-14)  │ (最優先)(最優先)(最優先)  (最優先) │
         └─────────────────────────────────────┘
```

#### 優先度ごとの実行ルール

| 優先度 | 実行タイミング | 追加対応 |
|--------|--------------|---------|
| **P1（最優先）** | 即時着手 | 他タスクを中断してでも対応 |
| **P2（優先）** | 現タスク完了後に着手 | - |
| **P3（通常）** | 工程表順に実行 | - |
| **P4（後回し）** | 余裕がある時に実行 | バッチ処理可 |

#### リスク軽減策の自動適用

```python
# リスクレベルを数値で管理（文字列比較は順序が破綻するため）
RISK_LEVELS = {
    'Low': 1,
    'Medium': 2,
    'High': 3,
    'Critical': 4
}

def apply_risk_mitigation(task, risk_level: str):
    """リスクレベルに応じた軽減策を自動適用"""

    level = RISK_LEVELS.get(risk_level, 0)
    mitigations = []

    if level >= RISK_LEVELS['Medium']:  # Medium以上
        mitigations.append({
            'type': 'code_review',
            'description': 'Codexによる自動コードレビュー必須'
        })

    if level >= RISK_LEVELS['High']:  # High以上
        mitigations.append({
            'type': 'staged_implementation',
            'description': '段階的実装（機能単位でコミット）'
        })
        mitigations.append({
            'type': 'additional_tests',
            'description': 'エッジケーステスト追加'
        })

    if level >= RISK_LEVELS['Critical']:  # Critical
        mitigations.append({
            'type': 'human_approval',
            'description': '実行前に人間承認必須'
        })
        mitigations.append({
            'type': 'rollback_plan',
            'description': 'ロールバック手順の事前作成'
        })
        mitigations.append({
            'type': 'backup',
            'description': '変更対象のバックアップ作成'
        })

    return mitigations
```

#### リスク評価記録

各タスクのリスク評価を工程表に記録。

**注意**: `リスクレベル` カラムには `RISK_LEVELS` のキー（Low/Medium/High/Critical）のみを記載。`リスクスコア` は別カラムとして数値で記録。`apply_risk_mitigation()` には `リスクレベル` を渡す。

```markdown
| タスクID | タスク名 | 難易度 | リスクレベル | リスクスコア | 優先度 | 軽減策 |
|---------|---------|--------|-------------|-------------|--------|--------|
| T-001 | 認証モジュール実装 | 9点 | High | 8 | P1 | 段階実装, 追加テスト |
| T-002 | ユーザー一覧UI | 4点 | Low | 2 | P3 | - |
| T-003 | 決済API連携 | 11点 | Critical | 12 | P1 | 人間承認, ロールバック計画 |
```

#### サブエージェント構成設定

Claude Codeのサブエージェント機能を活用し、各タスクに最適な構成を事前設定する。

##### スキル付与（skills）

タスク種別に応じて、サブエージェントに事前読み込みするスキルを指定。起動時にコンテキストに注入される。

| タスク種別 | 推奨スキル | 説明 |
|-----------|-----------|------|
| 認証・セキュリティ | `security`, `api-design` | セキュリティベストプラクティス、認証フロー設計 |
| API実装 | `api-design`, `error-handling` | RESTful設計、エラーハンドリングパターン |
| UI実装 | `ui-components`, `accessibility` | UI設計パターン、アクセシビリティ対応 |
| DB操作 | `db-design`, `sql-optimization` | スキーマ設計、クエリ最適化 |
| テスト | `testing`, `mocking` | テスト設計、モック戦略 |
| 検証 | `verification`, `code-review` | 検証ロジック、レビュー観点 |

##### ツール制限（tools / disallowedTools）

安全性と効率性のため、タスクに必要なツールのみ許可。

| ツール | 用途 | 制限すべきケース |
|--------|------|-----------------|
| `Read` | ファイル読み取り | 常に許可 |
| `Edit` | ファイル編集 | 読み取り専用タスクでは禁止 |
| `Write` | ファイル作成 | 既存ファイル編集のみのタスクでは禁止 |
| `Bash` | コマンド実行 | セキュリティリスクの高いタスクでは禁止 |
| `Grep`, `Glob` | 検索 | 常に許可 |

**ツール制限の原則:**
- **最小権限**: 必要最小限のツールのみ許可
- **読み取り専用タスク**: `Edit`, `Write`, `Bash` を禁止
- **DB操作**: `Bash` は許可するが、PreToolUseフックで読み取り専用クエリのみ許可

##### 思考トークン（Extended Thinking）

タスクの複雑さに応じて、Claude の思考トークン（Extended Thinking）を設定。

| レベル | 設定値 | 対象タスク | 効果 |
|-------|--------|-----------|------|
| **なし** | `-` | 軽量タスク（難易度0-3点） | 高速処理、コスト最小 |
| **低** | `low` | 標準タスク（難易度4-6点） | バランス型 |
| **中** | `medium` | 複雑タスク（難易度7-9点） | 深い推論、高精度 |
| **高** | `high` | 最高難度タスク（難易度10点以上） | 最大限の推論、アーキテクチャ設計向け |

**思考トークン設定の自動判定:**
```python
def determine_thinking_level(difficulty_score):
    if difficulty_score <= 3:
        return "-"      # なし
    elif difficulty_score <= 6:
        return "low"    # 低
    elif difficulty_score <= 9:
        return "medium" # 中
    else:
        return "high"   # 高
```

##### スキル自動推論アルゴリズム

Codexがタスク内容から必要スキルを自動推論する。

```python
def infer_skills(task_description, design_section, dependency_map):
    """
    タスク内容から必要スキルを自動推論
    """
    skills = []

    # キーワードベース推論
    keyword_skill_map = {
        ('認証', 'auth', 'login', 'JWT', 'OAuth'): 'security',
        ('API', 'endpoint', 'REST', 'GraphQL'): 'api-design',
        ('UI', 'コンポーネント', 'component', 'フォーム'): 'ui-components',
        ('DB', 'データベース', 'SQL', 'クエリ'): 'db-design',
        ('テスト', 'test', 'spec'): 'testing',
        ('検証', 'verify', 'validation'): 'verification',
        ('エラー', 'error', '例外'): 'error-handling',
    }

    for keywords, skill in keyword_skill_map.items():
        if any(kw in task_description.lower() for kw in keywords):
            skills.append(skill)

    # 設計書セクションから追加推論
    if 'security' in design_section.lower():
        skills.append('security')
    if 'performance' in design_section.lower():
        skills.append('performance')

    return list(set(skills))  # 重複除去


def infer_tool_restrictions(task_type, difficulty_score):
    """
    タスク種別からツール制限を自動推論
    """
    if task_type == 'readonly':
        return {
            'tools': ['Read', 'Grep', 'Glob'],
            'disallowedTools': ['Edit', 'Write', 'Bash']
        }
    elif task_type == 'verification':
        return {
            'tools': ['Read', 'Grep', 'Glob', 'Bash'],
            'disallowedTools': ['Edit', 'Write']
        }
    elif task_type == 'implementation':
        return {
            'tools': ['Read', 'Edit', 'Write', 'Bash', 'Grep', 'Glob'],
            'disallowedTools': []
        }
    elif task_type == 'ui':
        return {
            'tools': ['Read', 'Edit', 'Write', 'Grep', 'Glob'],
            'disallowedTools': ['Bash']  # UI実装ではBash不要
        }
    else:
        return {'tools': [], 'disallowedTools': []}  # 全許可
```

##### 実装前スキル生成フロー

タスク開始前に必要スキルを検索・生成するフロー。既存スキルで不足があれば自動生成。

```
┌─────────────────────────────────────────────────────────────────┐
│ 【スキル準備フェーズ】（実装開始前、Codex担当）                   │
└─────────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. タスク分析                                                    │
│    ・タスク内容からキーワード抽出                                 │
│    ・設計書の該当セクション特定                                   │
│    ・依存関係マップから関連コンポーネント特定                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 既存スキル検索                                                │
│    ・skills/ ディレクトリをスキャン                              │
│    ・タスクキーワードとスキル名/内容をマッチング                 │
│    ・適合度スコア算出（0-100）                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │ 適合度 >= 70? │
              └───────┬───────┘
                      │
         ┌────────────┴────────────┐
         │Yes                      │No
         ▼                         ▼
┌─────────────────┐    ┌─────────────────────────────────────────┐
│ 既存スキル採用   │    │ 3. スキル自動生成                        │
│ → 工程表に記載   │    │    ・タスク要件から新スキル生成          │
└─────────────────┘    │    ・既存スキルをベースにカスタマイズ    │
                       │    ・skills/{task-type}.md に保存         │
                       └─────────────────────────────────────────┘
```

```python
def prepare_skills_for_task(task, existing_skills_dir):
    """
    タスク開始前にスキルを準備
    """
    # 1. タスク分析
    required_capabilities = analyze_task_requirements(task)

    # 2. 既存スキル検索
    matched_skills = []
    for skill_file in glob(f"{existing_skills_dir}/*.md"):
        skill_content = read_file(skill_file)
        score = calculate_match_score(required_capabilities, skill_content)
        if score >= 70:
            matched_skills.append({
                'file': skill_file,
                'score': score,
                'action': 'use'
            })
        elif score >= 40:
            matched_skills.append({
                'file': skill_file,
                'score': score,
                'action': 'extend'  # 拡張して使用
            })

    # 3. 不足スキルの生成
    missing_capabilities = find_missing_capabilities(required_capabilities, matched_skills)
    if missing_capabilities:
        new_skill = generate_skill(
            task_description=task['description'],
            capabilities=missing_capabilities,
            base_skills=matched_skills  # 既存スキルを参考に
        )
        save_skill(f"{existing_skills_dir}/{task['type']}-custom.md", new_skill)
        matched_skills.append({'file': new_skill['path'], 'score': 100, 'action': 'generated'})

    return matched_skills
```

##### スキル改善ループ

使用したスキルの効果を測定し、継続的に改善するループ。

```
┌─────────────────────────────────────────────────────────────────┐
│ 【スキル改善ループ】（実装完了後、Codex担当）                     │
└─────────────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────────┐
   │                                                          │
   ▼                                                          │
┌─────────────────────────────────────────────────────────────┐│
│ 1. 効果測定                                                  ││
│    ・タスク完了までの手戻り回数                              ││
│    ・検証パス率（L2-L5）                                     ││
│    ・コード品質メトリクス（Lv判定結果）                      ││
│    ・所要ターン数（少ない方が良い）                          ││
└─────────────────────┬───────────────────────────────────────┘│
                      │                                        │
                      ▼                                        │
┌─────────────────────────────────────────────────────────────┐│
│ 2. 改善候補の特定                                            ││
│    ・手戻りが多い箇所の分析                                  ││
│    ・スキルでカバーされていない知識の特定                    ││
│    ・類似タスクとの比較                                      ││
└─────────────────────┬───────────────────────────────────────┘│
                      │                                        │
                      ▼                                        │
              ┌───────────────┐                                │
              │ 改善必要?     │                                │
              └───────┬───────┘                                │
                      │                                        │
         ┌────────────┴────────────┐                          │
         │No                       │Yes                        │
         ▼                         ▼                           │
   ┌──────────┐    ┌─────────────────────────────────────────┐│
   │ 維持     │    │ 3. スキル更新                            ││
   │ (v1.x)   │    │    ・不足知識を追記                      ││
   └──────────┘    │    ・失敗パターンを注意事項に追加        ││
                   │    ・バージョンをインクリメント（v1.x+1） ││
                   └─────────────────────────────────────────┘│
                                   │                           │
                                   └───────────────────────────┘
```

```python
def evaluate_and_improve_skill(task_result, used_skills):
    """
    タスク完了後にスキルを評価・改善
    """
    for skill in used_skills:
        # 効果測定
        metrics = {
            'rework_count': task_result['rework_count'],
            'verification_pass_rate': task_result['pass_rate'],
            'quality_level': task_result['achieved_lv'],
            'turns_used': task_result['turns'],
        }

        # スコア算出（高いほど良い）
        effectiveness_score = calculate_effectiveness(metrics)

        # 改善判定
        if effectiveness_score < 70:
            # 改善が必要
            improvement = analyze_improvement_needs(task_result, skill)
            updated_skill = apply_improvements(skill, improvement)

            # バージョンインクリメント
            new_version = increment_version(skill['version'])
            updated_skill['version'] = new_version

            # 変更履歴に記録
            updated_skill['changelog'].append({
                'version': new_version,
                'date': today(),
                'changes': improvement['description'],
                'trigger_task': task_result['task_id']
            })

            save_skill(skill['path'], updated_skill)

        # メトリクス記録（改善有無に関わらず）
        record_skill_metrics(skill['name'], metrics)

def calculate_effectiveness(metrics):
    """
    スキル効果スコア算出
    """
    # 重み付け
    weights = {
        'rework_count': -10,  # 手戻り1回につき-10点
        'verification_pass_rate': 0.5,  # パス率50%→50点
        'quality_level': 10,  # Lv1=10点, Lv5=50点
        'turns_used': -2,  # ターン数が多いほど減点
    }

    base_score = 100
    score = base_score
    score += metrics['rework_count'] * weights['rework_count']
    score += metrics['verification_pass_rate'] * weights['verification_pass_rate']
    score += metrics['quality_level'] * weights['quality_level']
    score += max(0, 10 - metrics['turns_used']) * abs(weights['turns_used'])

    return max(0, min(100, score))
```

##### スキルテンプレート

新規スキル生成時のテンプレート。

```markdown
# skills/{skill-name}.md

---
name: {skill-name}
version: 1.0.0
created: {date}
updated: {date}
effectiveness_score: null  # 使用後に記録
usage_count: 0
---

## 概要
{このスキルが提供する能力の説明}

## 適用タスク
- {適用されるタスクの種類}
- {例: 認証機能実装, APIエンドポイント設計}

## 必須知識
{エージェントが知っておくべき前提知識}

## 実装パターン
{推奨される実装パターン、コード例}

## 注意事項
{よくある失敗パターン、避けるべきアンチパターン}

## 検証ポイント
{実装後にチェックすべき項目}

## 変更履歴
| バージョン | 日付 | 変更内容 | トリガータスク |
|-----------|------|----------|--------------|
| 1.0.0 | {date} | 初版作成 | - |
```

##### スキル管理ディレクトリ構成

```
skills/
├── core/                      # コアスキル（変更頻度低）
│   ├── security.md            # v2.1.0 - 認証・認可・脆弱性対策
│   ├── api-design.md          # v1.5.0 - REST/GraphQL設計
│   ├── db-design.md           # v1.3.0 - スキーマ設計・クエリ最適化
│   └── testing.md             # v2.0.0 - テスト戦略・カバレッジ
├── project/                   # プロジェクト固有（自動生成含む）
│   ├── auth-custom.md         # v1.0.0 - 本プロジェクトの認証仕様
│   ├── ui-patterns.md         # v1.2.0 - UIコンポーネント規約
│   └── data-validation.md     # v1.1.0 - 入力検証ルール
├── generated/                 # タスク毎に自動生成（一時的）
│   ├── T-001-auth.md          # T-001用カスタムスキル
│   └── T-003-transaction.md   # T-003用カスタムスキル
└── metrics/                   # スキル効果測定データ
    └── skill-metrics.json     # 全スキルのメトリクス履歴
```

##### ナレッジ蓄積フロー

開発中に得た知見を構造化して蓄積し、後続タスク・プロジェクトで再利用可能にする。

###### 収集タイミング

| タイミング | 収集内容 | 自動/手動 |
|------------|----------|-----------|
| **エラー解決後** | 原因・解決策・回避策 | 自動（解決パターン検出） |
| **手戻り発生時** | 見積もり誤りの原因・実際の複雑さ | 自動 |
| **検証パス時** | 成功パターン・有効だったアプローチ | 自動 |
| **Lv5達成時** | 品質達成に寄与した要因 | 自動 |
| **人間指摘時** | 指摘内容・改善点 | 手動（重要度高） |
| **新規ライブラリ導入時** | 使い方・ハマりポイント・ベストプラクティス | 半自動 |

###### ナレッジ分類体系

```yaml
# knowledge/taxonomy.yaml
categories:
  error_patterns:        # エラーパターン（再発防止）
    - runtime_errors
    - build_errors
    - test_failures
    - integration_issues

  solution_patterns:     # 解決パターン（再利用）
    - debugging_techniques
    - performance_fixes
    - security_patches
    - refactoring_patterns

  architecture_decisions: # アーキテクチャ判断（設計指針）
    - tech_selection
    - tradeoff_analysis
    - scaling_strategies

  domain_knowledge:      # ドメイン知識（業務理解）
    - business_rules
    - edge_cases
    - regulatory_requirements

  tooling:               # ツール知識（効率化）
    - cli_tips
    - ide_shortcuts
    - library_gotchas

tags:
  severity: [critical, major, minor, info]
  reusability: [project_specific, cross_project, universal]
  confidence: [proven, experimental, deprecated]
```

###### ケーススタディ構造

```yaml
# knowledge/cases/CASE-{id}.yaml
---
id: CASE-001
title: "JWT認証でのトークンリフレッシュ競合問題"
created: 2025-01-15
updated: 2025-01-20
category: error_patterns.integration_issues
tags:
  severity: critical
  reusability: cross_project
  confidence: proven

# 状況（いつ・どこで発生したか）
context:
  project: "TaskFlow"
  task_id: T-001
  phase: "L4検証"
  tech_stack: [Next.js, FastAPI, JWT]
  trigger: "複数タブ同時操作時にログアウト"

# 問題（何が起きたか）
problem:
  症状: "複数タブで同時にAPIを叩くと、片方のタブが401エラーでログアウト"
  影響範囲: "全認証済みユーザー"
  発見方法: "E2Eテストで複数タブシナリオを実行"

# 調査過程（何を試したか）
investigation:
  - attempt: "トークン有効期限の延長"
    result: "効果なし - 根本原因ではなかった"
    time_spent: "2ターン"

  - attempt: "リフレッシュエンドポイントのログ追加"
    result: "競合状態を発見 - 同時リフレッシュでトークン不整合"
    time_spent: "3ターン"

# 解決策（何で解決したか）
solution:
  approach: "リフレッシュトークンのミューテックス実装"
  implementation: |
    // フロントエンド側
    let refreshPromise = null;
    async function refreshToken() {
      if (refreshPromise) return refreshPromise;  // 既存のリフレッシュを待つ
      refreshPromise = api.post('/auth/refresh');
      try {
        return await refreshPromise;
      } finally {
        refreshPromise = null;
      }
    }
  verification: "複数タブE2Eテストが全パス"

# 教訓（何を学んだか）
lessons:
  - "JWTリフレッシュは競合状態を必ず考慮する"
  - "複数タブ/ウィンドウシナリオはE2Eテストに含める"
  - "認証関連は難易度+2点で見積もる"

# 適用条件（いつ使えるか）
applicability:
  when_to_apply:
    - "JWT認証を実装する時"
    - "SPA + APIの構成でログイン機能がある時"
  prerequisites:
    - "フロントエンドでトークン管理している"
  contraindications:
    - "サーバーサイドセッション管理の場合は不要"

# 関連情報
references:
  - skill: "skills/common/security/SKILL.md#jwt-refresh"
  - external: "https://example.com/jwt-best-practices"
  - related_cases: [CASE-015, CASE-023]
```

###### ナレッジ蓄積ディレクトリ構成

```
knowledge/
├── taxonomy.yaml              # 分類体系定義
├── cases/                     # ケーススタディ
│   ├── CASE-001.yaml          # JWT認証競合問題
│   ├── CASE-002.yaml          # N+1クエリ問題
│   └── ...
├── patterns/                  # パターン集（ケースから抽出）
│   ├── error/                 # エラーパターン
│   │   ├── auth-race-condition.md
│   │   └── db-connection-pool.md
│   ├── solution/              # 解決パターン
│   │   ├── mutex-pattern.md
│   │   └── retry-with-backoff.md
│   └── architecture/          # アーキテクチャパターン
│       └── cqrs-implementation.md
├── gotchas/                   # ハマりポイント集
│   ├── nextjs-14.md           # Next.js 14固有の注意点
│   ├── fastapi-async.md       # FastAPI非同期の落とし穴
│   └── prisma-transactions.md # Prismaトランザクション注意
└── index.md                   # ナレッジ検索用インデックス
```

###### 自動収集ロジック

```python
class KnowledgeCollector:
    """タスク実行中のナレッジ自動収集"""

    def __init__(self, knowledge_dir):
        self.knowledge_dir = knowledge_dir
        self.pending_cases = []

    def on_error_resolved(self, error, resolution, context):
        """エラー解決時に自動収集"""
        if self._is_significant(error, resolution):
            case = self._create_case_draft(
                category="error_patterns",
                context=context,
                problem=error,
                solution=resolution,
                lessons=self._extract_lessons(error, resolution),
            )
            self.pending_cases.append(case)

    def on_rework_triggered(self, task, reason, actual_complexity):
        """手戻り発生時に見積もり誤りを記録"""
        case = self._create_case_draft(
            category="architecture_decisions",
            context=task,
            problem=f"見積もり誤り: 予想{task.difficulty}点 → 実際{actual_complexity}点",
            solution=reason,
            lessons=[f"{task.type}タスクは+{actual_complexity - task.difficulty}点で見積もる"],
        )
        self.pending_cases.append(case)

    def on_human_feedback(self, feedback, context):
        """人間指摘は即座に記録（重要度高）"""
        case = self._create_case_draft(
            category="domain_knowledge",
            context=context,
            problem=feedback.issue,
            solution=feedback.correction,
            lessons=[feedback.lesson],
            tags={'severity': 'critical', 'confidence': 'proven'},
        )
        # 人間指摘は即保存
        self._save_case(case)

    def _is_significant(self, error, resolution):
        """記録に値するか判定"""
        # 同じエラーが過去にない & 解決に3ターン以上かかった
        return (
            not self._exists_similar_case(error) and
            resolution.turns_to_resolve >= 3
        )

    def flush_pending(self):
        """保留中のケースを確定・保存"""
        for case in self.pending_cases:
            # 類似ケースがあればマージ
            similar = self._find_similar_case(case)
            if similar:
                self._merge_cases(similar, case)
            else:
                self._save_case(case)
        self.pending_cases = []
```

###### スキル化パイプライン（ナレッジ → スキル変換）

```
ナレッジ蓄積
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ スキル化判定（週次 or ケース10件蓄積時）                          │
├─────────────────────────────────────────────────────────────────┤
│ 判定基準:                                                        │
│ ・同一カテゴリのケースが3件以上                                   │
│ ・reusability が cross_project 以上                              │
│ ・confidence が proven                                           │
│ ・類似パターンが抽出可能                                          │
└─────────────────────────────────────────────────────────────────┘
    │ 基準クリア
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ パターン抽出                                                     │
├─────────────────────────────────────────────────────────────────┤
│ 1. 関連ケースをクラスタリング                                     │
│ 2. 共通要素を抽出（問題パターン、解決アプローチ）                  │
│ 3. 変動要素を特定（パラメータ化可能な部分）                        │
│ 4. 適用条件を汎用化                                               │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ スキル生成                                                       │
├─────────────────────────────────────────────────────────────────┤
│ 1. スキルテンプレートに流し込み                                   │
│ 2. 例示コードを汎用化                                             │
│ 3. 検証ポイントをチェックリスト化                                 │
│ 4. 関連スキルへのリンク追加                                       │
│ 5. skills/{category}/{name}/SKILL.md に配置 → SKILL_MAP.md 更新  │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ スキル検証                                                       │
├─────────────────────────────────────────────────────────────────┤
│ ・元ケースのタスクを再実行（ドライラン）                          │
│ ・新スキル適用で手戻り減少を確認                                  │
│ ・効果スコア >= 80 で正式採用                                     │
└─────────────────────────────────────────────────────────────────┘
```

###### スキル化の実例

```
【元ケース群】
- CASE-001: JWT認証でのトークンリフレッシュ競合問題
- CASE-015: OAuth2フローでの同時コールバック問題
- CASE-023: セッション更新の競合によるログアウト

【抽出されたパターン】
カテゴリ: error_patterns.integration_issues
共通問題: 認証状態の同時更新による競合
共通解決: ミューテックス/シングルフライトパターン

【生成されたスキル】
skills/common/security/SKILL.md に追記:

## 認証状態の競合防止

### 問題パターン
- 複数タブ/ウィンドウでの同時認証更新
- トークンリフレッシュの競合
- セッション状態の不整合

### 解決アプローチ
```typescript
// シングルフライトパターン
const inflightRequests = new Map<string, Promise<any>>();

async function singleFlight<T>(key: string, fn: () => Promise<T>): Promise<T> {
  if (inflightRequests.has(key)) {
    return inflightRequests.get(key) as Promise<T>;
  }
  const promise = fn();
  inflightRequests.set(key, promise);
  try {
    return await promise;
  } finally {
    inflightRequests.delete(key);
  }
}
```

### チェックリスト
- [ ] 認証エンドポイントにシングルフライト適用
- [ ] 複数タブシナリオのE2Eテスト追加
- [ ] トークン更新のログ追加（競合検知用）

### 関連ケース
- [CASE-001](../knowledge/cases/CASE-001.yaml)
- [CASE-015](../knowledge/cases/CASE-015.yaml)
- [CASE-023](../knowledge/cases/CASE-023.yaml)
```

#### タスク設計フロー（スキル生成込み）

```
┌─────────────────────────────────────────────────────────────────┐
│ L4工程表作成フェーズ（Codex担当）                                │
├─────────────────────────────────────────────────────────────────┤
│ 1. L3依存関係マップを読み取り                                    │
│ 2. 各タスクの難易度スコアを算出                                  │
│ 3. モデル割り当てルールに基づき担当モデル決定                    │
│ 4. タスク種別からスキル・ツール制限を自動推論                    │
│ 5. ★ スキル準備（既存スキル検索 → 不足あれば自動生成）          │
│ 6. 難易度スコアから思考トークンレベルを自動設定                  │
│ 7. 工程表に全設定を記載（スキルパス含む）                        │
│ 8. Opus介入が必要なタスク（11点以上）をリストアップ              │
│ 9. 人間にOpus介入タスクを報告（指摘がなければ続行）              │
└─────────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 実装フェーズ（Sonnet/Haiku担当）                                 │
├─────────────────────────────────────────────────────────────────┤
│ ・工程表に記載されたスキルをコンテキストに読み込み               │
│ ・スキルに従って実装                                             │
│ ・手戻り発生時はスキル不足を記録                                 │
└─────────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 検証フェーズ（Codex担当）                                        │
├─────────────────────────────────────────────────────────────────┤
│ ・L2-L5検証実行                                                  │
│ ・検証結果とスキル使用状況を記録                                 │
└─────────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ ★ スキル改善フェーズ（タスク完了後、Codex担当）                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. 効果測定（手戻り回数、検証パス率、Lv判定）                    │
│ 2. 効果スコア < 70 → スキル改善実行                              │
│    ・不足知識の追記                                              │
│    ・失敗パターンを注意事項に追加                                │
│    ・バージョンインクリメント                                    │
│ 3. メトリクス記録（metrics/skill-metrics.json）                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 工程表への記載例（完全版）

```markdown
| 工程ID | タスク | 難易度 | 担当モデル | スキル | ツール | 禁止ツール | 思考トークン | 前提工程 | 参照ドキュメント | 検証レイヤー | 目標Lv | 期限 |
|--------|--------|-------|-----------|--------|--------|-----------|-------------|----------|-----------------|-------------|--------|------|
| T-001 | 認証モジュール実装 | 9点 | Sonnet + Codex | security, api-design | Read,Edit,Bash | - | medium | なし | design/auth.md | L2, L3 | Lv5 | MM/DD |
| T-002 | UI部品作成 | 2点 | Haiku | ui-components | Read,Edit | Bash | - | T-001 | design/ui.md | L2 | Lv4.1 | MM/DD |
| T-003 | 分散トランザクション実装 | 12点 | Sonnet（Opus初期設計） | db-design, error-handling | Read,Edit,Bash | - | high | T-001 | design/transaction.md | L2, L5 | Lv5 | MM/DD |
| T-004 | DB読み取りクエリ最適化 | 4点 | Sonnet | db-design, sql-optimization | Read,Bash | Edit,Write | low | T-003 | design/database.md | L3 | Lv4.2 | MM/DD |
| T-005 | L2.5検証（API整合性） | 6点 | Codex | verification, api-design | Read,Grep,Glob | Edit,Write | low | T-001,T-003 | api-contract.yaml | L2.5 | - | MM/DD |
```

#### サブエージェント定義ファイル生成

工程表の設定からClaude Code用のAGENT.mdを自動生成する。オーケストレーターがタスク実行時に参照。

##### 生成例: T-001（認証モジュール実装）

`.claude/agents/T-001-auth/AGENT.md`:
```yaml
---
name: T-001-auth
description: 認証モジュール実装（難易度9点）
model: sonnet
skills:
  - security
  - api-design
tools: Read, Edit, Bash, Grep, Glob
disallowedTools: []
permissionMode: acceptEdits
---

## タスク
認証モジュールを実装する。

## 参照ドキュメント
- design/auth.md
- dependency-map.md

## 目標Lv
Lv5（設計書を上回る）

## 検証レイヤー
L2, L3

## 制約
- セキュリティベストプラクティスに従う
- JWT実装はライブラリを使用
- パスワードはbcryptでハッシュ化
```

##### 生成例: T-004（DB読み取りクエリ最適化）

`.claude/agents/T-004-db-readonly/AGENT.md`:
```yaml
---
name: T-004-db-readonly
description: DB読み取りクエリ最適化（難易度4点）
model: sonnet
skills:
  - db-design
  - sql-optimization
tools: Read, Bash, Grep, Glob
disallowedTools: Edit, Write
permissionMode: dontAsk
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
---

## タスク
DB読み取りクエリを最適化する。

## 参照ドキュメント
- design/database.md

## 目標Lv
Lv4.2（統合テスト通過）

## 検証レイヤー
L3

## 制約
- 読み取り専用（SELECT文のみ）
- インデックス活用を確認
- 実行計画の改善を検証
```

##### AGENT.md自動生成アルゴリズム

```python
def generate_agent_md(task_row):
    """
    工程表の1行からAGENT.mdを生成
    """
    template = f"""---
name: {task_row['工程ID']}-{slugify(task_row['タスク'])}
description: {task_row['タスク']}（難易度{task_row['難易度']}）
model: {map_model(task_row['担当モデル'])}
skills:
{format_skills(task_row['スキル'])}
tools: {task_row['ツール'] or 'Read, Edit, Write, Bash, Grep, Glob'}
disallowedTools: {task_row['禁止ツール'] or '[]'}
permissionMode: {determine_permission_mode(task_row)}
{generate_hooks(task_row)}
---

## タスク
{task_row['タスク']}を実行する。

## 参照ドキュメント
{format_docs(task_row['参照ドキュメント'])}

## 目標Lv
{task_row['目標Lv']}

## 検証レイヤー
{task_row['検証レイヤー']}
"""
    return template


def map_model(model_str):
    """担当モデル文字列をClaude Codeモデル名に変換"""
    if 'Haiku' in model_str:
        return 'haiku'
    elif 'Opus' in model_str:
        return 'opus'
    else:
        return 'sonnet'


def determine_permission_mode(task_row):
    """タスク種別から権限モードを決定"""
    if '検証' in task_row['タスク']:
        return 'dontAsk'  # 検証タスクは自動実行
    elif task_row['禁止ツール'] and 'Edit' in task_row['禁止ツール']:
        return 'dontAsk'  # 読み取り専用は自動実行
    else:
        return 'acceptEdits'  # 編集ありは確認付き
```

##### サブエージェント入出力（I/O）方針

サブエージェント間のデータ受け渡しを標準化し、情報欠落・認識齟齬を防止する。

###### 入力（Input）仕様

```yaml
# サブエージェントへの入力フォーマット
subagent_input:
  # 必須項目
  required:
    task_id: "T-001"                    # 工程表のタスクID
    task_description: "認証モジュール実装"  # タスク内容
    target_quality_level: "Lv5"         # 目標品質レベル
    verification_layers: ["L2", "L3"]   # 対象検証レイヤー

  # コンテキスト（自動注入）
  context:
    decisions_file: ".claude/memory/decisions.md"
    constraints_file: ".claude/memory/constraints.md"
    skills: ["security.md", "api-design.md"]
    reference_docs: ["design/auth.md"]

  # 前工程からの引継ぎ
  handover:
    from_task: "T-000"                  # 前タスクID（なければnull）
    artifacts:                          # 前タスクの成果物
      - path: "src/auth/types.ts"
        status: "created"
      - path: "docs/api-contract.yaml"
        status: "updated"
    notes: "JWT方式で決定済み。リフレッシュトークンの有効期限は15分"
    warnings: ["auth.ts:56にTODOあり"]

  # 制約・禁止事項
  constraints:
    allowed_tools: ["Read", "Edit", "Write", "Bash"]
    disallowed_tools: []
    allowed_paths: ["src/auth/**", "tests/auth/**"]
    disallowed_paths: ["src/db/**", "config/prod/**"]
    time_budget: "30 minutes"
    token_budget: 50000
```

###### 出力（Output）仕様

```yaml
# サブエージェントからの出力フォーマット
subagent_output:
  # 必須項目
  required:
    task_id: "T-001"
    status: "completed"  # completed | failed | blocked | partial
    quality_achieved: "Lv4.5"

  # 成果物リスト
  artifacts:
    created:
      - path: "src/auth/jwt.ts"
        description: "JWT生成・検証モジュール"
        lines_added: 120
      - path: "src/auth/middleware.ts"
        description: "認証ミドルウェア"
        lines_added: 85
    modified:
      - path: "src/auth/types.ts"
        description: "認証型定義を拡張"
        lines_changed: 15
    deleted: []

  # 検証結果
  verification:
    L2:
      status: "passed"
      score: 0.92
      notes: "設計書との整合性確認済み"
    L3:
      status: "passed"
      score: 0.88
      notes: "循環依存なし"

  # 次工程への引継ぎ
  handover:
    to_task: "T-002"
    notes: |
      - JWT実装完了。リフレッシュトークン対応済み
      - authMiddleware を各ルートに適用が必要
    warnings:
      - "E2Eテストで複数タブシナリオを追加すべき"
    dependencies_for_next:
      - "tests/auth/jwt.test.ts を先に実行すること"

  # 問題・ブロッカー（status != completed の場合）
  issues:
    - type: "blocked"
      description: "外部API仕様が未確定"
      blocker: "API契約書の更新待ち"
      suggested_action: "T-005完了後に再開"

  # メトリクス
  metrics:
    turns_used: 15
    tokens_consumed: 35000
    cache_hit_rate: 0.72
    time_elapsed: "18 minutes"
    rework_count: 1
```

###### I/O検証ルール

```python
class SubagentIOValidator:
    """サブエージェント入出力の検証"""

    def validate_input(self, input_data):
        """入力データの検証"""
        errors = []

        # 必須項目チェック
        required = ['task_id', 'task_description', 'target_quality_level']
        for field in required:
            if field not in input_data.get('required', {}):
                errors.append(f"必須項目不足: {field}")

        # コンテキストファイルの存在確認
        for file in input_data.get('context', {}).get('skills', []):
            skill_path = self._resolve_skill_path(file)  # SKILL_MAP.md で名前→パス解決
            if not self._file_exists(skill_path):
                errors.append(f"スキルファイル不存在: {file} (resolved: {skill_path})")

        # 前工程引継ぎの整合性
        if input_data.get('handover', {}).get('from_task'):
            prev_output = self._load_previous_output(input_data['handover']['from_task'])
            if prev_output['status'] != 'completed':
                errors.append(f"前工程未完了: {input_data['handover']['from_task']}")

        return errors

    def validate_output(self, output_data):
        """出力データの検証"""
        errors = []

        # 必須項目チェック
        if 'status' not in output_data.get('required', {}):
            errors.append("ステータス未指定")

        # 成果物の実在確認
        for artifact in output_data.get('artifacts', {}).get('created', []):
            if not self._file_exists(artifact['path']):
                errors.append(f"成果物が存在しない: {artifact['path']}")

        # 品質レベルの妥当性
        achieved = output_data.get('required', {}).get('quality_achieved')
        if achieved and not self._is_valid_quality_level(achieved):
            errors.append(f"不正な品質レベル: {achieved}")

        # failed/blocked時のissues必須
        status = output_data.get('required', {}).get('status')
        if status in ['failed', 'blocked'] and not output_data.get('issues'):
            errors.append("失敗/ブロック時はissues必須")

        return errors
```

##### サブエージェントのドキュメント更新方針

サブエージェントがドキュメントを更新する際のルールと権限を定義。

###### ドキュメント分類と更新権限

| ドキュメント種別 | 更新権限 | 更新条件 | 例 |
|-----------------|---------|----------|-----|
| **要件引継書** | 🔒 Opus + 人間承認 | 要件変更時のみ | requirements-handover.md |
| **設計書** | 🔒 Codex + 人間承認 | 設計変更時のみ | design/*.md |
| **決定事項（変更禁止セクション）** | 🔒 人間のみ | 人間指摘時 | decisions.md#変更禁止 |
| **決定事項（条件付き変更可セクション）** | ⚠️ エージェント条件付き | 記載条件を満たす時 | decisions.md#条件付き変更可 |
| **決定事項（AI判断セクション）** | ⚠️ エージェント追記可 | AI判断記録時 | decisions.md#AI判断 |
| **決定事項（決定ログセクション）** | ⚠️ エージェント追記可 | 判断記録時 | decisions.md#決定ログ |
| **工程表** | ⚠️ Codex | 計画変更時 | schedule.md |
| **検証レポート** | ✅ 各担当 | 検証完了時 | verification/*.md |
| **API契約書** | ⚠️ Codex | L2.5検証時 | api-contract.yaml |
| **ソースコード** | ✅ Sonnet/Haiku | 実装時 | src/**/* |
| **テストコード** | ✅ Sonnet/Haiku | テスト実装時 | tests/**/* |
| **ナレッジ** | ✅ 自動収集 | 条件満たした時 | knowledge/**/* |
| **スキル** | ⚠️ Codex | 改善トリガー時 | skills/**/* |

凡例: 🔒 = 厳重管理、⚠️ = 要注意、✅ = 自由

###### 更新プロトコル

```yaml
# ドキュメント更新時の標準プロトコル
update_protocol:
  # 1. 更新前チェック
  pre_update:
    - check_permission: "自分に更新権限があるか"
    - check_lock: "他のエージェントがロックしていないか"
    - backup_original: "元ファイルをバックアップ"

  # 2. 更新実行
  update:
    - add_changelog: "変更内容を記録"
    - increment_version: "バージョン番号を上げる"
    - update_timestamp: "更新日時を記録"
    - update_author: "更新者を記録"

  # 3. 更新後検証
  post_update:
    - validate_format: "フォーマット検証"
    - check_consistency: "他ドキュメントとの整合性"
    - notify_dependents: "依存ドキュメントに通知"

  # 4. 承認フロー（要承認ドキュメントの場合）
  approval:
    - create_diff: "差分を生成"
    - request_review: "人間にレビュー依頼"
    - wait_approval: "承認待ち"
    - apply_or_rollback: "承認→適用、却下→ロールバック"
```

###### 更新時のヘッダー規約

```markdown
<!-- 全ドキュメント共通ヘッダー -->
---
version: 1.2.0
last_updated: 2026-02-06T15:30:00Z
updated_by: Sonnet (T-001)
update_reason: "認証モジュール実装に伴うAPI契約更新"
requires_approval: false
locked_by: null
---
```

###### 更新ロック機構

```python
class DocumentLockManager:
    """ドキュメントの同時更新を防止"""

    def __init__(self, lock_dir=".claude/locks"):
        self.lock_dir = lock_dir

    def acquire_lock(self, doc_path, agent_id, timeout=300):
        """ドキュメントロックを取得"""
        lock_file = self._get_lock_path(doc_path)

        # 既存ロックをチェック
        if self._is_locked(lock_file):
            existing_lock = self._read_lock(lock_file)
            if self._is_expired(existing_lock, timeout):
                # 期限切れロックは解放
                self._release_lock(lock_file)
            else:
                return False, f"ロック中: {existing_lock['agent_id']}"

        # ロック取得
        lock_data = {
            'agent_id': agent_id,
            'doc_path': doc_path,
            'acquired_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=timeout)).isoformat(),
        }
        self._write_lock(lock_file, lock_data)
        return True, "ロック取得成功"

    def release_lock(self, doc_path, agent_id):
        """ドキュメントロックを解放"""
        lock_file = self._get_lock_path(doc_path)

        if not self._is_locked(lock_file):
            return True, "ロックなし"

        existing_lock = self._read_lock(lock_file)
        if existing_lock['agent_id'] != agent_id:
            return False, f"他エージェントのロック: {existing_lock['agent_id']}"

        self._release_lock(lock_file)
        return True, "ロック解放成功"
```

###### 更新の追跡と監査

```yaml
# ドキュメント更新ログ（自動記録）
# .claude/logs/doc-updates.jsonl

{"timestamp": "2026-02-06T15:30:00Z", "agent": "Sonnet", "task": "T-001", "action": "update", "doc": "src/auth/jwt.ts", "reason": "新規作成", "lines": 120, "approved": true}
{"timestamp": "2026-02-06T15:35:00Z", "agent": "Codex", "task": "T-001", "action": "update", "doc": "api-contract.yaml", "reason": "認証エンドポイント追加", "lines": 25, "approved": true}
{"timestamp": "2026-02-06T15:40:00Z", "agent": "Sonnet", "task": "T-001", "action": "update", "doc": "design/auth.md", "reason": "実装詳細追記", "lines": 10, "approved": false, "rejection_reason": "設計書は人間承認必須"}
```

###### サブエージェント間の引継ぎフロー

```
┌─────────────────────────────────────────────────────────────────┐
│ Task A (Sonnet)                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 1. 入力を受け取り、検証                                          │
│ 2. タスク実行                                                    │
│ 3. 成果物を生成                                                  │
│ 4. 出力を標準フォーマットで生成                                  │
│ 5. 引継ぎ情報を handover セクションに記載                        │
│ 6. ドキュメント更新（権限内のみ）                                │
│ 7. 更新ログを記録                                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼ 出力を次タスクの入力に変換
┌─────────────────────────────────────────────────────────────────┐
│ Orchestrator (Sonnet)                                           │
├─────────────────────────────────────────────────────────────────┤
│ 1. Task A の出力を検証                                           │
│ 2. 工程表から次タスク（Task B）を特定                            │
│ 3. Task A の出力を Task B の入力フォーマットに変換               │
│ 4. 引継ぎ情報をマージ                                            │
│ 5. Task B を起動                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Task B (Haiku)                                                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. 入力を受け取り、検証                                          │
│ 2. handover.notes を確認                                         │
│ 3. handover.warnings に注意してタスク実行                        │
│ 4. ...                                                          │
└─────────────────────────────────────────────────────────────────┘
```

###### 引継ぎ失敗時のリカバリ

```python
def handle_handover_failure(from_task, to_task, error):
    """引継ぎ失敗時のリカバリ処理"""

    if error.type == 'missing_artifact':
        # 成果物が見つからない
        return {
            'action': 'retry_from_task',
            'task': from_task,
            'reason': f"成果物不存在: {error.path}",
        }

    elif error.type == 'validation_failed':
        # 出力フォーマット不正
        return {
            'action': 'fix_and_retry',
            'task': from_task,
            'fix_instruction': "出力フォーマットを修正して再実行",
        }

    elif error.type == 'quality_not_met':
        # 品質未達
        return {
            'action': 'rework',
            'task': from_task,
            'target': error.required_level,
            'current': error.achieved_level,
        }

    elif error.type == 'lock_conflict':
        # ドキュメントロック競合
        return {
            'action': 'wait_and_retry',
            'wait_for': error.locked_by,
            'timeout': 300,
        }

    else:
        # 未知のエラー → 人間エスカレーション
        return {
            'action': 'escalate_to_human',
            'error': error,
            'context': {
                'from_task': from_task,
                'to_task': to_task,
            },
        }
```


## 手戻り評価

| 指標 | 内容 |
|------|------|
| 計測対象 | 各レイヤーでの検証ループ回数 |
| 記録場所 | 各レイヤーの検証レポート |
| 評価基準 | 手戻り回数が多い＝Codexの計画精度が低い |
| フィードバック | 手戻りレポートを次回の計画策定時にCodexが参照し改善 |
| 目標 | プロジェクトを重ねるごとに手戻り回数が減少すること |


## ループ検証の原則

1. **全レイヤーが常時ループ**：一度合格しても上位レイヤーの変更で再検証が走る
2. **各レイヤーは自レイヤー内で完結**：L3の不合格がL1に直接戻ることはない。L3内ループで解決不能→L2にエスカレーション
3. **検証は数値判定**：エージェントの自己申告を信用しない。Codexが数値で出力し閾値で機械的に判定
4. **スケールダウン禁止**：項目削除・粒度低下方向の変更はどのレイヤーでもNG
5. **エスカレーション経路**：レイヤー内ループで解決不能→1つ上のレイヤーへ→最終的に人間判断
6. **MVP禁止**：段階的リリースの判断権は人間のみ。エージェントがスコープを縮小しない


## エージェント人事配置

> **正本**: `skills/tools/ai-coding/SKILL.md` §4 のマルチエージェント戦略テーブルが正本。本セクションはその要約。

| 役割名 | モデル | 担当 | 稼働形態 |
|--------|--------|------|----------|
| 言語化 | Opus 4.6 | ユーザーの意図を構造化・言語化。ビジネス判断 | スポット（開始時＋要件変更時） |
| エンジニア | Codex 5.3 | 設計レビュー＋実装＋コードレビュー。設計から実装まで一気通貫 | 非同期常時 |
| 修正 | Codex 5.2 | 軽微なエラー修正。エラー多数時は5.3にエスカレーション | 非同期 |
| テスト・ドキュメント | Sonnet 4.5 | テストコード作成・実行、設計書・仕様書の更新 | 常時 |
| 調査 | Haiku 4.5 | 情報収集・下調べ・軽量タスク | 随時 |
| オーケストレーション | 人間 | タスク指示・方向修正。将来はAgent orchestration対応予定 | 常時 |

### 役割の分離原則
- **言語化（Opus 4.6）**：考える。書かない。企画から要件への変換に特化
- **エンジニア（Codex 5.3）**：設計→実装→レビューを一気通貫。設計者と実装者のギャップを排除し、修正サイクルを最小化
- **修正（Codex 5.2）**：軽微な修正を低コストで処理。判断が必要な修正は5.3へエスカレーション
- **テスト・ドキュメント（Sonnet 4.5）**：テスト作成・ドキュメント更新に専念。実装を持たないことで品質に集中
- **調査（Haiku 4.5）**：低コストで大量の情報収集・下調べ
- **オーケストレーション（人間）**：タスク指示と方向修正。エージェントはスコープを縮小しない

### Codex 5.3 による修正サイクル削減
- **Before**：Sonnet実装 → Codexレビュー → 指摘5件 → Sonnet修正 → レビュー → 指摘2件 → ... （3-5サイクル）
- **After**：Codex 5.3実装 → Codex 5.3レビュー → 指摘0-1件 → 完了（1-2サイクル）
- **本質**：設計者（Codex）が実装も担うことで、設計意図の伝達ロスが消滅

### モデル更新対応戦略
- **ワークフロー駆動**：モデル性能向上は即座に活用可能。役割の入れ替えはエージェント人事配置テーブルの更新のみ
- **Codex 5.3 の特性活用**：Terminal-Bench 77.3%（+13.3）、自律実行力を活かし実装を集約

### AIモデル変化追跡

モデルは頻繁に更新・廃止される。変化を検知し、フレームワークを最新状態に保つ。

#### モデル台帳（model-registry.yaml）

```yaml
# docs/model-registry.yaml
models:
  opus:
    current_version: "claude-opus-4-6-20260203"
    role: "言語化（ユーザー意図の構造化・ビジネス判断）"
    usage: "スポット"
    cost_tier: "premium"
    capabilities:
      - complex_reasoning
      - ambiguity_resolution
      - requirements_structuring
      - business_judgment
    deprecation_date: null
    successor: null
    benchmark_scores:
      reasoning: 96
      coding: 95
      instruction_following: 97

  codex_5_3:
    current_version: "codex-5.3"
    role: "エンジニア（設計レビュー・実装・コードレビュー）"
    usage: "非同期常時"
    cost_tier: "standard"
    capabilities:
      - planning
      - implementation
      - code_review
      - verification
      - dependency_analysis
    deprecation_date: null
    successor: null
    benchmark_scores:
      terminal_bench: 77.3
      os_world: 64.7

  codex_5_2:
    current_version: "codex-5.2"
    role: "修正（軽微なエラー修正。エラー多数時は5.3にエスカレーション）"
    usage: "非同期"
    cost_tier: "economy"
    capabilities:
      - minor_fixes
      - lint_correction
    deprecation_date: null
    successor: "codex_5_3"

  sonnet:
    current_version: "claude-sonnet-4-5-20251101"
    role: "テスト・ドキュメント（テスト作成・実行、設計書・仕様書更新）"
    usage: "常時"
    cost_tier: "standard"
    capabilities:
      - testing
      - documentation
      - specification_writing
      - orchestration
    deprecation_date: null
    successor: null
    benchmark_scores:
      reasoning: 85
      coding: 92
      instruction_following: 90

  haiku:
    current_version: "claude-haiku-4-5-20251001"
    role: "調査（情報収集・下調べ・軽量タスク）"
    usage: "随時"
    cost_tier: "economy"
    capabilities:
      - research
      - information_gathering
      - lightweight_tasks
    deprecation_date: null
    successor: null
    benchmark_scores:
      reasoning: 70
      coding: 75
      instruction_following: 85

# 変更履歴
changelog:
  - date: "2025-11-01"
    model: "opus"
    change: "4.5リリース"
    impact: "要件構造化精度向上"
  - date: "2025-11-01"
    model: "sonnet"
    change: "4.5リリース"
    impact: "実装速度・品質向上"
  - date: "2026-02-03"
    model: "opus"
    change: "4.6リリース"
    impact: "コーディング能力大幅向上。設計→実装の一貫性向上"
  - date: "2026-02-07"
    model: "codex"
    change: "5.3リリース"
    impact: "計画・検証精度向上"
  - date: "2026-02-07"
    model: "all"
    change: "エージェント人事配置刷新"
    impact: "Codex 5.3が実装を吸収（設計→実装一気通貫）。Sonnetはテスト・ドキュメントに専念。Haikuは調査担当に変更。修正サイクル3-5回→1-2回に削減"
```

#### 変化検知ルール

| 監視対象 | 検知方法 | アクション |
|----------|----------|------------|
| **新バージョンリリース** | Anthropic API changelog監視 | モデル台帳更新→テスト実行→切り替え判断 |
| **廃止予告** | 公式ドキュメント監視 | 移行計画策定→successor設定→段階的切り替え |
| **能力変化** | プロジェクト実績データ | benchmark_scores更新→役割再評価 |
| **コスト変更** | 料金表監視 | cost_tier更新→割り当てルール再計算 |

#### モデル切り替えプロセス

```
1. 新モデル検知
   ↓
2. サンドボックス環境でテスト
   - 既存タスクの再実行比較
   - ベンチマークスコア計測
   ↓
3. 判断基準チェック
   - 品質: 既存モデル比 >= 95%
   - コスト: 既存モデル比 <= 120%
   - 速度: 既存モデル比 >= 90%
   ↓
4. 段階的ロールアウト
   - 10% → 50% → 100%
   ↓
5. モデル台帳更新 + changelog記録
```

### 動的モデル割り当て最適化

タスク特性・状況に応じて最適なモデルを動的に選択する。

#### 割り当て判定フロー

```python
def select_optimal_model(task, context):
    """タスクとコンテキストから最適なモデルを選択"""

    # 1. タスク特性分析
    task_profile = analyze_task(task)
    # - complexity: 1-14（難易度スコア）
    # - type: reasoning | implementation | verification | transcription
    # - estimated_tokens: 推定トークン数
    # - requires_extended_thinking: bool

    # 2. コンテキスト評価
    context_factors = {
        'budget_remaining': context.daily_budget - context.spent_today,
        'deadline_pressure': context.hours_until_deadline,
        'error_rate_recent': context.recent_error_rate,  # 直近10タスクのエラー率
        'quality_priority': context.project_quality_level,  # Lv目標
    }

    # 3. 候補モデルのスコアリング
    candidates = []
    for model in available_models:
        score = calculate_fit_score(model, task_profile, context_factors)
        candidates.append((model, score))

    # 4. 最適モデル選択
    return max(candidates, key=lambda x: x[1])[0]

def calculate_fit_score(model, task, context):
    """モデル適合スコアを計算（0-100）"""

    base_score = 50

    # 能力適合: タスクタイプとモデル能力のマッチング
    if task['type'] in model.capabilities:
        base_score += 20

    # 難易度適合: 過剰スペック・スペック不足のペナルティ
    difficulty_gap = model.benchmark_scores['coding'] - task['complexity'] * 7
    if difficulty_gap > 30:  # 過剰スペック
        base_score -= 15  # コスト無駄
    elif difficulty_gap < -10:  # スペック不足
        base_score -= 30  # 品質リスク

    # コスト効率: 予算残量に応じた調整
    cost_factor = {
        'premium': -20 if context['budget_remaining'] < 0.3 else 0,
        'standard': 0,
        'economy': +10 if context['budget_remaining'] < 0.3 else 0,
    }
    base_score += cost_factor.get(model.cost_tier, 0)

    # 品質優先: 目標Lvが高い場合は高性能モデルを優先
    if context['quality_priority'] >= 4.5 and model.cost_tier == 'premium':
        base_score += 15

    # エラー率対応: 直近エラー率が高い場合は高性能モデルにフォールバック
    if context['error_rate_recent'] > 0.3:
        base_score += 10 if model.cost_tier in ['premium', 'standard'] else -10

    return max(0, min(100, base_score))
```

#### コスト/品質/速度トレードオフ設定

```yaml
# docs/model-allocation-policy.yaml
allocation_policies:
  default:
    priority_order: [quality, cost, speed]
    thresholds:
      quality_minimum: 0.85  # 品質下限（Lv4.2相当）
      cost_daily_limit: 50.0  # USD/日
      latency_max: 30000  # ms

  deadline_crunch:  # 締め切り直前
    priority_order: [speed, quality, cost]
    thresholds:
      quality_minimum: 0.80
      cost_daily_limit: 100.0  # 予算2倍
      latency_max: 15000

  cost_saving:  # 予算節約モード
    priority_order: [cost, quality, speed]
    thresholds:
      quality_minimum: 0.80
      cost_daily_limit: 20.0
      latency_max: 60000

  quality_first:  # 品質最優先（本番直前）
    priority_order: [quality, speed, cost]
    thresholds:
      quality_minimum: 0.95  # Lv5相当
      cost_daily_limit: 200.0
      latency_max: 60000
```

#### フォールバック戦略

| 状況 | 検知条件 | フォールバック先 | 理由 |
|------|----------|------------------|------|
| **モデル過負荷** | レスポンス > 30秒 3回連続 | 同tier別モデル → 下位tier | 可用性確保 |
| **連続エラー** | 同一タスクで3回失敗 | 上位tierモデル | 難易度見積もり誤り補正 |
| **予算枯渇** | daily_limit 90%到達 | economy tierのみ | コスト超過防止 |
| **品質低下** | Lv達成率 < 70% | premium tier一時投入 | 品質回復 |

#### 実行時モニタリング

```python
class ModelAllocationMonitor:
    """モデル割り当ての実行時監視"""

    def __init__(self):
        self.metrics = {
            'model_usage': {},       # モデル別使用回数
            'cost_by_model': {},     # モデル別コスト
            'success_rate': {},      # モデル別成功率
            'avg_latency': {},       # モデル別平均レイテンシ
            'quality_scores': {},    # モデル別品質スコア
        }

    def record_task_completion(self, model, task, result):
        """タスク完了時にメトリクスを記録"""
        self.metrics['model_usage'][model] += 1
        self.metrics['cost_by_model'][model] += result.cost
        self.metrics['success_rate'][model].append(result.success)
        self.metrics['avg_latency'][model].append(result.latency)
        self.metrics['quality_scores'][model].append(result.quality_level)

    def generate_daily_report(self):
        """日次レポート生成"""
        return {
            'total_cost': sum(self.metrics['cost_by_model'].values()),
            'model_efficiency': self._calculate_efficiency(),
            'recommendations': self._generate_recommendations(),
        }

    def _generate_recommendations(self):
        """割り当て改善提案"""
        recommendations = []

        # 過剰使用チェック
        for model, usage in self.metrics['model_usage'].items():
            if model.cost_tier == 'premium' and usage > threshold:
                recommendations.append(
                    f"{model}: 使用過多。下位tierへの委譲を検討"
                )

        # 品質低下チェック
        for model, scores in self.metrics['quality_scores'].items():
            if avg(scores) < 4.0:
                recommendations.append(
                    f"{model}: 品質低下。タスク難易度とのミスマッチ確認"
                )

        return recommendations
```

#### 割り当て最適化の継続的改善

```
週次サイクル:
1. メトリクス集計
   - モデル別使用統計
   - コスト/品質/速度の実績

2. 異常検知
   - 想定外の高コストタスク
   - 品質低下パターン

3. ルール調整
   - 難易度スコアの閾値調整
   - フォールバック条件の見直し

4. モデル台帳更新
   - 実績ベースのbenchmark_scores補正
   - 新たな能力/限界の発見記録
```

### プロンプトキャッシュ戦略

Claude APIのプロンプトキャッシュを最大限活用してコストを削減する。

#### キャッシュの仕組み

```
┌─────────────────────────────────────────────────────────────────┐
│ プロンプト構成                                                   │
├─────────────────────────────────────────────────────────────────┤
│ [System Prompt]  ← キャッシュ対象（静的・共通）                  │
│ [Context Files]  ← キャッシュ対象（セッション内で固定）          │
│ [Conversation]   ← キャッシュ対象（累積）                        │
│ [Current Query]  ← 非キャッシュ（毎回変化）                      │
└─────────────────────────────────────────────────────────────────┘

キャッシュヒット時: 入力トークン料金が 90% 削減
キャッシュミス時:  通常料金 + キャッシュ書き込みコスト（25%増）
```

#### キャッシュ最適化の原則

| 原則 | 説明 | 実装方法 |
|------|------|----------|
| **静的部分を先頭に** | 変化しない情報ほど先頭に配置 | System > Framework > Context > Query |
| **チャンク境界を意識** | キャッシュは1024トークン単位 | 重要情報を境界に合わせる |
| **セッション内で固定** | 同一セッションでコンテキストを変えない | ドキュメントロードは最初に確定 |
| **共通プレフィックス** | 複数リクエストで同じ先頭部分 | HELIX.md + decisions.md を固定 |

#### プロンプト構成の最適化

```yaml
# 推奨プロンプト構成（キャッシュ効率最大化）
prompt_structure:
  # 1. システムプロンプト（不変・最優先キャッシュ）
  system:
    - role_definition      # エージェントの役割定義
    - framework_rules      # Helixフレームワーク基本ルール
    - output_format        # 出力フォーマット指定
    estimated_tokens: 2000
    cache_priority: highest

  # 2. プロジェクトコンテキスト（セッション内固定）
  project_context:
    - decisions.md         # 決定事項（変更禁止）
    - constraints.md       # 制約条件
    - current_task_spec    # 現在のタスク仕様
    estimated_tokens: 3000
    cache_priority: high

  # 3. 参照ドキュメント（タスク種別で固定）
  reference_docs:
    - relevant_skills      # 該当スキル
    - design_docs          # 設計書の該当部分
    estimated_tokens: 2000
    cache_priority: medium

  # 4. 会話履歴（累積・キャッシュ効く）
  conversation:
    - previous_turns       # 過去のやり取り
    estimated_tokens: variable
    cache_priority: auto

  # 5. 現在のクエリ（毎回変化・キャッシュ対象外）
  current_query:
    - user_instruction     # ユーザーの指示
    - current_file_content # 編集対象ファイル（変化する）
    estimated_tokens: variable
    cache_priority: none
```

#### セッション設計とキャッシュ効率

```python
class CacheOptimizedSession:
    """キャッシュ効率を最大化するセッション設計"""

    def __init__(self, project_config):
        # セッション開始時に固定コンテキストを確定
        self.fixed_context = self._build_fixed_context(project_config)
        self.cache_stats = {'hits': 0, 'misses': 0, 'cost_saved': 0}

    def _build_fixed_context(self, config):
        """セッション内で変化しない固定コンテキストを構築"""
        return {
            'system': self._load_system_prompt(),
            'decisions': self._load_file('.claude/memory/decisions.md'),
            'constraints': self._load_file('.claude/memory/constraints.md'),
            'task_spec': self._load_current_task_spec(config.task_id),
            'skills': self._load_required_skills(config.task_type),
        }

    def build_prompt(self, user_query, dynamic_context=None):
        """キャッシュ効率を考慮したプロンプト構築"""
        prompt_parts = []

        # 1. 固定部分（キャッシュ効く）- 順序固定
        prompt_parts.append(self.fixed_context['system'])
        prompt_parts.append(self.fixed_context['decisions'])
        prompt_parts.append(self.fixed_context['constraints'])
        prompt_parts.append(self.fixed_context['task_spec'])
        prompt_parts.append('\n'.join(self.fixed_context['skills']))

        # 2. 会話履歴（累積でキャッシュ効く）
        prompt_parts.append(self._format_conversation_history())

        # 3. 動的部分（キャッシュ効かない）- 最後に配置
        if dynamic_context:
            prompt_parts.append(f"## Current File\n{dynamic_context}")
        prompt_parts.append(f"## User Query\n{user_query}")

        return '\n\n'.join(prompt_parts)

    def estimate_cache_savings(self, prompt):
        """キャッシュによるコスト削減を推定"""
        fixed_tokens = self._count_tokens(self.fixed_context)
        total_tokens = self._count_tokens(prompt)

        # 固定部分がキャッシュヒットすると仮定
        cache_hit_rate = fixed_tokens / total_tokens
        savings_rate = cache_hit_rate * 0.9  # 90%削減

        return {
            'fixed_tokens': fixed_tokens,
            'total_tokens': total_tokens,
            'estimated_savings': f"{savings_rate * 100:.1f}%",
        }
```

#### 並列実行戦略

```yaml
# 並列実行とキャッシュの関係
parallel_execution:
  # 同一コンテキストで並列実行 → キャッシュ共有で効率的
  same_context_parallel:
    use_case: "複数ファイルの同時レビュー"
    strategy: |
      1. 共通コンテキスト（設計書、ルール）を最初に送信
      2. 各ファイルレビューを並列リクエスト
      3. 共通部分はキャッシュヒット
    efficiency: high

  # 異なるコンテキストで並列実行 → キャッシュミス
  different_context_parallel:
    use_case: "異なるタスクの同時実行"
    strategy: |
      1. タスク毎にセッションを分離
      2. 各セッション内ではキャッシュ効く
      3. セッション間でキャッシュ共有なし
    efficiency: medium

  # 推奨パターン
  recommended_patterns:
    - pattern: "バッチレビュー"
      description: "同一ルールで複数ファイルをレビュー"
      cache_benefit: "ルール部分（~3000 tokens）が共有"

    - pattern: "段階的実装"
      description: "同一設計書から複数コンポーネント実装"
      cache_benefit: "設計書（~2000 tokens）が共有"

    - pattern: "テスト生成"
      description: "同一テスト戦略で複数テスト生成"
      cache_benefit: "テスト戦略（~1500 tokens）が共有"
```

#### コスト最適化戦略（統合版）

```python
class CostOptimizer:
    """プロンプトキャッシュ + モデル選択 + 並列実行の統合最適化"""

    def __init__(self):
        self.pricing = {
            'opus': {'input': 15.0, 'output': 75.0, 'cache_read': 1.5, 'cache_write': 18.75},
            'sonnet': {'input': 3.0, 'output': 15.0, 'cache_read': 0.3, 'cache_write': 3.75},
            'haiku': {'input': 0.25, 'output': 1.25, 'cache_read': 0.025, 'cache_write': 0.3125},
        }  # USD per 1M tokens

    def optimize_request_batch(self, tasks):
        """タスクバッチの最適実行計画を生成"""
        plan = {
            'sequential': [],    # 直列実行（依存関係あり）
            'parallel_groups': [],  # 並列実行グループ
            'estimated_cost': 0,
            'estimated_savings': 0,
        }

        # 1. 依存関係分析
        dependency_graph = self._build_dependency_graph(tasks)

        # 2. 並列実行可能なタスクをグループ化
        parallel_groups = self._group_parallelizable(tasks, dependency_graph)

        # 3. 各グループ内でキャッシュ効率を最大化
        for group in parallel_groups:
            # 共通コンテキストを持つタスクをまとめる
            context_groups = self._group_by_context(group)
            for ctx_group in context_groups:
                optimized = self._optimize_group(ctx_group)
                plan['parallel_groups'].append(optimized)

        # 4. コスト計算
        plan['estimated_cost'] = self._calculate_total_cost(plan)
        plan['estimated_savings'] = self._calculate_savings(plan)

        return plan

    def _optimize_group(self, tasks):
        """同一コンテキストグループの最適化"""
        # 共通コンテキストを抽出
        common_context = self._extract_common_context(tasks)

        # モデル選択（グループ内で統一するとキャッシュ効率UP）
        optimal_model = self._select_model_for_group(tasks)

        return {
            'tasks': tasks,
            'common_context': common_context,
            'model': optimal_model,
            'execution': 'parallel',
            'cache_strategy': 'shared_prefix',
        }

    def generate_cost_report(self, execution_log):
        """実行後のコストレポート生成"""
        report = {
            'total_cost': 0,
            'by_model': {},
            'cache_stats': {
                'hits': 0,
                'misses': 0,
                'hit_rate': 0,
                'savings': 0,
            },
            'optimization_opportunities': [],
        }

        for entry in execution_log:
            # コスト集計
            model = entry['model']
            cost = self._calculate_entry_cost(entry)
            report['total_cost'] += cost
            report['by_model'][model] = report['by_model'].get(model, 0) + cost

            # キャッシュ統計
            if entry.get('cache_hit'):
                report['cache_stats']['hits'] += 1
                report['cache_stats']['savings'] += entry['cache_savings']
            else:
                report['cache_stats']['misses'] += 1

        # ヒット率計算
        total_requests = report['cache_stats']['hits'] + report['cache_stats']['misses']
        if total_requests > 0:
            report['cache_stats']['hit_rate'] = report['cache_stats']['hits'] / total_requests

        # 最適化提案
        report['optimization_opportunities'] = self._find_opportunities(execution_log)

        return report

    def _find_opportunities(self, execution_log):
        """コスト最適化の機会を検出"""
        opportunities = []

        # 1. 高コストモデルの過剰使用
        opus_usage = sum(1 for e in execution_log if e['model'] == 'opus')
        if opus_usage > len(execution_log) * 0.1:
            opportunities.append({
                'type': 'model_downgrade',
                'detail': f'Opus使用率が高い（{opus_usage}/{len(execution_log)}）。Sonnetへの委譲を検討',
                'potential_savings': '50-70%',
            })

        # 2. キャッシュミスの多発
        cache_misses = sum(1 for e in execution_log if not e.get('cache_hit'))
        if cache_misses > len(execution_log) * 0.5:
            opportunities.append({
                'type': 'cache_optimization',
                'detail': 'キャッシュミス率が高い。コンテキスト構成を見直し',
                'potential_savings': '30-50%',
            })

        # 3. 並列化の機会
        sequential_count = sum(1 for e in execution_log if e.get('execution') == 'sequential')
        if sequential_count > len(execution_log) * 0.7:
            opportunities.append({
                'type': 'parallelization',
                'detail': '直列実行が多い。並列実行可能なタスクを検討',
                'potential_savings': '時間短縮（コストは同等）',
            })

        return opportunities
```

#### チャット画面でのキャッシュ活用ガイド

```markdown
## Claude Code / Cursor でのキャッシュ最適化

### セッション開始時
1. **固定コンテキストを最初にロード**
   ```
   @.claude/memory/decisions.md
   @.claude/memory/constraints.md
   @helix/HELIX.md
   ```
   → これらは変更しない。キャッシュが効き続ける。

2. **タスク仕様を確定してから開始**
   - タスク仕様を途中で変えるとキャッシュミス
   - 最初に「今日のタスク」を明確に宣言

### セッション中
3. **コンテキスト追加は最小限に**
   - 必要なファイルだけ `@` 参照
   - 追加するたびにキャッシュプレフィックスが変わる

4. **同一ファイルの繰り返し編集はキャッシュ効く**
   - 「auth.ts を修正して」→「さらに auth.ts を修正して」
   - 同じファイルへの連続操作はキャッシュヒット

### 避けるべきパターン
❌ セッション中に大量のファイルを `@` 参照追加
❌ タスクの途中で別タスクに切り替え
❌ 長文のコピペをプロンプトに含める（毎回変わる）
❌ 「前のコンテキストは忘れて」（キャッシュ無効化）

### 推奨パターン
✅ セッション開始時に必要なコンテキストを全てロード
✅ 1セッション1タスクの原則
✅ 繰り返し使う指示はシステムプロンプトに含める
✅ 大きなファイルは要約版を使う
```

#### コスト監視ダッシュボード

```yaml
# 日次コストレポートの構成
daily_cost_report:
  summary:
    total_cost: "$XX.XX"
    vs_yesterday: "+/-X%"
    cache_hit_rate: "XX%"
    savings_from_cache: "$XX.XX"

  by_model:
    opus:
      requests: N
      tokens: "XXk input / XXk output"
      cost: "$XX.XX"
      cache_hit_rate: "XX%"
    sonnet:
      requests: N
      tokens: "XXk input / XXk output"
      cost: "$XX.XX"
      cache_hit_rate: "XX%"
    haiku:
      requests: N
      tokens: "XXk input / XXk output"
      cost: "$XX.XX"
      cache_hit_rate: "XX%"

  optimization_alerts:
    - "⚠️ Opus使用率が目標（10%）を超過（15%）"
    - "⚠️ キャッシュヒット率が目標（70%）を下回る（55%）"
    - "✅ 並列実行率は目標達成（40%）"

  recommendations:
    - "T-005, T-006 は同一コンテキスト。並列実行で時間短縮可能"
    - "security.md のロード回数が多い。常時ロードに変更を検討"
```


## 管理ドキュメント：2枚

### 工程表
- 時間軸管理＋オーケストレーション指示
- L3依存関係に基づく実装順序
- 各工程の担当モデル・検証タイミング・目標Lv
- ブロッカー記録
- **ダッシュボード機能**：
  - リアルタイム進捗可視化（工程別進捗率）
  - 品質メトリクス（Lv達成率、テスト合格率、カバレッジ）
  - 手戻り回数の記録・集計（レイヤー別、工程別）
  - レイヤー別エスカレーション回数（5回上限）
  - 現在のボトルネック・ブロッカー状況

### 人事シート
- エージェント×担当コンポーネント×現在Lv×目標Lv×期限×ステータス
- 各レイヤーの検証ループ状況・手戻り回数
- ダッシュボード・ネクストアクション機能を統合


## プロジェクト構成

```
project/
├── CLAUDE.md                    # オーケストレーター指示（最小限）
├── .claude/
│   ├── agents/                  # 自動生成サブエージェント定義 ★新設
│   │   ├── T-001-auth/
│   │   │   └── AGENT.md        # 認証モジュール用エージェント
│   │   ├── T-002-ui/
│   │   │   └── AGENT.md        # UI実装用エージェント
│   │   └── [task-id]/
│   │       └── AGENT.md        # 工程表から自動生成
│   └── settings.local.json     # プロジェクト固有の権限設定
├── skills/
│   ├── orchestrator.md          # Sonnet用：工程表読み取り＋配送ルール
│   ├── security.md              # セキュリティスキル
│   ├── api-design.md            # API設計スキル
│   ├── ui-components.md         # UI設計スキル
│   ├── db-design.md             # DB設計スキル
│   ├── testing.md               # テストスキル
│   ├── verification.md          # 検証スキル
│   └── [domain-skill].md        # その他ドメイン別スキル
├── docs/
│   ├── requirements-handover.md # 要件引継書（Opus作成→Codex参照）
│   ├── schedule.md              # 工程表（オーケストレーション込み）
│   ├── hr-sheet.md              # 人事シート
│   ├── design/                  # 設計書（セクション分割）
│   │   ├── frontend.md          # Frontend設計
│   │   ├── backend.md           # Backend設計
│   │   └── database.md          # DB設計
│   ├── api-contract.yaml        # API契約書（OpenAPI仕様） ★L2.5
│   ├── dependency-map.md        # 依存関係マップ
│   ├── test-plan.md             # テスト計画書 ★L4
│   ├── deploy-plan.md           # デプロイ計画書 ★L5
│   ├── rules/                   # 実装・品質ルール ★新設
│   │   ├── coding-rules.md      # コーディング規約（ESLint/Prettier設定含む）
│   │   ├── common-components.md # 共通コンポーネント一覧・設計方針
│   │   ├── test-policy.md       # テスト規約（カバレッジ基準、命名規則）
│   │   └── quality-standards.md # 品質基準（メトリクス、レビュー基準）
│   └── verification/            # 各レイヤーの検証レポート
│       ├── L1-report.md         # 受入検証レポート
│       ├── L2-report.md         # 設計整合性レポート
│       ├── L2.5-report.md       # API整合性レポート ★新設
│       ├── L3-report.md         # 依存関係検証レポート
│       ├── L4-report.md         # テスト結果レポート ★拡張
│       └── L5-report.md         # 本番検証レポート ★新設
```


## 設計思想

### Helixの核心原則

1. **設計書を上回る開発**
   - 単なる要件充足ではなく、パフォーマンス・保守性・拡張性・セキュリティで設計書を超える
   - Lv5判定で「上回り度」を数値化し、継続的な品質向上を実現

2. **人間は指摘のみ、あとはエージェント駆動**
   - 人間は企画書（ビジネス要件）を提供したら、基本的に何もしない
   - 要件定義からデプロイまで、すべてエージェントが自律的に実行
   - 人間は問題を発見した時のみ指摘する（積極的な指示は出さない）
   - 判断が必要な箇所のみ人間にエスカレーション（MVP判断、スコープ縮小、本番リリース）

   **人間の役割（限定的）:**
   | 役割 | タイミング | 内容 |
   |------|----------|------|
   | 企画提出 | プロジェクト開始時 | ビジネス要件を自然言語で提供 |
   | 指摘 | 随時（問題発見時のみ） | 品質・方向性に問題があれば指摘。なければ何もしない |
   | 承認 | エスカレーション時のみ | MVP判断、スコープ変更、本番リリースの最終判断 |

   **人間がしないこと:**
   - 進捗確認の催促（AIが自律的に進行報告）
   - 実装詳細の指示（AIが設計書に基づき自律判断）
   - 設計レビューの積極的実施（AIが自動検証）
   - タスクの優先順位付け（工程表に従い自動実行）

3. **多層検証ループによる品質保証**
   - L1〜L5の各レイヤーが独立した検証サイクルを持つ
   - 問題の局所化と自動修復を実現
   - 特にL2.5（API整合性）で、Frontend/Backend/DBのズレを早期発見

4. **ワークフロー駆動、モデル非依存**
   - ワークフロー（仕組み）で精度を担保し、特定モデルに依存しない
   - Sonnet 5.0等の新モデルが登場しても、役割配置を変更するだけで対応可能
   - 処理パターンを先に固め、部品（モデル）は差し替え可能にする

5. **オーケストレーション自動化**
   - オーケストレーションを工程表に焼き込み、都度判断コストを排除
   - 工程表を読んで配送するだけのシンプルなオーケストレーター

6. **コスト最適化**
   - 高コストモデル（Opus）はスポット利用に限定し、原価率を最小化
   - Codex（計画・検証）、Sonnet（実装）、Haiku（軽量処理）の役割分担で効率化

7. **継続的改善**
   - 手戻り回数を計画精度の評価軸とし、プロジェクトを重ねるごとに改善サイクルを回す
   - 各レイヤーの検証レポートを蓄積し、次回計画時にフィードバック


## バージョン互換性ポリシー

Helixフレームワーク自体、および開発するプロダクトのバージョン互換性に関するポリシー。

### Helixフレームワークのバージョニング

セマンティックバージョニング（SemVer）に準拠: `MAJOR.MINOR.PATCH`

| 変更種別 | バージョン | 例 | 互換性 |
|---------|-----------|-----|--------|
| **破壊的変更** | MAJOR | 1.x → 2.0 | 非互換（マイグレーションガイド必須） |
| **機能追加** | MINOR | 1.0 → 1.1 | 後方互換 |
| **バグ修正** | PATCH | 1.0.0 → 1.0.1 | 完全互換 |

### AIモデルバージョン互換性

| 項目 | ポリシー |
|------|---------|
| **モデル更新対応** | 新モデルリリース後、2週間以内に互換性検証完了 |
| **非推奨期間** | モデル非推奨化後、6ヶ月間は旧モデルでの動作保証 |
| **フォールバック** | 新モデルで問題発生時、自動で安定版にフォールバック |
| **テスト** | 各モデルバージョンでの回帰テスト必須 |

### スキルバージョン互換性

```yaml
# skills/common/security/SKILL.md
---
version: "2.1.0"
min_helix_version: "1.0.0"
max_helix_version: "2.x"
deprecated: false
replacement: null
changelog:
  - version: "2.1.0"
    date: "2025-01-15"
    changes:
      - "JWT更新ロジック追加"
  - version: "2.0.0"
    date: "2024-12-01"
    changes:
      - "認証フロー再設計（破壊的変更）"
---
```

### 依存関係バージョンポリシー

#### プロダクション依存

| カテゴリ | ポリシー | 例 |
|---------|---------|-----|
| **フレームワーク** | メジャーバージョン固定 | `"next": "^14.0.0"` |
| **ライブラリ** | マイナーバージョンまで固定 | `"lodash": "~4.17.0"` |
| **セキュリティ関連** | パッチバージョンも固定 | `"bcrypt": "5.1.1"` |

#### 開発依存

| カテゴリ | ポリシー | 例 |
|---------|---------|-----|
| **テストツール** | マイナーバージョンまで固定 | `"jest": "~29.7.0"` |
| **Linter/Formatter** | メジャーバージョン固定 | `"eslint": "^8.0.0"` |
| **ビルドツール** | マイナーバージョンまで固定 | `"vite": "~5.0.0"` |

### バージョンアップ戦略

#### 定期アップデート

| 頻度 | 対象 | 手順 |
|------|------|------|
| **週次** | パッチバージョン | 自動更新 + CIテスト |
| **月次** | マイナーバージョン | 手動レビュー + 回帰テスト |
| **四半期** | メジャーバージョン | 影響調査 + マイグレーション計画 |

#### 自動更新フロー

```
Dependabot/Renovate検出
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. 変更種別判定                              │
│    - patch: 自動マージ可                    │
│    - minor: CIパス後に自動マージ            │
│    - major: 手動レビュー必須                │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 2. CI実行                                    │
│    - 単体テスト                             │
│    - 統合テスト                             │
│    - セキュリティスキャン                   │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 3. 条件判定                                  │
│    - patch + CI通過 → 自動マージ           │
│    - minor + CI通過 → 自動マージ           │
│    - major or CI失敗 → 人間レビュー        │
└─────────────────────────────────────────────┘
```

### 非推奨化プロセス

| フェーズ | 期間 | 対応 |
|---------|------|------|
| **告知** | 6ヶ月前 | 非推奨警告をログ出力 |
| **警告強化** | 3ヶ月前 | 起動時に警告表示 |
| **猶予終了** | 非推奨化 | 動作はするがサポート外 |
| **削除** | 12ヶ月後 | コードから完全削除 |

### ロックファイル管理

| ファイル | 管理ポリシー |
|---------|-------------|
| `package-lock.json` | コミット必須、CI環境で検証 |
| `pnpm-lock.yaml` | コミット必須 |
| `poetry.lock` | コミット必須 |
| `Cargo.lock` | アプリケーション: コミット、ライブラリ: コミットしない |

### 互換性マトリクス

プロジェクトで使用する主要技術のサポートバージョンを明示。

```markdown
# 互換性マトリクス（2026-02時点）

| 技術 | サポートバージョン | EOL | 備考 |
|------|-------------------|-----|------|
| Node.js | 20.x, 22.x | 20.x: 2026-04, 22.x: 2027-04 | 18.x は2025-04でEOL済み、サポート外 |
| Python | 3.11, 3.12, 3.13 | 3.11: 2027-10 | 3.10 は2026-10でEOL予定、移行推奨 |
| PostgreSQL | 15, 16, 17 | 15: 2027-11 | 14 は2026-11でEOL予定、移行推奨 |
| React | 18.x, 19.x | - | - |
| Next.js | 14.x, 15.x | - | - |

**注意**: EOL日付は定期的に更新すること。プロジェクト開始時に最新情報を確認。
```


## 実装・品質ルール制定

Helixフレームワークでは、コードの品質と一貫性を保証するため、L2（設計フェーズ）で実装・品質ルールを制定し、L4/L5で準拠を検証します。

### ルール制定のタイミング

| レイヤー | タイミング | 担当 | 制定内容 |
|---------|----------|------|---------|
| **L2** | 設計書作成時 | Codex | コーディング規約、共通コンポーネント設計、テスト規約、品質基準の制定 |
| **L4** | テスト計画時 | Codex | テスト規約の詳細化、カバレッジ基準の確定 |
| **L5** | デプロイ計画時 | Codex | 本番品質基準の確定（Lv5判定基準） |

### 1. コーディング規約（`docs/rules/coding-rules.md`）

L2で制定され、実装時に全エージェントが従うべきルール。

#### 含まれる内容

| 項目 | 内容 |
|------|------|
| **命名規則** | 変数・関数・クラス・ファイル名の命名パターン |
| **コードスタイル** | インデント、改行、括弧の位置、コメント形式 |
| **Linter設定** | ESLint / Pylint / RuboCop 等の設定ファイル |
| **Formatter設定** | Prettier / Black / rustfmt 等の設定ファイル |
| **禁止パターン** | 使用禁止API、非推奨パターン、アンチパターン |
| **セキュリティルール** | SQL Injection防止、XSS防止、認証/認可の実装方法 |

#### 例: TypeScript コーディング規約

```markdown
# コーディング規約（TypeScript）

## 命名規則
- **変数**: camelCase（例: `userName`, `isActive`）
- **定数**: UPPER_SNAKE_CASE（例: `MAX_RETRY_COUNT`）
- **関数**: camelCase、動詞始まり（例: `getUserById`, `validateEmail`）
- **クラス**: PascalCase（例: `UserService`, `AuthController`）
- **インターフェース**: PascalCase、`I` プレフィックス不要（例: `User`, `ApiResponse`）
- **型エイリアス**: PascalCase（例: `UserId`, `ApiError`）

## Linter設定
- ESLint: `@typescript-eslint/recommended`
- 最大行長: 100文字
- インデント: 2スペース
- セミコロン: 必須

## 禁止パターン
- `any` 型の使用（型推論不可能な場合のみ `unknown` を使用）
- `eval()` の使用
- `console.log()` の本番コード残存（ログライブラリを使用）

## セキュリティルール
- ユーザー入力は必ずバリデーション
- SQL クエリは必ずパラメータ化（ORM使用推奨）
- パスワードは bcrypt でハッシュ化（ソルトラウンド: 12）
```

#### 検証方法

- **L4検証**: 実装コードに対して ESLint / Prettier を実行し、警告0件を確認
- **L5検証**: セキュリティスキャンでCritical/High脆弱性0件を確認（Medium/Low許容可、理由記載必須）

### 2. 共通コンポーネント（`docs/rules/common-components.md`）

再利用可能なコンポーネント・ライブラリの設計方針と一覧。重複実装を防止し、保守性を向上。

#### 含まれる内容

| 項目 | 内容 |
|------|------|
| **UI共通コンポーネント** | Button, Input, Modal, Table等の再利用可能UI部品 |
| **ユーティリティ関数** | 日付フォーマット、文字列操作、バリデーション等 |
| **API共通処理** | HTTPクライアント、エラーハンドリング、リトライロジック |
| **状態管理** | グローバルストア、Context、カスタムフック |
| **使用方法** | 各コンポーネントのAPI、Props、使用例 |

#### 例: 共通コンポーネント一覧

```markdown
# 共通コンポーネント一覧

## UI コンポーネント

### Button
**パス**: `src/components/Button.tsx`
**Props**:
- `variant`: 'primary' | 'secondary' | 'danger'
- `size`: 'sm' | 'md' | 'lg'
- `onClick`: () => void
- `disabled`: boolean

**使用例**:
```tsx
<Button variant="primary" size="md" onClick={handleSubmit}>
  送信
</Button>
```

## ユーティリティ関数

### formatDate
**パス**: `src/utils/date.ts`
**シグネチャ**: `formatDate(date: Date, format: string): string`
**説明**: 日付を指定フォーマットで文字列化

**使用例**:
```ts
formatDate(new Date(), 'YYYY-MM-DD') // "2026-02-06"
```

## API共通処理

### apiClient
**パス**: `src/api/client.ts`
**説明**: すべてのAPI呼び出しで使用する共通HTTPクライアント。自動リトライ、エラーハンドリング、認証トークン付与を含む。

**使用例**:
```ts
const response = await apiClient.get<User>('/api/users/123')
```
```

#### 検証方法

- **L2検証**: 設計書に共通コンポーネント一覧が記載されているか確認
- **L4検証**: 実装コードで共通コンポーネントが使用され、重複実装がないか確認

### 3. テスト規約（`docs/rules/test-policy.md`）

テストの書き方、カバレッジ基準、命名規則を統一。

#### 含まれる内容

| 項目 | 内容 |
|------|------|
| **カバレッジ基準** | 単体/統合/E2Eの最低カバレッジ率 |
| **テストファイル配置** | `__tests__/` or `*.test.ts` の使い分け |
| **命名規則** | `describe`, `it` の記述パターン |
| **モック方針** | 外部API、DB、時刻のモック方法 |
| **テストデータ** | Fixture、Factory パターンの使用 |

#### 例: テスト規約

```markdown
# テスト規約

## カバレッジ基準
- **単体テスト**: 80%以上（関数・メソッドレベル）
- **統合テスト**: 60%以上（モジュール間連携）
- **E2Eテスト**: 主要ユーザーシナリオ100%カバー

## テストファイル配置
- 単体テスト: `src/**/*.test.ts`（実装ファイルと同階層）
- 統合テスト: `tests/integration/**/*.test.ts`
- E2Eテスト: `tests/e2e/**/*.test.ts`

## 命名規則
```ts
describe('UserService', () => {
  describe('getUserById', () => {
    it('should return user when ID exists', async () => {
      // Arrange
      const userId = '123'
      // Act
      const user = await userService.getUserById(userId)
      // Assert
      expect(user.id).toBe(userId)
    })

    it('should throw error when ID does not exist', async () => {
      // Arrange
      const invalidId = 'invalid'
      // Act & Assert
      await expect(userService.getUserById(invalidId)).rejects.toThrow()
    })
  })
})
```

## モック方針
- 外部API: `nock` または `msw` を使用
- DB: テストDB（Docker）を使用、各テスト後にクリーンアップ
- 時刻: `jest.useFakeTimers()` を使用
```

#### 検証方法

- **L4検証**: テスト実行し、カバレッジが基準を満たすか確認

### 4. 品質基準（`docs/rules/quality-standards.md`）

コード品質のメトリクスとレビュー基準。Lv5判定で使用。

#### 含まれる内容

| 項目 | 内容 |
|------|------|
| **コード品質メトリクス** | 循環的複雑度、認知的複雑度、重複率の上限 |
| **保守性指標** | 関数の最大行数、ファイルの最大行数、依存関係の深さ |
| **拡張性指標** | インターフェース設計、依存性注入の活用度 |
| **ドキュメント基準** | JSDoc / Docstring の必須箇所、README の記載項目 |
| **レビュー基準** | コードレビューで確認すべきチェックリスト |

#### 例: 品質基準

```markdown
# 品質基準

## コード品質メトリクス
| メトリクス | 基準値 | ツール |
|----------|-------|--------|
| 循環的複雑度（McCabe） | 10以下/関数 | ESLint complexity |
| 認知的複雑度 | 15以下/関数 | SonarQube |
| 重複率 | 3%以下 | jscpd |

## 保守性指標
- **関数の最大行数**: 50行
- **ファイルの最大行数**: 300行
- **最大ネスト深度**: 4段階
- **依存関係の深さ**: 5階層以下

## 拡張性指標
- 依存性注入パターンの活用（DIコンテナ使用）
- インターフェース分離原則の遵守
- Open/Closed原則の遵守（拡張に開き、修正に閉じる）

## ドキュメント基準
- **公開API**: JSDoc必須（説明・引数・戻り値・例外）
- **複雑なロジック**: インラインコメント必須
- **README**: セットアップ手順、使用方法、トラブルシューティング
```

#### 検証方法

- **L5検証**: SonarQube / CodeClimate等でメトリクスを測定し、Lv5判定基準を満たすか確認

### ルール制定・検証フロー

```
┌─────────────────────────────────────────────────────────────────┐
│ 【L2】設計フェーズ                                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Codex: 技術スタック確認 → ルール制定                         │ │
│ │ ・コーディング規約（ESLint/Prettier設定）                    │ │
│ │ ・共通コンポーネント設計                                     │ │
│ │ ・テスト規約（カバレッジ基準）                               │ │
│ │ ・品質基準（メトリクス上限）                                 │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ 出力: docs/rules/*.md                                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【底】実装フェーズ                                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Sonnet/Haiku: ルールに従って実装                             │ │
│ │ ・coding-rules.md を参照し命名規則・スタイル遵守             │ │
│ │ ・common-components.md を参照し共通コンポーネント使用        │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【L4】テスト検証フェーズ                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Codex: ルール準拠検証                                        │ │
│ │ ・ESLint実行 → 警告0件確認                                   │ │
│ │ ・Prettier実行 → フォーマット一致確認                        │ │
│ │ ・テストカバレッジ測定 → 基準達成確認                        │ │
│ │ ・共通コンポーネント使用率 → 重複実装検出                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ループ: 不合格 → 修正 → 再検証                                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │ 合格
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【L5】品質検証フェーズ                                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Codex: 品質基準検証（Lv5判定）                               │ │
│ │ ・SonarQube実行 → メトリクス基準達成確認                     │ │
│ │ ・循環的複雑度 ≤ 10                                          │ │
│ │ ・重複率 ≤ 3%                                                │ │
│ │ ・ドキュメント完備度 → 100%                                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ループ: 不合格 → 最適化 → 再検証                                │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Lv5達成
                      ▼
                   完成
```

### エージェントの責務分担

| エージェント | ルール制定 | ルール遵守 | ルール検証 |
|------------|----------|----------|----------|
| **Opus** | - | - | - |
| **Codex** | ◎ 制定主担当 | - | ◎ 検証主担当 |
| **Sonnet** | - | ◎ 実装時に遵守 | - |
| **Haiku** | - | ◎ 実装時に遵守 | - |

### 重要な原則

1. **ルールは早期制定**: L2設計フェーズで確定し、実装開始前に全エージェントに共有
2. **自動検証**: 人間の主観に依らず、Linter/Formatter/メトリクスツールで機械的に検証
3. **段階的厳格化**: L4で基本ルール（スタイル・カバレッジ）、L5で高度ルール（メトリクス・品質）
4. **ルール違反 = 不合格**: 検証ループで修正を強制し、妥協しない


## UI設計ワークフロー

Helixフレームワークでは、UI設計もエージェント駆動で効率化する。

### UI設計フロー

```
┌─────────────────────────────────────────────────────────────────┐
│ 【L2】UI設計フェーズ                                              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. Codex: 要件からUI要件抽出（画面一覧、遷移図）            │ │
│ │ 2. Sonnet: v0/Claude等でUIデザイン生成（ワイヤーフレーム）   │ │
│ │    ※ 人間が既存デザイン（Figma等）を持っていれば提供可能    │ │
│ │ 3. Codex: デザインからコンポーネント設計書生成              │ │
│ │ 4. Codex: デザイントークン定義（色、タイポグラフィ、間隔）   │ │
│ │ 5. 人間: 指摘があれば指摘（なければ何もしない）              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ 出力: design/ui.md, design/tokens.md, デザインファイル          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【底】UI実装フェーズ                                              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Sonnet/Haiku: Storybookでコンポーネント実装                 │ │
│ │ ・デザイントークンに従う                                     │ │
│ │ ・共通コンポーネントを優先使用                               │ │
│ │ ・アクセシビリティ対応（WCAG 2.1 AA）                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ 出力: Storybookコンポーネント、src/components/**                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【L4】UI検証フェーズ                                              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Codex: デザイン ↔ 実装の整合性検証                          │ │
│ │ ・Visual Regression Test（Chromatic/Percy）                  │ │
│ │ ・アクセシビリティ検証（axe-core）                           │ │
│ │ ・レスポンシブ検証（各ブレークポイント）                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ループ: 不合格 → 修正 → 再検証                                  │
└─────────────────────────────────────────────────────────────────┘
```

### UI設計ツール

| ツール | 用途 | Helix連携 |
|--------|------|-----------|
| **Figma** | ワイヤーフレーム・デザイン作成 | デザインURLを`design/ui.md`に記載 |
| **v0.dev** | AIベースのUI生成 | 生成コードをベースに実装 |
| **Storybook** | コンポーネントカタログ | 実装コンポーネントの可視化・テスト |
| **Chromatic** | Visual Regression Test | デザイン変更の検出 |
| **axe DevTools** | アクセシビリティ検証 | WCAG準拠チェック |

### デザイントークン定義

L2設計フェーズで定義し、実装で一貫して使用。

```typescript
// design-tokens.ts（Codexが設計書から自動生成）
export const tokens = {
  colors: {
    primary: '#3B82F6',
    secondary: '#10B981',
    error: '#EF4444',
    warning: '#F59E0B',
    background: '#FFFFFF',
    text: '#1F2937',
  },
  typography: {
    fontFamily: 'Inter, sans-serif',
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
    },
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    full: '9999px',
  },
} as const;
```


## 開発環境構築

Helixフレームワークでは、プロジェクト開始時に開発環境を自動セットアップする。

### 環境構築フロー

```
npx @ai-dev-kit/vscode init --spec docs/spec.md
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. 技術スタック検出                                               │
│    企画書から Next.js / FastAPI / PostgreSQL 等を自動検出        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. VSCode推奨拡張機能インストール                                 │
│    .vscode/extensions.json 生成 → ワークスペース推奨拡張表示      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Linter/Formatter設定                                          │
│    ESLint, Prettier, EditorConfig を技術スタックに応じて設定     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Claude Code/Codex設定                                         │
│    AGENTS.md, skills/, .claude/ を生成                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. 開発環境完成                                                   │
│    即座にHelix駆動の開発が開始可能                                │
└─────────────────────────────────────────────────────────────────┘
```

### VSCode推奨拡張機能

`.vscode/extensions.json` に以下を自動生成。技術スタックに応じて選択。

#### 必須拡張機能（全プロジェクト共通）

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **ESLint** | JavaScript/TypeScript Linter | `dbaeumer.vscode-eslint` |
| **Prettier** | コードフォーマッター | `esbenp.prettier-vscode` |
| **EditorConfig** | エディタ設定統一 | `editorconfig.editorconfig` |
| **GitLens** | Git履歴・blame表示 | `eamodio.gitlens` |
| **Error Lens** | インラインエラー表示 | `usernamehw.errorlens` |
| **Todo Tree** | TODO/FIXME一覧表示 | `gruntfuggly.todo-tree` |

#### AI開発支援

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **Cline** ★ | AIチャット統合（ファイル読込・コマンド実行） | `saoudrizwan.claude-dev` |
| **Continue** ★ | 任意のLLM接続・コードベース質問 | `Continue.continue` |
| **Cody** ★ | Sourcegraph AIペアプログラミング | `sourcegraph.cody-ai` |
| **GitHub Copilot** | AIコード補完 | `github.copilot` |
| **Codeium** | 無料AIコード補完 | `codeium.codeium` |
| **Tabnine** | コンテキスト認識AIコード補完 | `tabnine.tabnine-vscode` |

#### Frontend（React/Next.js）

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **ES7+ React Snippets** | Reactスニペット | `dsznajder.es7-react-js-snippets` |
| **Tailwind CSS IntelliSense** | Tailwind補完 | `bradlc.vscode-tailwindcss` |
| **CSS Modules** | CSSモジュール補完 | `clinyong.vscode-css-modules` |
| **Auto Rename Tag** | HTMLタグ自動リネーム | `formulahendry.auto-rename-tag` |
| **Headwind** | Tailwindクラスソート | `heybourn.headwind` |

#### Backend（Python/FastAPI）

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **Python** | Python言語サポート | `ms-python.python` |
| **Pylance** | Python型チェック・補完 | `ms-python.vscode-pylance` |
| **Black Formatter** | Pythonフォーマッター | `ms-python.black-formatter` |
| **Ruff** | 高速Python Linter | `charliermarsh.ruff` |

#### Backend（Node.js/Express/NestJS）

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **REST Client** | APIテスト | `humao.rest-client` |
| **Thunder Client** | APIテストGUI | `rangav.vscode-thunder-client` |
| **Prisma** | Prisma ORM補完 | `prisma.prisma` |

#### Database

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **SQLTools** | DBクライアント | `mtxr.sqltools` |
| **PostgreSQL** | PostgreSQL接続 | `mtxr.sqltools-driver-pg` |
| **Database Client** | マルチDB対応 | `cweijan.vscode-database-client2` |

#### デバッグ・バグ修正

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **JavaScript Debugger** | Node.js/ブラウザデバッグ（組込み拡張） | `ms-vscode.js-debug` |
| **Debug Visualizer** | 変数・データ構造の可視化 | `hediet.debug-visualizer` |
| **Console Ninja** ★ | console.log結果をコード横にインライン表示 | `WallabyJs.console-ninja` |
| **Quokka.js** ★ | ライブJS/TSスクラッチパッド（リアルタイム実行） | `WallabyJs.quokka-vscode` |
| **Turbo Console Log** | console.log自動挿入（Ctrl+Alt+L） | `chakrounanas.turbo-console-log` |
| **Pretty TypeScript Errors** ★ | TSエラーを人間が読みやすく整形 | `yoavbls.pretty-ts-errors` |
| **Bookmarks** | コード位置ブックマーク | `alefragnani.bookmarks` |
| **CodeSnap** | コードスクリーンショット（バグ報告用） | `adpyke.codesnap` |

#### Git操作・コミット管理

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **Git Graph** | Gitブランチグラフ可視化 | `mhutchie.git-graph` |
| **Git History** | ファイル・行単位の履歴表示 | `donjayamanne.githistory` |
| **Conventional Commits** ★ | コミットメッセージ規約補助（feat/fix/docs等） | `vivaxy.vscode-conventional-commits` |
| **GitHub Pull Requests** ★ | PR作成・レビュー・コメント返信 | `github.vscode-pull-request-github` |
| **GitHub Actions** ★ | CI/CDワークフロー管理・実行・デバッグ | `github.vscode-github-actions` |
| **GitLens** | Git履歴・blame・比較（必須に含む） | `eamodio.gitlens` |

#### テスト・検証

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **Wallaby.js** ★ | リアルタイムテストランナー（入力中にテスト実行） | `WallabyJs.wallaby-vscode` |
| **Jest** | Jestテストランナー | `orta.vscode-jest` |
| **Vitest** | Vitestテストランナー | `vitest.explorer` |
| **Playwright Test** | E2Eテスト実行・デバッグ | `ms-playwright.playwright` |
| **Test Explorer UI** | 汎用テストエクスプローラー | `hbenl.vscode-test-explorer` |
| **Coverage Gutters** | カバレッジ表示 | `ryanluker.vscode-coverage-gutters` |
| **SonarLint** | コード品質・脆弱性チェック | `sonarsource.sonarlint-vscode` |
| **Code Spell Checker** | スペルチェック（typo防止） | `streetsidesoftware.code-spell-checker` |

#### コンテキスト管理・効率化

AI駆動開発でのコンテキスト圧縮・トークン効率化を支援。

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **Import Cost** | インポートサイズ表示 | `wix.vscode-import-cost` |
| **Bundle Size** | バンドルサイズ表示 | `ambar.bundle-size` |
| **Code Metrics** | 関数複雑度・行数表示 | `kisstkondoros.vscode-codemetrics` |
| **Duplicate Finder** | 重複コード検出 | `paulhoughton.vscode-duplicate` |
| **Better Comments** ★ | TODO/NOTE/FIXME/AI:分類（AI指示明確化） | `aaron-bond.better-comments` |
| **Partial Diff** | 選択範囲の差分比較 | `ryu1kn.partial-diff` |
| **Quicktype** ★ | JSONから型定義自動生成 | `quicktype.quicktype` |
| **File Nesting** | ファイルツリー整理（コンテキスト削減） | 組み込み設定 |

#### コード品質・可読性

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **Indent Rainbow** ★ | インデント色分け表示 | `oderwat.indent-rainbow` |
| **Zenkaku** ★ | 全角スペース・文字検出（日本語混入防止） | `mosapride.zenkaku` |
| **TODO Highlight** | TODO/FIXMEハイライト | `wayou.vscode-todo-highlight` |
| **Indenticator** | 現在のインデントレベル表示 | `sirtori.indenticator` |
| **Markdown All in One** | Markdown編集支援（TOC生成等） | `yzhang.markdown-all-in-one` |

#### UI/デザイン

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **Figma for VS Code** | Figma連携 | `figma.figma-vscode-extension` |
| **Color Highlight** | カラーコード可視化 | `naumovs.color-highlight` |
| **SVG Preview** | SVGプレビュー | `simonsiefke.svg-preview` |
| **Image Preview** | 画像プレビュー | `kisstkondoros.vscode-gutter-preview` |

#### インフラ・DevOps

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **Docker** | Docker管理 | `ms-azuretools.vscode-docker` |
| **Dev Containers** ★ | 開発コンテナ（再現可能な環境） | `ms-vscode-remote.remote-containers` |
| **HashiCorp Terraform** ★ | IaC補完・検証 | `hashicorp.terraform` |
| **Ansible** ★ | Ansibleプレイブック補完・Lint | `redhat.ansible` |
| **YAML** | YAML補完 | `redhat.vscode-yaml` |
| **DotENV** | .env構文ハイライト | `mikestead.dotenv` |
| **Remote - SSH** | リモート開発 | `ms-vscode-remote.remote-ssh` |

#### セキュリティ

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **Aikido Security** ★ | アプリセキュリティ統合（脆弱性検出） | `AikidoSecurity.aikido` |
| **OWASP Dependency-Check** ★ | 依存関係の脆弱性スキャン | `dependency-check.dependencycheck` |
| **Threat Composer** | 脅威モデリング | `aws-samples.threat-composer` |
| **Snyk Security** | コード・依存関係セキュリティ | `snyk-security.snyk-vulnerability-scanner` |

#### ユーティリティ

| 拡張機能 | 説明 | 拡張機能ID |
|----------|------|-----------|
| **Project Manager** ★ | ワークスペース切替 | `alefragnani.project-manager` |
| **Draw.io** ★ | 図・フローチャート作成 | `hediet.vscode-drawio` |
| **Live Server** | ローカルサーバー（ホットリロード） | `ritwickdey.LiveServer` |
| **REST Client** | APIテスト（.httpファイル） | `humao.rest-client` |
| **Thunder Client** | APIテストGUI | `rangav.vscode-thunder-client` |

### extensions.json 自動生成例

```json
{
  "recommendations": [
    // 必須
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "editorconfig.editorconfig",
    "eamodio.gitlens",
    "usernamehw.errorlens",
    "gruntfuggly.todo-tree",

    // AI開発支援 ★
    "saoudrizwan.claude-dev",        // Cline
    "Continue.continue",              // Continue
    "sourcegraph.cody-ai",           // Cody
    "github.copilot",

    // デバッグ・バグ修正 ★
    "WallabyJs.console-ninja",       // Console Ninja
    "WallabyJs.quokka-vscode",       // Quokka.js
    "yoavbls.pretty-ts-errors",      // Pretty TypeScript Errors
    "hediet.debug-visualizer",
    "chakrounanas.turbo-console-log",
    "alefragnani.bookmarks",

    // Git操作・コミット管理 ★
    "mhutchie.git-graph",
    "vivaxy.vscode-conventional-commits",
    "github.vscode-pull-request-github",
    "github.vscode-github-actions",  // GitHub Actions

    // テスト・検証 ★
    "WallabyJs.wallaby-vscode",      // Wallaby.js
    "orta.vscode-jest",
    "ms-playwright.playwright",
    "ryanluker.vscode-coverage-gutters",
    "sonarsource.sonarlint-vscode",
    "streetsidesoftware.code-spell-checker",

    // コンテキスト管理・コード品質 ★
    "wix.vscode-import-cost",
    "kisstkondoros.vscode-codemetrics",
    "aaron-bond.better-comments",
    "quicktype.quicktype",           // JSONから型生成
    "oderwat.indent-rainbow",        // Indent Rainbow
    "mosapride.zenkaku",             // 全角検出

    // セキュリティ ★
    "AikidoSecurity.aikido",
    "snyk-security.snyk-vulnerability-scanner",

    // インフラ（検出時）
    "hashicorp.terraform",
    "ms-vscode-remote.remote-containers",

    // ユーティリティ ★
    "alefragnani.project-manager",
    "hediet.vscode-drawio",
    "ritwickdey.LiveServer",

    // Frontend（Next.js検出時）
    "dsznajder.es7-react-js-snippets",
    "bradlc.vscode-tailwindcss",

    // Backend（FastAPI検出時）
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",

    // Database（PostgreSQL検出時）
    "mtxr.sqltools",
    "mtxr.sqltools-driver-pg",

    // UI
    "figma.figma-vscode-extension"
  ],
  "unwantedRecommendations": []
}
```

### settings.json 自動生成例

```json
{
  // === フォーマット・Lint ===
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  },

  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  },

  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },

  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },

  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact"
  ],

  // === デバッグ設定 ===
  "debug.javascript.autoAttachFilter": "smart",
  "debug.console.fontSize": 13,
  "debug.inlineValues": "on",

  // === Git操作・コミット管理 ===
  "git.autofetch": true,
  "git.confirmSync": false,
  "git.enableSmartCommit": true,
  "git.postCommitCommand": "none",
  "gitlens.currentLine.enabled": true,
  "gitlens.hovers.currentLine.over": "line",
  "conventionalCommits.scopes": ["frontend", "backend", "api", "db", "test", "docs"],

  // === テスト・検証 ===
  "testing.automaticallyOpenPeekView": "failureVisible",
  "testing.defaultGutterClickAction": "debug",
  "sonarlint.rules": {},

  // === コンテキスト管理 ===
  "importCost.showCalculatingDecoration": true,
  "better-comments.tags": [
    { "tag": "!", "color": "#FF2D00", "backgroundColor": "transparent" },
    { "tag": "?", "color": "#3498DB", "backgroundColor": "transparent" },
    { "tag": "//", "color": "#474747", "backgroundColor": "transparent" },
    { "tag": "todo", "color": "#FF8C00", "backgroundColor": "transparent" },
    { "tag": "AI:", "color": "#98C379", "backgroundColor": "transparent" }
  ],

  // === ファイルネスト（コンテキスト圧縮） ===
  "explorer.fileNesting.enabled": true,
  "explorer.fileNesting.patterns": {
    "*.ts": "${capture}.js, ${capture}.d.ts, ${capture}.test.ts, ${capture}.spec.ts",
    "*.tsx": "${capture}.test.tsx, ${capture}.spec.tsx, ${capture}.stories.tsx",
    "package.json": "package-lock.json, yarn.lock, pnpm-lock.yaml, .npmrc",
    ".env": ".env.*, .env.local, .env.development, .env.production"
  },

  // === Tailwind（Frontend検出時） ===
  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascript"
  },

  "files.associations": {
    "*.css": "tailwindcss"
  }
}
```

### launch.json 自動生成例（デバッグ設定）

```json
{
  "version": "0.2.0",
  "configurations": [
    // === Node.js（Backend）===
    {
      "type": "node",
      "request": "launch",
      "name": "Debug: Node.js",
      "program": "${workspaceFolder}/src/index.ts",
      "preLaunchTask": "npm: build",
      "outFiles": ["${workspaceFolder}/dist/**/*.js"],
      "console": "integratedTerminal"
    },
    // === Next.js（Frontend）===
    {
      "type": "node",
      "request": "launch",
      "name": "Debug: Next.js",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "serverReadyAction": {
        "pattern": "ready on",
        "uriFormat": "http://localhost:3000",
        "action": "debugWithChrome"
      }
    },
    // === Jest（テスト）===
    {
      "type": "node",
      "request": "launch",
      "name": "Debug: Jest Current File",
      "program": "${workspaceFolder}/node_modules/.bin/jest",
      "args": ["${relativeFile}", "--runInBand", "--no-coverage"],
      "console": "integratedTerminal",
      "internalConsoleOptions": "neverOpen"
    },
    // === Python/FastAPI ===
    {
      "type": "debugpy",
      "request": "launch",
      "name": "Debug: FastAPI",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--port", "8000"],
      "cwd": "${workspaceFolder}/backend",
      "console": "integratedTerminal"
    },
    // === Playwright（E2E）===
    {
      "type": "node",
      "request": "launch",
      "name": "Debug: Playwright",
      "program": "${workspaceFolder}/node_modules/.bin/playwright",
      "args": ["test", "--debug"],
      "console": "integratedTerminal"
    }
  ],
  "compounds": [
    {
      "name": "Debug: Full Stack",
      "configurations": ["Debug: FastAPI", "Debug: Next.js"]
    }
  ]
}
```

### tasks.json 自動生成例（タスク定義）

```json
{
  "version": "2.0.0",
  "tasks": [
    // === ビルド ===
    {
      "type": "npm",
      "script": "build",
      "label": "npm: build",
      "group": "build",
      "problemMatcher": ["$tsc"]
    },
    // === テスト ===
    {
      "type": "npm",
      "script": "test",
      "label": "npm: test",
      "group": "test",
      "problemMatcher": []
    },
    {
      "type": "npm",
      "script": "test:watch",
      "label": "npm: test:watch",
      "isBackground": true,
      "problemMatcher": []
    },
    // === Lint・フォーマット ===
    {
      "type": "npm",
      "script": "lint",
      "label": "npm: lint",
      "problemMatcher": ["$eslint-stylish"]
    },
    {
      "type": "npm",
      "script": "lint:fix",
      "label": "npm: lint:fix",
      "problemMatcher": ["$eslint-stylish"]
    },
    // === 型チェック ===
    {
      "type": "npm",
      "script": "typecheck",
      "label": "npm: typecheck",
      "problemMatcher": ["$tsc"]
    },
    // === Helix検証（カスタム）===
    {
      "label": "Helix: L2.5 API整合性検証",
      "type": "shell",
      "command": "npx openapi-typescript-codegen --input api-contract.yaml --output src/types/api && npm run typecheck",
      "problemMatcher": ["$tsc"],
      "group": "test"
    },
    {
      "label": "Helix: L4 全テスト実行",
      "type": "shell",
      "command": "npm run test && npm run test:e2e",
      "problemMatcher": [],
      "group": "test"
    },
    // === Git操作 ===
    {
      "label": "Git: Conventional Commit",
      "type": "shell",
      "command": "npx git-cz",
      "problemMatcher": []
    }
  ]
}
```

### プロジェクト構成（環境構築追加版）

```
project/
├── .vscode/
│   ├── extensions.json         # 推奨拡張機能（自動生成） ★
│   ├── settings.json           # エディタ設定（自動生成） ★
│   ├── launch.json             # デバッグ設定（自動生成） ★
│   └── tasks.json              # タスク・検証定義（自動生成） ★
├── .claude/
│   ├── agents/                 # サブエージェント定義
│   └── settings.local.json     # 権限設定
├── CLAUDE.md                   # オーケストレーター指示
├── skills/                     # スキル定義
├── docs/
│   ├── design/
│   │   ├── ui.md               # UI設計（画面一覧、コンポーネント設計） ★
│   │   └── tokens.md           # デザイントークン定義 ★
│   └── ...
├── .storybook/                 # Storybook設定 ★
├── design-tokens.ts            # デザイントークン（TypeScript） ★
├── .eslintrc.js                # ESLint設定（自動生成）
├── .prettierrc                 # Prettier設定（自動生成）
├── .editorconfig               # EditorConfig（自動生成）
└── package.json
```

---

## 運用ポリシー（Helix Policy）

**Opus × Codex 議論により合意された運用規約**

### 前提

```yaml
premises:
  human_role: "planning_and_review_only"  # 企画と指摘のみ
  agent_autonomy: "full_execution"         # 自律実行
  human_interventions_allowed:
    - stop              # 止める
    - direction_change  # 方向修正
```

---

### 1. 粒度不足の判定基準（granularity_insufficiency）

決定・提案が粗すぎる場合の判定基準。スコア2以上で「粒度不足」と判定。

```yaml
granularity_insufficiency:
  insufficient_if_any:
    - id: G1
      description: "1つの決定に独立した変更単位が2件以上含まれる"
      score: 2
    - id: G2
      description: "成果物が特定不能（対象ファイル・機能・範囲が未記載）"
      score: 1
    - id: G3
      description: "成功条件/受入条件が未記載"
      score: 1
    - id: G4
      description: "影響範囲の記載が抽象的"
      score: 1
    - id: G5
      description: "技術理由が列挙されていない"
      score: 1

  insufficient_threshold: 2

  auto_action_on_insufficient:
    - split_decision
    - request_missing_fields
    - set_status: "needs_refinement"
```

---

### 2. 暫定決定の重大度別期限（provisional_decision_ttl）

企画書に明記されていない判断は「暫定決定」として進行し、期限後に自動確定。

```yaml
provisional_decision_ttl:
  levels:
    critical:
      ttl: "24h"
      review_deadline: "6h"
      expiry_action:
        - auto_stop_if_unreviewed
        - escalate_to_human

    high:
      ttl: "72h"
      review_deadline: "24h"
      expiry_action:
        - pause_execution
        - notify_human

    medium:
      ttl: "7d"
      review_deadline: "72h"
      expiry_action:
        - require_direction_change_or_confirm

    low:
      ttl: "30d"
      review_deadline: "7d"
      expiry_action:
        - auto_archive_with_notice

  default_severity: "medium"
  log_requirement: "all_provisional_decisions_must_be_logged"
```

---

### 3. 技術理由リストの変更プロセス（technical_rationale_registry）

例外承認に使用できる「技術的理由」の追加・変更プロセス。

```yaml
technical_rationale_registry:
  registry_path: ".claude/memory/tech-rationales.yaml"

  allowed_reasons:  # 事前承認済み（自動承認可能）
    - timezone_conversion: "フロントエンドでのタイムゾーン変換"
    - serialization: "JSON文字列へのシリアライズ"
    - normalization: "DB正規化による構造差異"
    - dto_transformation: "表示用DTOへの変換"

  change_process:
    steps:
      - id: T1
        name: "proposal"
        required_fields:
          - rationale_id
          - title
          - description
          - evidence
          - impact_assessment

      - id: T2
        name: "agent_validation"
        checks:
          - duplicate_id_check
          - conflicts_with_decisions_check

      - id: T3
        name: "cooling_period"
        duration: "24h"
        auto_apply_if_no_stop: true

      - id: T4
        name: "apply_and_log"
        log_to: ".claude/memory/decisions.md"

  conflict_rule:
    if_conflicts_with:
      - decisions_md
      - constraints_md
    action:
      - halt_change
      - request_human_direction_change
```

---

### 4. 監査の責任者・対応SLA（audit_policy）

RACI定義と対応時間のSLA。

```yaml
audit_policy:
  responsibility:  # RACI
    accountable: "agent:helix-auditor"
    responsible: "agent:task-owner"
    consulted: "agent:secondary-reviewer"
    informed: "human:project-owner"

  sla:
    triggers:
      - decision_conflict
      - critical_degradation
      - provisional_expiry

    response_times:
      critical: "1h"
      high: "4h"
      medium: "24h"
      low: "72h"

  escalation:
    if_no_progress_over:
      critical: "2h"
      high: "8h"
      medium: "48h"
      low: "5d"
    action:
      - notify_human
      - recommend_stop_or_direction_change
```

---

### 5. 劣化レベルとSLOの対応表（degradation_to_slo_map）

品質劣化の段階別定義と対応アクション。

```yaml
degradation_to_slo_map:
  slo_metrics:
    - availability
    - p95_latency_ms
    - error_rate_percent
    - task_success_rate_percent
    - cost_overrun_percent

  levels:
    none:
      thresholds:
        availability: ">=99.9%"
        p95_latency_ms: "<=200"
        error_rate_percent: "<=0.5"
        task_success_rate_percent: ">=98.0"
        cost_overrun_percent: "<=5"
      required_action: "continue"

    low:
      thresholds:
        availability: ">=99.5%"
        p95_latency_ms: "<=400"
        error_rate_percent: "<=1.0"
        task_success_rate_percent: ">=97.0"
        cost_overrun_percent: "<=10"
      required_action: "optimize_in_next_cycle"

    medium:
      thresholds:
        availability: ">=99.0%"
        p95_latency_ms: "<=800"
        error_rate_percent: "<=2.0"
        task_success_rate_percent: ">=95.0"
        cost_overrun_percent: "<=20"
      required_action:
        - initiate_investigation
        - apply_mitigations

    high:
      thresholds:
        availability: ">=98.0%"
        p95_latency_ms: "<=1500"
        error_rate_percent: "<=5.0"
        task_success_rate_percent: ">=90.0"
        cost_overrun_percent: "<=35"
      required_action:
        - immediate_mitigation
        - consider_rollback
        - notify_human

    critical:
      thresholds:
        availability: "<98.0%"
        p95_latency_ms: ">1500"
        error_rate_percent: ">5.0"
        task_success_rate_percent: "<90.0"
        cost_overrun_percent: ">35"
      required_action:
        - auto_stop
        - rollback_if_safe
        - notify_human_immediately
```

---

### 6. 決定ログの保管・権限方針（decision_log_policy）

決定の記録・保管・アクセス制御。

**注意: 本ポリシーは decisions.md 内の「決定ログ」セクションのみに適用。他セクションの権限は別途定義。**

```yaml
decision_log_policy:
  # 適用範囲（重要）
  scope:
    file: ".claude/memory/decisions.md"
    section: "決定ログ（エージェント追記可）"  # このセクションのみに適用
    other_sections:
      - name: "変更禁止（人間承認済み）"
        policy: "human_only"  # 人間のみ変更可
      - name: "条件付き変更可"
        policy: "agent_with_condition"  # 条件満たせばエージェント可
      - name: "AI判断（人間未承認）"
        policy: "agent_append_only"  # エージェント追記のみ

  storage:
    primary: ".claude/memory/decisions.md#決定ログ"
    secondary: ".claude/memory/decisions.yaml"
    retention:
      type: "indefinite"
      archive_after: "365d"

  integrity:
    mode: "append_only"  # 「決定ログ」セクションのみ追記限定
    checksum: "sha256"
    tamper_detection: true

  permissions:
    read:
      - agent:all
      - human:project-owner
    write:
      - agent:task-owner
      - agent:helix-auditor
    human_write_allowed_for:
      - stop
      - direction_change

  log_schema:
    required_fields:
      - id
      - status
      - severity
      - decision
      - rationale_ids
      - timestamp
      - author
      - review_deadline
      - expiry_action
```

---

### 7. 緊急時の一時権限委譲（emergency_override）

人間が応答できない緊急時のエージェント権限拡大。

**責任との整合（responsibility_chain参照）:**
- 通常時: 例外承認 = human:project-owner（指摘として）
- 緊急時: exception_approval がエージェントに一時委譲
- 事後: 必ず人間による事後承認が必要（post_incident_review）
- 責任: 緊急時判断の責任は agent:task-owner が負い、事後報告必須

```yaml
emergency_override:
  temporary_delegation:
    trigger_conditions:
      - human_unavailable_over: "4h"
      - critical_incident_in_progress: true
      - sla_breach_imminent: true

    delegated_powers:
      - provisional_decision_to_blocking: "暫定決定を即座に確定可能"
      - exception_approval: "技術理由例外の自動承認範囲拡大"
      - scope_reduction: "スコープ縮小の自律決定"

    restrictions:
      - cannot_modify: "decisions.md の変更禁止セクション"
      - cannot_approve: "cost > budget * 2"
      - cannot_affect: "production_data"

    duration: "until_human_responds OR max_24h"

    logging:
      - all_delegated_actions_logged
      - notification_sent_immediately
      - post_incident_review_required

    # 事後承認フロー（責任追跡）
    post_incident_review:
      required: true
      deadline: "72h after human response"
      reviewer: "human:project-owner"
      actions:
        - validate_delegated_decisions
        - approve_or_rollback
        - update_accountability_log
      if_not_approved:
        - rollback_decisions
        - log_as_unauthorized

  audit_delay_fallback:
    trigger: "audit_sla_breach"

    fallback_actions:
      critical:
        - auto_pause_execution
        - notify_all_stakeholders
        - create_incident_record

      high:
        - continue_with_enhanced_logging
        - retry_audit_in: "1h"
        - escalate_if_retry_fails

      medium_low:
        - continue_execution
        - schedule_async_audit
        - flag_for_human_review_in_next_cycle

    recovery:
      when_audit_resumes:
        - retroactive_audit_required
        - gap_analysis_report
        - remediation_if_violations_found
```

---

### 8. 合意形成の最終責任主体（responsibility_chain）

誰が何を決め、誰が最終責任を負うか。

```yaml
responsibility_chain:
  decision_authority:
    levels:
      - id: L1
        authority: "human:project-owner"
        scope: "stop, direction_change"
        binding: true
        override_possible_by: null  # 最終権限

      - id: L2
        authority: "agent:helix-auditor"
        scope: "compliance, security, consistency"
        binding: true
        override_possible_by: "human:project-owner"

      - id: L3
        authority: "agent:task-owner"
        scope: "implementation_details, technical_decisions"
        binding: false  # 暫定決定として
        override_possible_by: "agent:helix-auditor, human:project-owner"

  conflict_resolution:
    between_agents:
      rule: "helix-auditor wins"
      escalation: "if_auditor_uncertain → human"

    between_human_and_agent:
      rule: "human always wins"
      logging: "human_override_logged"

    no_response_from_human:
      rule: "エージェントは暫定決定で進行"
      conditions:
        - must_be_reversible
        - must_not_affect_production_data
        - must_log_all_decisions

  final_accountability:
    table:
      - domain: "品質基準の定義"
        accountable: "human:project-owner（企画書で定義）"
      - domain: "品質基準への準拠"
        accountable: "agent:task-owner"
      - domain: "準拠の監査"
        accountable: "agent:helix-auditor"
      - domain: "例外承認"
        accountable: "human:project-owner（指摘として）"
      - domain: "緊急時の自律判断"
        accountable: "agent:task-owner（事後報告必須）"
      - domain: "本番障害"
        accountable: "ルール定義者(human) vs ルール遵守者(agent)で切り分け"

    accountability_log:
      path: ".claude/memory/accountability.md"
      fields:
        - decision_id
        - accountable_party
        - timestamp
        - outcome
        - post_review_result
```

---

### 運用ポリシーの適用

```yaml
policy_application:
  location: "helix/operations/policy.yaml"

  loading:
    - always_load: ["premises", "responsibility_chain"]
    - phase_specific:
        planning: ["granularity_insufficiency"]
        implementation: ["provisional_decision_ttl", "technical_rationale_registry"]
        verification: ["audit_policy", "degradation_to_slo_map"]
        incident: ["emergency_override"]

  validation:
    on_startup: true
    on_decision: true
    periodic: "daily"
```

---

## AI Adversarial Review サイクル

> 単一AIの判断は盲点を持つ。複数AIによる批判的検証で決定品質を上げる。

**要約版（常時参照）:**
```yaml
ai_adversarial_review:
  principle: "Propose → Collide → Challenge → Decide"
  when: "本番影響あり / ロールバック1h超 / 外部説明責任あり"
  independence: "議長と提案者を分離、異なるモデル、同一プロンプト"
  arbitration: "倫理 > リスク > 可逆性 > ビジネス価値"
  record: ".claude/memory/decisions/"
  skill: "skills/workflow/adversarial-review/SKILL.md"
```

<details>
<summary>草案（Opus × Codex 徹底合意済み）</summary>

```yaml
# === AI Adversarial Review サイクル ===
# 設計判断における複数AI検証の原則

ai_adversarial_review:
  purpose: "意思決定の質と説明責任の担保"

  principle: |
    単一AIの判断は盲点を持つ。
    複数AIによる批判的検証で決定品質を上げる。

  # --- 適用条件（閾値定義済み） ---
  applicability:
    judge: "owner（人間 or helix-auditor）"
    timing: "判断開始前に適用可否を決定"
    criteria:
      required:
        - "本番環境への影響がある"
        - "ロールバックに1時間以上かかる"
        - "外部（顧客・監査）への説明責任がある"
      skip:
        - "開発環境のみ＆5分で戻せる"
        - "既存ルールの機械的適用"

  # --- 独立性（具体ルール） ---
  independence:
    structural_requirements:
      - "異なるモデルプロバイダ（Anthropic/OpenAI）を使用"
      - "評価軸を2つ以上定義してから開始"
      - "proposer同士は結論を共有しない"
      - "議長（coordinator）と提案者（proposer）は分離"
      - "議長が提案者を兼ねる場合、別インスタンスを起動"
      - "両提案者へのプロンプトは同一文面"
      - "評価軸は議論開始前に固定・公開"
    optional_enhancements:
      - "要約係を議長から分離"
      - "二重ブラインド化（モデル種別を伏せる）"
      - "プロンプト凍結（途中変更不可）"
    conflict_of_interest:
      - "自分が書いたコードのレビューは別AIが担当"
    audit:
      - "プロンプト/要約/裁定の全文ログを保管"
      - "第三者が追跡可能な形式で記録"

  # --- サイクル（アウトプット定義済み） ---
  core_cycle:
    1_propose:
      action: "各AIが独立して案を作成"
      output: "提案書（案＋根拠＋前提）"
      responsible: "proposers"
    2_collide:
      action: "差異・前提・評価軸を特定"
      output: "差異表（同意点/相違点/理由）"
      responsible: "owner"
    3_challenge:
      action: "暫定結論への批判的検証"
      output: "批判リスト（指摘＋代替案）"
      responsible: "adversarial_reviewer"
    4_decide:
      action: "決定＋反対意見を記録"
      output: "決定書（結論＋反対意見＋根拠）"
      responsible: "owner"
    extension:
      condition: "批判により修正が発生した場合"
      action: "3→4を繰り返す（最大3回）"

  # --- 裁定基準（優先順位定義済み） ---
  arbitration:
    priority_order:
      1: "倫理基準（法令・規約違反は絶対NG）"
      2: "リスク最小化（被害規模を優先）"
      3: "可逆性（戻せる選択肢を優先）"
      4: "ビジネス価値（同等なら価値が高い方）"
    conflict_resolution: "上位基準が優先"

  # --- 記録要件 ---
  record:
    minimum_fields:
      - "decision_id"
      - "decision_summary"
      - "dissent_summary"
      - "arbitration_basis（裁定理由）"
      - "timestamp"
    retention: "1年以上保管"
    location: ".claude/memory/decisions/"

  # --- 検証フィードバック ---
  validation_loop:
    external: "実データ・専門家レビュー"
    feedback: "検証結果は次回入力"
    learning: "失敗パターン→anti_patternsに追加"

  # --- 緊急時（ガードレール詳細） ---
  emergency:
    condition:
      - "障害対応など即時判断が必要"
      - "判断が24時間以内に可逆"
    guardrails:
      post_review: "24時間以内に事後レビュー実施"
      monthly_audit: "月次で例外適用を集計"
      escalation:
        trigger: "月3回超の例外適用"
        action: "プロセス改善会議を開催"
```

</details>

---
plan_id: PLAN-047
title: 'PLAN-047（DS-120 デジタル・ガバメント推進標準ガイドライン実践ガイドブックの HELIX 取り込み）'
status: completed
completed: 2026-05-10
created: 2026-05-10
author: 'Docs (Codex)'
priority: medium
size: L
phases_affected: L1, L2, L3, L6, L8, L9, L10, L11
parent_plan: PLAN-046
acceptance:
  ds120_p0_integration:
    verification_commands:
      command: "for w in 1 2 3 4; do git log --oneline | grep -c \"plan-047.*W-$w\"; done | awk '$1>=1' | wc -l"
      expected: "4"
  ds120_p1_integration:
    verification_commands:
      command: "git log --oneline | grep -c 'plan-047.*W-5'"
      expected: "1 以上"
  mapping_table_published:
    verification_commands:
      command: "ls docs/reference/ds120-mapping.md 2>/dev/null | wc -l"
      expected: "1"
  tests_all_pass:
    verification_commands:
      command: "cli/helix test"
      expected: "exit 0 / 0 failed"
  branch_minimal_footprint:
    verification_commands:
      command: "git branch --list 'improvements/plan-047*' | wc -l"
      expected: "0"
---

# PLAN-047: DS-120 HELIX 取り込み統合計画

## §1 背景

DS-120 は、デジタル・ガバメント推進標準ガイドライン実践ガイドブックとして、
要件定義、調達、設計、品質確保、運用までを横断して参照できる実務指針を含む。
注記: ガイドライン群名は「デジタル社会推進標準ガイドライン群」へ変更済 (旧称「デジタル・ガバメント推進標準ガイドライン群」)。本文中は旧称併記する。
HELIX 側では、既存の L1-L11 の工程表・テンプレート・受入定義に対して、
DS-120 の章立てをそのまま移植するのではなく、各章の実務要点を
既存の工程構造へマッピングする必要がある。

本 PLAN は、DS-120 を HELIX に取り込む際の統合方針を固定し、
W-1 から W-final までの作業単位を明確にするための土台である。
特に、P0 領域は設計の正本として強制力を持たせ、
P1 領域は運用整備として補完的に進める。

## 参照元情報の固定 (本 PLAN scope の根拠)

- **公式 URL**: https://www.digital.go.jp/resources/standard_guidelines#ds120
- **DS-120 本文**: 2025-06-19 更新版
- **テンプレート**: 2025-10-06 更新版
- **位置づけ**: Informative (参考文書、強制ルール化対象外)
- **固定理由**: 章 mapping とテンプレート反映の正確性保証
- **公式名称変更注記**: ガイドライン群名は「デジタル社会推進標準ガイドライン群」に変更 (旧称「デジタル・ガバメント推進標準ガイドライン群」)、政府内部手続文書は旧称継続

## §2 解消対象

本 PLAN で解消する課題は次のとおり。

1. DS-120 の章構成を HELIX のどのレイヤーに接続するかが曖昧である。
2. L1 要件定義、L2 ADR、L3 工程表、L6 品質、L8 受入の各テンプレートに
   どのレベルまで DS-120 を反映するかが未確定である。
3. 運用章の反映対象が分散しており、L9-L11 への適用単位が不明確である。
4. mapping table の公式版が未整備で、後続タスクの参照点が弱い。
5. 変更範囲が広いため、並列実施時の責務境界と依存順序を固定する必要がある。

この PLAN は、章ごとの解釈差を減らし、後続の文書実装を「どこまで書くか」で
迷わせないことを狙う。

## §3 PLAN 構成

### §3.1 W-pre

W-pre は、PLAN-047 の前提整理と mapping 仮説の確定フェーズである。
既知 mapping にある `ds120_chapters_count: 10`、`helix_mapping_count: 17`
を前提として、各章の主たる着地点を以下に整理する。

- P0: 要件、調達仕様、ADR、品質確保・受入
- P1: 運用、保守、改善
- P2: 補助参照、補足ガイド、横断索引

W-pre の完了条件は、W-1〜W-6 の実装順を崩さずに進められるだけの
章別マッピングが確定していることである。

### §3.2 W-0

W-0 は、PLAN 本体の初期化・整形・参照基盤整備である。
ここでは DS-120 の章番号、HELIX のレイヤー、既存 docs の相互参照をまとめ、
後続の実装でブレない参照名を定義する。

W-0 の主な成果物は次のとおり。

- 本 PLAN の frontmatter 確定
- DS-120 章別マッピングの一次ラベル整理
- 後続文書で使用する用語統一
- 参照リンクの初期点検

W-0 は実装範囲を増やす作業ではなく、後続 W-1〜W-6 を通すための
前処理として扱う。

### §3.3 W-1 (P0): L1 要件定義テンプレート補強

W-1 は DS-120 第5章を起点として、L1 要件定義テンプレートに
次の観点を補強する。

- D-REQ-F: 機能要件の粒度
- D-REQ-NF: 非機能要件の明示
- D-ACC: 受入条件の定義

重点は、要件を「書く」ことではなく、受入可能な粒度に落とし込むことにある。
曖昧な表現を残さず、検証可能な記述へ変換する。

### §3.4 W-2 (P0): L3 調達仕様書 → API/DB/工程表 補強

W-2 は DS-120 第6章を起点として、L3 の調達仕様書から
API 契約、DB 設計、WBS への落とし込みを補強する。

重点対象は次のとおり。

- API 契約: 入出力、責務、エラー
- DB 設計: データ保持、整合性、変更影響
- 工程表: Sprint 分解、依存順、受入条件

W-2 の成果は、仕様と工程の分離ではなく、仕様から工程へ自然に接続できる
記述形式を定義することにある。

### §3.5 W-3 (P0): L2 ADR + リスク管理

W-3 は、DS-120 から抽出した意思決定材料を L2 ADR に反映し、
同時にリスク管理の観点を整える。

想定する出力は以下である。

- ADR の決定理由と代替案の明記
- 章別リスクの分類
- 変更判断の根拠の追跡可能化

このタスクでは、なぜその方針を採るのかが文書から読み取れることを重視する。

### §3.6 W-4 (P0): L6 品質確保 + L8 受入 checklist

W-4 は、DS-120 の品質確保要点を HELIX の L6 と L8 に接続する。

対象は次のとおり。

- 品質観点のチェック項目化
- 受入 checklist の判定基準明確化
- 重要な抜け漏れの早期発見

W-4 は P0 の締めとして機能し、後続の運用整備に対して
「合格の定義」を固定する。

### §3.7 W-5 (P1): L9-L11 運用

W-5 は、DS-120 の運用・保守・改善に相当する章を L9-L11 に反映する。
あわせて DS-120 第10章のシステム監査の扱いも W-5 に統合し、SLO/SLI と
監査ログ requirements を運用観点へ接続する。

ここでは、運用手順、改訂フロー、定常確認の位置づけを整える。
単なる記載追加ではなく、実運用で参照される粒度を意識して書く。

W-5 の完了条件は、運用参照の入口が 1 か所以上明確化されることである。

### §3.8 W-6 (P1-P2): mapping table 公式版

W-6 は、`docs/reference/ds120-mapping.md` を公式 mapping table として刊行する。
これは後続の差分管理、レビュー、横断参照の基準点になる。

W-6 では以下を固定する。

- 章番号と HELIX レイヤーの対応
- P0/P1/P2 の分類根拠
- 代表的な参照先
- 迷いやすい境界の注記

mapping table は、他の W が先に完了していることを前提に最終確定する。

### §3.9 W-final

W-final は統合検証、retro、必要なら push 準備を行う最終工程である。

実施項目は以下。

- 本 PLAN の全節の整合確認
- 参照リンクの再検証
- 未解決項目の残存確認
- 回顧メモの整理

W-final の目的は、文書としての完成度を確認し、後続の実装にそのまま渡せる状態にすることである。

## §4 並列性

W-1 から W-5 は、依存が少ない範囲で並列に進められる。

| W | depends_on | reason | allowed_files |
|---|------------|--------|---------------|
| W-1 | (none) | L1 要件定義独立 | skills/workflow/requirements-handover/SKILL.md, cli/templates/D-REQ-F/, cli/templates/D-REQ-NF/, cli/templates/D-ACC/ |
| W-2 | (none) | L3 詳細設計独立 | skills/workflow/api-contract/SKILL.md, skills/common/db/SKILL.md, skills/workflow/schedule-wbs/SKILL.md |
| W-3 | (none) | L2 ADR 独立 | skills/workflow/design-doc/SKILL.md, skills/workflow/design-doc/references/ |
| W-4 | (none) | L6/L8 独立 | skills/workflow/quality-lv5/SKILL.md, skills/workflow/verification/SKILL.md |
| W-5 | (none) | L9-L11 独立 | skills/workflow/observability-sre/SKILL.md, skills/workflow/incident/SKILL.md, skills/workflow/postmortem/SKILL.md |
| W-6 | W-1〜W-5 | mapping table は他完了後 | docs/reference/ds120-mapping.md (新規) |
| W-final | W-1〜W-6 | 統合検証 + push | docs/plans/PLAN-047*.md, .helix/retros/PLAN-047.md |

- W-1 と W-3 は、要件と ADR の観点が分かれているため並列可
- W-2 は W-1 の表現を参照する部分があるが、一次案の段階では並列可
- W-4 は W-1〜W-3 の出力を前提にするため、後追い統合が安全
- W-5 は運用章の整理であり、依存表どおり並列に進められる
- W-6 は mapping table の公式版であるため、他の完了内容を集約した後に実施する
- W-final は W-1〜W-6 の完了後に統合し、必要なら push 準備まで行う

並列性を最大化しつつ、公式表や受入定義は最後に固定する。

## §5 受入条件

本 PLAN の受入条件は以下である。

1. W-1〜W-4 により P0 の統合が完了している。
2. W-5 により P1 の運用整備が 1 件以上反映されている。
3. W-6 により mapping table の公式版が公開されている。
4. 本 PLAN の参照リンクに破綻がない。
5. PLAN-047 で変更した `skills/workflow/*` + `docs/reference/ds120-mapping.md` に TODO/FIXME 残存なし。
6. 変更差分が PLAN-047 に必要な範囲へ収まっている。

受入は「書かれていること」だけでなく、「後続が使えること」を基準にする。

## §6 Risks

### §6.1 章解釈のぶれ

DS-120 の章解釈が広すぎると、L1 から L11 への割当が曖昧になる。
対策として、章ごとの主担当レイヤーを先に固定する。

### §6.2 文書量の肥大化

反映対象を広げすぎると、各文書が冗長になる。
対策として、各 W に「何を追加しないか」を暗黙でなく明示する。

### §6.3 参照リンクの崩れ

新規の mapping table 追加時に相対リンクの誤記が起きやすい。
対策として、最終工程でリンク整合を必ず点検する。

### §6.4 受入基準の曖昧化

受入 checklist が抽象的だと、L8 で判定不能になる。
対策として、判定語を定義し、可否の根拠を明文化する。

### §6.5 並列作業の競合

W-1〜W-5 を並列に進めると、同じ章番号や用語を別表現で書く恐れがある。
対策として、W-pre と W-0 で用語と参照名を固定する。

### §6.6 DS-120 原文の未取得

DS-120 PDF 未取得状態で着手すると、章番号やテンプレート差分がずれる。
対策として、各 W で WebFetch または手動 download を行い、必要に応じて
`HELIX_ALLOW_OPUS_PLAN_FIX` 環境変数で Opus 直接 fetch を許容する。

### §6.7 Codex 使用量の逼迫

Codex usage limit に達した場合、primary fail の後に `--role se` → `--role pg` → `--role docs`
の fallback role を使って別枠を活用する。

### §6.8 AI-native 不適合の判断

政府テンプレが手動前提で AI-native に不適合と判断される場合は、
HELIX の強制ルール化を避けて注記化し、各 Sprint 内で個別判断する。
Informative 位置づけに従い、適用可否を文書に残す。

## §7 関連

### §7.1 関連 PLAN

- PLAN-046: 直前の runtime quality 系統
- PLAN-047: 本計画
- 後続の実装計画: W-1〜W-final の個別タスク

### §7.2 参照文書

- `docs/reference/ds120-mapping.md`
- `docs/plans/PLAN-046-runtime-quality.md`
- `skills/SKILL_MAP.md`
- `helix/HELIX_CORE.md`

### §7.3 運用ノート

本 PLAN はドラフトとして開始し、W-1〜W-6 の進行に合わせて
節内の表現を更新する。
仕様が固まるまでは、個別文書に先行して断定的な表現を増やさない。

### §7.4 実装時の注意

- 章番号の表記ゆれを作らない
- P0/P1/P2 の区分を混ぜない
- mapping table を他文書の副産物にしない
- 保留項目を残す場合は理由を明示する
- `helix plan import --from-frontmatter --dry-run` で frontmatter 統合を点検する

### §7.5 後続確認項目

- 参照先が存在するか
- 相対リンクが正しいか
- 章とレイヤーの対応が一貫しているか
- 最終文言に未確定表現が残っていないか

### §7.6 更新履歴

- 2026-05-10: PLAN-047 ドラフトを新規作成
- 2026-05-10: W-pre / W-0 / W-1〜W-6 / W-final を整理
- 2026-05-10: 受入条件と Risks を明文化

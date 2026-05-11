---
plan_id: PLAN-064
title: "PLAN-064（helix asset CLI: 画像生成 preset コマンド）"
status: finalized
created: 2026-05-12
author: "PM (Opus)"
priority: medium
size: S
phases_affected: "cli/helix-asset (新規) / cli/templates/assets/ (新規 7 preset) / cli/lib/tests/test_helix_asset.bats (新規)"
parent_plan: PLAN-063
acceptance:
  cli_routing:
    verification_commands: { command: "cli/helix asset --help", expected: "7 preset (banner/logo/hero/card/thumb/icon/bg) が --help に表示" }
  one_shot_generation:
    verification_commands: { command: "cli/helix asset banner --motif test --out /tmp/test-banner.png", expected: "exit 0、1200x400 PNG が /tmp/test-banner.png に生成される" }
  preset_consistency:
    verification_commands: { command: "ls cli/templates/assets/ | wc -l", expected: "7 (banner.md / logo.md / hero.md / card.md / thumb.md / icon.md / bg.md)" }
  test_coverage:
    verification_commands: { command: "bats cli/tests/test-helix-asset.bats", expected: "全 PASS (mock codex で preset 解決 + prompt 注入確認)" }
finalized: 2026-05-11
---

# PLAN-064: helix asset CLI — 画像生成 preset コマンド

## §1 背景

PLAN-063 W-1 で Codex image-gen capability (gpt-5.4-mini 経由) を実証。
docs/assets/helix-banner.png 1200×400 を 1 ターンで生成成功。

これを再利用可能な preset CLI 化することで:
- FE pipeline (PLAN-063 memory) の Stage 2 (mockup) / Stage 6 (production asset) を CLI 化
- 開発時の画像 asset を Codex 内で完結 (外部 API ゼロ)
- preset prompt template により品質の再現性確保

## §2 仕様

### CLI

```bash
cli/helix asset <preset> [opts]

Presets:
  banner   1200×400  GitHub README / OG banner
  logo     512×512   brand mark
  hero     1920×1080 LP hero section
  card     800×600   service / feature card
  thumb    1200×630  blog / article thumbnail (OG)
  icon     256×256   UI icon set
  bg       1920×1080 background pattern (tileable)

Common options:
  --style <minimal|tech|playful|corp>  base style (default: minimal)
  --palette <hex,hex,hex>              color palette
  --motif <text>                       motif description (free text)
  --text <text>                        text overlay
  --out <path>                         output path (default: docs/assets/<preset>-<timestamp>.png)
  --variants N                         generate N variants (default: 1)
  --model <model>                      override model (default: gpt-5.4-mini)
  --dry-run                            show resolved prompt without invoking codex
```

### 内部実装

- `cli/helix-asset` (bash wrapper、~100 行):
  - 引数 parse + preset 解決
  - prompt template (`cli/templates/assets/<preset>.md`) を読み込み、option を変数展開で注入
  - `helix codex --role pg --thinking low --task "<resolved prompt>"` を呼び出し
  - 出力 PNG path を summary で報告

- `cli/templates/assets/<preset>.md` 7 ファイル: preset ごとの base prompt template。`{{motif}}` / `{{text}}` / `{{style}}` / `{{palette}}` プレースホルダー

- `cli/lib/tests/test-helix-asset.bats` (新規):
  - `--help` 出力に 7 preset 全表示
  - 各 preset で `--dry-run` 実行、resolved prompt が template + option を正しく組合せる
  - mock codex で生成 stub PNG が指定 path に書き出される
  - `--variants 3` で 3 ファイル生成

## §3 Sprint 構成 (4 Sprint、size=S)

| Sprint | 内容 | 委譲先 |
|---|---|---|
| W-0 | draft + TL Round 1 + finalize | PM |
| W-1 | cli/helix-asset bash wrapper + 引数 parse + dry-run | PG low |
| W-2 | 7 preset template (cli/templates/assets/*.md) | docs / PG low |
| W-3 | bats test + integration confirmation (mock codex) | PG low |
| W-final | 統合検証 + retro + push | Opus |

W-1 と W-2 は並列可能 (異なるファイル群)。W-3 は両者完了後。

## §4 Out of Scope

- 画像編集 / レタッチ (Codex 出力をそのまま採用)
- 動画 / アニメーション (still image のみ)
- AI 強化アップスケーリング (resolution は preset で固定)
- A/B 自動評価 (variants 出力後の選定は Opus or 人間判断)

## §5 リスク

- **画像生成 tool の挙動変化**: gpt-5.4-mini の image-gen 仕様変更で preset prompt の効果低下 → preset template に version pin + リグレッション fixture
- **prompt injection**: `--motif <text>` の自由テキストが prompt 構造を破壊 → 改行 / 制御文字を escape + 長さ制限 (256 chars)
- **生成失敗時の fallback**: 1 回目 fail で再試行最大 2 回、すべて失敗なら exit 1 + 明示 error
- **cost**: gpt-5.4-mini は安価だが、`--variants 10` のような大量生成は monthly budget 監視必要 → `--variants` max=8 で hard limit

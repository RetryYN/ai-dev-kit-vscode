#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const SKILLS_DIR = path.join(PACKAGE_ROOT, 'skills');

// スキルカテゴリ定義
const SKILL_CATEGORIES = {
  common: {
    name: '共通スキル',
    description: '全プロジェクトで使用',
    skills: [
      'coding', 'testing', 'git', 'error-fix', 'design', 'refactoring',
      'security', 'infrastructure', 'performance', 'documentation', 'code-review'
    ]
  },
  workflow: {
    name: 'ワークフロー',
    description: '開発プロセス',
    skills: [
      'design-doc', 'dev-setup', 'project-management', 'dev-policy',
      'estimation', 'deploy', 'incident'
    ]
  },
  tools: {
    name: 'ツール',
    description: '開発ツール活用',
    skills: ['ide-tools', 'vscode-plugins', 'ai-coding']
  },
  advanced: {
    name: '上級',
    description: '高度なトピック',
    skills: [
      'ai-integration', 'tech-selection', 'external-api',
      'migration', 'legacy', 'i18n'
    ]
  },
  project: {
    name: 'プロジェクト',
    description: 'プロジェクト固有設定',
    skills: ['architecture', 'api', 'db', 'ui']
  },
  integration: {
    name: '連携',
    description: 'エージェント連携',
    skills: ['codex', 'orchestrator']
  }
};

// 技術スタック検出パターン
const TECH_PATTERNS = {
  frontend: {
    'Next.js': /next\.?js|next\s*14|next\s*15/i,
    'React': /react(?!\s*native)/i,
    'Vue.js': /vue\.?js|vue\s*3/i,
    'Svelte': /svelte/i,
    'Angular': /angular/i,
    'TypeScript': /typescript|\.tsx?/i,
  },
  backend: {
    'FastAPI': /fastapi/i,
    'Django': /django/i,
    'Flask': /flask/i,
    'Express': /express\.?js|express/i,
    'NestJS': /nest\.?js/i,
    'Go': /golang|go\s+lang/i,
    'Rust': /rust/i,
    'Node.js': /node\.?js/i,
    'Python': /python\s*3?\.\d+|python/i,
  },
  database: {
    'PostgreSQL': /postgres(?:ql)?|psql/i,
    'MySQL': /mysql/i,
    'MongoDB': /mongo(?:db)?/i,
    'Redis': /redis/i,
    'SQLite': /sqlite/i,
    'DynamoDB': /dynamodb/i,
    'Supabase': /supabase/i,
    'Firebase': /firebase|firestore/i,
  },
  infra: {
    'Docker': /docker/i,
    'Kubernetes': /kubernetes|k8s/i,
    'AWS': /aws|amazon\s*web/i,
    'GCP': /gcp|google\s*cloud/i,
    'Azure': /azure/i,
    'Vercel': /vercel/i,
    'Cloudflare': /cloudflare/i,
  },
  auth: {
    'JWT': /jwt|json\s*web\s*token/i,
    'OAuth': /oauth/i,
    'Clerk': /clerk/i,
    'Auth0': /auth0/i,
    'NextAuth': /next-?auth/i,
  }
};

// エージェント構成
const AGENT_CONFIGS = {
  'claude-only': {
    name: 'Claude Codeのみ',
    agents: ['claude'],
    description: 'Claude Code単体で使用'
  },
  'codex-only': {
    name: 'Codexのみ',
    agents: ['codex'],
    description: 'Codex単体で使用'
  },
  'claude-codex': {
    name: 'Claude Code + Codex（推奨）',
    agents: ['claude', 'codex'],
    description: 'Claude Codeをメインに、Codexをレビュー・リファクタに活用'
  }
};

// コマンドライン引数解析
const args = process.argv.slice(2);
const command = args[0];
const flags = args.slice(1);

// ユーティリティ: プロンプト入力
function prompt(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  
  return new Promise(resolve => {
    rl.question(question, answer => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

// ユーティリティ: 選択入力
async function select(question, options) {
  console.log(question);
  options.forEach((opt, i) => {
    const marker = i === 0 ? '❯' : ' ';
    console.log(`  ${marker} ${i + 1}. ${opt.name}${opt.recommended ? ' (推奨)' : ''}`);
    if (opt.description) {
      console.log(`       ${opt.description}`);
    }
  });
  
  const answer = await prompt('\n選択 (1-' + options.length + '): ');
  const index = parseInt(answer, 10) - 1;
  
  if (index >= 0 && index < options.length) {
    return options[index];
  }
  return options[0]; // デフォルト
}

// ヘルプ表示
function showHelp() {
  console.log(`
@ai-dev-kit/vscode - VSCode用 AI開発環境セットアップCLI

使い方:
  npx @ai-dev-kit/vscode <command> [options]

コマンド:
  init              開発環境を初期化（対話式）
  init --quick      開発環境を初期化（推奨設定で即座に）
  init --spec <file>  企画書から開発環境を自動生成 ★
  sync-agents       CLAUDE.md → AGENTS.md を同期
  list              スキル一覧を表示
  path              スキルディレクトリのパスを表示

オプション:
  -h, --help        ヘルプを表示
  -v, --version     バージョンを表示
  -f, --force       既存ファイルを上書き
  --spec <file>     企画書ファイルを指定してカスタムAGENTS.mdを生成

例:
  npx @ai-dev-kit/vscode init
  npx @ai-dev-kit/vscode init --quick
  npx @ai-dev-kit/vscode init --spec docs/spec.md  # 企画書から自動生成
  npx @ai-dev-kit/vscode sync-agents
  npx @ai-dev-kit/vscode list

★ --spec オプション（差別化機能）:
  企画書のMarkdownを解析して、プロジェクト固有のAGENTS.mdを自動生成。
  - 技術スタック自動検出（Next.js, FastAPI, PostgreSQL等）
  - API設計の抽出
  - 機能要件の抽出
  - ディレクトリ構成の推定
`);
}

// バージョン表示
function showVersion() {
  const pkg = require('../package.json');
  console.log(pkg.version);
}

// スキル一覧表示
function listSkills() {
  console.log('\n📚 ai-dev-kit Skills 一覧\n');
  console.log('='.repeat(60));
  
  for (const [category, info] of Object.entries(SKILL_CATEGORIES)) {
    console.log(`\n## ${info.name} (${category}/)`);
    console.log(`   ${info.description}`);
    console.log('');
    
    for (const skill of info.skills) {
      const skillPath = path.join(SKILLS_DIR, category, skill, 'SKILL.md');
      const exists = fs.existsSync(skillPath);
      const status = exists ? '✅' : '⬜';
      console.log(`   ${status} ${skill}`);
    }
  }
  
  console.log('\n' + '='.repeat(60));
  console.log(`\n📁 スキルパス: ${SKILLS_DIR}`);
  console.log('');
}

// スキルパス表示
function showPath() {
  console.log(SKILLS_DIR);
}

// シンボリックリンク作成（クロスプラットフォーム）
function createSymlink(target, linkPath) {
  const linkDir = path.dirname(linkPath);
  if (!fs.existsSync(linkDir)) {
    fs.mkdirSync(linkDir, { recursive: true });
  }
  
  // 相対パスに変換
  const relativeTarget = path.relative(linkDir, target);
  
  try {
    // 既存リンク/ファイルがあれば削除
    if (fs.existsSync(linkPath) || fs.lstatSync(linkPath).isSymbolicLink()) {
      fs.unlinkSync(linkPath);
    }
  } catch (e) {
    // ファイルが存在しない場合は無視
  }
  
  fs.symlinkSync(relativeTarget, linkPath);
  return true;
}

// ディレクトリコピー（シンボリックリンクが使えない場合のフォールバック）
function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

// .agent/skills/ にスキルをコピー
function copySkillsToAgent(projectRoot) {
  const agentSkillsDir = path.join(projectRoot, '.agent', 'skills');
  
  // .agent/skills/ ディレクトリ作成
  fs.mkdirSync(agentSkillsDir, { recursive: true });
  
  // 各カテゴリのスキルをコピー
  for (const [category, info] of Object.entries(SKILL_CATEGORIES)) {
    for (const skill of info.skills) {
      const srcPath = path.join(SKILLS_DIR, category, skill);
      const destPath = path.join(agentSkillsDir, skill);
      
      if (fs.existsSync(srcPath)) {
        copyDir(srcPath, destPath);
      }
    }
  }
  
  return agentSkillsDir;
}

// シンボリックリンク構造を生成
function createSymlinkStructure(projectRoot, agents) {
  const agentSkillsDir = path.join(projectRoot, '.agent', 'skills');
  
  // .agent/skills/ にスキルをコピー
  copySkillsToAgent(projectRoot);
  
  // 各エージェント用のシンボリックリンク作成
  if (agents.includes('claude')) {
    const claudeSkillsLink = path.join(projectRoot, '.claude', 'skills');
    try {
      createSymlink(agentSkillsDir, claudeSkillsLink);
      console.log('  ✅ .claude/skills -> .agent/skills');
    } catch (e) {
      // シンボリックリンクが作れない場合はコピー
      copyDir(agentSkillsDir, claudeSkillsLink);
      console.log('  ✅ .claude/skills (コピー)');
    }
  }
  
  if (agents.includes('codex')) {
    const codexSkillsLink = path.join(projectRoot, '.codex', 'skills');
    try {
      createSymlink(agentSkillsDir, codexSkillsLink);
      console.log('  ✅ .codex/skills -> .agent/skills');
    } catch (e) {
      copyDir(agentSkillsDir, codexSkillsLink);
      console.log('  ✅ .codex/skills (コピー)');
    }
  }
}

// AGENTS.md テンプレート生成
function generateAgentsMd(projectName) {
  return `# ${projectName || 'プロジェクト名'}

## 概要
<!-- このプロジェクトの目的を1-2行で記載 -->

## 技術スタック
| レイヤー | 技術 |
|----------|------|
| Frontend | Next.js 14 / React / TypeScript |
| Backend | FastAPI / Python 3.12 |
| DB | PostgreSQL 16 |
| Infra | Docker / AWS ECS |

## ディレクトリ構成
\`\`\`
src/
├── app/           # Next.js App Router
├── components/    # UIコンポーネント
├── lib/           # 共通ユーティリティ
├── api/           # APIクライアント
└── types/         # 型定義

backend/
├── app/
│   ├── api/       # エンドポイント
│   ├── models/    # SQLAlchemyモデル
│   └── services/  # ビジネスロジック
└── tests/
\`\`\`

## コマンド
\`\`\`bash
# 開発
npm run dev          # フロント開発サーバー
uvicorn app.main:app --reload  # バックエンド

# テスト
npm run test         # フロントテスト
pytest tests/ -v     # バックエンドテスト

# ビルド・デプロイ
npm run build        # プロダクションビルド
npm run lint         # Lint実行
\`\`\`

## ワークフロー
1. **ブランチ作成**: \`git checkout -b feature/xxx\`
2. **実装**: 小さな差分で進める（200行以下推奨）
3. **テスト**: 変更に対応するテストを追加
4. **PR作成**: Conventional Commitsでコミット

## Rules（常時適用）

### コーディング
- TypeScript strict: true
- any禁止 → unknown + 型ガード
- 関数は単一責任、引数3つまで

### Git
- Conventional Commits: feat/fix/docs/refactor/test/chore
- ブランチ: feature/xxx, fix/xxx, hotfix/xxx

### 禁止事項
- console.log コミット禁止
- シークレットのハードコード禁止
- eslint-disable の乱用禁止

## 注意点（Gotchas）
<!-- プロジェクト固有の注意点を記載 -->
- 認証: JWT、24時間で期限切れ
- API: /api/v1 プレフィックス必須

## 詳細ドキュメント
以下のファイルを必要に応じて参照:
- docs/spec-template.md - 企画書テンプレート
- .agent/skills/ - 33スキル（タスクに応じて自動ロード）

Codex連携: "Use codex to review this PR" で品質レビューを委譲可能。
`;
}

// 企画書を解析して構造化データを抽出
function parseSpec(specContent) {
  const result = {
    projectName: '',
    overview: '',
    techStack: {
      frontend: [],
      backend: [],
      database: [],
      infra: [],
      auth: []
    },
    apis: [],
    dataModels: [],
    directories: [],
    requirements: [],
    phases: []
  };

  // プロジェクト名抽出（# で始まる最初の行）
  const titleMatch = specContent.match(/^#\s+(.+?)(?:\n|$)/m);
  if (titleMatch) {
    result.projectName = titleMatch[1].replace(/機能企画書[:：]\s*/, '').trim();
  }

  // 概要抽出
  const overviewMatch = specContent.match(/##\s*(?:概要|目的|Overview)[\s\S]*?(?:###\s*(?:目的|ゴール)[\s\S]*?)?([\s\S]*?)(?=\n##|\n---|\z)/i);
  if (overviewMatch) {
    result.overview = overviewMatch[1].replace(/<!--.*?-->/g, '').trim().slice(0, 200);
  }

  // 技術スタック検出
  for (const [category, patterns] of Object.entries(TECH_PATTERNS)) {
    for (const [techName, pattern] of Object.entries(patterns)) {
      if (pattern.test(specContent)) {
        result.techStack[category].push(techName);
      }
    }
  }

  // API設計抽出（テーブル形式）
  const apiTableMatch = specContent.match(/\|\s*Method\s*\|\s*Endpoint[\s\S]*?(?=\n\n|\n##|\n---)/i);
  if (apiTableMatch) {
    const apiLines = apiTableMatch[0].split('\n').filter(line => line.includes('|') && !line.includes('---'));
    apiLines.slice(1).forEach(line => {
      const parts = line.split('|').filter(p => p.trim());
      if (parts.length >= 2) {
        result.apis.push({
          method: parts[0].trim(),
          endpoint: parts[1].trim(),
          description: parts[2] ? parts[2].trim() : ''
        });
      }
    });
  }

  // データモデル抽出（SQLテーブル定義）
  const sqlMatches = specContent.matchAll(/CREATE\s+TABLE\s+(\w+)/gi);
  for (const match of sqlMatches) {
    result.dataModels.push(match[1]);
  }

  // ディレクトリ構成抽出
  const dirMatch = specContent.match(/```[\s\S]*?((?:src|app|backend|frontend)\/[\s\S]*?)```/);
  if (dirMatch) {
    result.directories = dirMatch[1].split('\n')
      .filter(line => line.includes('/') || line.includes('├') || line.includes('└'))
      .map(line => line.replace(/[├└│─\s]+/g, '').trim())
      .filter(line => line);
  }

  // 機能要件抽出
  const reqMatch = specContent.match(/###?\s*機能要件[\s\S]*?((?:\d+\.\s+.+\n?)+)/i);
  if (reqMatch) {
    result.requirements = reqMatch[1].split('\n')
      .filter(line => /^\d+\./.test(line.trim()))
      .map(line => line.replace(/^\d+\.\s*/, '').trim())
      .filter(line => line);
  }

  // フェーズ抽出
  const phaseMatches = specContent.matchAll(/###?\s*フェーズ\s*\d+[：:]\s*(.+)/gi);
  for (const match of phaseMatches) {
    result.phases.push(match[1].trim());
  }

  return result;
}

// 解析結果からカスタムAGENTS.mdを生成
function generateCustomAgentsMd(projectName, specData) {
  const { techStack, apis, dataModels, requirements, overview, phases } = specData;

  // 技術スタックの整形
  const techStackTable = [
    ['Frontend', techStack.frontend.length > 0 ? techStack.frontend.join(' / ') : 'TBD'],
    ['Backend', techStack.backend.length > 0 ? techStack.backend.join(' / ') : 'TBD'],
    ['DB', techStack.database.length > 0 ? techStack.database.join(' / ') : 'TBD'],
    ['Infra', techStack.infra.length > 0 ? techStack.infra.join(' / ') : 'TBD'],
    ['Auth', techStack.auth.length > 0 ? techStack.auth.join(' / ') : '-']
  ];

  // ディレクトリ構成の推定
  let dirStructure = '';
  if (techStack.frontend.includes('Next.js')) {
    dirStructure = `src/
├── app/           # Next.js App Router
├── components/    # UIコンポーネント
├── lib/           # 共通ユーティリティ
└── types/         # 型定義`;
  } else if (techStack.frontend.includes('React')) {
    dirStructure = `src/
├── components/    # UIコンポーネント
├── hooks/         # カスタムフック
├── pages/         # ページコンポーネント
└── utils/         # ユーティリティ`;
  }

  if (techStack.backend.includes('FastAPI') || techStack.backend.includes('Python')) {
    dirStructure += `

backend/
├── app/
│   ├── api/       # エンドポイント
│   ├── models/    # データモデル
│   └── services/  # ビジネスロジック
└── tests/`;
  } else if (techStack.backend.includes('Express') || techStack.backend.includes('NestJS')) {
    dirStructure += `

server/
├── src/
│   ├── controllers/
│   ├── services/
│   └── models/
└── tests/`;
  }

  // コマンドの推定
  let commands = '';
  if (techStack.frontend.some(t => ['Next.js', 'React', 'Vue.js'].includes(t))) {
    commands += `# 開発
npm run dev          # フロント開発サーバー
`;
  }
  if (techStack.backend.includes('FastAPI')) {
    commands += `uvicorn app.main:app --reload  # バックエンド
`;
  } else if (techStack.backend.includes('Express') || techStack.backend.includes('NestJS')) {
    commands += `npm run dev:server   # バックエンド
`;
  }
  commands += `
# テスト
npm run test         # フロントテスト
${techStack.backend.includes('FastAPI') ? 'pytest tests/ -v     # バックエンドテスト' : 'npm run test:server  # バックエンドテスト'}

# ビルド
npm run build        # プロダクションビルド
npm run lint         # Lint実行`;

  // API設計セクション
  let apiSection = '';
  if (apis.length > 0) {
    apiSection = `

## API設計（企画書より）
| Method | Endpoint | 説明 |
|--------|----------|------|
${apis.map(api => `| ${api.method} | ${api.endpoint} | ${api.description} |`).join('\n')}`;
  }

  // データモデルセクション
  let dataModelSection = '';
  if (dataModels.length > 0) {
    dataModelSection = `

## データモデル
テーブル: ${dataModels.join(', ')}`;
  }

  // 機能要件セクション
  let requirementsSection = '';
  if (requirements.length > 0) {
    requirementsSection = `

## 実装予定機能（企画書より）
${requirements.map((r, i) => `${i + 1}. ${r}`).join('\n')}`;
  }

  return `# ${projectName || specData.projectName || 'プロジェクト名'}

## 概要
${overview || '<!-- 企画書の目的を転記 -->'}

## 技術スタック
| レイヤー | 技術 |
|----------|------|
${techStackTable.map(([layer, tech]) => `| ${layer} | ${tech} |`).join('\n')}

## ディレクトリ構成
\`\`\`
${dirStructure || 'TBD - 技術スタック確定後に設定'}
\`\`\`

## コマンド
\`\`\`bash
${commands}
\`\`\`
${apiSection}${dataModelSection}${requirementsSection}

## ワークフロー
1. **ブランチ作成**: \`git checkout -b feature/xxx\`
2. **実装**: 小さな差分で進める（200行以下推奨）
3. **テスト**: 変更に対応するテストを追加
4. **PR作成**: Conventional Commitsでコミット

## Rules（常時適用）

### コーディング
- TypeScript strict: true
- any禁止 → unknown + 型ガード
- 関数は単一責任、引数3つまで

### Git
- Conventional Commits: feat/fix/docs/refactor/test/chore
- ブランチ: feature/xxx, fix/xxx, hotfix/xxx

### 禁止事項
- console.log コミット禁止
- シークレットのハードコード禁止
- eslint-disable の乱用禁止

## 詳細ドキュメント
以下のファイルを必要に応じて参照:
- docs/spec.md - 元の企画書
- .agent/skills/ - 33スキル（タスクに応じて自動ロード）

Codex連携: "Use codex to review this PR" で品質レビューを委譲可能。
`;
}

// VSCode設定生成
function generateVSCodeSettings() {
  return {
    "chat.useClaudeSkills": true
  };
}

// CLAUDE.md → AGENTS.md 同期
function syncAgentsMd() {
  const projectRoot = process.cwd();
  const claudeMdPath = path.join(projectRoot, 'CLAUDE.md');
  const agentsMdPath = path.join(projectRoot, 'AGENTS.md');
  
  if (!fs.existsSync(claudeMdPath)) {
    console.error('❌ CLAUDE.md が見つかりません。');
    console.error('   先に npx @ai-dev-kit/vscode init を実行してください。');
    process.exit(1);
  }
  
  // CLAUDE.md の内容を読み込み
  const claudeContent = fs.readFileSync(claudeMdPath, 'utf-8');
  
  // AGENTS.md として出力（Claude Code固有の記述があれば変換）
  let agentsContent = claudeContent;
  
  // Claude Code固有のパスをCodex形式に変換
  agentsContent = agentsContent.replace(/\.claude\/skills/g, '.agent/skills');
  agentsContent = agentsContent.replace(/@\.claude/g, '.agent');
  
  fs.writeFileSync(agentsMdPath, agentsContent);
  
  console.log('✅ AGENTS.md を同期しました。');
  console.log('');
  console.log('生成されたファイル:');
  console.log(`  - ${agentsMdPath}`);
}

// 初期化（対話式）
async function init(options = {}) {
  const projectRoot = process.cwd();
  const projectName = path.basename(projectRoot);
  
  console.log('\n🚀 ai-dev-kit VSCode セットアップ\n');
  console.log('=' .repeat(50));
  
  // 企画書解析（--spec オプション）
  let specData = null;
  if (options.spec) {
    const specPath = path.resolve(projectRoot, options.spec);
    if (!fs.existsSync(specPath)) {
      console.error(`❌ 企画書が見つかりません: ${specPath}`);
      process.exit(1);
    }
    
    console.log(`\n📄 企画書を解析中: ${options.spec}`);
    const specContent = fs.readFileSync(specPath, 'utf-8');
    specData = parseSpec(specContent);
    
    console.log('\n検出された技術スタック:');
    for (const [category, techs] of Object.entries(specData.techStack)) {
      if (techs.length > 0) {
        console.log(`  ${category}: ${techs.join(', ')}`);
      }
    }
    if (specData.apis.length > 0) {
      console.log(`\n検出されたAPI: ${specData.apis.length}件`);
    }
    if (specData.requirements.length > 0) {
      console.log(`検出された機能要件: ${specData.requirements.length}件`);
    }
    
    // 企画書をdocs/にコピー
    const docsDir = path.join(projectRoot, 'docs');
    fs.mkdirSync(docsDir, { recursive: true });
    const destSpecPath = path.join(docsDir, 'spec.md');
    fs.copyFileSync(specPath, destSpecPath);
    console.log(`\n  ✅ docs/spec.md (企画書コピー)`);
  }
  
  let agentConfig;
  
  if (options.quick || options.spec) {
    // クイックモード or specモード: 推奨設定を使用
    agentConfig = AGENT_CONFIGS['claude-codex'];
    console.log(`\nエージェント構成: ${agentConfig.name}`);
  } else {
    // 対話モード
    const configOptions = Object.entries(AGENT_CONFIGS).map(([key, config]) => ({
      key,
      name: config.name,
      description: config.description,
      recommended: key === 'claude-codex'
    }));
    
    const selected = await select('\nエージェント構成を選択:', configOptions);
    agentConfig = AGENT_CONFIGS[selected.key];
  }
  
  console.log('\n📁 ファイル生成中...\n');
  
  // 1. .agent/skills/ にスキルをコピー
  console.log('Skills構造を生成中...');
  createSymlinkStructure(projectRoot, agentConfig.agents);
  
  // 2. AGENTS.md 生成（企画書があればカスタム生成）
  const agentsMdPath = path.join(projectRoot, 'AGENTS.md');
  if (!fs.existsSync(agentsMdPath) || options.force || options.spec) {
    let agentsMd;
    if (specData) {
      agentsMd = generateCustomAgentsMd(projectName, specData);
      console.log('  ✅ AGENTS.md (企画書から自動生成)');
    } else {
      agentsMd = generateAgentsMd(projectName);
      console.log('  ✅ AGENTS.md');
    }
    fs.writeFileSync(agentsMdPath, agentsMd);
  } else {
    console.log('  ⏭️  AGENTS.md (既存)');
  }
  
  // 3. CLAUDE.md シンボリックリンク（Claude Code使用時）
  if (agentConfig.agents.includes('claude')) {
    const claudeMdPath = path.join(projectRoot, 'CLAUDE.md');
    try {
      createSymlink(agentsMdPath, claudeMdPath);
      console.log('  ✅ CLAUDE.md -> AGENTS.md');
    } catch (e) {
      // シンボリックリンクが作れない場合はコピー
      fs.copyFileSync(agentsMdPath, claudeMdPath);
      console.log('  ✅ CLAUDE.md (コピー)');
    }
  }
  
  // 4. .vscode/settings.json
  const vscodeDir = path.join(projectRoot, '.vscode');
  const vscodeSettingsPath = path.join(vscodeDir, 'settings.json');
  fs.mkdirSync(vscodeDir, { recursive: true });
  
  let vscodeSettings = {};
  if (fs.existsSync(vscodeSettingsPath)) {
    try {
      vscodeSettings = JSON.parse(fs.readFileSync(vscodeSettingsPath, 'utf-8'));
    } catch (e) {
      // JSONパースエラーは無視
    }
  }
  
  // Claude Skills設定を追加
  vscodeSettings = { ...vscodeSettings, ...generateVSCodeSettings() };
  fs.writeFileSync(vscodeSettingsPath, JSON.stringify(vscodeSettings, null, 2));
  console.log('  ✅ .vscode/settings.json');
  
  // 5. docs/spec-template.md
  const docsDir = path.join(projectRoot, 'docs');
  const specTemplatePath = path.join(docsDir, 'spec-template.md');
  fs.mkdirSync(docsDir, { recursive: true });
  
  if (!fs.existsSync(specTemplatePath) || options.force) {
    const specTemplate = generateSpecTemplate();
    fs.writeFileSync(specTemplatePath, specTemplate);
    console.log('  ✅ docs/spec-template.md');
  } else {
    console.log('  ⏭️  docs/spec-template.md (既存)');
  }
  
  console.log('\n' + '='.repeat(50));
  console.log('\n✨ セットアップ完了!\n');
  
  console.log('生成された構造:');
  console.log(`
${projectName}/
├── .agent/
│   └── skills/           # Skills実体
├── .claude/
│   └── skills -> ../.agent/skills
${agentConfig.agents.includes('codex') ? '├── .codex/\n│   └── skills -> ../.agent/skills\n' : ''}├── .vscode/
│   └── settings.json
├── AGENTS.md             # 実体
├── CLAUDE.md -> AGENTS.md
└── docs/
    └── spec-template.md
`);
  
  console.log('次のステップ:');
  console.log('  1. AGENTS.md の「プロジェクト概要」を編集');
  console.log('  2. 技術スタックを実際の構成に更新');
  if (agentConfig.agents.includes('codex')) {
    console.log('  3. Codex連携: "Use codex to review this PR" で自動委譲');
  }
  console.log('');
}

// 企画書テンプレート生成
function generateSpecTemplate() {
  return `# 機能企画書: [機能名]

## 概要

### 目的
<!-- この機能が解決する課題 -->

### ゴール
<!-- 達成したい状態 -->

---

## 要件

### 機能要件
1. 
2. 
3. 

### 非機能要件
- パフォーマンス: 
- セキュリティ: 
- 可用性: 

---

## 技術仕様

### アーキテクチャ
\`\`\`
[図を記載]
\`\`\`

### データモデル
\`\`\`sql
-- テーブル定義
\`\`\`

### API設計
| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | /api/xxx | |
| POST | /api/xxx | |

---

## 実装計画

### フェーズ1: 基盤
- [ ] タスク1
- [ ] タスク2

### フェーズ2: 機能実装
- [ ] タスク3
- [ ] タスク4

### フェーズ3: テスト・リリース
- [ ] タスク5
- [ ] タスク6

---

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| | | |

---

## 備考

<!-- その他の注意事項 -->
`;
}

// オプション解析
function parseOptions(flags) {
  const options = {
    force: false,
    quick: false,
    spec: null
  };
  
  for (let i = 0; i < flags.length; i++) {
    const flag = flags[i];
    if (flag === '-f' || flag === '--force') {
      options.force = true;
    } else if (flag === '--quick') {
      options.quick = true;
    } else if (flag === '--spec') {
      // 次の引数がファイルパス
      options.spec = flags[i + 1];
      i++;
    } else if (flag.startsWith('--spec=')) {
      options.spec = flag.replace('--spec=', '');
    }
  }
  
  return options;
}

// メイン処理
async function main() {
  if (!command || command === '-h' || command === '--help') {
    showHelp();
    return;
  }
  
  if (command === '-v' || command === '--version') {
    showVersion();
    return;
  }
  
  switch (command) {
    case 'init':
      const options = parseOptions(flags);
      await init(options);
      break;
      
    case 'sync-agents':
      syncAgentsMd();
      break;
      
    case 'list':
      listSkills();
      break;
      
    case 'path':
      showPath();
      break;
      
    default:
      console.error(`❌ 不明なコマンド: ${command}`);
      console.error('   npx @ai-dev-kit/vscode --help でヘルプを表示');
      process.exit(1);
  }
}

main().catch(err => {
  console.error('エラー:', err.message);
  process.exit(1);
});

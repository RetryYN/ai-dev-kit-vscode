/**
 * @ai-dev-kit/vscode
 * VSCode用 AI開発環境セットアップキット
 */

const path = require('path');

const SKILLS_DIR = path.join(__dirname, 'skills');

const SKILL_CATEGORIES = {
  common: [
    'coding', 'testing', 'git', 'error-fix', 'design', 'refactoring',
    'security', 'infrastructure', 'performance', 'documentation', 'code-review'
  ],
  workflow: [
    'design-doc', 'dev-setup', 'project-management', 'dev-policy',
    'estimation', 'deploy', 'incident'
  ],
  tools: ['ide-tools', 'vscode-plugins', 'ai-coding'],
  advanced: [
    'ai-integration', 'tech-selection', 'external-api',
    'migration', 'legacy', 'i18n'
  ],
  project: ['architecture', 'api', 'db', 'ui'],
  integration: ['codex', 'orchestrator']
};

module.exports = {
  SKILLS_DIR,
  SKILL_CATEGORIES,
  
  /**
   * スキルパスを取得
   * @param {string} category - カテゴリ名
   * @param {string} skill - スキル名
   * @returns {string} スキルのフルパス
   */
  getSkillPath(category, skill) {
    return path.join(SKILLS_DIR, category, skill, 'SKILL.md');
  },
  
  /**
   * 全スキル一覧を取得
   * @returns {Array<{category: string, skill: string, path: string}>}
   */
  getAllSkills() {
    const skills = [];
    for (const [category, skillList] of Object.entries(SKILL_CATEGORIES)) {
      for (const skill of skillList) {
        skills.push({
          category,
          skill,
          path: this.getSkillPath(category, skill)
        });
      }
    }
    return skills;
  }
};

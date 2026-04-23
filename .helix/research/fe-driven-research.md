# FE駆動/モック駆動開発の GitHub 実例調査

調査日: 2026-04-21 | 対象: OSS リポジトリ、ツール類のモック→API契約導出パターン

---

## 1. FE駆動/モック駆動を採用する OSS リポジトリ

### 1.1 Storybook Design System (2K+ ⭐)
**URL**: https://github.com/storybookjs/design-system  
**スター**: 2,000+  

**構造の特徴**:
- **React + Storybook** で UI component 設計と documented catalog を一元管理
- **Emotion** でコンポーネントスコープの CSS-in-JS
- **Chromatic** での visual regression testing で design contract をカバー
- **CircleCI** で CI/CD 統合

**モック↔本実装の分離**:
Design System は公開 NPM パッケージとして配布。Consumer はコンポーネントの **story (mockup) で全variations を確認**→本実装と同じコンポーネントを import。Storybook がすべてのバリエーションを catalog 化することで、API を暗黙に contract として機能させる。

**HELIX への示唆**: Storybook stories そのものが「設計駆動」の artifact。Phase L2(visual-design) で mock.html + stories を同時成果物化できる。debt は「本実装とstoryが乖離」→「storyを参照」で低減。

---

### 1.2 Mock Service Worker (MSW) - 公式リポジトリ (15K+ ⭐)
**URL**: https://github.com/mswjs/msw  
**スター**: 15,000+  

**構造の特徴**:
- `/src` — Core intercept algorithm
- `/browser` — Service Worker integration  
- `/node` — Node.js integration (setupServer)
- Mock handler の **定義と infrastructure の完全分離**

**モック↔本実装の分離**:
Developers は `setupWorker()` / `setupServer()` で handler を **宣言的に定義**し、実装の Service Worker / Node interception は MSW が吸収。同じ handler コードが dev / test / debug で機能 → **handler自体が contract**になる。

**重要**: MSW ハンドラーは TypeScript で型安全に定義可能。API の req/res contract がアプリコードと分離されたファイルにある。

**HELIX への示唆**: Phase L3 で `mock-handlers.ts` を生成し、tRPC/OpenAPI schema で型チェック。Phase L4 で本 API endpoint を実装時、handler と endpoint の型を sync するアクション。debt: handler の deprecated endpoint は自動 linting。

---

### 1.3 devmock-client (Lightweight Mock Backend)
**URL**: https://github.com/huynamboz/devmock-client  

**特徴**:
- FE developer が data model を定義 → mock DB + mock API を自動生成
- Real REST API を call する準備ができるまで mock で進める
- Mock と本実装の **temporal separation** (時間で切り替え)

**HELIX への示唆**: L4 前半で devmock-client style の mock data + endpoint を生成。L4 後半で本 API と swap。Git branch で切り替える運用も可。

---

## 2. モック → API 契約導出ツールの実運用例

### 2.1 tRPC + Zod (TypeScript Type-Driven)
**URL**: https://trpc.io/ | **Examples repo**: https://github.com/trpc/trpc  
**採用例**: `khayyam90/trpc-zod`, `ndraaditiya/Next-tRPC-Zod`

**パターン**:
```typescript
// BE: Zod schema + tRPC procedure で contract を定義
export const createPost = publicProcedure
  .input(z.object({ title: z.string(), body: z.string() }))
  .mutation(async ({ input }) => {
    // Prisma + DB logic
  });

// FE: 同じ型定義で完全型安全 (API call 不要)
const result = trpc.createPost.useMutation({ ... });
```

**モック→契約の流れ**:
1. **L2(Design)**: Zod schema を API design document として固める
2. **L3(Detail)**: tRPC router に schema を登録 → contract frozen
3. **L4(Impl)**: FE は mock data で先走り、BE が implementしたら無修正で動く

**導出方向**: TypeScript 型 → Runtime contract (Zod) → tRPC handler → API endpoint
**Debt管理**: tRPC 型推論で deprecated field の使用はタイプエラー（自動 detect）

**HELIX への示唆**: L2 の D-API にZod schema を埋め込む。L3 で state-events.md に procedure 型を emit。L4 で schema change は gate (G3 API Freeze)。

---

### 2.2 MSW + OpenAPI (Contract-First via Specification)
**URL**: https://mswjs.io/docs/recipes/keeping-mocks-in-sync  
**参考**: https://dev.to/michaliskout/supercharge-frontend-development-with-msw-openapi-and-ai-generated-mocks-1bfo

**パターン**:
```javascript
// OpenAPI spec → @msw/source で handler 自動生成
import { http, HttpResponse } from 'msw';
import { fromOpenApi } from '@msw/source';

const handlers = fromOpenApi(openAPISpec);
// ✓ paths, methods, responses すべて spec に従う
```

**モック→契約の流れ**:
1. **L2(Design)**: OpenAPI spec を作成・凍結
2. **L3(Detail)**: `@msw/source` で handler 自動生成 → test coverage 自動算出
3. **L4(Impl)**: FE は自動生成handler で mock、BE は OpenAPI から code-gen

**導出方向**: OpenAPI spec → MSW handler / BE code-gen (同期)
**Debt管理**: Spec に breaking change → handler も自動更新。FE で unhandled endpoint は dev-time error。

**HELIX への示唆**: D-API を OpenAPI yaml で記述。state-events.md は endpoint + response shape。L4 で spec drift を CI check (prism/dredd)。

---

### 2.3 Storybook + Chromatic (Visual Contract)
**URL**: https://github.com/storybookjs/design-system  
**Visual Testing**: Chromatic (https://www.chromatic.com/blog/introducing-storybook-design-system/)

**パターン**:
- **Story = living mock** (with props, interactions, visual states)
- **Chromatic baseline** = visual contract (pixel-perfect)
- Component code change → visual regression detected → review required

**モック→契約の流れ**:
1. **L2(Design)**: Figma design → Storybook story (mock component)
2. **L3(Detail)**: Story に props spec + interaction flow 定義 → Chromatic baseline capture
3. **L4(Impl)**: Component styling は story 対応を確認しながら (story drive)

**導出方向**: Visual design → Story (mock props/states) → Chromatic contract
**Debt管理**: Storybook baseline 更新で visual debt を trace。deprecated props は story を保留 → cleanup task化。

**HELIX への示唆**: Phase L5 (Visual Refinement) で mock.html と Chromatic baseline を同期。L2 frozen の visual design を artifact (screenshot) に落とし込む。

---

## 3. モック駆動の Debt 管理パターン

### 3.1 Self-Admitted Technical Debt (SATD) in GitHub Issues
**参考**: https://homepages.dcc.ufmg.br/~mtov/pub/2022-emse.pdf | https://github.com/orgs/community/discussions/178975

**実パターン**:
- **45%** の SATD は「船出優先」で incur（prototype/mock の throwaway code）
- **60%** は design flaw に分類 → Phase L4 で refactoring task に変換
- **Tool**: AdmiTD (GitHub issues 自動報告) で TODO 化

**継続パターン (実装例)**:
```markdown
## Mock-Driven Debt Register

| ID | Phase | Type | Status | Owner |
|----|----|------|--------|--------|
| MD-01 | L4.1 | throwaway-handler | ⏳ L4.5 consolidate | @BE-team |
| MD-02 | L5 | visual-mock-css | ✅ absorbed into L5 |  |
| MD-03 | L4 | missing-error-case | ⚠️ escalated to L6 test | @QA |
```

**HELIX との接続**: Phase L4 で「mock → real API」の境界で `debt-register` skill を trigger。debt はラベル化（`debt-mock-driven`, `debt-contract-boundary`）して SQLite に記録。L6 gate (G4) で debt ratio を check。

### 3.2 Contract-First Design の Debt 化戦略
**事例**: tRPC / MSW で spec change → FE breaking change
**対応**:
- **L3 API Freeze**: schema breaking change を禁止 (versioning)
- **Deprecation flag**: Old field は "deprecated": true で L5/L6 に持ち越し
- **Cleanup task**: deprecated field が unused → 自動削除タスク (Code Cleanup Phase L7)

---

## Phase 2（HELIX モック駆動 L2 強化）への示唆

### ✅ 即座に採用可能
1. **D-API に Zod / OpenAPI 統合**
   - L2 frozen で JSON schema を具体的に
   - L3 で state-events.md に型を emit
   - L4 で deploy-time contract check

2. **mock.html + Storybook story の二重作成廃止**
   - Storybook story を唯一の visual spec
   - Chromatic baseline で pixel-perfect contract
   - L2 凍結時に screenshot capture

3. **Debt Register の phase gate 統合**
   - L4 .1a: mock handler 自動生成 → debt log に「mockとして valid」
   - L4 .5: real API swap → debt log に「consolidated」
   - G4: debt ratio threshold (e.g., 10% 以上は escalate)

### 🔄 要検証・導入予定
1. **@msw/source との連携**
   - OpenAPI spec → handler 自動生成 (FE dev parallelization)
   - Prism/Dredd で spec drift detect (CI)

2. **tRPC 型推論の precompile check**
   - schema change → FE type error (pre-commit hook)
   - backward compat warning を verbose

3. **Debt metric の自動化**
   - `git log --grep="mock"` で throwaway commit 抽出
   - Debt register に自動挿入 (ログベース)

---

## References

- MSW Official: https://mswjs.io/
- tRPC: https://trpc.io/
- Storybook Design System: https://github.com/storybookjs/design-system
- devmock-client: https://github.com/huynamboz/devmock-client
- OpenAPI + MSW: https://dev.to/michaliskout/supercharge-frontend-development-with-msw-openapi-and-ai-generated-mocks-1bfo
- Self-Admitted Technical Debt (SATD): https://homepages.dcc.ufmg.br/~mtov/pub/2022-emse.pdf
- GitHub Technical Debt Discussion: https://github.com/orgs/community/discussions/178975

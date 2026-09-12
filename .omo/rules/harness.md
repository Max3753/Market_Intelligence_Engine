# Harness 项目契约 — Market Intelligence Engine

> 本文件是 **Harness Engineering 框架**在本项目的**完整执行契约**，由 omo rules-injector 自动注入（`.omo/rules`，source=0，最高优先级）。
> 激活标识见 `.harness-activated`。本文件是**唯一事实来源**，修改契约请改这里。
>
> 核心信念：**模型能力 ≠ 执行可靠性。** 模型权重之外的一切工程基础设施（harness），才是让 agent 从"不可靠"走向"可靠"的关键。

---

## 一、本项目是什么（架构基线）

Market Intelligence Engine 是一条 **Evidence-driven 产品发现流水线**，从原始用户表达一路加工到产品机会：

```
Data Sources (Reddit/GitHub/V2EX/HN)
  → Source Adapters (adapters/base.py 注册表 + reddit.py)
  → Crawling Scheduler + Workers (crawling/scheduler.py, workers.py)
  → Raw Data Layer (models/document.py RawDocument, §8.1 可追溯)
  → Clean & Normalize (extraction/pipeline.py normalise)
  → Deduplication (content_hash 四层去重)
  → Content Classifier (intelligence/classifier.py, 11 类)
  → Demand Extraction (intelligence/extractor.py)
  → Embedding (intelligence/embedder.py, all-MiniLM-L6-v2, 384 维)
  → Clustering (intelligence/clustering.py, HDBSCAN)
  → Demand Scoring (intelligence/scoring.py, 8 指标加权 0-100)
  → Opportunity Engine (api/routes/opportunities.py, Human-in-the-Loop 状态机)
  → Dashboard (frontend, Next.js 15 + Tailwind)
```

**本项目的四个架构特征，是 harness 必须守护的底线：**

1. **LLM 是流水线的"软肋"**——classifier / extractor / scoring / clustering 命名 / opportunity 起草，全部依赖 `intelligence/llm_client.py` 的 `chat_json()`（OpenAI 兼容，可切 DeepSeek/Kimi/MiMo）。LLM 输出不可靠，必须兜底校验。
2. **异步 + 独立 session**——后台爬取任务（`workers.py`）必须用独立 `async_session_factory()`，**绝不能复用请求的 session**。
3. **Human-in-the-Loop 是决策门禁**——`opportunities.py` 的 `VALID_TRANSITIONS` 状态机 + 单源门禁 + 否决必须留理由。AI 只做发现和起草，**最终签字的是人**。
4. **证据链必须完整**——RawDocument → Document → DemandSignal → Evidence → Source，每个需求结论必须可追溯到原始证据（Evidence First）。

---

## 二、五层防御（针对本项目落地）

> 通用五层防御（任务规范 / 上下文供给 / 执行环境 / 验证反馈 / 状态管理）在本项目中的**具体落地手段**。每一条都指向真实文件与真实风险。

### 2.1 任务规范 —— 每个任务写显式完成定义

| 本项目任务类型 | 完成定义必须包含 |
|---|---|
| **新增/修改 API 路由** | 端点路径、请求/响应 schema、状态码（404/409/422）、是否需独立 session、测试 |
| **新增/修改 LLM 调用** | 走 `chat_json()`、system prompt 要求 STRICT JSON、**必须兜底校验 LLM 输出**（参考 `classifier.py` 的枚举校验、`llm_client.py` 的 ```json 剥壳） |
| **新增/修改数据模型** | 表名、字段、外键、是否 pgvector 向量列、迁移 |
| **新增/修改爬取适配器** | 实现 `SourceAdapter` 四方法（name/discover/fetch/parse）、注册到 `ADAPTERS`、`normalise()` 标准化 |
| **前端页面/组件** | 遵循 `frontend/DESIGN.md` 设计契约、过视觉门禁 R011 |

### 2.2 上下文供给 —— 动手前必须读的文档

| 文档 | 作用 |
|---|---|
| `README.md` | 架构图、目录结构、技术栈、项目原则 |
| `docs/requirements-trace.md` | 需求追踪矩阵（REQ-001~025）、覆盖缺口、Phase 映射 |
| `docs/PROJECT_LOG.md` | 开发日志、历史决策 |
| `frontend/DESIGN.md` | 前端设计系统契约（色板/字体/组件规范） |
| 全局 `HARNESS.md` | Harness 路由指南（Intent → Agent 路由表） |

**隐性约定（代码里已体现，agent 必须遵守）：**
- SQLAlchemy 2.0 风格（`Mapped` / `mapped_column`），不是 1.x
- 所有 LLM 调用走 `chat_json()`，不直接 new OpenAI client
- 后台任务用独立 session，不复用请求 session
- 时间统一 `datetime.utcnow()`，Unix 时间戳在 `normalise()` 里转 datetime

### 2.3 执行环境 —— 工具链与运行约束

| 环境 | 约束 |
|---|---|
| **后端** | Python 3.12 + `uv sync`；启动 `uvicorn app.main:app --reload --port 8100`（winnat 动态端口已修复 2026-09-12，动态范围 49152-65535，8100 不再被保留段封锁） |
| **前端** | Next.js 15 + Tailwind 3.4；启动 `npm run dev`（端口 3000）；API 地址经 `frontend/.env.local` 的 `NEXT_PUBLIC_API_URL` 指向 8100 |
| **基础设施** | `docker compose up -d`（PostgreSQL 16 + pgvector + Redis 7） |
| **Embedding** | 本地模型 all-MiniLM-L6-v2，`local_files_only=True` 优先；`HF_HOME`/`HF_ENDPOINT` 用户级变量 |
| **验证命令** | 后端 `pytest`；前端 `tsc --noEmit` + `npm run build` |

**已知缺口（agent 不要误以为已实现）：**
- `crawling/workers.py` 的 `CrawlQueue` Redis 队列 / `crawl_worker` 循环是骨架（TODO）——`process_job` 已完整实现（独立 session + content_hash 去重 + 状态机）；自动调度已由 `scheduler.py`（APScheduler）接管
- github 源爬取需代理 `127.0.0.1:7890`（config.proxy 可覆盖），代理未开时 ConnectError（环境问题非代码问题）
- 知乎 `ZHIHU_COOKIES`（z_c0）约 6 天过期，需定期刷新；已有 `scripts/configure_zhihu_cookie.py` 校验工具（base64 合法性 + 时间戳新鲜度）

**已启用说明（历史缺口已关闭，勿再按缺口处理）：**
- `trend_metrics` 数据生成：2026-09-09 决策改为 **GET /trends 实时计算**（数据量小，实时算比落表更简单准确），不再落表；表保留（cluster_id 可空）
- V2EX 适配器（`adapters/v2ex.py`）：2026-09-07 已启用跑通——SNI 阻断结论反转，HTTPS 直连可用（200），证书链不完整需 `verify=False`（只读公共 API 可接受）；API_BASE 用 `/api/`（v2 需 token 不可用）
- 知乎适配器（`adapters/zhihu.py`）：2026-09-07 已启用跑通——配置 `ZHIHU_COOKIES`（z_c0/d_c0/__zse_ck）后热榜 20 条入库（language=zh）；签名用格式正确随机值，知乎收紧校验时需换真实 SM4 签名
- 掘金适配器（`adapters/juejin.py`）：已实现并创建 juejin 源（id=4，active，每小时调度）——沸点为有效信号源（40 条/次，language=zh）；文章热榜 brief 全空被 discover 过滤，暂不贡献信号

### 2.4 验证反馈 —— 质量门禁

| 门禁 | 触发时机 | 工具 |
|---|---|---|
| **类型检查** | 后端/前端改动后 | `tsc --noEmit`（前端）、`pytest`（后端） |
| **质量门禁** | 宣布完成前 | `quality-gate-check` 技能 |
| **代码审查** | 核心文件改动后 | `code-reviewer`（`task(category="deep")`） |
| **视觉门禁 R011** | 前端任务完成前 | `visual-qa` 验收（见第三节） |
| **需求追踪** | 需求相关任务 | `requirement-tracer`（`trace-changes` 技能） |

### 2.5 状态管理 —— 跨会话不丢上下文

| 机制 | 作用 |
|---|---|
| `docs/requirements-trace.md` | 需求 → 代码位置 → 状态，跨会话追踪 |
| `docs/PROJECT_LOG.md` | 历史决策与错误记录 |
| `trace-changes` 技能 | 追踪代码变更影响范围 |
| `.harness-activated` | 激活状态标识 |

---

## 三、前端 UI 审美要求（视觉门禁 R011）

> 前端 UI 是"设计是一等交付物"，不是"正确但平庸"。**Correct-but-flat 是失败，不是完成。**

### 3.1 触发机制（何时必须介入）

以下任一情况出现，**必须**加载前端视觉技能：
- 涉及 **UI / 前端 / 样式 / 布局 / 组件 / 页面 / 交互 / 动画** 的任务
- 新建或修改 **React / Next.js / 组件 / 页面 / 样式文件**
- 需要 **视觉验收**（页面是否好看、是否符合设计意图、CJK 是否裁剪）
- 涉及 **品牌 / 设计系统 / 参考锚点 / 审美** 的诉求

### 3.2 技能调用（skills 路由）

| 阶段 | 技能 | 作用 |
|---|---|---|
| **开工前** | `frontend` | 加载 `frontend/DESIGN.md` 设计契约，建立审美基准 |
| **开发中** | `frontend` | 按设计契约实现，避免"正确但平庸"的 AI slop |
| **开发中（可选强化）** | `design-taste-frontend` | 反 AI slop 审美判断强化（见下方适用范围） |
| **完成前** | `visual-qa` | 截图/像素级验收，跑设计系统 + 视觉保真 + CJK 检查 |
| **清理** | `remove-ai-slops` | 移除 AI 生成的平庸/冗余代码 |

**调用方式：**
```text
# 前端任务开工
task(category="visual-engineering", load_skills=["frontend"], run_in_background=false, prompt="...")

# 前端任务完成前验收
task(category="visual-engineering", load_skills=["visual-qa"], run_in_background=false, prompt="...")

# 前端任务（landing/portfolio/营销页）强化审美判断
task(category="visual-engineering", load_skills=["frontend", "design-taste-frontend"], run_in_background=false, prompt="...")
```

**`design-taste-frontend` 适用范围（重要）：**
- ✅ **适用**：landing page、portfolio、营销页、改版（redesign）——强化 Brief Inference、Design System Map、反 AI slop
- ⚠️ **不直接适用**：Dashboard、数据表、多步骤产品 UI（该 skill 明确声明 "Not dashboards, not data tables, not multi-step product UI"）
- **对 Dashboard 的价值**：仅借用其 **Design System Map** 指导——数据密集 UI 应选 Fluent/Carbon/Atlassian/Polaris 等官方设计体系，数据表用 TanStack Table/AG Grid，而非凭空造 CSS
- **原则**：本项目 Dashboard 以 `frontend/DESIGN.md` 设计契约为准，`design-taste-frontend` 只作审美判断补充，不覆盖内部设计系统

**Dashboard 三旋钮推荐（数据密集场景，会话内覆盖）：**
> `design-taste-frontend` 的旋钮是会话内对话式覆盖（不直接改 SKILL.md，避免影响其他项目）。本项目 Dashboard 推荐：
> - **`DESIGN_VARIANCE: 4`**（低方差）——数据仪表盘要克制、清晰，不做实验性布局
> - **`MOTION_INTENSITY: 3`**（低动效）——数据展示动效服务交互，不做花哨动画
> - **`VISUAL_DENSITY: 8`**（高密度）——信息丰富，一屏呈现更多数据（Demand Feed / Explorer / Opportunity Ranking）
> - **设计体系**：数据密集 UI 优先选 Fluent/Carbon/Atlassian/Polaris 官方体系，数据表用 TanStack Table/AG Grid，不凭空造 CSS

### 3.3 视觉门禁规则（R011）

> **R011（视觉门禁）**：涉及 UI/前端/样式/布局/组件/页面的任务 → **必须先加载 `frontend` 技能**；宣布完成前 → **必须跑 `visual-qa` 验收**。未通过视觉验收不得宣布完成。

### 3.4 审美基准（参考锚点）

- 目标是 **Linear / Stripe / Supabase 级别** 的 senior designer 出品，不是"干净且正确"
- 保护表面（surface）像保护构建（build）一样用力
- 设计是**一等交付物**，不是一次性决定后就走开

---

## 四、执行纪律

1. **遇到失败，先修 harness，再换模型**——换模型是成本最高的选择
2. **每次失败都是信号**——定位到五层防御中的某一层，修补，下次不再犯
3. **LLM 输出必须兜底校验**——参考 `classifier.py` 的枚举校验、`llm_client.py` 的 JSON 剥壳
4. **后台任务用独立 session**——`workers.py` 模式，不复用请求 session
5. **Human-in-the-Loop 不可绕过**——AI 只起草，人签字；单源门禁、否决留理由
6. **前端任务必须过视觉门禁**——frontend 技能开工 + visual-qa 验收
7. **所有 Harness Agent 调用**使用 `task(category="deep", ...)` 格式，携带完整行为定义
8. **等待 Agent 完成后才返回结果**，不阻塞开发流程

---

*本文件由 Harness Engineering 框架维护，内容针对 Market Intelligence Engine 项目定制，由 omo rules-injector 自动注入。修改前请确认理解五层防御与视觉门禁的意图。*

# Market Intelligence Engine — 项目日志

> 本文件记录项目开发过程中的状态变更、决策、验证结果与待办事项。
> 每次开发阶段结束时更新。

---

## 项目信息

| 项 | 值 |
|---|---|
| 项目名称 | Market Intelligence Engine (MIE) |
| 设计文档 | `Market_Intelligence_Engine.md` (v0.1, 2026-08-19) |
| 技术栈 | Python 3.12 / FastAPI / Next.js / PostgreSQL 16 / Redis 7 |
| 包管理 | uv (backend) / npm (frontend) |
| 开发环境 | Windows, Docker 29.6.2 (CLI), Node 22.14.0 |

---

## 时间线

### 2026-09-14 — 生产部署准备：GitHub 代理修复 + 自动播种 + Human-in-the-Loop 半自动

**背景**：用户将项目部署到阿里云服务器（docker compose，nginx 8082:80），要求"后端有数据"。

**GitHub 代理修复**（759aa9f）：
- 根因：`github.py` 代理解析逻辑——config 缺省 `proxy` 时默认 `127.0.0.1:7890`，但服务器无本地代理 → ConnectError
- 修复：`"proxy": ""` = 禁用代理直连；缺省 = 默认代理；显式 URL = 用之；httpx 0.28.1 对空串代理 URL 抛 ValueError，必须转 None
- 测试：`test_adapters.py::test_github_proxy_resolution` 三分支覆盖

**自动播种 + 自动流水线**（9336047，10 文件 +415/-222）：
- 新建 `app/crawling/seeding.py`：`default_sources()` 纯函数 + `seed_default_sources()`（幂等，仅空表播种）；HN+V2EX（interval 60）恒播种，GitHub 仅当 `GITHUB_REPO` 设置（interval 1440，config 带 proxy）
- 新建 `app/intelligence/analysis.py`：`LowValueSignal`、`analyze_one`、`analyze_unanalyzed`、`auto_pipeline`；`clustering.py` 新增 `rebuild_clusters/rescore_clusters`；documents/clusters 路由改薄
- `scheduler.py` 新增 `trigger_now(source_id)`；`main.py` lifespan：播种 → 启动调度器 → 对新源立即爬取一次
- `workers.py`：爬取成功且 `items_stored>0` 且 `AUTO_PIPELINE` → 后台 `auto_pipeline()`
- 验证：pytest 18 passed / 2 skipped（既有 async 测试缺 pytest-asyncio）；LSP 干净；openapi 25 端点齐全

**Human-in-the-Loop 半自动决策**（用户反对全自动按时触发，担心 API 额度滥用）：
- `settings.py`：新增 `CRAWL_SCHEDULER_ENABLED=False`（周期调度默认关闭）；`AUTO_PIPELINE` 默认改 `False`（自动分析默认关闭）
- `scheduler.py`：`start()` 中 `_recover_orphan_jobs()` 恒执行，`_register_active_sources()` 仅当 `CRAWL_SCHEDULER_ENABLED` 开启
- 最终行为：部署即播种 + 初始爬取一次（免费 API、零 LLM）→ 原始文档自动入库；之后爬取/分析/聚类/评分全部 Console 手动触发
- `deploy/.env.prod.example` / `deploy/README.md` 同步新配置说明

**验证**：pytest 18 passed / 2 skipped；LSP 零诊断；git 已推送（759aa9f + 9336047 + 半自动调整）

### 2026-09-12 — 前端视觉打磨 + UX 优化 + winnat 永久修复 + 品牌区返回链接

**前端视觉打磨与 UX 优化**（用户确认：落地页 + 仪表盘两者都打磨，UX 五项全选）：
- **落地页**（Agent 1，visual-engineering + design-taste-frontend）：新增 `SiteNav.tsx` 滚动毛玻璃导航（初始透明 → 滚动后 `bg rgba(11,17,32,.7) + blur(12px)` + 边框，focusRingCls）；`page.tsx` 加 section id + `scroll-mt-24` 锚点（#pipeline/#features/#data/#principles）、Hero 字号节奏、截图/流水线/bento 卡片 hover 动效；`landing.css` scroll-smooth（prefers-reduced-motion 保护）
- **仪表盘/应用壳**（Agent 2，visual-engineering + visual-qa）：`Skeleton.tsx` 扩 7 种图表骨架原语；`(app)/loading.tsx` 重写镜像仪表盘布局；`EmptyState.tsx` 加 variant + 引导文案（dashboard/opportunities/console/clusters/[id] 统一）；`error.tsx` 区分"无法连接后端" vs 其他错误；移动端 Sidebar 收窄 w-14 图标栏 + main `p-4 md:p-8`；雷达/环形图 tooltip、条形/排行/周期图行 hover、统计卡 hover
- **仪表盘截图嵌入落地页**：Playwright 截取 `/dashboard` → `frontend/public/dashboard-screenshot.png`（296KB），嵌入 hero + 数据展示两槽位（hero 立即加载、lazy 图滚动后加载）
- **品牌区返回链接**：Sidebar 品牌区（M/MIE/Market Intelligence）`<div>` → `<Link href="/">`（title="返回介绍页"、aria-label、logo group-hover:scale-105、focusRingCls）

**winnat 端口保留永久修复**（管理员权限，已持久化）：
- 根因：Windows winnat 动态端口保留段随机漂移，曾封锁 8000/8100/8101/3000（WinError 10013 / EACCES）
- 解法：`netsh int ipv4 set dynamic tcp start=49152 num=16384`（动态端口移至 49152-65535）+ `net stop winnat && net start winnat`；排除范围现仅 5357 与 50000-50059
- 结果：**3000/8100 不再被系统保留**，后端回到 8100（用户手动启动），前端 3000 正常

**验证**：`tsc --noEmit` exit 0；`next build` exit 0（10.2s，7 路由，落地页 5.41kB/155kB First Load）；Playwright QA：导航毛玻璃 ✅、锚点精确停 96px ✅、仪表盘数据 50/50/10/70.6 + 15 SVG ✅、移动端 375px 无水平溢出 ✅、控制台唯一错误 favicon.ico 404（无害）

**文档同步**（三份核心文档对齐到 09-12 实际状态）：
- `docs/requirements-trace.md`：REQ-004/REQ-009 状态更新；覆盖缺口拆分（当前缺口 + 已收尾缺口）；头部状态改 MVP 全链路完成
- `docs/PROJECT_LOG.md`：状态快照刷新（删已解决待办，新增知乎 Cookie 时效）；决策记录 +2；质量门禁 +1
- `.omo/rules/harness.md`：端口更新 8100（winnat 已修复）；已知缺口精简为 3 项真实缺口；新增「已启用说明」区块（trend_metrics 实时计算 / V2EX / 知乎 / 掘金）
- 交叉核对：三份文档对 REQ-004、趋势、V2EX/知乎、端口、CrawlQueue 表述一致，无残留过时信息

**⚠️ 教训**：`next build` 与运行中 dev server 共用 `.next` 会冲突（`Cannot find module './214.js'`）——build 前需停 dev server，或 build 后清 `.next` 重启

### 2026-09-10 — 机会 #3 断链修复 + 语义去重 + 仪表盘趋势接入 + 测试环境修复

**机会 #3 断链修复**（cluster_id=null → cluster #26）：
- 根因：clusters rebuild 全量重建删旧簇，机会作为人工决策记录存活但 cluster_id 置空（见 `Opportunity.cluster_id` 注释）
- 新增 `app/intelligence/opportunity_relink.py`：`relink_opportunity()` 按 problem_statement 与簇 name/description 的关键词重叠（coverage 0.7 + precision 0.3）+ 可选 embedding 相似度（0.4 语义 + 0.6 关键词）自动匹配；`MIN_MATCH_SCORE=0.15` 阈值（Human-in-the-Loop：宁缺毋滥）；子串匹配覆盖形态变化（alter↔altering），无需词干提取依赖
- 新增 `POST /opportunities/{id}/relink` 端点：默认自动匹配；显式 `cluster_id` 人工覆盖；已关联直接返回
- 修复端点 500：`return opp` 未预加载 `analysis` 关系 → async lazy load 失败（MissingGreenlet）→ 统一 `await db.refresh(opp, ["analysis"])`
- 实测：机会 #3 自动匹配 cluster #26（score=0.329, method=keyword+embedding），三个分支（已关联/显式覆盖/自动匹配）全部通过 ✅

**pgvector 语义去重**（REQ-004 收尾）：
- `pipeline.py` 新增 `check_semantic_duplicate()`：embedding 余弦相似度 ≥ 0.95 判定重复（距离阈值 0.05）；旧文档 embedding 为 null 自动跳过；惰性导入规避 tensorflow/protobuf 冲突
- `workers.py` 接线：content_hash 精确去重（5b）→ 语义去重兜底（5b'，fail-open 不阻断入库）→ author upsert → 存文档

**仪表盘趋势接入**：
- 新增 `TrendGrowthRank.tsx`（信号增长排行，7d→30d→90d 窗口优先级回退）+ `TrendPeriodBar.tsx`（周期信号量，纯 CSS 横条，尊重 prefers-reduced-motion）
- `page.tsx` 新增「信号增长排行 + 周期信号量」双卡片区块，`Promise.all` 并行取 trends，空态兜底

**测试环境修复**：
- `reddit_test.py`：加 `pytest.mark.skip`（Reddit 被墙，Phase 7 再接）+ `__main__` 保护——收集阶段不再直连 Reddit（ConnectTimeout 消失）
- `embedder.py`：`sentence_transformers` 导入移到 `get_model()` 内部（惰性导入）——`EMBEDDING_DIM` 常量可被 `document.py` 安全引用，不再触发 tensorflow→protobuf 冲突
- 验证：`pytest tests/` → **14 passed, 2 skipped**（reddit 显式 skip + hn async 自动跳过），收集干净

**爬取**：job 213-216（HN/V2EX/掘金/知乎）——知乎入库 15 条、HN 1 条；github 需代理跳过

### 2026-09-09 — 机会可行性分析中文输出 + 端口迁移 8101→8106（Windows 保留端口段复发）

**中文输出修复**：
- `opportunity_analyzer.py` `ANALYSIS_SYSTEM_PROMPT` 增加 LANGUAGE 规则：所有文本字段（technical/market/competition/risks/hypotheses/action_items/summary）必须简体中文输出，JSON key 保持英文
- 重新生成机会 #3 分析验证中文输出 ✅

**端口迁移 8101→8106**（Windows winnat 动态端口保留复发）：
- 根因：`netsh interface ipv4 show excludedportrange` 显示 **8006-8105** 被 winnat 动态保留（Hyper-V/WSL/Docker 触发，随机段），8100/8101 同时被封锁（WinError 10013）
- 与 9/7 的 5432/6379 保留段同机制；本次保留段恰好覆盖 8100/8101
- 解法：后端迁移到 **8106**（避开保留段）；前端 `.env.local` + `api.ts` 默认值同步改 `http://localhost:8106`
- 遗留：8100/8101 恢复需管理员执行 `net stop winnat && net start winnat`（临时）或 `netsh int ipv4 set dynamic tcp start=49152 num=16384`（一劳永逸）

### 2026-09-08 — 机会级可行性分析（总结反馈）功能落地

**背景**：demand_score 高 ≠ 可实现。用户洞察：高评分需求信号不代表可实现，需要深入分析 → 新增「总结反馈」功能，LLM 基于证据链评估机会可实现性，辅助人决策（Human-in-the-Loop：AI 只生成分析，人做最终判断）。

**后端**：
1. **新表 `opportunity_analyses`**（迁移链自 `5b90bf393966`）：`feasibility_score`(0-100) + technical/market/competition 三维度 + risks/validation_hypotheses/action_items（Text 列存 JSON 字符串，与 pain_points 模式一致）+ summary + 时间戳
2. **`app/intelligence/opportunity_analyzer.py`**（新建）：`analyze_opportunity()` 收集机会字段 + 关联簇评分 + 成员信号 → `chat_json()` → `_fallback_validate()` 兜底校验（缺字段给默认值、score 夹 0-100）
3. **断链处理**：cluster_id 为 null（rebuild 后）只用机会自身字段，risks 自动追加「来源簇已解绑，证据链需重建」
4. **API**：`POST /opportunities/{id}/analyze`（生成/覆盖分析，不自动改状态）；`GET /opportunities` 嵌套返回 `analysis`（可为 null）

**前端**（机会榜页）：
- 机会卡片新增「总结反馈」区块：可行性评分徽章 + 总结正文 + 可折叠可行性维度（风险红/假设琥珀/行动绿）+ 更新时间 + 重新生成按钮
- 无分析时显示「生成可行性分析」按钮

**验证**：契约测试 13 passed；`POST /opportunities/3/analyze` 实测生成（机会 #3「平台静默行为聚合提醒插件」feasibility_score=45，命中"高评分≠可实现"洞察：demand 68.9 vs 可行性 45）；`GET /opportunities` 嵌套 analysis ✅；tsc 0 错误；Playwright 实测区块完整渲染；DB 中文存储正确（PowerShell 显示乱码为控制台编码问题，非数据问题）

**⚠️ 遗留**：`test_health.py` 失败为预存在 protobuf/tensorflow 环境冲突，与本次改动无关

### 2026-09-08 — 信息源架构优化完成（P0 可靠性 + P1 数据质量/可观测性 + P2 扩展性，12 项全部落地）

**P0 可靠性（4 项）**：
1. **孤儿清理** `workers.py _recover_orphan_jobs()`：启动时把 `running` 残留 job 标记 `interrupted`（防重启后卡死）；实测通过
2. **重试退避**：`RETRY_ATTEMPTS=3` / `RETRY_BACKOFF=(1,5,30)` + `_is_transient()`（ConnectError/Timeout/5xx 才重试，4xx 不重试）
3. **超时统一**：`base.py DEFAULT_TIMEOUT = httpx.Timeout(connect=5, read=15, write=10, pool=5)` + `SourceAdapter.timeout()`，5 个适配器统一
4. **单 URL 容错**：fetch 循环逐 URL try/except——全部失败→job `failed`；部分失败→`completed` + `error_message` 记录失败数

**P1 数据质量/可观测性（5 项）**：
5. **增量爬取**：迁移 `363cdad6a037` 给 sources 加 `config`(JSON)/`last_crawl_at`/`last_success_at`/`consecutive_failures`/`avg_latency`；github discover 读 `last_crawl_at`→`since` 参数（实测 URL 带 `since=2026-09-07T07:58:44Z`）；hn.py 修 return-in-loop bug（3 feed 全收集）
6. **源级配置化**：zhihu `_cookies()` 改类方法（config.cookies → fallback settings.ZHIHU_COOKIES）；v2ex `verify` 从 config 读；github `token`/`proxy` 从 config 读（`_get_client()` 改实例方法）；实测 cookies/verify/token 均从 config 生效
7. **源质量反馈**：`/sources/stats` 返回 `signal_yield`（信号数/文档数）；前端 console 页显示信号产出
8. **源健康度**：workers 收尾写健康指标（`consecutive_failures±1`/`last_success_at`/`avg_latency` EMA α=0.3/推进 `last_crawl_at`）；前端 console 页健康点（绿/黄/红/灰）；实测 HN 爬取后健康字段联动更新
9. **爬取统计**：`GET /sources/stats`（doc_counts/signal_counts 左连 + 30 天 job 聚合：成功率/平均耗时/去重率）；`func.make_interval(0,0,0,30)` 修复关键字参数 500；实测 5 源全返回

**P2 扩展性（3 项）**：
10. **速率限制**：workers URL 循环 + hn discover 按 `config.rate_limit` sleep；实测 v2ex rate_limit=2 → job 耗时 21.6s（基线 3.2s，10 条 fetch 9×2s 间隔吻合）
11. **适配器契约测试**：`tests/test_adapters.py`（parse 契约字段+类型断言 ×7、MockTransport discover ×6）**13 passed**；`conftest.py` 改惰性导入 app.main（避开 tensorflow/protobuf 冲突）
12. **分页/深度配置**：6 适配器 discover 读 `config.depth`（juejin 页数/v2ex 条数倍数/hn 每 feed 倍数/github per_page 上限 100/zhihu limit/reddit 上限 100）；实测 HN depth=2 → items_found 120（基线 60，翻倍）

**验证汇总**：契约测试 13 passed；增量 since 参数 ✅；速率限制 21.6s vs 3.2s ✅；深度 120 vs 60 ✅；源配置 cookies/verify/token ✅；`/sources/stats` 5 源全返回 ✅；后端 8101 重启后全部生效（PID 32912）

**⚠️ 遗留**：github 源爬取需代理 `127.0.0.1:7890`（本次验证时代理未开 → ConnectError，非代码问题）；8100 僵尸端口（PID 25300/36944）待用户重启电脑清理

### 2026-09-07 — UI 优化完成（视觉 QA 通过）+ infra 端口变更 + 知乎源启用（遇 Cookie 阻塞）

**UI 全面优化**（视觉 QA 全流程闭环）：
1. DESIGN.md token 落地（tailwind.config.ts 色板/圆角/阴影 + globals.css + lib/ui.ts 共享类名）；首页 4 可视化卡片（雷达图/条形图/环形图，纯 SVG 无重图表库）+ 共享组件（Badge/EmptyState/Skeleton/SectionTitle/StatCard/Sidebar 等）+ Lucide 图标替换 emoji
2. 视觉 QA 双 pass 审查发现阻塞项 → 修复：严重度分桶改互斥（高 7-10/中 4-6/低 0-3）、interactiveCardCls 误用非交互 div→cardCls、13 处 emoji→Lucide TriangleAlert/CheckCircle2、侧边栏导航/统计卡标题中文化、DemandsTable 复用 table token、TypeDistribution 死 transition 移除
3. 复审双 PASS 无 BLOCKING → Verdict GOOD；`tsc --noEmit` + `npm run build` 0 错误；5 页面 200（前端 dev server 曾被 CORS 拦截，迁移到 3000 端口（后端 CORS 允许 3000）后解决）

**infra 端口变更**（Windows 保留端口段冲突）：
- 后端 8100 起不来：PostgreSQL 5432 / Redis 6379 落在 Hyper-V/WSL 保留段（netsh：5358-5457 含 5432、6308-6407 含 6379），docker host 端口无法绑定
- 解法：docker-compose host 端口改 `15432:5432` / `16379:6379`（避开全部保留段）；backend/.env 加 `DATABASE_URL=postgresql+asyncpg://mie:mie@localhost:15432/mie`、`REDIS_URL=redis://localhost:16379/0`
- 后端 8100 恢复正常；数据无损（named volume 未变，仅 host 暴露端口变）

**知乎源启用（遇 Cookie 阻塞）**：
1. backend/.env 配置 `ZHIHU_COOKIES`（z_c0/d_c0/__zse_ck）
2. `settings.py` 加 ZHIHU_COOKIES 字段（pydantic-settings extra_forbidden 拒绝额外字段）+ `zhihu.py` 改用 `settings.ZHIHU_COOKIES`（原 os.getenv 读不到 .env 值）
3. `adapters/__init__.py` 注册 zhihu（此前漏 import → `No adapter registered for source type: zhihu`）
4. 创建 zhihu 源 id=5（type=zhihu，active）
5. **爬取阻塞**：知乎 API 返回 401 `ERR_DECODE_SECURE_COOKIE`。对照测试（带/不带签名、多签名变体均 401，仅无 Cookie 时返回"未登录"）确认是 **z_c0 Cookie 自身无法解码**（过期/无效），非签名问题。字符修正（G/Q 疑似混淆）+ 后端重启重测仍 401 → 判断 z_c0 过期或已吊销，**待用户提供最新有效 Cookie**
6. **✅ 已解决（2026-09-07 晚）**：根因确认 = **z_c0 时间戳过期**（旧值 `10:1788226404` = 09-01，距今 6 天；知乎拒绝解码过期 z_c0）。用户重新登录后提供新 z_c0（`10:1788766070` = 09-07 当天）→ 实测知乎 API 200。新增 `scripts/configure_zhihu_cookie.py`（校验 base64 合法性 + 时间戳新鲜度后才写入 .env，避免中转转录损坏）
7. **✅ 爬取链路跑通**：修复 zhihu.py discover 解析（热榜项 question id 在 `card_id`（`Q_<qid>`）而非 `target.id`，原解析返回空 → items_found=0）→ job 79 `completed`，**items_found=20 / items_stored=20**，20 条 zh 文档入库（language=zh，title/content/engagement 正常）
8. **⚠️ 遗留**：8100 端口被两个查不到的僵尸进程（PID 25300/36944，taskkill/Stop-Process 均无法定位）占用 → 后端临时迁移到 **8101**，前端 `.env.local` 已指向 8101。需手动清理 8100 僵尸端口（见下方报告）

**V2EX 源启用（✅ 已跑通）**：
1. **调研反转**：此前"V2EX SNI 被墙"结论**错误**。实测 `https://www.v2ex.com` HTTPS 直连可用（200）；证书验证失败是 V2EX 服务器证书链不完整（缺中间证书，需 `verify=False`）；HTTP 被墙（502）、api.v2ex.com 超时（不可用）——但主站旧版 API 完全够用
2. **重写 `v2ex.py`**：API_BASE 修正 `/api/v2/`→`/api/`（v2 需 token 不可用）；去掉硬编码代理 `127.0.0.1:7890`（直连即可，代理反而失败）；`verify=False`（证书链问题，只读公共 API 可接受）；parse 补 `language: "zh"` + `_unix_ts()` 防御
3. **验证**：手动测试 discover 1.1s（10 urls）/ fetch 0.2s；job 108（调度器自动）入库 **9 条 zh 文档**（标题/内容/engagement 正常，如"为什么宽带师傅大都不愿意改桥接？"、"我姐姐想买个不超过 7w 的车…求推荐"）；job 121 手动重爬 completed，9 主题全部去重跳过（content_hash 匹配，去重逻辑正常）
4. **⚠️ 教训**：--reload 模式下 reload 后 worker 事件循环可能异常（job 95 卡 running 5 分钟，items_found=0）→ 干净重启（去掉 --reload）后恢复正常

### 2026-08-29 — 中文数据源适配器（掘金 ✅ + 知乎骨架）

**任务**：扩充数据源——中文源（知乎/掘金），补中文市场空白，为单源交叉验证提供多源基础。

1. **调研**（librarian）：掘金无反爬（沸点/文章热榜 API 无需认证，直连即可）；知乎反爬全面收紧（需登录 Cookie z_c0/d_c0/__zse_ck + x-zse-96 签名；GET 接口只校验签名头存在性，不校验密码学内容）
2. **掘金适配器** `app/adapters/juejin.py`：沸点推荐流（POST，cursor 分页 2 页 × 20）+ 文章热榜（GET category_id=1&type=hot）；discover 返回每条目一个内部 URL（`juejin://` scheme + index，与 github.py 同款）；parse 双分支映射（沸点 digg+comment / 文章 view+like+collect 作 engagement_score）；直连不走代理；`__init__.py` 注册
3. **知乎骨架** `app/adapters/zhihu.py`：热榜发现 → 问题回答采集；`ZHIHU_COOKIES` 环境变量配置后启用，未配置时 discover 抛清晰错误；签名用格式正确随机值（附注释说明升级路径）

**验证**：掘金 discover 90 条（沸点 40 + 文章 50），parse 7 字段全齐，注册表 `get_adapter('juejin')` 生效，LSP 0 错误；知乎骨架注册生效 + 未配置 Cookie 优雅失败

**全链路验证与修复**（创建 juejin 源 id=4 后）：
1. 首次爬取失败：`Invalid isoformat string: '1787794399'`——掘金 API 的 ctime 是 JSON 字符串，normalise 的 `isinstance(ts, (int, float))` 检查失败。修复：适配器加 `_unix_ts()` 辅助函数（字符串数字 → int，0 → None）+ normalise 加数字字符串防御分支
2. 文章热榜 brief 字段实测全空（50/50），详情接口不可用（err_no: 2）——discover 过滤空 brief 条目，文章热榜暂不贡献信号
3. language 修复：中文源标记 `"language": "zh"`（此前默认 en 会误导分类/抽取）
4. 清理 89 条脏数据（空 content + language=en）后重爬：found=40 stored=35，全部 zh、content 非空、published_at 正常
5. 分析流水线全链路验证：analyze-batch 95 候选 → 31 信号 / 64 低价值跳过 / 0 失败；掘金 35 条文档产出 7 条需求信号（alternative_search/complaint/buying_intent/price_complaint/pain/unmet_need，置信度 0.7-0.9）——中文内容分类/抽取正常

**决策**：UI 全面优化已规划（token 落地/首页可视化/机会榜/demands/视觉打磨）但用户暂停，待后续恢复

### 2026-08-29 — 评分落库 + trend_metrics FK 解耦 + 自动调度补全

**任务**：按顺序执行三项收尾（重跑评分 → FK 隐患 → 自动调度）。

1. **重跑评分**：POST /clusters/rescore → `{"scored": 3}`。三簇 demand_score 落库：Unexpected platform behavior 68.9 / Unified symptom and project tracking 55.1 / Loss of coding joy 53.6（LLM 维度 gap 7/6/7 有区分度）
2. **trend_metrics FK 解耦**：迁移 `5b90bf393966` — cluster_id 改 nullable（沿用 opportunities 模式，历史趋势数据在 rebuild 断链后存活）；模型同步 Optional
3. **自动调度补全**：`scheduler.py` 骨架 → 完整实现（AsyncIOScheduler + 活跃源注册 + interval job + max_instances=1 防并发 + coalesce 补跑）；`main.py` 加 lifespan 启动/停止钩子

**验证**：LSP 0 错误；/health OK（lifespan 启动成功）；实证脚本确认 3 活跃源（HN/V2EX/GitHub）各注册每小时 job，stop 正常

**注意**：V2EX 源为 active 但适配器被 SNI 阻断——scheduler 每小时会尝试并失败（process_job 有 error_message 兜底，job 标记 failed 不卡死）

### 2026-08-29 — 文档同步（harness 契约 + 需求追踪刷新）

**任务**：检索确认 harness 机制时发现文档与实际偏差，同步修复。

1. `.omo/rules/harness.md` §2.3 — 端口 8000 → 8100（WSL2 保留段 7925-8024）；已知缺口刷新：scheduler/CrawlQueue 骨架保留标注（process_job 已实现），删除 extractor/Dashboard 占位描述（已实现）
2. `docs/requirements-trace.md` — REQ-001~025 状态从"✅ 框架"刷新为实际实现状态；覆盖缺口与 Phase 映射同步

**验证**：codegraph 确认 process_job 完整实现（独立 session + content_hash 去重 + 状态机）、CrawlQueue/crawl_worker/scheduler 仍骨架、5 适配器（base/reddit/github/hn/v2ex）、7 路由文件、5 前端页面

### 2026-08-29 — 单源信号交叉验证（source_count）落地

**背景**：机会 #1 被人工否决，理由"单源信号，等待交叉验证"。此前系统完全不追踪来源多样性——交叉验证是纯人肉流程。

**设计决策**（用户拍板）：软警告 + 勾选确认 + 自动 EVIDENCE_GATHERING。人保留最终决定权，风险通过状态机语义编码。

**后端**：
1. 迁移 `954b622e7cdb` — demand_clusters.source_count（NOT NULL + server_default='0'，修复有数据表加列失败）+ opportunities.source_count（快照，nullable）
2. rebuild：按成员文档 source_id 去重计算 source_count
3. detail 端点返回 source_count
4. create_opportunity：单源簇（source_count<2）未带 acknowledge_single_source → 422；带确认 → 立项成功且 validation_status 自动 = EVIDENCE_GATHERING；source_count 快照落库（rebuild 断链后可追溯）

**前端**：簇详情页 + 机会页来源徽章（单源⚠️/双源✅）；PromoteForm 单源警告 + 勾选确认 + 未勾选禁用提交

**验证**：rebuild 200（3 簇全单源，source_count=1 正确）；单源未确认 422 ✅；单源已确认 200 + EVIDENCE_GATHERING ✅；测试机会已清理

**环境坑**：WinError 10013 — Docker Desktop WSL2 保留端口段 7925-8024 含 8000，后端被迫迁移到 **8100**；前端 .env.local 设 NEXT_PUBLIC_API_URL=http://localhost:8100

### 2026-08-22 — rebuild 与机会表的外键冲突修复

**问题**：Console 触发 rebuild 时 FK 崩溃——`opportunities.cluster_id` 引用着待删除的簇。上次修复只处理了 demand_signals 的引用，Opportunity 工作流引入了新引用方。

**设计决策**：机会与簇解耦——机会一旦立项就是独立实体（标题/陈述/方案已快照在自身），机器侧聚类漂移不应销毁人工决策记录。拒绝级联删除和禁止重建两个极端方案。

**修复内容**：
1. 迁移 `513706e4d731` — opportunities.cluster_id 改 nullable
2. 模型同步 Optional；schemas/前端类型同步
3. rebuild 端点：信号重置从循环改批量 `update()`（顺带修掉"未入 join 结果的信号不被重置"的边角漏洞）；新增 `update(Opportunity).values(cluster_id=None)` 断链保留
4. 前端机会卡：cluster_id 为 null 时显示"来源簇已随重建解绑"

**验证**：rebuild 200（3 簇+1 噪声）；被引用的机会存活、rejection_note 完整、cluster_id=None ✅

**遗留提示**：trend_metrics 表也有 cluster_id 外键——当前无数据不触发，写入趋势数据前需同样处理。

### 2026-08-22 — Console 运营控制台完成（功能绑定）

**任务**：把散落在 Swagger 里的运营操作集中成前端控制台，写操作全部进 UI。

**后端新增**：
1. `GET /crawl/jobs` — 最近任务列表（limit 参数，id 倒序）
2. `POST /documents/analyze-batch` — 批量分析所有无信号文档：
   - 重构：抽取 `_analyze_one` 共享管道（单篇/批量共用，不 commit 由调用方定事务边界）
   - `_LowValueSignal` 自定义异常承载低价值短路
   - outerjoin 查无信号文档；先取纯 id 再循环 db.get（rollback 后 ORM 对象失效教训的再应用）
   - 逐篇提交 + try/except，单篇失败不影响其余；返回统计

**前端** `/console`（client component）：
- 抓取区：源下拉（真数据）+ 启动爬取（10 秒后自动刷新任务表）+ 最近任务表（状态徽章/error_message 悬停提示）
- 分析区：单篇分析（422 低价值信息直接展示）+ 批量分析（两步确认 + 统计摘要）
- 聚类评分区：rebuild/rescore 两步确认绑定真实端点
- 数据源管理：新增表单 + 真实源列表
- 统一 `api()` 封装（非 2xx 抛后端 detail）；预览横幅移除

**验证**：tsc 通过；冒烟 GET /crawl/jobs=200(20条)、GET /sources=200(3个)；analyze-batch 未自动化测试（真实 LLM 调用，由用户从 UI 触发）

### 2026-08-22 — Opportunity 工作流完成（Human-in-the-Loop 落地）

**任务**：在"机器发现"和"人的决策"之间修一道正式的门——簇是 AI 产物，机会必须人签字。

**后端**：
1. `models/opportunity.py` — validation_status 默认改 DISCOVERED；新增 rejection_note 列（迁移 `3d13edeaa49c`）
2. `schemas.py` — OpportunityCreate / OpportunityStatusUpdate / OpportunityDraftRequest / Read 补 rejection_note
3. `opportunities.py` 重写 — 四端点：
   - POST "" 创建（簇存在校验 + 占用校验 409 + market_score 快照）
   - GET 列表/详情真查询
   - PATCH status 状态流转：显式 VALID_TRANSITIONS 流转表（11 态状态机），非法跳跃 422；REJECTED 必须带 note；REJECTED 终态、DORMANT 可复活
   - POST /draft — LLM 起草 problem_statement/target_customer/proposed_solution（起草 ≠ 决定）
4. `clusters.py` — GET /{id}/evidence-pack 决策简报（Markdown 导出：簇信息+信号+证据引用）

**前端**：
1. `/opportunities` 双区布局——已确认机会（11 态彩色徽章、否决理由展示）+ 候选簇（未立项的可进入详情升级）
2. `PromoteForm.tsx` 客户端组件——「升级为机会」表单 + 「LLM 起草」按钮（起草后人工修改再提交）
3. 簇详情页集成 PromoteForm
4. 打磨：demands 页 pain_points 徽章（JSON 字符串安全解析）、app/loading.tsx、app/error.tsx（错误边界+重试）

**冒烟测试**（scripts/smoke_opportunities.py，14/14 通过）：
创建→DISCOVERED、重复立项 409、合法流转、非法跳跃 422、否决必填 note、终态拒绝、evidence-pack Markdown、LLM 起草端到端

**过程中修复**：
- Docker 容器停机（电脑重启）→ compose up 拉起
- Start-Process 相对路径按会话目录解析 → 绝对路径
- Invoke-WebRequest 走系统代理导致 localhost 健康检查失败 → Python httpx trust_env=False
- rebuild 全量重建导致簇 ID 漂移 → 冒烟脚本动态选簇（教训：全量重建策略的代价之一）

### 2026-08-22 — Phase 7 扩展数据源（GitHub Issues）完成

**任务**：第二数据源接入，验证 SourceAdapter 架构的可扩展性。

**完成内容**：
1. `app/adapters/github.py` — GitHubAdapter：discover（按评论数排序的 open issues，排除 PR）/ fetch / parse
2. `pipeline.py` normalise — published_at 双格式兼容（unix 秒 + ISO8601→naive UTC 统一）
3. 网络韧性改造：共享 AsyncClient + AsyncHTTPTransport(retries=3) + 分层超时(15s/10s)
4. GITHUB_TOKEN 支持（Fine-grained PAT，公开仓库只读）——匿名 60/时 → 认证 5000/时
5. workers.py except 块加固：rollback 后重新 get job、error_message 带异常类名

**踩坑全记录**（真实世界爬虫故障谱系）：

| 故障 | 根因 | 解法 |
|---|---|---|
| V2EX SSL CERTIFICATE_VERIFY_FAILED | SNI 阻断（浏览器 ECH 能过、Python 明文 SNI 被掐） | certifi 无效；V2EX 挂起待网络环境变化 |
| GitHub 直连失败 | api.github.com 同样被干扰 | 显式 proxy=127.0.0.1:7890 |
| 403 | 匿名额度耗尽（60/时被调试烧光）+ 出口 IP 信誉 | PAT 认证 |
| 'str' cannot be interpreted as int | normalise 新旧代码叠加，旧单行覆盖新逻辑 | 删尸体代码 |
| offset-naive vs offset-aware | fromisoformat 产生 aware datetime 混入 naive 体系 | astimezone(utc).replace(tzinfo=None) 统一 naive UTC |
| ConnectError 空 message | rollback 后 ORM 对象失效导致 except 块二次异常静默死亡 | rollback 后重新 db.get + 异常类名前缀 |

**验收结果**：
- source_id=3 (GitHub VSCode)：items_found≈25 真实 issue 入库 ✅
- 数据特征：issue 标题+正文即结构化需求陈述，信号密度高于论坛帖

**遗留**：V2EX 适配器代码保留（v2ex.py），网络可达后即可启用；多节点 discover 扩展待做

### 2026-08-22 — Evidence 视图 + 簇详情页（Phase 6 增强）

**任务**：补完 Evidence First 闭环——每条需求结论可追溯到原始证据。

**完成内容**：
1. 后端 `GET /clusters/{id}/detail` — 组装型端点：簇信息 + 成员信号（join documents）+ 每信号的证据引用
2. 前端 `app/clusters/[id]/page.tsx` — Next.js 15 动态路由（params 是 Promise 要 await）
3. opportunities 页卡片改 Link 跳转详情

**UI 表达**：证据引用用 blockquote + 绿色竖线 + 斜体——视觉上明确"这是原文摘录"；信号卡标题链接到 HN 原帖。

**过程中修复**：Evidence.signal_id / signa.id 双笔误（列名是 demand_signal_id）；前后端路径不一致 /details vs /detail。

**验收结果**：机会榜 → 簇 4 详情 → 7 个成员信号各带绿色证据引用条，点击标题跳转 HN 原帖 ✅

### 2026-08-22 — Phase 6 Dashboard MVP 完成

**任务**：前端三页接真数据，核心链路可视化。

**完成内容**：
1. `types/index.ts` — 类型定义对齐后端真实 schema（demand_type 单值化、pain_points 改 JSON 字符串、cluster_id 补充、Evidence 接口修正）
2. `app/opportunities/page.tsx` — 机会排行榜：server component + force-dynamic 取数，纯 CSS 五维分数条（零图表库依赖）
3. `app/demands/page.tsx` — Demand Feed：11 类信号彩色徽章（Record<DemandType,string> 穷举检查）、可空字段兜底、未聚类标记
4. `app/page.tsx` — 首页：Promise.all 并行取数 + 统计卡 + 榜首机会高亮卡（Link 跳转）；删除假数据 Trending Topics
5. 🔧 修复 globals.css 缺失（架构精简时误删）——Tailwind 加载链断裂导致全站白屏裸样式

**关键教学点**：
- Server Component 心智模型：页面=文件、async 直接取数、无需 useEffect
- Tailwind 按需生成机制：@tailwind 三指令是入口，类名是构建期查表产物
- 样式链断裂不报错、只是安静地丑着——与功能 bug 的排查方式不同

**验收结果**：
- 三页真数据显示正常（42 docs / 12 signals / 3 clusters / top 69.9）
- 首页榜首卡跳转 opportunities 正常

**遗留优化**（按价值排序）：Evidence 视图 + 簇详情页 → Opportunity 工作流 → 趋势图（等 growth 数据）→ pain_points JSONB 化 → 分页过滤 → 流水线自动化

### 2026-08-22 — Phase 5 需求评分完成

**任务**：给每个需求簇打综合分并排序——"最值得做的机会"浮出水面。

**完成内容**：
1. `app/intelligence/scoring.py` — score() 加权公式（§17 八维权重）+ evaluate_cluster() 混合评估
2. `clusters.py` — POST /clusters/rescore 全量评分端点；GET /clusters 改按 demand_score 排序

**关键设计决策——混合评分策略**：
- 数据驱动（5 维）：pain=severity 均值、frequency/market_reach=计数归一化、wtp=均值(null→3.0 保守底分)、evidence=均值
- LLM 推理（2 维）：competition_gap + technical_feasibility（基于簇描述评估）
- MVP 占位（1 维）：growth=5.0 中性分（数据量不足以算趋势）
- Evidence First 落地：能用数据的不让 LLM 猜

**验收结果**：
- "Unexpected platform behavior" 69.9 登顶（frequency=10 杠杆 + gap=7）
- "Loss of coding joy" 55.1（pain=8.5 全场最高但小众）
- "Unified longitudinal tracking" 55.1（money=8 唯一有付费信号）
- LLM 维度有区分度（gap: 7/8/6），非敷衍输出

### 2026-08-22 — Phase 4 需求聚类完成

**任务**：语义相似的需求信号聚合成簇，LLM 自动命名——从碎片信号到需求主题。

**完成内容**：
1. `app/intelligence/clustering.py` — cluster_vectors（sklearn HDBSCAN, min_cluster_size=2 小样本参数）+ name_clusters（LLM 簇命名）
2. DemandSignal 加 cluster_id 外键列（迁移）
3. `clusters.py` — POST /clusters/rebuild 全量重建编排 + GET 真查询
4. 旧占位 cluster_signals 退役删除

**关键设计决策**：
- sklearn 内置 HDBSCAN 而非独立 hdbscan 包；euclidean 度量（归一化向量上与余弦距离数学等价）
- 全量重建策略：先解除 signal 引用 → flush → 删旧簇 → 重算重挂（外键依赖决定顺序）
- 手动触发端点，参数调稳前不自动化

**过程中修复的问题**：
- `'coroutine' object is not iterable` — 纯 CPU 函数误用 async def（判断标准：IO 用 async，CPU 用同步）
- DeepSeek JSON mode 400 — prompt 必须字面包含 "json" 一词
- `label.count` vs `labels.count` — 单复数变量名陷阱
- ForeignKeyViolationError — 删被引用行前必须先解除引用（flush 时序知识点再现）

**验收结果**：
- POST /clusters/rebuild → {"clusters_built": 3, "noise_signals": 1}
- 簇命名质量（LLM 抽象能力）：
  - "Unexpected platform behavior" ×7 —— 7 个不同作者的平台抱怨归一
  - "Loss of coding joy" ×2 —— AI 编程体验伤害的微妙共性
  - "Unified longitudinal tracking" ×2 —— 从具体混乱归纳出潜在需求
- unique_user_count 与 document_count 一致性验证通过

### 2026-08-22 — 数据扩充 + analyze 幂等修复

**任务**：为 Phase 4 聚类积累数据；修复批量分析暴露的重复信号 bug。

**完成内容**：
1. `app/adapters/hn.py` — discover 改多矿脉聚合：askstories(20) + showstories(20) + newstories(20)。Ask/Show HN 的需求信号密度远高于 news 流（信号率从 3/25 提升到 9/17）
2. `documents.py` analyze 端点 **upsert 化**：查已有 signal → 有则覆盖更新 / 无则新建；Evidence 删旧插新。语义 = "重新分析 = 刷新结果"，支持将来 prompt 调优后全量重跑
3. `embedder.py` — get_model 升级 local-first：先 `local_files_only=True` 纯本地加载，缓存缺失才联网下载。HF_HUB_OFFLINE 环境变量退役（会拦截兜底下载），README 同步更新
4. 存量数据清理：删除 doc 4 的 2 条重复 signal + 关联 evidence（psql 手术）

**验收结果**：
- 42 文档 / 12 信号 / 12 向量——信号向量化率 100%
- 信号类型分布：complaint×6, pain×2, feature_request/alternative_search/unmet_need/workaround 各×1（11 类中出现 6 类）
- 对 doc 4 重复 analyze → 记录数不变、内容刷新 ✅

### 2026-08-22 — Phase 3 Embedding（pgvector）完成

**任务**：文档向量化 + 相似需求搜索，为 Phase 4 聚类打地基。

**完成内容**：
1. `app/intelligence/embedder.py` — 本地 embedding（all-MiniLM-L6-v2, 384 维）：embed 单条 + embed_batch 批量；@lru_cache 模型单例；asyncio.to_thread 防 CPU 推理阻塞事件循环
2. 迁移 `4d81458701d7` — documents 表加 `embedding vector(384)` 列（nullable）+ CREATE EXTENSION IF NOT EXISTS vector
3. analyze 端点接入向量化（commit 前算向量随事务落库）
4. `GET /documents/{id}/similar` — cosine_distance（pgvector `<=>`）排序相似搜索

**关键设计决策**：
- **本地方案**（sentence-transformers）而非 API：零成本、离线、批量无顾虑
- **低价值文档不向量化**：422 短路在 embed 之前——noise 不配建索引；raw_documents 保留原文，随时可幂等补算
- **HF_HUB_OFFLINE=1 固化**：模型下载完成后彻底离线运行（已写入 README"Embedding 环境变量"节）

**过程中踩的坑与修复**：

| 问题 | 根因 | 解法 |
|---|---|---|
| transformers v5 import 链崩溃（sympy/DTensor） | 最新版互相打架 | 钉版本 `transformers<5` |
| hf-mirror.com 直连超时 / 走代理 SSL EOF | curl 不走系统代理而 Python requests 走——两条路径一通一堵 | 关代理直连官方站成功 |
| 下载中途断连 | 网络链路不稳 | 备选方案 ModelScope（未启用） |
| `CREATE EXTENSION vector` 报 not available | docker-compose 用了普通 postgres:16-alpine 镜像 | 换 `pgvector/pgvector:pg16` 重建容器（named volume 数据无损） |
| ImportError: embedding vs embedder | 新旧模块并存名字太像 | 删旧占位 embedding.py，函数合并进 embedder.py |

**附带工程事项**：
- Docker Desktop 磁盘迁移 C→D 盘（WSL2 vhdx，8.8GB），验证数据完好
- HF 三环境变量（HF_HOME/HF_ENDPOINT/HF_HUB_OFFLINE）写入 .env.example 与 README

**验收结果**：
- 25 篇文档全量 analyze：3 篇产出信号并向量化（id 4/9/17），其余被分类器正确判为新闻/观点（HN 数据源特性）
- doc 4 similar 搜索：doc 17（LLM 可靠性主题，高度相关）排第一 > doc 9（内存优化，弱相关）排第二——排序与人肉判断一致 ✅

### 2026-08-21 — Phase 2 LLM 需求识别完成

**任务**：把爬到的文档变成结构化需求信号（classify → extract → demand_signals 表）。

**完成内容**：
1. `app/intelligence/llm_client.py` — OpenAI 兼容客户端封装（单例 AsyncOpenAI + JSON mode + markdown 剥壳防御），一套代码适配 DeepSeek/Kimi/MiMo 等所有兼容 provider
2. `app/config/settings.py` — LLM_BASE_URL / LLM_API_KEY / LLM_MODEL 三变量切换 provider
3. `app/intelligence/classifier.py` — 11 类需求分类 + confidence + 枚举校验兜底
4. `app/intelligence/extractor.py` — 结构化抽取（problem/pain_points/severity/evidence_quote 等，Evidence First 硬规则）
5. `app/api/routes/documents.py` — POST /documents/{id}/analyze（分类→低价值短路→抽取→DemandSignal+Evidence 同事务落库）
6. `app/api/routes/demands.py` — GET 列表/详情真查询

**关键设计决策**：
- **OpenAI 兼容统一接入**：一个 SDK 覆盖所有 provider，换模型只改 .env 三个值
- **手动触发先行**：LLM 调用花钱且慢，先做单篇 analyze 端点调 prompt，调稳后再挂批量流程
- **temperature=0.1**：分类/抽取要稳定不要创造性
- **flush→commit 时序**：signal flush 拿 id → evidence 挂外键 → 单次 commit，两表同生共死

**Prompt 工程四段式**（沉淀的方法论）：角色 → 类别/字段定义 → 严格 JSON schema → 边界规则。类别 value 与 DemandType 枚举逐字一致，代码校验兜底。

**过程中修复的问题**：

| 问题 | 根因 | 教训 |
|---|---|---|
| NameError: CLASSIFIER_SYSTEM_PROMPT 未定义 | 只写了调用没写常量 | prompt 是模块级资产，先定义后引用 |
| db.add() 报错 | 把 Pydantic Read schema 当 ORM 模型传 | Read/Create 结尾 = API 进出口；db.add() 只认 models 类 |
| signal 与 evidence 分两次 commit | flush/commit 顺序理解错 | flush=探路拿 id，commit=正式落库；探路永远在落库前 |
| analyze 端点路径语义混乱 | 放在 /demands 下但参数是 document_id | REST 语义：对谁操作就挂在谁的资源下 |
| pain_points list 存 Text 列 | 类型不匹配 | json.dumps 序列化后存 |

**验收结果**：
- 分类质量：feature_request(0.95) / pain(0.85) / noise(0.95)，三样本全对 ✅
- POST /documents/{id}/analyze → 完整需求信号入库 ✅
- demand_signals + evidences 两表同事务写入 ✅

### 2026-08-21 — Phase 1 第一个数据源（Hacker News）完成

**任务**：实现第一条完整数据链路：发现 → 抓取 → 解析 → 标准化 → 存储。

**开发模式**：用户自己写代码，Sisyphus 指导（规格讲解 + 逐轮审查）。

**完成内容**：
1. `app/extraction/pipeline.py` — clean_text / parse_content / normalise 三函数（用户实现，3 轮审查修复）
2. `app/adapters/hn.py` — HackerNewsAdapter（discover/fetch/parse），替代被墙的 Reddit
3. `app/crawling/workers.py` — process_job 完整爬取流程（去重 + Author upsert + failed 兜底）
4. `app/api/routes/crawl.py` — POST /crawl/jobs（asyncio.create_task 后台执行）+ GET /crawl/jobs/{id}
5. `app/api/routes/sources.py` / `documents.py` — 真实 CRUD 替换占位

**数据源决策变更**：Reddit 因国内网络被墙（403，IP 层封锁）+ 官方 API 注册受限（Responsible Builder Policy），改用 Hacker News Firebase API 作为第一个数据源。Reddit 适配器保留，Phase 7 再接。

**过程中修复的问题**：

| 问题 | 根因 | 修复 |
|---|---|---|
| alembic 循环导入 | db/base.py 与 models/*.py 双向依赖 | base.py 只留 Base；模型注册归 models/__init__.py；env.py 显式 import app.models |
| `No adapter registered for hackernews` | hn.py 的 register() 被注释；注册器模式需模块被 import 才生效 | adapters/__init__.py 集中导入所有适配器模块触发注册 |
| normalise 返回 None | 映射表只有 reddit 键，hackernews 走隐式返回 None | 重构为通用映射（parse 已做源特定提取，normalise 只做统一补全） |
| GET /documents 500 | `.order_by()` 链在 await execute 之后 | order_by 移入 select() 构建链 |
| 307 重定向 | 路由路径 "/" + prefix 导致尾斜杠重定向 | 路径改空字符串 "" |
| curl JSON 报错 | cmd 下 PowerShell 转义不兼容 | 改用 Swagger UI 测试 |

**验收结果**：
- POST /sources 创建 HN 数据源 ✅
- POST /crawl/jobs → status=completed, items_found=25, items_stored=25 ✅
- documents 表 25 条真实 HN 帖子（title/content/engagement_score/content_hash）✅
- raw_documents 表 25 条原始 payload（可追溯层）✅

**遗留事项**：
- 时区：数据库存 UTC（约定），前端显示时转本地时间（Phase 6）
- tests/reddit_test.py、tests/hn_test.py 为临时脚本风格，后续转正式 pytest
- CrawlQueue/crawl_worker 仍为占位（MVP 用 asyncio.create_task，Redis 队列 Phase 后期接）

### 2026-08-20 — Phase 0 基础设施就绪

**任务**：启动 PostgreSQL + Redis，生成并应用初始数据库迁移。

**完成内容**：
1. Docker Desktop 启动，`docker compose up -d` 拉起 PostgreSQL 16.15 (pgvector) + Redis 7，均 healthy
2. 后端连接 PostgreSQL 验证成功（asyncpg）
3. 修复 `migrations/` 缺失 `script.py.mako` 模板（alembic 生成迁移必需）
4. `alembic revision --autogenerate` 生成初始迁移 `b0b66afc91a3`
5. `alembic upgrade head` 应用迁移，10 张表创建成功

**验证结果**：

| 检查项 | 结果 |
|---|---|
| Docker 容器健康 | ✅ mie-postgres / mie-redis healthy |
| PostgreSQL 连接 | ✅ PostgreSQL 16.15 |
| 初始迁移生成 | ✅ b0b66afc91a3_initial_schema.py |
| 迁移应用 | ✅ 10 张表创建 |
| 数据库表 | ✅ sources/crawl_jobs/raw_documents/documents/authors/demand_signals/demand_clusters/evidences/opportunities/trend_metrics |

**过程中修复的问题**：

| 问题 | 修复 |
|---|---|
| alembic 报 `No 'script_location' key found` | 用户从根目录执行，需 `cd backend` 再执行 |
| alembic 报 `No such file: migrations/script.py.mako` | 补上标准 alembic 模板文件 |

**开发模式变更**：用户要求改为**指导模式**——用户自己开发，Sisyphus 只做规划/解释/审查，不直接实现代码（已记录到 USER_PREFERENCES.md）。

### 2026-08-20 — 架构优化（精简）

**任务**：用户反馈架构偏复杂，要求"保证核心功能能够实现的前提下优化架构"。

**优化内容**：

| 模块 | 优化前 | 优化后 | 说明 |
|---|---|---|---|
| models/ | 13 文件 / 13 表 | 4 文件 / 10 表 | 按域合并（source/document/demand/opportunity），删 topic/user_segment/llm_run 3 张后加表 |
| schemas/ | 6 文件 | 1 文件 schemas.py | 全部 Create/Read 类合并 |
| repositories/ | 6 文件 | 删除 | 过度分层，routes 直接调 session |
| services/ | 2 文件 | 删除 | 空壳，逻辑并入 intelligence |
| adapters/ | 6 文件 | 2 文件 | base.py(含 registry) + reddit.py，删 github/v2ex/hackernews 占位（Phase 7 再加） |
| crawling/ | 3 文件 | 2 文件 | queue 并入 workers.py |
| extraction/ | 3 文件 | 1 文件 pipeline.py | cleaner/parser/normalizer 合并 |
| intelligence/ | 5 文件 | 5 文件 | 保留（核心流水线） |
| api/routes/ | 7 文件 | 7 文件 | 保留（API 是核心） |
| 前端页面 | 6 页面 | 3 页面 | 删 clusters/trends/evidence，功能并入 Dashboard/Demands/Opportunities |

**优化成果**：
- 后端：72 文件 928 行 → **36 文件 653 行**（文件 -50%，行数 -30%）
- 前端：12 文件 594 行 → **9 文件 419 行**
- 核心功能全部保留：10 张核心表 + 13 个 API 端点 + 采集/清洗/分类/提取/聚类/评分/机会/证据链路

**过程中修复的问题**：

| 问题 | 修复 |
|---|---|
| SQLAlchemy 2.0.52 中 `mapped_column(default_factory=...)` 报 ArgumentError | 改用 `default=datetime.utcnow`（`default_factory` 是 dataclass 专用参数）。此问题在优化前就存在（pytest 只测 /health 未加载 models，未暴露） |
| PowerShell `Set-Content` 默认 ANSI 编码损坏 UTF-8 中文注释 | 用 write 工具（UTF-8）重写模型文件 |

**验证结果**：

| 检查项 | 结果 |
|---|---|
| 后端导入 + 10 张表 + 13 端点 | ✅ 通过 |
| pytest 健康检查 | ✅ 1 passed |
| ruff 代码检查 | ✅ 0 错误 |
| LSP 诊断（36 文件） | ✅ 0 错误 |
| 前端 `npm run build` | ✅ 3 页面生成 |

### 2026-08-20 — 框架搭建完成

**任务**：阅读设计文档，搭建完整可运行的项目框架（用户要求：只搭框架，不写完整实现）。

**完成内容**：

1. **后端 FastAPI 骨架**（`backend/`，84 文件）
   - 入口 `app/main.py`：CORS + `/health` + 7 个路由挂载
   - 配置 `app/config/settings.py`：Pydantic Settings，.env 加载
   - 数据层 `app/db/`：async engine + session + DeclarativeBase
   - 模型 `app/models/`：13 张表（sources, documents, demand_signals, demand_clusters, opportunities, evidences, crawl_jobs, raw_documents, authors, topics, user_segments, trend_metrics, llm_runs）
   - Schema `app/schemas/`：Pydantic v2 Create/Read 模型
   - API `app/api/routes/`：13 个端点（对应设计文档 §32）
   - 仓储 `app/repositories/`：6 个数据访问层
   - 服务 `app/services/`：demand_service, opportunity_service
   - 适配器 `app/adapters/`：SourceAdapter ABC + reddit/github/v2ex/hackernews 占位
   - 爬取 `app/crawling/`：scheduler / queue / workers 骨架
   - 抽取 `app/extraction/`：cleaner / parser / normalizer 骨架
   - 智能 `app/intelligence/`：classifier(11类) / extractor / embedding / clustering / scoring(§17 权重)
   - 迁移 `migrations/`：alembic 配置
   - 测试 `tests/`：健康检查冒烟测试
   - Prompt 模板 `prompts/`：classifier / extractor / scoring

2. **前端 Next.js 骨架**（`frontend/`，20 文件）
   - 6 个页面：Dashboard / Demands / Clusters / Opportunities / Trends / Evidence
   - 3 个组件：Sidebar / StatCard / PageHeader
   - `src/lib/api.ts`：API 客户端封装（6 个函数签名）
   - `src/types/index.ts`：TS 类型定义

3. **基础设施**
   - `docker-compose.yml`：PostgreSQL 16 (pgvector) + Redis 7，含 healthcheck 与持久化 volume
   - `docker/`：backend/frontend Dockerfile + init-pgvector.sh
   - `.env.example` / `.gitignore` / `README.md`

4. **文档**
   - `docs/requirements-trace.md`：25 条需求追踪矩阵（REQ-001 ~ REQ-025）

**验证结果**：

| 检查项 | 结果 |
|---|---|
| `uv sync` 依赖安装 | ✅ 通过 |
| 后端导入 + OpenAPI 13 端点 | ✅ 通过 |
| pytest 健康检查 | ✅ 1 passed |
| ruff 代码检查 | ✅ 0 错误 |
| LSP 诊断（50 文件） | ✅ 0 错误 |
| 前端 `npm run build` | ✅ 7 页面生成 |
| docker-compose 配置校验 | ✅ 有效 |

**过程中修复的问题**：

| 问题 | 修复 |
|---|---|
| `uv sync` 报 hatchling 找不到包 | `pyproject.toml` 增加 `[tool.hatch.build.targets.wheel] packages = ["app"]` |
| pytest 报 `No module named 'app'` | `pyproject.toml` 增加 `[tool.pytest.ini_options] pythonpath = ["."]` |
| `test_health.py` 导入错误 | `from tests.conftest` → `from conftest` |

---

## 当前状态快照（2026-09-12 更新，替代 2026-09-09 旧快照）

### 已完成
- ✅ 基础设施：PostgreSQL + Redis + Docker（host 端口 15432/16379，避开 Windows 保留段）
- ✅ 数据源：6 适配器全跑通（HN/GitHub/V2EX/掘金/知乎/Reddit），源级配置化 + 增量 + 速率限制 + 深度
- ✅ 爬取调度：APScheduler + 孤儿清理 + 重试退避 + 单 URL 容错 + 源健康度
- ✅ 需求识别流水线：分类/抽取/嵌入/聚类/评分全链路
- ✅ 去重：content_hash 精确 + pgvector 语义（余弦 ≥ 0.95）双层兜底（2026-09-10 收尾）
- ✅ 机会引擎：状态机（11 态）+ 可行性分析（总结反馈，中文输出）+ relink 断链修复（2026-09-10）
- ✅ 趋势检测：GET /trends 实时计算 7/30/90 天信号增长率（2026-09-09 收尾）
- ✅ 前端：5 页面 + console 全部接真实 API；落地页 + 仪表盘视觉打磨与 UX 优化（骨架屏/空错误状态/响应式/交互反馈/信息层级，2026-09-12）
- ✅ 端口：winnat 动态保留段永久修复（动态端口 49152-65535），后端 8100 / 前端 3000 正常（2026-09-12）
- ✅ 需求追踪矩阵：26 条需求（REQ-001~026），25 条实现，1 条从 MVP 移除
- ✅ 契约测试：13 passed（test_adapters）+ pytest 14 passed + 2 skipped（2026-09-10）

### 待办 / 阻塞项
- ⏳ **CrawlQueue Redis 队列**：enqueue/dequeue/get_status 为占位（NotImplementedError）；调度器已绕过它直接调用 process_job，功能正常，属架构简化
- ✅ **github 源代理**：已修复（759aa9f）——config `"proxy": ""` = 禁用代理直连，缺省 = 默认 `127.0.0.1:7890`；服务器无代理时留空即可
- ⏳ **知乎 Cookie 时效**：z_c0 会过期（约 6 天），需定期刷新；已有 `scripts/configure_zhihu_cookie.py` 校验工具

### 决策记录
| 日期 | 决策 | 原因 |
|---|---|---|
| 2026-08-20 | 使用 Harness 工具链 | 用户确认，创建 `.harness-activated` |
| 2026-08-20 | 只搭框架，不写完整实现 | 用户明确要求 |
| 2026-08-20 | 后端采用 monolith 结构（非微服务） | 符合设计文档 §42 原则 |
| 2026-09-08 | 机会可行性分析（总结反馈） | 高 demand_score ≠ 可实现，需深入分析辅助人决策 |
| 2026-09-09 | 后端端口 8101→8106 | winnat 保留段复发封锁 8100/8101 |
| 2026-09-09 | GET /trends 实时计算 | 数据量小，实时算比落表更简单准确 |
| 2026-09-10 | 机会 #3 断链修复（relink） | rebuild 删旧簇致 cluster_id 置空，需自动/人工重挂 |
| 2026-09-10 | pgvector 语义去重 | content_hash 精确去重之外的语义兜底层（REQ-004） |
| 2026-09-12 | winnat 动态端口永久修复 | 保留段随机漂移反复封锁 8000/8100/8101/3000，一劳永逸 |
| 2026-09-12 | 前端视觉打磨 + UX 优化 | 用户确认两者都打磨、UX 五项全选 |
| 2026-09-14 | 生产部署半自动（Human-in-the-Loop） | 用户反对全自动按时触发（担心 API 额度滥用）；保留播种+初始爬取，关闭周期调度与自动分析 |

---

## 下一步计划（对应设计文档 §30/§41）

| Phase | 内容 | 前置条件 |
|---|---|---|
| 0 | 基础设施就绪（数据库 + Redis） | 选定方案 A/B/C |
| 1 | Reddit 适配器实现（发现→抓取→解析→存储） | 数据库就绪 |
| 2 | LLM 需求识别（分类 + 抽取） | LLM_API_KEY 配置 |
| 3 | Embedding + pgvector 相似搜索 | PostgreSQL 就绪 |
| 4 | 需求聚类（10000 posts → 500 signals → 50 clusters） | Phase 3 完成 |
| 5 | 需求评分 + 趋势检测 | Phase 4 完成 |
| 6 | Dashboard 接入真实 API | Phase 5 完成 |
| 7 | 扩展数据源（GitHub → V2EX → HN → PH → App Store） | 核心链路稳定 |

---

## 质量门禁记录

| 日期 | 检查 | 结果 |
|---|---|---|
| 2026-08-20 | ruff + pytest + LSP + 前端构建 | ✅ 全部通过 |
| 2026-09-08 | 契约测试 13 passed + tsc 0 错误 + Playwright 实测 | ✅ 通过 |
| 2026-09-10 | pytest 14 passed + 2 skipped + tsc 0 错误 + relink 三分支实测 | ✅ 通过 |
| 2026-09-12 | tsc 0 错误 + next build 0 错误 + Playwright 双页面 QA（导航/锚点/数据/图表/移动端） | ✅ 通过 |
| 2026-09-14 | pytest 18 passed + 2 skipped + LSP 零诊断 + openapi 25 端点 | ✅ 通过 |

*最后更新：2026-09-14*
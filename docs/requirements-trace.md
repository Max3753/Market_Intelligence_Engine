# MIE 需求追踪矩阵

> 来源：Market_Intelligence_Engine.md（v0.1, 2026-08-19）
> 生成日期：2026-08-20（架构优化后更新）
> 最近更新：2026-09-12（REQ-004 语义去重收尾、趋势实时计算决策、前端打磨）
> 状态：MVP 全链路完成（Phase 0-7 全部落地）

## 需求追踪矩阵

| 需求ID | 需求描述 | 文档章节 | 优先级 | 验收标准 | 代码位置 | 状态 |
|--------|----------|----------|--------|----------|----------|------|
| REQ-001 | 监控指定互联网数据源 | §2.1 | P0 | 可配置数据源列表 | `app/models/source.py`, `app/api/routes/sources.py` | ✅ 实现（3 源入库） |
| REQ-002 | 定期采集新增内容 | §2.1 | P0 | 按 crawl_interval 调度 | `app/crawling/scheduler.py` | ✅ 实现（APScheduler 注册活跃源） |
| REQ-003 | 抽取正文/标题/作者/时间/互动数据 | §2.1 | P0 | 统一 NormalizedDocument 结构 | `app/extraction/pipeline.py` | ✅ 实现 |
| REQ-004 | 内容清洗与去重 | §2.1, §9 | P0 | URL/SourceID/Hash/语义四层去重 | `app/extraction/pipeline.py` | ✅ 实现（content_hash 精确 + pgvector 语义双层去重，2026-09-10 收尾） |
| REQ-005 | 需求信号分类 | §2.1, §10 | P0 | 11 类分类，Precision ≥ 80% | `app/intelligence/classifier.py` | ✅ 实现 |
| REQ-006 | 提取用户群/问题/场景/痛点/方案 | §2.1, §11 | P0 | LLM 结构化输出 | `app/intelligence/extractor.py` | ✅ 实现 |
| REQ-007 | 相似需求聚类 | §2.1, §15 | P0 | Embedding + 相似度聚类 | `app/intelligence/clustering.py` | ✅ 实现（HDBSCAN，3 簇） |
| REQ-008 | 需求强度计算 | §2.1, §17 | P0 | 8 指标加权评分 0-100 | `app/intelligence/scoring.py` | ✅ 实现（当前数据需 rescore） |
| REQ-009 | 趋势检测（7/30/90 天） | §2.1, §20 | P0 | 增长率计算 | `app/api/routes/trends.py` | ✅ 实现（FK 已解耦 08-29；GET /trends 实时计算 7/30/90 天，2026-09-09 收尾） |
| REQ-010 | 产品机会列表输出 | §2.1, §19 | P0 | Opportunity 生成 | `app/api/routes/opportunities.py` | ✅ 实现（Human-in-the-Loop 状态机） |
| REQ-011 | 完整证据链保留 | §2.1, §12 | P0 | Demand→Evidence→Source→原文 | `app/models/demand.py` (Evidence) | ✅ 实现 |
| REQ-012 | 数据源适配器架构 | §5 | P0 | 统一 SourceAdapter 接口 | `app/adapters/base.py` + reddit/github/hn/v2ex/juejin/zhihu | ✅ 实现（6 源全跑通；源级配置化 config JSON + 增量 + 速率限制 + 深度） |
| REQ-013 | Raw 数据层 | §8.1 | P0 | 原始数据可追溯可重处理 | `app/models/document.py` (RawDocument) | ✅ 实现 |
| REQ-014 | 标准化内容层 | §8.2 | P0 | 统一内容结构 | `app/models/document.py` (Document) | ✅ 实现 |
| REQ-015 | 用户群体识别 | §13 | P1 | 预置 + 动态创建 | 已从 MVP 移除 | ⏳ 待实现 |
| REQ-016 | 需求生命周期管理 | §28 | P1 | DISCOVERED→VALIDATED→MVP | `app/models/opportunity.py` | ✅ 实现（11 态状态机） |
| REQ-017 | 人工审核反馈 | §29 | P1 | 修改/合并/拆分/评分调整 | `app/api/routes/demands.py` | ✅ 实现 |
| REQ-018 | 数据质量控制 | §26 | P1 | Data Quality Score | `app/extraction/pipeline.py` | ✅ 实现 |
| REQ-019 | Spam/Noise 过滤 | §27 | P1 | 广告/SEO/机器人过滤 | `app/intelligence/classifier.py` | ✅ 实现 |
| REQ-020 | Dashboard 展示 | §22, §33 | P1 | Overview/Feed/Explorer/Ranking/Trend | `frontend/src/app/`（5 页面 + console） | ✅ 实现（接真实 API） |
| REQ-021 | API 服务 | §32 | P0 | 13 个 REST 端点 | `app/api/routes/`（7 路由文件） | ✅ 实现（超 13 端点） |
| REQ-022 | 爬取任务管理 | §32 | P0 | 创建/查询 crawl jobs | `app/api/routes/crawl.py` | ✅ 实现（3 端点） |
| REQ-023 | LLM 流水线分层 | §24 | P0 | 分类→抽取→标准化→嵌入→聚类 | `app/intelligence/` | ✅ 实现 |
| REQ-024 | LLM Prompt 原则 | §25 | P0 | 证据引用/无证据输出 null | `prompts/*.md` | ✅ 实现 |
| REQ-025 | 基础设施 | §30 Phase 0 | P0 | PostgreSQL+Redis+Docker | `docker-compose.yml` | ✅ 实现（迁移链 6 个） |
| REQ-026 | 机会可行性分析（总结反馈） | §19 扩展 | P1 | LLM 基于证据链评估机会可实现性（demand_score 高≠可实现），输出可行性评分/技术/市场/竞争/风险/假设/行动建议 | `app/intelligence/opportunity_analyzer.py`, `app/models/opportunity.py` (OpportunityAnalysis), `app/api/routes/opportunities.py` (POST /opportunities/{id}/analyze), `frontend/src/components/OpportunitiesList.tsx` | ✅ 实现（2026-09-08；中文输出 2026-09-09） |

## 覆盖缺口

- **REQ-015 用户群体**：user_segments 表已从 MVP 移除，需要时再加
- **github 源代理**：适配器默认走 `127.0.0.1:7890`（config.proxy 可覆盖），代理未开时爬取失败（ConnectError，环境问题非代码问题）
- **CrawlQueue Redis 队列**：enqueue/dequeue/get_status 为占位（NotImplementedError）；调度器已绕过它直接调用 process_job，功能正常，属架构简化

## 已收尾缺口（历史）

- **REQ-004 语义去重**：content_hash 精确去重 + pgvector 语义去重（余弦 ≥ 0.95）双层兜底，2026-09-10 完成
- **trend_metrics 数据写入**：2026-09-09 决策改为 **GET /trends 实时计算**（数据量小，实时算比落表更简单准确），不再落表；trend_metrics 表保留（cluster_id 可空）

## 开发路线映射（§30/§41）

| Phase | 需求 | 状态 |
|-------|------|------|
| 0 基础设施 | REQ-025 | ✅ 完成 |
| 1 第一个数据源 (HN) | REQ-001/002/003/013/014 | ✅ 完成（HN 替代被墙的 Reddit） |
| 2 需求识别 | REQ-005/006/023/024 | ✅ 完成 |
| 3 Embedding | REQ-004/007 | ✅ 完成（pgvector 相似搜索） |
| 4 Cluster | REQ-007 | ✅ 完成 |
| 5 Scoring | REQ-008/009 | ✅ 完成（趋势实时计算 2026-09-09） |
| 6 Dashboard | REQ-020/021 | ✅ 完成（+ Console 控制台） |
| 7 扩展数据源 | REQ-012 | ✅ 完成（GitHub/HN/掘金/知乎/V2EX 全跑通；源级配置化 + 增量 + 速率限制 + 深度） |
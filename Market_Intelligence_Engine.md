# Market Intelligence Engine

> 面向“市场需求驱动型项目开发”的市场情报与需求发现系统设计文档  
> 版本：v0.1  
> 日期：2026-08-19

---

## 1. 项目概述

### 1.1 项目定位

**Market Intelligence Engine（MIE）** 是一个面向开发者、独立开发者、创业团队和产品团队的**自动化市场需求发现系统**。

它的核心目标不是“爬网页”，而是：

> 从互联网中持续采集真实用户表达，识别用户痛点、需求、抱怨、替代方案和付费信号，并最终形成可验证的产品机会。

核心链路：

```text
互联网数据源
    ↓
数据采集
    ↓
内容抽取
    ↓
清洗与标准化
    ↓
去重
    ↓
需求识别
    ↓
痛点/场景/人群提取
    ↓
需求聚类
    ↓
趋势分析
    ↓
需求评分
    ↓
产品机会发现
    ↓
人工验证
    ↓
MVP
```

### 1.2 核心原则

1. **Evidence First**：证据优先，而不是凭空生成需求。
2. **User Behavior > User Opinion**：真实行为优于主观意愿。
3. **Demand > Feature**：优先识别问题和任务，而不是功能愿望。
4. **Frequency + Pain + Money**：高频、强痛、已有成本的问题优先。
5. **Human in the Loop**：AI 做发现和整理，人做最终判断。
6. **Source Traceability**：每个需求结论都必须可以追溯到原始证据。
7. **Incremental Discovery**：持续监控市场变化，而不是一次性调研。
8. **Validation Before Development**：进入开发前必须经过验证。

---

# 2. 产品目标

## 2.1 第一阶段目标

建立一个能够自动完成以下工作的系统：

- 监控指定互联网数据源
- 定期采集新增内容
- 抽取正文、标题、作者、时间、互动数据等
- 对内容进行清洗和去重
- 判断内容是否包含市场需求信号
- 提取用户群体、问题、场景、痛点和当前解决方案
- 将相似需求聚类
- 计算需求强度
- 发现增长中的需求主题
- 输出产品机会列表
- 保留完整证据链

## 2.2 非目标

MVP 阶段暂不追求：

- 全网爬取
- 自动绕过验证码
- 大规模代理池
- 自动联系用户
- 自动做出最终创业决策
- 完全由 AI 替代产品经理

系统定位是：

> **Decision Support System，而不是 Decision Maker。**

---

# 3. 核心用户

## 3.1 独立开发者

典型需求：

> “我想找一个值得做的小型 SaaS 项目。”

需要：

- 小而明确的需求
- 真实用户
- 低竞争
- 明确付费信号
- 技术可实现

## 3.2 创业团队

典型需求：

> “我们准备进入某个市场，希望找到未被很好满足的需求。”

需要：

- 市场趋势
- 竞争格局
- 用户痛点
- 竞品缺陷
- 用户迁移信号

## 3.3 产品经理

需要：

- 高频用户问题
- Feature Request
- 用户投诉
- 用户流失原因
- 产品机会

## 3.4 技术团队

需要：

- 从开发者社区发现真实工具需求
- API / SDK / DevTool 痛点
- GitHub Issues
- 技术工作流中的重复劳动

---

# 4. 数据源策略

MVP 不建议一开始全网爬取。

优先选择：

| 数据源 | 价值 | 类型 | MVP |
|---|---|---|---|
| Reddit | 高 | 用户讨论/痛点 | P0 |
| GitHub | 高 | Issue/Feature Request | P0 |
| V2EX | 高 | 中文开发者讨论 | P0 |
| Hacker News | 高 | 技术/创业讨论 | P1 |
| Product Hunt | 高 | 新产品/评论 | P1 |
| App Store | 高 | 用户评价 | P1 |
| Google Play | 高 | 用户评价 | P1 |
| 知乎 | 中高 | 中文问答 | P2 |
| 小红书 | 中高 | 消费/生活场景 | P2 |
| 行业论坛 | 高 | 垂直行业 | P2 |

优先级原则：

```text
P0 = 第一版必须有
P1 = MVP 稳定后加入
P2 = 验证核心模型后加入
```

---

# 5. 数据源适配器架构

不同网站不要写成一个巨型爬虫。

采用统一的：

```text
Source Adapter
```

接口。

示例：

```python
class SourceAdapter:
    name: str

    async def discover(self):
        pass

    async def fetch(self, url):
        pass

    async def parse(self, response):
        pass
```

目录：

```text
adapters/
├── reddit/
├── github/
├── v2ex/
├── hackernews/
├── producthunt/
└── appstore/
```

这样新增数据源不会影响核心系统。

---

# 6. 推荐技术栈

## 6.1 MVP

推荐：

```text
Python
├── Crawlee
├── Playwright
├── FastAPI
├── PostgreSQL
├── Redis
├── SQLAlchemy
├── Pydantic
└── LLM API
```

## 6.2 调度

任务量较小时：

```text
APScheduler + Redis
```

规模增加后：

```text
Celery / ARQ
```

## 6.3 前端

推荐：

```text
Next.js
+
TypeScript
+
Tailwind CSS
```

---

# 7. 系统总体架构

```text
                         ┌─────────────────────┐
                         │      Data Sources   │
                         │ Reddit / GitHub ... │
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │   Source Adapters   │
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │ Crawling Scheduler  │
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │ Crawlee / Playwright│
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │   Raw Data Layer    │
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │ Clean & Normalize   │
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │ Deduplication       │
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │ Content Classifier  │
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │ Demand Extraction   │
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │ Embedding / Cluster │
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │ Demand Scoring      │
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │ Opportunity Engine  │
                         └──────────┬──────────┘
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │ Dashboard / Reports │
                         └─────────────────────┘
```

---

# 8. 数据处理流水线

## 8.1 Raw Layer

保存原始数据。

目的：

- 可追溯
- 可重新处理
- 模型升级后重新分析
- 避免重复抓取

示例：

```json
{
  "source": "reddit",
  "source_id": "abc123",
  "url": "https://...",
  "raw_content": "...",
  "captured_at": "2026-08-19T10:00:00Z"
}
```

## 8.2 Normalized Layer

转换成统一内容结构：

```json
{
  "source": "reddit",
  "source_id": "abc123",
  "content_type": "post",
  "title": "...",
  "content": "...",
  "author": "...",
  "published_at": "...",
  "score": 120,
  "comment_count": 38,
  "url": "...",
  "language": "en"
}
```

---

# 9. 内容去重

需要处理：

## 9.1 URL 去重

```text
canonical_url
```

## 9.2 Source ID 去重

```text
source + source_id
```

## 9.3 文本 Hash

```text
sha256(normalized_content)
```

## 9.4 语义去重

两个内容即使文字不同，也可能表达相同需求。

例如：

> “Excel 库存管理太麻烦了。”

和：

> “每天手工维护库存表真的浪费时间。”

应该能够识别为相似问题。

采用：

```text
Embedding
↓
Cosine Similarity
↓
Similarity > threshold
```

---

# 10. 需求识别模型

系统首先判断：

> 这条内容是不是一个需求信号？

分类：

```text
1. Pain
2. Feature Request
3. Complaint
4. Workaround
5. Buying Intent
6. Alternative Search
7. Price Complaint
8. Churn Signal
9. Unmet Need
10. General Discussion
11. Noise
```

示例：

```text
“有没有一个工具可以自动把这些 Excel 合并起来？”
→ Feature Request / Unmet Need
```

```text
“我每天花两个小时手工整理 Excel。”
→ Pain / Workaround
```

```text
“XX 太贵了，有没有便宜一点的替代品？”
→ Price Complaint / Alternative Search
```

---

# 11. LLM 需求提取

对于识别出的高价值内容，调用 LLM。

统一输出：

```json
{
  "is_demand": true,
  "demand_type": [
    "pain",
    "workaround"
  ],
  "user_segment": "small e-commerce business",
  "job_to_be_done": "reconcile inventory data",
  "problem": "inventory data needs to be manually reconciled",
  "pain_points": [
    "time consuming",
    "error prone"
  ],
  "current_solution": [
    "Excel"
  ],
  "desired_outcome": "automatically synchronize inventory data",
  "frequency": "daily",
  "severity": 8,
  "willingness_to_pay": null,
  "evidence_strength": 7
}
```

---

# 12. 证据体系

每一个需求都必须保留：

```text
Demand
 ↓
Evidence
 ↓
Source
 ↓
Original Content
```

例如：

```text
需求：
“中小电商需要自动同步库存”

Evidence #1
Reddit
用户：xxx
发布时间：2026-08-17
原文 URL：xxx

Evidence #2
GitHub Issue
用户：xxx
发布时间：2026-08-18
URL：xxx

Evidence #3
App Review
用户：xxx
发布时间：2026-08-19
URL：xxx
```

这样 AI 的结论不会变成“黑盒”。

---

# 13. 用户群体识别

建立：

```text
User Segment
```

例如：

```text
创业者
独立开发者
程序员
电商卖家
财务人员
销售
营销人员
HR
设计师
教师
学生
律师
房地产从业者
制造业
物流
餐饮
```

同时允许动态创建新的细分群体。

---

# 14. Job To Be Done

每个需求尽量提取：

```text
用户是谁？
↓
在什么场景？
↓
想完成什么任务？
↓
遇到什么障碍？
↓
现在怎么做？
↓
理想结果是什么？
```

标准模板：

```text
When [场景]

I want to [任务]

So that [期望结果]

But [痛点]
```

---

# 15. 需求聚类

单条帖子价值有限。

真正重要的是：

> **多个用户是否反复表达同一个问题？**

流程：

```text
Raw Content
 ↓
Embedding
 ↓
Vector Database
 ↓
Semantic Similarity
 ↓
Cluster
 ↓
Cluster Summary
```

MVP 推荐：

```text
PostgreSQL + pgvector
```

减少基础设施复杂度。

---

# 16. Demand Cluster

示例：

```text
Cluster #1024

主题：
电商库存自动同步

内容数量：
427

独立用户：
213

来源：
Reddit 102
GitHub 76
V2EX 21
App Store 28
其他 13

过去 30 天增长：
+67%

平均痛苦评分：
8.1

付费信号：
32

替代方案：
Excel
Shopify Plugin A
Manual Service
```

---

# 17. 需求评分模型

第一版评分：

```text
Pain                20%
Frequency           15%
Market Reach        15%
Willingness to Pay  15%
Evidence Strength   10%
Growth              10%
Competition Gap     10%
Technical Feasibility 5%
```

最终：

```text
Score =
Σ(metric × weight)
```

统一为：

```text
0～100
```

---

# 18. 指标定义

| 指标 | 说明 |
|---|---|
| Pain | 痛苦程度 |
| Frequency | 发生频率 |
| Reach | 目标用户覆盖 |
| Money | 付费可能/已有付费行为 |
| Evidence | 证据强度 |
| Growth | 需求增长速度 |
| Competition Gap | 现有解决方案空缺 |
| Technical Feasibility | 技术可行性 |

评分规则：

```text
0 = 极低
10 = 极高
```

---

# 19. Opportunity Engine

需求评分之后，不直接输出：

> “这个项目一定值得做。”

而输出：

```text
Opportunity
```

示例：

```text
Opportunity：
中小电商库存自动同步

需求强度：
86/100

证据：
427 条相关内容

独立用户：
213

增长：
+67%

当前解决方案：
Excel / 手工 / 第三方插件

主要痛点：
1. 数据重复录入
2. 数据延迟
3. 容易出错
4. 多平台同步困难

潜在机会：
开发一个面向中小电商的轻量级库存同步 SaaS
```

---

# 20. 趋势检测

系统不仅发现：

> “现在有什么需求”

还要发现：

> **“什么需求正在快速增长？”**

统计：

```text
7 days
30 days
90 days
```

增长率：

```text
Growth Rate =
(Current Period Volume - Previous Period Volume)
/
Previous Period Volume
```

同时结合：

- 独立用户数
- 来源数量
- 互动量
- 新增关键词
- 需求强度

---

# 21. Opportunity Radar

前端设计：

```text
┌────────────────────────────────────┐
│        Market Opportunity Radar     │
│                                    │
│  高增长                              │
│      ● AI Agent Monitoring         │
│                 ● AI Cost Control  │
│                                    │
│             ● Inventory Sync       │
│                                    │
│  ────────────────────────────────   │
│                                    │
│        高痛苦 ←────────→ 低痛苦      │
│                                    │
└────────────────────────────────────┘
```

点击后进入机会详情。

---

# 22. Dashboard

MVP Dashboard：

## Overview

```text
今日新增内容
今日需求信号
新增 Demand Cluster
高价值需求
增长最快需求
```

## Demand Feed

```text
实时需求流
```

## Demand Explorer

过滤：

```text
行业
用户群
关键词
来源
时间
痛苦程度
付费意愿
增长率
```

## Opportunity Ranking

```text
Top 10 产品机会
```

## Trend

```text
需求趋势
```

## Evidence

查看全部原始证据。

---

# 23. 数据库设计

MVP 使用 PostgreSQL。

核心表：

```text
sources
crawl_jobs
raw_documents
documents
authors
topics
demand_signals
demand_clusters
evidences
user_segments
opportunities
trend_metrics
llm_runs
```

## 23.1 sources

```sql
id
name
type
base_url
status
crawl_interval
created_at
updated_at
```

## 23.2 documents

```sql
id
source_id
source_item_id
url
canonical_url
title
content
author_id
published_at
engagement_score
language
content_hash
created_at
updated_at
```

## 23.3 demand_signals

```sql
id
document_id
demand_type
problem
pain_points
job_to_be_done
desired_outcome
current_solution
frequency
severity
willingness_to_pay
evidence_strength
confidence
created_at
```

## 23.4 demand_clusters

```sql
id
name
description
user_segment
document_count
unique_user_count
pain_score
frequency_score
money_score
growth_score
competition_gap
demand_score
created_at
updated_at
```

## 23.5 opportunities

```sql
id
cluster_id
title
problem_statement
target_customer
proposed_solution
market_score
validation_status
priority
created_at
updated_at
```

---

# 24. LLM 层设计

不要让 LLM 直接读取整个数据库。

采用 Pipeline：

```text
Document
 ↓
Classification
 ↓
Extraction
 ↓
Normalization
 ↓
Embedding
 ↓
Clustering
 ↓
Cluster-level Analysis
 ↓
Opportunity Generation
```

优势：

- 降低成本
- 提高稳定性
- 便于调试
- 保留中间结果

---

# 25. LLM Prompt 原则

要求模型：

1. 不得把普通讨论强行定义为需求。
2. 必须引用原始文本证据。
3. 无证据时输出 null。
4. 区分“用户明确表达”和“模型推测”。
5. 对付费意愿保持谨慎。
6. 不得凭空生成市场规模。
7. 所有评分都必须给出理由。

例如：

```json
{
  "willingness_to_pay": null,
  "willingness_to_pay_confidence": 0.12
}
```

而不是无依据地输出：

```json
{
  "willingness_to_pay": "high"
}
```

---

# 26. 数据质量控制

建立：

```text
Data Quality Score
```

考虑：

- 内容完整度
- 来源可信度
- 是否重复
- 是否广告
- 是否机器人
- 是否上下文缺失
- 发布时间
- 用户互动
- AI 置信度

低质量数据不进入核心需求池。

---

# 27. Spam / Noise Detection

需要过滤：

```text
广告
SEO 内容
机器人
推广帖
重复内容
无意义评论
抽奖
纯新闻转载
```

但是不要过度过滤。

原因：

> 有些“抱怨”本身就是最有价值的需求信号。

---

# 28. 需求生命周期

```text
DISCOVERED
    ↓
EVIDENCE_GATHERING
    ↓
HUMAN_REVIEW
    ↓
INTERVIEW
    ↓
VALIDATED
    ↓
MVP
    ↓
EARLY_USERS
    ↓
PAID
    ↓
SCALED
```

也允许：

```text
REJECTED
DORMANT
```

---

# 29. Human-in-the-Loop

系统不能完全自动决定项目。

建议：

```text
AI
 ↓
生成候选需求
 ↓
人工审核
 ↓
确认/驳回
 ↓
进入 Opportunity
```

人工可以：

- 修改用户群
- 修改问题
- 合并需求
- 拆分需求
- 调整评分
- 标记重要证据
- 标记误判

人工反馈可以反过来优化分类器。

---

# 30. MVP 开发路线

## Phase 0：基础设施

目标：

> 能稳定保存和处理数据。

实现：

- PostgreSQL
- Redis
- FastAPI
- Crawlee
- 基础日志
- Docker

## Phase 1：第一个数据源

先实现：

```text
Reddit
```

能力：

```text
发现
↓
抓取
↓
解析
↓
存储
```

## Phase 2：需求识别

加入：

```text
LLM Classification
```

输出：

```text
是否为需求
需求类型
痛点
用户
场景
```

## Phase 3：Embedding

加入：

```text
pgvector
```

实现：

```text
相似需求搜索
```

## Phase 4：Cluster

实现：

```text
10000 posts
↓
500 demand signals
↓
50 demand clusters
```

## Phase 5：Scoring

实现：

```text
Demand Score
```

## Phase 6：Dashboard

实现：

```text
Demand Feed
Demand Explorer
Opportunity Ranking
Trend
Evidence
```

## Phase 7：新增数据源

依次扩展：

```text
GitHub
V2EX
Hacker News
Product Hunt
App Store
Google Play
```

---

# 31. 推荐项目目录

```text
market-intelligence-engine/
│
├── apps/
│   ├── api/
│   ├── crawler/
│   └── web/
│
├── src/
│   ├── adapters/
│   │   ├── reddit/
│   │   ├── github/
│   │   ├── v2ex/
│   │   └── hackernews/
│   │
│   ├── crawling/
│   │   ├── scheduler.py
│   │   ├── queue.py
│   │   └── workers.py
│   │
│   ├── extraction/
│   │   ├── cleaner.py
│   │   ├── parser.py
│   │   └── normalizer.py
│   │
│   ├── intelligence/
│   │   ├── classifier.py
│   │   ├── extractor.py
│   │   ├── embedding.py
│   │   ├── clustering.py
│   │   └── scoring.py
│   │
│   ├── models/
│   ├── repositories/
│   ├── services/
│   └── config/
│
├── migrations/
├── tests/
├── prompts/
├── scripts/
├── docker/
│
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

# 32. API 设计

MVP API：

```text
GET /sources
POST /sources

GET /documents
GET /documents/{id}

GET /demands
GET /demands/{id}

GET /clusters
GET /clusters/{id}

GET /opportunities
GET /opportunities/{id}

GET /trends

POST /crawl/jobs

GET /crawl/jobs/{id}
```

---

# 33. 第一版 Dashboard

```text
┌──────────────────────────────────────────────┐
│ Market Intelligence Engine                   │
├──────────────────────────────────────────────┤
│                                              │
│  Documents      Demand Signals    Clusters  │
│    18,421            2,183            127    │
│                                              │
├──────────────────────────────────────────────┤
│                                              │
│  🔥 Rising Opportunities                     │
│                                              │
│  1. AI Agent Monitoring          91          │
│  2. AI Cost Control              87          │
│  3. Inventory Automation         84          │
│  4. Developer Workflow           82          │
│                                              │
├──────────────────────────────────────────────┤
│                                              │
│  📈 Trending Topics                          │
│                                              │
│  AI Agent          +126%                     │
│  MCP               +84%                      │
│  AI Cost           +72%                      │
│                                              │
└──────────────────────────────────────────────┘
```

---

# 34. 完整数据流实例

假设 Reddit 出现：

```text
Title:
I spend 2 hours every day cleaning Shopify inventory data

Content:
I have three stores...
Every morning I export CSV...
Then manually merge them...
I tried several tools...
They are either too expensive or too complicated...
```

处理：

```text
Crawler
 ↓
Document
 ↓
Classifier
 ↓
Demand Signal
```

得到：

```text
User:
Small e-commerce operator

Job:
Synchronize inventory data

Pain:
Manual CSV processing

Frequency:
Daily

Severity:
9

Current Solution:
Excel + CSV

Competition:
Existing tools but perceived as expensive/complex
```

然后：

```text
Embedding
 ↓
Cluster #182
```

发现：

```text
已有 312 个相关帖子
198 个独立用户
过去 30 天增长 58%
```

最后：

```text
Opportunity Score = 88
```

生成：

```text
Opportunity:

Lightweight multi-store inventory synchronization
for small e-commerce sellers.

Evidence:
312 signals

Main pain:
Manual CSV reconciliation

Current alternatives:
Excel / expensive SaaS / plugins

Potential differentiation:
Simple + low cost + multi-store
```

此时进入：

```text
用户访谈
↓
Landing Page
↓
预售
↓
MVP
```

而不是直接写代码。

---

# 35. 核心价值

MIE 最终应该让用户从：

```text
“我想做一个项目，但不知道做什么。”
```

变成：

```text
“这里有 127 个真实市场需求。”
```

再变成：

```text
“其中 14 个需求正在快速增长。”
```

再变成：

```text
“其中 5 个需求有明确付费信号。”
```

最后：

```text
“这 2 个需求值得我进行用户访谈。”
```

---

# 36. 最终闭环

```text
Market
   ↓
Signals
   ↓
Evidence
   ↓
Demand
   ↓
Cluster
   ↓
Trend
   ↓
Opportunity
   ↓
Validation
   ↓
MVP
   ↓
Real User Data
   ↓
Market
```

**这就是整个系统真正的护城河。**

---

# 37. MVP 成功标准

第一版不要用“爬了多少网页”衡量成功。

## 数据层

- ≥ 3 个数据源
- ≥ 10,000 条有效内容
- ≥ 95% 可追溯
- 重复率可控

## AI 层

- 需求识别 Precision ≥ 80%
- 需求抽取人工可接受率 ≥ 80%
- 需求聚类可解释

## 产品层

- 能发现 ≥ 50 个需求 Cluster
- 能生成 Top 20 Opportunity
- 每个 Opportunity 都有证据
- 用户能够从 Opportunity Drill-down 到原文

## 商业验证层

最终最重要的指标：

> **系统发现的需求，是否真的能通过人工访谈和付费实验得到验证。**

---

# 38. 后续高级能力

## 38.1 Market Map

自动生成：

```text
行业
 ↓
用户群
 ↓
痛点
 ↓
竞品
 ↓
机会
```

## 38.2 Competitor Intelligence

监控：

- 新产品
- 新功能
- 价格变化
- 用户评价
- 用户流失
- 竞品投诉

## 38.3 Demand Alert

例如：

```text
🚨 New Opportunity

“AI invoice reconciliation”

Demand growth:
+183% / 30 days

Evidence:
421

Paid signals:
37

Competition gap:
High
```

## 38.4 Weekly Market Report

每周自动生成：

```text
Top emerging problems
Top rising keywords
Top user complaints
Top alternatives searched
Top opportunities
```

## 38.5 AI Product Analyst

用户可以询问：

```text
“最近 30 天开发者最痛苦的问题是什么？”

“哪些需求增长最快？”

“有哪些用户正在寻找 Excel 的替代方案？”

“有哪些需求已经存在付费市场，但竞品评价很差？”

“如果我是独立开发者，哪些机会最值得做？”
```

---

# 39. 战略建议

不要把 MIE 的核心竞争力放在：

> “我能爬多少网站。”

因为爬虫本身容易被替代。

真正应该积累的是：

```text
数据
+
需求分类体系
+
需求历史
+
用户行为
+
需求 Cluster
+
趋势
+
竞品
+
验证结果
```

尤其是：

> **Demand History**

例如：

```text
2026-01
需求 A：20 条信号

2026-03
需求 A：120 条

2026-06
需求 A：430 条

2026-08
需求 A：1200 条
```

这会逐渐形成：

> **市场需求的时间序列数据库。**

这才是长期价值。

---

# 40. 产品愿景

MIE 最终可以从：

> “市场需求爬虫”

升级成：

# AI Market Intelligence Platform

核心能力：

```text
                 Market Intelligence
                         │
       ┌─────────────────┼─────────────────┐
       ↓                 ↓                 ↓
   Demand Discovery   Trend Detection   Competitor
       │                 │                 │
       ↓                 ↓                 ↓
   Pain Points       Emerging Market     Gap Analysis
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ↓
                  Opportunity Engine
                         ↓
                  Validation Engine
                         ↓
                  Product Discovery
```

最终目标不是：

> **“帮开发者爬数据。”**

而是：

> **“帮助开发者找到值得做的产品。”**

---

# 41. 推荐实际开发顺序

```text
Week 1
├── 项目初始化
├── PostgreSQL
├── Redis
├── Crawlee
└── Reddit Adapter

Week 2
├── Crawl Pipeline
├── Raw Data
├── Normalization
├── Deduplication
└── GitHub Adapter

Week 3
├── LLM Classification
├── Demand Extraction
├── Evidence
└── Human Review

Week 4
├── Embedding
├── pgvector
├── Similarity Search
└── Demand Cluster

Week 5
├── Demand Scoring
├── Trend Detection
└── Opportunity Engine

Week 6
├── FastAPI
├── Dashboard
├── Demand Explorer
└── Opportunity Ranking

Week 7+
├── V2EX
├── Hacker News
├── Product Hunt
├── App Store
└── Advanced Intelligence
```

---

# 42. 第一版必须遵守的原则

不要一开始做：

```text
❌ 全网爬虫
❌ 分布式集群
❌ 复杂微服务
❌ 自建大模型
❌ 复杂推荐算法
❌ 自动创业决策
❌ 100 个数据源
```

第一版只做：

```text
3 个数据源
+
10,000 条内容
+
需求识别
+
需求聚类
+
需求评分
+
证据追溯
+
一个可用的 Dashboard
```

如果这套链路能够发现出**真正值得访谈的需求**，再扩大规模。

---

# 43. 一句话定义

> **Market Intelligence Engine = 一个持续监听互联网用户行为与表达、自动提取市场痛点、聚合需求、识别趋势并生成产品机会的 Evidence-driven Product Discovery System。**

它应该成为整个“面向市场需求开发”体系的第一层：

```text
Market Intelligence Engine
            ↓
     Demand Discovery
            ↓
     Customer Discovery
            ↓
       Validation
            ↓
          MVP
            ↓
        Product
            ↓
        Business
```

**最终目标：先发现问题，再验证问题，最后才开发解决方案。**

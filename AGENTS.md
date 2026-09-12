# Market Intelligence Engine — Agent Guidelines

> 本文件由 Harness Engineering 框架生成，被 opencode/omo 自动注入（AGENTS.md）。
> 项目级完整契约见 `.omo/rules/harness.md`（被 omo 自动注入，source=0，最高优先级）。

## 项目概览

- **类型**：Evidence-driven 产品发现流水线（后端 FastAPI + 前端 Next.js）
- **语言**：Python 3.12（后端）+ TypeScript（前端）
- **工具链**：uv（后端）、npm（前端）、docker compose（基础设施）

## 开发约束

1. **任务规范**：每个任务写显式完成定义（API/LLM/模型/适配器/前端各有要求，见 `.omo/rules/harness.md` §2.1）
2. **上下文供给**：动手前读 `README.md`、`docs/requirements-trace.md`、`docs/PROJECT_LOG.md`、`frontend/DESIGN.md`
3. **执行环境**：后端 `uv sync` + `uvicorn`；前端 `npm run dev`；基础设施 `docker compose up -d`
4. **验证反馈**：完成前跑质量门禁（`quality-gate-check`）；前端过视觉门禁 R011
5. **状态管理**：需求变更更新 `docs/requirements-trace.md`；历史决策记入 `docs/PROJECT_LOG.md`

## 架构底线（必须守护）

1. **LLM 是软肋**——所有 LLM 调用走 `chat_json()`，必须兜底校验输出
2. **异步 + 独立 session**——后台任务用独立 `async_session_factory()`，不复用请求 session
3. **Human-in-the-Loop 是决策门禁**——AI 只起草，人签字；单源门禁、否决留理由
4. **证据链必须完整**——每个需求结论必须可追溯到原始证据（Evidence First）

## Harness 激活

- 本项目的 Harness 已激活（`.harness-activated` 存在）
- 完整契约见 `.omo/rules/harness.md`
- Harness Agent 调用使用 `task(category="deep", ...)` 格式

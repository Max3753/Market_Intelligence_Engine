# MIE 生产部署指南

> 将 Market Intelligence Engine 部署到云服务器（docker compose 管理）。
> **两阶段方案**：先无域名用 IP + HTTP 跑起来，绑定域名后再升级 HTTPS。

## 架构

```
阶段 A（无域名）：http://服务器IP:80
阶段 B（有域名）：https://你的域名:443
  └─ nginx 反代容器 (mie-prod-nginx)
       ├── /     → frontend (容器内 3000)
       └── /api  → backend  (容器内 8000)
  ├─ backend  (FastAPI, 容器内 8000, 不暴露 host)
  ├─ frontend (Next.js, 容器内 3000, 不暴露 host)
  ├─ postgres (容器内 5432, 不暴露 host)
  └─ redis    (容器内 6379, 不暴露 host)
```

- 独立 compose 项目 `mie-prod`，与服务器已有项目完全隔离（独立网络/容器名/卷）
- 仅 nginx 暴露 80/443，其余服务不暴露 host 端口，避免端口冲突

## 前置准备

1. **域名**（可选）：阶段 A 不需要；阶段 B 需要解析到服务器 IP（A 记录）
2. **LLM API Key**：DeepSeek（或任意 OpenAI 兼容 provider）
3. **SSH 访问**：服务器 Linux + Docker + docker compose 插件

---

# 阶段 A：无域名部署（HTTP + IP）

## A1. 服务器检查

```bash
# Docker 与 compose 版本
docker --version && docker compose version

# 80 端口是否空闲（若被已有项目占用需调整 nginx 端口映射）
ss -tlnp | grep -E ':(80|443)\s'

# 磁盘空间（torch CPU 版 + 模型缓存约需 3GB）
df -h /
```

> **阿里云注意**：控制台「安全组」必须放行 **80** 端口（轻量应用服务器在「防火墙」页面放行）。

## A2. 上传代码

```bash
# 方式一：git clone（推荐，代码已在 GitHub）
cd /opt
git clone https://github.com/Max3753/Macket_Intelligence_Engine.git mie
cd mie

# 方式二：本地 rsync（GitHub 慢时用）
rsync -av --exclude '.git' --exclude '.venv' --exclude 'node_modules' \
  --exclude '.next' --exclude '.env' --exclude '.env.*' --exclude '*.log' \
  ./ user@服务器IP:/opt/mie/
```

> 国内服务器 clone GitHub 可能慢，可加 `git config --global http.postBuffer 524288000` 或改用 rsync。

## A3. 配置环境变量

```bash
cd /opt/mie
cp deploy/.env.prod.example .env.prod
nano .env.prod
```

必填项（无域名阶段）：

```ini
POSTGRES_PASSWORD=改成你自己的强密码
LLM_API_KEY=sk-你的真实Key
NEXT_PUBLIC_API_URL=http://服务器IP/api     # ← 用 IP，不是域名
```

> **国内服务器建议直接启用 HF 镜像**（阿里云直连 huggingface.co 基本被墙）：
> 取消 `.env.prod` 中 `# HF_ENDPOINT=https://hf-mirror.com` 的注释。

## A4. 构建并启动全部服务

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

> **耗时提示**：首次构建 backend 镜像需下载 CPU 版 torch（约 200MB）+ 全部依赖，约 5-10 分钟，属正常。

首次启动后端会自动：
- 执行 `alembic upgrade head`（7 个迁移建表）
- 下载 embedding 模型 all-MiniLM-L6-v2（约 90MB，缓存到 hf_cache 卷，仅一次）
- 播种默认数据源（HN + V2EX，若设了 `GITHUB_REPO` 则含 GitHub）并**立即爬取一次**（免费 API，零 LLM 消耗）

> **Human-in-the-Loop（默认半自动）**：周期调度与自动分析默认关闭（`CRAWL_SCHEDULER_ENABLED=false` / `AUTO_PIPELINE=false`）。部署后原始文档自动入库，但**分析/聚类/评分全部在 Console 手动触发**——LLM 额度完全由你控制。需要按时自动爬取时，在 `.env.prod` 设 `CRAWL_SCHEDULER_ENABLED=true` 后重建。

## A5. 验证

```bash
# 容器状态（5 个都应为 running）
docker compose --env-file .env.prod -f docker-compose.prod.yml ps

# 后端健康检查
curl http://服务器IP/api/health

# 前端页面
curl -I http://服务器IP/

# 后端日志（确认迁移成功、模型下载完成）
docker logs -f mie-prod-backend
```

浏览器打开 `http://服务器IP`，看到仪表盘即部署成功。

---

# 阶段 B：绑定域名后升级 HTTPS

## B1. 域名解析

到域名服务商控制台添加 **A 记录**：`mie`（或 `@`）→ 服务器公网 IP。等待生效：

```bash
ping mie.你的域名.com
```

> 阿里云安全组同时放行 **443** 端口。

## B2. 切换 nginx 配置为 HTTPS 版

```bash
cd /opt/mie
cp deploy/nginx.https.conf deploy/nginx.conf
sed -i 's/your-domain.com/mie.你的域名.com/g' deploy/nginx.conf
grep server_name deploy/nginx.conf   # 确认替换成功
```

## B3. 签发 HTTPS 证书（一次性）

```bash
# 先启动 nginx（HTTP 模式，certbot 验证用）
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d nginx

# 签发证书（卷名随 compose 项目名 mie-prod 前缀）
docker run --rm \
  -v mie-prod_certbot_conf:/etc/letsencrypt \
  -v mie-prod_certbot_www:/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d mie.你的域名.com --email 你的邮箱 --agree-tos --no-eff-email
```

预期输出末尾：`Successfully received certificate.`

## B4. 更新前端 API 地址并重建

```bash
# .env.prod 里把 NEXT_PUBLIC_API_URL 改为 https://mie.你的域名.com/api
nano .env.prod

# 重建前端（build-time 变量必须重建）+ 重启 nginx
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

## B5. 验证 HTTPS

```bash
curl https://mie.你的域名.com/api/health
curl -I https://mie.你的域名.com/
```

浏览器访问 `https://mie.你的域名.com`，地址栏出现锁图标即完成。

---

## 更新部署

```bash
cd /opt/mie
git pull   # 或 rsync 重新上传
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

> 前端 `NEXT_PUBLIC_API_URL` 是 build-time 变量，改域名/IP 需 `--build` 重建前端镜像。

## 常见问题

| 问题 | 处理 |
|---|---|
| 后端启动失败：模型下载超时 | 阿里云直连 huggingface.co 被墙 → `.env.prod` 启用 `HF_ENDPOINT=https://hf-mirror.com` 后重建 |
| 后端启动失败：torch 版本冲突 | 移除 `backend.Dockerfile` 中 CPU torch 优化（`--no-install-package torch`），回退默认安装 |
| 80/443 被已有项目占用 | 修改 `docker-compose.prod.yml` 中 nginx 的 ports 映射（如 `8080:80`），或接入已有反代 |
| 浏览器打不开 | 阿里云安全组/防火墙未放行 80（或 443）端口 |
| 知乎源 401 | z_c0 Cookie 过期（约 6 天），更新 `.env.prod` 的 `ZHIHU_COOKIES` 后重启 backend |
| github 源 ConnectError | 服务器需代理时在源 config 配 `proxy`，或忽略该源 |
| 证书过期 | 手动续期：`docker run --rm -v mie-prod_certbot_conf:/etc/letsencrypt -v mie-prod_certbot_www:/var/www/certbot certbot/certbot renew` 后 `docker compose --env-file .env.prod -f docker-compose.prod.yml restart nginx` |

## 数据说明

- 全新开始：服务器空库启动，数据从零爬取积累
- 数据持久化：`postgres_data` / `redis_data` / `hf_cache` 三个 named volume
- 备份：`docker run --rm -v mie-prod_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/pg-data.tar.gz -C /data .`
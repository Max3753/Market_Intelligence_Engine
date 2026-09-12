# MIE 生产部署指南

> 将 Market Intelligence Engine 部署到云服务器（docker compose 管理，域名 + HTTPS）。

## 架构

```
域名 (HTTPS 443)
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

1. **域名**：解析到服务器 IP（A 记录）
2. **LLM API Key**：DeepSeek（或任意 OpenAI 兼容 provider）
3. **SSH 访问**：服务器 Linux + Docker + docker compose 插件

## 部署步骤

### 1. 服务器检查

```bash
# Docker 与 compose 版本
docker --version && docker compose version

# 80/443 端口是否空闲（若被已有项目占用需调整 nginx 端口映射）
ss -tlnp | grep -E ':(80|443)\s'

# 磁盘空间（torch CPU 版 + 模型缓存约需 3GB）
df -h /
```

### 2. 上传代码

```bash
# 本地（项目根目录）——排除敏感文件与构建产物
rsync -av --exclude '.git' --exclude '.venv' --exclude 'node_modules' \
  --exclude '.next' --exclude '.env' --exclude '.env.*' --exclude '*.log' \
  ./ user@server:/opt/mie/
```

> 或使用 git：`git clone <repo> /opt/mie`（.gitignore 已排除 .env 系列与构建产物）

### 3. 配置环境变量

```bash
cd /opt/mie
cp deploy/.env.prod.example .env.prod
vim .env.prod   # 填写 LLM_API_KEY、NEXT_PUBLIC_API_URL=https://你的域名/api 等
```

### 4. 替换 nginx 域名

```bash
sed -i 's/your-domain.com/你的域名/g' deploy/nginx.conf
```

### 5. 首次部署（签发 HTTPS 证书）

```bash
# 先启动 nginx（HTTP 模式，certbot 验证用）
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d nginx

# 签发证书（一次性；卷名随 compose 项目名 mie-prod 前缀）
docker run --rm \
  -v mie-prod_certbot_conf:/etc/letsencrypt \
  -v mie-prod_certbot_www:/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d 你的域名 --email 你的邮箱 --agree-tos --no-eff-email
```

### 6. 构建并启动全部服务

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

首次启动后端会自动：
- 执行 `alembic upgrade head`（7 个迁移建表）
- 下载 embedding 模型 all-MiniLM-L6-v2（约 90MB，缓存到 hf_cache 卷，仅一次）

### 7. 验证

```bash
# 容器状态
docker compose --env-file .env.prod -f docker-compose.prod.yml ps

# 后端健康检查
curl https://你的域名/api/health

# 前端页面
curl -I https://你的域名/

# 后端日志（确认迁移成功、模型下载完成）
docker logs -f mie-prod-backend
```

## 更新部署

```bash
cd /opt/mie
rsync -av --exclude ... ./ user@server:/opt/mie/   # 或 git pull
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

> 前端 `NEXT_PUBLIC_API_URL` 是 build-time 变量，改域名需 `--build` 重建前端镜像。

## 常见问题

| 问题 | 处理 |
|---|---|
| 后端启动失败：模型下载超时 | 服务器无法直连 huggingface.co → `.env.prod` 加 `HF_ENDPOINT=https://hf-mirror.com` 后重建 |
| 后端启动失败：torch 版本冲突 | 移除 `backend.Dockerfile` 中 CPU torch 优化（`--no-install-package torch`），回退默认安装 |
| 80/443 被已有项目占用 | 修改 `docker-compose.prod.yml` 中 nginx 的 ports 映射（如 `8080:80`），或接入已有反代 |
| 知乎源 401 | z_c0 Cookie 过期（约 6 天），更新 `.env.prod` 的 `ZHIHU_COOKIES` 后重启 backend |
| github 源 ConnectError | 服务器需代理时在源 config 配 `proxy`，或忽略该源 |
| 证书过期 | 手动续期：`docker run --rm -v mie-prod_certbot_conf:/etc/letsencrypt -v mie-prod_certbot_www:/var/www/certbot certbot/certbot renew` 后 `docker compose --env-file .env.prod -f docker-compose.prod.yml restart nginx` |

## 数据说明

- 全新开始：服务器空库启动，数据从零爬取积累
- 数据持久化：`postgres_data` / `redis_data` / `hf_cache` 三个 named volume
- 备份：`docker run --rm -v mie-prod_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/pg-data.tar.gz -C /data .`
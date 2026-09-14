# Frontend Dockerfile — Next.js + TypeScript (production, standalone output)
FROM node:22-alpine AS base

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# Build-time API URL — Next.js public env vars are inlined at build time
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Copy dependency files first for layer caching
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies with clean install
# npmmirror registry for CN servers (fallback: default npm registry)
# --mount=type=cache 持久化 npm 缓存（BuildKit），依赖未变时秒过
RUN --mount=type=cache,target=/root/.npm \
    npm config set registry https://registry.npmmirror.com && npm ci

# Copy application code
COPY frontend/ ./

# Build the application (standalone output — see next.config.ts)
# --mount=type=cache 持久化 .next/cache，增量构建只编译改动模块
# NODE_OPTIONS 限制堆内存，防止小内存服务器 OOM/换页
ENV NODE_OPTIONS=--max-old-space-size=1536
RUN --mount=type=cache,target=/app/.next/cache npm run build

# --- Production runner stage ---
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

# Copy standalone server + static assets + public files
COPY --from=base /app/public ./public
COPY --from=base --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=base --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
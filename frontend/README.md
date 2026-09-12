# Market Intelligence Engine — 前端

Next.js 15 + Tailwind CSS 前端骨架。

## 启动

```bash
cd frontend
cp .env.local.example .env.local   # 按需修改 API 地址
npm install
npm run dev
```

访问 http://localhost:3000。

## 目录

```
src/
├── app/          # Next.js App Router 页面
├── components/   # 共享组件
├── lib/          # API 封装
└── types/        # TypeScript 类型
```

## 注意

- 当前为骨架阶段，页面使用静态占位数据
- 需要后端 FastAPI 在 http://localhost:8000 运行才能接真实 API

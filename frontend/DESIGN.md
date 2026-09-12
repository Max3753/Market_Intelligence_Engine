# Market Intelligence Engine — 前端设计系统

> 本文件是前端 UI 的**设计契约**（Design System Gate）。任何涉及 UI/组件/页面的改动，必须先读本文件，再动手。
> 目标：**Linear / Stripe / Supabase 级别的内部运营控制台**。Correct-but-flat 是失败，不是完成。

## 1. 设计语言

**现代深色运营控制台** —— 数据密集但克制、有质感但不花哨。

- 深炭蓝基底（非纯黑），带微妙的环境光晕
- 半透明表面 + 内边框 + 彩色阴影，替代纯色块
- 语义色低饱和，用背景光晕而非刺眼纯色
- 数字用 `tabular-nums` 对齐，数据可扫读

## 2. 色板

### 表面（Surface）
| Token | 值 | 用途 |
|---|---|---|
| `bg-base` | `#0b1120` | 页面基底（深炭蓝） |
| `bg-base-2` | `#0f172a` | 基底渐变终点 |
| `bg-card` | `rgba(30,41,59,0.6)` | 卡片表面（半透明） |
| `bg-card-solid` | `#1e293b` | 卡片内嵌块 |
| `bg-inset` | `#0f172a` | 输入框/内嵌区 |
| `border-subtle` | `rgba(255,255,255,0.06)` | 卡片内边框 |
| `border-strong` | `rgba(255,255,255,0.1)` | 强调边框 |

### 文本（Text）
| Token | 值 | 用途 |
|---|---|---|
| `text-primary` | `#f8fafc` | 主文本 |
| `text-secondary` | `#94a3b8` | 次级文本 |
| `text-muted` | `#64748b` | 弱化文本/标签 |
| `text-faint` | `#475569` | 最弱文本 |

### 语义色（Semantic，低饱和 + 光晕）
| Token | 值 | 用途 |
|---|---|---|
| `accent` | `#38bdf8`（sky-400） | 主操作/聚焦 |
| `success` | `#34d399`（emerald-400） | 成功 |
| `danger` | `#f87171`（red-400） | 危险/失败 |
| `warning` | `#fbbf24`（amber-400） | 警告/待确认 |

语义色使用方式：**文字用 300-400 级，背景用 900/40 级 + 光晕**，不直接用纯色块。

## 3. 字体

- **字体栈**：`ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif`
- **数字**：`font-variant-numeric: tabular-nums`（数据/统计/表格）
- **层次**：标题用 `font-semibold`（600），正文 `font-normal`（400），标签 `font-medium`（500）
- **行高**：标题 `leading-tight`，正文 `leading-relaxed`

## 4. 间距与圆角

- **间距基准**：4px 网格（`space-y-4`、`p-5`、`gap-4`）
- **圆角**：卡片 `rounded-xl`（12px），按钮 `rounded-lg`（8px），徽章 `rounded-md`（6px），内嵌块 `rounded-lg`
- **卡片内边距**：`p-5`（20px）

## 5. 阴影与深度

- **卡片**：`shadow-lg shadow-black/20` + 内边框 `border border-white/5`
- **hover 提升**：`hover:shadow-xl hover:shadow-black/30 hover:border-white/10`
- **彩色光晕**：语义元素用 `shadow-[0_0_20px_rgba(56,189,248,0.15)]` 类光晕

## 6. 交互状态（必须全部实现）

| 状态 | 规则 |
|---|---|
| `hover` | 背景微亮 / 边框提亮 / 轻微上移 `-translate-y-0.5` |
| `active` | `scale-[0.98]` 按压反馈 |
| `focus` | `focus-visible:ring-2 ring-sky-400/50 ring-offset-2 ring-offset-slate-900` |
| `disabled` | `disabled:opacity-50 disabled:cursor-not-allowed` |
| 过渡 | `transition-all duration-200` |

## 7. 组件规范

### 卡片（Card）
```
rounded-xl border border-white/5 bg-slate-800/60 p-5 shadow-lg shadow-black/20
```

### 主按钮（Primary）
```
rounded-lg bg-sky-500 px-4 py-2 text-sm font-medium text-white
hover:bg-sky-400 active:scale-[0.98] transition-all duration-200
disabled:opacity-50 disabled:cursor-not-allowed
```

### 危险按钮（Danger）
```
rounded-lg bg-red-500/90 px-4 py-2 text-sm font-medium text-white
hover:bg-red-400 active:scale-[0.98] transition-all duration-200
```

### 次级按钮（Secondary）
```
rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200
hover:bg-white/10 active:scale-[0.98] transition-all duration-200
```

### 输入框（Input）
```
w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-slate-100
placeholder:text-slate-500
focus:border-sky-400/50 focus:ring-2 focus:ring-sky-400/20 focus:outline-none
```

### 状态徽章（Badge）
```
rounded-md px-2 py-0.5 text-xs font-medium
成功: bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/20
运行: bg-sky-400/10 text-sky-300 ring-1 ring-sky-400/20 animate-pulse
失败: bg-red-400/10 text-red-300 ring-1 ring-red-400/20
待定: bg-slate-400/10 text-slate-300 ring-1 ring-slate-400/20
```

### 区块标题（Section Title）
```
text-sm font-semibold text-slate-100  +  左侧 3px accent 竖条
```

## 8. 布局

- 主内容区：`p-8`，`max-w-7xl mx-auto`
- 卡片网格：`grid grid-cols-1 gap-6 lg:grid-cols-2`
- 侧边栏：`w-56`，激活项带左侧 accent 指示条

## 9. 禁止事项

- ❌ 不用纯 `#000` 背景
- ❌ 不用刺眼纯色块（用低饱和 + 光晕）
- ❌ 不用默认系统字体（用本文件字体栈）
- ❌ 不省略 hover/active/focus/disabled 状态
- ❌ 不用 `window.alert()` 做错误提示
- ❌ 数字不用比例字体（必须 `tabular-nums`）

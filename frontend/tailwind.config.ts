import type { Config } from "tailwindcss";

/**
 * 设计 token —— 与 frontend/DESIGN.md §2 色板对齐。
 * 所有颜色/间距/圆角/阴影都从这里取，禁止散落硬编码。
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // 表面（Surface）—— DESIGN.md §2
        base: {
          DEFAULT: "#0b1120",
          2: "#0f172a",
        },
        card: {
          DEFAULT: "rgba(30,41,59,0.6)", // bg-card 半透明
          solid: "#1e293b", // bg-card-solid
          inset: "#0f172a", // bg-inset
        },
        // 文本（Text）
        ink: {
          primary: "#f8fafc",
          secondary: "#94a3b8",
          muted: "#64748b",
          faint: "#475569",
        },
        // 语义色（Semantic）—— 低饱和 + 光晕
        accent: {
          DEFAULT: "#38bdf8", // sky-400
        },
        success: {
          DEFAULT: "#34d399", // emerald-400
        },
        danger: {
          DEFAULT: "#f87171", // red-400
        },
        warning: {
          DEFAULT: "#fbbf24", // amber-400
        },
        sidebar: {
          DEFAULT: "#0f172a",
          hover: "#1e293b",
          active: "#334155",
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "PingFang SC",
          "Microsoft YaHei",
          "sans-serif",
        ],
      },
      borderRadius: {
        // DESIGN.md §4
        card: "0.75rem", // rounded-xl 12px
        btn: "0.5rem", // rounded-lg 8px
        badge: "0.375rem", // rounded-md 6px
      },
      boxShadow: {
        // DESIGN.md §5
        card: "0 10px 15px -3px rgba(0,0,0,0.2)",
        "card-hover": "0 20px 25px -5px rgba(0,0,0,0.3)",
        glow: "0 0 20px rgba(56,189,248,0.15)",
        "glow-emerald": "0 0 20px rgba(52,211,153,0.15)",
        "glow-amber": "0 0 20px rgba(251,191,36,0.15)",
        "glow-violet": "0 0 20px rgba(167,139,250,0.15)",
      },
    },
  },
  plugins: [],
};

export default config;

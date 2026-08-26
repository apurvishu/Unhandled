import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#080e1a",
        surface: {
          DEFAULT: "#0f172a",
          secondary: "#1e293b",
          tertiary: "#334155",
          highlight: "#1e3a8a",
        },
        maritime: {
          primary: "#0284c7",
          teal: "#06b6d4",
          cyan: "#38bdf8",
          deep: "#0c4a6e",
          accent: "#3b82f6",
        },
        status: {
          success: "#10b981",
          warning: "#f59e0b",
          danger: "#ef4444",
          info: "#06b6d4",
          purple: "#8b5cf6",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "Monaco", "Courier New", "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px -5px rgba(14, 165, 233, 0.3)",
        "glow-green": "0 0 20px -5px rgba(16, 185, 129, 0.3)",
        "glow-amber": "0 0 20px -5px rgba(245, 158, 11, 0.3)",
        "glow-red": "0 0 20px -5px rgba(239, 68, 68, 0.3)",
      },
    },
  },
  plugins: [],
};
export default config;

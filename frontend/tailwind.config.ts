import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "rgb(var(--ink) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        "surface-2": "rgb(var(--surface-2) / <alpha-value>)",
        line: "rgb(var(--line) / <alpha-value>)",
        "line-2": "rgb(var(--line-2) / <alpha-value>)",
        text: "rgb(var(--text) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        faint: "rgb(var(--faint) / <alpha-value>)",
        "faint-2": "rgb(var(--faint-2) / <alpha-value>)",
        gold: "rgb(var(--gold) / <alpha-value>)",
        buy: "rgb(var(--buy) / <alpha-value>)",
        sell: "rgb(var(--sell) / <alpha-value>)",
        hold: "rgb(var(--hold) / <alpha-value>)",
        info: "rgb(var(--info) / <alpha-value>)",
      },
      fontFamily: {
        // Editorial grotesk for prose/UI; mono with tabular-nums for figures.
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      maxWidth: { content: "1280px", detail: "1180px" },
      transitionTimingFunction: { gentle: "cubic-bezier(0.22, 1, 0.36, 1)" },
    },
  },
  plugins: [],
};

export default config;

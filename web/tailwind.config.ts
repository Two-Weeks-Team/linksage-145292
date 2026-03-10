import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: "var(--primary)",
        accent: "var(--accent)",
        card: "var(--card)",
        muted: "var(--muted)",
        border: "var(--border)",
        success: "var(--success)",
        warning: "var(--warning)"
      },
      borderRadius: {
        DEFAULT: "var(--radius)"
      },
      boxShadow: {
        DEFAULT: "var(--shadow)"
      }
    }
  },
  plugins: []
} satisfies Config;

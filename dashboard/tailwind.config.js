/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Geist Sans"', "system-ui", "sans-serif"],
        mono: ['"Geist Mono"', "ui-monospace", "monospace"],
      },
      colors: {
        // Off-black surfaces (never pure #000), one cool neutral ramp.
        ink: {
          950: "#0a0c10",
          900: "#0e1116",
          850: "#141821",
          800: "#1a1f2b",
          700: "#232937",
          600: "#323a4d",
        },
        line: "#232937",
        // Single UI accent (cool cyan-blue). Not AI-purple.
        accent: {
          DEFAULT: "#38bdf8",
          soft: "#0e2a3a",
          fg: "#0a0c10",
        },
        // Semantic risk scale — real data state, not decoration.
        risk: {
          low: "#34d399",
          med: "#fbbf24",
          high: "#f87171",
        },
      },
      borderRadius: {
        // One radius system.
        DEFAULT: "10px",
        lg: "14px",
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 8px 30px -12px rgba(0,0,0,0.6)",
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        axiom: { bg: "#0b0f17", panel: "#141a26", accent: "#4f8cff" },
        risk: { low: "#22c55e", med: "#eab308", high: "#ef4444" },
      },
    },
  },
  plugins: [],
};

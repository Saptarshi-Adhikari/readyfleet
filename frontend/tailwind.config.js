/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#090d16",
        surface: "#111726",
        panel: "#161e31",
        border: "#232e47",
        primary: "#38bdf8",
        mc: "#22c55e",
        pmc: "#eab308",
        nmc: "#ef4444",
      }
    },
  },
  plugins: [],
}

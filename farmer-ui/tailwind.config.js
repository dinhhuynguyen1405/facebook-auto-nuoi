/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#1a5fd5",
        "primary-light": "#e8f0fd",
        accent:  "#ff8c42",
        success: "#10b981",
        warning: "#f59e0b",
        danger:  "#ef4444",
        surface: "#ffffff",
        "surface-2": "#f8fafc",
        border:  "#e2e8f0",
        muted:   "#94a3b8",
        "text-main": "#0f172a",
        "text-sub":  "#64748b",
      },
      borderRadius: { xl: "1rem", "2xl": "1.25rem", "3xl": "1.5rem" },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};

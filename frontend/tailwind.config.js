/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#F8FAFC",
        surface: "#FFFFFF",
        border: "#E2E8F0",
        navy: {
          900: "#0F172A",
          800: "#1E293B",
          700: "#334155",
          600: "#475569",
          500: "#64748B",
          400: "#94A3B8",
          100: "#F1F5F9",
          50: "#F8FAFC",
        },
        teal: {
          DEFAULT: "#0D9488",
          600: "#0D9488",
          700: "#0F766E",
          500: "#14B8A6",
          50: "#F0FDFA",
          100: "#CCFBF1",
        },
        blue: {
          600: "#2563EB",
          500: "#3B82F6",
          50: "#EFF6FF",
        },
        verified: {
          bg: "#ECFDF5",
          text: "#065F46",
          border: "#A7F3D0",
        },
        pending: {
          bg: "#FFFBEB",
          text: "#92400E",
          border: "#FDE68A",
        },
        danger: {
          bg: "#FEF2F2",
          text: "#991B1B",
          border: "#FECACA",
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        subtle: "0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 1px 2px -1px rgba(15, 23, 42, 0.05)",
        card: "0 4px 6px -1px rgba(15, 23, 42, 0.04), 0 2px 4px -2px rgba(15, 23, 42, 0.04)",
        lifted: "0 10px 15px -3px rgba(15, 23, 42, 0.06), 0 4px 6px -4px rgba(15, 23, 42, 0.04)",
      }
    },
  },
  plugins: [],
}

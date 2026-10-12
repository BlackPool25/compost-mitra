/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "var(--surface)",
        cream: "var(--bg)",
        sand: "var(--sand)",
        ink: {
          DEFAULT: "var(--text)",
          muted: "var(--text-muted)",
        },
        clay: {
          200: "#F2C4B4",
          500: "#E2725B", // decorative fills and illustration only
          600: "var(--accent)", // #B5523B primary button & brand
          700: "var(--accent-pressed)", // #9A4A32
          900: "var(--hero)", // #4A2A1E deep hero
        },
        neem: {
          100: "var(--ok-bg)", // #E3EFD8
          700: "var(--ok)", // #3F6B3A
        },
        haldi: {
          100: "var(--caution-bg)", // #F8E7B8
          500: "var(--caution)", // #E0A92E
          text: "var(--caution-text)", // #6B4E0A
        },
        mitti: {
          600: "var(--wet)", // #7A5236
        },
        kumkum: {
          600: "var(--act)", // #B3362F
        },
      },
      borderRadius: {
        card: "12px",
        sheet: "20px",
        matka: "28px 28px 18px 18px",
      },
      boxShadow: {
        warm: "0 2px 8px rgba(74, 42, 30, 0.08)",
        elevated: "0 4px 16px rgba(74, 42, 30, 0.12)",
      },
      fontFamily: {
        display: ["Fraunces", "Tiro Devanagari Hindi", "serif"],
        sans: ["Noto Sans Devanagari", "Hind", "system-ui", "sans-serif"],
      },
      transitionDuration: {
        micro: "120ms",
        std: "240ms",
        emph: "400ms",
      },
    },
  },
  plugins: [],
}

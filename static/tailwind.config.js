/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./*.html",
    "./*.py",
    "./*.js",
    "./*.json",
    "./quiz/**/*.html",
    "./templates/**/*.{html,js,py}",
    "./static/**/*.{html,js}",
    "./medical-rag-app/**/*.html",
    "./medical-rag-app/src/**/*.{html,js,jsx,ts,tsx}",
    "./medical-rag-app/vite.config.js",
    "./medical-rag-app-deploy/**/*.html",
    "./medical-rag-app-deploy/assets/**/*.js",
  ],
  safelist: [
    {
      pattern: /delay-(100|200|300|400|500)/,
    },
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: "#111111",
          light: "#F2F2F2",
          green: "#00C0B5",
          coral: "#FF6B6B",
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "sans-serif"],
        playfair: ['"Playfair Display"', "serif"],
      },
      transitionTimingFunction: {
        premium: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
      transitionDelay: {
        400: "400ms",
      },
    },
  },
  plugins: [],
}

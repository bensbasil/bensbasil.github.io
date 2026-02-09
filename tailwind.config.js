module.exports = {
  theme: {
    extend: {
      colors: {
        'ml-navy': '#0F172A',      // Deep slate for background
        'ml-slate': '#1E293B',     // Lighter slate for cards/sections
        'ml-accent': '#38BDF8',    // Bright sky blue for links/actions
        'ml-math': '#A5F3FC',      // Soft cyan for variables like Wx+b
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Fira Code', 'monospace'], // Critical for showing code/math
      },
      backgroundImage: {
        'grid-pattern': "url('https://www.transparenttextures.com/patterns/carbon-fibre.png')",
      }
    },
  },
}
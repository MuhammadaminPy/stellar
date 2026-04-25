/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        df: {
          bg: 'var(--bg)',
          surface: 'var(--surface)',
          card: 'var(--card)',
          border: 'var(--border)',
          accent: 'var(--accent)',
          gold: 'var(--gold)',
          green: 'var(--green)',
          red: 'var(--red)',
          text: 'var(--text)',
          muted: 'var(--muted)',
        },
      },
      fontFamily: {
        sans: ['Nunito', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

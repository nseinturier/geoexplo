/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Palantir-like dark palette
        surface: {
          DEFAULT: '#080c18',
          card: '#0d1525',
          hover: '#111d35',
          border: '#1e2d45',
        },
        brand: {
          DEFAULT: '#3b82f6',
          dim: '#1d4ed8',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem',
        sm: '0.25rem',
      },
    },
  },
  plugins: [],
}

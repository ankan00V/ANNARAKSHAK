/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        'instrument-serif': ['"Instrument Serif"', '"Noto Serif Devanagari"', 'serif'],
        sans: ['Inter', '"Noto Sans Devanagari"', 'system-ui', 'sans-serif'],
      },
      colors: {
        soil: {
          dark: '#2b1d12',
          DEFAULT: '#4a3423',
        },
        leaf: {
          deep: '#1f3d2b',
          DEFAULT: '#3d6b4a',
        },
        ochre: '#c8862d',
        cream: '#f7f3ec',
        ember: '#b0472a',
      },
      keyframes: {
        fadein: {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        scan: {
          '0%': { top: '-20%' },
          '50%': { top: '85%' },
          '100%': { top: '-20%' },
        },
      },
      animation: {
        fadein: 'fadein 0.25s ease-out',
      },
    },
  },
  plugins: [],
}

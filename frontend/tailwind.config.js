/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#ebf2f8',
          100: '#d6e4f1',
          200: '#adc8e3',
          300: '#85add6',
          400: '#5c91c8',
          500: '#004990',
          600: '#003f7d',
          700: '#00356a',
          800: '#002b57',
          900: '#002144',
        },
        dark: {
          100: '#1e293b',
          200: '#1a2234',
          300: '#151b2b',
          400: '#111827',
          500: '#0f172a',
          600: '#0d1424',
          700: '#0a101d',
          800: '#080d17',
          900: '#050912',
        }
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'gradient': 'gradient 8s linear infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        }
      }
    },
  },
  plugins: [],
}

import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eefbfa',
          100: '#d5f5f2',
          200: '#b0ebe6',
          300: '#7ddbd3',
          400: '#58B9AF',
          500: '#3fa69c',
          600: '#2f8580',
          700: '#296b68',
          800: '#255654',
          900: '#234846',
          950: '#0f2b2a',
        },
        accent: {
          50: '#f0faf9',
          100: '#C1DEDB',
          200: '#a3d0cb',
          300: '#7bbfb8',
          400: '#58B9AF',
          500: '#3fa69c',
          600: '#2f8580',
          700: '#296b68',
          800: '#255654',
          900: '#234846',
        },
        surface: {
          50: '#f8fafa',
          100: '#f0f3f3',
          200: '#e0e5e5',
          300: '#c5cccc',
          400: '#8a9494',
          500: '#6b7676',
          600: '#555e5e',
          700: '#454c4c',
          800: '#353A3A',
          900: '#2a2f2f',
          950: '#1a1e1e',
        },
        ctth: {
          white: '#FFFFFF',
          gunmetal: '#353A3A',
          frozen: '#C1DEDB',
          teal: '#58B9AF',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.06)',
        'card': '0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 16px rgba(0,0,0,0.08), 0 8px 32px rgba(0,0,0,0.06)',
        'glow-primary': '0 0 24px rgba(88, 185, 175, 0.2)',
        'glow-accent': '0 0 20px rgba(193, 222, 219, 0.3)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-in-left': 'slideInLeft 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}

export default config

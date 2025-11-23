/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Vibehuntr brand colors
        primary: '#FF6B6B',
        accent: '#FF8E8E',
        background: '#0F0F1E',
        secondary: '#1A1A2E',
        surface: '#16213E',
        text: {
          primary: '#FFFFFF',
          secondary: '#B8B8D1',
          muted: '#8B8B9E',
        },
      },
      fontFamily: {
        sans: ['Lexend', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glass: '0 8px 32px 0 rgba(255, 107, 107, 0.1)',
        glow: '0 0 20px rgba(255, 107, 107, 0.3)',
      },
      backdropBlur: {
        glass: '10px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
}

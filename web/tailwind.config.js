/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Freya Theme - Using CSS Variables for dynamic theming
        freya: {
          bg: {
            primary: 'var(--freya-bg-primary)',
            secondary: 'var(--freya-bg-secondary)',
            tertiary: 'var(--freya-bg-tertiary)',
            elevated: 'var(--freya-bg-elevated)',
          },
          border: {
            DEFAULT: 'var(--freya-border)',
            light: 'var(--freya-border-light)',
            accent: '#4299e1',
          },
          text: {
            primary: 'var(--freya-text-primary)',
            secondary: 'var(--freya-text-secondary)',
            muted: 'var(--freya-text-muted)',
            accent: '#58a6ff',
          },
          accent: {
            blue: '#58a6ff',
            green: '#3fb950',
            yellow: '#d29922',
            red: '#f85149',
            purple: '#a371f7',
            cyan: '#39d4ff',
          }
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Cascadia Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(88, 166, 255, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(88, 166, 255, 0.4)' },
        }
      }
    },
  },
  plugins: [],
}

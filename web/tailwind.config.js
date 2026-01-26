/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Freya Dark Theme
        freya: {
          bg: {
            primary: '#0a0e14',
            secondary: '#0f1419',
            tertiary: '#151b23',
            elevated: '#1a2230',
          },
          border: {
            DEFAULT: '#2d3748',
            light: '#3d4a5c',
            accent: '#4299e1',
          },
          text: {
            primary: '#e6edf3',
            secondary: '#8b949e',
            muted: '#6b7280',
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

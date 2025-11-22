/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
<<<<<<< HEAD
<<<<<<< HEAD
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
<<<<<<< HEAD
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
=======
>>>>>>> origin/claude/pdf-deck-renderer-01QnNpwQFSMU7WYfb9J8gfKi
=======
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
>>>>>>> origin/claude/notification-system-011TGLjzAos8ag9kBQK32dgF
=======
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
>>>>>>> origin/claude/team-management-features-01YbA13LtG8bARp7mPDMFyPw
  ],
  theme: {
    extend: {
      colors: {
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        // Sales OS Brand Colors
=======
>>>>>>> origin/claude/team-management-features-01YbA13LtG8bARp7mPDMFyPw
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
<<<<<<< HEAD
          950: '#082f49',
        },
        secondary: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          700: '#15803d',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          700: '#b45309',
        },
        error: {
          50: '#fef2f2',
          500: '#ef4444',
          700: '#b91c1c',
=======
        brand: {
          primary: '#1E40AF',
          secondary: '#3B82F6',
          accent: '#10B981',
>>>>>>> origin/claude/pdf-deck-renderer-01QnNpwQFSMU7WYfb9J8gfKi
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
<<<<<<< HEAD
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'medium': '0 4px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 25px -5px rgba(0, 0, 0, 0.04)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
=======
=======
        // Custom brand colors can be added here
>>>>>>> origin/claude/notification-system-011TGLjzAos8ag9kBQK32dgF
=======
        },
>>>>>>> origin/claude/team-management-features-01YbA13LtG8bARp7mPDMFyPw
      },
    },
  },
  plugins: [],
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> origin/claude/pdf-deck-renderer-01QnNpwQFSMU7WYfb9J8gfKi
}
=======
};
>>>>>>> origin/claude/notification-system-011TGLjzAos8ag9kBQK32dgF
=======
}
>>>>>>> origin/claude/team-management-features-01YbA13LtG8bARp7mPDMFyPw

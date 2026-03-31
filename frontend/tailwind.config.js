/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Cardiovascular theme colors
        cardio: {
          primary: '#dc2626', // Deep red
          secondary: '#b91c1c', // Darker red
          accent: '#f87171', // Light red
          danger: '#7f1d1d', // Very dark red
          light: '#fee2e2', // Pale red
          pulse: '#ef4444', // Bright red
        },
        heart: {
          crimson: '#991b1b',
          scarlet: '#dc2626',
          rose: '#f43f5e',
          pink: '#ec4899',
        },
        blood: {
          arterial: '#b91c1c',
          venous: '#6b21a8',
          plasma: '#fef3c7',
        },
      },
      animation: {
        'heartbeat': 'heartbeat 1.2s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'flow': 'flow 3s linear infinite',
      },
      keyframes: {
        heartbeat: {
          '0%, 100%': { transform: 'scale(1)' },
          '14%': { transform: 'scale(1.1)' },
          '28%': { transform: 'scale(1)' },
          '42%': { transform: 'scale(1.1)' },
          '70%': { transform: 'scale(1)' },
        },
        flow: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '100% 50%' },
        },
      },
      backgroundImage: {
        'cardio-gradient': 'linear-gradient(135deg, #dc2626 0%, #991b1b 50%, #7f1d1d 100%)',
        'heart-gradient': 'linear-gradient(135deg, #f43f5e 0%, #dc2626 50%, #b91c1c 100%)',
        'blood-flow': 'linear-gradient(90deg, #dc2626 0%, #ef4444 50%, #dc2626 100%)',
      },
    },
  },
  plugins: [],
}

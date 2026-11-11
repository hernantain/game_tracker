/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        racing: {
          blue:  '#00A8E8',
          light: '#33BBEF',
          dark:  '#0080B8',
        },
        surface: {
          0: '#0D1117',
          1: '#161B22',
          2: '#21262D',
          3: '#30363D',
        },
      },
    },
  },
  plugins: [],
};

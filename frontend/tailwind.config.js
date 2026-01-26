/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',
        secondary: '#10B981',
      },
      animation: {
        'bounce': 'bounce 1s infinite',
        'spin': 'spin 1s linear infinite',
      }
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        strava: {
          DEFAULT: '#FC4C02',
          dark: '#e04400',
        },
      },
      fontFamily: {
        system: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Text', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

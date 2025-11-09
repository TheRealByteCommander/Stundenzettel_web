/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#e90118",
          gray: "#5a5a5a",
          light: "#b3b3b5"
        }
      }
    },
  },
  plugins: [],
};


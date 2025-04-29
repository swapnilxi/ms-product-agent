/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: 'class',
    content: [
      "./src/**/*.{js,ts,jsx,tsx}",
      "./app/**/*.{js,ts,jsx,tsx}",
      "./components/**/*.{js,ts,jsx,tsx}",
      "./lib/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        animation: {
          'fade-in': 'fadeIn 0.3s ease-in-out',
        },
        colors: {
          background: 'var(--background)',
          foreground: 'var(--foreground)',
        },
        fontFamily: {
          sans: ['var(--font-sans)', 'sans-serif'],
          mono: ['var(--font-mono)', 'monospace'],
        },
      },
    },
    plugins: [],
  };
  
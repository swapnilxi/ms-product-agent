import { create } from 'zustand';

export const useThemeStore = create((set) => ({
  darkMode: false,

  initializeTheme: () => {
    if (typeof window !== 'undefined') {
      const storedMode = localStorage.getItem('darkMode');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

      const useDark = storedMode === null ? prefersDark : storedMode === 'true';

      if (useDark) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }

      set({ darkMode: useDark });
    }
  },

  toggleDarkMode: () => set((state) => {
    const newDarkMode = !state.darkMode;

    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    if (typeof window !== 'undefined') {
      localStorage.setItem('darkMode', newDarkMode.toString());
    }

    return { darkMode: newDarkMode };
  }),
}));

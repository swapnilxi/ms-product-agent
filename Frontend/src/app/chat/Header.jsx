"use client";

import { THEME } from '@/config';
import { useThemeStore } from '@/services/themeStore';
import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';

export default function Header() {
  const { darkMode, toggleDarkMode } = useThemeStore();

  return (
    <header
      className="w-full px-6 py-4 flex items-center justify-between shadow-sm bg-white dark:bg-gray-900"
    //   style={{ backgroundColor: THEME.primaryColor }}
    >
      <h1 className="text-xl font-bold text-white">AI Agents Platform</h1>

      <button
        onClick={toggleDarkMode}
        className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 hover:scale-110 transition-transform"
        aria-label="Toggle Dark Mode"
      >
        {darkMode ? (
          <SunIcon className="h-6 w-6 text-yellow-400" />
        ) : (
          <MoonIcon className="h-6 w-6 text-white-300" />
        )}
      </button>
    </header>
  );
}

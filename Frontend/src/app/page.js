"use client";

import { useState, useEffect } from 'react';
import { useThemeStore } from '@/services/themeStore';
import ChatPage from './chat/ChatPage'; // your main chat page

export default function Home() {
  const [mounted, setMounted] = useState(false);
  const initializeTheme = useThemeStore((state) => state.initializeTheme);

  useEffect(() => {
    initializeTheme();  // Initialize dark/light mode from localStorage
    setMounted(true);
  }, [initializeTheme]);

  if (!mounted) {
    return null; // Prevent hydration mismatch
  }

  return (
    <div className="flex flex-col overflow-y-auto">
      <ChatPage />
    </div>
  );
}

// app/Header.jsx

import { THEME } from '@/config';

export default function Header() {
  return (
    <header
      className="w-full px-6 py-4 flex items-center justify-between shadow-sm"
      style={{ backgroundColor: THEME.primaryColor }}
    >
      <h1 className="text-xl font-bold text-white">AI Agents Platform</h1>
      {/* You can add more things like profile menu later */}
    </header>
  );
}

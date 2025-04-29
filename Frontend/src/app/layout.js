import Header from './chat/Header';
import { Toaster } from 'react-hot-toast';
import './globals.css';

export const metadata = {
  title: 'AI Agents Platform',
  description: 'A platform for managing and interacting with AI agents.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen min-w-full bg-background text-foreground transition-colors">
        <Header />
        {children}
        <Toaster position="top-right" reverseOrder={false} />
      </body>
    </html>
  );
}

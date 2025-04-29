import Header from './chat/Header';
import ChatPage from './chat/ChatPage';

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1 overflow-y-auto">
        <ChatPage />
      </main>
    </div>
  );
}

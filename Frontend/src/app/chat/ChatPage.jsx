import CompanySelector from './CompanySelector';
import ActionButtons from './ActionButtons';
import ChatInterface from './ChatInterface';
import InputBox from './InputBox';

export default function ChatPage() {
  return (
    <div className="flex flex-col gap-4 p-6 max-w-5xl mx-auto">
      <CompanySelector />
      <ActionButtons />
      <ChatInterface />
      <InputBox />
    </div>
  );
}

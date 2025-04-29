"use client";

import CompanySelector from './CompanySelector';
import ActionButtons from './ActionButtons';
import ChatInterface from './ChatInterface';
import InputBox from './InputBox';

export default function ChatPage() {
  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-6xl mx-auto p-4">
      {/* Company Selector on top */}
      <div className="mb-4">
        <CompanySelector />
      </div>

      {/* Chat Window that fills available space */}
      <div className="flex-1 flex flex-col rounded-lg overflow-hidden bg-white dark:bg-gray-900">
        
        {/* Chat messages area (scrollable) */}
        <div className="flex-1 overflow-y-auto p-4">
          <ChatInterface />
        </div>

        {/* Bottom Actions */}
        <div className="p-4 flex flex-col gap-4 bg-gray-50 dark:bg-gray-800 border border-gray-200  rounded-lg dark:border-gray-700">
          <ActionButtons />
          <InputBox />
        </div>
      </div>
    </div>
  );
}

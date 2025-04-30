"use client";

import { useChatStore } from '@/services/chatApi';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';

export default function InputBox() {
  const { userInput, setUserInput, sendMessage, clearMessages } = useChatStore();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (userInput.trim()) {
      sendMessage(userInput);
      setUserInput('');
    }
  };

  return (
    <div className="flex items-center gap-2 w-full">
      <form onSubmit={handleSubmit} className="flex flex-1 items-center gap-2">
        <input
          type="text"
          value={userInput}
          onChange={(e) => {
            const input = e.target.value;
            setUserInput(input);
          }}
          placeholder="Type your message..."
          className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="p-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white transition-colors"
          aria-label="Send message"
        >
          <PaperAirplaneIcon className="h-5 w-5 transform hover:rotate-325" />
        </button>
      </form>
      <button
        onClick={() => clearMessages()}
        className="border px-4 py-2 rounded bg-gray-200 text-black dark:bg-gray-700 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-600 transition"
      >
        Clear Chat
      </button>
    </div>
  );
}
"use client";
import { useChatStore } from '@/services/chatApi';

export default function InputBox() {
  const { userInput, setUserInput } = useChatStore();

  return (
    <div className="flex mt-4">
      <input
        type="text"
        value={userInput}
        onChange={(e) => setUserInput(e.target.value)}
        placeholder="Enter task instructions..."
        className="border p-2 rounded w-full"
      />
    </div>
  );
}

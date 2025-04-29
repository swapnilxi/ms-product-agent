"use client";
import { useEffect, useRef } from 'react';
import { useChatStore } from '@/services/chatApi';
import MessageBubble from './MessageBubble';

export default function ChatInterface() {
  const { messages } = useChatStore();
  const bottomRef = useRef(null);
  const userMessageRef = useRef(null);

  useEffect(() => {
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.role === 'user') {
        userMessageRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }, [messages]);

  return (
    <div className="p-4 rounded h-full overflow-y-auto flex flex-col gap-4 text-black">
      {messages.map((msg, idx) => (
        <div key={idx} ref={msg.role === 'user' ? userMessageRef : null}>
          <MessageBubble role={msg.role} content={msg.content} />
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

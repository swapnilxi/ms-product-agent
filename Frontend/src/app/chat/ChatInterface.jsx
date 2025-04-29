"use client";
import React from 'react';
import { useEffect, useRef } from 'react';
import { useChatStore } from '@/services/chatApi';
import MessageBubble from './MessageBubble';

export default function ChatInterface() {
  const { messages } = useChatStore();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="p-4 rounded h-full overflow-y-scroll flex flex-col gap-2">
      {messages.map((msg, idx) => (
        <MessageBubble key={idx} role={msg.role} content={msg.content} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

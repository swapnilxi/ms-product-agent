"use client";

import ReactMarkdown from 'react-markdown';

export default function MessageBubble({ role, content }) {
  const isUser = role === 'user';
  const displayName = isUser
  ? 'You'
  : role
      ?.replace(/_/g, ' ')
      ?.replace(/bot/i, 'Agent')
      .trim()
      .replace(/\b\w/g, (c) => c.toUpperCase()); // Capitalize each word



  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`p-3 rounded-lg 
        ${isUser ? 'max-w-[70%]' : 'max-w-[90%]'} 
        ${isUser ? 'bg-blue-500 text-white' : 'bg-gray-200 text-black'} 
        break-words`}
      >
        
        {!isUser && 
          <div className="text-sm font-semibold
           text-gray-700 mb-1 border-b-2 border-gray-300 pb-1 px-2 py-2">
            {displayName}
          </div>
        }
        <ReactMarkdown
          components={{
            p: ({ node, ...props }) => <p className="mb-2" {...props} />,
            h1: ({ node, ...props }) => <h1 className="text-2xl font-bold my-2" {...props} />,
            h2: ({ node, ...props }) => <h2 className="text-xl font-semibold my-2" {...props} />,
            li: ({ node, ...props }) => <li className="list-disc ml-6" {...props} />,
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}

export default function MessageBubble({ role, content }) {
    const isUser = role === 'user';
  
    return (
      <div className={`p-2 rounded ${isUser ? 'bg-blue-100 text-right' : 'bg-gray-100 text-left'}`}>
        <p><strong>{isUser ? "You" : "Agent"}:</strong> {content}</p>
      </div>
    );
  }
  
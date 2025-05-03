import { Loader2 } from 'lucide-react';

export default function ChatLoader() {
  return (
    <div className="flex items-start space-x-2 px-4 py-2 animate-pulse">
      <div className="bg-gray-100 text-gray-800 rounded-xl px-4 py-2 max-w-xs shadow-sm">
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
          <span className="text-sm">Please wait while we are loading...</span>
        </div>
      </div>
    </div>
  );
}

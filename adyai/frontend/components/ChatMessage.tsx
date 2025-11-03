interface Source {
  title: string;
  content: string;
  score: number;
  source_type: string;
  source_url?: string;
}

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  sources?: Source[];
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  if (message.isUser) {
    return (
      <div className="flex justify-end">
        <div className="flex items-start gap-4 max-w-[80%] flex-row-reverse">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-600 to-purple-800 flex items-center justify-center text-2xl flex-shrink-0">
            👤
          </div>
          <div className="bg-gradient-to-r from-purple-600 to-purple-800 text-white rounded-2xl rounded-tr-sm px-6 py-4 shadow-md">
            <p className="whitespace-pre-wrap">{message.text}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="flex items-start gap-4 max-w-[80%]">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-400 to-red-500 flex items-center justify-center text-2xl flex-shrink-0">
          🧘
        </div>
        <div className="bg-white rounded-2xl rounded-tl-sm px-6 py-4 shadow-md">
          <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
            {message.text}
          </p>

          {message.sources && message.sources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs font-semibold text-gray-600 mb-2">
                📚 Sources:
              </p>
              <div className="space-y-2">
                {message.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="text-xs bg-gray-50 rounded-lg p-2"
                  >
                    <span className="font-semibold text-purple-700">
                      {source.title}
                    </span>
                    <span className="text-gray-500 ml-2">
                      ({Math.round(source.score * 100)}% match)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

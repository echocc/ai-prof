import ReactMarkdown from 'react-markdown';

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
          <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-2xl rounded-tr-sm px-6 py-4 shadow-md">
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{message.text}</ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="flex items-start gap-4 max-w-[80%]">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-200 to-gray-400 flex items-center justify-center text-2xl flex-shrink-0">
          🧘
        </div>
        <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-6 py-4 shadow-md">
          <div className="prose prose-sm max-w-none text-gray-800">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="mb-2 ml-4 list-disc">{children}</ul>,
                ol: ({ children }) => <ol className="mb-2 ml-4 list-decimal">{children}</ol>,
                li: ({ children }) => <li className="mb-1">{children}</li>,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                code: ({ children }) => <code className="bg-gray-200 px-1 py-0.5 rounded text-sm">{children}</code>,
                pre: ({ children }) => <pre className="bg-gray-200 p-2 rounded overflow-x-auto mb-2">{children}</pre>,
              }}
            >
              {message.text}
            </ReactMarkdown>
          </div>

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

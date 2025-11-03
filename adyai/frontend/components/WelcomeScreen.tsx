interface WelcomeScreenProps {
  onQuestionClick: (question: string) => void;
}

export default function WelcomeScreen({ onQuestionClick }: WelcomeScreenProps) {
  const exampleQuestions = [
    "What is awakening?",
    "How do I relate to thoughts?",
    "What is the nature of awareness?",
    "What does it mean to let go?",
  ];

  return (
    <div className="text-center py-12 px-6">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-4xl font-bold text-gray-800 mb-4">
          Welcome to Adyai
        </h2>
        <p className="text-lg text-gray-600 mb-8 leading-relaxed">
          Ask me anything about Adyashanti's teachings on awakening, awareness,
          and the nature of reality. I have access to his books, talks, and writings.
        </p>

        <div className="space-y-4">
          <p className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            Try asking:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {exampleQuestions.map((question, idx) => (
              <button
                key={idx}
                onClick={() => onQuestionClick(question)}
                className="bg-white border-2 border-gray-200 hover:border-purple-500 rounded-xl p-4 text-left transition-all hover:shadow-lg hover:scale-105 text-gray-700 hover:text-purple-700"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

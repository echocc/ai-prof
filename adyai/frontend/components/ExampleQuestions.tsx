interface ExampleQuestionsProps {
  onQuestionClick: (question: string) => void;
}

export default function ExampleQuestions({ onQuestionClick }: ExampleQuestionsProps) {
  const exampleQuestions = [
    "What is awakening?",
    "How do I relate to thoughts?",
    "What is the nature of awareness?",
    "What does it mean to let go?",
  ];

  return (
    <div className="text-center py-12 px-6">
      <div className="max-w-3xl mx-auto">
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-3">
            {exampleQuestions.map((question, idx) => (
              <button
                key={idx}
                onClick={() => onQuestionClick(question)}
                className="bg-purple-50 border-2 border-purple-200 hover:border-purple-400 rounded-xl p-4 text-left transition-all hover:shadow-md text-gray-700 hover:text-purple-700 hover:bg-purple-100"
              >
                {question}
              </button>
            ))}
          </div>
      </div>
    </div>
  );
}

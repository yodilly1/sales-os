"use client";

import { useState } from "react";

interface Question {
  question: string;
  category: string;
  context?: string;
  follow_ups?: string[];
}

interface QuestionsSectionProps {
  questions: Question[];
}

export function QuestionsSection({ questions }: QuestionsSectionProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const categories = Array.from(new Set(questions.map((q) => q.category)));

  const getCategoryColor = (category: string) => {
    const colors: Record<string, { bg: string; text: string; border: string }> = {
      situation: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
      pain: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200" },
      impact: { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
      critical_event: { bg: "bg-yellow-50", text: "text-yellow-700", border: "border-yellow-200" },
      decision: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
      discovery: { bg: "bg-green-50", text: "text-green-700", border: "border-green-200" },
    };
    return colors[category] || { bg: "bg-gray-50", text: "text-gray-700", border: "border-gray-200" };
  };

  const formatCategory = (category: string) => {
    return category
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const filteredQuestions = activeCategory
    ? questions.filter((q) => q.category === activeCategory)
    : questions;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          Questions to Ask
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Strategic questions aligned with SPICED methodology
        </p>
      </div>

      {/* Category Filters */}
      <div className="px-6 py-3 bg-gray-50 border-b border-gray-100 overflow-x-auto">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              activeCategory === null
                ? "bg-gray-900 text-white"
                : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-100"
            }`}
          >
            All ({questions.length})
          </button>
          {categories.map((category) => {
            const count = questions.filter((q) => q.category === category).length;
            const colors = getCategoryColor(category);
            return (
              <button
                key={category}
                onClick={() => setActiveCategory(category)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  activeCategory === category
                    ? `${colors.bg} ${colors.text} border ${colors.border}`
                    : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-100"
                }`}
              >
                {formatCategory(category)} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* Questions List */}
      <div className="divide-y divide-gray-100">
        {filteredQuestions.map((question, index) => {
          const colors = getCategoryColor(question.category);
          const isExpanded = expandedIndex === index;

          return (
            <div key={index} className="px-6 py-4 hover:bg-gray-50 transition-colors">
              <div
                className="cursor-pointer"
                onClick={() => setExpandedIndex(isExpanded ? null : index)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors.bg} ${colors.text}`}
                      >
                        {formatCategory(question.category)}
                      </span>
                    </div>
                    <p className="text-gray-900 font-medium">{question.question}</p>
                    {question.context && (
                      <p className="text-sm text-gray-500 mt-1">{question.context}</p>
                    )}
                  </div>
                  {question.follow_ups && question.follow_ups.length > 0 && (
                    <button className="ml-4 text-gray-400 hover:text-gray-600">
                      <svg
                        className={`w-5 h-5 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 9l-7 7-7-7"
                        />
                      </svg>
                    </button>
                  )}
                </div>
              </div>

              {/* Follow-up Questions */}
              {isExpanded && question.follow_ups && question.follow_ups.length > 0 && (
                <div className="mt-4 pl-4 border-l-2 border-gray-200">
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                    Follow-up Questions
                  </p>
                  <ul className="space-y-2">
                    {question.follow_ups.map((followUp, fIndex) => (
                      <li
                        key={fIndex}
                        className="text-sm text-gray-600 flex items-start"
                      >
                        <svg
                          className="w-4 h-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 5l7 7-7 7"
                          />
                        </svg>
                        {followUp}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredQuestions.length === 0 && (
        <div className="px-6 py-12 text-center text-gray-500">
          No questions in this category
        </div>
      )}
    </div>
  );
}

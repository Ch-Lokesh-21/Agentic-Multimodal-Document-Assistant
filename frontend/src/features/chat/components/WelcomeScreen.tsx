import React from "react";

interface WelcomeScreenProps {
  onCreateSession: () => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  onCreateSession,
}) => {
  return (
    <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-gray-50">
      <div className="max-w-2xl mx-auto px-8 text-center">
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-100 rounded-full mb-6">
            <svg
              className="w-10 h-10 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to Research Paper Assistance
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Your AI-powered assistant for analyzing research papers and
            documents
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
              <svg
                className="w-6 h-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">
              Upload Documents
            </h3>
            <p className="text-sm text-gray-600">
              Upload PDF, DOC, or TXT files to analyze
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Ask Questions</h3>
            <p className="text-sm text-gray-600">
              Get instant answers from your documents
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
              <svg
                className="w-6 h-6 text-purple-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Get Citations</h3>
            <p className="text-sm text-gray-600">
              Receive detailed citations and sources
            </p>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Getting Started</h3>
          <ol className="text-left space-y-2 text-sm text-gray-700">
            <li className="flex items-start">
              <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-600 text-white rounded-full mr-3 flex-shrink-0 text-xs font-semibold">
                1
              </span>
              <span>
                Create a new session or select an existing one from the left
                sidebar
              </span>
            </li>
            <li className="flex items-start">
              <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-600 text-white rounded-full mr-3 flex-shrink-0 text-xs font-semibold">
                2
              </span>
              <span>Upload your research papers or documents</span>
            </li>
            <li className="flex items-start">
              <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-600 text-white rounded-full mr-3 flex-shrink-0 text-xs font-semibold">
                3
              </span>
              <span>
                Ask questions and get AI-powered insights with citations
              </span>
            </li>
          </ol>
        </div>

        <div className="mt-8">
          <button
            onClick={onCreateSession}
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium shadow-sm transition-colors"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Create Your First Session
          </button>
        </div>
      </div>
    </div>
  );
};

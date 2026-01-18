import { useState, useRef, useEffect } from "react";
import type { UploadData } from "../App";
import { queryLogs } from "../services/api";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  sources?: Array<{
    content: string;
    score: number;
    source: string;
  }>;
  timestamp: Date;
}

// Helper function to parse and render markdown
function parseMarkdown(text: string) {
  const parts: (string | { type: string; content: string })[] = [];
  let lastIndex = 0;
  
  // Match **text** for bold
  const boldRegex = /\*\*(.*?)\*\*/g;
  let match;
  
  while ((match = boldRegex.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    // Add bold text
    parts.push({ type: "bold", content: match[1] });
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  
  return parts;
}

interface ChatInterfaceProps {
  uploadData: UploadData;
  onReset: () => void;
}

export default function ChatInterface({
  uploadData,
  onReset,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "assistant",
      content: `Hi! I've loaded your log file "${uploadData.filename}". I'm ready to help you analyze it. Ask me any questions about the logs and I'll search through them to find relevant information.`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: input,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await queryLogs(input, uploadData.collectionName);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : "Unknown error"}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="bg-slate-800/50 backdrop-blur-xl border-b border-slate-700/50 px-8 py-5 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-linear-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center shadow-lg">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">CrashGPT</h1>
              <p className="text-xs text-gray-400">{uploadData.filename}</p>
            </div>
          </div>
          <button
            onClick={onReset}
            className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white bg-slate-700/50 hover:bg-slate-600/50 rounded-lg transition-colors"
          >
            ↻ New Log
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-10">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-2xl ${
                  message.type === "user"
                    ? "bg-linear-to-br from-purple-600 to-pink-600 text-white rounded-3xl rounded-tr-lg"
                    : "bg-slate-800/50 border border-slate-700/50 text-gray-100 rounded-3xl rounded-tl-lg"
                } px-6 py-4 shadow-lg`}
              >
                <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">
                  {typeof message.content === 'string' 
                    ? parseMarkdown(message.content).map((part, idx) => 
                        typeof part === 'string' 
                          ? part 
                          : <strong key={idx}>{part.content}</strong>
                      )
                    : message.content
                  }
                </p>

                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-slate-600/50">
                    <button
                      onClick={() =>
                        setExpandedSources(
                          expandedSources === message.id ? null : message.id,
                        )
                      }
                      className="text-xs font-medium text-purple-300 hover:text-purple-200 flex items-center space-x-1 transition-colors"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                        />
                      </svg>
                      <span>{message.sources.length} sources found</span>
                      <svg
                        className={`w-4 h-4 transition-transform ${
                          expandedSources === message.id ? "rotate-180" : ""
                        }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 14l-7 7m0 0l-7-7m7 7V3"
                        />
                      </svg>
                    </button>

                    {expandedSources === message.id && (
                      <div className="mt-4 space-y-3">
                        {message.sources.map((source, idx) => (
                          <div
                            key={idx}
                            className="bg-slate-700/30 rounded-lg p-4 text-xs border border-slate-600/30"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <span className="text-purple-300 font-medium">
                                Source {idx + 1}
                              </span>
                              <span className="text-gray-400 text-xs">
                                Score: {(source.score * 100).toFixed(0)}%
                              </span>
                            </div>
                            <p className="text-gray-300 line-clamp-3 max-h-15 overflow-hidden">
                              {source.content}
                            </p>
                            <p className="text-gray-500 text-xs mt-2">
                              {source.source}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-slate-800/50 border border-slate-700/50 text-gray-100 rounded-3xl rounded-tl-lg px-6 py-4 shadow-lg">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div
                      className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0s" }}
                    />
                    <div
                      className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    />
                    <div
                      className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    />
                  </div>
                  <span className="text-sm text-gray-400 ml-2">
                    Analyzing logs...
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-slate-800/50 backdrop-blur-xl border-t border-slate-700/50 px-8 py-8 sticky bottom-0">
        <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto">
          <div className="flex space-x-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your logs..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-6 py-3 bg-linear-to-r from-purple-600 to-pink-600 text-white font-medium rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg"
            >
              <svg
                className="w-5 h-5 rotate-90"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            The AI will search your logs and provide insights based on the most
            relevant segments.
          </p>
        </form>
      </div>
    </div>
  );
}

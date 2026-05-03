"use client";

import { useRef, useState } from "react";
import { streamQuery, type Citation } from "@/lib/sse";
import TimestampBadge from "@/components/TimestampBadge";

interface Message {
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
}

interface Props {
  videoId: string;
  onTimestampClick: (seconds: number) => void;
}

export default function ChatPanel({ videoId, onTimestampClick }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const cancelRef = useRef<(() => void) | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  function sendQuestion() {
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);

    let assistantText = "";
    const assistantIndex = messages.length + 1;

    setMessages((prev) => [...prev, { role: "assistant", text: "" }]);

    cancelRef.current = streamQuery(
      videoId,
      question,
      (chunk) => {
        assistantText += chunk;
        setMessages((prev) =>
          prev.map((m, i) =>
            i === assistantIndex ? { ...m, text: assistantText } : m,
          ),
        );
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
      },
      (citations) => {
        setMessages((prev) =>
          prev.map((m, i) =>
            i === assistantIndex ? { ...m, citations } : m,
          ),
        );
      },
      () => {
        setLoading(false);
      },
      (err) => {
        setMessages((prev) =>
          prev.map((m, i) =>
            i === assistantIndex
              ? { ...m, text: `Error: ${err.message}` }
              : m,
          ),
        );
        setLoading(false);
      },
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center text-gray-600 text-sm text-center">
            Ask anything about the video content
            <br />
            <span className="text-xs mt-1 block text-gray-700">
              e.g. "When does the speaker discuss pricing?"
            </span>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed space-y-2 ${
                msg.role === "user"
                  ? "bg-emerald-700 text-white rounded-br-sm"
                  : "bg-gray-800 text-gray-200 rounded-bl-sm"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
              {msg.citations && msg.citations.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1 border-t border-gray-700">
                  {msg.citations.map((c, ci) => (
                    <TimestampBadge
                      key={ci}
                      seconds={c.start_time}
                      onClick={onTimestampClick}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendQuestion()}
            placeholder="Ask about this video..."
            disabled={loading}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-emerald-600 transition-colors disabled:opacity-50"
          />
          <button
            onClick={sendQuestion}
            disabled={loading || !input.trim()}
            className="btn-primary px-4 py-2.5 rounded-xl"
          >
            {loading ? (
              <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

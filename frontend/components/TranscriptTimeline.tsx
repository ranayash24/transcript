"use client";

import { useEffect, useRef } from "react";
import type { Segment } from "@/lib/api";
import clsx from "clsx";

interface Props {
  segments: Segment[];
  currentTime: number;
  onSeek: (seconds: number) => void;
}

function fmt(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
}

export default function TranscriptTimeline({ segments, currentTime, onSeek }: Props) {
  const activeRef = useRef<HTMLButtonElement>(null);

  const activeIndex = segments.findLastIndex(
    (seg) => currentTime >= seg.start_time && currentTime < seg.end_time,
  );

  useEffect(() => {
    activeRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [activeIndex]);

  if (segments.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">
        No segments yet
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto border-t border-gray-800">
      <div className="px-3 py-2 text-xs text-gray-500 font-medium uppercase tracking-wider sticky top-0 bg-gray-950">
        Transcript
      </div>
      {segments.map((seg, i) => {
        const isActive = i === activeIndex;
        return (
          <button
            key={seg.id}
            ref={isActive ? activeRef : undefined}
            onClick={() => onSeek(seg.start_time)}
            className={clsx(
              "w-full text-left px-3 py-2.5 flex gap-3 items-start transition-colors text-sm border-b border-gray-800/50 hover:bg-gray-800/50",
              isActive ? "bg-gray-800" : "",
            )}
          >
            <span className="text-xs font-mono text-emerald-500 mt-0.5 shrink-0">
              {fmt(seg.start_time)}
            </span>
            <span className={clsx("leading-relaxed", isActive ? "text-white" : "text-gray-400")}>
              {seg.fused_text ?? seg.transcript_text ?? ""}
            </span>
          </button>
        );
      })}
    </div>
  );
}

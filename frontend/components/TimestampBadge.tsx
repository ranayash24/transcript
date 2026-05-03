"use client";

interface Props {
  seconds: number;
  onClick: (seconds: number) => void;
}

function fmt(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
}

export default function TimestampBadge({ seconds, onClick }: Props) {
  return (
    <button
      onClick={() => onClick(seconds)}
      className="inline-flex items-center gap-1 bg-emerald-900/60 hover:bg-emerald-700/60 text-emerald-300 text-xs font-mono px-2 py-0.5 rounded-md border border-emerald-700/50 transition-colors"
    >
      <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
          clipRule="evenodd"
        />
      </svg>
      {fmt(seconds)}
    </button>
  );
}

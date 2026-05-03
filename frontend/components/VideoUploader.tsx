"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import clsx from "clsx";

interface Props {
  onComplete: (videoId: string) => void;
}

export default function VideoUploader({ onComplete }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      const allowed = ["video/mp4", "video/quicktime", "video/webm"];
      if (!allowed.includes(file.type)) {
        setError("Please upload an MP4, MOV, or WebM file.");
        return;
      }
      setError(null);
      setUploading(true);
      setProgress(0);

      try {
        const result = await api.uploadVideo(file, setProgress);
        // Store job ID for status polling on video page
        localStorage.setItem(`job_${result.video_id}`, result.job_id);
        onComplete(result.video_id);
      } catch (err) {
        setError((err as Error).message);
        setUploading(false);
      }
    },
    [onComplete],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div className="w-full space-y-3">
      <label
        className={clsx(
          "flex flex-col items-center justify-center gap-3 w-full border-2 border-dashed rounded-2xl p-12 cursor-pointer transition-colors",
          dragging
            ? "border-emerald-400 bg-emerald-950"
            : "border-gray-700 hover:border-gray-500 bg-gray-900",
          uploading && "pointer-events-none opacity-60",
        )}
        onDragEnter={() => setDragging(true)}
        onDragLeave={() => setDragging(false)}
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
      >
        <svg
          className="w-10 h-10 text-gray-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <div className="text-center">
          <p className="text-gray-300 font-medium">
            {uploading ? "Uploading..." : "Drop your video here"}
          </p>
          <p className="text-gray-500 text-sm mt-1">MP4, MOV, WebM · up to 500 MB</p>
        </div>
        <input
          type="file"
          accept="video/mp4,video/quicktime,video/webm"
          className="sr-only"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
          disabled={uploading}
        />
      </label>

      {/* Progress bar */}
      {uploading && (
        <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
          <div
            className="h-full bg-emerald-500 transition-all duration-200 rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {error && <p className="text-red-400 text-sm text-center">{error}</p>}
    </div>
  );
}

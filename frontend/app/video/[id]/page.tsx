"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import VideoPlayer from "@/components/VideoPlayer";
import ChatPanel from "@/components/ChatPanel";
import TranscriptTimeline from "@/components/TranscriptTimeline";
import JobStatusBar from "@/components/JobStatusBar";
import { api, type Segment, type VideoMeta } from "@/lib/api";

export default function VideoPage() {
  const { id } = useParams<{ id: string }>();
  const [video, setVideo] = useState<VideoMeta | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [playbackUrl, setPlaybackUrl] = useState<string>("");
  const [currentTime, setCurrentTime] = useState(0);
  const [seekTo, setSeekTo] = useState<number | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const playerRef = useRef<HTMLVideoElement>(null);

  // Poll for job ID from localStorage (set by uploader)
  useEffect(() => {
    const stored = localStorage.getItem(`job_${id}`);
    if (stored) setJobId(stored);
  }, [id]);

  // Poll video metadata until ready
  useEffect(() => {
    let timer: NodeJS.Timeout;
    async function poll() {
      try {
        const meta = await api.getVideo(id);
        setVideo(meta);
        if (meta.status === "ready") {
          const segs = await api.getSegments(id);
          setSegments(segs);
          const { url } = await api.getPlaybackUrl(id);
          setPlaybackUrl(url);
        } else if (meta.status !== "error") {
          timer = setTimeout(poll, 3000);
        }
      } catch {
        timer = setTimeout(poll, 5000);
      }
    }
    poll();
    return () => clearTimeout(timer);
  }, [id]);

  function handleSeek(seconds: number) {
    setSeekTo(seconds);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-65px)]">
      {/* Job progress bar */}
      {jobId && video?.status !== "ready" && (
        <JobStatusBar jobId={jobId} videoStatus={video?.status ?? "uploading"} />
      )}

      {video?.status === "ready" ? (
        <div className="flex flex-1 overflow-hidden">
          {/* Left: player + timeline */}
          <div className="flex flex-col w-[55%] border-r border-gray-800 overflow-hidden">
            <VideoPlayer
              src={playbackUrl}
              seekTo={seekTo}
              onTimeUpdate={setCurrentTime}
              ref={playerRef}
            />
            <TranscriptTimeline
              segments={segments}
              currentTime={currentTime}
              onSeek={handleSeek}
            />
          </div>
          {/* Right: Q&A chat */}
          <div className="flex-1 overflow-hidden">
            <ChatPanel videoId={id} onTimestampClick={handleSeek} />
          </div>
        </div>
      ) : (
        <div className="flex flex-1 items-center justify-center text-gray-500">
          {video?.status === "error"
            ? "Processing failed. Please try uploading again."
            : "Processing your video..."}
        </div>
      )}
    </div>
  );
}

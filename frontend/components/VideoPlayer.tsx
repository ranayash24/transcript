"use client";

import { forwardRef, useEffect, useRef } from "react";

interface Props {
  src: string;
  seekTo: number | null;
  onTimeUpdate: (time: number) => void;
}

const VideoPlayer = forwardRef<HTMLVideoElement, Props>(
  ({ src, seekTo, onTimeUpdate }, ref) => {
    const internalRef = useRef<HTMLVideoElement>(null);
    const videoRef = (ref as React.RefObject<HTMLVideoElement>) ?? internalRef;

    useEffect(() => {
      if (seekTo !== null && videoRef.current) {
        videoRef.current.currentTime = seekTo;
        videoRef.current.play().catch(() => {});
      }
    }, [seekTo]);

    return (
      <div className="bg-black flex-shrink-0">
        <video
          ref={videoRef}
          src={src}
          controls
          className="w-full max-h-[45vh] object-contain"
          onTimeUpdate={(e) => onTimeUpdate((e.target as HTMLVideoElement).currentTime)}
        />
      </div>
    );
  },
);

VideoPlayer.displayName = "VideoPlayer";
export default VideoPlayer;

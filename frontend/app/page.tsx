"use client";

import { useRouter } from "next/navigation";
import VideoUploader from "@/components/VideoUploader";

export default function HomePage() {
  const router = useRouter();

  function handleUploadComplete(videoId: string) {
    router.push(`/video/${videoId}`);
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-65px)] px-4 py-16">
      <div className="w-full max-w-xl text-center space-y-6">
        <h1 className="text-4xl font-bold text-white">
          Query your video with{" "}
          <span className="text-emerald-400">natural language</span>
        </h1>
        <p className="text-gray-400 text-lg">
          Upload a video. Ask anything. Get timestamped answers powered by AI.
        </p>
        <VideoUploader onComplete={handleUploadComplete} />
      </div>
    </div>
  );
}

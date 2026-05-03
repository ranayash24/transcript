"use client";

import { useEffect, useState } from "react";
import { api, type JobStatus } from "@/lib/api";
import clsx from "clsx";

interface Props {
  jobId: string;
  videoStatus: string;
}

const STEPS = ["Uploading", "Extracting frames", "Transcribing audio", "Captioning frames", "Fusing segments", "Indexing", "Ready"];

export default function JobStatusBar({ jobId, videoStatus }: Props) {
  const [job, setJob] = useState<JobStatus | null>(null);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    async function poll() {
      try {
        const status = await api.getJobStatus(jobId);
        setJob(status);
        if (status.status !== "done" && status.status !== "failed") {
          timer = setTimeout(poll, 2000);
        }
      } catch {
        timer = setTimeout(poll, 3000);
      }
    }
    poll();
    return () => clearTimeout(timer);
  }, [jobId]);

  if (!job || job.status === "done") return null;

  const pct = job.progress_pct;
  const failed = job.status === "failed";

  return (
    <div className={clsx(
      "border-b px-4 py-3 space-y-2",
      failed ? "border-red-800 bg-red-950/30" : "border-gray-800 bg-gray-900",
    )}>
      <div className="flex items-center justify-between text-sm">
        <span className={clsx("font-medium", failed ? "text-red-400" : "text-gray-300")}>
          {failed ? `Error: ${job.error ?? "Processing failed"}` : job.current_step ?? "Processing..."}
        </span>
        <span className="text-gray-500 tabular-nums">{pct}%</span>
      </div>
      {!failed && (
        <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
          <div
            className="h-full bg-emerald-500 transition-all duration-500 rounded-full"
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
    </div>
  );
}

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface VideoMeta {
  id: string;
  filename: string;
  status: string;
  duration_seconds: number | null;
  created_at: string;
}

export interface Segment {
  id: string;
  start_time: number;
  end_time: number;
  transcript_text: string | null;
  frame_caption: string | null;
  fused_text: string | null;
  keyframe_url: string | null;
}

export interface UploadResult {
  video_id: string;
  job_id: string;
  status_url: string;
}

export interface JobStatus {
  job_id: string;
  video_id: string;
  status: string;
  current_step: string | null;
  progress_pct: number;
  error: string | null;
}

function sessionId(): string {
  if (typeof window === "undefined") return "ssr";
  let id = localStorage.getItem("session_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("session_id", id);
  }
  return id;
}

export const api = {
  async uploadVideo(file: File, onProgress?: (pct: number) => void): Promise<UploadResult> {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append("file", file);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${BASE}/api/videos/upload`);
      xhr.setRequestHeader("x-session-id", sessionId());

      if (onProgress) {
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
        });
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      };
      xhr.onerror = () => reject(new Error("Network error"));
      xhr.send(formData);
    });
  },

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const res = await fetch(`${BASE}/api/jobs/${jobId}/status`);
    if (!res.ok) throw new Error("Failed to fetch job status");
    return res.json();
  },

  async getVideo(videoId: string): Promise<VideoMeta> {
    const res = await fetch(`${BASE}/api/videos/${videoId}`);
    if (!res.ok) throw new Error("Failed to fetch video");
    return res.json();
  },

  async getSegments(videoId: string, page = 1, limit = 100): Promise<Segment[]> {
    const res = await fetch(`${BASE}/api/videos/${videoId}/segments?page=${page}&limit=${limit}`);
    if (!res.ok) throw new Error("Failed to fetch segments");
    return res.json();
  },

  async getPlaybackUrl(videoId: string): Promise<{ url: string }> {
    const res = await fetch(`${BASE}/api/videos/${videoId}/playback-url`);
    if (!res.ok) throw new Error("Failed to get playback URL");
    return res.json();
  },
};

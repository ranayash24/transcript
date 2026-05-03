const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Citation {
  start_time: number;
  end_time: number;
  text: string;
}

export function streamQuery(
  videoId: string,
  question: string,
  onChunk: (text: string) => void,
  onCitations: (citations: Citation[]) => void,
  onDone: () => void,
  onError: (err: Error) => void,
): () => void {
  let cancelled = false;
  const controller = new AbortController();

  async function run() {
    try {
      const response = await fetch(`${BASE}/api/videos/${videoId}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Query failed: ${response.statusText}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done || cancelled) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("event: citations")) {
            // next data line has citations
            continue;
          }
          if (line.startsWith("data: ")) {
            const payload = line.slice(6);
            if (payload === "[DONE]") {
              onDone();
              return;
            }
            try {
              const citations: Citation[] = JSON.parse(payload);
              onCitations(citations);
            } catch {
              onChunk(payload);
            }
          }
        }
      }
    } catch (err) {
      if (!cancelled) onError(err as Error);
    }
  }

  run();

  return () => {
    cancelled = true;
    controller.abort();
  };
}

"use client";

import { useEffect, useRef, useState } from "react";
import { Film } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { SectionCard } from "@/components/shared/section-card";
import { voiceframeApiUrl, voiceframeMediaUrl } from "@/lib/voiceframe-api";

type JobStatus = "queued" | "running" | "complete" | "failed";

type GenerateResponse = {
  job_id?: string;
  status?: string;
  error?: string;
};

type StatusResponse = {
  status?: JobStatus | string;
  progress?: number;
  error?: string;
  video_url?: string;
};

type ResultResponse = {
  video_url?: string;
  error?: string;
};

export default function AnimatedStoryPage() {
  const [prompt, setPrompt] = useState("");
  const [jobId, setJobId] = useState<string>("");
  const [jobStatus, setJobStatus] = useState<JobStatus | "">("");
  const [progress, setProgress] = useState<number>(0);
  const [statusText, setStatusText] = useState<string>("");
  const [videoUrl, setVideoUrl] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const pollRef = useRef<number | null>(null);

  const stopPolling = () => {
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const fetchStatus = async (id: string) => {
    const res = await fetch(voiceframeApiUrl(`/voiceframe/status/${encodeURIComponent(id)}/`));
    const data = (await res.json()) as StatusResponse;
    if (!res.ok) {
      throw new Error(data?.error || "Failed to fetch status");
    }

    const s = (data.status || "") as JobStatus | string;
    const p = typeof data.progress === "number" ? data.progress : 0;

    setJobStatus((s as JobStatus) || "");
    setProgress(p);

    if (s === "failed") {
      stopPolling();
      setLoading(false);
      setStatusText(data.error || "Generation failed");
      return;
    }

    if (s === "complete") {
      stopPolling();
      setLoading(false);

      if (data.video_url) {
        setVideoUrl(voiceframeMediaUrl(data.video_url));
        setStatusText("Completed.");
        return;
      }

      const resultRes = await fetch(voiceframeApiUrl(`/voiceframe/result/${encodeURIComponent(id)}/`));
      const resultData = (await resultRes.json()) as ResultResponse;
      if (!resultRes.ok) {
        throw new Error(resultData?.error || "Failed to fetch result");
      }

      if (resultData.video_url) {
        setVideoUrl(voiceframeMediaUrl(resultData.video_url));
        setStatusText("Completed.");
      } else {
        setStatusText("Completed, but no video URL returned.");
      }
    }
  };

  useEffect(() => {
    return () => stopPolling();
  }, []);

  const startPolling = (id: string) => {
    stopPolling();
    pollRef.current = window.setInterval(() => {
      fetchStatus(id).catch((e) => {
        stopPolling();
        setLoading(false);
        setStatusText(e instanceof Error ? e.message : "Status polling failed");
      });
    }, 1500);
  };

  const handleGenerate = async () => {
    const p = prompt.trim();
    if (!p || loading) return;

    setLoading(true);
    setStatusText("Starting generation...");
    setProgress(0);
    setJobStatus("");

    try {
      const res = await fetch(voiceframeApiUrl("/voiceframe/generate/"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: p }),
      });

      const data = (await res.json()) as GenerateResponse;
      if (!res.ok) {
        throw new Error(data?.error || "Failed to start generation");
      }

      const id = (data.job_id || "").trim();
      if (!id) {
        throw new Error("No job_id returned");
      }

      setJobId(id);
      setStatusText("Generating...");
      startPolling(id);
      await fetchStatus(id);
    } catch (e) {
      setLoading(false);
      setStatusText(e instanceof Error ? e.message : "Generation failed");
    }
  };

  const isRunning = loading || jobStatus === "queued" || jobStatus === "running";

  return (
    <div className="p-6 lg:p-12 max-w-6xl mx-auto space-y-8">
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <Film className="h-8 w-8" />
          <h1 className="text-4xl font-bold">Animated Story</h1>
        </div>
        <p className="text-muted-foreground">
          Generate a short animated story video from a prompt.
        </p>
      </div>

      <SectionCard title="Prompt" description="Describe the story you want to generate">
        <div className="space-y-4">
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Example: A frog and a scorpion try to cross a river, with a moral at the end."
            className="min-h-[140px]"
            disabled={isRunning}
          />

          <div className="flex items-center gap-3">
            <Button onClick={handleGenerate} disabled={!prompt.trim() || isRunning}>
              {isRunning ? "Generating..." : "Generate"}
            </Button>

            {jobId ? (
              <span className="text-sm text-muted-foreground">Job: {jobId}</span>
            ) : null}
          </div>

          {statusText ? (
            <div className="text-sm text-muted-foreground">{statusText}</div>
          ) : null}

          {isRunning ? (
            <div className="text-sm text-muted-foreground">Progress: {Math.max(0, Math.min(100, Math.round(progress)))}%</div>
          ) : null}
        </div>
      </SectionCard>

      <SectionCard title="Result" description="Your generated video will appear here">
        {videoUrl ? (
          <div className="space-y-3">
            <video src={videoUrl} controls className="w-full rounded-lg border border-white/10" />
            <a className="text-sm underline text-muted-foreground" href={videoUrl} target="_blank" rel="noreferrer">
              Open video
            </a>
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">No video yet.</div>
        )}
      </SectionCard>
    </div>
  );
}

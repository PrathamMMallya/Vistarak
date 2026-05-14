"use client";

import { useState, useRef, useEffect } from "react";
import { Film, Wand2, ArrowLeft, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { SectionCard } from "@/components/shared/section-card";

type Domain = "Mathematics" | "Physics";
type ChatMessage = { role: "user" | "assistant"; text: string };

const TEMPLATES = [
  {
    id: "math.gradient_descent",
    title: "Gradient Descent",
    domain: "Mathematics",
    concept: "Finding minimum of a function",
    visuals: "Surface, contour, moving point, gradient arrow",
    icon: "📉"
  },
  {
    id: "math.eigenvalues",
    title: "Eigenvalues & Eigenvectors",
    domain: "Mathematics",
    concept: "Matrix transforming space",
    visuals: "Grid, vectors, transformation, invariant directions",
    icon: "📐"
  },
  {
    id: "math.fourier_series",
    title: "Fourier Series",
    domain: "Mathematics",
    concept: "Breaking signal into sine waves",
    visuals: "waves, partial sums, final waveform",
    icon: "🌊"
  },
  {
    id: "physics.projectile_motion",
    title: "Projectile Motion",
    domain: "Physics",
    concept: "Motion in x and y separately",
    visuals: "trajectory, velocity vectors, gravity",
    icon: "☄️"
  },
  {
    id: "physics.electric_field",
    title: "Electric Field & Potential",
    domain: "Physics",
    concept: "Field (vector) vs potential (scalar)",
    visuals: "charges, field lines, equipotential lines",
    icon: "⚡"
  },
  {
    id: "physics.wave_interference",
    title: "Wave Interference",
    domain: "Physics",
    concept: "Waves combining",
    visuals: "two waves → resulting wave",
    icon: "〰️"
  }
];

export default function ManimVisualizerPage() {
  const [selectedTemplate, setSelectedTemplate] = useState<typeof TEMPLATES[0] | null>(null);
  
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string>("");
  const [videoUrl, setVideoUrl] = useState<string>("");
  const [code, setCode] = useState<string>("");
  const [provider, setProvider] = useState<string>("");
  const [threadId, setThreadId] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to bottom when messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleTemplateSelect = async (template: typeof TEMPLATES[0]) => {
    setSelectedTemplate(template);
    setLoading(true);
    setStatus("Rendering template...");
    setVideoUrl("");
    setCode("");
    setProvider("");
    setThreadId("");
    setMessages([]);
    setPrompt("");

    try {
      // Fetch template metadata and render in parallel
      const [renderRes, infoRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/visualization/manim/generate/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            template_id: template.id,
            domain: template.domain,
            render_only: true,
          }),
        }),
        fetch(`http://127.0.0.1:8000/visualization/manim/template-info/?id=${encodeURIComponent(template.id)}`)
      ]);

      const renderData = await renderRes.json();
      if (!renderRes.ok || renderData.status !== "success") {
        throw new Error(renderData?.error || "Failed to render template");
      }

      setThreadId(renderData.thread_id || "");
      setProvider(renderData.provider || "Template");
      setCode(renderData.code || "");
      setVideoUrl(`http://127.0.0.1:8000${renderData.video_url}`);
      setStatus("Template rendered successfully.");

      // Build rich description from JSON metadata
      let assistantMsg = `📐 **${template.title}** loaded successfully!\n\n`;
      
      if (infoRes.ok) {
        const info = await infoRes.json();
        if (info.status === "success") {
          assistantMsg += `${info.description}\n\n`;

          if (info.variables && Object.keys(info.variables).length > 0) {
            assistantMsg += `🔧 **Variables you can tweak:**\n`;
            for (const [key, val] of Object.entries(info.variables) as [string, any][]) {
              assistantMsg += `  • ${key} = ${val.default} — ${val.description}\n`;
            }
            assistantMsg += `\n`;
          }

          if (info.what_to_modify) {
            assistantMsg += `💡 **Suggestions:** ${info.what_to_modify}`;
          }
        } else {
          assistantMsg += `What would you like to modify?`;
        }
      } else {
        assistantMsg += `What would you like to modify?`;
      }

      setMessages([{ role: "assistant", text: assistantMsg }]);
    } catch (e) {
      setStatus(`Error: ${e instanceof Error ? e.message : "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  const handleChatSubmit = async () => {
    if (!prompt.trim() || !selectedTemplate) return;
    
    const userPrompt = prompt.trim();
    setMessages((prev) => [...prev, { role: "user", text: userPrompt }]);
    setPrompt("");
    setLoading(true);
    setStatus("Processing...");
    
    try {
      const res = await fetch("http://127.0.0.1:8000/visualization/manim/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: userPrompt,
          domain: selectedTemplate.domain,
          thread_id: threadId || undefined,
          base_code_id: selectedTemplate.id,
        }),
      });

      const data = await res.json();
      if (!res.ok || data.status !== "success") {
        throw new Error(data?.error || "Request failed");
      }

      if (data.type === "explanation") {
        // Text-only reply — no video update
        setStatus("");
        setMessages((prev) => [...prev, { role: "assistant", text: data.message }]);
      } else {
        // Animation response — update video
        setThreadId(data.thread_id || threadId);
        setProvider(data.provider || "");
        setCode(data.code || "");
        setVideoUrl(`http://127.0.0.1:8000${data.video_url}`);
        setStatus("Animation updated successfully.");
        setMessages((prev) => [...prev, { role: "assistant", text: "✅ Animation updated! Check the video on the right." }]);
      }
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : "Unknown error";
      setStatus(`Error: ${errMsg}`);
      setMessages((prev) => [...prev, { role: "assistant", text: `❌ Error: ${errMsg}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 lg:p-12 max-w-7xl mx-auto space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold">Manim Visualizer</h1>
        <p className="text-muted-foreground">
          {selectedTemplate 
            ? `Editing Template: ${selectedTemplate.title}` 
            : "Choose a template to get started with an interactive Manim animation."}
        </p>
      </div>

      {!selectedTemplate ? (
        <div className="space-y-8">
          <SectionCard title="Mathematics Templates" description="Fundamental math concepts">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {TEMPLATES.filter(t => t.domain === "Mathematics").map(t => (
                <button
                  key={t.id}
                  onClick={() => handleTemplateSelect(t)}
                  className="text-left glass rounded-xl border border-white/10 p-6 hover:border-accent hover:bg-white/5 transition-all space-y-3 group"
                >
                  <div className="text-4xl group-hover:scale-110 transition-transform origin-left">{t.icon}</div>
                  <h3 className="text-xl font-bold text-white">{t.title}</h3>
                  <div className="space-y-1 mt-4">
                    <p className="text-sm text-white/80">
                      <span className="text-accent font-medium">Concept:</span> {t.concept}
                    </p>
                    <p className="text-xs text-white/60">
                      <span className="text-accent/80 font-medium">Visuals:</span> {t.visuals}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Physics Templates" description="Physical world simulations">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {TEMPLATES.filter(t => t.domain === "Physics").map(t => (
                <button
                  key={t.id}
                  onClick={() => handleTemplateSelect(t)}
                  className="text-left glass rounded-xl border border-white/10 p-6 hover:border-accent hover:bg-white/5 transition-all space-y-3 group"
                >
                  <div className="text-4xl group-hover:scale-110 transition-transform origin-left">{t.icon}</div>
                  <h3 className="text-xl font-bold text-white">{t.title}</h3>
                  <div className="space-y-1 mt-4">
                    <p className="text-sm text-white/80">
                      <span className="text-accent font-medium">Concept:</span> {t.concept}
                    </p>
                    <p className="text-xs text-white/60">
                      <span className="text-accent/80 font-medium">Visuals:</span> {t.visuals}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </SectionCard>
        </div>
      ) : (
        <div className="space-y-6 fade-in">
          <Button 
            variant="ghost" 
            className="mb-2 text-muted-foreground hover:text-white"
            onClick={() => setSelectedTemplate(null)}
          >
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Templates
          </Button>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-8">
            <SectionCard title="Interactive Chat" description="Ask questions or request animation changes" icon={<Wand2 size={18} />}>
              <div className="flex flex-col h-[600px]">
                <div className="flex-1 overflow-y-auto space-y-4 p-4 border border-border rounded-lg bg-black/20 mb-4 scrollbar-thin">
                  {messages.map((msg, idx) => (
                    <div 
                      key={idx} 
                      className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                        msg.role === "user" 
                          ? "bg-accent text-accent-foreground rounded-tr-sm" 
                          : "bg-card border border-border text-card-foreground rounded-tl-sm"
                      }`}>
                        <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-card border border-border text-card-foreground rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-3 text-sm text-muted-foreground">
                        <Wand2 size={14} className="animate-spin text-accent" /> 
                        <span>{status}</span>
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                <div className="flex gap-2 items-end">
                  <Textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Ask a question or request an animation change..."
                    className="min-h-[60px] max-h-[120px] resize-y rounded-xl border-border bg-black/40 focus-visible:ring-accent"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleChatSubmit();
                      }
                    }}
                  />
                  <Button 
                    className="h-[60px] px-6 rounded-xl bg-accent hover:bg-accent/90 text-accent-foreground font-semibold shadow-lg shadow-accent/20 transition-all active:scale-95" 
                    onClick={handleChatSubmit} 
                    disabled={loading || !prompt.trim()}
                  >
                    <Send size={18} />
                  </Button>
                </div>
              </div>
            </SectionCard>

            <SectionCard title="Animation Output" description={provider ? `Provider: ${provider}` : "Video preview"} icon={<Film size={18} />}>
              <div className="space-y-4">
                {videoUrl ? (
                  <div className="relative rounded-lg overflow-hidden border border-border shadow-2xl bg-black">
                    <video
                      key={videoUrl}
                      src={videoUrl}
                      controls
                      autoPlay
                      loop
                      className="w-full h-auto aspect-video object-contain"
                    />
                  </div>
                ) : (
                  <div className="aspect-video glass rounded-lg border border-white/10 flex flex-col items-center justify-center text-sm text-muted-foreground animate-pulse">
                    <Film size={32} className="mb-2 opacity-50" />
                    <span>{loading ? "Rendering video..." : "No video yet."}</span>
                  </div>
                )}
              </div>
            </SectionCard>
          </div>
        </div>
      )}
    </div>
  );
}

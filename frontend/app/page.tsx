"use client"

import { useState } from "react"
import Link from "next/link"
import { Video, FileText, BookOpen, Zap, Mic2, Languages, Sparkles, ArrowRight, Film } from "lucide-react"
import { Button } from "@/components/ui/button"

const modules = [
  {
    id: "video-transcription",
    title: "Video Transcription",
    description: "Extract and transcribe audio from videos with multi-language support",
    icon: Video,
    color: "from-blue-500 to-blue-600",
    href: "/video-transcription",
  },

  {
    id: "ocr",
    title: "OCR & Editable Docs",
    description: "Convert images and PDFs to editable text with intelligent processing",
    icon: BookOpen,
    color: "from-purple-500 to-purple-600",
    href: "/ocr",
  },

  {
    id: "tts",
    title: "Emotion TTS",
    description: "AI-labelled expressive speech — Groq emotion analysis + ChatterboxTurbo voice cloning",
    icon: Mic2,
    color: "from-pink-500 to-pink-600",
    href: "/tts",
  },

  {
    id: "manim-visualizer",
    title: "Manim Visualizer",
    description: "Create interactive mathematical and physical animations with AI",
    icon: Film,
    color: "from-orange-500 to-orange-600",
    href: "/manim-visualizer",
  },
  {
    id: "story-generator",
    title: "Story Video Generator",
    description: "Transform your narratives into cinematic visualizations with AI",
    icon: Sparkles,
    color: "from-purple-600 to-blue-600",
    href: "/story-generator",
  },
];

export default function Home() {
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-background p-6 lg:p-12">
      {/* Hero Section */}
      <div className="max-w-6xl mx-auto mb-16">
        <div className="relative mb-12">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 blur-3xl rounded-3xl" />
          <div className="relative">
            <h1 className="text-4xl lg:text-6xl font-bold text-foreground mb-4 text-balance">
              Your Complete <span className="gradient-text">Educational Platform</span>
            </h1>
            <p className="text-lg text-muted-foreground mb-8 text-balance">
              Powerful tools for content processing, translation, and learning. Transform your educational resources
              with AI-powered capabilities.
            </p>
            <div className="flex gap-4">
              <Button className="bg-primary hover:bg-primary/90 text-primary-foreground">
                <Sparkles size={18} />
                Get Started
              </Button>
              <Button variant="outline" className="border-border hover:bg-card bg-transparent">
                Learn More
                <ArrowRight size={18} />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Modules Grid */}
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-foreground mb-8">Available Tools</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {modules.map((module) => {
            const Icon = module.icon
            const isHovered = hoveredId === module.id

            return (
              <Link key={module.id} href={module.href}>
                <div
                  onMouseEnter={() => setHoveredId(module.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  className="group glass rounded-xl p-6 h-full transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 cursor-pointer hover:-translate-y-1"
                >
                  <div
                    className={`w-12 h-12 rounded-lg bg-gradient-to-br ${module.color} flex items-center justify-center mb-4 transition-transform group-hover:scale-110`}
                  >
                    <Icon size={24} className="text-white" />
                  </div>

                  <h3 className="text-lg font-semibold text-foreground mb-2">{module.title}</h3>

                  <p className="text-sm text-muted-foreground mb-4">{module.description}</p>

                  <div className="flex items-center gap-2 text-accent text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                    Explore
                    <ArrowRight size={16} />
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      </div>

      {/* System Methodology Section */}
      <div className="max-w-6xl mx-auto mt-24 mb-20">
        <div className="flex flex-col md:flex-row items-end justify-between mb-12 gap-6">
          <div className="max-w-2xl">
            <h2 className="text-3xl font-bold text-foreground mb-4">Advanced Service Orchestration</h2>
            <p className="text-muted-foreground">
              Our platform utilizes a multi-layered AI pipeline where <strong>Whisper-v3 transcription</strong>, 
              <strong>Vision-LLM OCR</strong>, and <strong>Manim-based procedural animation</strong> converge. 
              Data flows seamlessly from raw input extraction to high-fidelity multimedia synthesis, 
              powered by state-of-the-art inference engines.
            </p>
          </div>
          <div className="px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-sm font-medium">
            Logical Flow Architecture
          </div>
        </div>
        
        <div className="glass rounded-3xl p-2 lg:p-4 overflow-hidden shadow-2xl shadow-blue-500/10 border border-white/10 group">
          <div className="relative aspect-[21/9] w-full rounded-2xl overflow-hidden bg-card/50 flex items-center justify-center">
            {/* 
              USER: Save your exported Eraser image as:
              /frontend/public/images/system-methodology.png
            */}
            <img 
              src="/images/system_methodology.png" 
              alt="System Methodology Diagram" 
              className="w-full h-full object-contain transition-transform duration-700 group-hover:scale-[1.02]"
              onError={(e) => {
                const target = e.currentTarget;
                target.style.display = 'none';
                if (target.parentElement) {
                  const placeholder = document.createElement('div');
                  placeholder.className = "flex flex-col items-center justify-center text-center p-12";
                  placeholder.innerHTML = `
                    <div class="w-16 h-16 rounded-full bg-blue-500/20 flex items-center justify-center mb-4">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-blue-500"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
                    </div>
                    <h3 class="text-xl font-semibold mb-2">Methodology Diagram Placeholder</h3>
                    <p class="text-muted-foreground max-w-md">Once you generate the diagram from Eraser, save it to <code>public/images/system_methodology.png</code> to see it here.</p>
                  `;
                  target.parentElement.appendChild(placeholder);
                }
              }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

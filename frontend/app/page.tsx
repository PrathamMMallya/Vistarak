"use client"

import { useState } from "react"
import Link from "next/link"
import { Video, FileText, BookOpen, Zap, Mic2, Calculator, Languages, Sparkles, ArrowRight, Film } from "lucide-react"
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
    id: "mathcompute",
    title: "Math Visualization",
    description: "Extract, convert, and visualize mathematical equations",
    icon: Calculator,
    color: "from-emerald-500 to-emerald-600",
    href: "/mathcompute",
  },
  {
    id: "manim-visualizer",
    title: "Manim Visualizer",
    description: "Create interactive mathematical and physical animations with AI",
    icon: Film,
    color: "from-orange-500 to-orange-600",
    href: "/manim-visualizer",
  },
]

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
    </div>
  )
}

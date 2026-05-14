"use client"

import { useState, useRef, useCallback } from "react"

import {
  Mic2,
  Play,
  Download,
  Upload,
  Sparkles,
  RefreshCw,
  Volume2,
  AlertCircle,
  CheckCircle2,
  X,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { SectionCard } from "@/components/shared/section-card"

// ─────────────────────────────────────────────────────────────
// Emotion metadata
// ─────────────────────────────────────────────────────────────

const EMOTION_META: Record<
  string,
  {
    color: string
    bg: string
    emoji: string
    label: string
  }
> = {
  happy: {
    color: "text-yellow-400",
    bg: "bg-yellow-400/10 border-yellow-400/30",
    emoji: "😄",
    label: "Happy",
  },

  excited: {
    color: "text-orange-400",
    bg: "bg-orange-400/10 border-orange-400/30",
    emoji: "🤩",
    label: "Excited",
  },

  sad: {
    color: "text-blue-400",
    bg: "bg-blue-400/10 border-blue-400/30",
    emoji: "😢",
    label: "Sad",
  },

  tense: {
    color: "text-red-400",
    bg: "bg-red-400/10 border-red-400/30",
    emoji: "😬",
    label: "Tense",
  },

  angry: {
    color: "text-red-500",
    bg: "bg-red-500/10 border-red-500/30",
    emoji: "😡",
    label: "Angry",
  },

  calm: {
    color: "text-teal-400",
    bg: "bg-teal-400/10 border-teal-400/30",
    emoji: "😌",
    label: "Calm",
  },

  reflective: {
    color: "text-purple-400",
    bg: "bg-purple-400/10 border-purple-400/30",
    emoji: "🤔",
    label: "Reflective",
  },

  surprised: {
    color: "text-pink-400",
    bg: "bg-pink-400/10 border-pink-400/30",
    emoji: "😮",
    label: "Surprised",
  },

  fearful: {
    color: "text-indigo-400",
    bg: "bg-indigo-400/10 border-indigo-400/30",
    emoji: "😨",
    label: "Fearful",
  },

  neutral: {
    color: "text-gray-400",
    bg: "bg-gray-400/10 border-gray-400/30",
    emoji: "😐",
    label: "Neutral",
  },
}

// ─────────────────────────────────────────────────────────────
// Emotion Badge
// ─────────────────────────────────────────────────────────────

function EmotionBadge({ emotion }: { emotion: string }) {
  const meta = EMOTION_META[emotion] ?? EMOTION_META.neutral

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-semibold ${meta.bg} ${meta.color}`}
    >
      <span>{meta.emoji}</span>
      <span>{meta.label}</span>
    </span>
  )
}

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────

interface Segment {
  text: string
  emotion: string
}

// ─────────────────────────────────────────────────────────────
// Waveform animation
// ─────────────────────────────────────────────────────────────

function WaveformBars({ active }: { active: boolean }) {
  return (
    <div className="flex items-center gap-0.5 h-6">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className={`w-1 rounded-full bg-accent transition-all ${
            active ? "animate-pulse" : "h-2"
          }`}
          style={
            active
              ? {
                  animationDelay: `${i * 80}ms`,
                  height: `${8 + (i % 3) * 6}px`,
                }
              : {}
          }
        />
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────

export default function TextToSpeech() {
  const [inputText, setInputText] = useState("")
  const [refAudio, setRefAudio] = useState<File | null>(null)
  const [refAudioName, setRefAudioName] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [segments] = useState<Segment[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)

  // ───────────────────────────────────────────────────────────
  // BACKEND URL
  // ───────────────────────────────────────────────────────────

  const BACKEND = "http://172.16.2.131:9055"
  // ───────────────────────────────────────────────────────────
  // Upload voice file
  // ───────────────────────────────────────────────────────────

  const handleFileUpload = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0]

    if (file) {
      setRefAudio(file)
      setRefAudioName(file.name)
    }
  }

  // ───────────────────────────────────────────────────────────
  // Remove uploaded file
  // ───────────────────────────────────────────────────────────

  const removeRefAudio = () => {
    setRefAudio(null)
    setRefAudioName("")

    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  // ───────────────────────────────────────────────────────────
  // Generate TTS
  // ───────────────────────────────────────────────────────────

  const handleGenerate = useCallback(async () => {

    if (!inputText.trim()) return

    setIsGenerating(true)
    setError(null)
    setAudioUrl(null)

    try {

      const formData = new FormData()

      formData.append("text", inputText)

      if (refAudio) {
        formData.append("ref_audio", refAudio)
      }

      const res = await fetch(
        `${BACKEND}/generate/`,
        {
          method: "POST",
          body: formData,
        }
      )

      if (!res.ok) {
        throw new Error("Generation failed")
      }

      // receive wav blob
      const blob = await res.blob()

      // create browser audio URL
      const audioObjectUrl = URL.createObjectURL(blob)

      setAudioUrl(audioObjectUrl)

    } catch (err: any) {

      console.error(err)

      setError(
        err.message || "Unexpected error"
      )

    } finally {

      setIsGenerating(false)

    }

  }, [inputText, refAudio])

  // ───────────────────────────────────────────────────────────
  // Download
  // ───────────────────────────────────────────────────────────

  const handleDownload = () => {

    if (!audioUrl) return

    const a = document.createElement("a")

    a.href = audioUrl

    a.download = "emotion_tts.wav"

    a.click()
  }

  // ───────────────────────────────────────────────────────────
  // Audio events
  // ───────────────────────────────────────────────────────────

  const handlePlay = () => setIsPlaying(true)

  const handlePause = () => setIsPlaying(false)

  const handleEnded = () => setIsPlaying(false)

  // ───────────────────────────────────────────────────────────
  // Stats
  // ───────────────────────────────────────────────────────────

  const charCount = inputText.length

  const wordCount = inputText.trim()
    ? inputText.trim().split(/\s+/).length
    : 0

  // ───────────────────────────────────────────────────────────
  // UI
  // ───────────────────────────────────────────────────────────

  return (
    <div className="p-6 lg:p-10 max-w-5xl mx-auto space-y-8">

      {/* Header */}

      <div className="relative">

        <div className="absolute inset-0 bg-gradient-to-r from-pink-500/15 to-purple-500/15 blur-3xl rounded-3xl pointer-events-none" />

        <div className="relative">

          <div className="flex items-center gap-3 mb-2">

            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center shadow-lg">

              <Mic2
                size={20}
                className="text-white"
              />

            </div>

            <h1 className="text-3xl font-bold text-foreground">
              Emotion TTS
            </h1>

          </div>

          <p className="text-muted-foreground ml-13 pl-1">
            AI-powered expressive speech generation using ChatterboxTurboTTS
          </p>

        </div>
      </div>

      {/* Input Text */}

      <SectionCard
        title="Text to Speak"
        description="Enter text and generate expressive emotional speech"
        icon={<Sparkles size={18} />}
      >

        <div className="space-y-3">

          <textarea
            className="
              w-full
              min-h-[140px]
              bg-input
              border
              border-border
              rounded-xl
              px-4
              py-3
              text-foreground
              placeholder:text-muted-foreground
              focus:outline-none
              focus:ring-2
              focus:ring-accent/50
              resize-y
              transition-all
              text-sm
              leading-relaxed
            "
            placeholder="Enter text here..."
            value={inputText}
            onChange={(e) =>
              setInputText(e.target.value)
            }
          />

          <div className="flex justify-between text-xs text-muted-foreground px-1">

            <span>{wordCount} words</span>

            <span>{charCount} characters</span>

          </div>

        </div>

      </SectionCard>

      {/* Voice Reference */}

      <SectionCard
        title="Voice Reference"
        description="Optional voice cloning reference"
        icon={<Volume2 size={18} />}
      >

        <div className="space-y-3">

          <Button
            onClick={() =>
              fileInputRef.current?.click()
            }
            variant="outline"
            className="w-full border-dashed border-2 hover:bg-card/60 h-14 gap-2"
          >

            <Upload size={18} />

            {refAudioName
              ? "Change Voice File"
              : "Upload Voice Reference"}

          </Button>

          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            onChange={handleFileUpload}
            className="hidden"
          />

          {refAudioName && (

            <div className="flex items-center justify-between p-3 bg-accent/10 border border-accent/30 rounded-lg">

              <div className="flex items-center gap-2 text-sm text-foreground">

                <CheckCircle2
                  size={16}
                  className="text-accent"
                />

                <span className="font-medium">
                  {refAudioName}
                </span>

              </div>

              <button
                onClick={removeRefAudio}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X size={16} />
              </button>

            </div>
          )}

        </div>

      </SectionCard>

      {/* Generate Button */}

      <div className="flex gap-4">

        <Button
          onClick={handleGenerate}
          disabled={
            !inputText.trim() ||
            isGenerating
          }
          className="
            flex-1
            h-12
            bg-gradient-to-r
            from-pink-500
            to-purple-600
            hover:from-pink-600
            hover:to-purple-700
            text-white
            font-semibold
            text-sm
            shadow-lg
            shadow-pink-500/20
            transition-all
            duration-300
          "
        >

          {isGenerating ? (
            <>
              <RefreshCw
                size={18}
                className="animate-spin"
              />
              Generating...
            </>
          ) : (
            <>
              <Play size={18} />
              Generate Speech
            </>
          )}

        </Button>

      </div>

      {/* Error */}

      {error && (

        <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">

          <AlertCircle
            size={18}
            className="shrink-0 mt-0.5"
          />

          <div>

            <p className="font-semibold">
              Generation failed
            </p>

            <p className="text-red-400/80 mt-0.5">
              {error}
            </p>

          </div>

        </div>
      )}

      {/* Audio Output */}

      {audioUrl && (

        <SectionCard title="Generated Audio">

          <div className="space-y-4">

            <div className="flex items-center gap-4 p-4 bg-card/60 rounded-xl border border-border">

              <WaveformBars
                active={isPlaying}
              />

              <div className="flex-1">

                <p className="text-sm font-medium text-foreground">
                  Emotion TTS Output
                </p>

              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                className="gap-2"
              >

                <Download size={15} />

                Download

              </Button>

            </div>

            <audio
              ref={audioRef}
              src={audioUrl}
              controls
              className="w-full rounded-lg"
              onPlay={handlePlay}
              onPause={handlePause}
              onEnded={handleEnded}
            />

          </div>

        </SectionCard>
      )}

      {/* Segments */}

      {segments.length > 0 && (

        <SectionCard
          title="Emotion Breakdown"
        >

          <div className="space-y-2">

            {segments.map((seg, i) => (

              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded-lg border"
              >

                <div className="flex-1">

                  <p className="text-sm text-foreground">

                    {seg.text}

                  </p>

                </div>

                <EmotionBadge
                  emotion={seg.emotion}
                />

              </div>
            ))}

          </div>

        </SectionCard>
      )}

    </div>
  )
}
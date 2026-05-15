"use client"

import { useState, useRef, useCallback, useEffect } from "react"

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
  Mic,
  Square,
  Trash2,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { SectionCard } from "@/components/shared/section-card"

// ─────────────────────────────────────────────────────────────
// Emotion metadata
// ─────────────────────────────────────────────────────────────

const EMOTION_META: Record<
  string,
  { color: string; bg: string; emoji: string; label: string }
> = {
  happy:      { color: "text-yellow-400", bg: "bg-yellow-400/10 border-yellow-400/30",  emoji: "😄", label: "Happy"      },
  excited:    { color: "text-orange-400", bg: "bg-orange-400/10 border-orange-400/30",  emoji: "🤩", label: "Excited"    },
  sad:        { color: "text-blue-400",   bg: "bg-blue-400/10 border-blue-400/30",      emoji: "😢", label: "Sad"        },
  tense:      { color: "text-red-400",    bg: "bg-red-400/10 border-red-400/30",        emoji: "😬", label: "Tense"      },
  angry:      { color: "text-red-500",    bg: "bg-red-500/10 border-red-500/30",        emoji: "😡", label: "Angry"      },
  calm:       { color: "text-teal-400",   bg: "bg-teal-400/10 border-teal-400/30",      emoji: "😌", label: "Calm"       },
  reflective: { color: "text-purple-400", bg: "bg-purple-400/10 border-purple-400/30",  emoji: "🤔", label: "Reflective" },
  surprised:  { color: "text-pink-400",   bg: "bg-pink-400/10 border-pink-400/30",      emoji: "😮", label: "Surprised"  },
  fearful:    { color: "text-indigo-400", bg: "bg-indigo-400/10 border-indigo-400/30",  emoji: "😨", label: "Fearful"    },
  neutral:    { color: "text-gray-400",   bg: "bg-gray-400/10 border-gray-400/30",      emoji: "😐", label: "Neutral"    },
}

function EmotionBadge({ emotion }: { emotion: string }) {
  const meta = EMOTION_META[emotion] ?? EMOTION_META.neutral
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-semibold ${meta.bg} ${meta.color}`}>
      <span>{meta.emoji}</span>
      <span>{meta.label}</span>
    </span>
  )
}

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
          className={`w-1 rounded-full bg-accent transition-all ${active ? "animate-pulse" : "h-2"}`}
          style={active ? { animationDelay: `${i * 80}ms`, height: `${8 + (i % 3) * 6}px` } : {}}
        />
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Recording timer display
// ─────────────────────────────────────────────────────────────

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60).toString().padStart(2, "0")
  const s = (seconds % 60).toString().padStart(2, "0")
  return `${m}:${s}`
}

// ─────────────────────────────────────────────────────────────
// Live mic waveform bars (uses analyser data)
// ─────────────────────────────────────────────────────────────

function LiveWaveform({ analyserRef, isRecording }: { analyserRef: React.RefObject<AnalyserNode | null>; isRecording: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")!

    const draw = () => {
      const analyser = analyserRef.current
      if (!analyser || !isRecording) {
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        // draw flat idle line
        ctx.strokeStyle = "rgba(168,85,247,0.3)"
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(0, canvas.height / 2)
        ctx.lineTo(canvas.width, canvas.height / 2)
        ctx.stroke()
        return
      }

      const bufferLength = analyser.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)
      analyser.getByteTimeDomainData(dataArray)

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.lineWidth = 2
      ctx.strokeStyle = "rgba(236,72,153,0.9)" // pink-500
      ctx.beginPath()

      const sliceWidth = canvas.width / bufferLength
      let x = 0
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0
        const y = (v * canvas.height) / 2
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        x += sliceWidth
      }
      ctx.lineTo(canvas.width, canvas.height / 2)
      ctx.stroke()

      rafRef.current = requestAnimationFrame(draw)
    }

    rafRef.current = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(rafRef.current)
  }, [isRecording, analyserRef])

  return (
    <canvas
      ref={canvasRef}
      width={320}
      height={48}
      className="w-full rounded-lg bg-card/40"
    />
  )
}

// ─────────────────────────────────────────────────────────────
// Voice Reference tabs: Record | Upload
// ─────────────────────────────────────────────────────────────

type VoiceTab = "record" | "upload"

interface VoiceReferenceProps {
  refAudio: File | null
  refAudioName: string
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void
  onRemove: () => void
  onRecordingComplete: (file: File) => void
}

function VoiceReferenceSection({
  refAudio,
  refAudioName,
  onFileUpload,
  onRemove,
  onRecordingComplete,
}: VoiceReferenceProps) {
  const [tab, setTab] = useState<VoiceTab>("record")

  // ── Recorder state ──────────────────────────────────────────
  const [isRecording, setIsRecording] = useState(false)
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null)
  const [recordedUrl, setRecordedUrl] = useState<string | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [micError, setMicError] = useState<string | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      streamRef.current?.getTracks().forEach((t) => t.stop())
    }
  }, [])

  const startRecording = async () => {
    setMicError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      // Set up analyser for live waveform
      const audioCtx = new AudioContext()
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 1024
      source.connect(analyser)
      analyserRef.current = analyser

      const mr = new MediaRecorder(stream)
      mediaRecorderRef.current = mr
      chunksRef.current = []

      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" })
        const url = URL.createObjectURL(blob)
        setRecordedBlob(blob)
        setRecordedUrl(url)
        // Convert to File and hand up
        const file = new File([blob], "recorded_voice.webm", { type: "audio/webm" })
        onRecordingComplete(file)
        stream.getTracks().forEach((t) => t.stop())
        analyserRef.current = null
      }

      mr.start()
      setIsRecording(true)
      setElapsed(0)
      setRecordedBlob(null)
      setRecordedUrl(null)

      timerRef.current = setInterval(() => {
        setElapsed((prev) => prev + 1)
      }, 1000)
    } catch (err: any) {
      setMicError("Microphone access denied. Please allow mic permissions.")
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  const discardRecording = () => {
    setRecordedBlob(null)
    setRecordedUrl(null)
    setElapsed(0)
    onRemove()
  }

  // ── Render ──────────────────────────────────────────────────
  return (
    <SectionCard
      title="Voice Reference"
      description="Clone a voice by recording or uploading a sample"
      icon={<Volume2 size={18} />}
    >
      {/* Tab switcher */}
      <div className="flex gap-1 p-1 bg-card/60 rounded-xl border border-border w-fit mb-4">
        {(["record", "upload"] as VoiceTab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`
              flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium transition-all
              ${tab === t
                ? "bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow"
                : "text-muted-foreground hover:text-foreground"
              }
            `}
          >
            {t === "record" ? <Mic size={14} /> : <Upload size={14} />}
            {t === "record" ? "Record" : "Upload"}
          </button>
        ))}
      </div>

      {/* ── RECORD TAB ── */}
      {tab === "record" && (
        <div className="space-y-3">
          {micError && (
            <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
              <AlertCircle size={15} className="shrink-0" />
              {micError}
            </div>
          )}

          {/* Waveform canvas */}
          <LiveWaveform analyserRef={analyserRef} isRecording={isRecording} />

          {/* Timer */}
          <div className="flex items-center justify-between px-1">
            <span className={`text-sm font-mono font-semibold ${isRecording ? "text-pink-400" : "text-muted-foreground"}`}>
              {isRecording && (
                <span className="inline-block w-2 h-2 rounded-full bg-red-500 animate-pulse mr-2 align-middle" />
              )}
              {formatTime(elapsed)}
            </span>
            <span className="text-xs text-muted-foreground">
              {isRecording ? "Recording…" : recordedBlob ? "Recording saved" : "Ready to record"}
            </span>
          </div>

          {/* Controls */}
          <div className="flex gap-2">
            {!isRecording ? (
              <Button
                onClick={startRecording}
                disabled={!!recordedBlob}
                className="flex-1 h-11 bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white font-semibold gap-2 shadow shadow-pink-500/20"
              >
                <Mic size={16} />
                {recordedBlob ? "Recorded ✓" : "Start Recording"}
              </Button>
            ) : (
              <Button
                onClick={stopRecording}
                className="flex-1 h-11 bg-red-500 hover:bg-red-600 text-white font-semibold gap-2"
              >
                <Square size={14} fill="white" />
                Stop Recording
              </Button>
            )}

            {recordedBlob && !isRecording && (
              <Button
                onClick={discardRecording}
                variant="outline"
                size="icon"
                className="h-11 w-11 shrink-0 text-muted-foreground hover:text-red-400 hover:border-red-400/40"
                title="Discard recording"
              >
                <Trash2 size={15} />
              </Button>
            )}
          </div>

          {/* Playback of recording */}
          {recordedUrl && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground px-1">Preview recording</p>
              <audio src={recordedUrl} controls className="w-full rounded-lg h-10" />
            </div>
          )}
        </div>
      )}

      {/* ── UPLOAD TAB ── */}
      {tab === "upload" && (
        <div className="space-y-3">
          <Button
            onClick={() => fileInputRef.current?.click()}
            variant="outline"
            className="w-full border-dashed border-2 hover:bg-card/60 h-14 gap-2"
          >
            <Upload size={18} />
            {refAudioName && refAudio ? "Change Voice File" : "Upload Voice Reference"}
          </Button>

          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            onChange={onFileUpload}
            className="hidden"
          />

          {refAudioName && refAudio && (
            <div className="flex items-center justify-between p-3 bg-accent/10 border border-accent/30 rounded-lg">
              <div className="flex items-center gap-2 text-sm text-foreground">
                <CheckCircle2 size={16} className="text-accent" />
                <span className="font-medium">{refAudioName}</span>
              </div>
              <button
                onClick={onRemove}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X size={16} />
              </button>
            </div>
          )}
        </div>
      )}
    </SectionCard>
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

  const audioRef = useRef<HTMLAudioElement>(null)

  const BACKEND = "http://localhost:8000/modules/tts"

  // ── File upload handler ──────────────────────────────────────
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setRefAudio(file)
      setRefAudioName(file.name)
    }
  }

  // ── Recording complete handler ───────────────────────────────
  const handleRecordingComplete = (file: File) => {
    setRefAudio(file)
    setRefAudioName(file.name)
  }

  // ── Remove ref audio ────────────────────────────────────────
  const removeRefAudio = () => {
    setRefAudio(null)
    setRefAudioName("")
  }

  // ── Generate TTS ─────────────────────────────────────────────
  const handleGenerate = useCallback(async () => {
    if (!inputText.trim()) return
    setIsGenerating(true)
    setError(null)
    setAudioUrl(null)

    try {
      const formData = new FormData()
      formData.append("text", inputText)
      if (refAudio) formData.append("ref_audio", refAudio)

      const res = await fetch(`${BACKEND}/generate/`, { method: "POST", body: formData })
      if (!res.ok) throw new Error("Generation failed")

      const blob = await res.blob()
      setAudioUrl(URL.createObjectURL(blob))
    } catch (err: any) {
      setError(err.message || "Unexpected error")
    } finally {
      setIsGenerating(false)
    }
  }, [inputText, refAudio])

  // ── Download ─────────────────────────────────────────────────
  const handleDownload = () => {
    if (!audioUrl) return
    const a = document.createElement("a")
    a.href = audioUrl
    a.download = "emotion_tts.wav"
    a.click()
  }

  const charCount = inputText.length
  const wordCount = inputText.trim() ? inputText.trim().split(/\s+/).length : 0

  // ── UI ───────────────────────────────────────────────────────
  return (
    <div className="p-6 lg:p-10 max-w-5xl mx-auto space-y-8">

      {/* Header */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-pink-500/15 to-purple-500/15 blur-3xl rounded-3xl pointer-events-none" />
        <div className="relative">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center shadow-lg">
              <Mic2 size={20} className="text-white" />
            </div>
            <h1 className="text-3xl font-bold text-foreground">Emotion TTS</h1>
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
            className="w-full min-h-[140px] bg-input border border-border rounded-xl px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/50 resize-y transition-all text-sm leading-relaxed"
            placeholder="Enter text here..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />
          <div className="flex justify-between text-xs text-muted-foreground px-1">
            <span>{wordCount} words</span>
            <span>{charCount} characters</span>
          </div>
        </div>
      </SectionCard>

      {/* Voice Reference — Record or Upload */}
      <VoiceReferenceSection
        refAudio={refAudio}
        refAudioName={refAudioName}
        onFileUpload={handleFileUpload}
        onRemove={removeRefAudio}
        onRecordingComplete={handleRecordingComplete}
      />

      {/* Generate Button */}
      <div className="flex gap-4">
        <Button
          onClick={handleGenerate}
          disabled={!inputText.trim() || isGenerating}
          className="flex-1 h-12 bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white font-semibold text-sm shadow-lg shadow-pink-500/20 transition-all duration-300"
        >
          {isGenerating ? (
            <><RefreshCw size={18} className="animate-spin" /> Generating...</>
          ) : (
            <><Play size={18} /> Generate Speech</>
          )}
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">
          <AlertCircle size={18} className="shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Generation failed</p>
            <p className="text-red-400/80 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Audio Output */}
      {audioUrl && (
        <SectionCard title="Generated Audio">
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-4 bg-card/60 rounded-xl border border-border">
              <WaveformBars active={isPlaying} />
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">Emotion TTS Output</p>
              </div>
              <Button variant="outline" size="sm" onClick={handleDownload} className="gap-2">
                <Download size={15} /> Download
              </Button>
            </div>
            <audio
              ref={audioRef}
              src={audioUrl}
              controls
              className="w-full rounded-lg"
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onEnded={() => setIsPlaying(false)}
            />
          </div>
        </SectionCard>
      )}

      {/* Segments */}
      {segments.length > 0 && (
        <SectionCard title="Emotion Breakdown">
          <div className="space-y-2">
            {segments.map((seg, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg border">
                <div className="flex-1">
                  <p className="text-sm text-foreground">{seg.text}</p>
                </div>
                <EmotionBadge emotion={seg.emotion} />
              </div>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  )
}
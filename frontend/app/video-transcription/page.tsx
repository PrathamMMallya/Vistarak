"use client"

import { useState } from "react"
import { Upload, Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { FileUploader } from "@/components/shared/file-uploader"
import { LanguageSelector } from "@/components/shared/language-selector"
import { TextEditor } from "@/components/shared/text-editor"
import { SectionCard } from "@/components/shared/section-card"

// Only allowed languages for NLLB translation
const LANG_MAP: Record<string, string> = {
  en: "en",
  hi: "hi",
  kn: "kn",
  ta: "ta",
  te: "te",
  ml: "ml",
  bn: "bn",
}

export default function VideoTranscription() {
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [transcript, setTranscript] = useState("")
  const [audioLanguage, setAudioLanguage] = useState("auto") // auto for STT
  const [targetLanguage, setTargetLanguage] = useState("hi")
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [isTranslating, setIsTranslating] = useState(false)

  // -----------------------
  // Handle video selection
  // -----------------------
  const handleFileSelect = (files: File[]) => {
    if (files[0]) setVideoFile(files[0])
  }

  // -----------------------
  // Transcribe video
  // -----------------------
  const handleTranscribe = async () => {
    if (!videoFile) return
    setIsTranscribing(true)
    setTranscript("")

    const formData = new FormData()
    formData.append("video_file", videoFile)
    formData.append("source_lan", audioLanguage) // "auto"

    try {
      const response = await fetch(
        "http://localhost:8000/modules/video_transcribe/",
        { method: "POST", body: formData }
      )

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Transcription failed: ${response.status} - ${errorText}`)
      }

      const data = await response.json()
      setTranscript(data.only_transcript || data.transcript || "")
    } catch (error) {
      console.error(error)
      setTranscript(`Error: ${error instanceof Error ? error.message : "Failed to transcribe"}`)
    } finally {
      setIsTranscribing(false)
    }
  }

  // -----------------------
  // Translate transcript
  // -----------------------
  const handleTranslate = async () => {
    if (!transcript.trim()) {
      alert("Nothing to translate")
      return
    }

    const target_lan = LANG_MAP[targetLanguage]
    if (!target_lan) {
      alert("Invalid target language")
      return
    }

    setIsTranslating(true)

    const data = new FormData()
    data.append("target_lan", targetLanguage)
    data.append("text", transcript)

    try {
      const response = await fetch("http://localhost:8000/translate/nllb/", {
        method: "POST",
        body: data,
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || "Translation failed")
      }

      const res = await response.json()

      if (res.status === "success") {
        // ✅ Use translated_text from backend
        setTranscript(res.translated_text || "")
      } else {
        alert("Translation error: " + (res.error || "unknown"))
      }
    } catch (err) {
      console.error(err)
      alert("Translation failed: " + (err instanceof Error ? err.message : "Unknown error"))
    } finally {
      setIsTranslating(false)
    }
  }

  // -----------------------
  // Download transcript
  // -----------------------
  const downloadTranscript = (format: "txt" | "docx") => {
    if (!transcript) return
    const element = document.createElement("a")
    const file = new Blob([transcript], { type: "text/plain" })
    element.href = URL.createObjectURL(file)
    element.download = `transcript.${format}`
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
    URL.revokeObjectURL(element.href)
  }

  return (
    <div className="p-6 lg:p-12 max-w-6xl mx-auto space-y-8">
      <h1 className="text-4xl font-bold">Video Transcription</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <SectionCard title="Upload Video" description="Drag and drop or click">
          <FileUploader accept="video/*" onFileSelect={handleFileSelect} />
          {videoFile && <p>Ready to transcribe: {videoFile.name}</p>}
        </SectionCard>

        <SectionCard title="Transcript" description="Edit transcript">
          <TextEditor value={transcript} onChange={setTranscript} placeholder="Transcription appears here..." />
        </SectionCard>
      </div>

      <SectionCard title="Translate Transcript">
        <LanguageSelector label="Audio Language" value={audioLanguage} onSelect={setAudioLanguage} />
        <LanguageSelector label="Target Language" value={targetLanguage} onSelect={setTargetLanguage} />
        <Button onClick={handleTranslate} disabled={!transcript || isTranslating}>
          {isTranslating ? "Translating..." : "Translate Transcript"}
        </Button>
      </SectionCard>

      <div className="flex gap-4">
        <Button onClick={handleTranscribe} disabled={!videoFile || isTranscribing}>
          {isTranscribing ? "Transcribing..." : "Transcribe Video"}
        </Button>
        <Button onClick={() => downloadTranscript("txt")} disabled={!transcript}>Download TXT</Button>
        <Button onClick={() => downloadTranscript("docx")} disabled={!transcript}>Download DOCX</Button>
      </div>
    </div>
  )
}

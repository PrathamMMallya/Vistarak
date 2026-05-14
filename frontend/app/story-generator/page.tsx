"use client"

import { useState } from "react"
import { Sparkles, Video, Play, Type, Send, RefreshCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function StoryGenerator() {
  const [description, setDescription] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [videoUrl, setVideoUrl] = useState("http://localhost:8000/story/preview/")

  const handleGenerate = async () => {
    if (!description.trim()) return
    setIsGenerating(true)
    
    try {
      const response = await fetch("http://localhost:8000/story/generate/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description })
      })
      const data = await response.json()
      if (data.video_url) {
        // Append a timestamp to bypass caching if needed
        setVideoUrl(`${data.video_url}?t=${Date.now()}`)
      }
    } catch (error) {
      console.error("Failed to generate story:", error)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl min-h-screen bg-background text-foreground">
      <div className="flex flex-col gap-8">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-primary/10 rounded-xl border border-primary/20">
            <Video className="w-8 h-8 text-primary" />
          </div>
          <div>
            <h1 className="text-4xl font-bold tracking-tight">
              Story Video Generator
            </h1>
            <p className="text-muted-foreground mt-1">Transform your narratives into cinematic visualizations</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Input Panel */}
          <Card className="lg:col-span-5 bg-card border-border shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl">
                <Type className="w-5 h-5 text-blue-500" />
                Story Description
              </CardTitle>
              <CardDescription>
                Describe the characters, setting, and plot points of your story.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <Textarea
                placeholder="Once upon a time in a digital kingdom..."
                className="min-h-[400px] bg-background border-input text-lg resize-none focus-visible:ring-primary transition-all"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
              <Button
                className="w-full h-14 text-lg font-semibold bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg transition-all active:scale-[0.98]"
                onClick={handleGenerate}
                disabled={isGenerating || !description.trim()}
              >
                {isGenerating ? (
                  <span className="flex items-center gap-2">
                    <RefreshCcw className="animate-spin w-5 h-5" />
                    Generating Magic...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Send className="w-5 h-5" />
                    Generate Story
                  </span>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Preview Panel */}
          <Card className="lg:col-span-7 bg-card border-border shadow-lg overflow-hidden flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <div className="space-y-1">
                <CardTitle className="text-xl flex items-center gap-2">
                  <Play className="w-5 h-5 text-emerald-500" />
                  Preview
                </CardTitle>
                <CardDescription>Real-time cinematic rendering</CardDescription>
              </div>
              <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 px-3 py-1">
                Live Preview
              </Badge>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <div className="flex-1 min-h-[400px] bg-black rounded-xl border border-border overflow-hidden relative group">
                <video 
                  key={videoUrl}
                  controls 
                  className="w-full h-full object-contain"
                  poster="/placeholder-video.jpg"
                >
                  <source src={videoUrl} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              </div>
              
              <div className="mt-6 p-4 rounded-lg bg-primary/5 border border-primary/10">
                <p className="text-sm text-center text-primary/80 font-medium italic">
                  "Visualizing the journey of your narrative..."
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

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
  const [status, setStatus] = useState("")
  const [videoUrl, setVideoUrl] = useState("")

  const handleGenerate = async () => {
    if (!description.trim()) return
    setIsGenerating(true)
    setStatus("Connecting to story engine...")
    setVideoUrl("")
    
    try {
      // 1. Get backend configuration
      const configRes = await fetch("http://localhost:8000/story/config/")
      const { server_url, ws_url } = await configRes.json()

      // 2. Establish WebSocket connection
      const ws = new WebSocket(ws_url)

      ws.onopen = () => {
        console.log("Connected to Story WS")
        ws.send(JSON.stringify({ prompt: description }))
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log("WS Update:", data)

          if (data.status === "done") {
            const videoId = data.message
            setVideoUrl(`${server_url}/video/${videoId}`)
            setStatus("Success! Video generated.")
            setIsGenerating(false)
            ws.close()
          } else {
            setStatus(data.status || "Processing...")
          }
        } catch (e) {
          console.error("Failed to parse WS message:", e)
        }
      }

      ws.onerror = (error) => {
        console.error("WS Error:", error)
        setStatus("Connection failed. Please check the server.")
        setIsGenerating(false)
      }

      ws.onclose = () => {
        console.log("WS Connection closed")
      }

    } catch (error) {
      console.error("Failed to initiate story generation:", error)
      setStatus("Error: Could not reach the server.")
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
              <div className="flex-1 min-h-[400px] bg-black rounded-xl border border-border overflow-hidden relative group flex items-center justify-center">
                {videoUrl ? (
                  <video 
                    key={videoUrl}
                    controls 
                    autoPlay
                    className="w-full h-full object-contain shadow-2xl"
                  >
                    <source src={videoUrl} type="video/mp4" />
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center bg-slate-950/50 backdrop-blur-sm">
                    {isGenerating ? (
                      <div className="flex flex-col items-center gap-6 p-8">
                        <div className="relative">
                          <div className="w-20 h-20 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                          <Sparkles className="absolute inset-0 m-auto w-8 h-8 text-primary animate-pulse" />
                        </div>
                        <div className="space-y-2 text-center">
                          <p className="text-primary font-bold text-lg animate-pulse">Mastering Your Story...</p>
                          <p className="text-muted-foreground text-sm max-w-[200px]">{status}</p>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center p-12 transition-all duration-500 group-hover:scale-105">
                        <div className="w-20 h-20 rounded-full bg-primary/5 flex items-center justify-center mx-auto mb-6 border border-primary/10">
                          <Video className="w-10 h-10 text-muted-foreground/30" />
                        </div>
                        <h3 className="text-foreground/60 font-semibold text-lg mb-2">No Video Generated</h3>
                        <p className="text-muted-foreground/50 max-w-[240px] text-sm mx-auto">
                          Enter a description on the left and click generate to begin your cinematic journey.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              <div className="mt-6 p-4 rounded-lg bg-primary/5 border border-primary/10">
                <p className="text-sm text-center text-primary/80 font-medium italic">
                  {status || "Waiting for your narrative journey to begin..."}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

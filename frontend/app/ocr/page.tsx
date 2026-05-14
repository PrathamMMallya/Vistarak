"use client"

import { useState, useEffect, useRef } from "react"
import { BookOpen, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { FileUploader } from "@/components/shared/file-uploader"
import { SectionCard } from "@/components/shared/section-card"

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'math-field': any;
    }
  }
}

export default function OCR() {
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [latexOutput, setLatexOutput] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState("")
  const mathFieldRef = useRef<any>(null)

  useEffect(() => {
    // Import MathLive dynamically
    import('mathlive').then((mathlive) => {
      mathlive.MathfieldElement.fontsDirectory = '/mathcompute/libs/fonts';
      if (mathFieldRef.current && latexOutput) {
        mathFieldRef.current.value = latexOutput
        
        mathFieldRef.current.addEventListener('input', (evt: any) => {
          setLatexOutput(evt.target.value)
        })
      }
    })
  }, [latexOutput])

  const handleFileSelect = (files: File[]) => {
    if (files[0]) {
      setImageFile(files[0])
      setError("")
    }
  }

  const handleOCR = async () => {
    if (!imageFile) return
    
    setIsProcessing(true)
    setError("")
    
    try {
      const formData = new FormData()
      formData.append('file', imageFile)
      
      const response = await fetch("http://localhost:8000/mathocr/latex/", {
        method: "POST",
        body: formData,
      })
      
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.success && data.latex) {
        setLatexOutput(data.latex)
      } else if (data.error) {
        setError(data.error)
      } else {
        setError("No LaTeX output received")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process image")
      console.error("OCR Error:", err)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="p-6 lg:p-12 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-foreground mb-2">Math OCR to LaTeX</h1>
        <p className="text-muted-foreground">Upload handwritten math and convert to editable LaTeX</p>
      </div>

      {/* Upload Section */}
      <SectionCard
        title="Upload Math Image"
        description="Drag and drop or click to browse"
        icon={<BookOpen size={20} />}
      >
        <FileUploader accept="image/*" onFileSelect={handleFileSelect} />
        
        {imageFile && (
          <div className="mt-4 space-y-2">
            <p className="text-sm text-muted-foreground">
              Selected: {imageFile.name}
            </p>
            <Button 
              onClick={handleOCR} 
              disabled={isProcessing} 
              className="w-full bg-accent hover:bg-accent/90"
            >
              {isProcessing ? (
                <div className="flex items-center gap-2">
                  <div className="animate-spin">
                    <Zap size={18} />
                  </div>
                  Processing...
                </div>
              ) : (
                "Convert to LaTeX"
              )}
            </Button>
          </div>
        )}
        
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-600 text-sm">
            {error}
          </div>
        )}
      </SectionCard>

      {/* Editor and LaTeX Output */}
      {latexOutput && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Math Editor Section */}
          <SectionCard
            title="Math Editor"
            description="Edit and preview your mathematical expression"
          >
            <div className="space-y-4">
              <math-field
                ref={mathFieldRef}
                virtual-keyboard-mode="auto"
                smart-fence
                style={{
                  fontSize: '20px',
                  padding: '16px',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                  width: '100%',
                  minHeight: '200px',
                  backgroundColor: 'hsl(var(--background))',
                  color: 'white'
                }}
              />
            </div>
          </SectionCard>

          {/* LaTeX Output */}
          <SectionCard
            title="LaTeX Code"
            description="Generated LaTeX from your image"
            icon={<BookOpen size={20} />}
          >
            <textarea
              value={latexOutput}
              onChange={(e) => setLatexOutput(e.target.value)}
              className="w-full min-h-[200px] p-3 bg-muted border border-border rounded-md font-mono text-sm"
              placeholder="LaTeX output will appear here..."
            />
          </SectionCard>
        </div>
      )}
    </div>
  )
}
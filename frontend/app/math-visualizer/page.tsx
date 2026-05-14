"use client"
import { useState, useEffect } from "react"
import dynamic from "next/dynamic"
import { Plus, SlidersHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { TextEditor } from "@/components/shared/text-editor"
import { SectionCard } from "@/components/shared/section-card"

// Dynamically import Plotly to disable SSR
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false })

interface Equation {
  latex: string
  id: string
}

export default function MathVisualizer() {
  const [equations, setEquations] = useState<Equation[]>([])
  const [latexInput, setLatexInput] = useState("")
  const [parameter, setParameter] = useState(1) // Example parameter a*x^2
  const [plotData, setPlotData] = useState<any[]>([])

  // Add equation
  const addEquation = () => {
    if (!latexInput.trim()) return
    const eq: Equation = { latex: latexInput.trim(), id: Date.now().toString() }
    setEquations([...equations, eq])
    setLatexInput("")
  }

  // Generate x and y values for plotting
  const generatePlotData = () => {
    const x = Array.from({ length: 101 }, (_, i) => -5 + i * 0.1) // -5 to 5
    const newData = equations.map((eq) => {
      let y: number[] = []

      try {
        // simple parser: replace 'x' and 'a' for slider param
        const fnStr = eq.latex.replaceAll("^", "**").replaceAll("a", parameter.toString())
        y = x.map((xi) => eval(fnStr.replaceAll("x", `(${xi})`)))
      } catch (e) {
        y = x.map(() => 0)
      }

      return {
        x,
        y,
        type: "scatter",
        mode: "lines+markers",
        name: eq.latex,
      }
    })
    setPlotData(newData)
  }

  // Update plot whenever equations or parameter change
  useEffect(() => {
    generatePlotData()
  }, [equations, parameter])

  return (
    <div className="p-6 lg:p-12 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-4xl font-bold">Math Visualizer</h1>
        <p className="text-muted-foreground">Enter equations in JS/LaTeX format (e.g., y=x^2, y=a*x^3)</p>
      </div>

      <SectionCard title="Add Equation">
        <div className="space-y-3">
          <TextEditor
            value={latexInput}
            onChange={setLatexInput}
            placeholder="Enter equation (e.g., x**2, a*x**3)"
          />
          <div className="flex gap-2">
            <Button onClick={addEquation} className="bg-accent hover:bg-accent/90">
              <Plus size={18} /> Add Equation
            </Button>
            <div className="flex items-center gap-2">
              <SlidersHorizontal size={18} />
              <input
                type="range"
                min="1"
                max="10"
                value={parameter}
                onChange={(e) => setParameter(Number(e.target.value))}
                className="w-48"
              />
              <span className="ml-2">{parameter}</span>
            </div>
          </div>
        </div>
      </SectionCard>

      {equations.length > 0 && (
        <SectionCard title="Equations List">
          <ul className="list-disc list-inside">
            {equations.map((eq) => (
              <li key={eq.id} className="font-mono text-sm">{eq.latex}</li>
            ))}
          </ul>
        </SectionCard>
      )}

      <SectionCard title="Graph Visualization">
        <Plot
          data={plotData}
          layout={{
            width: 800,
            height: 500,
            title: "2D Graph",
            xaxis: { title: "x" },
            yaxis: { title: "y" },
          }}
        />
      </SectionCard>
    </div>
  )
}

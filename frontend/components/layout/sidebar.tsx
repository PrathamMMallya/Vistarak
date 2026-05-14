"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { FileText, Languages, Video, BookOpen, Zap, Mic2, Calculator, Settings, Home, Film } from "lucide-react"

const navItems = [
  { icon: Home, label: "Dashboard", href: "/" },
  { icon: Video, label: "Video Transcription", href: "/video-transcription" },
  { icon: BookOpen, label: "OCR", href: "/ocr" },
  { icon: Mic2, label: "Text-to-Speech", href: "/tts" },
  { icon: Calculator, label: "Math Visualizer", href: "/math-visualizer" },
  { icon: Settings, label: "Settings", href: "/settings" },
]

export function Sidebar() {
  const [open, setOpen] = useState(false)
  const pathname = usePathname()

  return (
    <>
      <div
        className={`fixed left-0 top-16 h-[calc(100vh-4rem)] bg-sidebar border-r border-sidebar-border transition-all duration-300 z-40 ${
          open ? "w-64" : "-translate-x-full"
        } overflow-y-auto`}
      >
        <div className="p-4 border-b border-sidebar-border">
          <h2 className="text-sm font-semibold text-sidebar-foreground uppercase tracking-wide">Menu</h2>
        </div>

        <nav className="p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/10"
                }`}
              >
                <Icon size={18} />
                <span className="text-sm font-medium">{item.label}</span>
              </Link>
            )
          })}
        </nav>
      </div>

      {open && <div className="fixed inset-0 bg-black/50 z-30" onClick={() => setOpen(false)} />}

      <SidebarContext.Provider value={{ open, setOpen }}>
        <></>
      </SidebarContext.Provider>
    </>
  )
}

import { createContext, useContext } from "react"

export const SidebarContext = createContext<{
  open: boolean
  setOpen: (open: boolean) => void
} | null>(null)

export function useSidebar() {
  const context = useContext(SidebarContext)
  if (!context) {
    throw new Error("useSidebar must be used within SidebarProvider")
  }
  return context
}

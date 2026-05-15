"use client"

import { 
  Bell, User, Search, Menu, 
  FileText, Languages, Mic, Settings, LayoutDashboard, Film 
} from "lucide-react"
import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"

export function Navbar() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pathname = usePathname()

  const navItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/" },
    { icon: FileText, label: "Video Transcription", href: "/video-transcription" },
    { icon: Languages, label: "OCR", href: "/ocr" },
    { icon: Mic, label: "Text-to-Speech", href: "/tts" },

    { icon: Film, label: "Manim Visualizer", href: "/manim-visualizer" },
    { icon: Film, label: "Story Generator", href: "/story-generator" },
    { icon: Settings, label: "Settings", href: "/settings" },
  ]

  return (
    <div className="h-16 border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-40">
      <div className="h-full px-6 flex items-center justify-between">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 hover:bg-card rounded-lg transition-colors mr-4"
          aria-label="Toggle menu"
        >
          <Menu size={20} />
        </button>

        <div className="flex-1 flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 bg-input rounded-lg px-3 py-2 flex-1 max-w-md">
            <Search size={18} className="text-muted-foreground" />
            <input
              type="text"
              placeholder="Search modules..."
              className="bg-transparent outline-none text-sm flex-1 placeholder-muted-foreground"
            />
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-card rounded-lg transition-colors relative">
            <Bell size={18} />
            <span className="absolute top-1 right-1 w-2 h-2 bg-accent rounded-full" />
          </button>
          <button className="p-2 hover:bg-card rounded-lg transition-colors">
            <User size={18} />
          </button>
        </div>
      </div>

      {sidebarOpen && (
        <div
          className={`fixed left-0 top-16 h-[calc(100vh-4rem)] bg-sidebar border-r border-sidebar-border transition-all duration-300 z-40 w-64 overflow-y-auto`}
        >
          <nav className="p-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
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
      )}

      {sidebarOpen && <div className="fixed inset-0 bg-black/50 z-30" onClick={() => setSidebarOpen(false)} />}
    </div>
  )
}

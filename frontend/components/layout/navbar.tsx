"use client"

import { Bell, User, Search, Menu } from "lucide-react"
import { useSidebar } from "@/components/layout/sidebar"

export function Navbar() {
  const { open, setOpen } = useSidebar()

  return (
    <div className="h-16 border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-40">
      <div className="h-full px-6 flex items-center justify-between">
        <button
          onClick={() => setOpen(!open)}
          className="p-2 hover:bg-card rounded-lg transition-colors mr-4 md:hidden"
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
    </div>
  )
}

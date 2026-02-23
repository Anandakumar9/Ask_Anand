'use client'

import { useThemeStore } from '@/store/themeStore'
import { Moon, Sun } from 'lucide-react'

export default function DarkModeToggle() {
  const { isDarkMode, toggleDarkMode } = useThemeStore()

  return (
    <button
      onClick={toggleDarkMode}
      className="p-2 rounded-full transition-all duration-300 hover:scale-110"
      style={{
        backgroundColor: isDarkMode ? '#374151' : '#F3F4F6',
      }}
      aria-label="Toggle dark mode"
    >
      {isDarkMode ? (
        <Sun className="w-5 h-5 text-yellow-400" />
      ) : (
        <Moon className="w-5 h-5 text-gray-600" />
      )}
    </button>
  )
}

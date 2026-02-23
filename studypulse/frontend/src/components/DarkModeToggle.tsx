'use client'

import { useThemeStore } from '@/store/themeStore'
import { Moon, Sun } from 'lucide-react'

export default function DarkModeToggle() {
  const { isDarkMode, toggleDarkMode } = useThemeStore()

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        onClick={toggleDarkMode}
        className="relative w-14 h-8 rounded-full transition-all duration-300 border-2 focus:outline-none focus:ring-2 focus:ring-instacart-green focus:ring-offset-2"
        style={{
          backgroundColor: isDarkMode ? '#374151' : '#F3F4F6',
          borderColor: isDarkMode ? '#8B5CF6' : '#43B02A',
        }}
        aria-label="Toggle dark mode"
      >
        {/* Sliding circle with icon */}
        <div
          className={`absolute top-0.5 w-6 h-6 rounded-full bg-white shadow-md flex items-center justify-center transition-all duration-300 ease-in-out ${
            isDarkMode ? 'left-[calc(100%-26px)]' : 'left-0.5'
          }`}
        >
          {isDarkMode ? (
            <Moon className="w-3.5 h-3.5 text-instacart-purple" />
          ) : (
            <Sun className="w-3.5 h-3.5 text-yellow-500" />
          )}
        </div>
      </button>
      <span 
        className="text-[10px] font-semibold transition-colors duration-300"
        style={{ color: isDarkMode ? '#9CA3AF' : '#767676' }}
      >
        Dark Mode
      </span>
    </div>
  )
}
 

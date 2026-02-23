'use client'

import { useEffect, useState } from 'react'
import { useThemeStore } from '@/store/themeStore'
import DarkModeToggle from './DarkModeToggle'

export default function ThemedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isDarkMode } = useThemeStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (mounted) {
      if (isDarkMode) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    }
  }, [isDarkMode, mounted])

  if (!mounted) {
    return <>{children}</>
  }

  return (
    <div
      className="max-w-md mx-auto min-h-screen shadow-2xl relative"
      style={{
        backgroundColor: isDarkMode ? '#1F2937' : '#FFFFFF',
        minHeight: '100vh',
      }}
    >
      {/* Dark mode toggle - fixed position in top right corner */}
      <div 
        className="fixed top-4 right-4 z-[9999]" 
        style={{ 
          position: 'fixed',
          top: '16px',
          right: '16px',
          zIndex: 9999,
        }}
      >
        <DarkModeToggle />
      </div>
      {children}
    </div>
  )
}

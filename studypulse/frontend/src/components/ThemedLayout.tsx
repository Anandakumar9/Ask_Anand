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
      {/* Dark mode toggle in top right */}
      <div className="absolute top-4 right-4 z-50">
        <DarkModeToggle />
      </div>
      {children}
    </div>
  )
}

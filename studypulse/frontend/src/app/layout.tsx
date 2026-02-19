import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/Providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'StudyPulse | AI-Powered Exam Prep',
  description: 'Master your exams with AI-powered mock tests and focus timers.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <div className="max-w-md mx-auto min-h-screen shadow-2xl relative bg-white">
            {children}
          </div>
        </Providers>
      </body>
    </html>
  )
}

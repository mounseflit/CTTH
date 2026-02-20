'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import Sidebar from '@/components/layout/Sidebar'
import ErrorBoundary from '@/components/ui/ErrorBoundary'
import { useAuthStore } from '@/lib/store'

export default function ClientShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const { hydrate } = useAuthStore()
  const isLoginPage = pathname === '/login'
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    hydrate()
    setMounted(true)
  }, [hydrate])

  useEffect(() => {
    if (mounted && !isLoginPage) {
      const storedToken = localStorage.getItem('ctth_token')
      if (!storedToken) {
        window.location.href = '/login'
      }
    }
  }, [mounted, isLoginPage])

  if (!mounted) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
      </div>
    )
  }

  if (isLoginPage) {
    return (
      <main className="min-h-screen">
        <ErrorBoundary>{children}</ErrorBoundary>
      </main>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto gradient-mesh">
        <div className="p-8 max-w-[1440px] mx-auto animate-fade-in">
          <ErrorBoundary>{children}</ErrorBoundary>
        </div>
      </main>
    </div>
  )
}

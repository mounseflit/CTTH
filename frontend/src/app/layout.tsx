'use client'

import './globals.css'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import Sidebar from '@/components/layout/Sidebar'
import { useAuthStore } from '@/lib/store'

function AppShell({ children }: { children: React.ReactNode }) {
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
    return <main className="min-h-screen">{children}</main>
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto gradient-mesh">
        <div className="p-8 max-w-[1440px] mx-auto animate-fade-in">{children}</div>
      </main>
    </div>
  )
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <head>
        <title>CTTH — AI Watch Agent</title>
        <meta
          name="description"
          content="Centre Technique du Textile et de l&#39;Habillement — Plateforme de veille sectorielle"
        />
      </head>
      <body className="bg-surface-50 text-surface-900 antialiased" suppressHydrationWarning>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  )
}

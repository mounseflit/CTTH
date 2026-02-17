'use client'

import './globals.css'
import { usePathname } from 'next/navigation'
import { useEffect } from 'react'
import Sidebar from '@/components/layout/Sidebar'
import { useAuthStore } from '@/lib/store'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const { hydrate, token } = useAuthStore()
  const isLoginPage = pathname === '/login'

  useEffect(() => {
    hydrate()
  }, [hydrate])

  // Redirect to login if not authenticated (client-side)
  useEffect(() => {
    if (typeof window !== 'undefined' && !isLoginPage) {
      const storedToken = localStorage.getItem('ctth_token')
      if (!storedToken) {
        window.location.href = '/login'
      }
    }
  }, [isLoginPage])

  return (
    <html lang="fr">
      <head>
        <title>CTTH — AI Watch Agent</title>
        <meta name="description" content="Centre Technique du Textile et de l'Habillement — Plateforme de veille sectorielle" />
      </head>
      <body className="bg-surface-50 text-surface-900 antialiased">
        {isLoginPage ? (
          <main className="min-h-screen">{children}</main>
        ) : (
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto gradient-mesh">
              <div className="p-8 max-w-[1440px] mx-auto animate-fade-in">{children}</div>
            </main>
          </div>
        )}
      </body>
    </html>
  )
}

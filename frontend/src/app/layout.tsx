import './globals.css'
import ClientShell from '@/components/layout/ClientShell'

export const metadata = {
  title: 'CTTH — AI Watch Agent',
  description: "Centre Technique du Textile et de l'Habillement — Plateforme de veille sectorielle",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className="bg-surface-50 text-surface-900 antialiased" suppressHydrationWarning>
        <ClientShell>{children}</ClientShell>
      </body>
    </html>
  )
}

'use client'

import { useEffect } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('[Page Error]', error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-red-50 flex items-center justify-center mb-4">
        <AlertTriangle size={28} className="text-red-400" />
      </div>
      <h2 className="text-xl font-bold text-surface-800 mb-2">
        Erreur de chargement
      </h2>
      <p className="text-sm text-surface-500 mb-6 max-w-md leading-relaxed">
        Une erreur inattendue est survenue lors du chargement de cette page.
      </p>
      <div className="flex items-center gap-3">
        <button
          onClick={reset}
          className="flex items-center gap-2 px-5 py-2.5 bg-primary-500 text-white rounded-xl text-sm font-semibold hover:bg-primary-600 transition-all duration-200 shadow-sm"
        >
          <RefreshCw size={14} />
          Réessayer
        </button>
        <a
          href="/"
          className="flex items-center gap-2 px-5 py-2.5 bg-surface-100 text-surface-700 rounded-xl text-sm font-semibold hover:bg-surface-200 transition-all duration-200"
        >
          <Home size={14} />
          Accueil
        </a>
      </div>
    </div>
  )
}

'use client'

import { useState } from 'react'
import Image from 'next/image'
import { authApi } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { Sparkles, Eye, EyeOff } from 'lucide-react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const { setAuth } = useAuthStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = isRegister
        ? await authApi.register(email, password, fullName || undefined)
        : await authApi.login(email, password)

      const { access_token, user } = response.data
      setAuth(access_token, user)
      window.location.href = '/'
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(
        axiosErr.response?.data?.detail || 'Erreur de connexion'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex relative overflow-hidden">
      {/* Left — Branding panel */}
      <div className="hidden lg:flex lg:w-[55%] gradient-primary relative flex-col justify-between p-12">
        {/* Decorative circles */}
        <div className="absolute top-20 right-20 w-64 h-64 rounded-full bg-white/[0.04]" />
        <div className="absolute bottom-32 left-16 w-40 h-40 rounded-full bg-white/[0.04]" />
        <div className="absolute top-1/2 right-1/3 w-80 h-80 rounded-full bg-white/[0.02]" />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl bg-white/15 backdrop-blur flex items-center justify-center overflow-hidden">
              <Image
                src="https://www.ctth.ma/wp-content/uploads/2021/05/logo-CTTH-FINAL-2.jpg"
                alt="CTTH"
                width={38}
                height={38}
                className="rounded-lg object-contain"
              />
            </div>
            <div>
              <h2 className="text-white text-xl font-bold tracking-tight">CTTH</h2>
              <div className="flex items-center gap-1">
                <Sparkles size={10} className="text-accent-300" />
                <span className="text-[10px] font-medium text-white/50 uppercase tracking-wider">AI Watch Agent</span>
              </div>
            </div>
          </div>
        </div>

        <div className="relative z-10 max-w-lg">
          <h1 className="text-4xl font-extrabold text-white leading-tight tracking-tight">
            Veille Intelligente du<br />
            <span className="text-accent-300">Secteur Textile</span>
          </h1>
          <p className="text-base text-white/60 mt-4 leading-relaxed">
            Plateforme d&apos;intelligence économique alimentée par l&apos;IA pour le suivi en temps réel du commerce textile et de l&apos;habillement marocain.
          </p>
          <div className="flex items-center gap-6 mt-8">
            <div className="text-center">
              <p className="text-2xl font-extrabold text-white">10+</p>
              <p className="text-[10px] uppercase tracking-wider text-white/40 mt-0.5">Sources de données</p>
            </div>
            <div className="w-px h-10 bg-white/10" />
            <div className="text-center">
              <p className="text-2xl font-extrabold text-white">24/7</p>
              <p className="text-[10px] uppercase tracking-wider text-white/40 mt-0.5">Surveillance</p>
            </div>
          </div>
        </div>

        <p className="relative z-10 text-xs text-white/25">
          &copy; {new Date().getFullYear()} Centre Technique du Textile et de l&apos;Habillement
        </p>
      </div>

      {/* Right — Login form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-surface-50">
        <div className="w-full max-w-[400px] animate-fade-in">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8 justify-center">
            <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center overflow-hidden">
              <Image
                src="https://www.ctth.ma/wp-content/uploads/2021/05/logo-CTTH-FINAL-2.jpg"
                alt="CTTH"
                width={32}
                height={32}
                className="rounded-lg object-contain"
              />
            </div>
            <h2 className="text-xl font-bold text-surface-900">CTTH</h2>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-extrabold text-surface-900 tracking-tight">
              {isRegister ? 'Créer un compte' : 'Bienvenue'}
            </h2>
            <p className="text-sm text-surface-500 mt-1">
              {isRegister
                ? 'Rejoignez la plateforme de veille textile'
                : 'Connectez-vous à votre tableau de bord'}
            </p>
          </div>

          {error && (
            <div className="mb-5 p-3.5 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600 font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1.5 uppercase tracking-wider">
                  Nom complet
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="input-field"
                  placeholder="Votre nom complet"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1.5 uppercase tracking-wider">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="input-field"
                placeholder="votre@email.com"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1.5 uppercase tracking-wider">
                Mot de passe
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="input-field pr-10"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600 transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary mt-2"
            >
              {loading
                ? 'Chargement...'
                : isRegister
                  ? 'Créer le compte'
                  : 'Se connecter'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setIsRegister(!isRegister)
                setError('')
              }}
              className="text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors"
            >
              {isRegister
                ? 'Déjà un compte ? Se connecter'
                : 'Pas de compte ? Créer un compte'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}


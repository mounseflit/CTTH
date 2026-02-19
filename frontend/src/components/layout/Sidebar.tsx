'use client'

import Link from 'next/link'
import Image from 'next/image'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  BarChart3,
  Newspaper,
  FileText,
  Settings,
  LogOut,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import { useAuthStore } from '@/lib/store'

const navItems = [
  { href: '/', label: 'Tableau de Bord', icon: LayoutDashboard },
  { href: '/trade', label: 'Analyse Commerciale', icon: BarChart3 },
  { href: '/market-research', label: 'Etude de March\u00e9', icon: TrendingUp },
  { href: '/news', label: 'Veille & Actualit\u00e9s', icon: Newspaper },
  { href: '/reports', label: 'Centre de Rapports', icon: FileText },
  { href: '/settings', label: 'Param\u00e8tres', icon: Settings },
]

export default function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <aside className="w-[272px] bg-surface-950 flex flex-col h-screen relative overflow-hidden">
      {/* Subtle gradient accent at top */}
      <div className="absolute top-0 left-0 right-0 h-48 bg-gradient-to-b from-primary-900/20 to-transparent pointer-events-none" />

      {/* Logo */}
      <div className="relative z-10 px-6 pt-6 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur flex items-center justify-center overflow-hidden flex-shrink-0">
            <Image
              src="https://www.ctth.ma/wp-content/uploads/2021/05/logo-CTTH-FINAL-2.jpg"
              alt="CTTH"
              width={32}
              height={32}
              className="object-contain rounded-lg"
            />
          </div>
          <div className="min-w-0">
            <h1 className="text-base font-bold text-white tracking-tight">CTTH</h1>
            <div className="flex items-center gap-1.5">
              <Sparkles size={10} className="text-accent-400" />
              <p className="text-[10px] font-medium text-surface-400 uppercase tracking-wider">AI Watch Agent</p>
            </div>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="mx-5 border-t border-white/[0.06]" />

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1 relative z-10">
        <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-surface-500">
          Navigation
        </p>
        {navItems.map((item) => {
          const isActive =
            item.href === '/'
              ? pathname === '/'
              : pathname.startsWith(item.href)
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-nav-item ${isActive ? 'sidebar-nav-active' : 'sidebar-nav-inactive'
                }`}
            >
              <Icon size={18} strokeWidth={isActive ? 2.2 : 1.8} />
              <span>{item.label}</span>
              {isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white/80" />
              )}
            </Link>
          )
        })}
      </nav>

      {/* User section */}
      <div className="relative z-10 px-4 pb-5">
        <div className="mx-1 mb-3 border-t border-white/[0.06]" />
        {user && (
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-white">
                {(user.full_name || user.email || '?')[0].toUpperCase()}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-white/90 truncate">
                {user.full_name || user.email}
              </p>
              <p className="text-[10px] font-medium text-surface-500 uppercase tracking-wider truncate">{user.role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-surface-500 hover:text-red-400 hover:bg-white/[0.05] transition-all duration-200"
              title="Déconnexion"
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}


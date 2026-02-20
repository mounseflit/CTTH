'use client'

import { useEffect, useState } from 'react'
import { dashboardApi } from '@/lib/api'
import type { DashboardData } from '@/types'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import AreaTrendChart from '@/components/charts/AreaTrendChart'
import BarChartWidget from '@/components/charts/BarChartWidget'
import {
  TrendingUp,
  TrendingDown,
  Scale,
  Bell,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  RefreshCw,
} from 'lucide-react'

const iconConfig: Record<string, { icon: React.ElementType; gradient: string; bg: string }> = {
  'trending-up': {
    icon: TrendingUp,
    gradient: 'from-emerald-500 to-green-600',
    bg: 'bg-emerald-50',
  },
  'trending-down': {
    icon: TrendingDown,
    gradient: 'from-amber-500 to-orange-600',
    bg: 'bg-amber-50',
  },
  scale: {
    icon: Scale,
    gradient: 'from-primary-500 to-primary-700',
    bg: 'bg-primary-50',
  },
  bell: {
    icon: Bell,
    gradient: 'from-purple-500 to-violet-600',
    bg: 'bg-purple-50',
  },
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = (bust = false) => {
    setLoading(true)
    if (bust) dashboardApi.invalidate()
    dashboardApi
      .get()
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Erreur de chargement'))
      .finally(() => { setLoading(false); setRefreshing(false) })
  }

  useEffect(() => { fetchData() }, [])

  if (loading && !refreshing) return <LoadingSpinner />
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-16 h-16 rounded-2xl bg-red-50 flex items-center justify-center mb-4">
          <Activity size={28} className="text-red-400" />
        </div>
        <p className="text-red-500 font-medium">{error}</p>
      </div>
    )
  }
  if (!data) return null

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-surface-900 tracking-tight">
            Tableau de Bord
          </h1>
          <p className="text-sm text-surface-500 mt-1.5">
            Vue d&apos;ensemble du secteur textile et habillement marocain
          </p>
        </div>
        <button
          onClick={() => { setRefreshing(true); fetchData(true) }}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-surface-600 bg-white border border-surface-200 rounded-xl hover:bg-surface-50 hover:border-surface-300 transition-all duration-200 shadow-sm"
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          Actualiser
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
        {data.kpi_cards.map((kpi, i) => {
          const config = iconConfig[kpi.icon] || iconConfig['scale']
          const Icon = config.icon
          const isPositive = kpi.change_pct !== null && kpi.change_pct >= 0

          return (
            <div
              key={i}
              className="group glass-card glass-card-hover rounded-2xl p-5 relative overflow-hidden animate-slide-up"
              style={{ animationDelay: `${i * 80}ms`, animationFillMode: 'both' }}
            >
              {/* Decorative corner */}
              <div className={`absolute -top-6 -right-6 w-20 h-20 rounded-full bg-gradient-to-br ${config.gradient} opacity-[0.07] group-hover:opacity-[0.12] transition-opacity duration-500`} />

              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-semibold uppercase tracking-wider text-surface-400">
                    {kpi.label}
                  </p>
                  <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${config.gradient} flex items-center justify-center shadow-sm`}>
                    <Icon size={16} className="text-white" />
                  </div>
                </div>
                <p className="text-2xl font-extrabold text-surface-900 tracking-tight">
                  {kpi.value}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  {kpi.change_pct !== null && kpi.change_pct !== undefined && (
                    <span
                      className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded-lg text-xs font-bold ${isPositive
                          ? 'bg-emerald-50 text-emerald-600'
                          : 'bg-red-50 text-red-500'
                        }`}
                    >
                      {isPositive ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                      {isPositive ? '+' : ''}{kpi.change_pct}%
                    </span>
                  )}
                  {kpi.period && (
                    <span className="text-[11px] text-surface-400">{kpi.period}</span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <Card title="Tendances Export / Import" subtitle="Évolution annuelle des échanges commerciaux">
            <AreaTrendChart data={data.trend_data} />
            <p className="text-[10px] text-surface-400 mt-3 text-right italic">Sources : Eurostat (ext_lt_maineu) &middot; UN Comtrade</p>
          </Card>
        </div>
        <Card title="Top Partenaires" subtitle="Par valeur commerciale totale">
          <BarChartWidget
            data={data.top_partners.map((p) => ({
              label: p.partner_name || p.label || 'N/A',
              value: Number(p.value) || 0,
            }))}
            layout="horizontal"
          />
          <p className="text-[10px] text-surface-400 mt-3 text-right italic">Sources : Eurostat &middot; UN Comtrade</p>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card title="Répartition par Chapitre SH" subtitle="Ventilation des échanges textile">
          <BarChartWidget
            data={data.hs_breakdown.slice(0, 10).map((h) => ({
              label: `Ch. ${h.chapter}`,
              value: Number(h.value) || 0,
            }))}
            color="#f05e06"
          />
          <p className="text-[10px] text-surface-400 mt-3 text-right italic">Sources : Eurostat (SITC) &middot; UN Comtrade (HS 50-63)</p>
        </Card>

        <div className="xl:col-span-2">
          <Card title="Actualités Récentes" subtitle="Dernières nouvelles du secteur — OpenAI, Gemini, Federal Register, OTEXA">
            <div className="space-y-1 max-h-[360px] overflow-y-auto pr-1">
              {data.recent_news.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10">
                  <Bell size={24} className="text-surface-300 mb-2" />
                  <p className="text-surface-400 text-sm">Aucune actualité</p>
                </div>
              ) : (
                data.recent_news.map((news, idx) => {
                  const content = (
                    <>
                      <div className="mt-1 flex-shrink-0">
                        {news.category && <Badge type={news.category} />}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-surface-800 line-clamp-2 group-hover/item:text-primary-700 transition-colors">
                          {news.title}
                        </p>
                        <p className="text-xs text-surface-400 mt-1">
                          {news.source_name}
                          {news.published_at &&
                            ` · ${new Date(news.published_at).toLocaleDateString('fr-FR', {
                              day: 'numeric',
                              month: 'short',
                              year: 'numeric',
                            })}`}
                        </p>
                      </div>
                      <ArrowUpRight size={14} className="mt-1 text-surface-300 group-hover/item:text-primary-500 flex-shrink-0 transition-colors" />
                    </>
                  )
                  const sharedClass = "flex items-start gap-3 p-3 rounded-xl hover:bg-surface-50 transition-all duration-200 group/item animate-slide-up"
                  const sharedStyle = { animationDelay: `${idx * 60}ms`, animationFillMode: 'both' as const }
                  return news.source_url ? (
                    <a
                      key={news.id}
                      href={news.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`${sharedClass} cursor-pointer`}
                      style={sharedStyle}
                    >
                      {content}
                    </a>
                  ) : (
                    <div key={news.id} className={sharedClass} style={sharedStyle}>
                      {content}
                    </div>
                  )
                })
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}


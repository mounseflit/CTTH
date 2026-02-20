'use client'

import { useEffect, useState } from 'react'
import { marketResearchApi } from '@/lib/api'
import BarChartWidget from '@/components/charts/BarChartWidget'
import PieChartWidget from '@/components/charts/PieChartWidget'
import type {
  MarketOverview,
  Segment,
  Company,
  MarketShare,
  CompetitiveEvent,
  Insight,
  FrameworkResult,
  MarketSizeSeries,
} from '@/types'
import Card from '@/components/ui/Card'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import {
  TrendingUp,
  Building2,
  Layers,
  Brain,
  Calendar,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Activity,
  Target,
  Shield,
  Lightbulb,
  AlertTriangle,
  Globe,
  ArrowUpRight,
  Sparkles,
  RotateCcw,
} from 'lucide-react'


const TABS = [
  { key: 'overview', label: 'Vue d\'ensemble', icon: TrendingUp },
  { key: 'segments', label: 'Segmentation', icon: Layers },
  { key: 'companies', label: 'Entreprises', icon: Building2 },
  { key: 'frameworks', label: 'Frameworks', icon: Brain },
  { key: 'events', label: 'Evenements', icon: Calendar },
]

const EVENT_TYPE_LABELS: Record<string, string> = {
  m_and_a: 'M&A',
  partnership: 'Partenariat',
  expansion: 'Expansion',
  regulation: 'Regulation',
  investment: 'Investissement',
}

const INSIGHT_ICONS: Record<string, React.ElementType> = {
  trend: TrendingUp,
  risk: AlertTriangle,
  opportunity: Lightbulb,
  challenge: Shield,
  driver: Target,
}

const formatValue = (val: number) => {
  const abs = Math.abs(val)
  const sign = val < 0 ? '-' : ''
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(1)}B`
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(1)}M`
  if (abs >= 1e3) return `${sign}$${(abs / 1e3).toFixed(0)}K`
  return `${sign}$${abs.toFixed(0)}`
}

// ── Framework value renderer (handles nested objects from LLM) ──
function renderFrameworkValue(val: unknown): string {
  if (val === null || val === undefined) return 'N/A'
  if (typeof val === 'string') return val
  if (typeof val === 'number') return String(val)
  if (Array.isArray(val)) {
    return val.map((item) => {
      if (typeof item === 'string') return item
      if (typeof item === 'object' && item !== null) {
        const obj = item as Record<string, unknown>
        const parts = [obj.factor, obj.text, obj.description, obj.impact, obj.content, obj.titre, obj.valeur]
          .filter(Boolean)
          .map(String)
        return parts.length > 0 ? parts.join(' — ') : JSON.stringify(item)
      }
      return String(item)
    }).join('\n• ')
  }
  if (typeof val === 'object') {
    const obj = val as Record<string, unknown>
    const text = obj.text || obj.description || obj.content || obj.summary || obj.factor
    if (text) return String(text)
    return Object.entries(obj)
      .map(([k, v]) => `${k}: ${String(v)}`)
      .join('; ')
  }
  return String(val)
}

export default function MarketResearchPage() {
  const [tab, setTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  // Data states
  const [overview, setOverview] = useState<MarketOverview | null>(null)
  const [segments, setSegments] = useState<Segment[]>([])
  const [marketSize, setMarketSize] = useState<MarketSizeSeries | null>(null)
  const [companies, setCompanies] = useState<Company[]>([])
  const [marketShare, setMarketShare] = useState<MarketShare | null>(null)
  const [events, setEvents] = useState<CompetitiveEvent[]>([])
  const [insights, setInsights] = useState<Insight[]>([])
  const [frameworks, setFrameworks] = useState<Record<string, FrameworkResult>>({})
  const [frameworkLoading, setFrameworkLoading] = useState<Record<string, boolean>>({})
  const [expandedCompany, setExpandedCompany] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      const [ovRes, segRes, sizeRes, compRes, shareRes, evRes, insRes] = await Promise.all([
        marketResearchApi.getOverview().catch(() => null),
        marketResearchApi.getSegments().catch(() => null),
        marketResearchApi.getMarketSize().catch(() => null),
        marketResearchApi.getCompanies().catch(() => null),
        marketResearchApi.getMarketShare().catch(() => null),
        marketResearchApi.getCompetitiveEvents().catch(() => null),
        marketResearchApi.getInsights().catch(() => null),
      ])
      if (ovRes) setOverview(ovRes.data)
      if (segRes) setSegments(segRes.data)
      if (sizeRes) setMarketSize(sizeRes.data)
      if (compRes) setCompanies(compRes.data)
      if (shareRes) setMarketShare(shareRes.data)
      if (evRes) setEvents(evRes.data)
      if (insRes) setInsights(insRes.data)
    } catch {
      /* ignore */
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const fetchFrameworks = async () => {
    // Load all 3 frameworks in parallel (backend uses 24h cache)
    setFrameworkLoading({ porter: true, pestel: true, tam_sam_som: true })
    const [porterRes, pestelRes, tamRes] = await Promise.all([
      marketResearchApi.generateFramework({ framework_type: 'porter' }).catch(() => null),
      marketResearchApi.generateFramework({ framework_type: 'pestel' }).catch(() => null),
      marketResearchApi.generateFramework({ framework_type: 'tam_sam_som' }).catch(() => null),
    ])
    const newFrameworks: Record<string, FrameworkResult> = {}
    if (porterRes) newFrameworks['porter'] = porterRes.data
    if (pestelRes) newFrameworks['pestel'] = pestelRes.data
    if (tamRes) newFrameworks['tam_sam_som'] = tamRes.data
    setFrameworks(newFrameworks)
    setFrameworkLoading({})
  }

  useEffect(() => {
    fetchData()
    fetchFrameworks()
  }, [])

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await marketResearchApi.refresh()
    } catch {
      /* ignore */
    }
    setTimeout(() => fetchData(), 2000)
  }

  const handleGenerateFramework = async (type: string) => {
    setFrameworkLoading((prev) => ({ ...prev, [type]: true }))
    try {
      const res = await marketResearchApi.generateFramework({ framework_type: type })
      setFrameworks((prev) => ({ ...prev, [type]: res.data }))
    } catch {
      /* ignore */
    } finally {
      setFrameworkLoading((prev) => ({ ...prev, [type]: false }))
    }
  }

  if (loading) return <LoadingSpinner />

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-surface-900 tracking-tight">
            Etude de March&eacute;
          </h1>
          <p className="text-sm text-surface-500 mt-1.5">
            Analyse compl&egrave;te du secteur textile et habillement marocain
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-surface-600 bg-white border border-surface-200 rounded-xl hover:bg-surface-50 hover:border-surface-300 transition-all duration-200 shadow-sm"
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          Actualiser
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-white/80 backdrop-blur rounded-xl border border-surface-200 shadow-sm">
        {TABS.map((t) => {
          const Icon = t.icon
          return (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                tab === t.key
                  ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-sm'
                  : 'text-surface-500 hover:text-surface-700 hover:bg-surface-50'
              }`}
            >
              <Icon size={15} />
              {t.label}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      {tab === 'overview' && <OverviewTab overview={overview} marketSize={marketSize} insights={insights} />}
      {tab === 'segments' && <SegmentsTab segments={segments} />}
      {tab === 'companies' && (
        <CompaniesTab
          companies={companies}
          marketShare={marketShare}
          expandedCompany={expandedCompany}
          setExpandedCompany={setExpandedCompany}
        />
      )}
      {tab === 'frameworks' && (
        <FrameworksTab
          frameworks={frameworks}
          frameworkLoading={frameworkLoading}
          onGenerate={handleGenerateFramework}
        />
      )}
      {tab === 'events' && <EventsTab events={events} />}
    </div>
  )
}

// ── Overview Tab ─────────────────────────────────────────────

function OverviewTab({
  overview,
  marketSize,
  insights,
}: {
  overview: MarketOverview | null
  marketSize: MarketSizeSeries | null
  insights: Insight[]
}) {
  if (!overview) return <div className="text-surface-400 text-center py-10">Aucune donnee disponible</div>

  const kpis = [
    { label: 'Taille du Marche', value: overview.market_size_formatted, icon: Globe, gradient: 'from-primary-500 to-primary-700' },
    { label: 'Croissance', value: overview.growth_pct !== null ? `${overview.growth_pct > 0 ? '+' : ''}${overview.growth_pct}%` : 'N/A', icon: TrendingUp, gradient: 'from-emerald-500 to-green-600' },
    { label: 'Balance Commerciale', value: formatValue(overview.trade_balance_usd), icon: Activity, gradient: 'from-amber-500 to-orange-600' },
    { label: 'Entreprises', value: String(overview.company_count), icon: Building2, gradient: 'from-purple-500 to-violet-600' },
  ]

  // Group market size by year for chart
  const sizeByYear: Record<number, { exports: number; imports: number }> = {}
  if (marketSize?.data) {
    for (const pt of marketSize.data) {
      if (!sizeByYear[pt.year]) sizeByYear[pt.year] = { exports: 0, imports: 0 }
      if (pt.flow === 'export') sizeByYear[pt.year].exports += pt.value_usd
      else if (pt.flow === 'import') sizeByYear[pt.year].imports += pt.value_usd
    }
  }
  const chartData = Object.entries(sizeByYear)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([year, v]) => ({ label: year, value: v.exports + v.imports }))

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
        {kpis.map((kpi, i) => {
          const Icon = kpi.icon
          return (
            <div key={i} className="glass-card glass-card-hover rounded-2xl p-5 relative overflow-hidden animate-slide-up" style={{ animationDelay: `${i * 80}ms`, animationFillMode: 'both' }}>
              <div className={`absolute -top-6 -right-6 w-20 h-20 rounded-full bg-gradient-to-br ${kpi.gradient} opacity-[0.07]`} />
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-semibold uppercase tracking-wider text-surface-400">{kpi.label}</p>
                  <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${kpi.gradient} flex items-center justify-center shadow-sm`}>
                    <Icon size={16} className="text-white" />
                  </div>
                </div>
                <p className="text-2xl font-extrabold text-surface-900 tracking-tight">{kpi.value}</p>
                <p className="text-[11px] text-surface-400 mt-1">{overview.latest_year}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Market Size Chart + Insights */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <Card title="Evolution de la Taille du Marche" subtitle="Volume total des echanges textiles par annee">
            <BarChartWidget data={chartData} />
            <p className="text-[10px] text-surface-400 mt-3 text-right italic">Sources : Eurostat &middot; UN Comtrade (derive)</p>
          </Card>
        </div>
        <Card title="Insights Cles" subtitle={`${insights.length} analyse(s) disponible(s)`}>
          <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
            {insights.length === 0 ? (
              <div className="flex flex-col items-center py-10">
                <Lightbulb size={24} className="text-surface-300 mb-2" />
                <p className="text-surface-400 text-sm">Aucun insight</p>
                <p className="text-surface-300 text-xs mt-1">Lancez l&apos;agent pour en generer</p>
              </div>
            ) : (
              insights.slice(0, 8).map((ins) => {
                const Icon = INSIGHT_ICONS[ins.category] || Lightbulb
                return (
                  <div key={ins.id} className="flex items-start gap-3 p-3 rounded-xl hover:bg-surface-50 transition-all">
                    <div className="mt-0.5 w-7 h-7 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0">
                      <Icon size={14} className="text-primary-600" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-surface-800 line-clamp-1">{ins.title}</p>
                      <p className="text-xs text-surface-500 mt-0.5 line-clamp-2">{ins.narrative_fr}</p>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

// ── Segments Tab ─────────────────────────────────────────────

function SegmentsTab({ segments }: { segments: Segment[] }) {
  const hsSegments = segments.filter((s) => s.axis === 'hs_chapter')
  const productSegments = segments.filter((s) => s.axis === 'product_category')
  const fiberSegments = segments.filter((s) => s.axis === 'fiber_type')

  const hsChartData = hsSegments
    .filter((s) => s.market_value && s.market_value > 0)
    .sort((a, b) => (b.market_value || 0) - (a.market_value || 0))
    .slice(0, 10)
    .map((s) => ({ label: `Ch. ${s.code}`, value: s.market_value || 0 }))

  return (
    <div className="space-y-6">
      <Card title="Repartition par Chapitre SH" subtitle="Valeur commerciale par chapitre textile (HS 50-63)">
        {hsChartData.length > 0 ? (
          <BarChartWidget data={hsChartData} color="#f05e06" />
        ) : (
          <div className="text-center py-10 text-surface-400 text-sm">Lancez le script de derivation pour peupler les donnees</div>
        )}
        <p className="text-[10px] text-surface-400 mt-3 text-right italic">Sources : Eurostat (SITC) &middot; UN Comtrade (HS 50-63)</p>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Chapitres SH" subtitle={`${hsSegments.length} chapitres textiles`}>
          <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
            {hsSegments.map((s) => (
              <div key={s.id} className="flex items-center justify-between p-3 rounded-xl hover:bg-surface-50 transition-all">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center">
                    <span className="text-xs font-bold text-primary-700">{s.code}</span>
                  </div>
                  <p className="text-sm font-medium text-surface-700">{s.label_fr}</p>
                </div>
                {s.market_value && (
                  <span className="text-xs font-semibold text-surface-500">{formatValue(s.market_value)}</span>
                )}
              </div>
            ))}
          </div>
        </Card>

        <div className="space-y-6">
          <Card title="Categories de Produits" subtitle={`${productSegments.length} categorie(s)`}>
            <div className="space-y-2">
              {productSegments.length === 0 ? (
                <p className="text-center py-6 text-surface-400 text-sm">Aucune categorie</p>
              ) : productSegments.map((s) => (
                <div key={s.id} className="flex items-center gap-3 p-3 rounded-xl hover:bg-surface-50 transition-all">
                  <div className="w-2 h-2 rounded-full bg-primary-400" />
                  <p className="text-sm text-surface-700">{s.label_fr}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Types de Fibres" subtitle={`${fiberSegments.length} type(s)`}>
            <div className="space-y-2">
              {fiberSegments.length === 0 ? (
                <p className="text-center py-6 text-surface-400 text-sm">Aucun type</p>
              ) : fiberSegments.map((s) => (
                <div key={s.id} className="flex items-center gap-3 p-3 rounded-xl hover:bg-surface-50 transition-all">
                  <div className="w-2 h-2 rounded-full bg-amber-400" />
                  <p className="text-sm text-surface-700">{s.label_fr}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

// ── Companies Tab ────────────────────────────────────────────

function CompaniesTab({
  companies,
  marketShare,
  expandedCompany,
  setExpandedCompany,
}: {
  companies: Company[]
  marketShare: MarketShare | null
  expandedCompany: string | null
  setExpandedCompany: (id: string | null) => void
}) {
  const shareData = (marketShare?.entries || []).map((e) => ({
    label: e.company_name,
    value: e.share_pct,
  }))

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Market Share Chart */}
        <Card title="Parts de Marche" subtitle={marketShare ? `Annee ${marketShare.year}` : 'Aucune donnee'}>
          {shareData.length > 0 ? (
            <PieChartWidget data={shareData} />
          ) : (
            <div className="flex flex-col items-center py-10">
              <Target size={24} className="text-surface-300 mb-2" />
              <p className="text-surface-400 text-sm">Aucune donnee</p>
              <p className="text-surface-300 text-xs mt-1">Lancez l&apos;agent pour collecter les parts de marche</p>
            </div>
          )}
        </Card>

        {/* Company List */}
        <div className="xl:col-span-2">
          <Card title="Entreprises du Secteur" subtitle={`${companies.length} entreprise(s) repertoriee(s)`}>
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
              {companies.length === 0 ? (
                <div className="flex flex-col items-center py-10">
                  <Building2 size={24} className="text-surface-300 mb-2" />
                  <p className="text-surface-400 text-sm">Aucune entreprise</p>
                  <p className="text-surface-300 text-xs mt-1">Lancez l&apos;agent de recherche pour decouvrir les acteurs</p>
                </div>
              ) : companies.map((c) => (
                <div key={c.id} className="rounded-xl border border-surface-100 overflow-hidden transition-all hover:border-surface-200">
                  <button
                    onClick={() => setExpandedCompany(expandedCompany === c.id ? null : c.id)}
                    className="w-full flex items-center gap-4 p-4 text-left"
                  >
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-bold text-white">{c.name[0]}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-surface-800 truncate">{c.name}</p>
                      <p className="text-xs text-surface-400 mt-0.5">
                        {c.hq_city ? `${c.hq_city}, ` : ''}{c.country}
                        {c.market_share_pct !== null && ` · ${c.market_share_pct}% du marche`}
                      </p>
                    </div>
                    {expandedCompany === c.id ? <ChevronUp size={16} className="text-surface-400" /> : <ChevronDown size={16} className="text-surface-400" />}
                  </button>

                  {expandedCompany === c.id && (
                    <div className="px-4 pb-4 space-y-4 animate-fade-in">
                      {c.description_fr && (
                        <p className="text-sm text-surface-600 leading-relaxed">{c.description_fr}</p>
                      )}

                      {/* SWOT */}
                      <div className="grid grid-cols-2 gap-3">
                        {[
                          { key: 'strengths', label: 'Forces', color: 'emerald' },
                          { key: 'weaknesses', label: 'Faiblesses', color: 'red' },
                          { key: 'opportunities', label: 'Opportunites', color: 'blue' },
                          { key: 'threats', label: 'Menaces', color: 'amber' },
                        ].map((sw) => {
                          const items = (c.swot as Record<string, string[]>)?.[sw.key] || []
                          return (
                            <div key={sw.key} className={`p-3 rounded-lg bg-${sw.color}-50/50`}>
                              <p className={`text-[10px] font-bold uppercase tracking-wider text-${sw.color}-600 mb-1.5`}>{sw.label}</p>
                              {items.length > 0 ? (
                                <ul className="space-y-1">
                                  {items.slice(0, 3).map((item, idx) => (
                                    <li key={idx} className="text-xs text-surface-600 flex items-start gap-1.5">
                                      <span className={`w-1 h-1 rounded-full bg-${sw.color}-400 mt-1.5 flex-shrink-0`} />
                                      {item}
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="text-xs text-surface-400 italic">Non disponible</p>
                              )}
                            </div>
                          )
                        })}
                      </div>

                      {/* Website */}
                      {c.website && (
                        <a href={c.website} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-xs text-primary-600 hover:text-primary-700 font-medium">
                          <Globe size={12} /> {c.website}
                          <ArrowUpRight size={10} />
                        </a>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

// ── Frameworks Tab ───────────────────────────────────────────

function FrameworksTab({
  frameworks,
  frameworkLoading,
  onGenerate,
}: {
  frameworks: Record<string, FrameworkResult>
  frameworkLoading: Record<string, boolean>
  onGenerate: (type: string) => void
}) {
  const frameworkTypes = [
    {
      key: 'porter',
      label: 'Forces de Porter',
      desc: 'Analyse des 5 forces concurrentielles du secteur textile marocain',
      icon: Shield,
      gradient: 'from-blue-500 to-indigo-600',
      bgLight: 'bg-blue-50',
    },
    {
      key: 'pestel',
      label: 'Analyse PESTEL',
      desc: 'Facteurs macro-environnementaux : Politique, Economique, Social, Technologique, Environnemental, Legal',
      icon: Globe,
      gradient: 'from-primary-500 to-primary-700',
      bgLight: 'bg-primary-50',
    },
    {
      key: 'tam_sam_som',
      label: 'TAM / SAM / SOM',
      desc: 'Estimation de la taille du marche adressable, exploitable et obtenable',
      icon: Target,
      gradient: 'from-amber-500 to-orange-600',
      bgLight: 'bg-amber-50',
    },
  ]

  return (
    <div className="space-y-6">
      {frameworkTypes.map((fw) => {
        const Icon = fw.icon
        const result = frameworks[fw.key]
        const isLoading = frameworkLoading[fw.key]

        return (
          <div key={fw.key} className="glass-card rounded-2xl overflow-hidden">
            {/* Header band */}
            <div className={`px-6 py-4 bg-gradient-to-r ${fw.gradient} flex items-center justify-between`}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
                  <Icon size={20} className="text-white" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{fw.label}</h3>
                  <p className="text-xs text-white/70 mt-0.5">{fw.desc}</p>
                </div>
              </div>
              {/* Regenerate button */}
              <button
                onClick={() => onGenerate(fw.key)}
                disabled={isLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-white/20 hover:bg-white/30 rounded-lg transition-all disabled:opacity-50 border border-white/30"
              >
                {isLoading ? (
                  <>
                    <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Generation...
                  </>
                ) : (
                  <>
                    <RotateCcw size={12} />
                    {result ? 'Regenerer' : 'Generer'}
                  </>
                )}
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="animate-pulse">
                      <div className="h-3 bg-surface-100 rounded w-1/4 mb-2" />
                      <div className="h-12 bg-surface-50 rounded" />
                    </div>
                  ))}
                </div>
              ) : result ? (
                <FrameworkContent type={fw.key} content={result.content} />
              ) : (
                <div className="flex flex-col items-center py-10">
                  <Sparkles size={24} className="text-surface-300 mb-3" />
                  <p className="text-surface-400 text-sm mb-1">Analyse non encore generee</p>
                  <p className="text-surface-300 text-xs">Cliquez sur &quot;Generer&quot; pour lancer l&apos;analyse IA</p>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function FrameworkContent({ type, content }: { type: string; content: Record<string, unknown> }) {
  if (type === 'porter') {
    const fields = [
      { key: 'rivalry', label: 'Rivalite entre concurrents', color: 'blue' },
      { key: 'new_entrants', label: 'Menace des nouveaux entrants', color: 'purple' },
      { key: 'substitutes', label: 'Menace des substituts', color: 'amber' },
      { key: 'buyer_power', label: 'Pouvoir des acheteurs', color: 'emerald' },
      { key: 'supplier_power', label: 'Pouvoir des fournisseurs', color: 'red' },
    ]
    return (
      <div className="space-y-3 text-xs">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {fields.map((f) => (
            <div key={f.key} className="p-3 rounded-xl bg-surface-50 border border-surface-100">
              <p className={`font-bold text-surface-700 mb-1.5 flex items-center gap-1.5`}>
                <span className={`w-2 h-2 rounded-full bg-${f.color}-400 flex-shrink-0`} />
                {f.label}
              </p>
              <p className="text-surface-500 leading-relaxed whitespace-pre-line">
                {renderFrameworkValue(content[f.key]) || 'N/A'}
              </p>
            </div>
          ))}
        </div>
        {content.summary && (
          <div className="p-4 rounded-xl bg-blue-50 border border-blue-100 mt-4">
            <p className="font-bold text-blue-700 mb-1.5">Synthese</p>
            <p className="text-blue-600 leading-relaxed whitespace-pre-line">{renderFrameworkValue(content.summary)}</p>
          </div>
        )}
      </div>
    )
  }

  if (type === 'pestel') {
    const fields = [
      { key: 'political', label: 'Politique', color: 'blue', emoji: '🏛️' },
      { key: 'economic', label: 'Economique', color: 'emerald', emoji: '📈' },
      { key: 'social', label: 'Social', color: 'purple', emoji: '👥' },
      { key: 'technological', label: 'Technologique', color: 'cyan', emoji: '⚙️' },
      { key: 'environmental', label: 'Environnemental', color: 'green', emoji: '🌿' },
      { key: 'legal', label: 'Legal', color: 'amber', emoji: '⚖️' },
    ]
    return (
      <div className="space-y-3 text-xs">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {fields.map((f) => (
            <div key={f.key} className="p-3 rounded-xl bg-surface-50 border border-surface-100">
              <p className="font-bold text-surface-700 mb-1.5 flex items-center gap-1.5">
                <span className="text-sm">{f.emoji}</span>
                {f.label}
              </p>
              <p className="text-surface-500 leading-relaxed whitespace-pre-line">
                {renderFrameworkValue(content[f.key]) || 'N/A'}
              </p>
            </div>
          ))}
        </div>
        {content.summary && (
          <div className="p-4 rounded-xl bg-primary-50 border border-primary-100 mt-4">
            <p className="font-bold text-primary-700 mb-1.5">Synthese</p>
            <p className="text-primary-600 leading-relaxed whitespace-pre-line">{renderFrameworkValue(content.summary)}</p>
          </div>
        )}
      </div>
    )
  }

  // TAM/SAM/SOM
  const tam = content.tam as Record<string, unknown> | undefined
  const sam = content.sam as Record<string, unknown> | undefined
  const som = content.som as Record<string, unknown> | undefined

  return (
    <div className="space-y-4 text-xs">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { data: tam, label: 'TAM', sublabel: 'Marche Total Adressable', color: 'amber', bgColor: 'bg-amber-50', borderColor: 'border-amber-200', textColor: 'text-amber-700' },
          { data: sam, label: 'SAM', sublabel: 'Marche Disponible Exploitable', color: 'orange', bgColor: 'bg-orange-50', borderColor: 'border-orange-200', textColor: 'text-orange-700' },
          { data: som, label: 'SOM', sublabel: 'Marche Obtenable', color: 'red', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-700' },
        ].map((item) => (
          <div key={item.label} className={`p-4 rounded-xl ${item.bgColor} border ${item.borderColor}`}>
            <div className="flex items-baseline gap-2 mb-2">
              <span className={`text-2xl font-extrabold ${item.textColor}`}>{item.label}</span>
              <span className="text-xs text-surface-500">{item.sublabel}</span>
            </div>
            {item.data?.value_usd && Number(item.data.value_usd) > 0 ? (
              <p className={`text-xl font-bold ${item.textColor} mb-1`}>{formatValue(Number(item.data.value_usd))}</p>
            ) : null}
            <p className="text-surface-600 leading-relaxed whitespace-pre-line">
              {renderFrameworkValue(item.data?.description) || 'N/A'}
            </p>
          </div>
        ))}
      </div>
      {(content.methodology || content.summary) && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-100 mt-2">
          <p className="font-bold text-amber-700 mb-1.5">Methodologie</p>
          <p className="text-amber-600 leading-relaxed whitespace-pre-line">
            {renderFrameworkValue(content.methodology || content.summary)}
          </p>
        </div>
      )}
    </div>
  )
}

// ── Events Tab ───────────────────────────────────────────────

function EventsTab({ events }: { events: CompetitiveEvent[] }) {
  return (
    <Card title="Evenements Concurrentiels" subtitle={`${events.length} evenement(s)`}>
      <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
        {events.length === 0 ? (
          <div className="flex flex-col items-center py-16">
            <Calendar size={24} className="text-surface-300 mb-2" />
            <p className="text-surface-400 text-sm">Aucun evenement</p>
            <p className="text-surface-300 text-xs mt-1">Lancez l&apos;agent pour decouvrir les evenements recents</p>
          </div>
        ) : events.map((e, idx) => (
          <div
            key={e.id}
            className="flex items-start gap-4 p-4 rounded-xl hover:bg-surface-50 transition-all animate-slide-up"
            style={{ animationDelay: `${idx * 40}ms`, animationFillMode: 'both' }}
          >
            <div className="mt-1">
              <span className={`inline-flex px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider ${
                e.event_type === 'investment' ? 'bg-emerald-50 text-emerald-600' :
                e.event_type === 'expansion' ? 'bg-blue-50 text-blue-600' :
                e.event_type === 'm_and_a' ? 'bg-purple-50 text-purple-600' :
                e.event_type === 'partnership' ? 'bg-amber-50 text-amber-600' :
                'bg-surface-100 text-surface-500'
              }`}>
                {EVENT_TYPE_LABELS[e.event_type] || e.event_type}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              {e.source_url ? (
                <a
                  href={e.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-semibold text-surface-800 hover:text-primary-600 transition-colors inline-flex items-center gap-1"
                >
                  {e.title}
                  <ArrowUpRight size={12} className="text-primary-400 flex-shrink-0" />
                </a>
              ) : (
                <p className="text-sm font-semibold text-surface-800">{e.title}</p>
              )}
              {e.company_name && (
                <p className="text-xs text-primary-600 font-medium mt-0.5">{e.company_name}</p>
              )}
              {e.description_fr && (
                <p className="text-xs text-surface-500 mt-1 leading-relaxed line-clamp-2">{e.description_fr}</p>
              )}
              <div className="flex items-center gap-3 mt-2">
                {e.event_date && (
                  <span className="text-[10px] text-surface-400">
                    {new Date(e.event_date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </span>
                )}
                {e.source_name && (
                  <>
                    <span className="w-1 h-1 rounded-full bg-surface-300" />
                    {e.source_url ? (
                      <a
                        href={e.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] text-primary-500 hover:underline"
                      >
                        {e.source_name}
                      </a>
                    ) : (
                      <span className="text-[10px] text-surface-400">{e.source_name}</span>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

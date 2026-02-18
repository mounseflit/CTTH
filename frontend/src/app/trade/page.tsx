'use client'

import { useEffect, useState } from 'react'
import { tradeApi } from '@/lib/api'
import type { TradeDataRow, TradePaginatedResponse, ChartDataPoint } from '@/types'
import Card from '@/components/ui/Card'
import BarChartWidget from '@/components/charts/BarChartWidget'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Pagination from '@/components/ui/Pagination'
import { Filter, Table2, BarChart3, ChevronDown, X } from 'lucide-react'

const HS_CHAPTERS = [
  { code: '50', label: 'Soie' },
  { code: '51', label: 'Laine' },
  { code: '52', label: 'Coton' },
  { code: '53', label: 'Fibres végétales' },
  { code: '54', label: 'Filaments synthétiques' },
  { code: '55', label: 'Fibres discontinues' },
  { code: '56', label: 'Ouates, feutres' },
  { code: '57', label: 'Tapis' },
  { code: '58', label: 'Tissus spéciaux' },
  { code: '59', label: 'Tissus imprégnés' },
  { code: '60', label: 'Bonneterie (étoffes)' },
  { code: '61', label: 'Bonneterie (vêtements)' },
  { code: '62', label: 'Vêtements (non bonneterie)' },
  { code: '63', label: 'Autres textiles' },
]

const FLOW_OPTIONS = [
  { key: '', label: 'Tous les flux', icon: '↕' },
  { key: 'export', label: 'Exportations', icon: '↑' },
  { key: 'import', label: 'Importations', icon: '↓' },
]

export default function TradePage() {
  const [tab, setTab] = useState<'overview' | 'data'>('data')
  const [flow, setFlow] = useState('')
  const [selectedHS, setSelectedHS] = useState<string[]>([])
  const [showHSPicker, setShowHSPicker] = useState(false)
  const [loading, setLoading] = useState(true)
  const [topPartners, setTopPartners] = useState<ChartDataPoint[]>([])
  const [hsBreakdown, setHsBreakdown] = useState<ChartDataPoint[]>([])
  const [tableData, setTableData] = useState<TradeDataRow[]>([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [total, setTotal] = useState(0)

  const fetchCharts = async () => {
    try {
      const [partnersRes, hsRes] = await Promise.all([
        tradeApi.getTopPartners({ flow: flow || undefined, limit: 10 }),
        tradeApi.getHsBreakdown({ flow: flow || undefined }),
      ])
      setTopPartners(
        partnersRes.data.map((p: Record<string, unknown>) => ({
          label: String(p.label || p.partner_name || 'N/A'),
          value: Number(p.value) || 0,
        }))
      )
      setHsBreakdown(
        hsRes.data.map((h: Record<string, unknown>) => ({
          label: `Ch. ${h.chapter}`,
          value: Number(h.value) || 0,
        }))
      )
    } catch {
      /* ignore */
    }
  }

  const fetchTable = async (p: number = 1) => {
    try {
      const params: Record<string, unknown> = { page: p, per_page: 25 }
      if (flow) params.flow = flow
      if (selectedHS.length) params.hs_codes = selectedHS.join(',')

      const res = await tradeApi.getData(params)
      const result: TradePaginatedResponse = res.data
      setTableData(result.data)
      setTotalPages(result.total_pages)
      setTotal(result.total)
      setPage(result.page)
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    setLoading(true)
    Promise.all([fetchCharts(), fetchTable()]).finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleApply = () => {
    setLoading(true)
    Promise.all([fetchCharts(), fetchTable(1)]).finally(() => setLoading(false))
  }

  const toggleHS = (code: string) => {
    setSelectedHS((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    )
  }

  const formatNum = (val: number | null) => {
    if (val === null || val === undefined) return '-'
    if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(1)}M`
    if (val >= 1_000) return `$${(val / 1_000).toFixed(0)}K`
    return `$${val.toFixed(0)}`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-surface-800 tracking-tight">Analyse Commerciale</h1>
          <p className="text-sm text-surface-500 mt-1">
            Données commerciales textiles du Maroc — {total} enregistrements
          </p>
        </div>
        <button
          onClick={handleApply}
          className="flex items-center gap-2 px-5 py-2.5 gradient-primary text-white rounded-xl text-sm font-semibold shadow-glow-primary hover:shadow-lg transition-all duration-200"
        >
          <Filter size={14} />
          Appliquer les filtres
        </button>
      </div>

      {/* Filters Bar */}
      <div className="bg-white border border-white/60 shadow-card rounded-2xl p-4 relative z-[60] overflow-visible">
        <div className="flex flex-wrap items-center gap-3">
          {/* Flow toggle */}
          <div className="flex bg-surface-100 rounded-xl p-1">
            {FLOW_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                onClick={() => setFlow(opt.key)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 ${flow === opt.key
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-surface-500 hover:text-surface-700'
                  }`}
              >
                <span className="text-sm">{opt.icon}</span>
                {opt.label}
              </button>
            ))}
          </div>

          {/* Divider */}
          <div className="w-px h-8 bg-surface-200" />

          {/* HS Chapters dropdown */}
          <div className="relative z-[999]">
            <button
              onClick={() => setShowHSPicker(!showHSPicker)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold border transition-all duration-200 ${selectedHS.length > 0
                ? 'bg-primary-50 border-primary-200 text-primary-700'
                : 'bg-white border-surface-200 text-surface-600 hover:border-surface-300'
                }`}
            >
              <span>Chapitres SH</span>
              {selectedHS.length > 0 && (
                <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary-500 text-white text-[10px] font-bold">
                  {selectedHS.length}
                </span>
              )}
              <ChevronDown size={14} className={`transition-transform ${showHSPicker ? 'rotate-180' : ''}`} />
            </button>

            {showHSPicker && (
              <>
                <div className="fixed inset-0 z-[9998]" onClick={() => setShowHSPicker(false)} />
                <div className="absolute top-full mt-2 left-0 z-[9999] bg-white rounded-2xl shadow-xl border border-surface-100 p-3 w-[420px] max-h-[320px] overflow-y-auto animate-fade-in">
                  <div className="flex items-center justify-between mb-2 px-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-surface-400">Sélectionnez les chapitres</span>
                    {selectedHS.length > 0 && (
                      <button
                        onClick={() => setSelectedHS([])}
                        className="text-[10px] font-semibold text-red-500 hover:text-red-600"
                      >
                        Tout effacer
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-1.5">
                    {HS_CHAPTERS.map((ch) => (
                      <button
                        key={ch.code}
                        onClick={() => toggleHS(ch.code)}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-left transition-all ${selectedHS.includes(ch.code)
                          ? 'bg-primary-50 text-primary-700 ring-1 ring-primary-200'
                          : 'hover:bg-surface-50 text-surface-600'
                          }`}
                      >
                        <span className={`w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 transition-all ${selectedHS.includes(ch.code)
                          ? 'bg-primary-500 border-primary-500'
                          : 'border-surface-300'
                          }`}>
                          {selectedHS.includes(ch.code) && (
                            <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </span>
                        <span className="font-mono text-primary-600 font-bold mr-1">{ch.code}</span>
                        {ch.label}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Selected HS chips */}
          {selectedHS.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {selectedHS.map((code) => {
                const ch = HS_CHAPTERS.find((c) => c.code === code)
                return (
                  <span
                    key={code}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-primary-50 text-primary-700 text-[11px] font-semibold ring-1 ring-primary-100"
                  >
                    {code} — {ch?.label}
                    <button onClick={() => toggleHS(code)} className="ml-0.5 hover:text-red-500">
                      <X size={12} />
                    </button>
                  </span>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="relative z-[1] flex gap-1 bg-surface-100 rounded-xl p-1 w-fit">
        <button
          onClick={() => {
            setTab('data')
            if (!tableData.length) fetchTable()
          }}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${tab === 'data'
            ? 'bg-white text-surface-800 shadow-sm'
            : 'text-surface-400 hover:text-surface-600'
            }`}
        >
          <Table2 size={15} />
          <span>Données détaillées</span>
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ml-auto ${tab === 'data' ? 'bg-primary-50 text-primary-600' : 'bg-surface-200 text-surface-500'
            }`}>
            {total}
          </span>
        </button>
        <button
          onClick={() => setTab('overview')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${tab === 'overview'
            ? 'bg-white text-surface-800 shadow-sm'
            : 'text-surface-400 hover:text-surface-600'
            }`}
        >
          <BarChart3 size={15} />
          Vue d&apos;ensemble
        </button>
      </div>

      {/* Content */}
      <div className="relative z-[1]">
      {loading ? (
        <LoadingSpinner />
      ) : tab === 'overview' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="Top 10 Partenaires" subtitle="Par valeur commerciale">
            <BarChartWidget data={topPartners} layout="horizontal" />
          </Card>
          <Card title="Répartition par Chapitre SH" subtitle="Ventilation textile">
            <BarChartWidget data={hsBreakdown} color="#353A3A" />
          </Card>
        </div>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-100">
                  <th className="text-left py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">Période</th>
                  <th className="text-left py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">Source</th>
                  <th className="text-left py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">Partenaire</th>
                  <th className="text-left py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">Code SH</th>
                  <th className="text-left py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">Flux</th>
                  <th className="text-right py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">Valeur (USD)</th>
                  <th className="text-right py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">Valeur (EUR)</th>
                  <th className="text-right py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">Poids (kg)</th>
                </tr>
              </thead>
              <tbody>
                {tableData.map((row) => (
                  <tr key={row.id} className="border-b border-surface-50 hover:bg-primary-50/30 transition-colors">
                    <td className="py-3 px-3 text-surface-600">{row.period_date}</td>
                    <td className="py-3 px-3">
                      <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-1 rounded-lg bg-surface-100 text-surface-500">
                        {row.source}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-medium text-surface-800">{row.partner_name || row.partner_code}</td>
                    <td className="py-3 px-3">
                      <span className="font-mono text-primary-700 font-semibold">{row.hs_code}</span>
                      {row.hs_description && (
                        <span className="text-xs text-surface-400 ml-1">
                          {row.hs_description}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-lg ${row.flow === 'export' ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'
                          }`}
                      >
                        {row.flow === 'export' ? '↑ Export' : '↓ Import'}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-surface-700">
                      {formatNum(row.value_usd)}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-surface-500">
                      {row.value_eur ? `${formatNum(row.value_eur).replace('$', '€')}` : '-'}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-surface-500">
                      {row.weight_kg ? `${(row.weight_kg / 1000).toFixed(1)}t` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            onPageChange={(p) => {
              fetchTable(p)
            }}
          />
        </Card>
      )}
      </div>
    </div>
  )
}

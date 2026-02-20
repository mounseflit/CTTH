'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { tradeApi, settingsApi } from '@/lib/api'
import type { DeepAnalysisResult, EmailRecipient } from '@/types'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import AreaTrendChart from '@/components/charts/AreaTrendChart'
import BarChartWidget from '@/components/charts/BarChartWidget'
import PieChartWidget from '@/components/charts/PieChartWidget'
import {
  Search,
  TrendingUp,
  TrendingDown,
  Minus,
  ArrowUpRight,
  ArrowDownRight,
  Star,
  HelpCircle,
  DollarSign,
  Trash2,
  Globe,
  Lightbulb,
  Target,
  Shield,
  Activity,
  Building2,
  Newspaper,
  ChevronDown,
  ChevronUp,
  Zap,
  Users,
  Calendar,
  ExternalLink,
  PieChart,
  BarChart3,
  Award,
  Mail,
  Download,
  Send,
  X,
  Check,
  Plus,
  FileText,
  Loader2,
} from 'lucide-react'

// ── HS Chapters 50-63 ────────────────────────────────────────────────────────
const HS_CHAPTERS = [
  { code: '50', label: 'Soie' },
  { code: '51', label: 'Laine & poils fins' },
  { code: '52', label: 'Coton' },
  { code: '53', label: 'Fibres végétales' },
  { code: '54', label: 'Filaments synthétiques' },
  { code: '55', label: 'Fibres discontinues' },
  { code: '56', label: 'Ouates, feutres, ficelles' },
  { code: '57', label: 'Tapis & revêtements' },
  { code: '58', label: 'Tissus spéciaux' },
  { code: '59', label: 'Tissus imprégnés' },
  { code: '60', label: 'Bonneterie (étoffes)' },
  { code: '61', label: 'Vêtements bonneterie' },
  { code: '62', label: 'Vêtements non-bonneterie' },
  { code: '63', label: 'Autres articles textiles' },
]

// Dynamic year list: current year down to 2018
const CURRENT_YEAR = new Date().getFullYear()
const YEARS = Array.from({ length: CURRENT_YEAR - 2018 + 1 }, (_, i) => CURRENT_YEAR - i)

// ── Helpers ──────────────────────────────────────────────────────────────────
function fmtUsd(val: number): string {
  const abs = Math.abs(val)
  const sign = val < 0 ? '-' : ''
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(1)}B`
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(1)}M`
  if (abs >= 1e3) return `${sign}$${(abs / 1e3).toFixed(0)}K`
  return `${sign}$${abs.toFixed(0)}`
}

function renderVal(val: unknown): string {
  if (val === null || val === undefined) return 'N/A'
  if (typeof val === 'string') return val
  if (typeof val === 'number') return String(val)
  if (Array.isArray(val)) {
    return val
      .map((item) => {
        if (typeof item === 'string') return item
        if (typeof item === 'object' && item !== null) {
          const obj = item as Record<string, unknown>
          const parts = [obj.factor, obj.text, obj.description, obj.impact, obj.content, obj.titre]
            .filter(Boolean)
            .map(String)
          return parts.length > 0 ? parts.join(' — ') : JSON.stringify(item)
        }
        return String(item)
      })
      .join('\n• ')
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

// ── BCG Position config ───────────────────────────────────────────────────────
const BCG_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; dotHex: string; icon: React.ElementType; desc: string }
> = {
  star: {
    label: 'Étoile',
    color: 'text-yellow-600',
    bg: 'bg-yellow-50',
    dotHex: '#ca8a04',
    icon: Star,
    desc: 'Fort potentiel + forte part de marché',
  },
  cash_cow: {
    label: 'Vache à lait',
    color: 'text-emerald-600',
    bg: 'bg-emerald-50',
    dotHex: '#059669',
    icon: DollarSign,
    desc: 'Forte part de marché + croissance faible',
  },
  question_mark: {
    label: 'Dilemme',
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    dotHex: '#2563eb',
    icon: HelpCircle,
    desc: 'Fort potentiel + faible part de marché',
  },
  dog: {
    label: 'Poids mort',
    color: 'text-surface-500',
    bg: 'bg-surface-100',
    dotHex: '#6b7280',
    icon: Trash2,
    desc: 'Faible croissance + faible part de marché',
  },
}

// ── Collapsible section ───────────────────────────────────────────────────────
function Section({
  title,
  icon: Icon,
  children,
  defaultOpen = true,
}: {
  title: string
  icon: React.ElementType
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-surface-50/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
            <Icon size={16} className="text-white" />
          </div>
          <h2 className="text-base font-bold text-surface-900">{title}</h2>
        </div>
        {open ? (
          <ChevronUp size={18} className="text-surface-400" />
        ) : (
          <ChevronDown size={18} className="text-surface-400" />
        )}
      </button>
      {open && <div className="px-6 pb-6">{children}</div>}
    </div>
  )
}

// ── PESTEL grid ───────────────────────────────────────────────────────────────
function PestelGrid({ data }: { data: Record<string, unknown> }) {
  const fields = [
    { key: 'political', label: 'Politique', icon: Shield, color: 'from-blue-500 to-blue-700' },
    { key: 'economic', label: 'Économique', icon: TrendingUp, color: 'from-emerald-500 to-emerald-700' },
    { key: 'social', label: 'Social', icon: Users, color: 'from-purple-500 to-purple-700' },
    { key: 'technological', label: 'Technologique', icon: Zap, color: 'from-orange-500 to-orange-700' },
    { key: 'environmental', label: 'Environnemental', icon: Globe, color: 'from-green-500 to-green-700' },
    { key: 'legal', label: 'Légal', icon: Activity, color: 'from-red-500 to-red-700' },
  ]
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {fields.map((f) => {
          const FIcon = f.icon
          const val = renderVal(data[f.key])
          if (!val || val === 'N/A') return null
          return (
            <div key={f.key} className="bg-surface-50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div
                  className={`w-6 h-6 rounded-lg bg-gradient-to-br ${f.color} flex items-center justify-center flex-shrink-0`}
                >
                  <FIcon size={12} className="text-white" />
                </div>
                <span className="text-xs font-bold uppercase tracking-wider text-surface-500">{f.label}</span>
              </div>
              <p className="text-sm text-surface-700 leading-relaxed whitespace-pre-line">{val}</p>
            </div>
          )
        })}
      </div>
      {data.summary && (
        <div className="bg-primary-50 rounded-xl p-4 border border-primary-100">
          <p className="text-sm font-semibold text-primary-700 mb-1">Synthèse</p>
          <p className="text-sm text-primary-800 leading-relaxed">{renderVal(data.summary)}</p>
        </div>
      )}
    </div>
  )
}

// ── Porter 5 Forces ───────────────────────────────────────────────────────────
function PorterGrid({ data }: { data: Record<string, unknown> }) {
  const forces = [
    { key: 'rivalry', label: 'Rivalité concurrentielle' },
    { key: 'new_entrants', label: 'Menace nouveaux entrants' },
    { key: 'substitutes', label: 'Menace des substituts' },
    { key: 'buyer_power', label: 'Pouvoir des acheteurs' },
    { key: 'supplier_power', label: 'Pouvoir des fournisseurs' },
  ]
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {forces.map((f) => {
          const val = renderVal(data[f.key])
          if (!val || val === 'N/A') return null
          return (
            <div key={f.key} className="bg-surface-50 rounded-xl p-4">
              <p className="text-xs font-bold uppercase tracking-wider text-surface-400 mb-2">{f.label}</p>
              <p className="text-sm text-surface-700 leading-relaxed whitespace-pre-line">{val}</p>
            </div>
          )
        })}
      </div>
      {data.summary && (
        <div className="bg-primary-50 rounded-xl p-4 border border-primary-100">
          <p className="text-sm font-semibold text-primary-700 mb-1">Synthèse</p>
          <p className="text-sm text-primary-800 leading-relaxed">{renderVal(data.summary)}</p>
        </div>
      )}
    </div>
  )
}

// ── TAM/SAM/SOM ───────────────────────────────────────────────────────────────
function TamGrid({ data }: { data: NonNullable<DeepAnalysisResult['frameworks']['tam_sam_som']> }) {
  const markets = [
    { key: 'tam' as const, label: 'TAM', sublabel: 'Marché Total Adressable', color: 'from-blue-500 to-blue-700' },
    { key: 'sam' as const, label: 'SAM', sublabel: 'Marché Disponible', color: 'from-primary-500 to-primary-700' },
    { key: 'som' as const, label: 'SOM', sublabel: 'Marché Obtenable', color: 'from-emerald-500 to-emerald-700' },
  ]
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {markets.map((m) => {
          const entry = data[m.key]
          if (!entry) return null
          return (
            <div key={m.key} className="glass-card rounded-xl p-5">
              <div
                className={`inline-flex px-3 py-1 rounded-lg bg-gradient-to-r ${m.color} text-white text-xs font-bold uppercase tracking-wider mb-3`}
              >
                {m.label}
              </div>
              <p className="text-xs text-surface-400 mb-1">{m.sublabel}</p>
              <p className="text-2xl font-extrabold text-surface-900 tracking-tight">
                {entry.value_usd ? fmtUsd(entry.value_usd) : 'N/A'}
              </p>
              <p className="text-sm text-surface-500 mt-2 leading-relaxed">{entry.description}</p>
            </div>
          )
        })}
      </div>
      {data.methodology && (
        <div className="bg-surface-50 rounded-xl p-4">
          <p className="text-xs font-bold uppercase tracking-wider text-surface-400 mb-1">Méthodologie</p>
          <p className="text-sm text-surface-600 leading-relaxed">{data.methodology}</p>
        </div>
      )}
      {data.summary && (
        <div className="bg-primary-50 rounded-xl p-4 border border-primary-100">
          <p className="text-sm font-semibold text-primary-700 mb-1">Synthèse</p>
          <p className="text-sm text-primary-800 leading-relaxed">{data.summary}</p>
        </div>
      )}
    </div>
  )
}

// ── BCG Matrix ────────────────────────────────────────────────────────────────
function BcgCard({ data }: { data: NonNullable<DeepAnalysisResult['frameworks']['bcg']> }) {
  const cfg = BCG_CONFIG[data.position] || BCG_CONFIG.question_mark
  const BcgIcon = cfg.icon
  return (
    <div className="space-y-4">
      <div className={`inline-flex items-center gap-3 px-4 py-3 rounded-xl ${cfg.bg} border border-current/10`}>
        <div className={`w-10 h-10 rounded-xl ${cfg.bg} flex items-center justify-center`}>
          <BcgIcon size={20} className={cfg.color} />
        </div>
        <div>
          <p className={`text-lg font-extrabold ${cfg.color}`}>{cfg.label}</p>
          <p className="text-xs text-surface-500">{cfg.desc}</p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-surface-50 rounded-xl p-4">
          <p className="text-xs font-bold uppercase tracking-wider text-surface-400 mb-1">Part de marché relative</p>
          <p className="text-2xl font-extrabold text-surface-900">{(data.x_market_share * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-surface-50 rounded-xl p-4">
          <p className="text-xs font-bold uppercase tracking-wider text-surface-400 mb-1">Croissance du marché</p>
          <p className="text-2xl font-extrabold text-surface-900">{(data.y_market_growth * 100).toFixed(1)}%</p>
        </div>
      </div>
      {data.justification && (
        <div className="bg-primary-50 rounded-xl p-4 border border-primary-100">
          <p className="text-sm text-primary-800 leading-relaxed">{data.justification}</p>
        </div>
      )}
      {/* Visual BCG quadrant */}
      <div className="relative h-56 bg-surface-50 rounded-2xl overflow-hidden border border-surface-200">
        <div className="absolute inset-0 grid grid-cols-2 grid-rows-2 text-[10px] font-semibold uppercase tracking-widest">
          <div className="flex items-start justify-start p-3 text-yellow-500 border-r border-b border-surface-200">
            Étoile
          </div>
          <div className="flex items-start justify-end p-3 text-blue-500 border-b border-surface-200">Dilemme</div>
          <div className="flex items-end justify-start p-3 text-emerald-500 border-r border-surface-200">
            Vache à lait
          </div>
          <div className="flex items-end justify-end p-3 text-surface-400">Poids mort</div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 flex justify-between px-4 pb-1 text-[9px] text-surface-400">
          <span>Faible part de marché</span>
          <span>Forte part de marché</span>
        </div>
        <div
          className="absolute w-5 h-5 rounded-full border-2 border-white shadow-lg"
          style={{
            left: `${Math.min(95, Math.max(5, data.x_market_share * 100))}%`,
            top: `${Math.min(90, Math.max(10, 100 - data.y_market_growth * 100))}%`,
            transform: 'translate(-50%, -50%)',
            backgroundColor: cfg.dotHex,
          }}
        />
      </div>
    </div>
  )
}

// ── Share Email Modal ─────────────────────────────────────────────────────────
function ShareModal({
  onClose,
  onSend,
  sending,
  sendResult,
}: {
  onClose: () => void
  onSend: (emails: string[]) => void
  sending: boolean
  sendResult: { sent: number; failed: number } | null
}) {
  const [emailInput, setEmailInput] = useState('')
  const [emailList, setEmailList] = useState<string[]>([])
  const [savedRecipients, setSavedRecipients] = useState<EmailRecipient[]>([])
  const [selectedRecipientIds, setSelectedRecipientIds] = useState<string[]>([])

  useEffect(() => {
    settingsApi.getEmailRecipients().then((res) => {
      const data = (res as { data: EmailRecipient[] }).data || []
      setSavedRecipients(data)
    }).catch(() => {})
  }, [])

  const addEmail = () => {
    const email = emailInput.trim()
    if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && !emailList.includes(email)) {
      setEmailList([...emailList, email])
      setEmailInput('')
    }
  }

  const removeEmail = (e: string) => setEmailList(emailList.filter((x) => x !== e))
  const toggleRecipient = (id: string) => {
    setSelectedRecipientIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  const handleSend = () => {
    const allEmails = [...emailList]
    // Add selected saved recipients' emails
    savedRecipients.forEach((r) => {
      if (selectedRecipientIds.includes(r.id) && !allEmails.includes(r.email)) {
        allEmails.push(r.email)
      }
    })
    if (allEmails.length > 0) onSend(allEmails)
  }

  const totalSelected = emailList.length + selectedRecipientIds.length

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden animate-fade-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-100">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
              <Mail size={16} className="text-white" />
            </div>
            <h3 className="text-base font-bold text-surface-900">Partager l&apos;analyse par email</h3>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-surface-100 transition-colors">
            <X size={18} className="text-surface-400" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4 max-h-[60vh] overflow-y-auto">
          {/* Saved recipients */}
          {savedRecipients.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-surface-400 mb-2">
                Destinataires enregistrés
              </p>
              <div className="space-y-1.5">
                {savedRecipients.map((r) => (
                  <label
                    key={r.id}
                    className={`flex items-center gap-3 px-3 py-2 rounded-xl cursor-pointer transition-colors ${
                      selectedRecipientIds.includes(r.id) ? 'bg-primary-50 border border-primary-200' : 'bg-surface-50 border border-transparent hover:bg-surface-100'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedRecipientIds.includes(r.id)}
                      onChange={() => toggleRecipient(r.id)}
                      className="rounded border-surface-300 text-primary-500 focus:ring-primary-300"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-surface-800 truncate">{r.name || r.email}</p>
                      {r.name && <p className="text-[10px] text-surface-400">{r.email}</p>}
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Manual email input */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-surface-400 mb-2">
              Ajouter un email
            </p>
            <div className="flex gap-2">
              <input
                type="email"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addEmail())}
                placeholder="email@exemple.com"
                className="flex-1 px-3 py-2 rounded-xl border border-surface-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-primary-400"
              />
              <button
                onClick={addEmail}
                className="px-3 py-2 bg-surface-100 rounded-xl hover:bg-surface-200 transition-colors"
              >
                <Plus size={16} className="text-surface-600" />
              </button>
            </div>
            {emailList.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {emailList.map((e) => (
                  <span
                    key={e}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-primary-50 text-primary-700 text-xs font-medium"
                  >
                    {e}
                    <button onClick={() => removeEmail(e)} className="hover:text-red-500 transition-colors">
                      <X size={12} />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Send result */}
          {sendResult && (
            <div
              className={`rounded-xl px-4 py-3 text-sm ${
                sendResult.failed === 0
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border border-amber-200'
              }`}
            >
              <div className="flex items-center gap-2">
                <Check size={16} />
                <span>
                  {sendResult.sent} email{sendResult.sent > 1 ? 's' : ''} envoyé{sendResult.sent > 1 ? 's' : ''}
                  {sendResult.failed > 0 && ` · ${sendResult.failed} échoué${sendResult.failed > 1 ? 's' : ''}`}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-surface-100 flex items-center justify-between">
          <p className="text-xs text-surface-400">
            {totalSelected} destinataire{totalSelected > 1 ? 's' : ''} sélectionné{totalSelected > 1 ? 's' : ''}
          </p>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-surface-600 rounded-xl hover:bg-surface-100 transition-colors"
            >
              Fermer
            </button>
            <button
              onClick={handleSend}
              disabled={sending || totalSelected === 0}
              className="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-primary-500 to-primary-700 text-white text-sm font-semibold rounded-xl hover:from-primary-600 hover:to-primary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
            >
              {sending ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Send size={14} />
              )}
              Envoyer
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────────────────
export default function ProductAnalysisPage() {
  const [selectedHs, setSelectedHs] = useState('61')
  const [selectedYear, setSelectedYear] = useState(CURRENT_YEAR)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<DeepAnalysisResult | null>(null)
  const [error, setError] = useState('')

  // Share & PDF state
  const [showShareModal, setShowShareModal] = useState(false)
  const [sending, setSending] = useState(false)
  const [sendResult, setSendResult] = useState<{ sent: number; failed: number } | null>(null)
  const [downloadingPdf, setDownloadingPdf] = useState(false)

  const handleSearch = async () => {
    setLoading(true)
    setError('')
    setResult(null)
    setSendResult(null)
    try {
      const res = await tradeApi.deepAnalysis({ hs_code: selectedHs, year: selectedYear })
      setResult(res.data)
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      setError(e?.response?.data?.detail || "Erreur lors de l'analyse. Vérifiez que le backend est démarré.")
    } finally {
      setLoading(false)
    }
  }

  const handleShareEmail = useCallback(
    async (emails: string[]) => {
      if (!result) return
      setSending(true)
      setSendResult(null)
      try {
        const res = await tradeApi.shareAnalysis({
          hs_code: result.hs_code,
          year: result.year,
          extra_emails: emails,
        })
        setSendResult({ sent: res.data.sent, failed: res.data.failed })
      } catch {
        setSendResult({ sent: 0, failed: emails.length })
      } finally {
        setSending(false)
      }
    },
    [result],
  )

  const handleDownloadPdf = useCallback(async () => {
    if (!result) return
    setDownloadingPdf(true)
    try {
      const res = await tradeApi.downloadAnalysisPdf({ hs_code: result.hs_code, year: result.year })
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `CTTH_Analyse_${result.hs_code}_${result.year}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      setError('Erreur lors de la génération du PDF. Vérifiez que WeasyPrint est installé sur le serveur.')
    } finally {
      setDownloadingPdf(false)
    }
  }, [result])

  const trend_data =
    result?.trade_trend.map((p) => ({
      period: String(p.year),
      exports: p.export_usd,
      imports: p.import_usd,
    })) ?? []

  const trendIsUp = result ? result.trend_pct > 0 : null
  const TrendIcon = trendIsUp === true ? TrendingUp : trendIsUp === false ? TrendingDown : Minus
  const trendColor =
    trendIsUp === true ? 'text-emerald-600' : trendIsUp === false ? 'text-red-500' : 'text-surface-400'
  const trendBg = trendIsUp === true ? 'bg-emerald-50' : trendIsUp === false ? 'bg-red-50' : 'bg-surface-100'
  const balancePositive = result ? result.trade_balance_usd >= 0 : true

  // ── Trend probability from LLM ─────────────────────────────────────────────
  const trendProb = result?.frameworks?.trend_probability
  const upwardPct = trendProb?.upward_pct ?? (trendIsUp ? Math.min(95, 50 + Math.abs(result?.trend_pct ?? 0)) : Math.max(5, 50 - Math.abs(result?.trend_pct ?? 0)))

  // ── Market segmentation from LLM ───────────────────────────────────────────
  const segmentation = result?.frameworks?.market_segmentation
  const segments = segmentation?.segments ?? []
  const segmentPieData = segments.map((s) => ({ label: s.name, value: s.share_pct }))

  // ── Leader companies from LLM ──────────────────────────────────────────────
  const leaderCompanies = result?.frameworks?.leader_companies ?? []

  // ── Export / Import partners split ─────────────────────────────────────────
  const exportPartners = result?.export_partners ?? []
  const importPartners = result?.import_partners ?? []

  // ── Competitive events ─────────────────────────────────────────────────────
  const competitiveEvents = result?.competitive_events ?? []

  return (
    <div className="space-y-6">
      {/* Share Modal */}
      {showShareModal && (
        <ShareModal
          onClose={() => { setShowShareModal(false); setSendResult(null) }}
          onSend={handleShareEmail}
          sending={sending}
          sendResult={sendResult}
        />
      )}

      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-surface-900 tracking-tight">Analyse Produit</h1>
          <p className="text-sm text-surface-500 mt-1.5">
            Plongée profonde sur un produit textile — données commerciales, frameworks stratégiques &amp;
            recommandations IA
          </p>
        </div>
      </div>

      {/* Search Form */}
      <Card title="Sélection du produit" subtitle="Choisissez un chapitre SH et une année pour lancer l'analyse IA">
        <div className="flex flex-col sm:flex-row gap-4 items-end">
          <div className="flex-1">
            <label className="text-xs font-semibold uppercase tracking-wider text-surface-500 mb-2 block">
              Chapitre SH (Produit)
            </label>
            <select
              value={selectedHs}
              onChange={(e) => setSelectedHs(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-surface-200 bg-white text-surface-800 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-primary-400 transition-all"
            >
              {HS_CHAPTERS.map((c) => (
                <option key={c.code} value={c.code}>
                  CH. {c.code} — {c.label}
                </option>
              ))}
            </select>
          </div>
          <div className="w-40">
            <label className="text-xs font-semibold uppercase tracking-wider text-surface-500 mb-2 block">Année</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="w-full px-4 py-2.5 rounded-xl border border-surface-200 bg-white text-surface-800 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-primary-400 transition-all"
            >
              {YEARS.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-primary-500 to-primary-700 text-white text-sm font-semibold rounded-xl hover:from-primary-600 hover:to-primary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm whitespace-nowrap"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Search size={16} />
            )}
            Lancer l&apos;analyse
          </button>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-5 py-4 text-sm">{error}</div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="glass-card rounded-2xl p-12 flex flex-col items-center justify-center gap-4">
          <LoadingSpinner />
          <div className="text-center">
            <p className="text-surface-800 font-semibold">Analyse en cours…</p>
            <p className="text-surface-400 text-sm mt-1">
              Collecte des données commerciales + génération des frameworks IA (30–60 s)
            </p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="space-y-6 animate-slide-up">
          {/* Result header + action buttons */}
          <div className="glass-card rounded-2xl px-6 py-5 flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-6">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 flex-wrap">
                <span className="px-3 py-1 rounded-lg bg-primary-100 text-primary-700 text-xs font-bold uppercase tracking-wider">
                  HS {result.hs_code}
                </span>
                <span className="px-3 py-1 rounded-lg bg-surface-100 text-surface-600 text-xs font-semibold">
                  {result.year}
                </span>
              </div>
              <h2 className="text-xl font-extrabold text-surface-900 mt-2 tracking-tight">
                {result.hs_description}
              </h2>
            </div>
            {/* Action buttons */}
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={() => { setShowShareModal(true); setSendResult(null) }}
                className="flex items-center gap-2 px-4 py-2 bg-surface-50 border border-surface-200 text-surface-700 text-sm font-medium rounded-xl hover:bg-surface-100 hover:border-surface-300 transition-all"
              >
                <Mail size={14} />
                Partager
              </button>
              <button
                onClick={handleDownloadPdf}
                disabled={downloadingPdf}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-500 to-primary-700 text-white text-sm font-semibold rounded-xl hover:from-primary-600 hover:to-primary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
              >
                {downloadingPdf ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Download size={14} />
                )}
                PDF
              </button>
            </div>
          </div>

          {/* ═══ 1. KPI cards ═══ */}
          <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
            {[
              {
                label: 'Exports',
                value: result.export_formatted || fmtUsd(result.export_total_usd),
                icon: ArrowUpRight,
                gradient: 'from-emerald-500 to-green-600',
              },
              {
                label: 'Imports',
                value: result.import_formatted || fmtUsd(result.import_total_usd),
                icon: ArrowDownRight,
                gradient: 'from-amber-500 to-orange-600',
              },
              {
                label: 'Balance commerciale',
                value: fmtUsd(result.trade_balance_usd),
                icon: balancePositive ? TrendingUp : TrendingDown,
                gradient: balancePositive ? 'from-primary-500 to-primary-700' : 'from-red-500 to-red-700',
              },
              {
                label: 'Tendance export',
                value: `${result.trend_pct > 0 ? '+' : ''}${result.trend_pct}%`,
                icon: TrendIcon,
                gradient: trendIsUp
                  ? 'from-emerald-500 to-emerald-700'
                  : trendIsUp === false
                    ? 'from-red-500 to-red-700'
                    : 'from-surface-400 to-surface-600',
              },
            ].map((kpi, i) => {
              const KIcon = kpi.icon
              return (
                <div key={i} className="group glass-card glass-card-hover rounded-2xl p-5 relative overflow-hidden">
                  <div
                    className={`absolute -top-6 -right-6 w-20 h-20 rounded-full bg-gradient-to-br ${kpi.gradient} opacity-[0.07] group-hover:opacity-[0.12] transition-opacity duration-500`}
                  />
                  <div className="relative z-10">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-semibold uppercase tracking-wider text-surface-400">{kpi.label}</p>
                      <div
                        className={`w-8 h-8 rounded-xl bg-gradient-to-br ${kpi.gradient} flex items-center justify-center shadow-sm`}
                      >
                        <KIcon size={14} className="text-white" />
                      </div>
                    </div>
                    <p className="text-2xl font-extrabold text-surface-900 tracking-tight">{kpi.value}</p>
                  </div>
                </div>
              )
            })}
          </div>

          {/* ═══ 2. Trend chart + Probability indicator ═══ */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2">
              <Card
                title="Évolution Export / Import"
                subtitle={`Tendance sur ${result.trade_trend.length} années`}
              >
                {trend_data.length > 0 ? (
                  <AreaTrendChart data={trend_data} />
                ) : (
                  <div className="h-48 flex items-center justify-center text-surface-400 text-sm">
                    Données de tendance non disponibles
                  </div>
                )}
              </Card>
            </div>
            <div className="glass-card rounded-2xl p-6 flex flex-col items-center justify-center gap-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-surface-400">
                Probabilité de tendance haussière
              </p>

              {/* Big circular indicator */}
              <div className="relative w-32 h-32">
                <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                  <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" strokeWidth="2.5" />
                  <circle
                    cx="18"
                    cy="18"
                    r="15.9"
                    fill="none"
                    stroke={upwardPct >= 50 ? '#059669' : '#ef4444'}
                    strokeWidth="2.5"
                    strokeDasharray={`${upwardPct} ${100 - upwardPct}`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <TrendIcon size={20} className={trendColor} />
                  <p className={`text-2xl font-extrabold ${upwardPct >= 50 ? 'text-emerald-600' : 'text-red-500'} mt-0.5`}>
                    {upwardPct}%
                  </p>
                </div>
              </div>

              <div className="text-center">
                <p className={`text-base font-bold capitalize ${trendColor}`}>{result.trend_direction}</p>
                <p className="text-xs text-surface-400 mt-1">Vs année précédente (exports)</p>
              </div>

              {trendProb?.justification && (
                <p className="text-xs text-surface-500 text-center leading-relaxed mt-1 px-2">
                  {trendProb.justification}
                </p>
              )}
            </div>
          </div>

          {/* ═══ 3. Export & Import Partners (side by side) ═══ */}
          {(exportPartners.length > 0 || importPartners.length > 0) && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              {exportPartners.length > 0 && (
                <Section title="Destinations Export" icon={ArrowUpRight} defaultOpen={true}>
                  <BarChartWidget
                    data={exportPartners.map((p) => ({ label: p.label || 'N/A', value: Number(p.value) || 0 }))}
                    layout="horizontal"
                    color="#059669"
                  />
                </Section>
              )}
              {importPartners.length > 0 && (
                <Section title="Sources Import" icon={ArrowDownRight} defaultOpen={true}>
                  <BarChartWidget
                    data={importPartners.map((p) => ({ label: p.label || 'N/A', value: Number(p.value) || 0 }))}
                    layout="horizontal"
                    color="#f59e0b"
                  />
                </Section>
              )}
            </div>
          )}

          {/* Fallback: combined top partners if no split */}
          {exportPartners.length === 0 && importPartners.length === 0 && result.top_partners.length > 0 && (
            <Section title="Top Partenaires Commerciaux" icon={Globe}>
              <BarChartWidget
                data={result.top_partners.map((p) => ({ label: p.label || 'N/A', value: Number(p.value) || 0 }))}
                layout="horizontal"
              />
            </Section>
          )}

          {/* ═══ 4. Market Segmentation ═══ */}
          {segments.length > 0 && (
            <Section title="Segmentation du Marché" icon={PieChart}>
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {/* Pie chart */}
                <div>
                  <PieChartWidget data={segmentPieData} />
                </div>

                {/* Segment cards */}
                <div className="space-y-3">
                  {segments.map((seg, i) => (
                    <div key={i} className="bg-surface-50 rounded-xl p-4 flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-[10px] font-extrabold text-white">{seg.share_pct}%</span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-bold text-surface-800">{seg.name}</p>
                          {seg.growth && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-600 text-[10px] font-bold">
                              <TrendingUp size={10} />
                              {seg.growth}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-surface-500 mt-1 leading-relaxed">{seg.description}</p>
                        {seg.size_usd > 0 && (
                          <p className="text-xs font-semibold text-surface-600 mt-1">
                            Taille : {fmtUsd(seg.size_usd)}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                  {segmentation?.summary && (
                    <div className="bg-primary-50 rounded-xl p-4 border border-primary-100">
                      <p className="text-sm text-primary-800 leading-relaxed">{segmentation.summary}</p>
                    </div>
                  )}
                </div>
              </div>
            </Section>
          )}

          {/* ═══ 5. Leader Companies ═══ */}
          {leaderCompanies.length > 0 && (
            <Section title="Entreprises Leaders" icon={Award}>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {leaderCompanies.map((comp, i) => (
                  <div key={i} className="bg-surface-50 rounded-xl p-4 relative overflow-hidden group hover:shadow-md transition-shadow">
                    <div className="absolute -top-4 -right-4 w-14 h-14 rounded-full bg-primary-500 opacity-[0.05] group-hover:opacity-[0.10] transition-opacity" />
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${i < 3 ? 'bg-gradient-to-br from-yellow-400 to-amber-500' : 'bg-gradient-to-br from-surface-300 to-surface-400'}`}>
                        <span className="text-xs font-extrabold text-white">#{i + 1}</span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-bold text-surface-800 truncate">{comp.name}</p>
                        <p className="text-[10px] text-surface-400 uppercase tracking-wider">{comp.country}</p>
                      </div>
                      {comp.market_share_pct > 0 && (
                        <span className="px-2 py-0.5 rounded-md bg-primary-50 text-primary-700 text-[10px] font-bold flex-shrink-0">
                          {comp.market_share_pct}%
                        </span>
                      )}
                    </div>
                    {comp.strengths && (
                      <p className="text-xs text-surface-500 leading-relaxed mt-1">{comp.strengths}</p>
                    )}
                    {comp.description && comp.description !== comp.strengths && (
                      <p className="text-xs text-surface-400 leading-relaxed mt-1 line-clamp-2">{comp.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* ═══ 6. PESTEL ═══ */}
          {result.frameworks.pestel && (
            <Section title="Analyse PESTEL" icon={Activity}>
              <PestelGrid data={result.frameworks.pestel} />
            </Section>
          )}

          {/* ═══ 7. TAM / SAM / SOM ═══ */}
          {result.frameworks.tam_sam_som && (
            <Section title="Taille de Marché — TAM / SAM / SOM" icon={Target}>
              <TamGrid data={result.frameworks.tam_sam_som} />
            </Section>
          )}

          {/* ═══ 8. Porter ═══ */}
          {result.frameworks.porter && (
            <Section title="Forces de Porter" icon={Shield}>
              <PorterGrid data={result.frameworks.porter as Record<string, unknown>} />
            </Section>
          )}

          {/* ═══ 9. BCG ═══ */}
          {result.frameworks.bcg && (
            <Section title="Matrice BCG" icon={Star}>
              <BcgCard data={result.frameworks.bcg} />
            </Section>
          )}

          {/* ═══ 10. Competitive Events & News (side by side) ═══ */}
          {(competitiveEvents.length > 0 || result.recent_news.length > 0) && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              {/* Competitive Events */}
              {competitiveEvents.length > 0 && (
                <Section title="Événements Concurrentiels" icon={Zap} defaultOpen={true}>
                  <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                    {competitiveEvents.map((evt, idx) => (
                      <div key={idx} className="bg-surface-50 rounded-xl p-3 hover:bg-surface-100 transition-colors">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <Badge type={evt.event_type || 'industry'} label={evt.event_type || 'Événement'} />
                          {evt.company && (
                            <span className="text-[10px] font-semibold text-surface-500 uppercase tracking-wider">
                              {evt.company}
                            </span>
                          )}
                          {evt.date && (
                            <span className="text-[10px] text-surface-400 flex items-center gap-1">
                              <Calendar size={10} />
                              {evt.date}
                            </span>
                          )}
                        </div>
                        <p className="text-sm font-medium text-surface-800">{evt.title}</p>
                        {evt.description && (
                          <p className="text-xs text-surface-500 mt-1 line-clamp-2">{evt.description}</p>
                        )}
                        {evt.source_url && (
                          <a
                            href={evt.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[10px] text-primary-500 hover:text-primary-700 mt-1.5 transition-colors"
                          >
                            <ExternalLink size={10} />
                            {evt.source_name || 'Source'}
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {/* News */}
              {result.recent_news.length > 0 && (
                <Section title="Actualités & Tendances" icon={Newspaper} defaultOpen={true}>
                  <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                    {result.recent_news.map((news, idx) => (
                      <div
                        key={idx}
                        className="bg-surface-50 rounded-xl p-3 hover:bg-surface-100 transition-colors group/item"
                      >
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          {news.category && <Badge type={news.category} />}
                          {news.published_at && (
                            <span className="text-[10px] text-surface-400 flex items-center gap-1">
                              <Calendar size={10} />
                              {new Date(news.published_at).toLocaleDateString('fr-FR', {
                                day: 'numeric',
                                month: 'short',
                                year: 'numeric',
                              })}
                            </span>
                          )}
                        </div>
                        <p className="text-sm font-medium text-surface-800 group-hover/item:text-primary-700 transition-colors">
                          {news.title}
                        </p>
                        {news.summary && (
                          <p className="text-xs text-surface-500 mt-1 line-clamp-2">{news.summary}</p>
                        )}
                        <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                          {news.source_url ? (
                            <a
                              href={news.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-[10px] text-primary-500 hover:text-primary-700 transition-colors"
                            >
                              <ExternalLink size={10} />
                              {news.source_name || 'Source'}
                            </a>
                          ) : (
                            news.source_name && (
                              <span className="text-[10px] text-surface-400">{news.source_name}</span>
                            )
                          )}
                          {news.tags &&
                            news.tags.slice(0, 3).map((tag, ti) => (
                              <span
                                key={ti}
                                className="text-[10px] text-surface-400 bg-surface-100 px-1.5 py-0.5 rounded"
                              >
                                {tag}
                              </span>
                            ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </Section>
              )}
            </div>
          )}

          {/* ═══ 11. Recommendations + Strategic Projection ═══ */}
          {result.frameworks.recommendations && result.frameworks.recommendations.length > 0 && (
            <Section title="Recommandations Stratégiques" icon={Lightbulb}>
              <div className="space-y-3">
                {result.frameworks.recommendations.map((rec, i) => (
                  <div key={i} className="flex items-start gap-3 bg-surface-50 rounded-xl p-4">
                    <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-[10px] font-extrabold text-white">{i + 1}</span>
                    </div>
                    <p className="text-sm text-surface-700 leading-relaxed">{rec}</p>
                  </div>
                ))}
                {result.frameworks.strategic_projection && (
                  <div className="bg-gradient-to-r from-primary-50 to-accent-50 rounded-xl p-5 border border-primary-100">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp size={16} className="text-primary-600" />
                      <p className="text-sm font-bold text-primary-700">Projection stratégique (3–5 ans)</p>
                    </div>
                    <p className="text-sm text-surface-700 leading-relaxed">
                      {result.frameworks.strategic_projection}
                    </p>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* ═══ Companies from DB (if any) ═══ */}
          {result.companies && result.companies.length > 0 && leaderCompanies.length === 0 && (
            <Section title="Entreprises du Secteur" icon={Building2} defaultOpen={false}>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                {result.companies.map((comp, i) => (
                  <div key={i} className="bg-surface-50 rounded-xl p-4">
                    <p className="text-sm font-bold text-surface-800">{comp.name}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {comp.country && (
                        <span className="text-[10px] text-surface-400 uppercase tracking-wider">
                          {comp.country}
                          {comp.city ? `, ${comp.city}` : ''}
                        </span>
                      )}
                      {comp.market_share_pct && (
                        <span className="px-1.5 py-0.5 rounded-md bg-primary-50 text-primary-700 text-[10px] font-bold">
                          {comp.market_share_pct}% part
                        </span>
                      )}
                    </div>
                    {comp.description && (
                      <p className="text-xs text-surface-500 mt-2 line-clamp-3">{comp.description}</p>
                    )}
                    {comp.website && (
                      <a
                        href={comp.website.startsWith('http') ? comp.website : `https://${comp.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[10px] text-primary-500 hover:text-primary-700 mt-1.5 transition-colors"
                      >
                        <ExternalLink size={10} />
                        Site web
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <div className="glass-card rounded-2xl py-20 flex flex-col items-center justify-center gap-4 text-center">
          <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center">
            <Search size={28} className="text-primary-400" />
          </div>
          <div>
            <p className="text-surface-700 font-semibold text-lg">Sélectionnez un produit</p>
            <p className="text-surface-400 text-sm mt-1 max-w-sm">
              Choisissez un chapitre SH et une année, puis cliquez sur &laquo; Lancer l&apos;analyse &raquo; pour
              obtenir une analyse complète.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

'use client'

import { useEffect, useRef, useState, type ComponentPropsWithoutRef } from 'react'
import { reportsApi, settingsApi } from '@/lib/api'
import type { Report, EmailRecipient } from '@/types'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  FileText,
  Download,
  Eye,
  X,
  Send,
  Mail,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Calendar,
  Clock,
  FileBarChart,
  TrendingUp,
  Plus,
  Users,
} from 'lucide-react'

const REPORT_TYPES = [
  { key: 'weekly_summary', label: 'Resume Hebdomadaire', icon: Calendar, desc: 'Synthese hebdomadaire des indicateurs cles' },
  { key: 'market_analysis', label: 'Analyse de Marche', icon: FileBarChart, desc: 'Analyse approfondie du marche textile' },
  { key: 'market_research', label: 'Etude de Marche', icon: TrendingUp, desc: 'Rapport complet avec Porter, PESTEL, segmentation' },
  { key: 'regulatory_alert', label: 'Alerte Reglementaire', icon: AlertCircle, desc: 'Veille reglementaire et normative' },
  { key: 'custom', label: 'Rapport Personnalise', icon: Sparkles, desc: 'Rapport sur mesure par IA' },
]

// Custom markdown components for beautiful rendering
const markdownComponents = {
  table: ({ children, ...props }: ComponentPropsWithoutRef<'table'>) => (
    <div className="overflow-x-auto my-4 rounded-xl border border-surface-100">
      <table className="w-full text-sm" {...props}>{children}</table>
    </div>
  ),
  thead: ({ children, ...props }: ComponentPropsWithoutRef<'thead'>) => (
    <thead className="bg-primary-500 text-white" {...props}>{children}</thead>
  ),
  th: ({ children, ...props }: ComponentPropsWithoutRef<'th'>) => (
    <th className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wider" {...props}>{children}</th>
  ),
  td: ({ children, ...props }: ComponentPropsWithoutRef<'td'>) => (
    <td className="px-4 py-2.5 border-b border-surface-100 text-surface-600" {...props}>{children}</td>
  ),
  tr: ({ children, ...props }: ComponentPropsWithoutRef<'tr'>) => (
    <tr className="even:bg-surface-50/50 hover:bg-primary-50/30 transition-colors" {...props}>{children}</tr>
  ),
  blockquote: ({ children }: ComponentPropsWithoutRef<'blockquote'>) => (
    <div className="border-l-4 border-primary-400 bg-primary-50/40 rounded-r-xl px-5 py-3 my-4">
      <div className="text-surface-700 font-medium text-sm leading-relaxed">{children}</div>
    </div>
  ),
  h2: ({ children, ...props }: ComponentPropsWithoutRef<'h2'>) => (
    <h2 className="text-lg font-extrabold text-surface-800 border-b-2 border-primary-100 pb-2 mt-8 mb-3" {...props}>{children}</h2>
  ),
  h3: ({ children, ...props }: ComponentPropsWithoutRef<'h3'>) => (
    <h3 className="text-base font-bold text-surface-700 mt-5 mb-2" {...props}>{children}</h3>
  ),
  hr: (props: ComponentPropsWithoutRef<'hr'>) => (
    <hr className="my-6 border-none h-0.5 bg-gradient-to-r from-primary-300 via-primary-100 to-transparent" {...props} />
  ),
  strong: ({ children, ...props }: ComponentPropsWithoutRef<'strong'>) => (
    <strong className="font-bold text-surface-800" {...props}>{children}</strong>
  ),
  li: ({ children, ...props }: ComponentPropsWithoutRef<'li'>) => (
    <li className="text-surface-600 leading-relaxed mb-1" {...props}>{children}</li>
  ),
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  // Track all polling intervals so they can be cleared on unmount (prevents memory leaks)
  const pollIntervalsRef = useRef<Set<ReturnType<typeof setInterval>>>(new Set())
  const [viewingReport, setViewingReport] = useState<Report | null>(null)

  // Email share modal state
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [emailReportId, setEmailReportId] = useState<string | null>(null)
  const [savedRecipients, setSavedRecipients] = useState<EmailRecipient[]>([])
  const [selectedRecipientIds, setSelectedRecipientIds] = useState<string[]>([])
  const [newEmailInput, setNewEmailInput] = useState('')
  const [newNameInput, setNewNameInput] = useState('')
  const [showAddNew, setShowAddNew] = useState(false)
  const [emailSending, setEmailSending] = useState(false)
  const [emailResult, setEmailResult] = useState<{ ok: boolean; msg: string } | null>(null)

  // Form state
  const [title, setTitle] = useState('')
  const [reportType, setReportType] = useState('market_analysis')
  const [dateFrom, setDateFrom] = useState('2023-01-01')
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0])

  const fetchReports = async () => {
    try {
      const res = await reportsApi.list()
      setReports(res.data)
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    setLoading(true)
    fetchReports().finally(() => setLoading(false))
    // Clean up ALL polling intervals when the component unmounts
    return () => {
      pollIntervalsRef.current.forEach(clearInterval)
      pollIntervalsRef.current.clear()
    }
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    setCreating(true)
    try {
      const res = await reportsApi.create({
        title,
        report_type: reportType,
        parameters: { date_from: dateFrom, date_to: dateTo },
      })

      const reportId = res.data.id

      setReports((prev) => [
        {
          id: reportId,
          title,
          report_type: reportType,
          status: 'pending',
          parameters: { date_from: dateFrom, date_to: dateTo },
          created_at: new Date().toISOString(),
        },
        ...prev,
      ])

      setTitle('')

      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await reportsApi.getStatus(reportId)
          const status = statusRes.data.status

          setReports((prev) =>
            prev.map((r) =>
              r.id === reportId ? { ...r, status } : r
            )
          )

          if (status === 'completed' || status === 'failed') {
            clearInterval(pollInterval)
            pollIntervalsRef.current.delete(pollInterval)
          }
        } catch {
          clearInterval(pollInterval)
          pollIntervalsRef.current.delete(pollInterval)
        }
      }, 4000)
      // Register so we can clear it on page unmount
      pollIntervalsRef.current.add(pollInterval)
    } catch {
      /* ignore */
    } finally {
      setCreating(false)
    }
  }

  const handleView = async (report: Report) => {
    try {
      const res = await reportsApi.get(report.id)
      setViewingReport(res.data)
    } catch {
      /* ignore */
    }
  }

  const handleDownloadPdf = async (reportId: string) => {
    try {
      const res = await reportsApi.downloadPdf(reportId)
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `CTTH_Rapport_${reportId.slice(0, 8)}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch {
      /* ignore */
    }
  }

  const openEmailModal = async (reportId: string) => {
    setEmailReportId(reportId)
    setSelectedRecipientIds([])
    setNewEmailInput('')
    setNewNameInput('')
    setShowAddNew(false)
    setEmailResult(null)
    setShowEmailModal(true)

    // Fetch saved recipients
    try {
      const res = await settingsApi.getEmailRecipients()
      setSavedRecipients(res.data || [])
      // Pre-select all saved recipients
      setSelectedRecipientIds((res.data || []).map((r: EmailRecipient) => r.id))
    } catch {
      setSavedRecipients([])
    }
  }

  const toggleRecipient = (id: string) => {
    setSelectedRecipientIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  const handleAddNewRecipient = async () => {
    if (!newEmailInput.trim()) return
    try {
      const res = await settingsApi.addEmailRecipient({ email: newEmailInput.trim(), name: newNameInput.trim() })
      const newR = res.data
      setSavedRecipients((prev) => [newR, ...prev])
      setSelectedRecipientIds((prev) => [...prev, newR.id])
      setNewEmailInput('')
      setNewNameInput('')
      setShowAddNew(false)
    } catch {
      /* ignore */
    }
  }

  const handleSendEmail = async () => {
    if (!emailReportId) return
    if (selectedRecipientIds.length === 0 && !newEmailInput.trim()) return

    setEmailSending(true)
    setEmailResult(null)

    try {
      const extraEmails = newEmailInput.trim() ? [newEmailInput.trim()] : []

      const res = await reportsApi.sendEmail(emailReportId, {
        recipient_ids: selectedRecipientIds,
        extra_emails: extraEmails,
      })

      const data = res.data
      if (data.sent > 0) {
        setEmailResult({ ok: true, msg: `${data.sent} email(s) envoye(s) avec succes !` })
        setTimeout(() => {
          setShowEmailModal(false)
          setEmailResult(null)
        }, 2500)
      } else {
        setEmailResult({ ok: false, msg: `Echec de l'envoi (${data.failed} erreur(s))` })
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Erreur inconnue'
      setEmailResult({ ok: false, msg: message })
    } finally {
      setEmailSending(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-surface-800 tracking-tight">Centre de Rapports</h1>
        <p className="text-sm text-surface-500 mt-1">
          Generation et gestion des rapports analytiques par IA
        </p>
      </div>

      {/* Report Creator */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-surface-100 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl gradient-primary flex items-center justify-center">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-surface-800">Generer un nouveau rapport</h3>
            <p className="text-[11px] text-surface-400">Choisissez le type et la periode d&apos;analyse</p>
          </div>
        </div>
        <div className="p-6">
          <form onSubmit={handleCreate} className="space-y-5">
            {/* Report type selector */}
            <div>
              <label className="block text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-3">
                Type de rapport
              </label>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {REPORT_TYPES.map((t) => {
                  const Icon = t.icon
                  return (
                    <button
                      key={t.key}
                      type="button"
                      onClick={() => setReportType(t.key)}
                      className={`p-4 rounded-xl text-left transition-all duration-200 border-2 ${reportType === t.key
                          ? 'border-primary-400 bg-primary-50/50 shadow-glow-primary'
                          : 'border-surface-100 hover:border-surface-200 bg-white'
                        }`}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 ${reportType === t.key ? 'gradient-primary' : 'bg-surface-100'
                        }`}>
                        <Icon size={14} className={reportType === t.key ? 'text-white' : 'text-surface-500'} />
                      </div>
                      <p className={`text-xs font-bold ${reportType === t.key ? 'text-primary-700' : 'text-surface-700'}`}>
                        {t.label}
                      </p>
                      <p className="text-[10px] text-surface-400 mt-0.5 leading-relaxed">{t.desc}</p>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Title + Dates */}
            <div className="flex flex-wrap items-end gap-4">
              <div className="flex-1 min-w-[200px]">
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-1.5">
                  Titre du rapport
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  className="input-field w-full"
                  placeholder="Rapport mensuel textile — Fevrier 2026"
                />
              </div>
              <div>
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-1.5">Du</label>
                <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="input-field" />
              </div>
              <div>
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-1.5">Au</label>
                <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="input-field" />
              </div>
              <button
                type="submit"
                disabled={creating}
                className="flex items-center gap-2 px-6 py-3 gradient-primary text-white rounded-xl text-sm font-semibold shadow-glow-primary hover:shadow-lg transition-all duration-200 disabled:opacity-50"
              >
                <Sparkles size={15} className={creating ? 'animate-pulse' : ''} />
                {creating ? 'Generation en cours...' : 'Generer le rapport'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Reports List */}
      <Card title="Rapports generes" subtitle={`${reports.length} rapport(s) disponible(s)`}>
        {loading ? (
          <LoadingSpinner />
        ) : reports.length === 0 ? (
          <div className="flex flex-col items-center py-16">
            <div className="w-16 h-16 rounded-2xl bg-surface-100 flex items-center justify-center mb-4">
              <FileText size={24} className="text-surface-300" />
            </div>
            <p className="text-surface-400 text-sm font-medium">Aucun rapport genere</p>
            <p className="text-surface-300 text-xs mt-1">Creez votre premier rapport ci-dessus</p>
          </div>
        ) : (
          <div className="space-y-2">
            {reports.map((report, idx) => (
              <div
                key={report.id}
                className="flex items-center gap-4 p-4 rounded-xl hover:bg-surface-50/50 transition-all group animate-slide-up"
                style={{ animationDelay: `${idx * 40}ms`, animationFillMode: 'both' }}
              >
                {/* Icon */}
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${report.status === 'completed' ? 'gradient-primary' :
                    report.status === 'generating' ? 'bg-primary-100' :
                      report.status === 'failed' ? 'bg-red-50' : 'bg-surface-100'
                  }`}>
                  <FileText size={16} className={
                    report.status === 'completed' ? 'text-white' :
                      report.status === 'generating' ? 'text-primary-500 animate-pulse' :
                        report.status === 'failed' ? 'text-red-400' : 'text-surface-400'
                  } />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-surface-800 truncate">{report.title}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-[10px] font-medium text-surface-400">
                      {REPORT_TYPES.find((t) => t.key === report.report_type)?.label || report.report_type}
                    </span>
                    <span className="w-1 h-1 rounded-full bg-surface-300" />
                    <span className="text-[10px] text-surface-400">
                      {new Date(report.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </span>
                  </div>
                </div>

                {/* Status */}
                <Badge type={report.status} />

                {/* Actions */}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {report.status === 'completed' && (
                    <>
                      <button
                        onClick={() => handleView(report)}
                        className="p-2 text-surface-400 hover:text-primary-500 hover:bg-primary-50 rounded-lg transition-all"
                        title="Voir le rapport"
                      >
                        <Eye size={16} />
                      </button>
                      <button
                        onClick={() => handleDownloadPdf(report.id)}
                        className="p-2 text-surface-400 hover:text-emerald-500 hover:bg-emerald-50 rounded-lg transition-all"
                        title="Telecharger PDF"
                      >
                        <Download size={16} />
                      </button>
                      <button
                        onClick={() => openEmailModal(report.id)}
                        className="p-2 text-surface-400 hover:text-primary-500 hover:bg-primary-50 rounded-lg transition-all"
                        title="Envoyer par email"
                      >
                        <Send size={16} />
                      </button>
                    </>
                  )}
                  {report.status === 'generating' && (
                    <div className="flex items-center gap-2 px-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary-400 animate-pulse" />
                      <span className="text-xs text-primary-500 font-semibold">Generation...</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Report Viewer Modal */}
      {viewingReport && (
        <div className="fixed inset-0 bg-surface-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Report header with CTTH branding */}
            <div className="gradient-primary px-6 py-5">
              <div className="flex items-center gap-3 mb-4">
                <img
                  src="https://www.ctth.ma/wp-content/uploads/2021/05/logo-CTTH-FINAL-2.jpg"
                  alt="CTTH"
                  className="w-10 h-10 rounded-xl"
                />
                <div>
                  <p className="text-white/80 text-[10px] font-semibold uppercase tracking-wider">CTTH — Rapport Analytique</p>
                  <p className="text-white text-xs mt-0.5">
                    {REPORT_TYPES.find(t => t.key === viewingReport.report_type)?.label}
                    {' · '}
                    {new Date(viewingReport.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })}
                  </p>
                </div>
              </div>
              <h2 className="text-xl font-extrabold text-white tracking-tight">{viewingReport.title}</h2>
            </div>

            {/* Subheader bar */}
            <div className="flex items-center justify-between px-6 py-3 bg-surface-800">
              <div className="flex items-center gap-2">
                <Sparkles size={12} className="text-primary-300" />
                <span className="text-[10px] font-semibold text-surface-300 uppercase tracking-wider">Genere par Intelligence Artificielle</span>
              </div>
              <div className="flex items-center gap-2">
                {viewingReport.id && (
                  <>
                    <button
                      onClick={() => handleDownloadPdf(viewingReport.id)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold text-white/80 hover:text-white bg-white/10 hover:bg-white/20 rounded-lg transition-all"
                    >
                      <Download size={12} /> PDF
                    </button>
                    <button
                      onClick={() => { setViewingReport(null); openEmailModal(viewingReport.id) }}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold text-white/80 hover:text-white bg-white/10 hover:bg-white/20 rounded-lg transition-all"
                    >
                      <Send size={12} /> Email
                    </button>
                  </>
                )}
                <button
                  onClick={() => setViewingReport(null)}
                  className="p-1.5 text-white/60 hover:text-white hover:bg-white/10 rounded-lg transition-all ml-2"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-8 py-6">
              <div className="prose prose-sm max-w-none">
                {viewingReport.content_markdown ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                    {viewingReport.content_markdown}
                  </ReactMarkdown>
                ) : (
                  <div className="flex flex-col items-center py-12">
                    <Clock size={24} className="text-surface-300 mb-3" />
                    <p className="text-surface-400 font-medium">Contenu non disponible</p>
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-3 bg-surface-50 border-t border-surface-100 flex items-center justify-between">
              <p className="text-[10px] text-surface-400">
                &copy; {new Date().getFullYear()} CTTH — Centre Technique du Textile et de l&apos;Habillement
              </p>
              <p className="text-[10px] text-surface-400">
                Rapport ID: {viewingReport.id?.slice(0, 8)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Email Share Modal */}
      {showEmailModal && (
        <div className="fixed inset-0 bg-surface-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-5 border-b border-surface-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center">
                  <Mail size={18} className="text-white" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-surface-800">Partager le rapport</h3>
                  <p className="text-xs text-surface-400 mt-0.5">Selectionnez les destinataires</p>
                </div>
              </div>
            </div>

            <div className="p-6 space-y-4 max-h-[50vh] overflow-y-auto">
              {/* Saved recipients with checkboxes */}
              {savedRecipients.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Users size={14} className="text-surface-400" />
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-surface-400">
                      Destinataires enregistres
                    </span>
                  </div>
                  <div className="space-y-1">
                    {savedRecipients.map((r) => (
                      <label
                        key={r.id}
                        className="flex items-center gap-3 p-3 rounded-xl hover:bg-surface-50 cursor-pointer transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={selectedRecipientIds.includes(r.id)}
                          onChange={() => toggleRecipient(r.id)}
                          className="w-4 h-4 rounded border-surface-300 text-primary-500 focus:ring-primary-500"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-surface-800 truncate">
                            {r.name || r.email}
                          </p>
                          {r.name && (
                            <p className="text-xs text-surface-400 font-mono truncate">{r.email}</p>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Add new recipient inline */}
              {showAddNew ? (
                <div className="bg-surface-50/50 rounded-xl p-4 space-y-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-surface-400">
                    Nouveau destinataire
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newNameInput}
                      onChange={(e) => setNewNameInput(e.target.value)}
                      className="input-field flex-1"
                      placeholder="Nom"
                    />
                    <input
                      type="email"
                      value={newEmailInput}
                      onChange={(e) => setNewEmailInput(e.target.value)}
                      className="input-field flex-1"
                      placeholder="email@exemple.com"
                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleAddNewRecipient}
                      disabled={!newEmailInput.trim()}
                      className="px-3 py-1.5 gradient-primary text-white rounded-lg text-xs font-semibold disabled:opacity-50"
                    >
                      Ajouter et selectionner
                    </button>
                    <button
                      onClick={() => setShowAddNew(false)}
                      className="px-3 py-1.5 text-xs text-surface-500"
                    >
                      Annuler
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowAddNew(true)}
                  className="flex items-center gap-2 text-xs font-semibold text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-xl px-3 py-2 transition-all w-full justify-center"
                >
                  <Plus size={13} />
                  Ajouter un nouveau destinataire
                </button>
              )}

              {emailResult && (
                <div className={`flex items-center gap-2 p-3 rounded-xl text-sm ${emailResult.ok
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-red-50 text-red-700'
                  }`}>
                  {emailResult.ok ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                  {emailResult.msg}
                </div>
              )}
            </div>

            <div className="px-6 py-4 bg-surface-50 border-t border-surface-100 flex items-center justify-between">
              <span className="text-xs text-surface-400">
                {selectedRecipientIds.length} destinataire(s) selectionne(s)
              </span>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="px-4 py-2.5 text-sm font-medium text-surface-600 hover:text-surface-800 transition-colors"
                >
                  Annuler
                </button>
                <button
                  onClick={handleSendEmail}
                  disabled={emailSending || (selectedRecipientIds.length === 0 && !newEmailInput.trim())}
                  className="flex items-center gap-2 px-5 py-2.5 gradient-primary text-white rounded-xl text-sm font-semibold shadow-glow-primary hover:shadow-lg transition-all duration-200 disabled:opacity-50"
                >
                  <Send size={14} className={emailSending ? 'animate-pulse' : ''} />
                  {emailSending ? 'Envoi...' : 'Envoyer'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

'use client'

import { useEffect, useState } from 'react'
import { reportsApi } from '@/lib/api'
import type { Report } from '@/types'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ReactMarkdown from 'react-markdown'
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
} from 'lucide-react'

const REPORT_TYPES = [
  { key: 'weekly_summary', label: 'Résumé Hebdomadaire', icon: Calendar, desc: 'Synthèse hebdomadaire des indicateurs clés' },
  { key: 'market_analysis', label: 'Analyse de Marché', icon: FileBarChart, desc: 'Analyse approfondie du marché textile' },
  { key: 'regulatory_alert', label: 'Alerte Réglementaire', icon: AlertCircle, desc: 'Veille réglementaire et normative' },
  { key: 'custom', label: 'Rapport Personnalisé', icon: Sparkles, desc: 'Rapport sur mesure par IA' },
]

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [viewingReport, setViewingReport] = useState<Report | null>(null)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [emailTo, setEmailTo] = useState('')
  const [emailSending, setEmailSending] = useState(false)
  const [emailResult, setEmailResult] = useState<{ ok: boolean; msg: string } | null>(null)
  const [emailReportId, setEmailReportId] = useState<string | null>(null)

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
          }
        } catch {
          clearInterval(pollInterval)
        }
      }, 3000)
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

  const openEmailModal = (reportId: string) => {
    setEmailReportId(reportId)
    setEmailTo('')
    setEmailResult(null)
    setShowEmailModal(true)
  }

  const handleSendEmail = async () => {
    if (!emailTo.trim() || !emailReportId) return

    setEmailSending(true)
    setEmailResult(null)

    try {
      // Get report content
      const reportRes = await reportsApi.get(emailReportId)
      const report = reportRes.data
      const reportTitle = report.title || 'Rapport CTTH'
      const content = report.content_markdown || 'Rapport en cours de préparation.'

      // Build professional HTML email
      const htmlEmail = buildReportEmail(reportTitle, content, report.report_type, report.created_at)

      const response = await fetch('https://aic-mail-server.vercel.app/api/send-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to: emailTo,
          subject: `📊 CTTH — ${reportTitle}`,
          message: htmlEmail,
          isHtml: true,
        }),
      })

      const result = await response.json()

      if (response.ok) {
        setEmailResult({ ok: true, msg: 'Rapport envoyé avec succès !' })
        setTimeout(() => {
          setShowEmailModal(false)
          setEmailResult(null)
        }, 2000)
      } else {
        setEmailResult({ ok: false, msg: result.error || 'Échec de l\'envoi' })
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Erreur inconnue'
      setEmailResult({ ok: false, msg: message })
    } finally {
      setEmailSending(false)
    }
  }

  const buildReportEmail = (title: string, markdown: string, type?: string, date?: string) => {
    // Convert markdown to basic HTML (headings, bold, lists, paragraphs)
    const htmlContent = markdown
      .replace(/^### (.*$)/gm, '<h3 style="color:#353A3A;font-size:16px;margin:20px 0 8px;">$1</h3>')
      .replace(/^## (.*$)/gm, '<h2 style="color:#353A3A;font-size:18px;margin:24px 0 10px;border-bottom:2px solid #C1DEDB;padding-bottom:8px;">$1</h2>')
      .replace(/^# (.*$)/gm, '<h1 style="color:#353A3A;font-size:22px;margin:28px 0 12px;">$1</h1>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^- (.*)$/gm, '<li style="margin:4px 0;color:#555e5e;">$1</li>')
      .replace(/(<li.*<\/li>\n?)+/g, '<ul style="padding-left:20px;margin:10px 0;">$&</ul>')
      .replace(/\n\n/g, '</p><p style="color:#555e5e;line-height:1.7;margin:10px 0;">')

    const typeLabel = REPORT_TYPES.find(t => t.key === type)?.label || 'Rapport'
    const dateStr = date ? new Date(date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }) : ''

    return `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f0f3f3;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f3f3;padding:40px 20px;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(53,58,58,0.08);">
        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#3fa69c 0%,#58B9AF 50%,#7ddbd3 100%);padding:32px 40px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <img src="https://www.ctth.ma/wp-content/uploads/2021/05/logo-CTTH-FINAL-2.jpg" alt="CTTH" width="48" height="48" style="border-radius:12px;display:block;" />
                </td>
                <td style="padding-left:16px;">
                  <p style="margin:0;font-size:20px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;">CTTH</p>
                  <p style="margin:2px 0 0;font-size:11px;color:rgba(255,255,255,0.8);letter-spacing:1px;text-transform:uppercase;">Centre Technique du Textile et de l&apos;Habillement</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- Title bar -->
        <tr>
          <td style="background:#353A3A;padding:16px 40px;">
            <p style="margin:0;font-size:18px;font-weight:700;color:#ffffff;">${title}</p>
            <p style="margin:6px 0 0;font-size:12px;color:#C1DEDB;">
              ${typeLabel} &nbsp;·&nbsp; ${dateStr} &nbsp;·&nbsp; Généré par IA
            </p>
          </td>
        </tr>
        <!-- Content -->
        <tr>
          <td style="padding:32px 40px;">
            <p style="color:#555e5e;line-height:1.7;margin:0 0 10px;">
              ${htmlContent}
            </p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:#f8fafa;padding:24px 40px;border-top:1px solid #e0e5e5;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <p style="margin:0;font-size:11px;color:#8a9494;">
                    Ce rapport a été généré automatiquement par la plateforme de veille CTTH.
                  </p>
                  <p style="margin:4px 0 0;font-size:11px;color:#8a9494;">
                    © ${new Date().getFullYear()} CTTH — Centre Technique du Textile et de l&apos;Habillement
                  </p>
                </td>
                <td align="right">
                  <a href="https://www.ctth.ma" style="display:inline-block;padding:8px 16px;background:#58B9AF;color:#ffffff;text-decoration:none;border-radius:8px;font-size:12px;font-weight:600;">
                    Visiter ctth.ma
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-surface-800 tracking-tight">Centre de Rapports</h1>
        <p className="text-sm text-surface-500 mt-1">
          Génération et gestion des rapports analytiques par IA
        </p>
      </div>

      {/* Report Creator */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-surface-100 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl gradient-primary flex items-center justify-center">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-surface-800">Générer un nouveau rapport</h3>
            <p className="text-[11px] text-surface-400">Choisissez le type et la période d&apos;analyse</p>
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
                  placeholder="Rapport mensuel textile — Février 2026"
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
                {creating ? 'Génération en cours...' : 'Générer le rapport'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Reports List */}
      <Card title="Rapports générés" subtitle={`${reports.length} rapport(s) disponible(s)`}>
        {loading ? (
          <LoadingSpinner />
        ) : reports.length === 0 ? (
          <div className="flex flex-col items-center py-16">
            <div className="w-16 h-16 rounded-2xl bg-surface-100 flex items-center justify-center mb-4">
              <FileText size={24} className="text-surface-300" />
            </div>
            <p className="text-surface-400 text-sm font-medium">Aucun rapport généré</p>
            <p className="text-surface-300 text-xs mt-1">Créez votre premier rapport ci-dessus</p>
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
                        title="Télécharger PDF"
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
                      <span className="text-xs text-primary-500 font-semibold">Génération...</span>
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
                <span className="text-[10px] font-semibold text-surface-300 uppercase tracking-wider">Généré par Intelligence Artificielle</span>
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
              <div className="prose prose-sm max-w-none prose-headings:text-surface-800 prose-headings:font-extrabold prose-p:text-surface-600 prose-p:leading-relaxed prose-strong:text-surface-800 prose-li:text-surface-600 prose-a:text-primary-600 prose-h2:border-b prose-h2:border-primary-100 prose-h2:pb-2">
                {viewingReport.content_markdown ? (
                  <ReactMarkdown>{viewingReport.content_markdown}</ReactMarkdown>
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
                © {new Date().getFullYear()} CTTH — Centre Technique du Textile et de l&apos;Habillement
              </p>
              <p className="text-[10px] text-surface-400">
                Rapport ID: {viewingReport.id?.slice(0, 8)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Email Modal */}
      {showEmailModal && (
        <div className="fixed inset-0 bg-surface-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-5 border-b border-surface-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center">
                  <Mail size={18} className="text-white" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-surface-800">Envoyer par email</h3>
                  <p className="text-xs text-surface-400 mt-0.5">Le rapport sera envoyé au format HTML professionnel</p>
                </div>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-1.5">
                  Adresse email du destinataire
                </label>
                <input
                  type="email"
                  value={emailTo}
                  onChange={(e) => setEmailTo(e.target.value)}
                  className="input-field"
                  placeholder="exemple@entreprise.com"
                  autoFocus
                />
              </div>

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

            <div className="px-6 py-4 bg-surface-50 border-t border-surface-100 flex items-center justify-end gap-3">
              <button
                onClick={() => setShowEmailModal(false)}
                className="px-4 py-2.5 text-sm font-medium text-surface-600 hover:text-surface-800 transition-colors"
              >
                Annuler
              </button>
              <button
                onClick={handleSendEmail}
                disabled={!emailTo.trim() || emailSending}
                className="flex items-center gap-2 px-5 py-2.5 gradient-primary text-white rounded-xl text-sm font-semibold shadow-glow-primary hover:shadow-lg transition-all duration-200 disabled:opacity-50"
              >
                <Send size={14} className={emailSending ? 'animate-pulse' : ''} />
                {emailSending ? 'Envoi en cours...' : 'Envoyer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

'use client'

import { useEffect, useState } from 'react'
import { settingsApi, schedulerApi } from '@/lib/api'
import type { DataSourceStatus, APIKeyStatus, EmailRecipient, SchedulerStatus } from '@/types'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { RefreshCw, Mail, Plus, Trash2, Clock, Play } from 'lucide-react'

const SOURCE_LABELS: Record<string, string> = {
  eurostat_comext: 'Eurostat (Comext)',
  un_comtrade: 'UN Comtrade',
  federal_register: 'Federal Register',
  openai_search: 'Veille IA (OpenAI)',
  otexa_tradegov: 'OTEXA (trade.gov)',
  market_research_agent: 'Etude de Marche (IA)',
}

export default function SettingsPage() {
  const [sources, setSources] = useState<DataSourceStatus[]>([])
  const [apiKeys, setApiKeys] = useState<APIKeyStatus[]>([])
  const [recipients, setRecipients] = useState<EmailRecipient[]>([])
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState<string | null>(null)
  const [triggeringPipeline, setTriggeringPipeline] = useState(false)

  // Email form state
  const [showAddEmail, setShowAddEmail] = useState(false)
  const [newEmailAddr, setNewEmailAddr] = useState('')
  const [newEmailName, setNewEmailName] = useState('')
  const [addingEmail, setAddingEmail] = useState(false)

  const fetchData = async () => {
    try {
      const [sourcesRes, keysRes, recipientsRes, schedulerRes] = await Promise.all([
        settingsApi.getDataSources(),
        settingsApi.getApiKeys(),
        settingsApi.getEmailRecipients().catch(() => ({ data: [] })),
        schedulerApi.getStatus().catch(() => ({ data: null })),
      ])
      setSources(sourcesRes.data)
      setApiKeys(keysRes.data)
      setRecipients(recipientsRes.data || [])
      if (schedulerRes.data) setScheduler(schedulerRes.data)
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    setLoading(true)
    fetchData().finally(() => setLoading(false))

    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleRefresh = async (sourceName: string) => {
    setRefreshing(sourceName)
    try {
      await settingsApi.refreshSource(sourceName)
      setTimeout(fetchData, 5000)
    } catch {
      /* ignore */
    } finally {
      setTimeout(() => setRefreshing(null), 5000)
    }
  }

  const handleTriggerPipeline = async () => {
    setTriggeringPipeline(true)
    try {
      await schedulerApi.trigger()
      setTimeout(fetchData, 10000)
    } catch {
      /* ignore */
    } finally {
      setTimeout(() => setTriggeringPipeline(false), 10000)
    }
  }

  const handleAddEmail = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newEmailAddr.trim()) return
    setAddingEmail(true)
    try {
      await settingsApi.addEmailRecipient({ email: newEmailAddr.trim(), name: newEmailName.trim() })
      setNewEmailAddr('')
      setNewEmailName('')
      setShowAddEmail(false)
      await fetchData()
    } catch {
      /* ignore */
    } finally {
      setAddingEmail(false)
    }
  }

  const handleDeleteEmail = async (id: string) => {
    try {
      await settingsApi.deleteEmailRecipient(id)
      setRecipients((prev) => prev.filter((r) => r.id !== id))
    } catch {
      /* ignore */
    }
  }

  if (loading) return <LoadingSpinner />

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-surface-900 tracking-tight">Paramètres</h1>
        <p className="text-sm text-surface-500 mt-1.5">
          Gestion des sources de données, emails et configuration
        </p>
      </div>

      {/* Scheduler Status */}
      {scheduler && (
        <Card title="Planificateur Automatique" subtitle="Pipeline quotidien de collecte de données">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${scheduler.running ? 'bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,.4)] animate-pulse' : 'bg-red-400'}`} />
                <span className={`text-sm font-semibold ${scheduler.running ? 'text-emerald-600' : 'text-red-500'}`}>
                  {scheduler.running ? 'Actif' : 'Inactif'}
                </span>
              </div>
              {scheduler.jobs.length > 0 && scheduler.jobs[0].next_run_time && (
                <div className="flex items-center gap-1.5 text-xs text-surface-500">
                  <Clock size={12} />
                  <span>
                    Prochain: {new Date(scheduler.jobs[0].next_run_time).toLocaleString('fr-FR')}
                  </span>
                </div>
              )}
            </div>
            <button
              onClick={handleTriggerPipeline}
              disabled={triggeringPipeline}
              className="flex items-center gap-2 px-4 py-2 gradient-primary text-white rounded-xl text-xs font-semibold shadow-glow-primary hover:shadow-lg transition-all duration-200 disabled:opacity-50"
            >
              <Play size={13} className={triggeringPipeline ? 'animate-pulse' : ''} />
              {triggeringPipeline ? 'En cours...' : 'Lancer maintenant'}
            </button>
          </div>
        </Card>
      )}

      {/* Data Sources */}
      <Card title="Sources de Données" subtitle="Statut de collecte en temps réel">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-100">
                <th className="text-left py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">
                  Source
                </th>
                <th className="text-left py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">
                  Statut
                </th>
                <th className="text-left py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">
                  Dernière MAJ
                </th>
                <th className="text-right py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">
                  Enregistrements
                </th>
                <th className="text-right py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">
                  Appels API
                </th>
                <th className="text-right py-3 px-3 text-[10px] font-semibold uppercase tracking-wider text-surface-400">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source) => (
                <tr
                  key={source.source_name}
                  className="border-b border-surface-50 hover:bg-surface-50/50 transition-colors"
                >
                  <td className="py-3 px-3 font-semibold text-surface-800">
                    {SOURCE_LABELS[source.source_name] || source.source_name}
                  </td>
                  <td className="py-3 px-3">
                    <Badge type={source.status} />
                  </td>
                  <td className="py-3 px-3 text-surface-500">
                    {source.last_successful_fetch
                      ? new Date(
                        source.last_successful_fetch
                      ).toLocaleString('fr-FR')
                      : 'Jamais'}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-surface-600">
                    {source.records_fetched_today}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-surface-600">
                    {source.api_calls_today}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => handleRefresh(source.source_name)}
                      disabled={refreshing === source.source_name}
                      className="p-2 text-surface-400 hover:text-primary-500 hover:bg-primary-50 rounded-lg disabled:opacity-50 transition-all"
                      title="Actualiser"
                    >
                      <RefreshCw
                        size={16}
                        className={
                          refreshing === source.source_name
                            ? 'animate-spin'
                            : ''
                        }
                      />
                    </button>
                  </td>
                </tr>
              ))}

              {sources.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-surface-400">
                    Aucune source configurée. Lancez le script de seed.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Show errors if any */}
        {sources
          .filter((s) => s.last_error_message)
          .map((s) => (
            <div
              key={s.source_name}
              className="mt-3 p-4 bg-red-50/80 border border-red-200/60 rounded-xl text-sm"
            >
              <p className="font-bold text-red-700 text-xs uppercase tracking-wider">
                {SOURCE_LABELS[s.source_name]}:
              </p>
              <p className="text-red-600 text-xs mt-1.5 leading-relaxed">
                {s.last_error_message}
              </p>
            </div>
          ))}
      </Card>

      {/* Email Recipients */}
      <Card title="Destinataires Email" subtitle="Contacts pour le partage de rapports">
        <div className="space-y-3">
          {recipients.map((r) => (
            <div
              key={r.id}
              className="flex items-center justify-between py-3 px-3 border-b border-surface-50 last:border-0 hover:bg-surface-50/30 rounded-lg transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-primary-50 flex items-center justify-center">
                  <Mail size={14} className="text-primary-500" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-surface-800">
                    {r.name || r.email}
                  </p>
                  {r.name && (
                    <p className="text-xs text-surface-400 font-mono mt-0.5">{r.email}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[10px] text-surface-400">
                  {new Date(r.created_at).toLocaleDateString('fr-FR')}
                </span>
                <button
                  onClick={() => handleDeleteEmail(r.id)}
                  className="p-2 text-surface-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                  title="Supprimer"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}

          {recipients.length === 0 && !showAddEmail && (
            <p className="text-center py-8 text-surface-400 text-sm">
              Aucun destinataire enregistré
            </p>
          )}

          {/* Add email form */}
          {showAddEmail ? (
            <form onSubmit={handleAddEmail} className="flex flex-wrap items-end gap-3 p-4 bg-surface-50/50 rounded-xl">
              <div className="flex-1 min-w-[150px]">
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Nom</label>
                <input
                  type="text"
                  value={newEmailName}
                  onChange={(e) => setNewEmailName(e.target.value)}
                  className="input-field w-full"
                  placeholder="Jean Dupont"
                />
              </div>
              <div className="flex-1 min-w-[200px]">
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-surface-400 mb-1">Email</label>
                <input
                  type="email"
                  value={newEmailAddr}
                  onChange={(e) => setNewEmailAddr(e.target.value)}
                  className="input-field w-full"
                  placeholder="email@exemple.com"
                  required
                />
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="submit"
                  disabled={addingEmail || !newEmailAddr.trim()}
                  className="px-4 py-2.5 gradient-primary text-white rounded-xl text-xs font-semibold shadow-glow-primary disabled:opacity-50 transition-all"
                >
                  {addingEmail ? 'Ajout...' : 'Ajouter'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddEmail(false)}
                  className="px-3 py-2.5 text-xs text-surface-500 hover:text-surface-800 transition-colors"
                >
                  Annuler
                </button>
              </div>
            </form>
          ) : (
            <button
              onClick={() => setShowAddEmail(true)}
              className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-xl transition-all w-full justify-center"
            >
              <Plus size={14} />
              Ajouter un destinataire
            </button>
          )}
        </div>
      </Card>

      {/* API Keys */}
      <Card title="Clés API" subtitle="Configuration des accès">
        <div className="space-y-1">
          {apiKeys.map((key) => (
            <div
              key={key.name}
              className="flex items-center justify-between py-3.5 px-1 border-b border-surface-50 last:border-0 hover:bg-surface-50/30 rounded-lg transition-colors"
            >
              <div>
                <p className="text-sm font-semibold text-surface-800">{key.name}</p>
                <p className="text-xs text-surface-400 font-mono mt-1">
                  {key.configured ? key.masked_value : 'Non configurée'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-bold uppercase tracking-wider ${key.configured ? 'text-emerald-500' : 'text-red-400'}`}>
                  {key.configured ? 'Active' : 'Manquante'}
                </span>
                <div
                  className={`w-2.5 h-2.5 rounded-full ${key.configured ? 'bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,.4)]' : 'bg-red-400'
                    }`}
                />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

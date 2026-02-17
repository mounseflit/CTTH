'use client'

import { useEffect, useState } from 'react'
import { settingsApi } from '@/lib/api'
import type { DataSourceStatus, APIKeyStatus } from '@/types'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { RefreshCw } from 'lucide-react'

const SOURCE_LABELS: Record<string, string> = {
  eurostat_comext: 'Eurostat (Comext)',
  un_comtrade: 'UN Comtrade',
  federal_register: 'Federal Register',
  openai_search: 'Veille IA (OpenAI)',
  otexa_tradegov: 'OTEXA (trade.gov)',
}

export default function SettingsPage() {
  const [sources, setSources] = useState<DataSourceStatus[]>([])
  const [apiKeys, setApiKeys] = useState<APIKeyStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      const [sourcesRes, keysRes] = await Promise.all([
        settingsApi.getDataSources(),
        settingsApi.getApiKeys(),
      ])
      setSources(sourcesRes.data)
      setApiKeys(keysRes.data)
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

  if (loading) return <LoadingSpinner />

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-surface-900 tracking-tight">Paramètres</h1>
        <p className="text-sm text-surface-500 mt-1.5">
          Gestion des sources de données et configuration
        </p>
      </div>

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

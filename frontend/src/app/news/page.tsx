'use client'

import { useEffect, useState } from 'react'
import { newsApi } from '@/lib/api'
import type { NewsArticle, NewsPaginatedResponse } from '@/types'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { RefreshCw, ExternalLink } from 'lucide-react'

const CATEGORIES = [
  { key: '', label: 'Tous' },
  { key: 'regulatory', label: 'Réglementaire' },
  { key: 'market', label: 'Marché' },
  { key: 'policy', label: 'Politique' },
  { key: 'trade_agreement', label: 'Accords' },
  { key: 'industry', label: 'Industrie' },
  { key: 'sustainability', label: 'Durabilité' },
]

export default function NewsPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [category, setCategory] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  const fetchArticles = async (p: number = 1) => {
    try {
      const params: Record<string, unknown> = { page: p, per_page: 20 }
      if (category) params.category = category
      if (search) params.search = search

      const res = await newsApi.getArticles(params)
      const result: NewsPaginatedResponse = res.data
      setArticles(result.data)
      setTotal(result.total)
      setPage(result.page)
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    setLoading(true)
    fetchArticles().finally(() => setLoading(false))
  }, [category]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await newsApi.refresh()
      setTimeout(() => {
        fetchArticles()
        setRefreshing(false)
      }, 3000)
    } catch {
      setRefreshing(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    fetchArticles(1).finally(() => setLoading(false))
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-surface-900 tracking-tight">
            Veille & Actualités
          </h1>
          <p className="text-sm text-surface-500 mt-1.5">
            {total} articles collectés
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-5 py-3 gradient-primary text-white rounded-xl text-sm font-semibold shadow-glow-primary hover:shadow-lg transition-all duration-200 disabled:opacity-50"
        >
          <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          Actualiser
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2.5">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.key}
            onClick={() => setCategory(cat.key)}
            className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-200 ${category === cat.key
                ? 'gradient-primary text-white shadow-glow-primary'
                : 'bg-surface-100 text-surface-500 hover:bg-surface-200 hover:text-surface-700'
              }`}
          >
            {cat.label}
          </button>
        ))}

        <form onSubmit={handleSearch} className="ml-auto flex gap-2">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher..."
            className="input-field w-56"
          />
          <button
            type="submit"
            className="px-4 py-2.5 bg-surface-100 text-surface-600 rounded-xl text-sm font-semibold hover:bg-surface-200 transition-colors"
          >
            Chercher
          </button>
        </form>
      </div>

      {/* Articles Grid */}
      {loading ? (
        <LoadingSpinner />
      ) : articles.length === 0 ? (
        <div className="text-center py-16 text-surface-400">
          Aucun article trouvé
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {articles.map((article, idx) => (
            <div
              key={article.id}
              className="glass-card glass-card-hover rounded-2xl p-5 group"
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  {article.category && (
                    <Badge type={article.category} />
                  )}
                  <h3 className="text-sm font-bold text-surface-900 mt-2.5 line-clamp-2 group-hover:text-primary-600 transition-colors">
                    {article.title}
                  </h3>
                  {article.summary && (
                    <p className="text-sm text-surface-500 mt-2 line-clamp-3 leading-relaxed">
                      {article.summary}
                    </p>
                  )}
                </div>
                {article.source_url && (
                  <a
                    href={article.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-surface-300 hover:text-primary-500 flex-shrink-0 transition-colors"
                  >
                    <ExternalLink size={16} />
                  </a>
                )}
              </div>

              {article.tags && article.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {article.tags.slice(0, 4).map((tag, i) => (
                    <span
                      key={i}
                      className="text-[10px] font-semibold uppercase tracking-wider px-2.5 py-1 bg-surface-100 text-surface-400 rounded-lg"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-center justify-between mt-4 pt-3 border-t border-surface-100/80">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-surface-400">
                  {article.source_name}
                </span>
                <span className="text-xs text-surface-400">
                  {article.published_at
                    ? new Date(article.published_at).toLocaleDateString('fr-FR')
                    : ''}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Load more */}
      {articles.length > 0 && articles.length < total && (
        <div className="text-center">
          <button
            onClick={() => fetchArticles(page + 1)}
            className="px-6 py-2.5 text-sm text-primary-600 hover:text-primary-700 font-bold hover:bg-primary-50 rounded-xl transition-all"
          >
            Charger plus...
          </button>
        </div>
      )}
    </div>
  )
}

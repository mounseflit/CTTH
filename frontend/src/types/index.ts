export interface User {
  id: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface KPICard {
  label: string
  value: string
  change_pct: number | null
  period: string
  icon: string
}

export interface TrendDataPoint {
  period: string
  exports: number
  imports: number
}

export interface RecentNewsItem {
  id: string
  title: string
  category: string | null
  source_name: string | null
  published_at: string | null
}

export interface DashboardData {
  kpi_cards: KPICard[]
  trend_data: TrendDataPoint[]
  recent_news: RecentNewsItem[]
  top_partners: { label?: string; partner_name?: string; value: number }[]
  hs_breakdown: { chapter: string; value: number }[]
}

export interface TradeDataRow {
  id: number
  period_date: string
  source: string
  reporter_code: string
  reporter_name: string | null
  partner_code: string
  partner_name: string | null
  hs_code: string
  hs_description: string | null
  flow: string
  value_usd: number | null
  value_eur: number | null
  weight_kg: number | null
  quantity: number | null
  frequency: string
}

export interface TradePaginatedResponse {
  data: TradeDataRow[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface ChartDataPoint {
  label: string
  value: number
  count?: number
}

export interface NewsArticle {
  id: string
  title: string
  summary: string | null
  source_url: string
  source_name: string | null
  category: string | null
  tags: string[]
  published_at: string | null
  relevance_score: number | null
  created_at: string
}

export interface NewsPaginatedResponse {
  data: NewsArticle[]
  total: number
  page: number
  per_page: number
}

export interface Report {
  id: string
  title: string
  report_type: string
  status: 'pending' | 'generating' | 'completed' | 'failed'
  parameters: Record<string, unknown> | null
  content_markdown?: string | null
  created_at: string
  generation_started_at?: string | null
  generation_completed_at?: string | null
}

export interface DataSourceStatus {
  source_name: string
  status: string
  last_successful_fetch: string | null
  last_error_message: string | null
  records_fetched_today: number
  api_calls_today: number
}

export interface APIKeyStatus {
  name: string
  configured: boolean
  masked_value: string | null
}

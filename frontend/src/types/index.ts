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
  source_url: string | null
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

// ── Market Research Types ──────────────────────────────────

export interface MarketOverview {
  total_market_size_usd: number
  market_size_formatted: string
  growth_pct: number | null
  trade_balance_usd: number
  export_total_usd: number
  import_total_usd: number
  segment_count: number
  company_count: number
  insight_count: number
  latest_year: number
}

export interface Segment {
  id: string
  axis: string
  code: string
  label_fr: string
  label_en: string
  parent_code: string | null
  description_fr: string
  market_value: number | null
}

export interface MarketSizePoint {
  year: number
  value_usd: number
  flow: string
  segment_code: string
  geography_code: string
}

export interface MarketSizeSeries {
  data: MarketSizePoint[]
  segment_code: string | null
  geography_code: string | null
}

export interface SWOT {
  strengths: string[]
  weaknesses: string[]
  opportunities: string[]
  threats: string[]
}

export interface Company {
  id: string
  name: string
  country: string
  hq_city: string
  description_fr: string
  swot: SWOT
  financials: Record<string, unknown>
  executives: { name: string; title: string }[]
  website: string
  sector: string
  market_share_pct: number | null
}

export interface MarketShareEntry {
  company_name: string
  share_pct: number
  value_usd: number
}

export interface MarketShare {
  year: number
  segment_code: string
  entries: MarketShareEntry[]
}

export interface CompetitiveEvent {
  id: string
  event_type: string
  company_name: string
  title: string
  description_fr: string
  event_date: string | null
  source_url: string
  source_name: string
}

export interface Insight {
  id: string
  category: string
  title: string
  narrative_fr: string
  droc_type: string | null
  tags: string[]
  created_at: string | null
}

export interface FrameworkResult {
  id: string
  framework_type: string
  content: Record<string, unknown>
  created_at: string | null
}

// ── Email Recipients ──────────────────────────────────────

export interface EmailRecipient {
  id: string
  email: string
  name: string
  created_at: string
}

// ── Deep Product Analysis ─────────────────────────────────

export interface DeepAnalysisTrendPoint {
  year: number
  export_usd: number
  import_usd: number
}

export interface DeepSegment {
  name: string
  share_pct: number
  size_usd: number
  growth: string
  description: string
}

export interface DeepLeaderCompany {
  name: string
  country: string
  market_share_pct: number
  strengths: string
  description: string
}

export interface DeepAnalysisFrameworks {
  pestel?: Record<string, unknown>
  tam_sam_som?: {
    tam?: { value_usd: number; description: string }
    sam?: { value_usd: number; description: string }
    som?: { value_usd: number; description: string }
    methodology?: string
    summary?: string
  }
  porter?: Record<string, unknown>
  bcg?: {
    position: 'star' | 'cash_cow' | 'question_mark' | 'dog'
    x_market_share: number
    y_market_growth: number
    justification: string
  }
  market_segmentation?: {
    segments: DeepSegment[]
    summary?: string
  }
  leader_companies?: DeepLeaderCompany[]
  trend_probability?: {
    upward_pct: number
    justification: string
  }
  recommendations?: string[]
  strategic_projection?: string
}

export interface DeepCompanyInfo {
  name: string
  description: string
  country: string
  city: string
  website: string
  market_share_pct: number | null
  revenue_usd: number | null
}

export interface DeepNewsItem {
  title: string
  summary: string
  source_url: string
  source_name: string
  category: string
  tags: string[]
  published_at: string
}

export interface DeepCompetitiveEvent {
  event_type: string
  company: string
  title: string
  description: string
  date: string
  source_url: string
  source_name: string
}

export interface DeepAnalysisResult {
  hs_code: string
  hs_description: string
  year: number
  export_total_usd: number
  import_total_usd: number
  trade_balance_usd: number
  export_formatted: string
  import_formatted: string
  trade_trend: DeepAnalysisTrendPoint[]
  trend_pct: number
  trend_direction: string
  top_partners: { label: string; value: number }[]
  export_partners: { label: string; value: number }[]
  import_partners: { label: string; value: number }[]
  frameworks: DeepAnalysisFrameworks
  companies: DeepCompanyInfo[]
  recent_news: DeepNewsItem[]
  competitive_events: DeepCompetitiveEvent[]
}

// ── Scheduler ─────────────────────────────────────────────

export interface SchedulerStatus {
  enabled: boolean
  running: boolean
  jobs: { id: string; name: string; next_run_time: string | null; trigger: string }[]
}

export interface PipelineRun {
  id: string
  started_at: string
  completed_at: string | null
  duration_seconds: number | null
  status: string
  phase_results: Record<string, unknown> | null
}

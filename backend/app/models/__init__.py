# Collection name constants for MongoDB
USERS_COL = "users"
TRADE_DATA_COL = "trade_data"
NEWS_COL = "news_articles"
REPORTS_COL = "reports"
SOURCE_STATUS_COL = "data_source_status"

# Market research collections
MARKET_SEGMENTS_COL = "market_segments"
MARKET_SIZE_COL = "market_size_series"
COMPANIES_COL = "companies"
MARKET_SHARE_COL = "market_share_series"
COMPETITIVE_EVENTS_COL = "competitive_events"
INSIGHTS_COL = "insights"
FRAMEWORK_RESULTS_COL = "framework_results"

# Email & scheduler
EMAIL_RECIPIENTS_COL = "email_recipients"
SCHEDULER_RUNS_COL = "scheduler_runs"

# Re-export document factory helpers
from app.models.report import new_report_doc  # noqa: F401, E402
from app.models.user import new_user_doc  # noqa: F401, E402

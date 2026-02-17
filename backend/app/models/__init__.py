# Collection name constants for MongoDB
USERS_COL = "users"
TRADE_DATA_COL = "trade_data"
NEWS_COL = "news_articles"
REPORTS_COL = "reports"
SOURCE_STATUS_COL = "data_source_status"

# Re-export document factory helpers
from app.models.report import new_report_doc  # noqa: F401, E402
from app.models.user import new_user_doc  # noqa: F401, E402

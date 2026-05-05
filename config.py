"""
IntimaGuard — Configuration
Loaded by the Flask app factory. All secrets come from environment variables.
"""

import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    DEBUG = False
    TESTING = False

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # anon/public key for client ops

    # LLM API keys (for generating model responses on the platform)
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")

    # Judge model — override to avoid conflict of interest on leaderboard runs
    JUDGE_MODEL = os.getenv("JUDGE_MODEL", "claude-sonnet-4-6")

    # Geo-blocking: block EU and Brazil (GDPR / LGPD)
    # Uses ipapi.co free tier for IP lookup. Set GEOBLOCK_ENABLED=false to disable locally.
    GEOBLOCK_ENABLED = os.getenv("GEOBLOCK_ENABLED", "true").lower() == "true"
    BLOCKED_COUNTRY_CODES = {
        # EU member states
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
        "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
        "PL", "PT", "RO", "SK", "SI", "ES", "SE",
        # EEA non-EU
        "IS", "LI", "NO",
        # UK (post-Brexit, still GDPR-equivalent)
        "GB",
        # Brazil (LGPD)
        "BR",
    }

    # Daily interaction limit per session
    DAILY_INTERACTION_LIMIT = 10


class DevelopmentConfig(Config):
    DEBUG = True
    GEOBLOCK_ENABLED = False  # Skip geo-block in local dev


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

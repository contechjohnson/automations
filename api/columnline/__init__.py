"""
Columnline API module

Clean API endpoints for Make.com integration with Supabase.
Replaces Google Sheets with proper database and eliminates JavaScript parsing.
"""

from .routes import router

__all__ = ['router']

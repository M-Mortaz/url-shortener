"""
Analytics Service - Litestar Application

Serves analytics and aggregated statistics from ClickHouse.
"""

from litestar import Litestar, get
from litestar.exceptions import NotFoundException
from litestar.di import Provide
from litestar.config.cors import CORSConfig
import os
from typing import Dict, Any, Optional
from datetime import datetime
from aiochclient import ChClient as ClickHouseClient

# Configuration from environment variables
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "url_shortener")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")

# Global ClickHouse client
clickhouse_client: Optional[ClickHouseClient] = None


async def get_clickhouse_client() -> ClickHouseClient:
    """Get or create ClickHouse client."""
    global clickhouse_client
    
    if clickhouse_client is None:
        clickhouse_url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/"
        
        # Build client kwargs
        client_kwargs = {
            "url": clickhouse_url,
            "database": CLICKHOUSE_DATABASE,
        }
        
        # Only add user/password if explicitly provided and not empty
        if CLICKHOUSE_USER and CLICKHOUSE_USER != "default":
            client_kwargs["user"] = CLICKHOUSE_USER
        if CLICKHOUSE_PASSWORD:
            client_kwargs["password"] = CLICKHOUSE_PASSWORD
        
        clickhouse_client = ClickHouseClient(**client_kwargs)
    
    return clickhouse_client


async def close_clickhouse_client() -> None:
    """Close ClickHouse connection."""
    global clickhouse_client
    
    if clickhouse_client:
        await clickhouse_client.close()
        clickhouse_client = None


@get("/stats/{short_code:str}")
async def get_url_stats(
    short_code: str,
    client: ClickHouseClient = Provide(get_clickhouse_client)
) -> Dict[str, Any]:
    """
    Get aggregated statistics for a short URL.
    
    Queries ClickHouse for click events and returns aggregated statistics.
    """
    try:
        # Escape short_code for SQL injection prevention
        # aiochclient handles parameterization, but we'll use proper escaping
        escaped_short_code = short_code.replace("'", "''")
        
        # Query total clicks
        total_clicks_query = f"""
        SELECT count() as total_clicks
        FROM {CLICKHOUSE_DATABASE}.click_events
        WHERE short_code = '{escaped_short_code}'
        """
        
        total_clicks_result = await client.fetch(total_clicks_query)
        total_clicks = total_clicks_result[0][0] if total_clicks_result else 0
        
        # Query unique visitors (by IP address)
        unique_visitors_query = f"""
        SELECT uniqExact(ip_address) as unique_visitors
        FROM {CLICKHOUSE_DATABASE}.click_events
        WHERE short_code = '{escaped_short_code}'
        """
        
        unique_visitors_result = await client.fetch(unique_visitors_query)
        unique_visitors = unique_visitors_result[0][0] if unique_visitors_result else 0
        
        # Query last clicked timestamp
        last_clicked_query = f"""
        SELECT max(timestamp) as last_clicked
        FROM {CLICKHOUSE_DATABASE}.click_events
        WHERE short_code = '{escaped_short_code}'
        """
        
        last_clicked_result = await client.fetch(last_clicked_query)
        last_clicked = last_clicked_result[0][0] if last_clicked_result else None
        
        # Query clicks by day (last 30 days)
        clicks_by_day_query = f"""
        SELECT 
            toDate(timestamp) as date,
            count() as clicks
        FROM {CLICKHOUSE_DATABASE}.click_events
        WHERE short_code = '{escaped_short_code}'
            AND timestamp >= now() - INTERVAL 30 DAY
        GROUP BY date
        ORDER BY date DESC
        """
        
        clicks_by_day_result = await client.fetch(clicks_by_day_query)
        clicks_by_day = [
            {"date": str(row[0]), "clicks": row[1]}
            for row in clicks_by_day_result
        ]
        
        # Query top referrers
        top_referrers_query = f"""
        SELECT 
            referrer,
            count() as clicks
        FROM {CLICKHOUSE_DATABASE}.click_events
        WHERE short_code = '{escaped_short_code}'
            AND referrer != ''
        GROUP BY referrer
        ORDER BY clicks DESC
        LIMIT 10
        """
        
        top_referrers_result = await client.fetch(top_referrers_query)
        top_referrers = [
            {"referrer": row[0], "clicks": row[1]}
            for row in top_referrers_result
        ]
        
        # If no clicks found, return 404
        if total_clicks == 0:
            raise NotFoundException(
                detail=f"No analytics data found for short_code: {short_code}"
            )
        
        return {
            "short_code": short_code,
            "total_clicks": total_clicks,
            "unique_visitors": unique_visitors,
            "last_clicked": last_clicked.isoformat() if last_clicked else None,
            "clicks_by_day": clicks_by_day,
            "top_referrers": top_referrers,
        }
    
    except NotFoundException:
        raise
    except Exception as e:
        # Log error and return 500
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching stats for {short_code}: {e}", exc_info=True)
        raise


@get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "analytics"}


def create_app() -> Litestar:
    """Create and configure Litestar application."""
    # Configure CORS to allow requests from any origin (for Swagger UI and other clients)
    cors_config = CORSConfig(
        allow_origins=["*"],  # Allow all origins
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
        allow_credentials=True,  # Allow cookies and authentication headers
        expose_headers=["*"],  # Expose all response headers
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    app = Litestar(
        route_handlers=[get_url_stats, health_check],
        dependencies={"client": Provide(get_clickhouse_client)},
        on_shutdown=[close_clickhouse_client],
        cors_config=cors_config,
    )
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)


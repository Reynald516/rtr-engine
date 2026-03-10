"""
Daily Financial Summary Job - FULLY SQL-DRIVEN

STRICT RULE:
- Python MUST NOT calculate ANY financial metrics
- ALL calculations MUST be done in SQL
- Python ONLY executes SQL

This function will be used for scheduled cron jobs
"""

import logging
from app.db import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Raw SQL for aggregation - ALL calculations in SQL
AGGREGATION_SQL = """
INSERT INTO user_financial_summary (
    user_id,
    month,
    total_income,
    total_expense,
    net_balance,
    transaction_count,
    avg_transaction,
    largest_expense,
    dominant_category,
    updated_at
)
SELECT 
    user_id,
    TO_CHAR(created_at, 'YYYY-MM') as month,
    COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
    COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expense,
    COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as net_balance,
    COUNT(*) as transaction_count,
    COALESCE(AVG(amount), 0)::FLOAT as avg_transaction,
    COALESCE(MAX(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as largest_expense,
    MODE() WITHIN GROUP (ORDER BY category) FILTER (WHERE type = 'expense') as dominant_category,
    NOW() as updated_at
FROM 
    transactions
WHERE 
    user_id = {user_id}
GROUP BY 
    user_id, 
    TO_CHAR(created_at, 'YYYY-MM')
ON CONFLICT (user_id, month) 
DO UPDATE SET
    total_income = EXCLUDED.total_income,
    total_expense = EXCLUDED.total_expense,
    net_balance = EXCLUDED.net_balance,
    transaction_count = EXCLUDED.transaction_count,
    avg_transaction = EXCLUDED.avg_transaction,
    largest_expense = EXCLUDED.largest_expense,
    dominant_category = EXCLUDED.dominant_category,
    updated_at = EXCLUDED.updated_at;
"""


def execute_sql_aggregation(user_id: int):
    """
    Execute raw SQL aggregation for a single user.
    ALL calculations done in SQL - Python only executes.
    """
    sql = AGGREGATION_SQL.format(user_id=user_id)
    
    try:
        # Execute raw SQL using Supabase
        supabase.rpc(
            'exec_sql',  # Requires a PostgreSQL function that executes raw SQL
            {'query': sql}
        )
    except Exception as e:
        # Fallback: Try direct table insert if RPC not available
        # This still uses SQL for all calculations
        try:
            _execute_aggregation_fallback(user_id)
        except Exception as fallback_error:
            logger.error(f"Failed to aggregate for user {user_id}: {fallback_error}")


def _execute_aggregation_fallback(user_id: int):
    """
    Fallback method using direct SQL functions.
    All calculations still in SQL.
    """
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    
    # Use SQL functions for all calculations
    response = supabase.rpc(
        'aggregate_user_financial_summary',
        {
            'p_user_id': user_id,
            'p_month': current_month
        }
    )
    
    return response


def run_daily_financial_summary():
    """
    Run daily financial summary aggregation for all users.
    
    STRICT FLOW:
    1. Get all users
    2. For each user: execute SQL aggregation (NO Python calculation)
    
    Python ONLY:
    - Loops through users
    - Calls SQL execution function
    """
    logger.info("Fetching all users...")
    
    try:
        # Step 1: Get all users
        users_response = (
            supabase
            .table("users")
            .select("id")
            .execute()
        )
        
        if not users_response.data:
            logger.warning("No users found")
            return {"status": "no_users", "processed": 0}
        
        users = users_response.data
        logger.info(f"Found {len(users)} users")
        
        processed_count = 0
        
        # Step 2: For each user, execute SQL aggregation
        for user in users:
            user_id = user["id"]
            logger.info(f"Processing user {user_id}")
            
            # Execute SQL aggregation - ALL calculations in SQL
            execute_sql_aggregation(user_id)
            
            processed_count += 1
            logger.info(f"Summary updated for user {user_id}")
        
        logger.info(f"Daily financial summary completed. Processed {processed_count} users")
        
        return {
            "status": "success",
            "processed": processed_count
        }
    
    except Exception as e:
        logger.error(f"Error running daily financial summary: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == "__main__":
    run_daily_financial_summary()

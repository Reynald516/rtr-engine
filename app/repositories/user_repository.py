# app/repositories/user_repository.py

from app.db import (
    fetch_transactions_by_user,
    fetch_recent_analyses,
    fetch_analysis_by_date,
    fetch_last_analysis_before_today,
)

# =========================================
# DEBUG MODE - Toggle for debugging
# =========================================
DEBUG = True


# =========================================
# HELPER FUNCTION: Get Financial Summary from RPC
# Correctly handles Supabase RPC response format
# =========================================
def get_financial_summary(user_id: str) -> dict:
    """
    Fetch financial summary from RPC function.
    
    Supabase RPC returns a list containing a row dict:
        response.data = [{"income": 100000, "expense": 50000, "dominant": "food"}]
    
    This function correctly accesses response.data[0] to get the row.
    
    Args:
        user_id: The user's UUID
        
    Returns:
        dict with keys: income, expense, dominant (or defaults if empty)
    """
    from app.db import supabase
    
    # Default values for safe fallback
    default_summary = {
        "income": 0,
        "expense": 0,
        "dominant": None
    }
    
    try:
        response = supabase.rpc("get_full_financial_summary", {
            "p_user_id": user_id
        }).execute()
        
        # =====================================================
        # CRITICAL FIX: Check if response.data is a list with rows
        # Supabase RPC returns a LIST, not a direct dict
        # =====================================================
        if not response.data:
            print(f"[WARNING] RPC returned empty data for user {user_id}")
            return default_summary
        
        if not isinstance(response.data, list) or len(response.data) == 0:
            print(f"[WARNING] Invalid financial summary format for user {user_id}")
            return default_summary
        
        # Access the FIRST row (Supabase RPC returns list of rows)
        row = response.data[0]
        
        if DEBUG:
            print(f"[DEBUG] Financial summary row for user {user_id}: {row}")
        
        # Safely extract values with defaults
        income = row.get("income") if row.get("income") is not None else 0
        expense = row.get("expense") if row.get("expense") is not None else 0
        dominant = row.get("dominant") if row.get("dominant") is not None else None
        
        return {
            "income": income,
            "expense": expense,
            "dominant": dominant
        }
        
    except Exception as e:
        print(f"[ERROR] RPC failed for user {user_id}: {e}")
        return default_summary


# =========================================
# MANUAL PER-USER CACHE STORE
# Uses dict for precise per-user invalidation
# =========================================
_financial_summary_cache = {}


# =========================================
# CACHED HELPER FUNCTION (outside class)
# This ensures cache key is only user_id, not (self, user_id)
# =========================================
def _cached_financial_summary(user_id: str):
    """
    Cached fallback for financial summary.
    Uses manual per-user cache for precise invalidation.
    Only caches based on user_id (not self).
    """
    # Check cache first
    if user_id in _financial_summary_cache:
        return _financial_summary_cache[user_id]
    
    # Fetch from DB and cache
    result = _fetch_financial_summary_from_db(user_id)
    _financial_summary_cache[user_id] = result
    return result


def _fetch_financial_summary_from_db(user_id: str):
    """
    Fetch financial summary from database (multi-query approach).
    
    CRITICAL FIX: 
    - user_financial_summary table uses field name 'net_balance' NOT 'net_cashflow'
    - Now orders by month DESC to get the latest month record
    - Handles multiple rows (one per month) properly
    
    Returns:
        dict with financial summary data for latest month
    """
    from app.db import supabase
    
    # =====================================================
    # CRITICAL FIX: Query correct field name 'net_balance' 
    # AND order by month desc to get latest month
    # =====================================================
    try:
        financial_response = (
            supabase
            .table("user_financial_summary")
            .select("total_income, total_expense, net_balance, month, dominant_category")
            .eq("user_id", user_id)
            .order("month", desc=True)  # Get latest month
            .limit(1)  # Only latest month
            .execute()
        )
        
        # DEFENSIVE LOGGING: Check for zero rows
        if not financial_response.data or len(financial_response.data) == 0:
            print(f"[WARNING] SQL view returned ZERO rows for user {user_id}")
            financial_data = {}
        else:
            # DEFENSIVE LOGGING: Log multiple rows if any
            if len(financial_response.data) > 1:
                print(f"[DEBUG] Multiple rows returned for user {user_id}, using latest: {financial_response.data[0].get('month')}")
            financial_data = financial_response.data[0] or {}
            
    except Exception as e:
        # DEFENSIVE LOGGING: RPC / query failures
        print(f"[ERROR] Database query failed for user {user_id}: {e}")
        financial_data = {}
    
    total_income = financial_data.get("total_income") if financial_data.get("total_income") is not None else 0
    total_expense = financial_data.get("total_expense") if financial_data.get("total_expense") is not None else 0
    # FIX: Use net_balance (DB field) instead of net_cashflow
    net_balance = financial_data.get("net_balance") if financial_data.get("net_balance") is not None else 0
    month = financial_data.get("month")
    
    # Query user_largest_category view
    try:
        largest_response = (
            supabase
            .table("user_largest_category")
            .select("category, total_amount")
            .eq("user_id", user_id)
            .execute()
        )
        
        largest_category = None
        if largest_response.data and len(largest_response.data) > 0:
            largest_category = largest_response.data[0].get("category") if largest_response.data[0] else None
    except Exception:
        largest_category = None
    
    # Query user_smallest_category view
    try:
        smallest_response = (
            supabase
            .table("user_smallest_category")
            .select("category, total_amount")
            .eq("user_id", user_id)
            .execute()
        )
        
        smallest_category = None
        if smallest_response.data and len(smallest_response.data) > 0:
            smallest_category = smallest_response.data[0].get("category") if smallest_response.data[0] else None
    except Exception:
        smallest_category = None
    
    # Query user_category_breakdown view
    try:
        breakdown_response = (
            supabase
            .table("user_category_breakdown")
            .select("category, total_amount")
            .eq("user_id", user_id)
            .execute()
        )
        
        category_breakdown = {}
        if breakdown_response.data:
            for row in breakdown_response.data:
                if row and row.get("category"):
                    category_breakdown[row["category"]] = row.get("total_amount") or row.get("amount") or 0
    except Exception:
        category_breakdown = {}
    
    # Query user_largest_income_category view
    try:
        largest_income_response = (
            supabase
            .table("user_largest_income_category")
            .select("category, total_amount")
            .eq("user_id", user_id)
            .execute()
        )
        
        largest_income_category = None
        if largest_income_response.data and len(largest_income_response.data) > 0:
            largest_income_category = largest_income_response.data[0].get("category") if largest_income_response.data[0] else None
    except Exception:
        largest_income_category = None
    
    # Query user_smallest_income_category view
    try:
        smallest_income_response = (
            supabase
            .table("user_smallest_income_category")
            .select("category, total_amount")
            .eq("user_id", user_id)
            .execute()
        )
        
        smallest_income_category = None
        if smallest_income_response.data and len(smallest_income_response.data) > 0:
            smallest_income_category = smallest_income_response.data[0].get("category") if smallest_income_response.data[0] else None
    except Exception:
        smallest_income_category = None
    
    # Query user_income_category_breakdown view
    try:
        income_breakdown_response = (
            supabase
            .table("user_income_category_breakdown")
            .select("category, total_amount")
            .eq("user_id", user_id)
            .execute()
        )
        
        income_breakdown = {}
        if income_breakdown_response.data:
            for row in income_breakdown_response.data:
                if row and row.get("category"):
                    income_breakdown[row["category"]] = row.get("total_amount") or row.get("amount") or 0
    except Exception:
        income_breakdown = {}
    
    # Query user_dominant_category view
    try:
        dominant_response = (
            supabase
            .table("user_dominant_category")
            .select("category")
            .eq("user_id", user_id)
            .execute()
        )
        
        dominant_category = None
        if dominant_response.data and len(dominant_response.data) > 0:
            dominant_category = dominant_response.data[0].get("category") if dominant_response.data[0] else None
    except Exception:
        dominant_category = None
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        # Include both: net_balance (DB field) and net_cashflow (for backward compatibility)
        "net_balance": net_balance,
        "net_cashflow": net_balance,  # Alias for backward compatibility
        "month": month,
        "largest_category": largest_category,
        "smallest_category": smallest_category,
        "category_breakdown": category_breakdown,
        "largest_income_category": largest_income_category,
        "smallest_income_category": smallest_income_category,
        "income_breakdown": income_breakdown,
        "dominant_category": dominant_category or financial_data.get("dominant_category"),
    }


# =========================================
# CACHE INVALIDATION FUNCTION
# Call this when transactions are added/updated/deleted
# =========================================
def clear_financial_summary_cache(user_id: str):
    """
    Clear cached financial summary for a specific user.
    Call this function when:
    - New transaction is added
    - Transaction is updated
    - Transaction is deleted
    
    This ensures no stale data is served after financial changes.
    """
    if user_id in _financial_summary_cache:
        del _financial_summary_cache[user_id]
    if DEBUG:
        print(f"[DEBUG] Cache invalidated for user {user_id}")


class UserRepository:

    def get_transactions(self, user_id: str):
        return fetch_transactions_by_user(user_id)

    def get_recent_analyses(self, user_id: str, days: int):
        return fetch_recent_analyses(user_id, days)

    def get_analysis_by_date(self, user_id: str, analysis_date: str):
        return fetch_analysis_by_date(user_id, analysis_date)

    def get_last_analysis_before_today(self, user_id: str):
        return fetch_last_analysis_before_today(user_id)

    def get_user_financial_summary(self, user_id: str):
        """
        Query SQL views for financial aggregation.
        Returns dict with total_income, total_expense, net_cashflow,
        largest_category, smallest_category, category_breakdown.
        
        OPTIMIZATION:
        - Tries RPC first for single-query optimization
        - Falls back to cached multi-view queries if RPC unavailable
        - Includes debug logging for visibility
        - Validates for negative values (anti silent failure)
        
        NOTE: Caching is handled by _cached_financial_summary helper function
        to avoid including self in cache key.
        """
        from app.db import supabase
        
        if DEBUG:
            print(f"[DEBUG] Fetching financial summary for {user_id}")
        
        # =====================================================
        # OPTIMIZATION: Try RPC first (NO CACHE - fresh data)
        # =====================================================
        try:
            response = supabase.rpc("get_full_financial_summary", {
                "p_user_id": user_id
            }).execute()
            
            # FIX 2: Add RPC validation - prevent empty/invalid RPC from overriding SQL fallback
            if (
                response.data
                and len(response.data) > 0
                and response.data[0].get("total_income") is not None
            ):
                if DEBUG:
                    print(f"[DEBUG] RPC call successful for user {user_id}")
                
                parsed = self._parse_rpc_response(response.data[0])
                
                # SAVE TO CACHE FOR CONSISTENCY
                _financial_summary_cache[user_id] = parsed
                
                return parsed
            else:
                # FIX 2: Log when RPC returns invalid data, will fall back to SQL
                print(f"[WARNING] RPC returned invalid/empty data for user {user_id}, falling back to SQL")
        except Exception as rpc_err:
            if DEBUG:
                print(f"[DEBUG] RPC not available, falling back to cached multi-query: {rpc_err}")
        
        # =====================================================
        # FALLBACK: Use cached multi-query (cached by user_id only)
        # =====================================================
        result = _cached_financial_summary(user_id)
        
        # =====================================================
        # SAFETY: Anti silent failure - validate negative values
        # =====================================================
        total_income = result.get("total_income", 0)
        total_expense = result.get("total_expense", 0)
        
        if total_income < 0 or total_expense < 0:
            raise RuntimeError("Invalid financial data from SQL")
        
        if DEBUG:
            print("[DEBUG RESULT]", {
                "income": total_income,
                "expense": total_expense,
                "dominant": result.get("dominant_category")
            })
        
        return result

    def _parse_rpc_response(self, data: dict) -> dict:
        """
        Parse RPC response into expected format.
        
        FIX 1: Support both field names (net_cashflow and net_balance)
        RPC may return either, so we check both for backward compatibility.
        """
        return {
            "total_income": data.get("total_income") or 0,
            "total_expense": data.get("total_expense") or 0,
            # FIX 1: Support both field names - fallback from net_cashflow to net_balance
            "net_cashflow": data.get("net_cashflow") or data.get("net_balance") or 0,
            "net_balance": data.get("net_balance") or data.get("net_cashflow") or 0,
            "largest_category": data.get("largest_category"),
            "smallest_category": data.get("smallest_category"),
            "category_breakdown": data.get("category_breakdown") or {},
            "largest_income_category": data.get("largest_income_category"),
            "smallest_income_category": data.get("smallest_income_category"),
            "income_breakdown": data.get("income_breakdown") or {},
            "dominant_category": data.get("dominant_category"),
        }

# app/engine/behavior_engine.py

"""
Behavior Engine - Analyzes financial behavior changes

This engine analyzes financial behavior changes between:
- current analysis
- previous snapshot  
- recent snapshots (last 3 days)

This engine does NOT access database. It only works with data passed from FinancialAnalyzer.
"""

from typing import Dict, List, Optional, Any


def safe_number(value):
    """
    Safely convert value to number, treating None as 0.
    
    Args:
        value: Any value that might be None
    
    Returns:
        The value if not None, otherwise 0
    """
    if value is None:
        return 0
    return value


def calculate_percentage_change(new_value: float, old_value: float) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        new_value: The new value
        old_value: The old value to compare against
    
    Returns:
        Percentage change: (new - old) / old * 100
    """
    if old_value == 0:
        if new_value == 0:
            return 0.0
        return 100.0  # Treat as 100% increase if old is 0 and new is not 0
    return ((new_value - old_value) / abs(old_value)) * 100


def determine_trend(change_pct: float) -> str:
    """
    Determine trend direction based on percentage change.
    
    Args:
        change_pct: The percentage change value
    
    Returns:
        "up" if change_pct > 10, "down" if change_pct < -10, "stable" otherwise
    """
    if change_pct > 10:
        return "up"
    elif change_pct < -10:
        return "down"
    return "stable"



def detect_behavior(
    current_analysis: Dict[str, Any],
    previous_snapshot: Optional[Dict[str, Any]],
    recent_snapshots: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Analyze financial behavior changes between current analysis and previous data.
    
    Args:
        current_analysis: Current financial analysis with keys:
            - total_income: float
            - total_expense: float
            - dominant_category: str
        previous_snapshot: Previous financial snapshot with keys:
            - total_income: float
            - total_expense: float
            (optional, can be None)
        recent_snapshots: List of recent snapshots (last 3 days)
            Each with keys:
            - total_expense: float
            - total_income: float (optional)
        (optional, can be None or empty)
    
    Returns:
        Behavior dict with keys:
        - expense_change_pct: float
        - income_change_pct: float
        - spending_trend: "up" | "down" | "stable"
        - income_trend: "up" | "down" | "stable"
        - behavior_flags: list of strings
    """
    # Default values if previous snapshot is missing
    if previous_snapshot is None:
        return {
            "expense_change_pct": 0.0,
            "income_change_pct": 0.0,
            "spending_trend": "stable",
            "income_trend": "stable",
            "behavior_flags": []
        }
    
    # Extract values from current analysis with safe_number protection
    current_income = safe_number(current_analysis.get("total_income"))
    current_expense = safe_number(current_analysis.get("total_expense"))
    current_dominant = current_analysis.get("dominant_category")
    
    # Extract values from previous snapshot with safe_number protection
    previous_income = safe_number(previous_snapshot.get("total_income"))
    previous_expense = safe_number(previous_snapshot.get("total_expense"))
    previous_dominant = previous_snapshot.get("dominant_category")
    
    # Calculate percentage changes
    expense_change_pct = calculate_percentage_change(current_expense, previous_expense)
    income_change_pct = calculate_percentage_change(current_income, previous_income)
    
    # Determine trends
    spending_trend = determine_trend(expense_change_pct)
    income_trend = determine_trend(income_change_pct)
    
    # Build behavior flags
    behavior_flags: List[str] = []
    
    # Check for expense spike
    if expense_change_pct > 30:
        behavior_flags.append("expense_spike")
    
    # Check for income drop
    if income_change_pct < -30:
        behavior_flags.append("income_drop")
    
    # Check for overspending
    if current_expense > current_income:
        behavior_flags.append("overspending")
    
    # Check for category shift
    if current_dominant and previous_dominant and current_dominant != previous_dominant:
        behavior_flags.append("category_shift")
    
    return {
        "expense_change_pct": round(expense_change_pct, 2),
        "income_change_pct": round(income_change_pct, 2),
        "spending_trend": spending_trend,
        "income_trend": income_trend,
        "behavior_flags": behavior_flags
    }
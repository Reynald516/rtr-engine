"""
Pattern Engine - Detects long-term financial patterns from recent snapshots

This engine analyzes long-term patterns from recent snapshots data.
This engine does NOT access database. It only works with data passed from the daily job.
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


def detect_patterns(
    current_analysis: Dict[str, Any],
    recent_snapshots: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Detect long-term financial patterns from recent snapshots.
    
    Args:
        current_analysis: Current financial analysis with keys:
            - total_income: float
            - total_expense: float
            - dominant_category: str
        recent_snapshots: List of recent snapshots
            Each with keys:
            - total_expense: float
            - total_income: float
            - dominant_category: str (optional)
        (optional, can be None or empty)
    
    Returns:
        Patterns dict with keys:
        - patterns: list of detected pattern strings
    """
    # Initialize empty patterns list
    detected_patterns: List[str] = []
    
    # Return empty patterns if no recent snapshots
    if not recent_snapshots or len(recent_snapshots) == 0:
        return {"patterns": detected_patterns}
    
    # Extract current values with safe_number protection
    current_expense = safe_number(current_analysis.get("total_expense"))
    current_dominant = current_analysis.get("dominant_category")
    
    # =====================================================
    # Pattern 1: WEEKLY SPENDING PATTERN
    # If average expense of recent snapshots > 20% higher than current expense
    # =====================================================
    total_expense_sum = 0
    valid_expense_count = 0
    
    for snapshot in recent_snapshots:
        expense = safe_number(snapshot.get("total_expense"))
        if expense is not None:
            total_expense_sum += expense
            valid_expense_count += 1
    
    if valid_expense_count > 0 and current_expense > 0:
        avg_recent_expense = total_expense_sum / valid_expense_count
        expense_ratio = (avg_recent_expense - current_expense) / current_expense * 100
        
        if expense_ratio > 20:
            detected_patterns.append("weekly_spending_spike")
    
    # =====================================================
    # Pattern 2: CONSISTENT OVERSPENDING
    # If more than 2 recent snapshots have expense > income
    # =====================================================
    overspending_count = 0
    
    for snapshot in recent_snapshots:
        expense = safe_number(snapshot.get("total_expense"))
        income = safe_number(snapshot.get("total_income"))
        
        if expense > income:
            overspending_count += 1
    
    if overspending_count > 2:
        detected_patterns.append("consistent_overspending")
    
    # =====================================================
    # Pattern 3: CATEGORY HABIT
    # If same dominant_category appears frequently in recent snapshots
    # =====================================================
    if current_dominant:
        category_count = 0
        total_with_category = 0
        
        for snapshot in recent_snapshots:
            snapshot_category = snapshot.get("dominant_category")
            if snapshot_category is not None:
                total_with_category += 1
                if snapshot_category == current_dominant:
                    category_count += 1
        
        # If category appears in more than 50% of snapshots with category data
        if total_with_category > 0 and (category_count / total_with_category) > 0.5:
            detected_patterns.append("category_habit")
    
    return {
        "patterns": detected_patterns
    }


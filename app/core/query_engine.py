# app/core/query_engine.py

from typing import Dict, Any


def query_engine(user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return hasil query berbasis data (BUKAN narasi)
    """

    message = user_message.lower()

    # Safe guard: empty context
    if not context:
        return {"type": "text", "message": "Belum ada data, coba mulai catat dulu ya"}

    if "pemasukan terbesar" in message:
        return handle_largest_income(context)
    
    if "pemasukan terkecil" in message:
        return handle_smallest_income(context)
    
    if "pengeluaran terbesar" in message:
        return handle_largest_category(context)
    
    if "pengeluaran terkecil" in message:
        return handle_smallest_category(context)

    if "total pengeluaran" in message:
        return {
            "type": "total_expense",
            "value": context.get("total_expense", 0)
        }
    
    if "total pemasukan" in message:
        return {
            "type": "total_income",
            "value": context.get("total_income", 0)
        }

    return {
        "type": "unknown",
        "data": None
    }

def handle_total_expense(context: Dict[str, Any]) -> Dict[str, Any]:
    total = context.get("total_expense", 0)

    return {
        "type": "total_expense",
        "value": total
    }

def handle_total_income(context: Dict[str, Any]) -> Dict[str, Any]:
    total = context.get("total_income", 0)

    return {
        "type": "total_income",
        "value": total
    }


def handle_largest_category(context: Dict[str, Any]) -> Dict[str, Any]:
    # Use largest_category from context (provided by SQL)
    category = context.get("largest_category")
    breakdown = context.get("category_breakdown", {})

    if not category:
        return {"type": "text", "message": "Belum ada data kategori"}
    
    if not breakdown or category not in breakdown:
        return {"type": "text", "message": "Belum ada data kategori"}

    amount = breakdown.get(category, 0)

    return {
        "type": "largest_category",
        "category": category,
        "amount": amount
    }


def handle_smallest_category(context: Dict[str, Any]) -> Dict[str, Any]:
    # Use smallest_category from context (provided by SQL)
    category = context.get("smallest_category")
    breakdown = context.get("category_breakdown", {})

    if not category:
        return {"type": "text", "message": "Belum ada data kategori"}
    
    if not breakdown or category not in breakdown:
        return {"type": "text", "message": "Belum ada data kategori"}

    amount = breakdown.get(category, 0)

    return {
        "type": "smallest_category",
        "category": category,
        "amount": amount
    }

def handle_largest_income(context: Dict[str, Any]) -> Dict[str, Any]:
    # Use largest_income_category from context (provided by SQL)
    category = context.get("largest_income_category")
    income_breakdown = context.get("income_breakdown", {})

    if not category:
        return {"type": "text", "message": "Belum ada data kategori"}
    
    if not income_breakdown or category not in income_breakdown:
        return {"type": "text", "message": "Belum ada data kategori"}

    amount = income_breakdown.get(category, 0)

    return {
        "type": "largest_income",
        "category": category,
        "amount": amount
    }

def handle_smallest_income(context: Dict[str, Any]) -> Dict[str, Any]:
    # Use smallest_income_category from context (provided by SQL)
    category = context.get("smallest_income_category")
    income_breakdown = context.get("income_breakdown", {})

    if not category:
        return {"type": "text", "message": "Belum ada data kategori"}
    
    if not income_breakdown or category not in income_breakdown:
        return {"type": "text", "message": "Belum ada data kategori"}

    amount = income_breakdown.get(category, 0)

    return {
        "type": "smallest_income",
        "category": category,
        "amount": amount
    }

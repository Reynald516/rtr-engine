# app/engine/data_loader.py

from app.repositories.user_repository import UserRepository


def load_user_data(user_id: str) -> dict:
    """
    Load user data for the pipeline.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict with "profile" key containing user data
    """
    repo = UserRepository()
    
    transactions = repo.get_transactions(user_id)
    previous_snapshot = repo.get_last_analysis_before_today(user_id)
    recent_snapshots = repo.get_recent_analyses(user_id, days=3)
    
    return {
        "profile": {
            "user_id": user_id,
            "transactions": transactions,
            "previous_snapshot": previous_snapshot,
            "recent_snapshots": recent_snapshots
        }
    }

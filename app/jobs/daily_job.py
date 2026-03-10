# app/jobs/daily_job.py

from datetime import datetime
from app.engine.data_loader import load_user_data
from app.core.analyzer import FinancialAnalyzer
from app.insights.generator import generate_insight
from app.repositories.insight_repository import save_user_financial_insight
from app.engine.scheduled_engine import run_scheduled_analysis
from app.engine.behavior_engine import detect_behavior  # Import behavior engine
from app.engine.pattern_engine import detect_patterns  # Import pattern engine
from app.db import supabase


def get_all_users():
    """
    Get all user IDs from database.
    Returns list of user_id strings.
    """
    try:
        response = supabase.table("profiles").select("id").execute()
        if response.data:
            return [user["id"] for user in response.data]
        return []
    except Exception:
        # Return empty list if table doesn't exist or error
        return []


def run_daily_job():
    """
    Run daily job to generate and save insights for all users.
    Moves heavy processing out of chat into scheduled job.
    
    PHASE 4: After computing, insights are saved to user_insights table.
    UI should read from this table - NEVER recompute at request time.
    """
    users = get_all_users()
    
    for user_id in users:
        try:
            user_data = load_user_data(user_id)
            profile = user_data["profile"]
            
            analyzer = FinancialAnalyzer(
                transactions=profile["transactions"],
                previous_snapshot=profile["previous_snapshot"],
                recent_snapshots=profile["recent_snapshots"],
                user_id=user_id,
            )
            
            # Run analysis (this fetches from SQL as source of truth)
            analysis = analyzer.run()
            
            # =====================================================
            # BEHAVIOR DETECTION - Run after analysis is produced
            # =====================================================
            behavior = detect_behavior(
                current_analysis=analysis,
                previous_snapshot=profile.get("previous_snapshot"),
                recent_snapshots=profile.get("recent_snapshots")
            )
            
            # Merge behavior into analysis so it's available for insight generation
            analysis["behavior"] = behavior
            
            # =====================================================
            # PATTERN DETECTION - Run after behavior detection
            # =====================================================
            patterns = detect_patterns(
                current_analysis=analysis,
                recent_snapshots=profile.get("recent_snapshots")
            )
            
            # Merge patterns into analysis so it's available for insight generation
            analysis["patterns"] = patterns
            
            # Generate insight text
            insight = generate_insight(analysis)
            
            # PHASE 4 RULE:
            # ALL computed data MUST be merged and stored in user_insights
            # NEVER store partial insight or duplicate tables
            
            # Merge analysis + generated insight into single source of truth
            merged_insight = {
                **analysis,
                **insight,
                "engine_version": "RTR_v1",
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # PHASE 4: Save merged insight to user_insights table
            # This is the ONLY source - UI reads from here, never recomputes
            save_user_financial_insight(user_id, merged_insight)
            
            # PHASE 6: Run scheduled behavior analysis after financial insight
            run_scheduled_analysis(user_id, analysis)
            
        except Exception as e:
            # Continue to next user if one fails
            print(f"[WARNING] Failed to process user {user_id}: {e}")
            continue
    
    return {"status": "completed", "users_processed": len(users)}

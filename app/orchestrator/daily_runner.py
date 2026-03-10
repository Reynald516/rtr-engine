"""
Daily Runner - Orchestrator for RTR Engine
Main entry point for daily analysis pipeline
"""

from app.core.analyzer import FinancialAnalyzer
from app.engine.data_loader import load_user_data
from app.behavior.pattern_memory import analyze_pattern_memory
from app.insights.generator import generate_insight


class DataLoader:
    """Wrapper class for data loading operations"""
    
    async def load_user_transactions(self, user_id: str):
        """Load user transactions and related data"""
        user_data = load_user_data(user_id)
        return user_data.get("profile", {}).get("transactions", [])


class Analyzer:
    """Wrapper class for financial analysis"""
    
    def analyze(self, transactions: list, previous_snapshot=None, recent_snapshots=None, user_id: str = None):
        """Run financial analysis on transactions"""
        engine = FinancialAnalyzer(
            transactions=transactions,
            previous_snapshot=previous_snapshot,
            recent_snapshots=recent_snapshots,
            user_id=user_id,
        )
        return engine.run()


class PatternMemory:
    """Wrapper class for pattern memory/behavior tracking"""
    
    def update(self, user_id: str, analysis: dict, recent_snapshots: list = None):
        """Update and return behavior pattern analysis"""
        if recent_snapshots and len(recent_snapshots) >= 2:
            return analyze_pattern_memory(recent_snapshots)
        return None


class InsightGenerator:
    """Wrapper class for insight generation"""
    
    def generate(self, analysis: dict, behavior: dict = None):
        """Generate AI-style insights from analysis"""
        # Merge behavior into analysis if available
        if behavior:
            analysis_with_behavior = {**analysis, "pattern_memory": behavior}
        else:
            analysis_with_behavior = analysis
            
        return generate_insight(analysis_with_behavior)


async def run_daily_analysis(user_id: str):
    """
    Main orchestrator function for daily analysis.
    
    Flow:
    1. Load data
    2. Analyze
    3. Behavior tracking
    4. Generate insight
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict with analysis, behavior, and insight
    """
    # 1. Load data
    loader = DataLoader()
    user_data = load_user_data(user_id)
    profile = user_data.get("profile", {})
    transactions = profile.get("transactions", [])
    
    if not transactions:
        return {"status": "no_data", "message": "No transactions found for user"}

    previous_snapshot = profile.get("previous_snapshot")
    recent_snapshots = profile.get("recent_snapshots", [])

    # 2. Analyze
    analyzer = Analyzer()
    analysis = analyzer.analyze(
        transactions=transactions,
        previous_snapshot=previous_snapshot,
        recent_snapshots=recent_snapshots,
        user_id=user_id,
    )

    # 3. Behavior tracking
    memory = PatternMemory()
    behavior = memory.update(user_id, analysis, recent_snapshots)

    # 4. Generate insight (AI style)
    generator = InsightGenerator()
    insight = generator.generate(analysis, behavior)

    return {
        "status": "success",
        "analysis": analysis,
        "behavior": behavior,
        "insight": insight
    }

# app/conversation/insight_router.py

def route_insight(engine_output: dict) -> dict:
    insight_block = engine_output.get("insight", {})
    patterns = insight_block.get("patterns", [])

    insight_types = {pattern["type"] for pattern in patterns}

    if "HABIT_WARNING" in insight_types:
        return {
            "mode": "gentle_warning",
            "goal": "Bikin user sadar TANPA menghakimi"
        }

    if "PATTERN_MEMORY" in insight_types:
        return {
            "mode": "reflective",
            "goal": "Ngajak user refleksi ringan"
        }

    return {
        "mode": "supportive",
        "goal": "Bikin user ngerasa ditemenin"
    }
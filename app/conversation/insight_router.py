# app/conversation/insight_router.py

def route_insight(engine_output: dict) -> dict:
    insight_types = [i["type"] for i in engine_output.get("insights", [])]

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
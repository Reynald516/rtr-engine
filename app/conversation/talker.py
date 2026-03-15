# app/conversation/talker.py
import os
from datetime import datetime, timezone
from app.conversation.llm_client import chat_completion
from app.conversation.insight_router import route_insight
from app.conversation.insight_prompt import build_system_prompt
from app.conversation.context import save_engine_context
from app.conversation.memory import get_memory, save_message
from app.core.query_engine import query_engine


def generate_user_message(engine_output: dict) -> dict:
    route = route_insight(engine_output)
    mode = route.get("mode")
    goal = route.get("goal")

    if mode == "WARNING":
        goal = "Buat user sadar tanpa menghakimi"
    elif mode == "RISK":
        goal = "Bantu user refleksi dan hati-hati"
    else:
        goal = "Bantu user memahami kondisi keuangannya"

    insight_block = engine_output.get("insight", {})
    summary = insight_block.get("summary", "")

    system_prompt = build_system_prompt(
        mode=mode,
        goal=goal,
        context={
            "risk_level": engine_output.get("risk_level"),
            "dominant_category": engine_output.get("dominant_category"),
            "summary": summary
        }
    )

    user_payload = {
        "engine_insight": insight_block,
        "summary": summary
    }

    return {
        "system_prompt": system_prompt,
        "user_payload": user_payload
    }


def talk_to_user(engine_output: dict) -> str:
    payload = generate_user_message(engine_output)

    return chat_completion(
        messages=[
            {"role": "system", "content": payload["system_prompt"]},
            {
                "role": "user",
                "content": f"""
    Ringkasan kondisi user:
    {payload['user_payload']['summary']}
    
    Insight mesin:
    {payload['user_payload']['engine_insight']}
    """
            }
        ]
    )


def chat_with_user(user_id: str, user_message: str, context: dict) -> str:
    # 1. EKSTRAK DATA DARI CONTEXT BARU
    # FIX: Pipeline provides context with insight data directly, not nested under "analysis"
    # Try both keys for backward compatibility
    analysis = context.get("analysis", context)  # Fallback to context itself
    insight = context.get("insight", context.get("summary", {}))
    behavior = context.get("behavior", {})
    
    # SAFE GUARD: Check for empty data - first time user
    total_income = analysis.get("total_income", 0)
    total_expense = analysis.get("total_expense", 0)
    category_breakdown = analysis.get("category_breakdown", {})
    
    if total_income == 0 and total_expense == 0 and not category_breakdown:
        return "Belum ada data keuangan. Yuk mulai catat dulu biar gue bisa bantu analisis."
    
    # 2. ROUTING BERDASARKAN RISK LEVEL
    risk_level = analysis.get("risk_level", "NORMAL")
    
    # 3. TENTUKAN TONE BERDASARKAN RISK LEVEL & TREND
    tone = determine_tone(risk_level, behavior)
    
    # 4. PENENTUAN GOAL
    if risk_level == "WARNING":
        goal = "Buat user sadar tanpa menghakimi"
    elif risk_level == "RISK":
        goal = "Bantu user refleksi dan hati-hati"
    else:
        goal = "Bantu user memahami kondisi keuangannya"
    
    # 5. MEMBANGUN SYSTEM PROMPT
    summary = insight.get("summary", "")
    
    system_prompt = build_system_prompt(
        mode=risk_level,
        goal=goal,
        context={
            "risk_level": risk_level,
            "dominant_category": analysis.get("dominant_category"),
            "summary": summary,
        }
    )
    
    # 6. BUILD ENGINE CONTEXT (TANPA SIMPAN)
    net_cashflow = total_income - total_expense
    
    engine_context = {
        "system_prompt": system_prompt,
        "risk_level": risk_level,
        "dominant_category": analysis.get("dominant_category"),
        "summary": insight.get("summary"),
        "patterns": insight.get("patterns"),
        "category_breakdown": category_breakdown,
        "smallest_category": analysis.get("smallest_category"),
        "largest_category": analysis.get("largest_category"),
        "total_income": total_income,
        "total_expense": total_expense,
        "net_cashflow": net_cashflow,
        "income_breakdown": analysis.get("income_breakdown", {}),
        "behavior": behavior,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Lanjutkan dengan logic LLM yang sudah ada
    memory = get_memory(user_id)

    # 9. DETEKSI INTENT USER
    intent = detect_intent(user_message)
    
    # 10. CEK JIKA INTENT SPESIFIK - JIKA ADA, LANGSUNG RETURN
    intent_response = build_intent_based_response(intent, user_message, analysis, insight, behavior, tone)
    
    # PRIORITY: Jika ada intent_response, langsung return tanpa LLM
    if intent_response:
        save_message(user_id, "user", user_message)
        save_message(user_id, "assistant", intent_response)
        return intent_response

    query_result = query_engine(user_message, engine_context)
    
    if query_result["type"] != "unknown":
        return generate_response_from_query(query_result, engine_context)

    category_text = "\n".join([
        f"- {k}: {v}" for k, v in category_breakdown.items()
    ])

    # 7. BANGUN ACTIONABLE RECOMMENDATION
    actionable_rec = generate_actionable_recommendation(risk_level, analysis, insight)
    
    # 8. BANGUN CONTEXT MESSAGE DENGAN TONE DAN RECOMMENDATION   
    def fmt(n) -> str:
        try:
            return f"Rp {int(n):,}".replace(",", ".")
        except:
            return "Rp 0"

    dominant_cat = context.get("dominant_category") or "Belum terdeteksi"
    summary_text = context.get("summary_text") or context.get("summary") or ""
    spending_pattern = context.get("spending_pattern") or {}
    pattern_notes = ""
    if isinstance(spending_pattern, dict):
        notes = spending_pattern.get("notes", [])
        if notes:
            pattern_notes = "\n".join([f"  - {n}" for n in notes])

    context_message = f"""
DATA KEUANGAN USER (REAL DATA — WAJIB DIPAKAI):

- Total Pemasukan  : {fmt(total_income)}
- Total Pengeluaran: {fmt(total_expense)}
- Net Cashflow     : {fmt(net_cashflow)}
- Risk Level       : {risk_level}
- Kategori Dominan : {dominant_cat}
- Largest Expense  : {fmt(context.get("largest_expense", 0) or 0)}
- Ringkasan        : {summary_text}

POLA PENGELUARAN:
{pattern_notes if pattern_notes else "Belum ada pola terdeteksi"}

TONE: {tone}

{generate_actionable_recommendation(risk_level, {"total_income": total_income, "total_expense": total_expense, "net_cashflow": net_cashflow, "dominant_category": dominant_cat, "largest_category": dominant_cat, "category_breakdown": {}}, {})}

RULES WAJIB:
- Semua jawaban HARUS mengacu data di atas
- Jangan pernah sebut "N/A" — gunakan "Belum terdeteksi" jika data kosong
- Gunakan bahasa Indonesia yang santai dan akrab
- Sajikan angka dalam format Rp X.XXX.XXX
- Berikan jawaban yang natural, bukan template
"""

    messages = [
        {"role": "system", "content": engine_context["system_prompt"]},
        {"role": "system", "content": context_message},
    ]

    messages.extend(memory)

    messages.append({
        "role": "user",
        "content": user_message
    })

    assistant_reply = chat_completion(messages=messages)

    save_message(user_id, "user", user_message)
    save_message(user_id, "assistant", assistant_reply)

    return assistant_reply


def determine_tone(risk_level: str, behavior: dict) -> str:
    """Tentukan tone response berdasarkan risk level dan behavior."""
    trend = behavior.get("trend", "stable")
    
    if risk_level == "CRITICAL":
        return "Waspada dan urgent - langsung ingatkan bahaya"
    elif risk_level == "RISK":
        if trend == "increasing":
            return "Empati tapi tegas - ingatkan kondisi memburuk"
        return "Supportif - bantu user sadar tanpa menghakimi"
    elif risk_level == "WARNING":
        return "Warm - ingatkan dengan lembut"
    else:
        if trend == "increasing":
            return "Informatif - bantu optimize sebelum ada masalah"
        return "Positif - apresiasi kondisi keuangan baik"


def format_behavior(behavior: dict) -> str:
    """Format behavior data untuk context message."""
    if not behavior:
        return "Belum ada data perilaku yang cukup"
    
    parts = []
    
    if behavior.get("trend"):
        parts.append(f"- Trend: {behavior['trend']}")
    
    if behavior.get("spending_pattern"):
        parts.append(f"- Pola spending: {behavior['spending_pattern']}")
    
    if behavior.get("consistency"):
        parts.append(f"- Konsistensi: {behavior['consistency']}")
    
    if behavior.get("comparison"):
        parts.append(f"- Perbandingan: {behavior['comparison']}")
    
    return "\n".join(parts) if parts else "Data perilaku belum tersedia"


def generate_actionable_recommendation(risk_level: str, analysis: dict, insight: dict) -> str:
    """Generate actionable recommendations based on risk level, analysis, and insight."""
    
    recommendations = []
    
    # Kategori pengeluaran terbesar
    largest_category = analysis.get("largest_category", "")
    category_breakdown = analysis.get("category_breakdown", {})
    
    # Total dan net cashflow
    total_income = analysis.get("total_income", 0)
    total_expense = analysis.get("total_expense", 0)
    net_cashflow = total_income - total_expense
    
    # Risk-based recommendations
    if risk_level == "CRITICAL":
        recommendations.append("🚨 PRIORITAS: Hentikan pengeluaran non-esensial sekarang!")
        recommendations.append("💰 Coba cari sumber income tambahan mendesak")
        if largest_category:
            recommendations.append(f"📉 Kurangi {largest_category} - ini yang paling besar pengeluarannya")
        recommendations.append("📊 Buat budget darurat dengan 50% sisa income")
        
    elif risk_level == "RISK":
        recommendations.append("⚠️ Kondisi perlu perhatian - evaluasi pengeluaran wajib")
        if net_cashflow < 0:
            recommendations.append("💡 Kamu minus bulan ini. Prioritaskan utang dantagihan essential")
        if largest_category:
            recommendations.append(f"🎯 Fokus kurangi {largest_category} untuk improve cashflow")
        recommendations.append("📋 Buat anggaran maksimal per kategori minggu ini")
        
    elif risk_level == "WARNING":
        recommendations.append("💪 Kondisi bisa dibaiki dengan penyesuaian kecil")
        if largest_category and category_breakdown.get(largest_category, 0) > total_income * 0.3:
            recommendations.append(f"📌 {largest_category} mencapai 30%+ income. Coba alihkan 10% ke tabungan")
        recommendations.append("✅ Mulai sisihkan 10% income untuk dana darurat")
        
    else:  # NORMAL
        recommendations.append("👍 Kondisi keuangan baik! Pertahankan kebiasaan ini")
        recommendations.append("💎 Pertimbangkan investasi atau peningkatan skill")
        recommendations.append("🎯 Sisihkan dana untuk goal finansial spesifik")
    
    # Pattern-based recommendations
    patterns = insight.get("patterns", [])
    if patterns:
        for pattern in patterns[:2]:  # Ambil max 2 patterns
            rec = get_pattern_recommendation(pattern)
            if rec:
                recommendations.append(rec)
    
    # Format output
    if recommendations:
        header = "🎯 ACTION ITEMS:\n"
        items = "\n".join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations)])
        return header + items
    
    return ""


def get_pattern_recommendation(pattern: str) -> str:
    """Get specific recommendation based on spending pattern."""
    
    pattern_lower = pattern.lower() if pattern else ""
    
    if "makanan" in pattern_lower or "food" in pattern_lower:
        return "🍔 Coba cooking at home lebih sering - bisa hemat 40%"
    
    if "transport" in pattern_lower or "ojek" in pattern_lower:
        return "🚗 Gunakan transportasi publik atau carpool untuk jarak dekat"
    
    if "belanja" in pattern_lower or "shopping" in pattern_lower:
        return "🛍️ Terapkan 24-hour rule sebelum beli barang non-essential"
    
    if "hiburan" in pattern_lower or "entertainment" in pattern_lower:
        return "🎬 Cari alternatif hiburan gratisan atau diskon keluarga"
    
    if "langganan" in pattern_lower or "subscription" in pattern_lower:
        return "📱 Audit langganan - cancel yang tidak dipakai sebulan ini"
    
    return None


def detect_intent(user_message: str) -> str:
    """
    Minimal intent detection.
    Semua pertanyaan diteruskan ke Groq LLM untuk jawaban yang lebih baik.
    """
    return "general"


def build_intent_based_response(intent: str, user_message: str, analysis: dict, insight: dict, behavior: dict, tone: str) -> str:
    """
    Semua pertanyaan diteruskan ke Groq LLM.
    Fast path untuk angka sudah ditangani di engine_pipeline.py.
    """
    return None


def generate_response_from_query(query_result, context):
    t = query_result["type"]

    if t == "largest_category":
        return (
            f"Pengeluaran terbesar kamu ada di kategori {query_result['category']} "
            f"dengan total Rp{query_result['amount']:,}.\n\n"
            "Ini yang paling banyak nguras uang kamu."
        )

    if t == "smallest_category":
        return (
            f"Pengeluaran terkecil kamu ada di kategori {query_result['category']} "
            f"dengan total Rp{query_result['amount']:,}."
        )
    
    if t == "total_income":
        return f"Total pemasukan kamu adalah Rp{query_result['value']:,}."

    if t == "total_expense":
        return f"Total pengeluaran kamu adalah Rp{query_result['value']:,}."

    if t == "error":
        return "Data kamu belum cukup untuk menjawab itu."

    if t == "text":
        return query_result.get("message", "Data kamu belum cukup untuk menjawab itu.")
    
    if t == "largest_income":
        return (
            f"Pemasukan terbesar kamu ada di kategori {query_result['category']} "
            f"dengan total Rp{query_result['amount']:,}.\n\n"
            "Ini yang paling banyak ngisi uang kamu."
        )

    return "Gue belum bisa jawab itu dari data yang ada."

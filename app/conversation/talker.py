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
    context_message = f"""
DATA KEUANGAN USER (REAL DATA):

TONE: {tone}

- Patterns: 
{engine_context.get("patterns")}

- Largest Category: {engine_context.get("largest_category")}
- Smallest Category: {engine_context.get("smallest_category")}

- Total Income: {engine_context.get("total_income")}
- Total Expense: {engine_context.get("total_expense")}
- Net Cashflow: {engine_context.get("net_cashflow")}
- Risk Level: {engine_context.get("risk_level")}
- Dominant Category: {engine_context.get("dominant_category")}

CATEGORY BREAKDOWN (WAJIB DIPAKAI UNTUK JAWABAN):
{category_text}

BEHAVIOR INSIGHT:
{format_behavior(behavior)}

{actionable_rec}

RULE:
- Gunakan tone yang sesuai: {tone}
- Jangan pernah keluar dari konteks data
- Semua jawaban harus mengacu ke category_breakdown atau metrics
- Jika user minta saran → wajib berbasis angka / kategori nyata dan sertakan action items
- Jawaban HARUS berdasarkan data di atas
- Sajikan rekomendasi dalam format numbered list
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
    Detect user intent from their message.
    
    FIX: Uses regex word boundaries to prevent false positives.
    Example: "keluar" should NOT match "pengeluaran"
    """
    import re
    
    message_lower = user_message.lower()
    
    # =====================================================
    # FIX: Use regex word boundaries (\b) to prevent false matches
    # Structure: {intent_keyword: (keywords_list, intent_name)}
    # =====================================================
    
    # 🔥 CORE FINANCIAL INTENTS - with word boundaries
    # Check for "pengeluaran" FIRST (longer match) before "keluar"
    if re.search(r"\b(pemasukan|income|gaji|penghasilan)\b", message_lower):
        return "income"
    
    # Expense: check longer phrases first to avoid substring issues
    if re.search(r"\b(pengeluaran|expense|belanja)\b", message_lower):
        return "expense"
    
    # Cashflow: also check for "keluar" as standalone word (not inside "pengeluaran")
    if re.search(r"\b(saldo|cashflow|sisa uang|sisa)\b", message_lower):
        return "cashflow"

    # EXISTING INTENTS - with word boundaries
    if re.search(r"\b(kenapa|mengapa|why|penyebab|sebab)\b", message_lower):
        return "reason"
    
    if re.search(r"\b(hemat|irit|save|kurangi|optimize|boros)\b", message_lower):
        return "saving"
    
    if re.search(r"\b(saran|rekomendasi|tips|advice|bagaimana|harus|mesti)\b", message_lower):
        return "recommendation"
    
    if re.search(r"\b(analisa|analysis|cek|lihat|tampil)\b", message_lower):
        return "analysis"
    
    if re.search(r"\b(banding|compare|beda|versus|lebih)\b", message_lower):
        return "comparison"
    
    if re.search(r"\b(target|goal|plan|rencana|tabung|invest)\b", message_lower):
        return "planning"
    
    if re.search(r"\b(status|kondisi|keuangan|sehat)\b", message_lower):
        return "status"
    
    if re.search(r"\b(benar|oke|ok|sip|good|nice)\b", message_lower):
        return "acknowledgment"
    
    return "general"


def build_intent_based_response(intent: str, user_message: str, analysis: dict, insight: dict, behavior: dict, tone: str) -> str:
    """Build response based on detected intent."""
    
    risk_level = analysis.get("risk_level", "NORMAL")
    largest_category = analysis.get("largest_category", "N/A")
    smallest_category = analysis.get("smallest_category", "N/A")
    total_expense = analysis.get("total_expense", 0)
    total_income = analysis.get("total_income", 0)
    net_cashflow = total_income - total_expense
    
    # 🔥 CORE FINANCIAL INTENTS - Data-driven, no LLM
    if intent == "income":
        return f"Pemasukan kamu bulan ini sekitar Rp{total_income:,}. Kalau konsisten, ini udah bagus."

    elif intent == "expense":
        return f"Total pengeluaran kamu bulan ini Rp{total_expense:,}."

    elif intent == "cashflow":
        if net_cashflow < 0:
            return f"Kamu minus Rp{abs(net_cashflow):,} bulan ini. Perlu kontrol pengeluaran."
        return f"Sisa uang kamu Rp{net_cashflow:,}. Masih aman."
    
    # EXISTING INTENTS
    if intent == "reason":
        return f"Kondisi keuangan kamu: Risk {risk_level}. Terbesar di {largest_category} (Rp{total_expense:,}). Net: Rp{net_cashflow:,}. Trend: {behavior.get('trend', 'stabil')}."
    
    elif intent == "saving":
        actionable = generate_actionable_recommendation(risk_level, analysis, insight)
        return f"Untuk hemat, fokus kurangi {largest_category}. {actionable}"
    
    elif intent == "recommendation":
        actionable = generate_actionable_recommendation(risk_level, analysis, insight)
        return f"Saran untukmu:\n{actionable}"
    
    elif intent == "analysis":
        breakdown = analysis.get("category_breakdown", {})
        txt = ", ".join([f"{k}: Rp{v:,}" for k, v in breakdown.items()])
        return f"Analisis: {txt}"
    
    elif intent == "comparison":
        return f"Perbandingan: Income Rp{total_income:,} vs Expense Rp{total_expense:,}."
    
    elif intent == "planning":
        return "Planning: 1) Dana darurat 3x pengeluaran, 2) Investasi, 3) Pelunasan utang."
    
    elif intent == "status":
        return f"Status: {risk_level}. Net cashflow Rp{net_cashflow:,}. Perilaku: {behavior.get('spending_pattern', 'normal')}."
    
    elif intent == "acknowledgment":
        return "Terima kasih! Ada yang lain?"
    
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

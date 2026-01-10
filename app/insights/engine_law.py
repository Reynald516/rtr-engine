# app/insights/engine_law.py

RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "DANGER"]

RISK_TITLES = {
    "LOW": "Keuangan kamu relatif aman hari ini",
    "MEDIUM": "Ada pola yang perlu kamu perhatikan",
    "HIGH": "Pengeluaran kamu mulai berisiko",
    "DANGER": "Kondisi keuangan kamu dalam bahaya"
}

WARNING_LEVEL = {
    "LOW": "INFO",
    "MEDIUM": "WARNING",
    "HIGH": "WARNING",
    "DANGER": "CRITICAL"
}
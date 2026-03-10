# app/core/analyzer.py

import pandas as pd
from app.features import extract_features, extract_daily_features
from app.clustering import cluster_user
from app.anomaly import detect_anomaly
from app.logic import rtr_logic
from app.behavior.evolution import evaluate_evolution
from app.behavior.pattern_memory import analyze_pattern_memory
from app.behavior.profile import build_behavior_profile
from app.behavior.habit_warning import detect_habit_warning
from app.repositories.user_repository import UserRepository


class FinancialAnalyzer:
    """
    Core Financial Intelligence Engine.
    Tidak tahu DB.
    Tidak tahu FastAPI.
    Tidak tahu LLM.
    Pure deterministic engine.

    # =========================================
    # ⚠️ SYSTEM RULE (DO NOT BREAK)
    # =========================================
    # ALL financial metrics MUST come from SQL
    # DO NOT compute:
    # - total_income
    # - total_expense
    # - net_cashflow
    # - category breakdown
    # from pandas DataFrame
    # =========================================
    """

    def __init__(
        self,
        transactions: list,
        previous_snapshot: dict | None,
        recent_snapshots: list | None,
        user_id: str | None = None,
    ):
        self.transactions = transactions
        self.previous_snapshot = previous_snapshot
        self.recent_snapshots = recent_snapshots
        self.user_id = user_id

        self.df = None
        self.features = None
        self.daily_features = None

        self.user_cluster = None
        self.anomaly_flag = None
        self.is_anomaly = None
        self.total_income = None
        self.total_expense = None
        self.dominant_category = None
        self.risk_level = None
        self.evolution = None
        self.pattern_memory = None
        self.habit_warning = None
        self.behavior_profile = None
        self.is_income_unstable = None
        self.net_cashflow = None
        self.category_breakdown = None
        self.largest_category = None
        self.smallest_category = None
        self.income_breakdown = None
        self.largest_income_category = None
        self.smallest_income_category = None

    # ==============================
    # PUBLIC ENTRYPOINT
    # ==============================
    def run(self):
        self._prepare_data()
        self._run_clustering()
        self._run_anomaly_detection()
        self._compute_basic_metrics()
        self._compute_risk_logic()
        self._evaluate_behavior()
        return self._build_result()

    # ==============================
    # PHASE 1 — PREPARATION
    # ==============================
    def _prepare_data(self):
        # =========================================================
        # IMPORTANT:
        # DataFrame is ONLY for:
        # - behavior analysis
        # - anomaly detection
        # NEVER for financial totals
        # =========================================================
        
        if not self.transactions:
            raise ValueError("Transaction list kosong.")
        
        self.df = pd.DataFrame(self.transactions)
        
        required_columns = {"amount", "type", "category"}
        if not required_columns.issubset(self.df.columns):
            raise ValueError("Format transaksi tidak valid.")
        
        # =========================
        # NORMALIZE TYPE
        # =========================
        TYPE_MAP = {
            "expense": "expense",
            "pengeluaran": "expense",
            "income": "income",
            "pemasukan": "income",
        }
        
        self.df["type"] = (
            self.df["type"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map(lambda x: TYPE_MAP.get(x, x))
        )
        
        # =========================
        # NORMALIZE CATEGORY
        # =========================
        CATEGORY_MAP = {
            "entertainment": "hiburan",
            "hiburan": "hiburan",
            "makanan": "makanan & minuman",
            "food": "makanan & minuman",
        }
        
        self.df["category"] = (
            self.df["category"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map(lambda x: CATEGORY_MAP.get(x, x))
        )
        
        # HANDLE NULL
        self.df["category"] = self.df["category"].fillna("unknown")
        
        # Note: extract_features is called AFTER SQL data is available
        # (in _compute_basic_metrics) to ensure SQL is the source of truth
        self.daily_features = extract_daily_features(self.df)

    # ==============================
    # PHASE 2 — CLUSTERING
    # ==============================
    def _run_clustering(self):
        expected_cols = [
            "total_spend",
            "transaction_count",
            "night_ratio"
        ]
        
        if self.daily_features.empty or self.daily_features.shape[0] < 3:
            self.user_cluster = 0
            return
        
        cluster_cols = [
            col for col in expected_cols
            if col in self.daily_features.columns
        ]
        
        if len(cluster_cols) < 3:
            self.user_cluster = 0
            return
        
        clusters, _ = cluster_user(
            self.daily_features[cluster_cols],
            n_clusters=3
        )
        
        self.daily_features["cluster"] = clusters
        self.user_cluster = int(self.daily_features["cluster"].mode()[0])

    # ==============================
    # PHASE 3 — ANOMALY
    # ==============================
    def _run_anomaly_detection(self):
        self.df["type"] = self.df["type"].str.lower()
        expense_df = self.df[self.df["type"] == "expense"]
        
        if expense_df.empty:
            self.anomaly_flag = []
            self.is_anomaly = False
        else:
            self.anomaly_flag = detect_anomaly(expense_df["amount"])
            self.is_anomaly = -1 in self.anomaly_flag

    # ==============================
    # PHASE 4 — BASIC METRICS (FROM SQL)
    # ==============================
    def _compute_basic_metrics(self):
        # Get financial summary from SQL views via repository
        # This is required - user_id must be provided
        if not self.user_id:
            raise ValueError("user_id is required for financial calculations")
        
        repo = UserRepository()
        summary = repo.get_user_financial_summary(self.user_id)
        
        # =====================================================
        # ⚠️ CRITICAL VALIDATION: SQL must return data
        # =====================================================
        if summary is None:
            raise RuntimeError("CRITICAL: SQL summary returned None")
        
        # Safe fallback: never crash, return default values
        if not summary:
            summary = {
                "total_income": 0,
                "total_expense": 0,
                "net_cashflow": 0,
                "category_breakdown": {},
                "largest_category": None,
                "smallest_category": None,
                "income_breakdown": {}
            }
        
        self.total_income = summary.get("total_income", 0) or 0
        self.total_expense = summary.get("total_expense", 0) or 0
        self.net_cashflow = summary.get("net_cashflow", 0) or 0
        self.category_breakdown = summary.get("category_breakdown", {}) or {}
        self.largest_category = summary.get("largest_category")
        self.smallest_category = summary.get("smallest_category")
        self.largest_income_category = summary.get("largest_income_category")
        self.smallest_income_category = summary.get("smallest_income_category")
        self.income_breakdown = summary.get("income_breakdown", {}) or {}
        self.dominant_category = summary.get("dominant_category")
        
        # =====================================================
        # ⚠️ WARNING: Log empty financial summary
        # =====================================================
        if self.total_income == 0 and self.total_expense == 0:
            print(f"[WARNING] Empty financial summary for user {self.user_id}")

        self.is_income_unstable = self.total_expense > self.total_income

        # NOW extract features with SQL financial data
        # This ensures behavior metrics are synced with SQL totals
        self.features = extract_features(
            self.df,
            financial_data={
                "total_income": self.total_income,
                "total_expense": self.total_expense
            }
        )

    # ==============================
    # PHASE 5 — RISK LOGIC
    # ==============================
    def _compute_risk_logic(self):
        self.risk_level = rtr_logic(
            cluster=self.user_cluster,
            anomaly_flag=self.anomaly_flag,
            night_ratio=self.features.get("night_ratio", 0),
        )

    # ==============================
    # PHASE 6 — BEHAVIOR INTELLIGENCE
    # ==============================
    def _evaluate_behavior(self):
        if self.previous_snapshot:
            self.evolution = evaluate_evolution(
                today={
                    "total_expense": self.total_expense,
                    "risk_level": self.risk_level,
                    "dominant_category": self.dominant_category
                },
                previous=self.previous_snapshot
            )

        if self.recent_snapshots and len(self.recent_snapshots) >= 2:
            self.pattern_memory = analyze_pattern_memory(self.recent_snapshots)

        self.habit_warning = detect_habit_warning(
            pattern_memory=self.pattern_memory,
            dominant_category=self.dominant_category
        )

        self.behavior_profile = build_behavior_profile(
            total_income=self.total_income,
            total_expense=self.total_expense,
            risk_level=self.risk_level,
            dominant_category=self.dominant_category,
            pattern_memory=self.pattern_memory
        )

    # ==============================
    # FINAL OUTPUT
    # ==============================
    def _build_result(self):
        return {
            "cluster": self.user_cluster,
            "anomaly": self.is_anomaly,
            "risk_level": self.risk_level,
            "dominant_category": self.dominant_category,
            "total_expense": self.total_expense,
            "total_income": self.total_income,
            "evolution": self.evolution,
            "pattern_memory": self.pattern_memory,
            "behavior_profile": self.behavior_profile,
            "habit_warning": self.habit_warning,
            "income_unstable": self.is_income_unstable,
            "category_breakdown": self.category_breakdown,
            "smallest_category": self.smallest_category,
            "largest_category": self.largest_category,
            "income_breakdown": self.income_breakdown,
            "largest_income_category": self.largest_income_category,
            "smallest_income_category": self.smallest_income_category,
        }

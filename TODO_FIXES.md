# TODO: Fix AI Fintech Engine Backend Issues

## Phase 1: Fix Repository Layer ✅ COMPLETED
- [x] 1. Fix user_repository.py - field name mismatch (net_cashflow -> net_balance)
- [x] 2. Fix user_repository.py - get latest month logic (.order("month", desc=True).limit(1))
- [x] 3. Add defensive logging for zero rows, RPC failures, etc.

## Phase 2: Fix Engine Pipeline ✅ COMPLETED
- [x] 4. Fix engine_pipeline.py - field name consistency (net_balance -> net_cashflow)

## Phase 3: Fix Talker ✅ COMPLETED
- [x] 5. Fix talker.py - read correct key from context (analysis -> insight)

## Phase 4: Fix Intent Detection ✅ COMPLETED
- [x] 6. Implement word boundary matching for intent detection

## Phase 5: Documentation ✅ COMPLETED
- [x] 7. Provide root cause explanation (see below)
- [x] 8. Provide architecture improvements (see below)
- [x] 9. Provide scalability suggestions for 1M users (see below)

---

## Fix Summary

### Issue #1 & #5: user_repository.py
- ROOT CAUSE: Field name `net_cashflow` doesn't exist in `user_financial_summary` table (uses `net_balance`)
- Also missing: ordering by month to get latest record
- FIX: Changed field names to match DB schema and added `.order("month", desc=True).limit(1)`

### Issue #2: engine_pipeline.py
- ROOT CAUSE: Uses `net_balance` but `insight_repository` saves as `net_cashflow`
- FIX: Changed to `net_cashflow` to match insight data

### Issue #3: talker.py
- ROOT CAUSE: Pipeline provides `context["insight"]` but code reads `context.get("analysis")`
- FIX: Changed to read from `context.get("insight", {})`

### Issue #4: Intent Detection
- ROOT CAUSE: Loose substring matching - "keluar" matches "pengeluaran"
- FIX: Implemented regex word boundary matching


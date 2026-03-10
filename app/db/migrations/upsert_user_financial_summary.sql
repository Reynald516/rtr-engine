-- UPSERT Query for user_financial_summary
-- If (user_id, month) exists → UPDATE
-- If not exists → INSERT

INSERT INTO user_financial_summary (
    user_id,
    month,
    total_income,
    total_expense,
    net_balance,
    transaction_count,
    avg_transaction,
    largest_expense,
    dominant_category,
    risk_level,
    updated_at
)
VALUES (
    :user_id,
    :month,
    :total_income,
    :total_expense,
    :net_balance,
    :transaction_count,
    :avg_transaction,
    :largest_expense,
    :dominant_category,
    :risk_level,
    CURRENT_TIMESTAMP
)
ON CONFLICT (user_id, month) 
DO UPDATE SET
    total_income = EXCLUDED.total_income,
    total_expense = EXCLUDED.total_expense,
    net_balance = EXCLUDED.net_balance,
    transaction_count = EXCLUDED.transaction_count,
    avg_transaction = EXCLUDED.avg_transaction,
    largest_expense = EXCLUDED.largest_expense,
    dominant_category = EXCLUDED.dominant_category,
    risk_level = EXCLUDED.risk_level,
    updated_at = CURRENT_TIMESTAMP;

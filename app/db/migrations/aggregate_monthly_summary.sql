-- SQL Query to aggregate transactions into monthly financial summary
-- This query populates user_financial_summary table

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
    updated_at
)
SELECT 
    user_id,
    TO_CHAR(created_at, 'YYYY-MM') as month,
    COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
    COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expense,
    COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as net_balance,
    COUNT(*) as transaction_count,
    COALESCE(AVG(amount), 0)::FLOAT as avg_transaction,
    COALESCE(MAX(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as largest_expense,
    MODE() WITHIN GROUP (ORDER BY category) as dominant_category,
    NOW() as updated_at
FROM 
    transactions
WHERE 
    type = 'expense'
GROUP BY 
    user_id, 
    TO_CHAR(created_at, 'YYYY-MM')
ON CONFLICT (user_id, month) 
DO UPDATE SET
    total_income = EXCLUDED.total_income,
    total_expense = EXCLUDED.total_expense,
    net_balance = EXCLUDED.net_balance,
    transaction_count = EXCLUDED.transaction_count,
    avg_transaction = EXCLUDED.avg_transaction,
    largest_expense = EXCLUDED.largest_expense,
    dominant_category = EXCLUDED.dominant_category,
    updated_at = EXCLUDED.updated_at;

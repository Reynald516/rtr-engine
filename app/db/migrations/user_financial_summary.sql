-- Drop existing view if exists
DROP VIEW IF EXISTS user_financial_summary;

-- Create user_financial_summary table (FINAL STRUCTURE)
-- Stores precomputed monthly financial metrics

CREATE TABLE user_financial_summary (
    user_id UUID,
    month TEXT,
    
    total_income NUMERIC DEFAULT 0,
    total_expense NUMERIC DEFAULT 0,
    net_balance NUMERIC DEFAULT 0,
    
    transaction_count INTEGER DEFAULT 0,
    avg_transaction NUMERIC DEFAULT 0,
    largest_expense NUMERIC DEFAULT 0,
    dominant_category TEXT,
    
    updated_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (user_id, month)
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_user_financial_summary_user 
ON user_financial_summary(user_id);

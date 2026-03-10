# Fix RPC Response Parsing - TODO

## Task
Fix the Python code to correctly read the Supabase RPC response and return clean dictionary.

## Plan
1. Create a new helper function `get_financial_summary` in user_repository.py
2. The function will:
   - Call supabase.rpc("get_full_financial_summary", {"p_user_id": user_id})
   - Check if response.data exists and has at least one row
   - Access the first row: response.data[0]
   - Safely extract income, expense, dominant with default values
   - Return clean dict with expected format
3. Add proper error handling and logging

## Expected Output Format
{
  "income": 100000,
  "expense": 50000,
  "dominant": "food"
}

## Steps
- [x] Add new get_financial_summary function to user_repository.py
- [x] Test that it handles empty responses correctly
- [x] Verify it returns the correct format

## Implementation Complete
The new function `get_financial_summary(user_id: str)` has been added to:
- File: app/repositories/user_repository.py

Key features:
1. Correctly accesses response.data[0] (first row of the list)
2. Safely handles empty/null responses with default values
3. Returns clean dict with income, expense, dominant keys
4. Includes debug logging for visibility
5. Proper exception handling


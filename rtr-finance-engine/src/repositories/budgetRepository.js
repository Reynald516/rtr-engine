const supabase = require('../utils/supabase');

class BudgetRepository {
  /**
   * Ambil semua budget user
   * @param {string} userId - User ID
   * @returns {Promise<Array>} - Array of budgets
   */
  async getUserBudgets(userId) {
    const { data, error } = await supabase
      .from('budgets')
      .select('*, budget_categories(*)')
      .eq('user_id', userId);

    if (error) {
      throw new Error(`Failed to fetch budgets: ${error.message}`);
    }

    return data || [];
  }

  /**
   * Ambil budget berdasarkan kategori
   * @param {string} userId - User ID
   * @param {string} category - Kategori
   * @returns {Promise<Object|null>}
   */
  async getBudgetByCategory(userId, category) {
    const { data, error } = await supabase
      .from('budgets')
      .select('*')
      .eq('user_id', userId)
      .eq('category', category)
      .single();

    if (error && error.code !== 'PGRST116') {
      throw new Error(`Failed to fetch budget: ${error.message}`);
    }

    return data || null;
  }
}

module.exports = new BudgetRepository();

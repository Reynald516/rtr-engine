const supabase = require('../utils/supabase');

class TransactionRepository {
  /**
   * Ambil semua transaksi user hari ini
   * @param {string} userId - User ID
   * @returns {Promise<Array>} - Array of transactions
   */
  async getTodayTransactions(userId) {
    const today = new Date().toISOString().split('T')[0];
    
    const { data, error } = await supabase
      .from('transactions')
      .select('*')
      .eq('user_id', userId)
      .gte('created_at', `${today}T00:00:00`)
      .lt('created_at', `${today}T23:59:59`);

    if (error) {
      throw new Error(`Failed to fetch transactions: ${error.message}`);
    }

    return data || [];
  }

  /**
   * Ambil transaksi user untuk periode tertentu
   * @param {string} userId - User ID
   * @param {number} days - Jumlah hari ke belakang
   * @returns {Promise<Array>} - Array of transactions
   */
  async getTransactionsForPeriod(userId, days) {
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    
    const { data, error } = await supabase
      .from('transactions')
      .select('*')
      .eq('user_id', userId)
      .gte('created_at', startDate.toISOString());

    if (error) {
      throw new Error(`Failed to fetch transactions: ${error.message}`);
    }

    return data || [];
  }
}

module.exports = new TransactionRepository();

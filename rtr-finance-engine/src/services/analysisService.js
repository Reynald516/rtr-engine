const transactionRepository = require('../repositories/transactionRepository');
const analysisRepository = require('../repositories/analysisRepository');

class AnalysisService {
  /**
   * Hitung total income dan expense dari transaksi
   * @param {Array} transactions - Array of transactions
   * @returns {Object} - { total_income, total_expense, net_cashflow }
   */
  calculateMetrics(transactions) {
    let totalIncome = 0;
    let totalExpense = 0;

    for (const tx of transactions) {
      if (tx.type === 'income') {
        totalIncome += tx.amount;
      } else if (tx.type === 'expense') {
        totalExpense += tx.amount;
      }
    }

    return {
      total_income: totalIncome,
      total_expense: totalExpense,
      net_cashflow: totalIncome - totalExpense
    };
  }

  /**
   * Tentukan dominant category (kategori paling sering muncul)
   * @param {Array} transactions - Array of transactions
   * @returns {string} - Dominant category
   */
  getDominantCategory(transactions) {
    const expenseTxs = transactions.filter(tx => tx.type === 'expense');
    
    if (expenseTxs.length === 0) {
      return null;
    }

    const categoryCount = {};
    for (const tx of expenseTxs) {
      const category = tx.category || 'unknown';
      categoryCount[category] = (categoryCount[category] || 0) + 1;
    }

    let maxCount = 0;
    let dominantCategory = 'unknown';
    
    for (const [category, count] of Object.entries(categoryCount)) {
      if (count > maxCount) {
        maxCount = count;
        dominantCategory = category;
      }
    }

    return dominantCategory;
  }

  /**
   * Tentukan risk level berdasarkan kondisi keuangan
   * @param {number} totalIncome - Total income
   * @param {number} totalExpense - Total expense
   * @returns {string} - Risk level: 'high', 'medium', atau 'low'
   */
  determineRiskLevel(totalIncome, totalExpense) {
    if (totalExpense > totalIncome) {
      return 'high';
    } else if (totalExpense === totalIncome) {
      return 'medium';
    } else {
      // Check if expense is more than 80% of income
      const ratio = totalExpense / totalIncome;
      if (ratio > 0.8) {
        return 'medium';
      }
      return 'low';
    }
  }

  /**
   * Deteksi anomaly berdasarkan expense vs rata-rata harian
   * @param {Array} transactions - Array of transactions
   * @param {number} averageDailyExpense - Rata-rata expense harian
   * @returns {boolean} - True jika ada anomaly
   */
  detectAnomaly(transactions, averageDailyExpense = 0) {
    const totalExpense = transactions
      .filter(tx => tx.type === 'expense')
      .reduce((sum, tx) => sum + tx.amount, 0);

    // Jika expense > 2x rata-rata, dianggap anomaly
    if (averageDailyExpense > 0 && totalExpense > averageDailyExpense * 2) {
      return true;
    }

    // Jika expense > 1 juta dan tidak ada income, dianggap anomaly
    if (totalExpense > 1000000) {
      const hasIncome = transactions.some(tx => tx.type === 'income');
      if (!hasIncome) {
        return true;
      }
    }

    return false;
  }

  /**
   * Hitung rata-rata expense harian dari 7 hari terakhir
   * @param {string} userId - User ID
   * @returns {Promise<number>} - Rata-rata expense harian
   */
  async calculateAverageDailyExpense(userId) {
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const { data, error } = await supabase
      .from('transactions')
      .select('amount')
      .eq('user_id', userId)
      .eq('type', 'expense')
      .gte('created_at', sevenDaysAgo.toISOString());

    if (error || !data || data.length === 0) {
      return 0;
    }

    const totalExpense = data.reduce((sum, tx) => sum + tx.amount, 0);
    return totalExpense / 7;
  }

  /**
   * Buat AI-style summary
   * @param {Object} analysisData - Data analisis
   * @returns {string} - Summary
   */
  generateSummary(analysisData) {
    const { total_income, total_expense, dominant_category, risk_level, anomaly } = analysisData;
    
    let summary = `Hari ini kamu pengeluaran Rp ${total_expense.toLocaleString('id-ID')}`;
    
    if (dominant_category) {
      summary += ` dengan kategori terbesar ${dominant_category}`;
    }
    
    summary += `. Kondisi keuanganmu ${risk_level === 'high' ? 'perlu perhatian' : risk_level === 'medium' ? 'seimbang' : 'stabil'}.`;
    
    if (anomaly) {
      summary += ` Terdeteksi transaksi tidak biasa hari ini.`;
    }
    
    return summary;
  }

  /**
   * Bandingkan dengan hari sebelumnya
   * @param {Object} currentAnalysis - Analisis hari ini
   * @param {Object|null} previousAnalysis - Analisis hari sebelumnya
   * @returns {Object} - { expense_change, income_change, risk_change }
   */
  compareWithPrevious(currentAnalysis, previousAnalysis) {
    if (!previousAnalysis) {
      return {
        expense_change: 0,
        income_change: 0,
        risk_change: 'new'
      };
    }

    const expenseChange = currentAnalysis.total_expense - previousAnalysis.total_expense;
    const incomeChange = currentAnalysis.total_income - previousAnalysis.total_income;
    
    // Risk change
    const riskLevels = { 'low': 1, 'medium': 2, 'high': 3 };
    const currentRisk = riskLevels[currentAnalysis.risk_level] || 2;
    const previousRisk = riskLevels[previousAnalysis.risk_level] || 2;
    
    let riskChange;
    if (currentRisk > previousRisk) {
      riskChange = 'increased';
    } else if (currentRisk < previousRisk) {
      riskChange = 'decreased';
    } else {
      riskChange = 'stable';
    }

    return {
      expense_change: expenseChange,
      income_change: incomeChange,
      risk_change: riskChange
    };
  }
}

module.exports = new AnalysisService();

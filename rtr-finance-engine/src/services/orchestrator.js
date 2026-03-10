const transactionRepository = require('../repositories/transactionRepository');
const analysisRepository = require('../repositories/analysisRepository');
const analysisService = require('./analysisService');

/**
 * Main Orchestrator - runDailyAnalysis
 * 
 * Alur:
 * 1. Ambil semua transaksi user hari ini
 * 2. Hitung: total_income, total_expense, net_cashflow
 * 3. Analisa: dominant_category, risk_level
 * 4. Deteksi anomaly
 * 5. Simpan ke user_analysis
 * 6. Bandingkan dengan hari sebelumnya
 * 7. Simpan ke user_behavior_analysis
 * 
 * @param {string} userId - User ID
 * @returns {Object} - Hasil analisis lengkap
 */
async function runDailyAnalysis(userId) {
  try {
    console.log(`[Orchestrator] Starting daily analysis for user: ${userId}`);

    // Step 1: Ambil semua transaksi user hari ini
    const transactions = await transactionRepository.getTodayTransactions(userId);
    console.log(`[Orchestrator] Found ${transactions.length} transactions today`);

    // Step 2: Hitung metrics (total_income, total_expense, net_cashflow)
    const metrics = analysisService.calculateMetrics(transactions);
    console.log(`[Orchestrator] Metrics:`, metrics);

    // Step 3: Analisa - dominant_category & risk_level
    const dominantCategory = analysisService.getDominantCategory(transactions);
    const riskLevel = analysisService.determineRiskLevel(metrics.total_income, metrics.total_expense);
    
    console.log(`[Orchestrator] Dominant category: ${dominantCategory}`);
    console.log(`[Orchestrator] Risk level: ${riskLevel}`);

    // Step 4: Deteksi anomaly
    // Hitung rata-rata expense harian dari 7 hari terakhir
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    
    const recentTransactions = await transactionRepository.getTransactionsForPeriod(userId, 7);
    const recentExpenses = recentTransactions.filter(tx => tx.type === 'expense');
    const averageDailyExpense = recentExpenses.length > 0 
      ? recentExpenses.reduce((sum, tx) => sum + tx.amount, 0) / 7 
      : 0;
    
    const anomaly = analysisService.detectAnomaly(transactions, averageDailyExpense);
    console.log(`[Orchestrator] Anomaly detected: ${anomaly}`);

    // Step 5: Siapkan data untuk disimpan
    const analysisData = {
      user_id: userId,
      total_income: metrics.total_income,
      total_expense: metrics.total_expense,
      dominant_category: dominantCategory,
      risk_level: riskLevel,
      anomaly: anomaly,
      summary: analysisService.generateSummary({
        total_income: metrics.total_income,
        total_expense: metrics.total_expense,
        dominant_category: dominantCategory,
        risk_level: riskLevel,
        anomaly: anomaly
      })
    };

    // Simpan ke user_analysis
    const savedAnalysis = await analysisRepository.saveAnalysis(analysisData);
    console.log(`[Orchestrator] Analysis saved:`, savedAnalysis.id);

    // Step 6: Bandingkan dengan hari sebelumnya
    const previousAnalysis = await analysisRepository.getLastAnalysis(userId);
    const comparison = analysisService.compareWithPrevious(analysisData, previousAnalysis);
    console.log(`[Orchestrator] Comparison with previous:`, comparison);

    // Step 7: Simpan ke user_behavior_analysis
    const behaviorData = {
      user_id: userId,
      expense_change: comparison.expense_change,
      income_change: comparison.income_change,
      risk_change: comparison.risk_change,
      notes: generateBehaviorNotes(comparison, analysisData)
    };

    await analysisRepository.saveBehaviorAnalysis(behaviorData);
    console.log(`[Orchestrator] Behavior analysis saved`);

    // Return hasil lengkap
    return {
      success: true,
      user_id: userId,
      analysis_date: new Date().toISOString().split('T')[0],
      transactions_count: transactions.length,
      metrics: metrics,
      dominant_category: dominantCategory,
      risk_level: riskLevel,
      anomaly: anomaly,
      summary: analysisData.summary,
      comparison: comparison,
      behavior_notes: behaviorData.notes
    };

  } catch (error) {
    console.error(`[Orchestrator] Error:`, error.message);
    return {
      success: false,
      user_id: userId,
      error: error.message
    };
  }
}

/**
 * Generate behavior notes berdasarkan perbandingan
 */
function generateBehaviorNotes(comparison, analysisData) {
  const notes = [];

  // Expense change
  if (comparison.expense_change > 0) {
    notes.push(`Pengeluaran naik Rp ${comparison.expense_change.toLocaleString('id-ID')} dari kemarin`);
  } else if (comparison.expense_change < 0) {
    notes.push(`Pengeluaran turun Rp ${Math.abs(comparison.expense_change).toLocaleString('id-ID')} dari kemarin`);
  }

  // Income change
  if (comparison.income_change > 0) {
    notes.push(`Pemasukan naik Rp ${comparison.income_change.toLocaleString('id-ID')} dari kemarin`);
  } else if (comparison.income_change < 0) {
    notes.push(`Pemasukan turun Rp ${Math.abs(comparison.income_change).toLocaleString('id-ID')} dari kemarin`);
  }

  // Risk change
  if (comparison.risk_change === 'increased') {
    notes.push('Tingkat risiko meningkat');
  } else if (comparison.risk_change === 'decreased') {
    notes.push('Tingkat risiko menurun');
  }

  // Anomaly
  if (analysisData.anomaly) {
    notes.push('Terdeteksi transaksi tidak biasa');
  }

  return notes.length > 0 ? notes : ['Tidak ada perubahan signifikan'];
}

module.exports = {
  runDailyAnalysis
};

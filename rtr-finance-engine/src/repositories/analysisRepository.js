const supabase = require('../utils/supabase');

class AnalysisRepository {
  /**
   * Ambil analisis terakhir user
   * @param {string} userId - User ID
   * @returns {Promise<Object|null>} - Analisis terakhir atau null
   */
  async getLastAnalysis(userId) {
    const { data, error } = await supabase
      .from('user_analysis')
      .select('*')
      .eq('user_id', userId)
      .order('analysis_date', { ascending: false })
      .limit(1)
      .single();

    if (error && error.code !== 'PGRST116') {
      throw new Error(`Failed to fetch last analysis: ${error.message}`);
    }

    return data || null;
  }

  /**
   * Simpan analisis ke table user_analysis
   * @param {Object} analysisData - Data analisis
   * @returns {Promise<Object>} - Data yang disimpan
   */
  async saveAnalysis(analysisData) {
    const { data, error } = await supabase
      .from('user_analysis')
      .upsert({
        user_id: analysisData.user_id,
        analysis_date: new Date().toISOString().split('T')[0],
        total_income: analysisData.total_income,
        total_expense: analysisData.total_expense,
        dominant_category: analysisData.dominant_category,
        risk_level: analysisData.risk_level,
        anomaly: analysisData.anomaly,
        summary: analysisData.summary,
      }, {
        onConflict: 'user_id,analysis_date'
      })
      .select()
      .single();

    if (error) {
      throw new Error(`Failed to save analysis: ${error.message}`);
    }

    return data;
  }

  /**
   * Ambil behavior analysis terakhir
   * @param {string} userId - User ID
   * @returns {Promise<Object|null>}
   */
  async getLastBehaviorAnalysis(userId) {
    const { data, error } = await supabase
      .from('user_behavior_analysis')
      .select('*')
      .eq('user_id', userId)
      .order('analysis_date', { ascending: false })
      .limit(1)
      .single();

    if (error && error.code !== 'PGRST116') {
      throw new Error(`Failed to fetch behavior analysis: ${error.message}`);
    }

    return data || null;
  }

  /**
   * Simpan behavior analysis
   * @param {Object} behaviorData - Data behavior
   * @returns {Promise<Object>}
   */
  async saveBehaviorAnalysis(behaviorData) {
    const { data, error } = await supabase
      .from('user_behavior_analysis')
      .upsert({
        user_id: behaviorData.user_id,
        analysis_date: new Date().toISOString().split('T')[0],
        expense_change: behaviorData.expense_change,
        income_change: behaviorData.income_change,
        risk_change: behaviorData.risk_change,
        notes: behaviorData.notes,
      }, {
        onConflict: 'user_id,analysis_date'
      })
      .select()
      .single();

    if (error) {
      throw new Error(`Failed to save behavior analysis: ${error.message}`);
    }

    return data;
  }
}

module.exports = new AnalysisRepository();

/**
 * RTR Finance Engine - Main Entry Point
 * 
 * Usage:
 * const { runDailyAnalysis } = require('./src/index');
 * 
 * await runDailyAnalysis('user-uuid-here');
 */

const { runDailyAnalysis } = require('./services/orchestrator');
const analysisService = require('./services/analysisService');
const transactionRepository = require('./repositories/transactionRepository');
const analysisRepository = require('./repositories/analysisRepository');
const budgetRepository = require('./repositories/budgetRepository');

module.exports = {
  runDailyAnalysis,
  analysisService,
  transactionRepository,
  analysisRepository,
  budgetRepository
};

// CLI usage
if (require.main === module) {
  const userId = process.argv[2];
  
  if (!userId) {
    console.log('Usage: node src/index.js <user_id>');
    process.exit(1);
  }

  console.log('Starting RTR Finance Engine...\n');
  
  runDailyAnalysis(userId)
    .then(result => {
      console.log('\n=== RESULT ===');
      console.log(JSON.stringify(result, null, 2));
    })
    .catch(error => {
      console.error('Error:', error);
      process.exit(1);
    });
}

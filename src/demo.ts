/**
 * 企業価値評価システムのデモスクリプト
 * 実際の企業データを使用してシステム全体の動作確認
 */

import { 
  computeValuation, 
  generateSensitivityScenarios,
  type Inputs 
} from './lib/valuation/compute.js';
import { 
  generateValuationReport, 
  generateSimpleReport,
  type ReportDependencies 
} from './reports/generateValuationReport.js';
import { toYen, toShares } from './lib/units/normalizeUnits.js';

// デモ用企業データ（架空のテック企業）
const demoInputs: Inputs = {
  companyName: 'テックイノベーション株式会社',
  valuationDate: new Date('2024-03-31'),
  
  // 発行済株式数: 100万株
  sharesOutstanding: toShares(1000, '千株'),
  
  // ネット有利子負債: 37.9億円
  netDebtYen: toYen(3790, '百万円'),
  
  // EV手法による企業価値推計
  evByMethod: {
    'EV/Sales': toYen(5062, '百万円'),    // 売上倍率2.5x × 売上20.25億円
    'EV/EBITDA': toYen(4860, '百万円')    // EBITDA倍率12x × EBITDA4.05億円
  },
  
  // P/E手法による株価推計: 1,234円/株
  pePrice: 1234,
  
  // 手法別重み（保守的にEV手法重視）
  weights: {
    'EV/Sales': 0.4,
    'EV/EBITDA': 0.4,
    'P/E': 0.2
  }
};

// レポート生成用の依存関数
const dependencies: ReportDependencies = {
  generateSensitivityScenarios,
  computeValuation
};

async function runDemo() {
  console.log('🚀 企業価値評価システム デモ開始');
  console.log('=' .repeat(60));
  
  try {
    // 1. 基本的な企業価値評価
    console.log('\n📊 Step 1: 企業価値評価実行');
    const result = computeValuation(demoInputs);
    
    if (!result.success) {
      console.error('❌ 評価に失敗しました:');
      result.errors.forEach(error => console.error(`  - ${error}`));
      return;
    }
    
    // 2. 簡易レポート表示
    console.log('\n📈 Step 2: 評価結果サマリー');
    const simpleReport = generateSimpleReport(result);
    console.log(simpleReport);
    
    // 3. 感応度分析
    console.log('\n🔍 Step 3: 感応度分析');
    const scenarios = generateSensitivityScenarios(demoInputs, 0.1, 0.1);
    console.log(`${scenarios.length}種類のシナリオを生成しました:`);
    
    scenarios.forEach((scenario, index) => {
      const scenarioResult = computeValuation(scenario.inputs);
      const targetPrice = scenarioResult.summary.weighted || scenarioResult.summary.avg;
      console.log(`  ${index + 1}. ${scenario.scenario}: ${targetPrice ? `¥${targetPrice.toLocaleString()}` : 'N/A'}`);
    });
    
    // 4. 詳細レポート生成
    console.log('\n📝 Step 4: 詳細レポート生成');
    const reportPath = generateValuationReport(
      result,
      {
        fileName: 'demo-valuation-report',
        includeSensitivity: true,
        includeDetailedBridge: true,
        includeDiagnostics: true,
        includeExecutiveSummary: true
      },
      dependencies
    );
    
    console.log(`✅ レポートを生成しました: ${reportPath}`);
    
    // 5. 警告とエラーの表示
    if (result.warnings.length > 0) {
      console.log('\n⚠️ 警告事項:');
      result.warnings.forEach(warning => console.log(`  - ${warning}`));
    }
    
    // 6. 実装統計
    console.log('\n📈 実装統計:');
    console.log(`  - 採用手法数: ${result.summary.validMethodCount}/3`);
    console.log(`  - 価格レンジ: ¥${result.summary.range[0].toLocaleString()} - ¥${result.summary.range[1].toLocaleString()}`);
    console.log(`  - 標準偏差: ¥${Math.sqrt(
      result.bridges
        .filter(b => b.used)
        .map(b => Math.pow(b.PricePerShare - result.summary.avg, 2))
        .reduce((a, b) => a + b, 0) / result.summary.validMethodCount
    ).toFixed(0)}`);
    
    console.log('\n🎉 デモ完了！すべての機能が正常に動作しています。');
    
  } catch (error) {
    console.error('💥 デモ実行中にエラーが発生しました:', error);
  }
}

// エッジケースのテスト
function runEdgeCaseTests() {
  console.log('\n🧪 エッジケーステスト開始');
  console.log('=' .repeat(40));
  
  const testCases = [
    {
      name: '債務超過ケース',
      inputs: {
        ...demoInputs,
        netDebtYen: toYen(10000, '百万円'), // 100億円の負債
        evByMethod: { 'EV/Sales': toYen(5000, '百万円') } // 50億円のEV
      }
    },
    {
      name: 'EBITDA負値ケース', 
      inputs: {
        ...demoInputs,
        evByMethod: {
          'EV/Sales': toYen(3000, '百万円'),
          'EV/EBITDA': -toYen(500, '百万円') // 負のEV
        }
      }
    },
    {
      name: '単一手法ケース',
      inputs: {
        ...demoInputs,
        evByMethod: { 'EV/Sales': toYen(4000, '百万円') },
        pePrice: undefined
      }
    }
  ];
  
  testCases.forEach(testCase => {
    console.log(`\n🔬 ${testCase.name}:`);
    const result = computeValuation(testCase.inputs);
    
    if (result.success) {
      console.log(`  ✅ 成功 - 有効手法数: ${result.summary.validMethodCount}`);
      console.log(`  💰 加重平均株価: ¥${result.summary.weighted?.toLocaleString() || 'N/A'}`);
    } else {
      console.log(`  ❌ 失敗 - エラー数: ${result.errors.length}`);
    }
    
    if (result.warnings.length > 0) {
      console.log(`  ⚠️ 警告数: ${result.warnings.length}`);
    }
  });
}

// メイン実行
if (import.meta.url === `file://${process.argv[1]}`) {
  runDemo()
    .then(() => runEdgeCaseTests())
    .then(() => {
      console.log('\n🏁 全デモ完了');
      process.exit(0);
    })
    .catch(error => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}
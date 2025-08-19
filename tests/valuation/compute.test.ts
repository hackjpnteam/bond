/**
 * 企業価値算定ロジックのテストスイート
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { 
  computeValuation,
  generateSensitivityScenarios,
  type Inputs,
  type Method,
  type ValuationResult
} from '../../src/lib/valuation/compute.js';

describe('computeValuation', () => {
  let standardInputs: Inputs;

  beforeEach(() => {
    standardInputs = {
      sharesOutstanding: 1_000_000, // 100万株
      netDebtYen: 3_790_000_000,    // 37.9億円
      evByMethod: {
        'EV/Sales': 5_062_000_000,  // 50.62億円
        'EV/EBITDA': 4_860_000_000  // 48.6億円
      },
      pePrice: 1_234,               // 1,234円/株
      companyName: 'テスト株式会社',
      valuationDate: new Date('2024-03-31')
    };
  });

  it('標準的なケースでの算定', () => {
    const result = computeValuation(standardInputs);
    
    expect(result.success).toBe(true);
    expect(result.summary.validMethodCount).toBe(3);
    expect(result.summary.usedMethods).toEqual(['EV/Sales', 'EV/EBITDA', 'P/E']);
    
    // ブリッジ計算の検証
    const evSalesBridge = result.bridges.find(b => b.method === 'EV/Sales');
    expect(evSalesBridge?.used).toBe(true);
    expect(evSalesBridge?.EV).toBe(5_062_000_000);
    expect(evSalesBridge?.Equity).toBe(5_062_000_000 - 3_790_000_000); // 1,272,000,000
    expect(evSalesBridge?.PricePerShare).toBe(1_272); // 1,272円/株

    const evEbitdaBridge = result.bridges.find(b => b.method === 'EV/EBITDA');
    expect(evEbitdaBridge?.used).toBe(true);
    expect(evEbitdaBridge?.EV).toBe(4_860_000_000);
    expect(evEbitdaBridge?.Equity).toBe(4_860_000_000 - 3_790_000_000); // 1,070,000,000
    expect(evEbitdaBridge?.PricePerShare).toBe(1_070); // 1,070円/株

    const peBridge = result.bridges.find(b => b.method === 'P/E');
    expect(peBridge?.used).toBe(true);
    expect(peBridge?.PricePerShare).toBe(1_234);

    // 統計値の検証
    expect(result.summary.range[0]).toBeGreaterThan(0);
    expect(result.summary.range[1]).toBeGreaterThan(result.summary.range[0]);
    expect(result.summary.avg).toBeCloseTo((1272 + 1070 + 1234) / 3, 0);
  });

  it('EBITDA<=0の場合のスキップテスト', () => {
    const inputsWithNegativeEbitda: Inputs = {
      ...standardInputs,
      evByMethod: {
        'EV/Sales': 5_000_000_000,
        'EV/EBITDA': -1_000_000_000 // 負のEV（EBITDA<=0を想定）
      }
    };

    const result = computeValuation(inputsWithNegativeEbitda);
    
    // 負のEVは無効として扱われるため、EV/EBITDAは使用されず、valid methodは2つ
    expect(result.success).toBe(true);
    expect(result.summary.validMethodCount).toBe(2); // EV/Sales と P/E のみ
    expect(result.summary.usedMethods).toEqual(['EV/Sales', 'P/E']);
    
    const evEbitdaBridge = result.bridges.find(b => b.method === 'EV/EBITDA');
    expect(evEbitdaBridge?.used).toBe(false);
    expect(evEbitdaBridge?.skipReason).toBe('EBITDA <= 0 or invalid EV');
    
    // 警告メッセージの確認（EBITDA手法スキップと重み調整の警告が出る）
    expect(result.warnings.length).toBeGreaterThan(0);
    expect(result.warnings.some(w => w.includes('EV/EBITDA手法をスキップ'))).toBe(true);
  });

  it('株主価値が負になる場合の処理', () => {
    const inputsWithHighDebt: Inputs = {
      ...standardInputs,
      netDebtYen: 10_000_000_000, // 100億円（EVより大きい負債）
      evByMethod: {
        'EV/Sales': 5_000_000_000   // 50億円のEV
      }
    };

    const result = computeValuation(inputsWithHighDebt);
    
    const bridge = result.bridges.find(b => b.method === 'EV/Sales');
    expect(bridge?.used).toBe(false);
    expect(bridge?.Equity).toBe(-5_000_000_000); // 負の株主価値
    expect(bridge?.PricePerShare).toBe(0); // 負の場合は0に設定
    expect(bridge?.skipReason).toContain('Negative equity value');
    
    expect(result.warnings.length).toBeGreaterThan(0);
    expect(result.warnings[0]).toContain('株主価値が負になりました');
  });

  it('入力データの検証エラー', () => {
    const invalidInputs: Inputs = {
      sharesOutstanding: -1000,      // 負の株式数
      netDebtYen: NaN,              // 無効なネット負債
      evByMethod: {},               // 空のEVデータ
    };

    const result = computeValuation(invalidInputs);
    
    expect(result.success).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
    expect(result.errors).toContain('Invalid shares outstanding: -1000');
    expect(result.errors).toContain('Invalid net debt: NaN');
    expect(result.errors).toContain('No valid valuation methods provided');
  });

  it('部分的なデータでの算定', () => {
    const partialInputs: Inputs = {
      sharesOutstanding: 500_000,
      netDebtYen: 1_000_000_000,
      evByMethod: {
        'EV/Sales': 3_000_000_000
      }
      // P/E価格なし、EV/EBITDAなし
    };

    const result = computeValuation(partialInputs);
    
    expect(result.success).toBe(true);
    expect(result.summary.validMethodCount).toBe(1);
    expect(result.summary.usedMethods).toEqual(['EV/Sales']);
    
    // 単一手法の場合、平均・中央値・加重平均は同じ値
    const expectedPrice = (3_000_000_000 - 1_000_000_000) / 500_000; // 4,000円
    expect(result.summary.avg).toBe(expectedPrice);
    expect(result.summary.median).toBe(expectedPrice);
    expect(result.summary.range[0]).toBe(expectedPrice);
    expect(result.summary.range[1]).toBe(expectedPrice);
  });

  it('ネットキャッシュ（負のネット負債）の処理', () => {
    const inputsWithNetCash: Inputs = {
      ...standardInputs,
      netDebtYen: -1_000_000_000, // ネットキャッシュ10億円
      evByMethod: {
        'EV/Sales': 3_000_000_000
      }
    };

    const result = computeValuation(inputsWithNetCash);
    
    const bridge = result.bridges.find(b => b.method === 'EV/Sales');
    expect(bridge?.Equity).toBe(3_000_000_000 + 1_000_000_000); // EV + キャッシュ
    expect(bridge?.PricePerShare).toBe(4_000); // 4,000円/株
    expect(bridge?.used).toBe(true);
  });

  it('重み付け設定のカスタマイズ', () => {
    const inputsWithWeights: Inputs = {
      ...standardInputs,
      weights: {
        'EV/Sales': 0.6,
        'EV/EBITDA': 0.3,
        'P/E': 0.1
      }
    };

    const result = computeValuation(inputsWithWeights);
    
    expect(result.success).toBe(true);
    
    // 手動で加重平均を計算して検証
    const expectedWeighted = 1272 * 0.6 + 1070 * 0.3 + 1234 * 0.1;
    expect(result.summary.weighted).toBeCloseTo(expectedWeighted, 0);
  });

  it('全ての手法が無効な場合', () => {
    const allInvalidInputs: Inputs = {
      sharesOutstanding: 1_000_000,
      netDebtYen: 5_000_000_000,
      evByMethod: {
        'EV/Sales': 1_000_000_000,    // EVより大きなネット負債で株主価値が負
        'EV/EBITDA': 1_500_000_000    // EVより大きなネット負債で株主価値が負
      }
      // P/E価格なし
    };

    const result = computeValuation(allInvalidInputs);
    
    expect(result.success).toBe(false); // 有効な手法がないため失敗
    expect(result.summary.validMethodCount).toBe(0);
    expect(result.summary.usedMethods).toEqual([]);
    expect(Number.isNaN(result.summary.avg)).toBe(true);
  });
});

describe('generateSensitivityScenarios', () => {
  let baseInputs: Inputs;

  beforeEach(() => {
    baseInputs = {
      sharesOutstanding: 1_000_000,
      netDebtYen: 2_000_000_000,
      evByMethod: {
        'EV/Sales': 5_000_000_000,
        'EV/EBITDA': 4_500_000_000
      },
      pePrice: 1_200
    };
  });

  it('感応度シナリオ生成', () => {
    const scenarios = generateSensitivityScenarios(baseInputs, 0.1, 0.15);
    
    // ベースケース + ネット負債±10% + EV/Sales±15% + EV/EBITDA±15% + P/E±15%
    expect(scenarios.length).toBe(9); // 1 + 2 + 2 + 2 + 2 = 9シナリオ
    
    // ベースケース
    expect(scenarios[0].scenario).toBe('Base Case');
    expect(scenarios[0].inputs).toEqual(baseInputs);
    
    // ネット負債感応度
    const netDebtUpScenario = scenarios.find(s => s.scenario.includes('ネット負債 +10%'));
    expect(netDebtUpScenario?.inputs.netDebtYen).toBe(2_000_000_000 * 1.1);
    
    const netDebtDownScenario = scenarios.find(s => s.scenario.includes('ネット負債 -10%'));
    expect(netDebtDownScenario?.inputs.netDebtYen).toBe(2_000_000_000 * 0.9);
    
    // EV倍率感応度
    const evSalesUpScenario = scenarios.find(s => s.scenario.includes('EV/Sales +15%'));
    expect(evSalesUpScenario?.inputs.evByMethod['EV/Sales']).toBe(5_000_000_000 * 1.15);
    
    // P/E感応度
    const peUpScenario = scenarios.find(s => s.scenario.includes('P/E +15%'));
    expect(peUpScenario?.inputs.pePrice).toBe(1_200 * 1.15);
  });

  it('デフォルトパラメータでの感応度分析', () => {
    const scenarios = generateSensitivityScenarios(baseInputs);
    
    // デフォルト±10%での感応度分析
    const netDebtUp = scenarios.find(s => s.scenario.includes('ネット負債 +10%'));
    expect(netDebtUp?.inputs.netDebtYen).toBe(2_000_000_000 * 1.1);
  });

  it('一部手法のみでの感応度分析', () => {
    const limitedInputs: Inputs = {
      sharesOutstanding: 1_000_000,
      netDebtYen: 1_000_000_000,
      evByMethod: {
        'EV/Sales': 3_000_000_000
        // EV/EBITDAなし
      }
      // P/E価格なし
    };

    const scenarios = generateSensitivityScenarios(limitedInputs);
    
    // ベースケース + ネット負債±10% + EV/Sales±10% = 5シナリオ
    expect(scenarios.length).toBe(5);
    
    // EV/EBITDAとP/Eのシナリオは生成されない
    const evEbitdaScenario = scenarios.find(s => s.scenario.includes('EV/EBITDA'));
    const peScenario = scenarios.find(s => s.scenario.includes('P/E'));
    expect(evEbitdaScenario).toBeUndefined();
    expect(peScenario).toBeUndefined();
  });
});

// 数値精度テスト
describe('数値精度と境界値', () => {
  it('極小値での算定精度', () => {
    const microInputs: Inputs = {
      sharesOutstanding: 1,
      netDebtYen: 1,
      evByMethod: {
        'EV/Sales': 1000
      }
    };

    const result = computeValuation(microInputs);
    expect(result.success).toBe(true);
    expect(result.bridges[0].PricePerShare).toBe(999); // 1000 - 1 = 999
  });

  it('巨大数値での算定', () => {
    const largeInputs: Inputs = {
      sharesOutstanding: 1_000_000_000, // 10億株
      netDebtYen: 1_000_000_000_000,    // 1兆円
      evByMethod: {
        'EV/Sales': 5_000_000_000_000   // 5兆円
      }
    };

    const result = computeValuation(largeInputs);
    expect(result.success).toBe(true);
    expect(Number.isFinite(result.summary.avg)).toBe(true);
    expect(result.bridges[0].PricePerShare).toBe(4000); // (5兆 - 1兆) / 10億 = 4000円
  });

  it('ゼロ値での境界テスト', () => {
    const zeroDebtInputs: Inputs = {
      sharesOutstanding: 1_000_000,
      netDebtYen: 0, // ネット負債ゼロ
      evByMethod: {
        'EV/Sales': 2_000_000_000
      }
    };

    const result = computeValuation(zeroDebtInputs);
    expect(result.success).toBe(true);
    expect(result.bridges[0].Equity).toBe(2_000_000_000); // EV = Equity
    expect(result.bridges[0].PricePerShare).toBe(2000);
  });
});

// パフォーマンステスト（簡易）
describe('パフォーマンス', () => {
  it('大量のシナリオ計算でのパフォーマンス', () => {
    const baseInputs: Inputs = {
      sharesOutstanding: 1_000_000,
      netDebtYen: 3_000_000_000,
      evByMethod: {
        'EV/Sales': 5_000_000_000,
        'EV/EBITDA': 4_500_000_000
      },
      pePrice: 1_500
    };

    const startTime = performance.now();
    
    // 100回の算定実行
    for (let i = 0; i < 100; i++) {
      computeValuation(baseInputs);
    }
    
    const endTime = performance.now();
    const executionTime = endTime - startTime;
    
    // 100回の実行が1秒以内に完了することを確認
    expect(executionTime).toBeLessThan(1000);
  });
});
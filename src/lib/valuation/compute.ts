/**
 * 堅牢な企業価値算定ロジック
 * Fintech実務レベルの計算精度とエラーハンドリングを実装
 */

import { formatJPY, formatMultiple, formatRange } from '../formatters/currency.js';

/**
 * 評価手法の種類
 */
export type Method = 'EV/Sales' | 'EV/EBITDA' | 'P/E';

/**
 * 企業価値算定の入力パラメータ
 */
export interface Inputs {
  /** 発行済株式数（株） */
  sharesOutstanding: number;
  /** ネット有利子負債（円、正値=負債超過、負値=ネットキャッシュ） */
  netDebtYen: number;
  /** 手法別のEV推計値（円） */
  evByMethod: Partial<Record<Method, number>>;
  /** P/E手法による株価（円/株）直接指定 */
  pePrice?: number;
  /** 手法別の重み（合計1.0推奨） */
  weights?: Partial<Record<Method, number>>;
  /** 計算対象企業名 */
  companyName?: string;
  /** 計算基準日 */
  valuationDate?: Date;
}

/**
 * 手法別ブリッジ表の行データ
 */
export interface Bridge {
  /** 評価手法 */
  method: Method;
  /** 企業価値（円） */
  EV: number;
  /** 株主価値（円） */
  Equity: number;
  /** 1株あたり価格（円/株） */
  PricePerShare: number;
  /** この手法を最終算定に使用するか */
  used: boolean;
  /** 使用しない理由（デバッグ用） */
  skipReason?: string;
}

/**
 * 評価サマリー統計
 */
export interface Summary {
  /** 平均株価 */
  avg: number;
  /** 中央値株価 */
  median: number;
  /** 加重平均株価 */
  weighted: number;
  /** 価格レンジ [最低価格, 最高価格] */
  range: [number, number];
  /** 有効な手法の数 */
  validMethodCount: number;
  /** 使用された手法名 */
  usedMethods: Method[];
}

/**
 * 算定結果の詳細データ
 */
export interface ValuationResult {
  /** 手法別ブリッジ表 */
  bridges: Bridge[];
  /** 統計サマリー */
  summary: Summary;
  /** 入力データのスナップショット */
  inputs: Inputs;
  /** 警告メッセージ */
  warnings: string[];
  /** エラーメッセージ */
  errors: string[];
  /** 算定成功フラグ */
  success: boolean;
}

/**
 * デフォルト重み設定（実務では業界特性に応じて調整）
 */
const DEFAULT_WEIGHTS: Record<Method, number> = {
  'EV/Sales': 0.4,
  'EV/EBITDA': 0.4,
  'P/E': 0.2,
};

/**
 * 配列から中央値を計算
 * @param arr - 数値配列
 * @returns 中央値
 */
function median(arr: number[]): number {
  if (arr.length === 0) return NaN;
  
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  
  return sorted.length % 2 !== 0 
    ? sorted[mid] 
    : (sorted[mid - 1] + sorted[mid]) / 2;
}

/**
 * 入力データの検証
 * @param inputs - 入力データ
 * @returns 検証結果
 */
function validateInputs(inputs: Inputs): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // 発行済株式数の検証
  if (!Number.isFinite(inputs.sharesOutstanding) || inputs.sharesOutstanding <= 0) {
    errors.push(`Invalid shares outstanding: ${inputs.sharesOutstanding}`);
  }

  // ネット有利子負債の検証（負の値も有効）
  if (!Number.isFinite(inputs.netDebtYen)) {
    errors.push(`Invalid net debt: ${inputs.netDebtYen}`);
  }

  // EVデータの検証（有効な手法が1つもない場合のみエラー）
  const evMethods = Object.keys(inputs.evByMethod) as Method[];
  const validEvMethods = evMethods.filter(method => {
    const ev = inputs.evByMethod[method];
    return ev !== undefined && Number.isFinite(ev) && ev > 0;
  });
  
  if (validEvMethods.length === 0 && !inputs.pePrice) {
    errors.push('No valid valuation methods provided');
  }

  // 個別のEV検証はwarning扱い（エラーではない）

  // P/E株価の検証
  if (inputs.pePrice !== undefined && (!Number.isFinite(inputs.pePrice) || inputs.pePrice <= 0)) {
    errors.push(`Invalid P/E price: ${inputs.pePrice}`);
  }

  return { valid: errors.length === 0, errors };
}

/**
 * 企業価値評価を実行
 * @param inputs - 算定パラメータ
 * @returns 算定結果
 */
export function computeValuation(inputs: Inputs): ValuationResult {
  const warnings: string[] = [];
  const bridges: Bridge[] = [];

  // 入力検証
  const validation = validateInputs(inputs);
  if (!validation.valid) {
    return {
      bridges: [],
      summary: {
        avg: NaN,
        median: NaN,
        weighted: NaN,
        range: [NaN, NaN],
        validMethodCount: 0,
        usedMethods: []
      },
      inputs,
      warnings,
      errors: validation.errors,
      success: false
    };
  }

  // 重み設定（デフォルト値をマージ）
  const weights = { ...DEFAULT_WEIGHTS, ...inputs.weights };

  /**
   * ブリッジ行を作成・追加する内部関数
   */
  const addBridge = (method: Method, ev?: number, directPrice?: number): void => {
    if (method === 'P/E') {
      // P/E手法は直接株価指定
      if (directPrice === undefined || !Number.isFinite(directPrice) || directPrice <= 0) {
        bridges.push({
          method,
          EV: NaN,
          Equity: NaN,
          PricePerShare: NaN,
          used: false,
          skipReason: 'No valid P/E price provided'
        });
        return;
      }

      bridges.push({
        method,
        EV: NaN, // P/E手法では企業価値は逆算
        Equity: directPrice * inputs.sharesOutstanding,
        PricePerShare: directPrice,
        used: true
      });
      return;
    }

    // EV系手法（EV/Sales, EV/EBITDA）
    if (ev === undefined || !Number.isFinite(ev) || ev <= 0) {
      bridges.push({
        method,
        EV: NaN,
        Equity: NaN,
        PricePerShare: NaN,
        used: false,
        skipReason: `Invalid EV: ${ev}`
      });
      return;
    }

    // EV → Equity変換
    const equity = ev - inputs.netDebtYen;
    
    // 株主価値が負の場合の処理
    if (equity <= 0) {
      bridges.push({
        method,
        EV: ev,
        Equity: equity,
        PricePerShare: 0, // 理論的には負だが、0に設定
        used: false,
        skipReason: `Negative equity value: ${formatJPY(equity)}`
      });
      
      warnings.push(
        `${method}: 株主価値が負になりました (EV: ${formatJPY(ev)}, ネット負債: ${formatJPY(inputs.netDebtYen)})`
      );
      return;
    }

    // 1株価値計算
    const pricePerShare = equity / inputs.sharesOutstanding;

    bridges.push({
      method,
      EV: ev,
      Equity: equity,
      PricePerShare: pricePerShare,
      used: true
    });
  };

  // 各手法のブリッジ計算
  addBridge('EV/Sales', inputs.evByMethod['EV/Sales']);
  
  // EBITDA手法の特別処理
  const evEbitda = inputs.evByMethod['EV/EBITDA'];
  if (evEbitda !== undefined && evEbitda > 0) {
    addBridge('EV/EBITDA', evEbitda);
  } else {
    bridges.push({
      method: 'EV/EBITDA',
      EV: NaN,
      Equity: NaN,
      PricePerShare: NaN,
      used: false,
      skipReason: 'EBITDA <= 0 or invalid EV'
    });
    
    if (evEbitda !== undefined) {
      warnings.push('EV/EBITDA手法をスキップ: EBITDA値が無効または負の値');
      // EV/Salesの重みを増加させる
      const evSalesUsed = bridges.find(b => b.method === 'EV/Sales')?.used;
      if (evSalesUsed) {
        weights['EV/Sales'] += weights['EV/EBITDA'];
        weights['EV/EBITDA'] = 0;
        warnings.push('EV/Sales手法の重みを調整しました');
      }
    }
  }

  addBridge('P/E', undefined, inputs.pePrice);

  // 有効な手法でのサマリー計算
  const validBridges = bridges.filter(b => b.used);
  const prices = validBridges.map(b => b.PricePerShare);
  const methods = validBridges.map(b => b.method);

  // 統計計算
  const avg = prices.length > 0 ? prices.reduce((sum, price) => sum + price, 0) / prices.length : NaN;
  const medianValue = prices.length > 0 ? median(prices) : NaN;
  
  // 加重平均計算（重みを正規化）
  let weighted = NaN;
  if (prices.length > 0) {
    const totalWeight = validBridges.reduce((sum, bridge) => sum + (weights[bridge.method] || 0), 0);
    
    if (totalWeight > 0) {
      weighted = validBridges.reduce((sum, bridge) => {
        const weight = (weights[bridge.method] || 0) / totalWeight;
        return sum + bridge.PricePerShare * weight;
      }, 0);
    } else {
      weighted = avg; // 重みが設定されていない場合は平均値を使用
      warnings.push('重みが設定されていないため、平均値を使用');
    }
  }

  const range: [number, number] = prices.length > 0 
    ? [Math.min(...prices), Math.max(...prices)]
    : [NaN, NaN];

  const summary: Summary = {
    avg,
    median: medianValue,
    weighted,
    range,
    validMethodCount: validBridges.length,
    usedMethods: methods
  };

  return {
    bridges,
    summary,
    inputs,
    warnings,
    errors: [],
    success: validBridges.length > 0
  };
}

/**
 * 感応度分析用のパラメータセット生成
 * @param baseInputs - ベースケースの入力データ  
 * @param netDebtVariation - ネット負債の変動幅（±%）
 * @param multipleVariation - 倍率の変動幅（±%）
 * @returns 感応度分析用の入力データセット
 */
export function generateSensitivityScenarios(
  baseInputs: Inputs,
  netDebtVariation: number = 0.1, // ±10%
  multipleVariation: number = 0.1 // ±10%
): Array<{ scenario: string; inputs: Inputs }> {
  const scenarios: Array<{ scenario: string; inputs: Inputs }> = [];

  // ベースケース
  scenarios.push({ scenario: 'Base Case', inputs: baseInputs });

  // ネット負債感応度
  const netDebtBase = baseInputs.netDebtYen;
  scenarios.push({
    scenario: `ネット負債 +${(netDebtVariation * 100).toFixed(0)}%`,
    inputs: {
      ...baseInputs,
      netDebtYen: netDebtBase * (1 + netDebtVariation)
    }
  });

  scenarios.push({
    scenario: `ネット負債 -${(netDebtVariation * 100).toFixed(0)}%`,
    inputs: {
      ...baseInputs,
      netDebtYen: netDebtBase * (1 - netDebtVariation)
    }
  });

  // 倍率感応度（各手法）
  const methods: Method[] = ['EV/Sales', 'EV/EBITDA'];
  methods.forEach(method => {
    const baseEV = baseInputs.evByMethod[method];
    if (baseEV) {
      scenarios.push({
        scenario: `${method} +${(multipleVariation * 100).toFixed(0)}%`,
        inputs: {
          ...baseInputs,
          evByMethod: {
            ...baseInputs.evByMethod,
            [method]: baseEV * (1 + multipleVariation)
          }
        }
      });

      scenarios.push({
        scenario: `${method} -${(multipleVariation * 100).toFixed(0)}%`,
        inputs: {
          ...baseInputs,
          evByMethod: {
            ...baseInputs.evByMethod,
            [method]: baseEV * (1 - multipleVariation)
          }
        }
      });
    }
  });

  // P/E感応度
  if (baseInputs.pePrice) {
    scenarios.push({
      scenario: `P/E +${(multipleVariation * 100).toFixed(0)}%`,
      inputs: {
        ...baseInputs,
        pePrice: baseInputs.pePrice * (1 + multipleVariation)
      }
    });

    scenarios.push({
      scenario: `P/E -${(multipleVariation * 100).toFixed(0)}%`,
      inputs: {
        ...baseInputs,
        pePrice: baseInputs.pePrice * (1 - multipleVariation)
      }
    });
  }

  return scenarios;
}

/**
 * ブリッジ表の表示用フォーマット
 * @param bridges - ブリッジデータ
 * @returns フォーマット済みテーブルデータ
 */
export function formatBridgeTable(bridges: Bridge[]): Array<{
  method: string;
  ev: string;
  netDebt: string;
  equity: string;
  shares: string;
  pricePerShare: string;
  used: string;
}> {
  return bridges.map(bridge => ({
    method: bridge.method,
    ev: Number.isFinite(bridge.EV) ? formatJPY(bridge.EV, { autoScale: true }) : 'N/A',
    netDebt: '-', // 入力データから取得
    equity: Number.isFinite(bridge.Equity) ? formatJPY(bridge.Equity, { autoScale: true }) : 'N/A',
    shares: '/', // 入力データから取得  
    pricePerShare: Number.isFinite(bridge.PricePerShare) ? formatJPY(bridge.PricePerShare) : 'N/A',
    used: bridge.used ? '✓' : (bridge.skipReason || '✗')
  }));
}
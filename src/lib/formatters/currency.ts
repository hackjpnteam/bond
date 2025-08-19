/**
 * 金融レポート用の通貨フォーマッター
 * 日本の金融業界の表示慣行に対応
 */

import { fromYen, type JpyUnit } from '../units/normalizeUnits.js';

/**
 * フォーマットオプション
 */
export interface FormatOptions {
  /** 小数点以下の桁数 */
  maximumFractionDigits?: number;
  /** 最小小数点以下桁数 */
  minimumFractionDigits?: number;
  /** 通貨記号を表示するか */
  showCurrencySymbol?: boolean;
  /** 自動で最適な単位に変換するか */
  autoScale?: boolean;
  /** 強制的に使用する単位 */
  forceUnit?: JpyUnit;
  /** 負の値の表示方法 */
  negativeStyle?: 'parentheses' | 'minus';
}

/**
 * 標準的な日本円フォーマット
 * @param amount - 金額（円）
 * @param options - フォーマットオプション
 * @returns フォーマット済み文字列
 * 
 * @example
 * ```typescript
 * formatJPY(3790000000) // "¥3,790,000,000"
 * formatJPY(3790000000, { autoScale: true }) // "¥37.9億円"
 * formatJPY(-1000000, { negativeStyle: 'parentheses' }) // "(¥1,000,000)"
 * ```
 */
export function formatJPY(amount: number, options: FormatOptions = {}): string {
  const {
    maximumFractionDigits = 0,
    minimumFractionDigits = 0,
    showCurrencySymbol = true,
    autoScale = false,
    forceUnit,
    negativeStyle = 'minus'
  } = options;

  // 無効な値のハンドリング
  if (!Number.isFinite(amount)) {
    return amount === Infinity ? '∞' : amount === -Infinity ? '-∞' : 'N/A';
  }

  let displayAmount = amount;
  let unit = '';
  let prefix = showCurrencySymbol ? '¥' : '';

  // 単位の決定
  if (forceUnit) {
    // 強制単位が指定されている場合
    const factors: Record<JpyUnit, number> = {
      '円': 1,
      '千円': 1e3,
      '百万円': 1e6,
      '億円': 1e8,
      '兆円': 1e12,
    };
    displayAmount = amount / factors[forceUnit];
    unit = forceUnit !== '円' ? forceUnit : '';
  } else if (autoScale) {
    // 自動スケーリング
    const scaled = fromYen(amount);
    displayAmount = scaled.value;
    unit = scaled.unit !== '円' ? scaled.unit : '';
  }

  // 負の値の処理
  const isNegative = displayAmount < 0;
  const absAmount = Math.abs(displayAmount);

  // 数値フォーマット
  const formatter = new Intl.NumberFormat('ja-JP', {
    maximumFractionDigits,
    minimumFractionDigits,
    useGrouping: true,
  });

  let formattedNumber = formatter.format(absAmount);

  // 負の値のスタイル適用
  if (isNegative) {
    if (negativeStyle === 'parentheses') {
      return `(${prefix}${formattedNumber}${unit})`;
    } else {
      prefix = '-' + prefix;
    }
  }

  return `${prefix}${formattedNumber}${unit}`;
}

/**
 * 株価専用フォーマッター
 * @param pricePerShare - 1株あたり価格（円）
 * @param options - フォーマットオプション
 * @returns フォーマット済み文字列
 */
export function formatSharePrice(
  pricePerShare: number, 
  options: Omit<FormatOptions, 'autoScale'> = {}
): string {
  const defaultOptions: FormatOptions = {
    maximumFractionDigits: 0,
    showCurrencySymbol: true,
    negativeStyle: 'minus',
    ...options
  };

  return formatJPY(pricePerShare, defaultOptions);
}

/**
 * パーセンテージフォーマッター
 * @param ratio - 比率（0.15 = 15%）
 * @param decimalPlaces - 小数点以下桁数
 * @returns フォーマット済み文字列
 */
export function formatPercentage(ratio: number, decimalPlaces: number = 1): string {
  if (!Number.isFinite(ratio)) {
    return 'N/A';
  }

  const percentage = ratio * 100;
  return `${percentage.toFixed(decimalPlaces)}%`;
}

/**
 * 倍率フォーマッター（EV/EBITDA等）
 * @param multiple - 倍率
 * @param decimalPlaces - 小数点以下桁数
 * @returns フォーマット済み文字列
 */
export function formatMultiple(multiple: number, decimalPlaces: number = 1): string {
  if (!Number.isFinite(multiple) || multiple < 0) {
    return 'N/A';
  }

  return `${multiple.toFixed(decimalPlaces)}x`;
}

/**
 * レンジフォーマッター（価格レンジ等）
 * @param min - 最小値
 * @param max - 最大値
 * @param options - フォーマットオプション
 * @returns フォーマット済み文字列
 */
export function formatRange(
  min: number, 
  max: number, 
  options: FormatOptions = {}
): string {
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return 'N/A';
  }

  const formattedMin = formatJPY(min, options);
  const formattedMax = formatJPY(max, options);
  return `${formattedMin} - ${formattedMax}`;
}

/**
 * 大規模数値の短縮表示（B=億、T=兆）
 * @param amount - 金額（円）
 * @param useEnglish - 英語表記を使用するか（B, T）
 * @returns 短縮表示文字列
 */
export function formatCompact(amount: number, useEnglish: boolean = false): string {
  if (!Number.isFinite(amount)) {
    return 'N/A';
  }

  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';

  if (useEnglish) {
    if (absAmount >= 1e12) {
      return `${sign}¥${(amount / 1e12).toFixed(1)}T`;
    } else if (absAmount >= 1e8) {
      return `${sign}¥${(amount / 1e8).toFixed(1)}B`;
    } else if (absAmount >= 1e6) {
      return `${sign}¥${(amount / 1e6).toFixed(1)}M`;
    }
  } else {
    if (absAmount >= 1e12) {
      return `${sign}¥${(amount / 1e12).toFixed(1)}兆円`;
    } else if (absAmount >= 1e8) {
      return `${sign}¥${(amount / 1e8).toFixed(1)}億円`;
    } else if (absAmount >= 1e6) {
      return `${sign}¥${(amount / 1e6).toFixed(1)}百万円`;
    }
  }

  return formatJPY(amount);
}

/**
 * 金融表向けのテーブルフォーマッター
 * @param values - フォーマット対象の値の配列
 * @param options - フォーマットオプション
 * @returns 揃えられた文字列の配列
 */
export function formatTableColumn(
  values: number[], 
  options: FormatOptions = {}
): string[] {
  // 最適な単位を決定（最大値基準）
  const maxAbsValue = Math.max(...values.map(Math.abs));
  const optimalUnit = fromYen(maxAbsValue).unit;

  const formatOptions: FormatOptions = {
    ...options,
    forceUnit: optimalUnit,
    autoScale: false,
  };

  return values.map(value => formatJPY(value, formatOptions));
}

/**
 * 市場データ表示用フォーマッター
 * @param value - 値
 * @param type - データの種類
 * @returns フォーマット済み文字列
 */
export function formatMarketData(
  value: number, 
  type: 'price' | 'volume' | 'ratio' | 'multiple'
): string {
  switch (type) {
    case 'price':
      return formatSharePrice(value);
    case 'volume':
      return formatCompact(value);
    case 'ratio':
      return formatPercentage(value);
    case 'multiple':
      return formatMultiple(value);
    default:
      return formatJPY(value);
  }
}
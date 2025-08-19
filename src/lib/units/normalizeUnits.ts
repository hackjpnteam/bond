/**
 * 日本の金融業界で使用される通貨単位の正規化ユーティリティ
 * JGAAP/TDnet等で一般的な単位を「円」に統一
 */

export type JpyUnit = '円' | '千円' | '百万円' | '億円' | '兆円';
export type ShareUnit = '株' | '千株' | '百万株';

/**
 * 通貨単位の換算係数
 */
const JPY_FACTORS: Record<JpyUnit, number> = {
  '円': 1,
  '千円': 1e3,
  '百万円': 1e6,
  '億円': 1e8,
  '兆円': 1e12,
} as const;

/**
 * 株式単位の換算係数
 */
const SHARE_FACTORS: Record<ShareUnit, number> = {
  '株': 1,
  '千株': 1e3,
  '百万株': 1e6,
} as const;

/**
 * 指定された日本円単位を円に変換
 * @param value - 変換する値
 * @param unit - 元の単位
 * @returns 円に変換された値
 * @throws Error 無効な単位が指定された場合
 * 
 * @example
 * ```typescript
 * const result = toYen(3790, '百万円'); // 3,790,000,000
 * ```
 */
export function toYen(value: number, unit: JpyUnit): number {
  if (!Object.prototype.hasOwnProperty.call(JPY_FACTORS, unit)) {
    throw new Error(`Unsupported JPY unit: ${unit}`);
  }
  
  const factor = JPY_FACTORS[unit];
  const result = value * factor;
  
  // オーバーフローチェック
  if (!Number.isFinite(result) || Math.abs(result) > Number.MAX_SAFE_INTEGER) {
    throw new Error(`Conversion overflow: ${value} ${unit} resulted in ${result}`);
  }
  
  return result;
}

/**
 * 指定された株式単位を株に変換
 * @param value - 変換する値
 * @param unit - 元の単位
 * @returns 株に変換された値
 * @throws Error 無効な単位が指定された場合
 * 
 * @example
 * ```typescript
 * const result = toShares(1000, '千株'); // 1,000,000
 * ```
 */
export function toShares(value: number, unit: ShareUnit): number {
  if (!Object.prototype.hasOwnProperty.call(SHARE_FACTORS, unit)) {
    throw new Error(`Unsupported share unit: ${unit}`);
  }
  
  const factor = SHARE_FACTORS[unit];
  const result = value * factor;
  
  // 株式数は整数であるべき
  if (result !== Math.floor(result)) {
    console.warn(`Non-integer share count detected: ${result}. Rounding to nearest integer.`);
    return Math.round(result);
  }
  
  return result;
}

/**
 * 円からより読みやすい単位に変換（表示用）
 * @param yen - 円での値
 * @returns より読みやすい単位での表現
 * 
 * @example
 * ```typescript
 * const result = fromYen(3790000000); // { value: 3790, unit: '百万円' }
 * ```
 */
export function fromYen(yen: number): { value: number; unit: JpyUnit } {
  const absYen = Math.abs(yen);
  
  if (absYen >= 1e12) {
    return { value: yen / 1e12, unit: '兆円' };
  } else if (absYen >= 1e8) {
    return { value: yen / 1e8, unit: '億円' };
  } else if (absYen >= 1e6) {
    return { value: yen / 1e6, unit: '百万円' };
  } else if (absYen >= 1e3) {
    return { value: yen / 1e3, unit: '千円' };
  } else {
    return { value: yen, unit: '円' };
  }
}

/**
 * 数値が有効な金額かどうかをチェック
 * @param value - チェックする値
 * @returns 有効な場合true
 */
export function isValidAmount(value: number): boolean {
  return Number.isFinite(value) && !Number.isNaN(value);
}

/**
 * 複数の通貨入力を一括で円に正規化
 * @param inputs - 入力データの配列
 * @returns 正規化された値の配列
 */
export function normalizeAmounts(
  inputs: Array<{ value: number; unit: JpyUnit }>
): number[] {
  return inputs.map(({ value, unit }) => toYen(value, unit));
}

/**
 * 単位変換の安全性チェック付きラッパー
 * @param value - 変換する値
 * @param unit - 元の単位
 * @returns 成功時は値、失敗時はエラー情報
 */
export function safeToYen(
  value: number, 
  unit: JpyUnit
): { success: true; value: number } | { success: false; error: string } {
  try {
    if (!isValidAmount(value)) {
      return { success: false, error: `Invalid amount: ${value}` };
    }
    
    const result = toYen(value, unit);
    return { success: true, value: result };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}
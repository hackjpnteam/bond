/**
 * 単位正規化ユーティリティのテストスイート
 */

import { describe, it, expect, test } from 'vitest';
import { 
  toYen, 
  toShares,
  fromYen,
  isValidAmount,
  normalizeAmounts,
  safeToYen,
  type JpyUnit,
  type ShareUnit 
} from '../../src/lib/units/normalizeUnits.js';

describe('toYen', () => {
  it('円単位の変換（変換なし）', () => {
    expect(toYen(1000, '円')).toBe(1000);
  });

  it('千円→円の変換', () => {
    expect(toYen(100, '千円')).toBe(100_000);
  });

  it('百万円→円の変換', () => {
    expect(toYen(3790, '百万円')).toBe(3_790_000_000);
  });

  it('億円→円の変換', () => {
    expect(toYen(10, '億円')).toBe(1_000_000_000);
  });

  it('兆円→円の変換', () => {
    expect(toYen(1, '兆円')).toBe(1_000_000_000_000);
  });

  it('小数値の変換', () => {
    expect(toYen(1.5, '百万円')).toBe(1_500_000);
  });

  it('負の値の変換', () => {
    expect(toYen(-500, '百万円')).toBe(-500_000_000);
  });

  it('ゼロの変換', () => {
    expect(toYen(0, '億円')).toBe(0);
  });

  it('無効な単位でエラーをスロー', () => {
    expect(() => toYen(100, '万円' as JpyUnit)).toThrow('Unsupported JPY unit: 万円');
  });

  it('Infinity値でエラーをスロー', () => {
    expect(() => toYen(Infinity, '円')).toThrow('Conversion overflow');
  });
});

describe('toShares', () => {
  it('株単位の変換（変換なし）', () => {
    expect(toShares(1000, '株')).toBe(1000);
  });

  it('千株→株の変換', () => {
    expect(toShares(100, '千株')).toBe(100_000);
  });

  it('百万株→株の変換', () => {
    expect(toShares(1, '百万株')).toBe(1_000_000);
  });

  it('小数値の四捨五入', () => {
    expect(toShares(1.7, '千株')).toBe(1_700); // 整数なので四捨五入
  });

  it('無効な単位でエラーをスロー', () => {
    expect(() => toShares(100, '万株' as ShareUnit)).toThrow('Unsupported share unit: 万株');
  });
});

describe('fromYen', () => {
  it('円の適切な単位への変換', () => {
    expect(fromYen(1000)).toEqual({ value: 1, unit: '千円' });
    expect(fromYen(50_000)).toEqual({ value: 50, unit: '千円' });
    expect(fromYen(3_790_000_000)).toEqual({ value: 37.9, unit: '億円' });
    expect(fromYen(100_000_000_000)).toEqual({ value: 1000, unit: '億円' });
    expect(fromYen(5_000_000_000_000)).toEqual({ value: 5, unit: '兆円' });
  });

  it('負の値の変換', () => {
    expect(fromYen(-3_790_000_000)).toEqual({ value: -37.9, unit: '億円' });
  });

  it('ゼロの変換', () => {
    expect(fromYen(0)).toEqual({ value: 0, unit: '円' });
  });

  it('境界値でのテスト', () => {
    expect(fromYen(999_999)).toEqual({ value: 999.999, unit: '千円' });
    expect(fromYen(1_000_000)).toEqual({ value: 1, unit: '百万円' });
  });
});

describe('isValidAmount', () => {
  it('有効な金額を正しく判定', () => {
    expect(isValidAmount(100)).toBe(true);
    expect(isValidAmount(0)).toBe(true);
    expect(isValidAmount(-500)).toBe(true);
    expect(isValidAmount(3.14)).toBe(true);
  });

  it('無効な金額を正しく判定', () => {
    expect(isValidAmount(NaN)).toBe(false);
    expect(isValidAmount(Infinity)).toBe(false);
    expect(isValidAmount(-Infinity)).toBe(false);
  });
});

describe('normalizeAmounts', () => {
  it('複数の金額を一括変換', () => {
    const inputs = [
      { value: 1000, unit: '百万円' as JpyUnit },
      { value: 50, unit: '億円' as JpyUnit },
      { value: 500, unit: '千円' as JpyUnit }
    ];
    
    const expected = [
      1_000_000_000,    // 1000百万円
      5_000_000_000,    // 50億円
      500_000           // 500千円
    ];
    
    expect(normalizeAmounts(inputs)).toEqual(expected);
  });

  it('空配列を正しく処理', () => {
    expect(normalizeAmounts([])).toEqual([]);
  });
});

describe('safeToYen', () => {
  it('成功ケース', () => {
    const result = safeToYen(3790, '百万円');
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.value).toBe(3_790_000_000);
    }
  });

  it('無効な金額でのエラーケース', () => {
    const result = safeToYen(NaN, '円');
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toContain('Invalid amount');
    }
  });

  it('無効な単位でのエラーケース', () => {
    const result = safeToYen(100, '万円' as JpyUnit);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toContain('Unsupported JPY unit');
    }
  });
});

// スナップショットテスト
describe('単位変換スナップショット', () => {
  const testCases = [
    { value: 3790, unit: '百万円' as JpyUnit },
    { value: 150, unit: '億円' as JpyUnit },
    { value: 2.5, unit: '兆円' as JpyUnit },
    { value: 50000, unit: '千円' as JpyUnit },
  ];

  testCases.forEach(({ value, unit }) => {
    it(`${value}${unit}の変換結果`, () => {
      const result = toYen(value, unit);
      expect(result).toMatchSnapshot();
    });
  });
});

// エッジケーステスト
describe('エッジケース', () => {
  it('最大値近くでのオーバーフローチェック', () => {
    expect(() => toYen(Number.MAX_SAFE_INTEGER, '兆円')).toThrow();
  });

  it('極小値での動作確認', () => {
    expect(toYen(0.001, '百万円')).toBe(1000);
  });

  it('JavaScript精度限界での動作', () => {
    const result = toYen(0.1 + 0.2, '円'); // JavaScript精度問題のテスト
    expect(Number.isFinite(result)).toBe(true);
  });
});
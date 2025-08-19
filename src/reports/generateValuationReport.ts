/**
 * 企業価値評価レポート生成機能
 * 実務レベルの包括的なMarkdownレポートを生成
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import type { 
  ValuationResult, 
  Inputs, 
  Bridge, 
  Summary,
  generateSensitivityScenarios,
  computeValuation 
} from '../lib/valuation/compute.js';
import { formatJPY, formatRange, formatMultiple, formatPercentage } from '../lib/formatters/currency.js';
import { fromYen } from '../lib/units/normalizeUnits.js';

/**
 * レポート生成オプション
 */
export interface ReportOptions {
  /** 出力ディレクトリ */
  outputDir?: string;
  /** ファイル名（拡張子なし） */
  fileName?: string;
  /** 感応度分析を含めるか */
  includeSensitivity?: boolean;
  /** 詳細なブリッジ表を含めるか */
  includeDetailedBridge?: boolean;
  /** 警告とエラーを含めるか */
  includeDiagnostics?: boolean;
  /** エグゼクティブサマリーを含めるか */
  includeExecutiveSummary?: boolean;
}

/**
 * レポート生成に必要な依存関数の型定義
 */
export interface ReportDependencies {
  generateSensitivityScenarios: typeof generateSensitivityScenarios;
  computeValuation: typeof computeValuation;
}

/**
 * 日付を YYYY-MM-DD 形式でフォーマット
 * @param date - フォーマット対象の日付
 * @returns フォーマット済み文字列
 */
function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

/**
 * 日時を YYYY-MM-DD HH:MM 形式でフォーマット
 * @param date - フォーマット対象の日時
 * @returns フォーマット済み文字列
 */
function formatDateTime(date: Date): string {
  return date.toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * エグゼクティブサマリーセクション生成
 * @param result - 算定結果
 * @returns Markdownセクション
 */
function generateExecutiveSummary(result: ValuationResult): string {
  const { summary, inputs } = result;
  
  if (!result.success || summary.validMethodCount === 0) {
    return `## エグゼクティブサマリー

**評価不能**: 有効な評価手法がありませんでした。

`;
  }

  const targetPrice = summary.weighted || summary.avg;
  const range = formatRange(summary.range[0], summary.range[1]);
  const confidence = summary.validMethodCount >= 2 ? '高' : '中';

  return `## エグゼクティブサマリー

**目標株価**: ${formatJPY(targetPrice)}  
**価格レンジ**: ${range}  
**信頼性**: ${confidence} (${summary.validMethodCount}手法)

${inputs.companyName || '対象企業'}の企業価値評価を${summary.usedMethods.join('、')}手法により実施しました。
加重平均による目標株価は**${formatJPY(targetPrice)}**、評価レンジは**${range}**となります。

`;
}

/**
 * 前提条件セクション生成
 * @param inputs - 入力データ
 * @returns Markdownセクション
 */
function generateAssumptions(inputs: Inputs): string {
  const valuationDate = inputs.valuationDate || new Date();
  const netDebtDisplay = fromYen(inputs.netDebtYen);
  const sharesDisplay = fromYen(inputs.sharesOutstanding);
  
  return `## 前提条件

| 項目 | 値 | 備考 |
|------|-----|------|
| **評価基準日** | ${formatDate(valuationDate)} | |
| **発行済株式数** | ${sharesDisplay.value.toLocaleString()}${sharesDisplay.unit === '円' ? '株' : sharesDisplay.unit.replace('円', '株')} | |
| **ネット有利子負債** | ${formatJPY(inputs.netDebtYen, { autoScale: true })} | ${inputs.netDebtYen >= 0 ? '負債超過' : 'ネットキャッシュ'} |
| **希薄化考慮** | なし | 潜在株式は考慮せず |

### 使用倍率

`;
}

/**
 * ブリッジ表セクション生成
 * @param bridges - ブリッジデータ
 * @param inputs - 入力データ
 * @returns Markdownセクション
 */
function generateBridgeTable(bridges: Bridge[], inputs: Inputs): string {
  const netDebt = formatJPY(inputs.netDebtYen, { autoScale: true });
  const shares = inputs.sharesOutstanding.toLocaleString();

  let table = `## 手法別ブリッジ表

| 手法 | 企業価値(EV) | ネット負債 | 株主価値 | 発行済株式数 | 1株価値 | 採用 |
|------|-------------|-----------|---------|-------------|---------|------|
`;

  bridges.forEach(bridge => {
    const ev = Number.isFinite(bridge.EV) 
      ? formatJPY(bridge.EV, { autoScale: true })
      : bridge.method === 'P/E' ? '-' : 'N/A';
      
    const equity = Number.isFinite(bridge.Equity)
      ? formatJPY(bridge.Equity, { autoScale: true })
      : 'N/A';
      
    const pricePerShare = Number.isFinite(bridge.PricePerShare)
      ? formatJPY(bridge.PricePerShare)
      : 'N/A';
      
    const used = bridge.used ? '✓' : '✗';
    
    table += `| **${bridge.method}** | ${ev} | (${netDebt}) | ${equity} | ${shares}株 | ${pricePerShare} | ${used} |\n`;
  });

  return table + '\n';
}

/**
 * 評価サマリーセクション生成
 * @param summary - サマリーデータ
 * @returns Markdownセクション
 */
function generateSummaryStatistics(summary: Summary): string {
  if (summary.validMethodCount === 0) {
    return `## 評価サマリー

有効な評価手法がありませんでした。

`;
  }

  return `## 評価サマリー

| 統計値 | 金額 |
|--------|------|
| **平均株価** | ${formatJPY(summary.avg)} |
| **中央値株価** | ${formatJPY(summary.median)} |
| **加重平均株価** | ${formatJPY(summary.weighted)} |
| **最高価格** | ${formatJPY(summary.range[1])} |
| **最低価格** | ${formatJPY(summary.range[0])} |
| **価格レンジ** | ${formatRange(summary.range[0], summary.range[1])} |

**有効手法数**: ${summary.validMethodCount}/3  
**採用手法**: ${summary.usedMethods.join('、')}

`;
}

/**
 * 感応度分析セクション生成
 * @param baseResult - ベースケース結果
 * @param dependencies - 依存関数
 * @returns Markdownセクション
 */
function generateSensitivityAnalysis(
  baseResult: ValuationResult, 
  dependencies: ReportDependencies
): string {
  const scenarios = dependencies.generateSensitivityScenarios(baseResult.inputs);
  
  let table = `## 感応度分析

| シナリオ | 加重平均株価 | 変動率 | レンジ |
|----------|-------------|--------|-------|
`;

  const basePrice = baseResult.summary.weighted || baseResult.summary.avg;

  scenarios.forEach(scenario => {
    const result = dependencies.computeValuation(scenario.inputs);
    const targetPrice = result.summary.weighted || result.summary.avg;
    const changeRate = Number.isFinite(targetPrice) && Number.isFinite(basePrice) && basePrice !== 0
      ? (targetPrice - basePrice) / basePrice
      : 0;
    const range = formatRange(result.summary.range[0], result.summary.range[1]);
    
    const priceDisplay = Number.isFinite(targetPrice) ? formatJPY(targetPrice) : 'N/A';
    const changeDisplay = formatPercentage(changeRate);
    
    table += `| ${scenario.scenario} | ${priceDisplay} | ${changeDisplay} | ${range} |\n`;
  });

  return table + `
### 感応度分析の解釈

- **ベースケース**: ${formatJPY(basePrice)}
- **主要リスクファクター**: ネット有利子負債の変動、倍率の見直し
- **上昇要因**: 負債削減、業界倍率の改善
- **下落要因**: 負債増加、収益性悪化による倍率低下

`;
}

/**
 * 診断セクション生成
 * @param result - 算定結果
 * @returns Markdownセクション
 */
function generateDiagnostics(result: ValuationResult): string {
  let section = '';

  if (result.warnings.length > 0) {
    section += `## ⚠️ 警告事項\n\n`;
    result.warnings.forEach(warning => {
      section += `- ${warning}\n`;
    });
    section += '\n';
  }

  if (result.errors.length > 0) {
    section += `## ❌ エラー\n\n`;
    result.errors.forEach(error => {
      section += `- ${error}\n`;
    });
    section += '\n';
  }

  if (section === '') {
    section = `## ✅ 診断結果\n\n問題は検出されませんでした。\n\n`;
  }

  return section;
}

/**
 * 企業価値評価レポート生成
 * @param result - 算定結果
 * @param options - レポートオプション
 * @param dependencies - 依存関数
 * @returns 生成されたファイルパス
 */
export function generateValuationReport(
  result: ValuationResult,
  options: ReportOptions = {},
  dependencies: ReportDependencies
): string {
  const {
    outputDir = './reports',
    fileName = `valuation-${formatDate(new Date())}`,
    includeSensitivity = true,
    includeDetailedBridge = true,
    includeDiagnostics = true,
    includeExecutiveSummary = true
  } = options;

  // ディレクトリ作成
  mkdirSync(outputDir, { recursive: true });

  const companyName = result.inputs.companyName || '対象企業';
  const reportDate = formatDateTime(new Date());

  let markdown = `# 企業価値評価レポート

**対象企業**: ${companyName}  
**レポート作成日**: ${reportDate}  
**評価基準日**: ${formatDate(result.inputs.valuationDate || new Date())}

---

`;

  // エグゼクティブサマリー
  if (includeExecutiveSummary) {
    markdown += generateExecutiveSummary(result);
  }

  // 前提条件
  markdown += generateAssumptions(result.inputs);

  // 使用倍率の詳細
  const methods = Object.keys(result.inputs.evByMethod) as Array<keyof typeof result.inputs.evByMethod>;
  methods.forEach(method => {
    const ev = result.inputs.evByMethod[method];
    if (ev) {
      markdown += `- **${method}**: 推計企業価値 ${formatJPY(ev, { autoScale: true })}\n`;
    }
  });

  if (result.inputs.pePrice) {
    markdown += `- **P/E**: 推計株価 ${formatJPY(result.inputs.pePrice)}\n`;
  }

  markdown += '\n';

  // ブリッジ表
  if (includeDetailedBridge) {
    markdown += generateBridgeTable(result.bridges, result.inputs);
  }

  // 評価サマリー
  markdown += generateSummaryStatistics(result.summary);

  // 感応度分析
  if (includeSensitivity && result.success) {
    markdown += generateSensitivityAnalysis(result, dependencies);
  }

  // 診断情報
  if (includeDiagnostics) {
    markdown += generateDiagnostics(result);
  }

  // フッター
  markdown += `---

**免責事項**: このレポートは情報提供のみを目的としており、投資判断の根拠として使用すべきではありません。
実際の投資においては、より詳細な分析と専門家の助言をお求めください。

*Generated by Bond Valuation System*
`;

  // ファイル保存
  const filePath = join(outputDir, `${fileName}.md`);
  writeFileSync(filePath, markdown, 'utf-8');

  return filePath;
}

/**
 * 簡易レポート生成（コンソール出力用）
 * @param result - 算定結果
 * @returns フォーマット済み文字列
 */
export function generateSimpleReport(result: ValuationResult): string {
  const companyName = result.inputs.companyName || '対象企業';
  
  if (!result.success) {
    return `❌ ${companyName}の評価に失敗しました:\n${result.errors.join('\n')}`;
  }

  const { summary } = result;
  
  return `📊 ${companyName} 企業価値評価結果

🎯 目標株価: ${formatJPY(summary.weighted || summary.avg)}
📈 価格レンジ: ${formatRange(summary.range[0], summary.range[1])}
✅ 採用手法: ${summary.usedMethods.join('、')} (${summary.validMethodCount}手法)

統計サマリー:
- 平均: ${formatJPY(summary.avg)}
- 中央値: ${formatJPY(summary.median)}
- 加重平均: ${formatJPY(summary.weighted)}
`;
}

/**
 * JSONフォーマットでの結果出力
 * @param result - 算定結果
 * @param filePath - 出力ファイルパス
 */
export function exportResultAsJSON(result: ValuationResult, filePath: string): void {
  const exportData = {
    ...result,
    exportedAt: new Date().toISOString(),
    version: '1.0.0'
  };

  writeFileSync(filePath, JSON.stringify(exportData, null, 2), 'utf-8');
}
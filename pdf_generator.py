"""
PDF レポート生成機能
企業価値評価結果を美しいPDFレポートとして出力
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import pandas as pd
from typing import Dict, Any, List
import io
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_agg import FigureCanvasAgg
import base64

# フォント設定（日本語対応）
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

class PDFReportGenerator:
    def __init__(self):
        # 基本スタイル設定
        self.styles = getSampleStyleSheet()
        
        # カスタムスタイル追加
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.darkblue,
            borderPadding=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkgreen
        ))
    
    def generate_comprehensive_report(self, 
                                    financial_data: Dict[str, Any], 
                                    valuation_result: Dict[str, Any],
                                    conversation_context: List[Dict[str, str]] = None) -> bytes:
        """
        包括的な企業価値評価PDFレポートを生成
        
        Args:
            financial_data: 財務分析データ
            valuation_result: 企業価値評価結果
            conversation_context: チャット履歴
            
        Returns:
            PDFバイナリデータ
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # レポート要素リスト
        story = []
        
        # 1. タイトルページ
        story.extend(self._create_title_page(financial_data, valuation_result))
        
        # 2. エグゼクティブサマリー
        story.extend(self._create_executive_summary(valuation_result))
        
        # 3. 会社概要・財務分析
        story.extend(self._create_financial_analysis_section(financial_data))
        
        # 4. 企業価値評価結果
        story.extend(self._create_valuation_results_section(valuation_result))
        
        # 5. 投資推奨・リスク分析
        story.extend(self._create_investment_recommendation_section(valuation_result))
        
        # 6. 詳細分析（会話履歴）
        if conversation_context:
            story.extend(self._create_detailed_analysis_section(conversation_context))
        
        # 7. 免責事項
        story.extend(self._create_disclaimer_section())
        
        # PDF生成
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    def _create_title_page(self, financial_data: Dict[str, Any], valuation_result: Dict[str, Any]) -> List:
        """タイトルページ作成"""
        elements = []
        
        # メインタイトル
        elements.append(Paragraph("企業価値評価レポート", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.5*inch))
        
        # 企業名
        company_name = financial_data.get('company_name', '対象企業')
        elements.append(Paragraph(f"{company_name}", self.styles['CompanyName']))
        elements.append(Spacer(1, 0.5*inch))
        
        # 基本情報テーブル
        basic_info = [
            ['項目', '内容'],
            ['評価基準日', datetime.now().strftime('%Y年%m月%d日')],
            ['評価手法', 'EV/売上、EV/EBITDA、P/E倍率法'],
            ['決算期間', financial_data.get('fiscal_period', '最新期')],
            ['信頼性レベル', valuation_result.get('summary', {}).get('confidence_level', '中')]
        ]
        
        table = Table(basic_info, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 1*inch))
        
        # 目標株価ハイライト
        if valuation_result.get('summary', {}).get('target_price'):
            target_price = valuation_result['summary']['target_price']
            price_text = f"目標株価: ¥{target_price:,.0f}"
            elements.append(Paragraph(price_text, self.styles['CustomTitle']))
        
        elements.append(PageBreak())
        return elements
    
    def _create_executive_summary(self, valuation_result: Dict[str, Any]) -> List:
        """エグゼクティブサマリー作成"""
        elements = []
        
        elements.append(Paragraph("エグゼクティブサマリー", self.styles['CustomHeading']))
        
        summary = valuation_result.get('summary', {})
        
        # 主要指標テーブル
        summary_data = [
            ['指標', '値'],
            ['目標株価', f"¥{summary.get('target_price', 0):,.0f}"],
            ['価格レンジ', f"¥{summary.get('price_range', {}).get('min', 0):,.0f} - ¥{summary.get('price_range', {}).get('max', 0):,.0f}"],
            ['加重平均価格', f"¥{summary.get('weighted_average', 0):,.0f}"],
            ['信頼性レベル', summary.get('confidence_level', '中')]
        ]
        
        table = Table(summary_data, colWidths=[2*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # 主要前提条件
        if summary.get('key_assumptions'):
            elements.append(Paragraph("主要前提条件:", self.styles['Heading2']))
            for assumption in summary['key_assumptions']:
                elements.append(Paragraph(f"• {assumption}", self.styles['CustomBody']))
        
        elements.append(Spacer(1, 0.3*inch))
        return elements
    
    def _create_financial_analysis_section(self, financial_data: Dict[str, Any]) -> List:
        """財務分析セクション作成"""
        elements = []
        
        elements.append(Paragraph("財務分析", self.styles['CustomHeading']))
        
        # 正規化後財務データテーブル
        if 'normalized_financials' in financial_data:
            normalized = financial_data['normalized_financials']
            
            financial_table_data = [
                ['項目', '金額（円）', '備考'],
                ['売上高', f"¥{normalized.get('revenue_yen', 0):,.0f}", '年間売上'],
                ['EBITDA', f"¥{normalized.get('ebitda_yen', 0):,.0f}", '利払前税前償却前利益'],
                ['純利益', f"¥{normalized.get('net_income_yen', 0):,.0f}", '当期純利益'],
                ['ネット有利子負債', f"¥{normalized.get('net_debt_yen', 0):,.0f}", '負債-現金'],
                ['発行済株式数', f"{normalized.get('shares_outstanding', 0):,.0f}株", '普通株式']
            ]
            
            table = Table(financial_table_data, colWidths=[2*inch, 2*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ]))
            
            elements.append(table)
        
        # 企業分析
        if 'company_analysis' in financial_data:
            analysis = financial_data['company_analysis']
            
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph("企業分析", self.styles['Heading2']))
            
            if analysis.get('strengths'):
                elements.append(Paragraph("強み:", self.styles['Heading3']))
                for strength in analysis['strengths']:
                    elements.append(Paragraph(f"• {strength}", self.styles['CustomBody']))
            
            if analysis.get('weaknesses'):
                elements.append(Paragraph("弱み:", self.styles['Heading3']))
                for weakness in analysis['weaknesses']:
                    elements.append(Paragraph(f"• {weakness}", self.styles['CustomBody']))
        
        elements.append(Spacer(1, 0.3*inch))
        return elements
    
    def _create_valuation_results_section(self, valuation_result: Dict[str, Any]) -> List:
        """企業価値評価結果セクション作成"""
        elements = []
        
        elements.append(Paragraph("企業価値評価結果", self.styles['CustomHeading']))
        
        # 手法別評価テーブル
        if 'valuation_methods' in valuation_result:
            methods = valuation_result['valuation_methods']
            
            methods_data = [
                ['手法', '企業価値', '株主価値', '1株価値', '使用倍率', '妥当性']
            ]
            
            for method_name, method_data in methods.items():
                if method_data and method_data.get('price_per_share'):
                    methods_data.append([
                        method_name.replace('_', '/').upper(),
                        f"¥{method_data.get('enterprise_value', 0):,.0f}" if 'enterprise_value' in method_data else '-',
                        f"¥{method_data.get('equity_value', 0):,.0f}",
                        f"¥{method_data.get('price_per_share', 0):,.0f}",
                        f"{method_data.get('multiple_used', 0):.1f}x",
                        method_data.get('validity', '中')
                    ])
            
            table = Table(methods_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1*inch, 0.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            
            elements.append(table)
        
        elements.append(Spacer(1, 0.3*inch))
        return elements
    
    def _create_investment_recommendation_section(self, valuation_result: Dict[str, Any]) -> List:
        """投資推奨セクション作成"""
        elements = []
        
        elements.append(Paragraph("投資推奨", self.styles['CustomHeading']))
        
        if 'investment_recommendation' in valuation_result:
            rec = valuation_result['investment_recommendation']
            
            # 推奨
            elements.append(Paragraph(f"推奨: {rec.get('recommendation', '保有')}", self.styles['Heading2']))
            elements.append(Paragraph(f"理由: {rec.get('rationale', '')}", self.styles['CustomBody']))
            
            # シナリオ分析
            if 'price_targets' in rec:
                targets = rec['price_targets']
                
                elements.append(Spacer(1, 0.2*inch))
                elements.append(Paragraph("シナリオ分析", self.styles['Heading2']))
                
                scenario_data = [
                    ['シナリオ', '目標株価'],
                    ['強気ケース', f"¥{targets.get('bull_case', 0):,.0f}"],
                    ['ベースケース', f"¥{targets.get('base_case', 0):,.0f}"],
                    ['弱気ケース', f"¥{targets.get('bear_case', 0):,.0f}"]
                ]
                
                table = Table(scenario_data, colWidths=[2*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                ]))
                
                elements.append(table)
        
        elements.append(Spacer(1, 0.3*inch))
        return elements
    
    def _create_detailed_analysis_section(self, conversation_context: List[Dict[str, str]]) -> List:
        """詳細分析セクション（会話履歴）作成"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("詳細分析・質疑応答", self.styles['CustomHeading']))
        
        for i, message in enumerate(conversation_context[-10:]):  # 最新10件
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'user':
                elements.append(Paragraph(f"Q{i+1}: {content[:200]}{'...' if len(content) > 200 else ''}", 
                                        self.styles['Heading3']))
            else:
                elements.append(Paragraph(f"A{i+1}: {content[:500]}{'...' if len(content) > 500 else ''}", 
                                        self.styles['CustomBody']))
                elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_disclaimer_section(self) -> List:
        """免責事項セクション作成"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("免責事項", self.styles['CustomHeading']))
        
        disclaimer_text = """
        本レポートは情報提供のみを目的として作成されており、投資判断の根拠として使用すべきではありません。
        実際の投資においては、より詳細な分析と専門家の助言をお求めください。
        
        本レポートに記載された情報の正確性について、作成者は一切の保証をいたしません。
        投資に関する最終的な判断は、投資家ご自身の責任において行ってください。
        
        Generated by Claude AI Enterprise Valuation System
        作成日時: {}
        """.format(datetime.now().strftime('%Y年%m月%d日 %H:%M'))
        
        elements.append(Paragraph(disclaimer_text, self.styles['CustomBody']))
        
        return elements
    
    def generate_simple_summary_pdf(self, valuation_result: Dict[str, Any], company_name: str = "対象企業") -> bytes:
        """
        簡易サマリーPDF生成
        
        Args:
            valuation_result: 企業価値評価結果
            company_name: 企業名
            
        Returns:
            PDFバイナリデータ
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        story = []
        
        # タイトル
        story.append(Paragraph(f"{company_name} 企業価値評価サマリー", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # 主要指標
        summary = valuation_result.get('summary', {})
        summary_data = [
            ['目標株価', f"¥{summary.get('target_price', 0):,.0f}"],
            ['価格レンジ', f"¥{summary.get('price_range', {}).get('min', 0):,.0f} - ¥{summary.get('price_range', {}).get('max', 0):,.0f}"],
            ['評価日', datetime.now().strftime('%Y年%m月%d日')]
        ]
        
        for item, value in summary_data:
            story.append(Paragraph(f"{item}: {value}", self.styles['CustomBody']))
        
        # 免責事項
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("※本レポートは情報提供目的のみです", self.styles['CustomBody']))
        
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
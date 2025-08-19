import streamlit as st
import pandas as pd
import numpy as np
import pdfplumber
import openpyxl
from io import BytesIO
import json
import re
from typing import Dict, List, Any, Optional
from valuation import Valuator

class FinancialStatementAnalyzer:
    def __init__(self):
        self.valuator = Valuator()
    
    def extract_from_pdf(self, pdf_file) -> str:
        """PDFファイルからテキストを抽出"""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                for page in pdf.pages[:10]:  # 最初の10ページまで
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            st.error(f"PDF読み取りエラー: {e}")
            return ""
    
    def extract_from_excel(self, excel_file) -> str:
        """Excelファイルからテキストを抽出"""
        try:
            df_dict = pd.read_excel(excel_file, sheet_name=None, nrows=50)
            text = ""
            for sheet_name, df in df_dict.items():
                text += f"=== {sheet_name} ===\n"
                text += df.to_string() + "\n\n"
            return text
        except Exception as e:
            st.error(f"Excel読み取りエラー: {e}")
            return ""
    
    def analyze_financial_data(self, text: str) -> Dict[str, Any]:
        """決算書テキストを解析して財務データを抽出"""
        # 簡易的なパターンマッチング（実際の実装ではより高度な解析が必要）
        financial_data = {
            'revenue': None,
            'ebitda': None, 
            'net_income': None,
            'total_debt': None,
            'cash': None,
            'shares_outstanding': None
        }
        
        # 数値パターンを探す（百万円、億円単位を考慮）
        patterns = {
            'revenue': [r'売上高[^\d]*(\d+(?:,\d{3})*)', r'営業収益[^\d]*(\d+(?:,\d{3})*)', r'売上[^\d]*(\d+(?:,\d{3})*)'],
            'net_income': [r'当期純利益[^\d]*(\d+(?:,\d{3})*)', r'純利益[^\d]*(\d+(?:,\d{3})*)'],
            'total_debt': [r'負債合計[^\d]*(\d+(?:,\d{3})*)', r'総負債[^\d]*(\d+(?:,\d{3})*)'],
            'cash': [r'現金及び現金同等物[^\d]*(\d+(?:,\d{3})*)', r'現金[^\d]*(\d+(?:,\d{3})*)'],
        }
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text)
                if match:
                    value_str = match.group(1).replace(',', '')
                    try:
                        financial_data[key] = float(value_str)
                        break
                    except ValueError:
                        continue
        
        return financial_data
    
    def generate_analysis_prompt(self, financial_data: Dict[str, Any], filename: str) -> str:
        """分析プロンプトを生成"""
        return f"""
        決算書ファイル「{filename}」を解析しました。
        
        抽出されたデータ:
        - 売上高: {financial_data.get('revenue', 'N/A')}
        - 純利益: {financial_data.get('net_income', 'N/A')}  
        - 総負債: {financial_data.get('total_debt', 'N/A')}
        - 現金: {financial_data.get('cash', 'N/A')}
        
        企業価値評価を実行しますか？
        比較企業データも必要ですが、業界平均値を使用することもできます。
        """
    
    def perform_valuation(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """企業価値評価を実行"""
        # デフォルト比較企業データ（業界平均値）
        default_comps = pd.DataFrame({
            'company': ['業界平均'],
            'ev_revenue': [2.5],
            'ev_ebitda': [12.0], 
            'pe_ratio': [18.0]
        })
        
        # EBITDAを売上高の20%と仮定（データが不足している場合）
        if financial_data['revenue'] and not financial_data['ebitda']:
            financial_data['ebitda'] = financial_data['revenue'] * 0.2
        
        # 発行済株式数をデフォルト設定（実際は決算書から抽出すべき）
        if not financial_data['shares_outstanding']:
            financial_data['shares_outstanding'] = 1000  # 1000千株（100万株）
        
        pl_data = {
            'revenue': financial_data['revenue'] or 0,
            'revenue_unit': '百万円',
            'ebitda': financial_data['ebitda'] or 0,
            'ebitda_unit': '百万円',
            'net_income': financial_data['net_income'] or 0,
            'net_income_unit': '百万円'
        }
        
        bs_data = {
            'total_debt': financial_data['total_debt'] or 0,
            'debt_unit': '百万円',
            'cash': financial_data['cash'] or 0,
            'cash_unit': '百万円',
            'shares_outstanding': financial_data['shares_outstanding'],
            'shares_unit': '千株'
        }
        
        return self.valuator.compute_valuation(pl_data, bs_data, default_comps)

def main():
    st.set_page_config(
        page_title="AI企業価値算定チャット",
        page_icon="💰",
        layout="wide"
    )
    
    st.title("💰 AI企業価値算定チャット")
    st.markdown("決算書をアップロードすると、AIが自動で企業価値を算定します")
    
    # セッションステートの初期化
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "こんにちは！決算書ファイル（PDF/Excel）をアップロードしてください。AIが自動で解析し、企業価値を算定します。"
        })
    
    if "analyzer" not in st.session_state:
        st.session_state.analyzer = FinancialStatementAnalyzer()
    
    # サイドバーでファイルアップロード
    with st.sidebar:
        st.header("📁 決算書アップロード")
        uploaded_file = st.file_uploader(
            "決算書ファイルを選択",
            type=['pdf', 'xlsx', 'xls'],
            help="PDF形式またはExcel形式の決算書をアップロードしてください"
        )
        
        if uploaded_file is not None:
            st.success(f"ファイル '{uploaded_file.name}' がアップロードされました")
            
            if st.button("🔍 解析開始", use_container_width=True):
                with st.spinner("決算書を解析中..."):
                    # ファイル解析
                    if uploaded_file.type == "application/pdf":
                        text = st.session_state.analyzer.extract_from_pdf(uploaded_file)
                    else:
                        text = st.session_state.analyzer.extract_from_excel(uploaded_file)
                    
                    if text:
                        # 財務データ抽出
                        financial_data = st.session_state.analyzer.analyze_financial_data(text)
                        
                        # チャットにメッセージ追加
                        analysis_message = st.session_state.analyzer.generate_analysis_prompt(
                            financial_data, uploaded_file.name
                        )
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": analysis_message
                        })
                        
                        # セッションステートに財務データ保存
                        st.session_state.financial_data = financial_data
                        
                        st.rerun()
    
    # チャット表示エリア
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # チャット入力
    if prompt := st.chat_input("メッセージを入力してください..."):
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AIレスポンス
        with st.chat_message("assistant"):
            with st.spinner("分析中..."):
                if "企業価値評価" in prompt or "評価" in prompt or "算定" in prompt:
                    if hasattr(st.session_state, 'financial_data'):
                        # 企業価値評価実行
                        result = st.session_state.analyzer.perform_valuation(
                            st.session_state.financial_data
                        )
                        
                        if result['success']:
                            response = f"""
### 📊 企業価値評価結果

**評価サマリー:**
- 平均株価: ¥{result['summary']['average_share_price']:,.0f}
- 中央値株価: ¥{result['summary']['median_share_price']:,.0f}
- 評価レンジ: {result['summary']['valuation_range']}

**手法別評価:**
"""
                            if 'from_revenue' in result['share_prices']:
                                response += f"- EV/売上倍率: ¥{result['share_prices']['from_revenue']:,.0f}\n"
                            if 'from_ebitda' in result['share_prices']:
                                response += f"- EV/EBITDA倍率: ¥{result['share_prices']['from_ebitda']:,.0f}\n"
                            if 'from_pe' in result['share_prices']:
                                response += f"- P/E倍率: ¥{result['share_prices']['from_pe']:,.0f}\n"
                            
                            response += f"""
**前提条件:**
- 発行済株式数: {result['summary']['shares_outstanding']:,.0f}株
- ネット有利子負債: ¥{result['summary']['net_debt']:,.0f}

何か質問がございましたら、お気軽にお尋ねください！
"""
                        else:
                            response = "申し訳ございませんが、評価に必要なデータが不足しています。決算書の再アップロードまたは手動でのデータ入力をお試しください。"
                    else:
                        response = "まず決算書ファイルをアップロードしてください。"
                
                else:
                    # 一般的な質問への応答
                    response = """
ご質問ありがとうございます。

このシステムでは以下のことができます：
- 決算書（PDF/Excel）の自動解析
- 複数手法による企業価値評価
- 対話的な分析結果の説明

「企業価値評価を実行してください」とお伝えいただければ、アップロードされた決算書データを基に評価を開始します。
"""
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
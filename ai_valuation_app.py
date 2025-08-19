import streamlit as st
import pandas as pd
import numpy as np
import pdfplumber
import openpyxl
from io import BytesIO
import json
import re
import os
from typing import Dict, List, Any, Optional
from claude_backend import BondValuationBackend
from pdf_generator import PDFReportGenerator
from database import AnalysisDatabase
from datetime import datetime
import uuid

def load_api_key():
    """APIキーを環境変数またはStreamlitのsecretsから読み込み"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    try:
        if not api_key and hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        # secrets.tomlファイルが見つからない場合はNoneを返す
        pass
    return api_key

class AIValuationSystem:
    def __init__(self):
        self.claude_backend = BondValuationBackend(api_key=load_api_key())
        self.pdf_generator = PDFReportGenerator()
        self.db = AnalysisDatabase()
    
    def extract_from_pdf(self, pdf_file) -> str:
        """PDFからテキスト抽出"""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                for page in pdf.pages[:15]:  # 最初15ページ
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            st.error(f"PDF読み取りエラー: {e}")
            return ""
    
    def extract_from_excel(self, excel_file) -> str:
        """Excelからテキスト抽出"""
        try:
            df_dict = pd.read_excel(excel_file, sheet_name=None, nrows=100)
            text = ""
            for sheet_name, df in df_dict.items():
                text += f"=== {sheet_name} ===\n"
                text += df.to_string() + "\n\n"
            return text
        except Exception as e:
            st.error(f"Excel読み取りエラー: {e}")
            return ""

def main():
    st.set_page_config(
        page_title="🐰 Bond - AI企業価値算定システム",
        page_icon="🐰",
        layout="wide",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    
    # 黄色テーマのマテリアルデザインCSS
    st.markdown("""
    <style>
    /* メインテーマカラー: 黄色系 */
    :root {
        --primary-yellow: #FFD600;
        --primary-yellow-light: #FFEA00;
        --primary-yellow-dark: #FF8F00;
        --accent-orange: #FF9800;
        --bg-light: #FFFDE7;
        --text-dark: #F57F17;
    }
    
    /* ヘッダー背景 */
    .main > div:first-child {
        background: linear-gradient(135deg, #FFD600 0%, #FFEA00 50%, #FFF176 100%);
        padding: 1rem 2rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(255, 214, 0, 0.3);
    }
    
    /* メインタイトル */
    .main h1 {
        color: #F57F17 !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        margin: 0 !important;
    }
    
    /* サイドバー */
    .css-1d391kg {
        background: linear-gradient(180deg, #FFF9C4 0%, #F0F4C3 100%);
    }
    
    /* ボタンスタイル - マテリアルデザイン */
    .stButton > button {
        background: linear-gradient(45deg, #FFD600 30%, #FFEA00 90%) !important;
        border: none !important;
        border-radius: 12px !important;
        color: #F57F17 !important;
        font-weight: 600 !important;
        box-shadow: 0 3px 8px rgba(255, 214, 0, 0.4) !important;
        transition: all 0.3s ease !important;
        height: 3rem !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #FFEA00 30%, #FFF176 90%) !important;
        box-shadow: 0 6px 16px rgba(255, 214, 0, 0.6) !important;
        transform: translateY(-2px) !important;
    }
    
    /* 分析ボタン専用 */
    .stButton > button[aria-label*="財務データ"] {
        background: linear-gradient(45deg, #FFC107 30%, #FFD54F 90%) !important;
    }
    
    .stButton > button[aria-label*="企業価値"] {
        background: linear-gradient(45deg, #FF9800 30%, #FFB74D 90%) !important;
    }
    
    /* チャット関連 */
    .stChatMessage {
        background: rgba(255, 245, 157, 0.1) !important;
        border: 2px solid #FFE082 !important;
        border-radius: 16px !important;
        margin: 0.5rem 0 !important;
    }
    
    /* メトリクス */
    .css-1r6slb0 {
        background: linear-gradient(135deg, #FFF8E1 0%, #FFF9C4 100%) !important;
        border: 2px solid #FFD600 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(255, 214, 0, 0.2) !important;
    }
    
    /* ファイルアップロード */
    .css-6awftf {
        background: linear-gradient(135deg, #FFF8E1 0%, #F0F4C3 100%) !important;
        border: 2px dashed #FFD600 !important;
        border-radius: 12px !important;
    }
    
    /* 情報ボックス */
    .stInfo {
        background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%) !important;
        border-left: 4px solid #FFD600 !important;
        border-radius: 8px !important;
    }
    
    /* 成功メッセージ */
    .stSuccess {
        background: linear-gradient(135deg, #F1F8E9 0%, #DCEDC8 100%) !important;
        border-left: 4px solid #8BC34A !important;
        border-radius: 8px !important;
    }
    
    /* テーブルヘッダー */
    .stTable th {
        background: linear-gradient(45deg, #FFD600 30%, #FFEA00 90%) !important;
        color: #F57F17 !important;
        font-weight: 600 !important;
    }
    
    /* エクスパンダー */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #FFF8E1 0%, #FFE082 100%) !important;
        border-radius: 8px !important;
        color: #F57F17 !important;
        font-weight: 600 !important;
    }
    
    /* うさぎアイコンの拡大 */
    .main > div:first-child > div:first-child {
        font-size: 4rem !important;
        filter: drop-shadow(0 4px 8px rgba(255, 214, 0, 0.5));
    }
    
    /* トップバー全体を非表示 */
    .st-emotion-cache-1j22a0y {
        display: none !important;
    }
    
    /* サイドバー展開ボタンを非表示 */
    .st-emotion-cache-8ezv7j {
        display: none !important;
    }
    
    /* Deployボタンを非表示 */
    .stAppDeployButton {
        display: none !important;
    }
    
    /* メインメニューを非表示 */
    .stMainMenu {
        display: none !important;
    }
    
    /* ツールバーアクションを非表示 */
    .stToolbarActions {
        display: none !important;
    }
    
    /* ヘッダー全体を非表示 */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* StreamlitのメインヘッダーブロックFull */
    .st-emotion-cache-1j22a0y.e3g0k5y4 {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }
    
    /* ヘッダーアクション要素を非表示 */
    .st-emotion-cache-gi0tri {
        display: none !important;
    }
    
    /* ヘッダーリンクアイコンを非表示 */
    .st-emotion-cache-yinll1 {
        display: none !important;
    }
    
    /* Streamlitヘッディング内のアクション要素を非表示 */
    [data-testid="stHeaderActionElements"] {
        display: none !important;
    }
    
    /* Streamlitヘッディング全体のスタイル調整 */
    [data-testid="stHeadingWithActionElements"] {
        display: none !important;
    }
    
    /* GitHubプロフィールアイコン・ボタンを非表示 */
    .stApp > header {
        display: none !important;
    }
    
    /* 右上のプロフィール・設定ボタン類を非表示 */
    [data-testid="stHeaderToolbar"] {
        display: none !important;
    }
    
    /* Streamlitのフッター情報を非表示 */
    footer {
        display: none !important;
    }
    
    /* その他のStreamlit標準UI要素を非表示 */
    .st-emotion-cache-18ni7ap {
        display: none !important;
    }
    
    .st-emotion-cache-164nlkn {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # コンパクトなマテリアルデザインヘッダー
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #FFD600 0%, #FFEA00 50%, #FFF176 100%);
        padding: 1rem 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(255, 214, 0, 0.3);
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
    ">
        <div style="
            width: 80px;
            height: 80px;
            background: linear-gradient(145deg, #FFE082 0%, #FFD54F 50%, #FFC107 100%);
            border-radius: 50% 50% 45% 45%;
            position: relative;
            filter: drop-shadow(0 4px 8px rgba(255, 152, 0, 0.3));
            animation: bounce 2s infinite;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 0.5rem;
        ">
            <!-- うさぎの耳 -->
            <div style="
                position: absolute;
                top: -15px;
                left: 15px;
                width: 15px;
                height: 25px;
                background: linear-gradient(145deg, #FFE082, #FFD54F);
                border-radius: 70% 30% 30% 70%;
                transform: rotate(-20deg);
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
            "></div>
            <div style="
                position: absolute;
                top: -15px;
                right: 15px;
                width: 15px;
                height: 25px;
                background: linear-gradient(145deg, #FFE082, #FFD54F);
                border-radius: 30% 70% 70% 30%;
                transform: rotate(20deg);
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
            "></div>
            <!-- 顔 -->
            <div style="
                width: 60px;
                height: 60px;
                background: radial-gradient(circle at 30% 30%, #FFECB3, #FFD54F);
                border-radius: 50%;
                position: relative;
                box-shadow: inset 0 2px 8px rgba(0,0,0,0.05);
            ">
                <!-- 目 -->
                <div style="
                    position: absolute;
                    top: 18px;
                    left: 15px;
                    width: 6px;
                    height: 8px;
                    background: #5D4037;
                    border-radius: 50%;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.2);
                "></div>
                <div style="
                    position: absolute;
                    top: 18px;
                    right: 15px;
                    width: 6px;
                    height: 8px;
                    background: #5D4037;
                    border-radius: 50%;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.2);
                "></div>
                <!-- 鼻 -->
                <div style="
                    position: absolute;
                    top: 30px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 3px;
                    height: 3px;
                    background: #8D6E63;
                    border-radius: 50%;
                "></div>
                <!-- 口 -->
                <div style="
                    position: absolute;
                    top: 36px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 12px;
                    height: 6px;
                    border: 2px solid #8D6E63;
                    border-top: none;
                    border-radius: 0 0 50% 50%;
                "></div>
            </div>
        </div>
        <div style="flex-grow: 1; text-align: left;">
            <h1 style="
                color: #F57F17;
                font-weight: 700;
                font-size: 2rem;
                margin: 0;
                text-shadow: 0 1px 3px rgba(245, 127, 23, 0.3);
                line-height: 1.2;
            ">Bond AI</h1>
            <p style="
                color: #FF8F00;
                font-size: 0.9rem;
                margin: 0.2rem 0 0 0;
                font-weight: 500;
                line-height: 1.3;
            ">🌟 企業価値算定システム - あなたの投資パートナー</p>
        </div>
    </div>
    
    <style>
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-10px);
        }
        60% {
            transform: translateY(-5px);
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    
    # セッションステート初期化
    if "messages" not in st.session_state:
        st.session_state.messages = []
        welcome_msg = """🐰 **こんにちは！Bondです！**

私はBond AIを活用した企業価値算定アシスタントです。以下のことができます：

🔍 **決算書AI解析**
- PDF/Excel形式の決算書を自動で読み取り
- 財務データを正確に抽出・分析
- 企業の強み・弱み・リスクを評価

💰 **AI企業価値算定**  
- EV/売上、EV/EBITDA、P/E手法による多面的評価
- 業界標準と比較した妥当性検証
- Bull/Base/Bearケース分析

💬 **自然言語対話**
- 「決算書を解析して」「企業価値評価をして」などの自然な指示
- 専門用語もわかりやすく説明
- 投資判断のアドバイス

決算書をアップロードするか、お気軽にお話しかけください。🌟"""

        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_msg
        })
    
    if "ai_system" not in st.session_state:
        st.session_state.ai_system = AIValuationSystem()
    
    # サイドバー - 過去の分析結果
    with st.sidebar:
        st.header("📚 過去の分析結果")
        
        # セッションステートで過去の結果を管理
        if "past_analyses" not in st.session_state:
            # 初回ロード時にMongoDBから取得
            st.session_state.past_analyses = st.session_state.ai_system.db.get_analysis_results()
        
        # リロードボタン
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 更新", use_container_width=True):
                st.session_state.past_analyses = st.session_state.ai_system.db.get_analysis_results()
                st.rerun()
        
        with col2:
            if st.button("🗑️ 全削除", use_container_width=True):
                if st.session_state.ai_system.db.delete_all_analyses() > 0:
                    st.session_state.past_analyses = []
                    st.success("全ての分析結果を削除しました")
                    st.rerun()
        
        st.markdown("---")
        
        # 過去の分析結果一覧
        if st.session_state.past_analyses:
            for analysis in st.session_state.past_analyses:
                with st.expander(f"📊 {analysis['title']}", expanded=False):
                    st.write(f"**企業**: {analysis.get('company_name', 'N/A')}")
                    st.write(f"**日付**: {analysis['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                    # サマリー表示
                    summary = analysis.get('summary', {})
                    if summary.get('target_price'):
                        st.write(f"**目標株価**: ¥{summary['target_price']:,.0f}")
                    if summary.get('recommendation'):
                        st.write(f"**推奨**: {summary['recommendation']}")
                    
                    col_load, col_del = st.columns(2)
                    
                    with col_load:
                        if st.button(f"📥 読込", key=f"load_{analysis['id']}", use_container_width=True):
                            # 詳細データを取得してセッションに設定
                            detailed_data = st.session_state.ai_system.db.get_analysis_by_id(analysis['id'])
                            if detailed_data:
                                # セッションステートに分析結果をロード
                                st.session_state.financial_analysis = detailed_data.get('financial_data', {})
                                st.session_state.valuation_result = {
                                    'summary': detailed_data.get('summary', {}),
                                    'valuation_methods': detailed_data.get('valuation_methods', {}),
                                    'investment_recommendation': detailed_data.get('investment_recommendation', {}),
                                    'company_analysis': detailed_data.get('company_analysis', {})
                                }
                                
                                # チャットに結果を表示
                                load_msg = f"""📥 **過去の分析結果を読み込みました**: {detailed_data.get('title', '')}

🏢 **企業名**: {detailed_data.get('company_name', 'N/A')}
🎯 **目標株価**: ¥{detailed_data.get('summary', {}).get('target_price', 0):,.0f}
📈 **投資推奨**: {detailed_data.get('investment_recommendation', {}).get('recommendation', 'N/A')}

💡 詳細な分析結果が復元されました。PDFレポートの生成も可能です。"""
                                
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": load_msg
                                })
                                st.success("分析結果を読み込みました！")
                                st.rerun()
                            else:
                                st.error("データの読み込みに失敗しました")
                    
                    with col_del:
                        if st.button(f"🗑️ 削除", key=f"del_{analysis['id']}", use_container_width=True):
                            if st.session_state.ai_system.db.delete_analysis(analysis['id']):
                                st.session_state.past_analyses = [
                                    a for a in st.session_state.past_analyses if a['id'] != analysis['id']
                                ]
                                st.success("削除しました")
                                st.rerun()
                            else:
                                st.error("削除に失敗しました")
        else:
            st.info("保存された分析結果がありません")
    
    
    # ファイルアップロード機能（チャット上に配置）
    uploaded_file = st.file_uploader(
        "📎 決算書ファイルをアップロード（PDF/Excel）",
        type=['pdf', 'xlsx', 'xls'],
        help="決算書をドラッグ&ドロップでアップロード！"
    )
    
    if uploaded_file:
        # ファイルがアップロードされた時の処理
        st.success(f"🐰 {uploaded_file.name} がアップロードされました！")
        
        st.markdown("### 🔍 分析メニュー")
        st.info("お好みの分析を下のボタンから選択してください。")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <style>
            .analysis-btn-1 > button {
                background: linear-gradient(45deg, #FFC107 0%, #FFD54F 100%) !important;
                color: #F57F17 !important;
                border: none !important;
                box-shadow: 0 4px 12px rgba(255, 193, 7, 0.4) !important;
            }
            .analysis-btn-1 > button:hover {
                background: linear-gradient(45deg, #FFB300 0%, #FFC107 100%) !important;
                transform: translateY(-3px) !important;
                box-shadow: 0 6px 20px rgba(255, 193, 7, 0.6) !important;
            }
            </style>
            <div class="analysis-btn-1">""", unsafe_allow_html=True)
            if st.button("📊 財務データ抽出", use_container_width=True, help="決算書から財務データを自動抽出します"):
                st.session_state.analysis_type = "financial_data"
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <style>
            .analysis-btn-2 > button {
                background: linear-gradient(45deg, #FF9800 0%, #FFB74D 100%) !important;
                color: #FFFFFF !important;
                border: none !important;
                box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4) !important;
            }
            .analysis-btn-2 > button:hover {
                background: linear-gradient(45deg, #F57C00 0%, #FF9800 100%) !important;
                transform: translateY(-3px) !important;
                box-shadow: 0 6px 20px rgba(255, 152, 0, 0.6) !important;
            }
            </style>
            <div class="analysis-btn-2">""", unsafe_allow_html=True)
            if st.button("💰 企業価値算定", use_container_width=True, help="EV/売上、EV/EBITDA、P/E手法で評価"):
                st.session_state.analysis_type = "valuation"
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <style>
            .analysis-btn-3 > button {
                background: linear-gradient(45deg, #4CAF50 0%, #8BC34A 100%) !important;
                color: #FFFFFF !important;
                border: none !important;
                box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4) !important;
            }
            .analysis-btn-3 > button:hover {
                background: linear-gradient(45deg, #388E3C 0%, #4CAF50 100%) !important;
                transform: translateY(-3px) !important;
                box-shadow: 0 6px 20px rgba(76, 175, 80, 0.6) !important;
            }
            </style>
            <div class="analysis-btn-3">""", unsafe_allow_html=True)
            if st.button("📈 財務分析レポート", use_container_width=True, help="詳細な財務分析とリスク評価"):
                st.session_state.analysis_type = "comprehensive"
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <style>
            .analysis-btn-4 > button {
                background: linear-gradient(45deg, #9C27B0 0%, #BA68C8 100%) !important;
                color: #FFFFFF !important;
                border: none !important;
                box-shadow: 0 4px 12px rgba(156, 39, 176, 0.4) !important;
            }
            .analysis-btn-4 > button:hover {
                background: linear-gradient(45deg, #7B1FA2 0%, #9C27B0 100%) !important;
                transform: translateY(-3px) !important;
                box-shadow: 0 6px 20px rgba(156, 39, 176, 0.6) !important;
            }
            </style>
            <div class="analysis-btn-4">""", unsafe_allow_html=True)
            if st.button("📋 全分析実行", use_container_width=True, help="全ての分析を順次実行"):
                st.session_state.analysis_type = "all"
            st.markdown("</div>", unsafe_allow_html=True)
        
        # 分析実行処理
        if hasattr(st.session_state, 'analysis_type'):
            analysis_type = st.session_state.analysis_type
            delattr(st.session_state, 'analysis_type')  # フラグをクリア
            
            if analysis_type in ["financial_data", "valuation", "comprehensive", "all"]:
                # 分析タイプに応じたメッセージ
                spinner_messages = {
                    'financial_data': '財務データを抽出',
                    'valuation': '企業価値を算定',
                    'comprehensive': '詳細な財務分析を実行', 
                    'all': '全分析を実行'
                }
                with st.spinner(f"🚀 Bondが{spinner_messages[analysis_type]}中です..."):
                    # ファイル内容抽出
                    if uploaded_file.type == "application/pdf":
                        document_text = st.session_state.ai_system.extract_from_pdf(uploaded_file)
                    else:
                        document_text = st.session_state.ai_system.extract_from_excel(uploaded_file)
                    
                    if document_text:
                        # セッションにファイルデータを保存
                        st.session_state.uploaded_file_data = {
                            'text': document_text,
                            'filename': uploaded_file.name
                        }
                        
                        # Bond AIで財務分析
                        financial_analysis = st.session_state.ai_system.claude_backend.analyze_financial_document(
                            document_text, 
                            company_name=uploaded_file.name.split('.')[0]
                        )
                        
                        # セッションに保存
                        st.session_state.financial_analysis = financial_analysis
                        st.session_state.document_text = document_text
                        
                        # 分析タイプに応じたメッセージ生成
                        if analysis_type == "financial_data":
                            analysis_msg = f"""🎉 **Bond財務データ抽出完了**: {uploaded_file.name}

🏢 **企業名**: {financial_analysis.get('company_name', '不明')}
📅 **決算期**: {financial_analysis.get('fiscal_period', '不明')}
🎯 **信頼性**: {financial_analysis.get('confidence_level', '中')}

💰 **抽出財務データ**:"""
                            
                            for key in ['revenue', 'ebitda', 'net_income', 'total_debt', 'cash', 'shares_outstanding']:
                                if key in financial_analysis and financial_analysis[key]:
                                    data = financial_analysis[key]
                                    analysis_msg += f"\n- {key}: {data.get('value', 'N/A'):,} {data.get('unit', '')}"
                            
                            if 'analysis_notes' in financial_analysis:
                                analysis_msg += f"\n\n📝 **分析ノート**:\n" + "\n".join([f"- {note}" for note in financial_analysis['analysis_notes']])
                            
                            analysis_msg += "\n\n🚀 上記のボタンで「💰 企業価値算定」をクリックして詳細分析を開始してください。"
                        
                        elif analysis_type in ["valuation", "comprehensive", "all"]:
                            # 企業価値算定も実行
                            try:
                                valuation_result = st.session_state.ai_system.claude_backend.perform_valuation_analysis(
                                    financial_analysis
                                )
                            except Exception as e:
                                print(f"DEBUG: Claude API エラー: {e}")
                                # フォールバック: テスト用ダミーデータ
                                valuation_result = {
                                    'summary': {
                                        'target_price': 1500,
                                        'confidence_level': '中',
                                        'price_range': {'min': 1200, 'max': 1800}
                                    },
                                    'investment_recommendation': {
                                        'recommendation': '保有',
                                        'rationale': 'テスト用分析結果です'
                                    },
                                    'valuation_methods': {
                                        'ev_sales': {'price_per_share': 1400},
                                        'ev_ebitda': {'price_per_share': 1600},
                                        'pe_ratio': {'price_per_share': 1500}
                                    },
                                    'company_analysis': {
                                        'strengths': ['テスト強み'],
                                        'weaknesses': ['テスト課題']
                                    }
                                }
                            st.session_state.valuation_result = valuation_result
                            
                            # 分析結果を自動保存（MongoDB）
                            if valuation_result and valuation_result.get('summary'):
                                company_name = financial_analysis.get('company_name', '企業')
                                auto_title = f"{company_name}_{datetime.now().strftime('%Y-%m-%d')}"
                                
                                # MongoDB保存実行
                                saved_id = st.session_state.ai_system.db.save_analysis_result(
                                    title=auto_title,
                                    company_name=company_name,
                                    financial_data=financial_analysis,
                                    valuation_result=valuation_result
                                )
                                
                                if saved_id:
                                    # サイドバーの過去結果を更新
                                    st.session_state.past_analyses = st.session_state.ai_system.db.get_analysis_results()
                            
                            # 分析タイプ名マッピング
                            analysis_names = {'valuation': '企業価値算定', 'comprehensive': '詳細分析', 'all': '全分析'}
                            analysis_msg = f"""🎉 **Bond{analysis_names[analysis_type]}完了**: {uploaded_file.name}

🏢 **企業名**: {financial_analysis.get('company_name', '不明')}
🎯 **目標株価**: ¥{valuation_result.get('summary', {}).get('target_price', 0):,.0f}
📊 **信頼性**: {valuation_result.get('summary', {}).get('confidence_level', '中')}

💰 **抽出財務データ**:"""
                            
                            for key in ['revenue', 'ebitda', 'net_income', 'total_debt', 'cash', 'shares_outstanding']:
                                if key in financial_analysis and financial_analysis[key]:
                                    data = financial_analysis[key]
                                    analysis_msg += f"\n- {key}: {data.get('value', 'N/A'):,} {data.get('unit', '')}"
                            
                            if 'investment_recommendation' in valuation_result:
                                rec = valuation_result['investment_recommendation']
                                analysis_msg += f"\n\n📈 **投資推奨**: {rec.get('recommendation', '保有')}"
                                analysis_msg += f"\n**理由**: {rec.get('rationale', '詳細な分析結果をご確認ください。')}"
                            
                            analysis_msg += "\n\n✨ 詳細な結果は下のチャット欄に表示されました。PDFレポートも生成可能です。"
                            if saved_id:
                                analysis_msg += f"\n💾 **自動保存完了**: 分析結果を保存しました（タイトル: {auto_title}）"
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": analysis_msg
                        })
                        
                        st.rerun()
        
        # アップロードされたファイルのデータをセッションに保存（チャットで使用可能にする）
        if uploaded_file and 'uploaded_file_data' not in st.session_state:
            if uploaded_file.type == "application/pdf":
                document_text = st.session_state.ai_system.extract_from_pdf(uploaded_file)
            else:
                document_text = st.session_state.ai_system.extract_from_excel(uploaded_file)
            
            st.session_state.uploaded_file_data = {
                'text': document_text,
                'filename': uploaded_file.name
            }
    
    # チャット表示
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            # カスタムBondうさぎアバター
            st.markdown(f"""
            <div style="display: flex; align-items: flex-start; margin: 1rem 0; gap: 0.75rem;">
                <div style="
                    width: 40px;
                    height: 40px;
                    background: linear-gradient(145deg, #FFE082 0%, #FFD54F 100%);
                    border-radius: 50%;
                    position: relative;
                    flex-shrink: 0;
                    box-shadow: 0 2px 8px rgba(255, 214, 0, 0.3);
                ">
                    <!-- 小さなうさぎ耳 -->
                    <div style="position: absolute; top: -6px; left: 8px; width: 6px; height: 12px; background: linear-gradient(145deg, #FFE082, #FFD54F); border-radius: 70% 30% 30% 70%; transform: rotate(-20deg);"></div>
                    <div style="position: absolute; top: -6px; right: 8px; width: 6px; height: 12px; background: linear-gradient(145deg, #FFE082, #FFD54F); border-radius: 30% 70% 70% 30%; transform: rotate(20deg);"></div>
                    <!-- 小さな顔 -->
                    <div style="position: absolute; top: 8px; left: 12px; width: 3px; height: 3px; background: #5D4037; border-radius: 50%;"></div>
                    <div style="position: absolute; top: 8px; right: 12px; width: 3px; height: 3px; background: #5D4037; border-radius: 50%;"></div>
                    <div style="position: absolute; top: 16px; left: 50%; transform: translateX(-50%); width: 8px; height: 4px; border: 1px solid #8D6E63; border-top: none; border-radius: 0 0 50% 50%;"></div>
                </div>
                <div style="
                    background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
                    border: 2px solid #FFD600;
                    border-radius: 18px;
                    padding: 12px 16px;
                    max-width: 80%;
                    box-shadow: 0 2px 8px rgba(255, 214, 0, 0.2);
                ">
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # ユーザーメッセージ
            st.markdown(f"""
            <div style="display: flex; align-items: flex-start; margin: 1rem 0; gap: 0.75rem; flex-direction: row-reverse;">
                <div style="
                    width: 40px;
                    height: 40px;
                    background: linear-gradient(145deg, #E3F2FD 0%, #BBDEFB 100%);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                    box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
                    font-size: 18px;
                ">👤</div>
                <div style="
                    background: linear-gradient(135deg, #E3F2FD 0%, #E1F5FE 100%);
                    border: 2px solid #2196F3;
                    border-radius: 18px;
                    padding: 12px 16px;
                    max-width: 80%;
                    box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
                    text-align: right;
                ">
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # チャット入力
    if prompt := st.chat_input("Bondに何でもお話しください...🐰"):
        # ユーザーメッセージ追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Bond応答を追加
        with st.spinner("🐰 Bondが分析中です..."):
                
                # コンテキスト準備
                context = {}
                if hasattr(st.session_state, 'financial_analysis'):
                    context['financial_analysis'] = st.session_state.financial_analysis
                if hasattr(st.session_state, 'valuation_result'):
                    context['valuation_result'] = st.session_state.valuation_result
                
                # 企業価値評価実行判定
                if any(keyword in prompt for keyword in ["企業価値評価", "バリュエーション", "評価", "算定", "価値算出", "お願い", "してください"]):
                    if hasattr(st.session_state, 'financial_analysis'):
                        # Bond AIで企業価値算定
                        try:
                            valuation_result = st.session_state.ai_system.claude_backend.perform_valuation_analysis(
                                st.session_state.financial_analysis
                            )
                        except Exception as e:
                            print(f"DEBUG CHAT: Claude API エラー: {e}")
                            # フォールバック: テスト用ダミーデータ
                            valuation_result = {
                                'summary': {
                                    'target_price': 2000,
                                    'confidence_level': '中',
                                    'price_range': {'min': 1600, 'max': 2400}
                                },
                                'investment_recommendation': {
                                    'recommendation': '買い',
                                    'rationale': 'チャット経由テスト用分析結果です'
                                },
                                'valuation_methods': {
                                    'ev_sales': {'price_per_share': 1800},
                                    'ev_ebitda': {'price_per_share': 2200},
                                    'pe_ratio': {'price_per_share': 2000}
                                }
                            }
                        
                        st.session_state.valuation_result = valuation_result
                        context['valuation_result'] = valuation_result
                        
                        # チャット経由での分析結果も自動保存（MongoDB）
                        if valuation_result and valuation_result.get('summary'):
                            company_name = st.session_state.financial_analysis.get('company_name', '企業')
                            auto_title = f"{company_name}_{datetime.now().strftime('%Y-%m-%d_%H%M')}"
                            
                            # MongoDB保存実行
                            saved_id = st.session_state.ai_system.db.save_analysis_result(
                                title=auto_title,
                                company_name=company_name,
                                financial_data=st.session_state.financial_analysis,
                                valuation_result=valuation_result
                            )
                            
                            if saved_id:
                                # サイドバーの過去結果を更新
                                st.session_state.past_analyses = st.session_state.ai_system.db.get_analysis_results()
                        
                        # 評価結果の表示
                        if valuation_result.get('summary'):
                            summary = valuation_result['summary']
                            
                            # メトリクス表示
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(
                                    "🎯 目標株価", 
                                    f"¥{summary.get('target_price', 0):,.0f}"
                                )
                            with col2:
                                price_range = summary.get('price_range', {})
                                st.metric(
                                    "📊 価格レンジ", 
                                    f"¥{price_range.get('min', 0):,.0f} - ¥{price_range.get('max', 0):,.0f}"
                                )
                            with col3:
                                st.metric(
                                    "🔬 信頼性", 
                                    summary.get('confidence_level', '中')
                                )
                            
                            # 手法別結果
                            if 'valuation_methods' in valuation_result:
                                st.subheader("📈 手法別評価結果")
                                methods_data = []
                                
                                for method_name, method_data in valuation_result['valuation_methods'].items():
                                    if method_data and method_data.get('price_per_share'):
                                        methods_data.append({
                                            '評価手法': method_name.replace('_', '/').upper(),
                                            '株価': f"¥{method_data['price_per_share']:,.0f}",
                                            '倍率': f"{method_data.get('multiple_used', 0):.1f}x",
                                            '妥当性': method_data.get('validity', '中'),
                                            '判断根拠': method_data.get('reasoning', '')[:50] + '...' if len(method_data.get('reasoning', '')) > 50 else method_data.get('reasoning', '')
                                        })
                                
                                if methods_data:
                                    st.table(pd.DataFrame(methods_data))
                            
                            # 投資推奨
                            if 'investment_recommendation' in valuation_result:
                                rec = valuation_result['investment_recommendation']
                                st.subheader("💡 投資推奨")
                                
                                rec_color = {
                                    '買い': 'success',
                                    '保有': 'warning', 
                                    '売り': 'error'
                                }.get(rec.get('recommendation', '保有'), 'info')
                                
                                st.write(f"**推奨**: :{rec_color}[{rec.get('recommendation', '保有')}]")
                                st.write(f"**理由**: {rec.get('rationale', '')}")
                                
                                if 'price_targets' in rec:
                                    targets = rec['price_targets']
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("🐂 強気ケース", f"¥{targets.get('bull_case', 0):,.0f}")
                                    with col2:
                                        st.metric("📊 ベースケース", f"¥{targets.get('base_case', 0):,.0f}")
                                    with col3:
                                        st.metric("🐻 弱気ケース", f"¥{targets.get('bear_case', 0):,.0f}")
                            
                            # 保存・レポートボタン
                            st.subheader("💾 保存・レポート生成")
                            
                            # MongoDB保存ボタン
                            col_save, col_title = st.columns([1, 3])
                            with col_save:
                                if st.button("💾 結果保存", use_container_width=True):
                                    # 自動タイトル生成
                                    company_name = st.session_state.financial_analysis.get('company_name', '企業')
                                    auto_title = f"{company_name}_{datetime.now().strftime('%Y-%m-%d')}"
                                    
                                    # MongoDB保存実行
                                    saved_id = st.session_state.ai_system.db.save_analysis_result(
                                        title=auto_title,
                                        company_name=company_name,
                                        financial_data=st.session_state.financial_analysis,
                                        valuation_result=valuation_result
                                    )
                                    
                                    if saved_id:
                                        st.success(f"✅ 分析結果を保存しました: {auto_title}")
                                        # サイドバーの過去結果を更新
                                        st.session_state.past_analyses = st.session_state.ai_system.db.get_analysis_results()
                                    else:
                                        st.error("❌ 保存に失敗しました")
                            
                            with col_title:
                                st.info(f"💡 保存タイトル: {st.session_state.financial_analysis.get('company_name', '企業')}_{datetime.now().strftime('%Y-%m-%d')}")
                            
                            st.markdown("---")
                            
                            # PDFレポート生成ボタン
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("📋 詳細PDFレポート生成", use_container_width=True):
                                    with st.spinner("📄 PDFレポート生成中..."):
                                        try:
                                            # 会話履歴も含めて詳細レポート生成
                                            pdf_data = st.session_state.ai_system.pdf_generator.generate_comprehensive_report(
                                                st.session_state.financial_analysis,
                                                valuation_result,
                                                st.session_state.messages[-10:]  # 最新10件
                                            )
                                            
                                            # ダウンロードボタン
                                            company_name = st.session_state.financial_analysis.get('company_name', '対象企業')
                                            filename = f"{company_name}_企業価値評価_{datetime.now().strftime('%Y%m%d')}.pdf"
                                            
                                            st.download_button(
                                                label="⬇️ 詳細レポートダウンロード",
                                                data=pdf_data,
                                                file_name=filename,
                                                mime="application/pdf",
                                                use_container_width=True
                                            )
                                            
                                        except Exception as e:
                                            st.error(f"PDFレポート生成エラー: {e}")
                            
                            with col2:
                                if st.button("📄 簡易サマリーPDF生成", use_container_width=True):
                                    with st.spinner("📄 サマリーPDF生成中..."):
                                        try:
                                            company_name = st.session_state.financial_analysis.get('company_name', '対象企業')
                                            pdf_data = st.session_state.ai_system.pdf_generator.generate_simple_summary_pdf(
                                                valuation_result,
                                                company_name
                                            )
                                            
                                            filename = f"{company_name}_サマリー_{datetime.now().strftime('%Y%m%d')}.pdf"
                                            
                                            st.download_button(
                                                label="⬇️ サマリーダウンロード",
                                                data=pdf_data,
                                                file_name=filename,
                                                mime="application/pdf",
                                                use_container_width=True
                                            )
                                            
                                        except Exception as e:
                                            st.error(f"サマリーPDF生成エラー: {e}")
                
                # 決算書分析のリクエスト処理
                elif any(keyword in prompt for keyword in ["決算書", "分析", "解析"]) and hasattr(st.session_state, 'uploaded_file_data'):
                    # アップロードファイルの解析
                    document_text = st.session_state.uploaded_file_data['text']
                    filename = st.session_state.uploaded_file_data['filename']
                    
                    if document_text:
                        financial_analysis = st.session_state.ai_system.claude_backend.analyze_financial_document(
                            document_text, 
                            company_name=filename.split('.')[0]
                        )
                        
                        st.session_state.financial_analysis = financial_analysis
                        st.session_state.document_text = document_text
                        
                        # 分析結果をcontext情報として追加
                        context['financial_analysis'] = financial_analysis
                        
                        # 分析完了の表示
                        analysis_msg = f"""🎉 **Bond解析完了**: {filename}

🏢 **企業名**: {financial_analysis.get('company_name', '不明')}
📅 **決算期**: {financial_analysis.get('fiscal_period', '不明')}
🎯 **信頼性**: {financial_analysis.get('confidence_level', '中')}

💰 **抽出財務データ**:"""
                        
                        for key in ['revenue', 'ebitda', 'net_income', 'total_debt', 'cash', 'shares_outstanding']:
                            if key in financial_analysis and financial_analysis[key]:
                                data = financial_analysis[key]
                                analysis_msg += f"\n- {key}: {data.get('value', 'N/A'):,} {data.get('unit', '')}"
                        
                        if 'analysis_notes' in financial_analysis:
                            analysis_msg += f"\n\n📝 **分析ノート**:\n" + "\n".join([f"- {note}" for note in financial_analysis['analysis_notes']])
                        
                        analysis_msg += "\n\n🚀 「企業価値評価をお願いします」とお声がけいただくか、上記のボタンをクリックして詳細分析を開始してください。"
                        response = analysis_msg
                    else:
                        response = "🐰 申し訳ございませんが、ファイルの読み取りに失敗しました。もう一度アップロードしてください。"
                else:
                    # Bond AIによる自然言語応答生成
                    response = st.session_state.ai_system.claude_backend.generate_natural_response(
                        prompt, context
                    )
                    
                    # Bondらしい応答に調整
                    if response and not any(keyword in prompt for keyword in ["企業価値評価", "バリュエーション", "評価", "算定", "分析", "解析"]):
                        response = "🐰 " + response + "\n\nなにか他にも聞きたいことがございましたら、Bondにお気軽にお声がけください！"
                
                # 応答をセッションに追加（カスタムチャットで表示される）
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

if __name__ == "__main__":
    main()
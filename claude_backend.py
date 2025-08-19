"""
Claude AI統合バックエンドシステム
決算書解析から企業価値算定まで全てClaude AIが自動実行
"""

import anthropic
import json
import re
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import os
from datetime import datetime
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BondValuationBackend:
    def __init__(self, api_key: str = None):
        """
        Bond AI統合バックエンド初期化
        
        Args:
            api_key: Anthropic APIキー（環境変数ANTHROPIC_API_KEYからも取得可能）
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not found. Bond AI機能は無効化されます。")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def analyze_financial_document(self, document_text: str, company_name: str = None) -> Dict[str, Any]:
        """
        Bond AIが決算書を解析し、財務データを抽出
        
        Args:
            document_text: 決算書のテキスト
            company_name: 企業名（オプション）
            
        Returns:
            財務データ辞書
        """
        if not self.client:
            return self._fallback_analysis(document_text)
        
        prompt = f"""
あなたは経験豊富なファイナンシャルアナリストです。以下の決算書データから財務情報を正確に抽出してください。

# 決算書データ
{document_text}

# 抽出対象項目
1. 企業名（document内から推測）
2. 決算期間・基準日
3. 売上高（売上・営業収益等）
4. EBITDA（または営業利益から推計）
5. 当期純利益
6. 総負債（借入金・社債等の有利子負債）
7. 現金・現金同等物
8. 発行済株式数
9. 各数値の単位（円、千円、百万円、億円等）

# 出力形式
以下のJSON形式で出力してください：
```json
{{
    "company_name": "企業名",
    "fiscal_period": "2024年3月期",
    "revenue": {{
        "value": 数値,
        "unit": "百万円",
        "source": "売上高として記載"
    }},
    "ebitda": {{
        "value": 数値,
        "unit": "百万円", 
        "source": "営業利益+減価償却費として推計"
    }},
    "net_income": {{
        "value": 数値,
        "unit": "百万円",
        "source": "当期純利益として記載"
    }},
    "total_debt": {{
        "value": 数値,
        "unit": "百万円",
        "source": "借入金合計として記載"
    }},
    "cash": {{
        "value": 数値,
        "unit": "百万円",
        "source": "現金及び現金同等物として記載"
    }},
    "shares_outstanding": {{
        "value": 数値,
        "unit": "千株",
        "source": "発行済株式数として記載"
    }},
    "analysis_notes": [
        "重要な発見事項や推計根拠",
        "データ品質に関する注意点"
    ],
    "confidence_level": "高・中・低"
}}
```

# 重要な注意事項
- 数値は可能な限り正確に抽出
- 単位を必ず明記
- 推計や仮定を行った場合はsourceで説明
- データが不明な場合はnullとし、analysis_notesで言及
- 複数の可能性がある場合は最も確からしいものを選択
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # JSONを抽出
            content = response.content[0].text
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            
            if json_match:
                return json.loads(json_match.group(1))
            else:
                logger.warning("Claude AI response does not contain valid JSON")
                return self._fallback_analysis(document_text)
                
        except Exception as e:
            logger.error(f"Claude AI analysis error: {e}")
            return self._fallback_analysis(document_text)
    
    def perform_valuation_analysis(self, financial_data: Dict[str, Any], industry_context: str = None) -> Dict[str, Any]:
        """
        Bond AIが企業価値算定を実行
        
        Args:
            financial_data: 財務データ
            industry_context: 業界情報（オプション）
            
        Returns:
            企業価値算定結果
        """
        if not self.client:
            return self._fallback_valuation(financial_data)
        
        prompt = f"""
あなたは企業価値評価の専門家です。以下の財務データを基に、包括的な企業価値評価を実行してください。

# 財務データ
{json.dumps(financial_data, indent=2, ensure_ascii=False)}

# 業界情報
{industry_context or "一般的な業界として評価"}

# 評価要件
1. EV/売上倍率法による評価
2. EV/EBITDA倍率法による評価  
3. P/E倍率法による評価
4. 各手法の妥当性検証
5. 総合的な企業価値レンジの算出
6. リスクファクターの分析

# 使用する倍率（業界標準値）
- EV/売上: 1.5-3.5倍（中央値2.5倍）
- EV/EBITDA: 8-15倍（中央値12倍）
- P/E: 12-25倍（中央値18倍）

# 単位統一処理
- 全ての金額を「円」に統一して計算
- 株式数も「株」に統一

# 出力形式
```json
{{
    "valuation_date": "2024-08-19",
    "company_analysis": {{
        "strengths": ["強み1", "強み2"],
        "weaknesses": ["弱み1", "弱み2"],
        "risk_factors": ["リスク1", "リスク2"]
    }},
    "normalized_financials": {{
        "revenue_yen": 数値,
        "ebitda_yen": 数値,
        "net_income_yen": 数値,
        "net_debt_yen": 数値,
        "shares_outstanding": 数値
    }},
    "valuation_methods": {{
        "ev_sales": {{
            "enterprise_value": 数値,
            "equity_value": 数値,
            "price_per_share": 数値,
            "multiple_used": 数値,
            "validity": "高・中・低",
            "reasoning": "判断理由"
        }},
        "ev_ebitda": {{
            "enterprise_value": 数値,
            "equity_value": 数値, 
            "price_per_share": 数値,
            "multiple_used": 数値,
            "validity": "高・中・低",
            "reasoning": "判断理由"
        }},
        "pe_ratio": {{
            "equity_value": 数値,
            "price_per_share": 数値,
            "multiple_used": 数値,
            "validity": "高・中・低",
            "reasoning": "判断理由"
        }}
    }},
    "summary": {{
        "target_price": 数値,
        "price_range": {{
            "min": 数値,
            "max": 数値
        }},
        "weighted_average": 数値,
        "confidence_level": "高・中・低",
        "key_assumptions": ["前提1", "前提2"],
        "sensitivity_factors": ["感応度要因1", "感応度要因2"]
    }},
    "investment_recommendation": {{
        "recommendation": "買い・保有・売り",
        "rationale": "推奨理由",
        "price_targets": {{
            "bull_case": 数値,
            "base_case": 数値,
            "bear_case": 数値
        }}
    }}
}}
```

# 計算プロセス
1. 各財務データを円・株単位に正規化
2. 各評価手法で企業価値を算出
3. EV→株主価値→1株価値のブリッジを実行
4. 妥当性を検証し重み付け
5. 総合判断とレンジを決定

重要：全ての計算根拠を明確にし、実務で使える精度を確保してください。
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # JSONを抽出
            content = response.content[0].text
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group(1))
                result['ai_analysis'] = content  # 完全な分析も保存
                return result
            else:
                logger.warning("Claude AI valuation response does not contain valid JSON")
                return self._fallback_valuation(financial_data)
                
        except Exception as e:
            logger.error(f"Claude AI valuation error: {e}")
            return self._fallback_valuation(financial_data)
    
    def generate_natural_response(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """
        Bond AIが自然言語で応答を生成
        
        Args:
            user_message: ユーザーメッセージ
            context: 会話コンテキスト（財務データ、評価結果等）
            
        Returns:
            自然言語レスポンス
        """
        if not self.client:
            return self._generate_fallback_response(user_message, context)
        
        context_str = ""
        if context:
            context_str = f"\n\n# 利用可能なデータ\n{json.dumps(context, indent=2, ensure_ascii=False)}"
        
        prompt = f"""
あなたは経験豊富な金融アナリストとして、ユーザーとの対話を行います。
専門的でありながら分かりやすく、実務に役立つ回答を心がけてください。

# ユーザーメッセージ
{user_message}
{context_str}

# 応答ガイドライン
1. 専門用語は適切に説明
2. 数値は具体的に提示（フォーマット: ¥1,234,567）
3. 根拠を明確にする
4. リスクや前提条件も言及
5. 次のアクション提案も含める
6. フレンドリーで親しみやすいトーン

# 対応できる内容
- 決算書の解析依頼
- 企業価値評価の実行
- 財務指標の説明
- 投資判断のアドバイス
- 業界比較分析

具体的で実用的な回答をお願いします。
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Claude AI response generation error: {e}")
            return self._generate_fallback_response(user_message, context)
    
    def _fallback_analysis(self, document_text: str) -> Dict[str, Any]:
        """Claude AI利用不可時のフォールバック財務分析"""
        # 簡易パターンマッチング
        patterns = {
            'revenue': [r'売上高[^\d]*(\d+(?:,\d{3})*)', r'営業収益[^\d]*(\d+(?:,\d{3})*)'],
            'net_income': [r'当期純利益[^\d]*(\d+(?:,\d{3})*)', r'純利益[^\d]*(\d+(?:,\d{3})*)'],
            'total_debt': [r'借入金[^\d]*(\d+(?:,\d{3})*)', r'負債[^\d]*(\d+(?:,\d{3})*)'],
        }
        
        extracted_data = {}
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, document_text)
                if match:
                    try:
                        value = float(match.group(1).replace(',', ''))
                        extracted_data[key] = {"value": value, "unit": "百万円", "source": "パターンマッチング"}
                        break
                    except ValueError:
                        continue
        
        return {
            "company_name": "不明",
            "confidence_level": "低",
            "analysis_notes": ["Claude AI利用不可のためフォールバック処理を実行"],
            **extracted_data
        }
    
    def _fallback_valuation(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Claude AI利用不可時のフォールバック企業価値算定"""
        # 基本的な倍率による簡易評価
        revenue = financial_data.get('revenue', {}).get('value', 0)
        
        return {
            "valuation_date": datetime.now().strftime("%Y-%m-%d"),
            "summary": {
                "target_price": revenue * 2.5 / 1000 if revenue > 0 else 0,  # 簡易計算
                "confidence_level": "低",
                "key_assumptions": ["Claude AI利用不可のため簡易計算"]
            },
            "ai_analysis": "Claude AI機能が利用できないため、基本的な評価のみ実行しました。"
        }
    
    def _generate_fallback_response(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """Claude AI利用不可時のフォールバック応答"""
        if "企業価値評価" in user_message or "評価" in user_message:
            return """
申し訳ございませんが、現在Claude AI機能が利用できません。
基本的な企業価値評価機能のみ提供しています。

ANTHROPIC_API_KEYを設定することで、以下の高度な機能が利用可能になります：
- AI による決算書自動解析
- 専門的な企業価値算定
- 詳細な投資レポート生成
- 自然言語での質疑応答

TypeScript版の算定エンジンは引き続き利用可能です。
"""
        else:
            return f"「{user_message}」について、Claude AI機能が利用できないため詳細な回答ができません。ANTHROPIC_API_KEYを設定してください。"
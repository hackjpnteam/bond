"""
MongoDB Atlas データベース統合
分析結果の保存・取得・削除機能
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

class AnalysisDatabase:
    def __init__(self):
        """MongoDB Atlas接続初期化"""
        # MongoDB Atlas 接続URI (環境変数から取得)
        self.connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.database_name = "bond_analytics"
        self.collection_name = "analysis_results"
        
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # 接続テスト
            self.client.admin.command('ping')
            logger.info("MongoDB Atlas接続成功")
            
        except Exception as e:
            logger.error(f"MongoDB接続エラー: {e}")
            self.client = None
    
    def save_analysis_result(self, 
                           title: str,
                           company_name: str,
                           financial_data: Dict[str, Any],
                           valuation_result: Dict[str, Any],
                           user_id: str = "default") -> Optional[str]:
        """
        分析結果をMongoDBに保存
        
        Args:
            title: 分析タイトル（ユーザー指定 or 自動生成）
            company_name: 企業名
            financial_data: 財務データ
            valuation_result: 評価結果
            user_id: ユーザーID
            
        Returns:
            保存されたドキュメントのID
        """
        if not self.client:
            logger.error("MongoDB接続が無効です")
            return None
            
        logger.info(f"保存開始 - タイトル: {title}, 企業名: {company_name}")
        try:
            # 自動タイトル生成（タイトルが空の場合）
            if not title.strip():
                title = f"{company_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            # 保存用ドキュメント構造
            document = {
                "title": title,
                "company_name": company_name,
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "summary": {
                    "target_price": valuation_result.get('summary', {}).get('target_price', 0),
                    "confidence_level": valuation_result.get('summary', {}).get('confidence_level', '中'),
                    "price_range": valuation_result.get('summary', {}).get('price_range', {}),
                    "recommendation": valuation_result.get('investment_recommendation', {}).get('recommendation', '保有')
                },
                "financial_data": {
                    "revenue": financial_data.get('revenue', {}),
                    "ebitda": financial_data.get('ebitda', {}),
                    "net_income": financial_data.get('net_income', {}),
                    "total_debt": financial_data.get('total_debt', {}),
                    "cash": financial_data.get('cash', {}),
                    "shares_outstanding": financial_data.get('shares_outstanding', {}),
                    "fiscal_period": financial_data.get('fiscal_period', ''),
                    "analysis_notes": financial_data.get('analysis_notes', [])
                },
                "valuation_methods": valuation_result.get('valuation_methods', {}),
                "investment_recommendation": valuation_result.get('investment_recommendation', {}),
                "company_analysis": valuation_result.get('company_analysis', {}),
                "metadata": {
                    "analysis_type": "full_valuation",
                    "ai_model": "claude-3-5-sonnet",
                    "version": "1.0"
                }
            }
            
            # MongoDB に保存
            result = self.collection.insert_one(document)
            logger.info(f"分析結果保存成功: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"分析結果保存エラー: {e}")
            return None
    
    def get_analysis_results(self, user_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        """
        保存された分析結果を取得（最新順）
        
        Args:
            user_id: ユーザーID
            limit: 取得件数制限
            
        Returns:
            分析結果リスト
        """
        if not self.client:
            return []
            
        try:
            cursor = self.collection.find(
                {"user_id": user_id},
                {
                    "_id": 1,
                    "title": 1,
                    "company_name": 1,
                    "created_at": 1,
                    "summary": 1
                }
            ).sort("created_at", -1).limit(limit)
            
            results = []
            for doc in cursor:
                results.append({
                    "id": str(doc["_id"]),
                    "title": doc.get("title", ""),
                    "company_name": doc.get("company_name", ""),
                    "created_at": doc.get("created_at"),
                    "summary": doc.get("summary", {})
                })
            
            logger.info(f"分析結果取得成功: {len(results)}件")
            return results
            
        except Exception as e:
            logger.error(f"分析結果取得エラー: {e}")
            return []
    
    def get_analysis_by_id(self, analysis_id: str, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """
        IDで特定の分析結果を取得
        
        Args:
            analysis_id: 分析結果ID
            user_id: ユーザーID
            
        Returns:
            分析結果詳細
        """
        if not self.client:
            return None
            
        try:
            from bson import ObjectId
            result = self.collection.find_one({
                "_id": ObjectId(analysis_id),
                "user_id": user_id
            })
            
            if result:
                result["_id"] = str(result["_id"])
                logger.info(f"分析詳細取得成功: {analysis_id}")
                return result
            else:
                logger.warning(f"分析結果が見つかりません: {analysis_id}")
                return None
                
        except Exception as e:
            logger.error(f"分析詳細取得エラー: {e}")
            return None
    
    def delete_analysis(self, analysis_id: str, user_id: str = "default") -> bool:
        """
        指定した分析結果を削除
        
        Args:
            analysis_id: 分析結果ID
            user_id: ユーザーID
            
        Returns:
            削除成功フラグ
        """
        if not self.client:
            return False
            
        try:
            from bson import ObjectId
            result = self.collection.delete_one({
                "_id": ObjectId(analysis_id),
                "user_id": user_id
            })
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"分析結果削除成功: {analysis_id}")
            else:
                logger.warning(f"削除対象が見つかりません: {analysis_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"分析結果削除エラー: {e}")
            return False
    
    def delete_all_analyses(self, user_id: str = "default") -> int:
        """
        ユーザーの全分析結果を削除
        
        Args:
            user_id: ユーザーID
            
        Returns:
            削除件数
        """
        if not self.client:
            return 0
            
        try:
            result = self.collection.delete_many({"user_id": user_id})
            deleted_count = result.deleted_count
            logger.info(f"全分析結果削除完了: {deleted_count}件")
            return deleted_count
            
        except Exception as e:
            logger.error(f"全分析結果削除エラー: {e}")
            return 0
    
    def close_connection(self):
        """MongoDB接続を閉じる"""
        if self.client:
            self.client.close()
            logger.info("MongoDB接続を閉じました")
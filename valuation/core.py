from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np


class Valuator:
    def __init__(self):
        pass
    
    def _convert_units(self, value: float, unit: str) -> float:
        """単位換算（百万円・千株 → 円・株）"""
        if unit == "百万円" or unit == "million_yen":
            return value * 1_000_000
        elif unit == "千株" or unit == "thousand_shares":
            return value * 1_000
        else:
            return value
    
    def validate_inputs(self, pl: Dict[str, Any], bs: Dict[str, Any], comps: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
        """
        入力データの不整合を検出し、エラーメッセージと修正提案を返す
        
        Args:
            pl: 損益計算書データ
            bs: 貸借対照表データ  
            comps: 比較企業データ
            
        Returns:
            (is_valid, errors, suggestions)
        """
        errors = []
        suggestions = []
        
        # 必須項目チェック
        required_pl_fields = ['revenue', 'ebitda', 'net_income']
        for field in required_pl_fields:
            if field not in pl or pl[field] is None:
                errors.append(f"損益計算書に{field}が不足しています")
                suggestions.append(f"{field}の値を入力してください")
        
        required_bs_fields = ['total_debt', 'cash', 'shares_outstanding']
        for field in required_bs_fields:
            if field not in bs or bs[field] is None:
                errors.append(f"貸借対照表に{field}が不足しています")
                suggestions.append(f"{field}の値を入力してください")
        
        # 数値妥当性チェック
        if 'revenue' in pl and pl['revenue'] is not None:
            if pl['revenue'] <= 0:
                errors.append("売上高が0以下です")
                suggestions.append("売上高は正の値を入力してください")
        
        if 'shares_outstanding' in bs and bs['shares_outstanding'] is not None:
            if bs['shares_outstanding'] <= 0:
                errors.append("発行済み株式数が0以下です")
                suggestions.append("発行済み株式数は正の値を入力してください")
        
        # EBITDA vs 純利益の整合性
        if ('ebitda' in pl and 'net_income' in pl and 
            pl['ebitda'] is not None and pl['net_income'] is not None):
            if pl['net_income'] > pl['ebitda']:
                errors.append("純利益がEBITDAを上回っています")
                suggestions.append("EBITDAは純利益以上の値であることを確認してください")
        
        # 比較企業データチェック
        if comps is not None and not comps.empty:
            required_comp_cols = ['ev_revenue', 'ev_ebitda', 'pe_ratio']
            for col in required_comp_cols:
                if col not in comps.columns:
                    errors.append(f"比較企業データに{col}が不足しています")
                    suggestions.append(f"比較企業データに{col}列を追加してください")
        else:
            errors.append("比較企業データが空です")
            suggestions.append("比較企業データを入力してください")
        
        is_valid = len(errors) == 0
        return is_valid, errors, suggestions
    
    def compute_valuation(self, pl: Dict[str, Any], bs: Dict[str, Any], comps: pd.DataFrame) -> Dict[str, Any]:
        """
        企業価値評価を実行
        
        Args:
            pl: 損益計算書データ
            bs: 貸借対照表データ
            comps: 比較企業データ
            
        Returns:
            評価結果の辞書
        """
        # 入力検証
        is_valid, errors, suggestions = self.validate_inputs(pl, bs, comps)
        if not is_valid:
            return {
                'success': False,
                'errors': errors,
                'suggestions': suggestions
            }
        
        # 単位換算
        revenue = self._convert_units(pl['revenue'], pl.get('revenue_unit', '円'))
        ebitda = self._convert_units(pl['ebitda'], pl.get('ebitda_unit', '円'))
        net_income = self._convert_units(pl['net_income'], pl.get('net_income_unit', '円'))
        
        total_debt = self._convert_units(bs['total_debt'], bs.get('debt_unit', '円'))
        cash = self._convert_units(bs['cash'], bs.get('cash_unit', '円'))
        shares_outstanding = self._convert_units(bs['shares_outstanding'], bs.get('shares_unit', '株'))
        
        # 比較企業の倍率計算
        ev_revenue_multiples = comps['ev_revenue'].dropna()
        ev_ebitda_multiples = comps['ev_ebitda'].dropna()
        pe_multiples = comps['pe_ratio'].dropna()
        
        results = {
            'success': True,
            'multiples': {},
            'enterprise_values': {},
            'equity_values': {},
            'share_prices': {},
            'summary': {}
        }
        
        # EV/売上による評価
        if not ev_revenue_multiples.empty and revenue > 0:
            ev_rev_median = ev_revenue_multiples.median()
            ev_from_revenue = revenue * ev_rev_median
            equity_from_revenue = ev_from_revenue - total_debt + cash
            share_price_from_revenue = equity_from_revenue / shares_outstanding
            
            results['multiples']['ev_revenue'] = {
                'median_multiple': ev_rev_median,
                'range': f"{ev_revenue_multiples.min():.1f}x - {ev_revenue_multiples.max():.1f}x"
            }
            results['enterprise_values']['from_revenue'] = ev_from_revenue
            results['equity_values']['from_revenue'] = equity_from_revenue
            results['share_prices']['from_revenue'] = share_price_from_revenue
        
        # EV/EBITDAによる評価
        if not ev_ebitda_multiples.empty and ebitda > 0:
            ev_ebitda_median = ev_ebitda_multiples.median()
            ev_from_ebitda = ebitda * ev_ebitda_median
            equity_from_ebitda = ev_from_ebitda - total_debt + cash
            share_price_from_ebitda = equity_from_ebitda / shares_outstanding
            
            results['multiples']['ev_ebitda'] = {
                'median_multiple': ev_ebitda_median,
                'range': f"{ev_ebitda_multiples.min():.1f}x - {ev_ebitda_multiples.max():.1f}x"
            }
            results['enterprise_values']['from_ebitda'] = ev_from_ebitda
            results['equity_values']['from_ebitda'] = equity_from_ebitda
            results['share_prices']['from_ebitda'] = share_price_from_ebitda
        
        # P/Eによる評価
        if not pe_multiples.empty and net_income > 0:
            pe_median = pe_multiples.median()
            equity_from_pe = net_income * pe_median
            share_price_from_pe = equity_from_pe / shares_outstanding
            
            results['multiples']['pe_ratio'] = {
                'median_multiple': pe_median,
                'range': f"{pe_multiples.min():.1f}x - {pe_multiples.max():.1f}x"
            }
            results['equity_values']['from_pe'] = equity_from_pe
            results['share_prices']['from_pe'] = share_price_from_pe
        
        # サマリー計算
        share_prices = [v for v in results['share_prices'].values()]
        if share_prices:
            results['summary'] = {
                'average_share_price': np.mean(share_prices),
                'median_share_price': np.median(share_prices),
                'min_share_price': min(share_prices),
                'max_share_price': max(share_prices),
                'valuation_range': f"¥{min(share_prices):,.0f} - ¥{max(share_prices):,.0f}",
                'net_debt': total_debt - cash,
                'shares_outstanding': shares_outstanding
            }
        
        return results
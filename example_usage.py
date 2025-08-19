import pandas as pd
from valuation import Valuator

# 使用例
def example_valuation():
    valuator = Valuator()
    
    # サンプルデータ
    pl_data = {
        'revenue': 1000,  # 1000百万円
        'revenue_unit': '百万円',
        'ebitda': 200,    # 200百万円
        'ebitda_unit': '百万円', 
        'net_income': 100, # 100百万円
        'net_income_unit': '百万円'
    }
    
    bs_data = {
        'total_debt': 300,    # 300百万円
        'debt_unit': '百万円',
        'cash': 50,          # 50百万円
        'cash_unit': '百万円',
        'shares_outstanding': 10,  # 10千株
        'shares_unit': '千株'
    }
    
    # 比較企業データ
    comps_data = pd.DataFrame({
        'company': ['A社', 'B社', 'C社'],
        'ev_revenue': [2.5, 3.0, 2.8],
        'ev_ebitda': [12.0, 15.0, 13.5],
        'pe_ratio': [18.0, 22.0, 20.0]
    })
    
    # バリュエーション実行
    result = valuator.compute_valuation(pl_data, bs_data, comps_data)
    
    if result['success']:
        print("=== バリュエーション結果 ===")
        print(f"平均株価: ¥{result['summary']['average_share_price']:,.0f}")
        print(f"中央値株価: ¥{result['summary']['median_share_price']:,.0f}")
        print(f"評価レンジ: {result['summary']['valuation_range']}")
        
        print("\n=== 手法別結果 ===")
        if 'from_revenue' in result['share_prices']:
            print(f"EV/売上倍率による株価: ¥{result['share_prices']['from_revenue']:,.0f}")
        if 'from_ebitda' in result['share_prices']:
            print(f"EV/EBITDA倍率による株価: ¥{result['share_prices']['from_ebitda']:,.0f}")
        if 'from_pe' in result['share_prices']:
            print(f"P/E倍率による株価: ¥{result['share_prices']['from_pe']:,.0f}")
            
    else:
        print("=== エラー ===")
        for error in result['errors']:
            print(f"- {error}")
        print("\n=== 修正提案 ===")
        for suggestion in result['suggestions']:
            print(f"- {suggestion}")

if __name__ == "__main__":
    example_valuation()
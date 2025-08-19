import streamlit as st
import pandas as pd
from valuation import Valuator

st.title("企業価値評価ツール")

# サイドバーで入力
st.sidebar.header("財務データ入力")

# 損益計算書
st.sidebar.subheader("損益計算書")
revenue = st.sidebar.number_input("売上高 (百万円)", value=1000.0, min_value=0.0)
ebitda = st.sidebar.number_input("EBITDA (百万円)", value=200.0, min_value=0.0)
net_income = st.sidebar.number_input("純利益 (百万円)", value=100.0)

# 貸借対照表
st.sidebar.subheader("貸借対照表")
total_debt = st.sidebar.number_input("総負債 (百万円)", value=300.0, min_value=0.0)
cash = st.sidebar.number_input("現金 (百万円)", value=50.0, min_value=0.0)
shares = st.sidebar.number_input("発行済株式数 (千株)", value=10.0, min_value=0.1)

# 比較企業倍率
st.sidebar.subheader("比較企業倍率")
ev_rev = st.sidebar.number_input("EV/売上倍率", value=2.8, min_value=0.1)
ev_ebitda = st.sidebar.number_input("EV/EBITDA倍率", value=13.5, min_value=0.1)
pe_ratio = st.sidebar.number_input("P/E倍率", value=20.0, min_value=0.1)

if st.button("評価実行"):
    # データ準備
    pl_data = {
        'revenue': revenue,
        'revenue_unit': '百万円',
        'ebitda': ebitda,
        'ebitda_unit': '百万円',
        'net_income': net_income,
        'net_income_unit': '百万円'
    }
    
    bs_data = {
        'total_debt': total_debt,
        'debt_unit': '百万円',
        'cash': cash,
        'cash_unit': '百万円',
        'shares_outstanding': shares,
        'shares_unit': '千株'
    }
    
    comps_data = pd.DataFrame({
        'company': ['比較企業'],
        'ev_revenue': [ev_rev],
        'ev_ebitda': [ev_ebitda],
        'pe_ratio': [pe_ratio]
    })
    
    # 評価実行
    valuator = Valuator()
    result = valuator.compute_valuation(pl_data, bs_data, comps_data)
    
    if result['success']:
        st.success("評価完了！")
        
        # 結果表示
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("平均株価", f"¥{result['summary']['average_share_price']:,.0f}")
        with col2:
            st.metric("中央値株価", f"¥{result['summary']['median_share_price']:,.0f}")
        with col3:
            st.metric("評価レンジ", result['summary']['valuation_range'])
        
        st.subheader("手法別評価結果")
        
        methods_data = []
        if 'from_revenue' in result['share_prices']:
            methods_data.append({
                '評価手法': 'EV/売上倍率',
                '株価': f"¥{result['share_prices']['from_revenue']:,.0f}",
                '倍率': f"{result['multiples']['ev_revenue']['median_multiple']:.1f}x"
            })
        
        if 'from_ebitda' in result['share_prices']:
            methods_data.append({
                '評価手法': 'EV/EBITDA倍率',
                '株価': f"¥{result['share_prices']['from_ebitda']:,.0f}",
                '倍率': f"{result['multiples']['ev_ebitda']['median_multiple']:.1f}x"
            })
        
        if 'from_pe' in result['share_prices']:
            methods_data.append({
                '評価手法': 'P/E倍率',
                '株価': f"¥{result['share_prices']['from_pe']:,.0f}",
                '倍率': f"{result['multiples']['pe_ratio']['median_multiple']:.1f}x"
            })
        
        st.table(pd.DataFrame(methods_data))
        
    else:
        st.error("エラーが発生しました")
        for error in result['errors']:
            st.error(f"• {error}")
        
        st.subheader("修正提案")
        for suggestion in result['suggestions']:
            st.info(f"• {suggestion}")
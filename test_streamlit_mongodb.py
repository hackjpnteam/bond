import streamlit as st
from pymongo import MongoClient

st.title("🔍 MongoDB接続テスト")

st.write("### 設定確認")
if "MONGODB_URI" in st.secrets:
    st.success("✅ MONGODB_URI がsecrets.tomlに設定されています")
    uri_preview = st.secrets["MONGODB_URI"][:50] + "..."
    st.info(f"URI プレビュー: {uri_preview}")
else:
    st.error("❌ MONGODB_URI がsecrets.tomlに設定されていません")

if "ANTHROPIC_API_KEY" in st.secrets:
    st.success("✅ ANTHROPIC_API_KEY がsecrets.tomlに設定されています")
    key_preview = st.secrets["ANTHROPIC_API_KEY"][:20] + "..."
    st.info(f"API Key プレビュー: {key_preview}")
else:
    st.warning("⚠️ ANTHROPIC_API_KEY がsecrets.tomlに設定されていません")

st.write("### MongoDB接続テスト")

try:
    client = MongoClient(st.secrets["MONGODB_URI"], serverSelectionTimeoutMS=10000)
    
    # 接続テスト
    client.admin.command('ping')
    st.success("✅ MongoDB接続成功！")
    
    # データベース一覧
    databases = client.list_database_names()
    st.write("**利用可能なDB:**", databases)
    
    # bond_analytics データベースの詳細
    if "bond_analytics" in databases:
        db = client["bond_analytics"]
        collections = db.list_collection_names()
        st.write("**bond_analytics コレクション:**", collections)
        
        if "analysis_results" in collections:
            collection = db["analysis_results"]
            count = collection.count_documents({})
            st.write(f"**保存された分析結果数:** {count}件")
            
            # 最新3件のタイトルを表示
            if count > 0:
                recent_results = collection.find({}, {"title": 1, "company_name": 1, "created_at": 1}).sort("created_at", -1).limit(3)
                st.write("**最新の分析結果:**")
                for i, result in enumerate(recent_results, 1):
                    st.write(f"  {i}. {result.get('title', 'N/A')} - {result.get('company_name', 'N/A')}")
    
    client.close()
    
except Exception as e:
    st.error(f"❌ MongoDB接続失敗: {e}")
    st.write("**エラー詳細:**")
    import traceback
    st.code(traceback.format_exc())

st.write("---")
st.write("💡 **次のステップ:**")
st.write("1. MongoDB接続が成功していれば、メインアプリでも保存機能が動作します")
st.write("2. 接続が失敗している場合は、Streamlit Cloud の Secrets 設定を確認してください")
st.write("3. メインアプリ: https://bond20250819.streamlit.app/")
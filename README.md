# 🐰 Bond AI - 企業価値算定システム

Bond AIは、Claude AIを活用した企業価値算定システムです。決算書をアップロードするだけで、自動的に財務データを抽出し、複数の手法で企業価値を算定します。

![Bond AI](https://img.shields.io/badge/AI-Powered-yellow) ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white) ![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=white)

## ✨ 主な機能

- 🎯 **決算書AI解析**: PDF/Excel形式の決算書から自動データ抽出
- 💰 **企業価値算定**: EV/売上、EV/EBITDA、P/E手法による多面的評価
- 📊 **分析結果保存**: MongoDB Atlasへの自動保存機能
- 💬 **自然言語対話**: Bondとのチャットで簡単分析指示
- 📋 **PDFレポート生成**: 分析結果の詳細レポート出力
- 🎨 **マテリアルデザイン**: 黄色いうさぎキャラクターBondとの親しみやすいUI

## 🚀 デプロイ

### Streamlit Cloud
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bond-ai.streamlit.app)

### ローカル実行

1. **リポジトリのクローン**
```bash
git clone https://github.com/hackjpnteam/bond.git
cd bond
```

2. **依存関係のインストール**
```bash
pip install -r requirements.txt
```

3. **環境変数の設定**
```bash
# .envファイルを作成
ANTHROPIC_API_KEY=your-anthropic-api-key
MONGODB_URI=your-mongodb-connection-string
```

4. **アプリケーションの起動**
```bash
streamlit run ai_valuation_app.py
```

## 📋 必要な環境変数

- `ANTHROPIC_API_KEY`: Anthropic Claude APIキー
- `MONGODB_URI`: MongoDB Atlas接続文字列

## 🏗️ アーキテクチャ

```
├── ai_valuation_app.py      # メインStreamlitアプリ
├── claude_backend.py        # Claude AI統合バックエンド
├── database.py              # MongoDB Atlas統合
├── pdf_generator.py         # PDFレポート生成
├── requirements.txt         # Python依存関係
└── .env.example            # 環境変数テンプレート
```

## 🎯 使用方法

1. **ファイルアップロード**: PDF/Excel形式の決算書をアップロード
2. **分析選択**: 財務データ抽出、企業価値算定、詳細分析から選択
3. **結果確認**: 自動生成された分析結果とレポートを確認
4. **履歴管理**: 過去の分析結果をサイドバーで管理

## 🛠️ 技術スタック

- **Frontend**: Streamlit + カスタムCSS
- **AI**: Anthropic Claude 3.5 Sonnet
- **Database**: MongoDB Atlas
- **Reports**: ReportLab (PDF生成)
- **UI**: マテリアルデザイン + カスタム3Dうさぎアイコン

## 📄 ライセンス

MIT License

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します！

---

**🐰 Bond AI - あなたの投資パートナー**
#!/bin/bash

# 記事ネタ提案ツール 起動スクリプト

echo "🚀 記事ネタ提案ツールを起動中..."

# 仮想環境のパス
VENV_PATH=".venv"

# 仮想環境をアクティベート
if [ -d "$VENV_PATH" ]; then
    echo "✅ 仮想環境を読み込み中..."
    source "$VENV_PATH/bin/activate"
else
    echo "❌ 仮想環境が見つかりません: $VENV_PATH"
    exit 1
fi

# Streamlitアプリを起動（ポート8502を明示的に指定）
echo "📖 アプリを起動します..."
echo "ポート: 8502"
echo "URL: http://localhost:8502"
echo "ブラウザが自動的に開きます"
echo "終了するには Ctrl+C を押してください"
echo ""

STREAMLIT_SERVER_HEADLESS=true python3 -m streamlit run app.py --server.port 8502

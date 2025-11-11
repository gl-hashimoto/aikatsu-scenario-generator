#!/bin/bash

# 漫画シナリオ生成AI 起動スクリプト

echo "🚀 漫画シナリオ生成AI を起動中..."

# 仮想環境のパス
VENV_PATH="../.venv"

# 仮想環境をアクティベート
if [ -d "$VENV_PATH" ]; then
    echo "✅ 仮想環境を読み込み中..."
    source "$VENV_PATH/bin/activate"
else
    echo "❌ 仮想環境が見つかりません: $VENV_PATH"
    exit 1
fi

# Streamlitアプリを起動
echo "📖 アプリを起動します..."
echo "ブラウザが自動的に開きます"
echo "終了するには Ctrl+C を押してください"
echo ""

streamlit run app.py

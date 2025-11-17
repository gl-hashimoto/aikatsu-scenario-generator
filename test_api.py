#!/usr/bin/env python3
"""APIキーのテストスクリプト"""
from dotenv import load_dotenv
import os
from anthropic import Anthropic

# 環境変数読み込み
load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')

print(f"API Key exists: {api_key is not None}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"API Key prefix: {api_key[:20] if api_key else 'None'}...")

# Anthropicクライアントを作成してテスト
try:
    client = Anthropic(api_key=api_key)
    print("\nClient created successfully")

    # 簡単なテストリクエスト
    print("Sending test request...")
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": "Hello, just testing!"}]
    )

    print(f"✅ Success! Response: {message.content[0].text[:50]}...")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

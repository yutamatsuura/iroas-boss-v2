#!/bin/bash
# API機能チェックスクリプト - 開発時に必ず実行

echo "🔍 API機能チェックを開始..."

# Pythonスクリプト実行
cd /Users/lennon/projects/iroas-boss-v2/backend
python3 check_api_health.py

# テスト実行
if [ $? -eq 0 ]; then
    echo ""
    echo "📋 統合テストも実行中..."
    python3 tests/test_member_api.py
fi

echo ""
echo "✨ チェック完了"
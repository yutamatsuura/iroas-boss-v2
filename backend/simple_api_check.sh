#!/bin/bash
# シンプルなAPI機能チェックスクリプト

echo "🏥 IROAS BOSS API ヘルスチェック"
echo "================================="
echo "実行時刻: $(date)"
echo ""

# サーバー起動チェック
echo "1. サーバー起動チェック"
if curl -s "http://localhost:8001/api/health" > /dev/null 2>&1; then
    echo "   ✅ サーバーは正常に起動しています"
else
    echo "   ❌ サーバーが起動していません"
    echo "   → サーバーを起動してください"
    exit 1
fi
echo ""

# 会員一覧APIチェック
echo "2. 会員一覧API"
RESPONSE=$(curl -s "http://localhost:8001/api/v1/members/" | head -100)
if echo "$RESPONSE" | grep -q '"data"' && echo "$RESPONSE" | grep -q '"total"'; then
    MEMBER_COUNT=$(echo "$RESPONSE" | grep -o '"total":[0-9]*' | cut -d: -f2)
    echo "   ✅ OK - 合計 $MEMBER_COUNT 名の会員データ"
else
    echo "   ❌ 会員一覧APIが正常に応答していません"
fi
echo ""

# 検索機能チェック
echo "3. 検索機能チェック"

# 会員番号検索
echo "   会員番号検索テスト (memberNumber=0000):"
SEARCH_RESPONSE=$(curl -s "http://localhost:8001/api/v1/members/?memberNumber=0000")
if echo "$SEARCH_RESPONSE" | grep -q '"data"' && echo "$SEARCH_RESPONSE" | grep -q '00000000000'; then
    echo "   ✅ 会員番号検索: 正常"
else
    echo "   ❌ 会員番号検索: 失敗"
fi

# 名前検索  
echo "   名前検索テスト (name=白石):"
NAME_RESPONSE=$(curl -s "http://localhost:8001/api/v1/members/?name=%E7%99%BD%E7%9F%B3")
if echo "$NAME_RESPONSE" | grep -q '"data"' && echo "$NAME_RESPONSE" | grep -q '白石'; then
    echo "   ✅ 名前検索: 正常"
else
    echo "   ❌ 名前検索: 失敗"
fi

# メール検索
echo "   メール検索テスト (email=gmail):"
EMAIL_RESPONSE=$(curl -s "http://localhost:8001/api/v1/members/?email=gmail")
if echo "$EMAIL_RESPONSE" | grep -q '"data"' && echo "$EMAIL_RESPONSE" | grep -q 'gmail'; then
    echo "   ✅ メール検索: 正常"
else
    echo "   ❌ メール検索: 失敗"
fi
echo ""

# 会員詳細取得チェック
echo "4. 会員詳細取得チェック"

# ID取得
echo "   ID指定取得テスト (ID: 2):"
ID_RESPONSE=$(curl -s "http://localhost:8001/api/v1/members/2")
if echo "$ID_RESPONSE" | grep -q '"id":2' && ! echo "$ID_RESPONSE" | grep -q '"error"'; then
    echo "   ✅ ID指定取得: 正常"
else
    echo "   ❌ ID指定取得: 失敗"
fi

# 会員番号取得（編集画面で重要）
echo "   会員番号指定取得テスト (会員番号: 00000000000):"
MEMBER_NUM_RESPONSE=$(curl -s "http://localhost:8001/api/v1/members/00000000000")
if echo "$MEMBER_NUM_RESPONSE" | grep -q '"member_number":"00000000000"' && ! echo "$MEMBER_NUM_RESPONSE" | grep -q '"error"'; then
    echo "   ✅ 会員番号指定取得: 正常（編集画面で使用）"
    
    # 編集画面必須フィールドのチェック
    if echo "$MEMBER_NUM_RESPONSE" | grep -q '"phone"' && echo "$MEMBER_NUM_RESPONSE" | grep -q '"gender"' && echo "$MEMBER_NUM_RESPONSE" | grep -q '"bank_name"'; then
        echo "   ✅ 編集画面用フィールド: 正常"
    else
        echo "   ❌ 編集画面用フィールド: 不足"
    fi
else
    echo "   ❌ 会員番号指定取得: 失敗"
fi

echo ""
echo "🎉 APIヘルスチェック完了"
echo ""
echo "💡 このスクリプトは開発中に定期的に実行してください"
echo "   ./simple_api_check.sh"
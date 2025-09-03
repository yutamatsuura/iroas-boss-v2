# Network Error トラブルシューティングメモ

## 🚨 発生した問題（2025/09/02）

### 症状
- フロントエンドから「Network Error」が発生
- 会員データが「No rows」と表示
- ブラウザコンソールで「XMLHttpRequest」エラー
- 「サーバに接続できませんでした」エラー

### 根本原因
**環境変数とAPIサーバーのポート番号不一致**

1. **APIサーバー**: `http://localhost:8001` で起動
2. **環境変数**: `.env.development`で `http://localhost:8000` を指定
3. **結果**: フロントエンドが存在しないポート8000に接続を試行

## 詳細な原因分析

### 設定不一致の詳細
```bash
# 実際のAPIサーバー起動コマンド
PYTHONPATH=backend python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

# 問題のあった環境変数設定
# frontend/.env.development
VITE_API_BASE_URL=http://localhost:8000/api/v1  # ❌ 間違ったポート

# 正しい設定
VITE_API_BASE_URL=http://localhost:8001/api     # ✅ 正しいポート
```

### なぜ気づきにくかったか
1. **curlテストでは成功**: 直接APIを叩いた場合は正常に動作
2. **CORS設定は正常**: サーバー側の設定に問題なし
3. **APIパス修正後の混乱**: パス修正作業中にポート設定を見落とし

## 修正手順

### 1. 環境変数修正
```bash
# frontend/.env.development
- VITE_API_BASE_URL=http://localhost:8000/api/v1
+ VITE_API_BASE_URL=http://localhost:8001/api
```

### 2. フロントエンド再起動
```bash
cd frontend
npm run dev
# Port 3000で起動確認
```

### 3. 動作確認
- ブラウザで http://localhost:3000 にアクセス
- 会員データ45件の表示を確認

## 再発防止策

### 1. 起動時のポート確認チェックリスト
```bash
# バックエンド確認
ps aux | grep uvicorn
curl http://localhost:8001/api/health

# フロントエンド確認
ps aux | grep vite
echo $VITE_API_BASE_URL

# 環境変数確認
cat frontend/.env.development | grep VITE_API_BASE_URL
```

### 2. 設定ファイルの統一管理
- **推奨**: 開発環境のポート番号を標準化
  - API: 8001
  - Frontend: 3000
- 設定変更時は必ず両方を確認

### 3. デバッグ手順の標準化
```bash
# 1. APIサーバー状態確認
curl http://localhost:8001/api/v1/members/ | head -n 5

# 2. フロントエンド環境変数確認  
grep VITE_API_BASE_URL frontend/.env.development

# 3. 不一致があれば修正後にフロントエンド再起動
cd frontend && npm run dev
```

### 4. 起動スクリプトの作成（今後の改善）
```bash
# scripts/start-dev.sh
#!/bin/bash
echo "=== 開発環境起動 ==="
echo "Backend: http://localhost:8001"
echo "Frontend: http://localhost:3000"

# バックエンド起動
PYTHONPATH=backend python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8001 &

# フロントエンド起動
cd frontend && npm run dev
```

## 学んだこと

### 技術的教訓
1. **環境変数とサーバー設定は必ずセットで確認**
2. **ポート番号の不一致は最も見落としやすいエラー**
3. **curlテストだけでは不十分、ブラウザからの接続も確認**

### デバッグ手法
1. **症状**: Network Error → **確認**: ポート番号の一致
2. **症状**: CORS Error → **確認**: オリジンの設定
3. **症状**: 404 Error → **確認**: APIパスの一致

## 現在の正常な構成

### サーバー構成
- **Backend**: http://localhost:8001 (FastAPI + SQLAlchemy)
- **Frontend**: http://localhost:3000 (React + Vite)
- **Database**: SQLite (`backend/iroas_boss_v2.db`)

### API エンドポイント
- **会員一覧**: `GET http://localhost:8001/api/v1/members/`
- **組織ツリー**: `GET http://localhost:8001/api/v1/organization/tree`
- **ヘルスチェック**: `GET http://localhost:8001/api/health`

### 環境変数（正常）
```
VITE_API_BASE_URL=http://localhost:8001/api
VITE_SKIP_AUTH=true
VITE_MOCK_USER=true
```

---
**作成日**: 2025/09/02  
**最終更新**: 2025/09/02  
**重要度**: 🔴 高（開発環境の基本設定）
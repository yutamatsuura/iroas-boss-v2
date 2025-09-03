# データベース設定に関する重要事項

## 🚨 発生した問題（2025/09/01）

### 症状
- データベースから会員データを削除したが、画面に反映されなかった
- 総会員数23件が表示され続けた

### 原因
**2つの異なるデータベースが存在していた：**
1. **PostgreSQL** (`iroas_boss_dev`) - 初期データ作成時に使用
2. **SQLite** (`iroas_boss_v2.db`) - APIサーバーが実際に使用

削除操作をPostgreSQLに対して実行したが、APIサーバーはSQLiteを参照していたため、画面に変更が反映されなかった。

## 現在の設定

### APIサーバー（backend/app/database.py）
```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./iroas_boss_v2.db")
# 環境変数が未設定の場合、デフォルトでSQLiteを使用
```

### データベースファイル
- **SQLite**: `backend/iroas_boss_v2.db` ← 現在使用中
- **PostgreSQL**: `iroas_boss_dev` データベース

## 正しいデータ操作方法

### SQLiteの場合（現在のデフォルト）
```bash
# データ確認
sqlite3 iroas_boss_v2.db "SELECT COUNT(*) FROM members;"

# データ削除
sqlite3 iroas_boss_v2.db "DELETE FROM members WHERE member_number <> '00000000400';"

# 全データ削除
sqlite3 iroas_boss_v2.db "DELETE FROM members;"
```

### PostgreSQLに切り替える場合
```bash
# 環境変数設定
export DATABASE_URL="postgresql://lennon:@localhost/iroas_boss_dev"

# APIサーバー再起動
source venv/bin/activate
python main.py

# データ操作
psql -U lennon -d iroas_boss_dev -c "SELECT COUNT(*) FROM members;"
```

## チェックリスト

### データ操作前の確認
- [ ] 現在のデータベース設定を確認
- [ ] APIサーバーが参照しているデータベースを特定
- [ ] データ操作対象が正しいか確認

### 確認コマンド
```bash
# SQLiteの確認
ls -la *.db
sqlite3 iroas_boss_v2.db ".tables"

# PostgreSQLの確認
psql -U lennon -l | grep iroas

# API経由での確認
curl http://localhost:8000/api/v1/members/ | python -m json.tool | grep total_count
```

## 推奨事項

1. **開発環境では統一したデータベースを使用**
   - SQLiteは手軽だが、本番環境と差異が生じる可能性
   - PostgreSQL推奨（本番環境と同じ）

2. **環境変数の明示的設定**
   ```bash
   # .envファイルを作成
   echo "DATABASE_URL=postgresql://lennon:@localhost/iroas_boss_dev" > .env
   ```

3. **起動時のログ確認**
   - APIサーバー起動時にデータベース接続先をログ出力
   - データベース種別（SQLite/PostgreSQL）を明示

## トラブルシューティング

### 画面のデータが更新されない場合
1. ブラウザキャッシュをクリア（Cmd+Shift+R）
2. APIレスポンスを直接確認
3. 正しいデータベースを操作しているか確認
4. APIサーバーの再起動

### データベースが不明な場合
```python
# 確認スクリプト
python -c "
from app.database import DATABASE_URL
print(f'使用中のデータベース: {DATABASE_URL}')
"
```

---
**最終更新**: 2025/09/01
**作成者**: IROAS BOSS V2 開発チーム
# IROAS BOSS V2 - デプロイ実行ガイド

## 🚀 実行概要
Step 19完了状態の完全デプロイ設定一覧  
要件定義書100%準拠・MLMビジネス要件簡略化一切なし

## 📋 デプロイ前チェックリスト

### ✅ 必須確認事項
- [ ] 要件定義書の再確認完了
- [ ] MLMビジネスルール（29項目会員データ、7種ボーナス、50名上限）理解
- [ ] 固定料金（ヒーロープラン10,670円、テストプラン9,800円）確認
- [ ] Univapay・GMOネットバンク連携要件確認
- [ ] Shift-JIS CSV要件確認
- [ ] エンタープライズテーマ（ネイビーブルー#1e3a8a）確認

### 🔧 技術準備
- [ ] GCPプロジェクト作成・設定完了
- [ ] Vercelアカウント・設定完了
- [ ] PostgreSQL環境準備完了
- [ ] Docker環境構築完了
- [ ] Secret Manager設定完了

## 🌐 環境別デプロイ手順

### 1. 開発環境デプロイ
```bash
# 1. GCP Cloud Runデプロイ（開発環境）
gcloud builds submit --config deployment/gcp/cloudbuild.yaml \
  --substitutions BRANCH_NAME=develop

# 2. Vercel環境変数設定（開発環境）
vercel env add --environment=development < deployment/vercel/development.env

# 3. Vercelデプロイ（開発環境）
vercel --prod --token=$VERCEL_TOKEN
```

### 2. ステージング環境デプロイ
```bash
# 1. データベース初期化（ステージング）
psql -h $STAGING_DB_HOST -U postgres -f deployment/database/init.sql

# 2. GCP Cloud Runデプロイ（ステージング）
gcloud builds submit --config deployment/gcp/cloudbuild.yaml \
  --substitutions BRANCH_NAME=develop

# 3. Vercel環境変数設定（ステージング）
vercel env add --environment=staging < deployment/vercel/staging.env

# 4. Vercelデプロイ（ステージング）
vercel --prod --token=$VERCEL_TOKEN
```

### 3. 本番環境デプロイ
```bash
# 1. データベース初期化（本番）
psql -h $PRODUCTION_DB_HOST -U postgres -f deployment/database/init.sql

# 2. GCP Cloud Runデプロイ（本番）
gcloud builds submit --config deployment/gcp/cloudbuild.yaml \
  --substitutions BRANCH_NAME=main

# 3. Vercel環境変数設定（本番）
vercel env add --environment=production < deployment/vercel/production.env

# 4. Vercelデプロイ（本番）
vercel --prod --token=$VERCEL_TOKEN

# 5. DNS設定・独自ドメイン設定
vercel domains add iroas-boss-v2.com
```

## 🔐 Secret Manager設定

### 必須シークレット設定
```bash
# データベース接続文字列
gcloud secrets create database-url-production --data-file=-
gcloud secrets create database-url-staging --data-file=-
gcloud secrets create database-url-development --data-file=-

# Redis接続文字列
gcloud secrets create redis-url-production --data-file=-
gcloud secrets create redis-url-staging --data-file=-

# APIキー
gcloud secrets create secret-key-production --data-file=-
gcloud secrets create univapay-api-key-production --data-file=-
gcloud secrets create gmo-bank-api-key-production --data-file=-

# CSV暗号化キー
gcloud secrets create csv-encryption-key-production --data-file=-
```

## 📊 デプロイ後検証

### 1. ヘルスチェック
```bash
# バックエンドヘルスチェック
curl https://iroas-boss-v2-backend.run.app/health

# フロントエンドアクセス確認
curl https://iroas-boss-v2.vercel.app
```

### 2. MLM機能検証
- [ ] 会員管理画面表示確認
- [ ] 29項目会員データ表示確認
- [ ] 組織図ビューア動作確認
- [ ] 決済管理（4種決済方法）表示確認
- [ ] 報酬計算（7種ボーナス）表示確認
- [ ] GMO CSV出力機能確認
- [ ] Shift-JIS エンコーディング確認

### 3. パフォーマンス検証
```bash
# ロードテスト
ab -n 100 -c 10 https://iroas-boss-v2-backend.run.app/api/v1/members

# レスポンス時間確認
curl -w "@curl-format.txt" -o /dev/null -s https://iroas-boss-v2.vercel.app
```

## 🔄 継続運用設定

### 1. 自動バックアップ設定
```bash
# crontab設定（日次バックアップ）
0 2 * * * /path/to/deployment/database/backup-scripts/daily_backup.sh
```

### 2. 監視設定
```bash
# Cloud Monitoring設定
gcloud alpha monitoring policies create --policy-from-file=deployment/monitoring/alerts.yaml
```

### 3. ログ監視設定
```bash
# Cloud Logging設定
gcloud logging sinks create iroas-boss-v2-logs \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/iroas_logs
```

## 📈 スケーリング設定

### Auto Scaling設定（Cloud Run）
```yaml
# 本番環境
min_instances: 1
max_instances: 10
cpu_utilization_target: 70

# ステージング環境  
min_instances: 0
max_instances: 5
cpu_utilization_target: 70

# 開発環境
min_instances: 0
max_instances: 2
cpu_utilization_target: 80
```

## 🚨 トラブルシューティング

### 1. デプロイ失敗時
```bash
# Cloud Buildログ確認
gcloud builds log $BUILD_ID

# Cloud Runログ確認
gcloud logs read "resource.type=cloud_run_revision"
```

### 2. データベース接続エラー
```bash
# 接続テスト
pg_isready -h $DB_HOST -p 5432

# PostgreSQL接続確認
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT version();"
```

### 3. Vercelデプロイエラー
```bash
# Vercelログ確認
vercel logs

# ビルドログ確認
vercel inspect
```

## 🔄 ロールバック手順

### 1. バックエンドロールバック
```bash
# 前のリビジョンに戻す
gcloud run services update-traffic iroas-boss-v2-backend \
  --to-revisions=PREVIOUS_REVISION=100
```

### 2. フロントエンドロールバック
```bash
# Vercelロールバック
vercel rollback
```

### 3. データベースロールバック
```bash
# バックアップからリストア
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < backup_file.sql
```

## ✅ デプロイ完了チェック

### 最終確認項目
- [ ] 全環境のヘルスチェック合格
- [ ] MLM業務機能正常動作確認
- [ ] 29項目会員データ完全表示確認
- [ ] 7種ボーナス計算機能確認
- [ ] Univapay・GMO連携確認
- [ ] Shift-JIS CSV出力確認
- [ ] エンタープライズテーマ表示確認
- [ ] 自動バックアップ動作確認
- [ ] 監視アラート設定確認

## 🎯 Step 19 完了基準

1. **3環境構築完了**: 本番・ステージング・開発環境全て稼働
2. **要件定義書100%準拠**: MLMビジネス要件完全実装
3. **技術仕様準拠**: React18+FastAPI+PostgreSQL構成
4. **セキュリティ確保**: Secret Manager・暗号化・HTTPS
5. **監視・運用体制**: ログ・アラート・バックアップ完備

**Step 19完了により、IROAS BOSS V2 MLM管理システムが完全運用可能状態となります。**
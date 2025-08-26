# IROAS BOSS V2 - デプロイ環境構築ガイド

## 📊 概要
Step 19: 3環境構築（本番・ステージング・開発環境）  
要件定義書準拠の完全なデプロイ環境構築

## 🏗️ インフラ構成（要件定義書準拠）

### フロントエンド: Vercel
- **本番**: https://iroas-boss-v2.vercel.app
- **ステージング**: https://iroas-boss-v2-staging.vercel.app  
- **開発**: https://iroas-boss-v2-dev.vercel.app

### バックエンド: GCP Cloud Run
- **本番**: https://iroas-boss-v2-backend.run.app
- **ステージング**: https://iroas-boss-v2-backend-staging.run.app
- **開発**: https://iroas-boss-v2-backend-dev.run.app

### データベース: PostgreSQL 15+
- **本番**: NEON PostgreSQL / Railway PostgreSQL
- **ステージング**: 専用PostgreSQL インスタンス
- **開発**: ローカル PostgreSQL / Docker

## 🔧 技術仕様

### MLMビジネス要件（簡略化厳禁）
```yaml
会員管理:
  最大会員数: 50名
  新規募集: なし
  29項目データ: 完全実装必須

料金体系:
  ヒーロープラン: 10,670円（固定）
  テストプラン: 9,800円（固定）

報酬計算:
  実行頻度: 月次（毎月25日頃）
  ボーナス種類: 7種類（デイリー、タイトル、リファラル、パワー、メンテナンス、セールスアクティビティ、ロイヤルファミリー）
  最低振込: 5,000円（未満繰越）

外部連携:
  Univapay: カード決済・口座振替（Shift-JIS CSV）
  GMOネットバンク: 振込用CSV生成
  エンコーディング: Shift-JIS必須対応
```

### セキュリティ要件
```yaml
認証: Phase 21で追加（現在は未実装）
CSV暗号化: 本番環境で必須
セッション: 12時間有効
データ保護: PostgreSQL + バックアップ
```

## 📁 ディレクトリ構成

```
deployment/
├── README.md                 # このファイル
├── vercel/                  # Vercel設定
│   ├── vercel.json          # Vercel設定ファイル
│   ├── production.env       # 本番環境変数
│   ├── staging.env          # ステージング環境変数
│   └── development.env      # 開発環境変数
├── gcp/                     # GCP Cloud Run設定
│   ├── Dockerfile          # コンテナ設定
│   ├── cloudbuild.yaml     # Cloud Build設定
│   ├── production.yaml     # 本番デプロイ設定
│   ├── staging.yaml        # ステージングデプロイ設定
│   └── development.yaml    # 開発デプロイ設定
├── database/               # PostgreSQL設定
│   ├── init.sql           # 初期化スクリプト
│   ├── migrations/        # マイグレーションファイル
│   └── backup-scripts/    # バックアップスクリプト
└── monitoring/            # 監視・ログ設定
    ├── logging.yaml       # ログ設定
    └── alerts.yaml        # アラート設定
```

## 🌐 環境別設定

### 本番環境（Production）
- **目的**: 実際の業務運用環境
- **URL**: iroas-boss-v2.vercel.app
- **データベース**: 高可用性PostgreSQL
- **セキュリティ**: 最高レベル
- **バックアップ**: 日次自動実行

### ステージング環境（Staging）
- **目的**: 本番デプロイ前検証環境
- **URL**: iroas-boss-v2-staging.vercel.app
- **データベース**: 本番同等構成
- **用途**: 最終動作確認・ユーザー受入テスト

### 開発環境（Development）
- **目的**: 開発・テスト環境
- **URL**: iroas-boss-v2-dev.vercel.app
- **データベース**: 開発用PostgreSQL
- **用途**: 機能開発・統合テスト

## 🔄 デプロイフロー

### 1. 開発→ステージング
```bash
# 機能開発完了後
git push origin develop
# 自動デプロイ: staging環境
```

### 2. ステージング→本番
```bash
# ステージング検証完了後
git push origin main
# 自動デプロイ: 本番環境
```

## 📊 監視・運用

### ヘルスチェック
- **フロントエンド**: Vercel標準監視
- **バックエンド**: Cloud Run自動監視
- **データベース**: PostgreSQL監視

### ログ管理
- **アプリケーションログ**: Cloud Logging
- **アクセスログ**: Vercel Analytics
- **エラー追跡**: 統合エラー監視

## 🚀 デプロイ手順概要

1. **Vercel設定**: フロントエンドデプロイ設定
2. **GCP設定**: バックエンドCloud Run設定  
3. **PostgreSQL**: データベース環境構築
4. **環境変数**: 3環境別設定管理
5. **動作検証**: 各環境での統合テスト

この構成により、要件定義書に完全準拠した MLM管理システムの安全で効率的な運用環境が実現されます。
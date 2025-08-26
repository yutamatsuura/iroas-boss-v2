# IROAS BOSS V2 - Backend Dockerfile
# GCP Cloud Run用コンテナ設定
# Python 3.11 + FastAPI + SQLAlchemy 2.0

FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# システム依存関係インストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をコピー
COPY backend/requirements.txt .

# Python依存関係インストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY backend/ .

# 環境変数設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# MLM業務設定（要件定義書準拠）
ENV HERO_PLAN_PRICE=10670
ENV TEST_PLAN_PRICE=9800
ENV MINIMUM_PAYOUT_AMOUNT=5000
ENV REWARD_CALCULATION_DAY=25
ENV MAX_MEMBERS=50

# セキュリティ設定
ENV CORS_ORIGINS='["https://iroas-boss-v2.vercel.app","https://iroas-boss-v2-staging.vercel.app","https://iroas-boss-v2-dev.vercel.app"]'

# ヘルスチェックエンドポイント
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# 非root ユーザー作成
RUN useradd --create-home --shell /bin/bash app
USER app

# ポート公開
EXPOSE 8080

# アプリケーション起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
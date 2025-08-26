"""
データベース基盤設定

PostgreSQL 15+ + SQLAlchemy 2.0 を使用
Alembicマイグレーション対応
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from typing import Generator

# 環境変数からデータベース接続情報を取得
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/iroas_boss_v2")

# SQLAlchemy エンジン作成
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # SQL出力設定
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # 接続確認
    pool_recycle=3600,   # 1時間で接続をリサイクル
)

# セッション設定
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ベースクラス
Base = declarative_base()

def get_db() -> Generator:
    """
    データベースセッション取得
    FastAPI依存性注入で使用
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    テーブル作成（開発時のみ使用）
    本番環境ではAlembicマイグレーションを使用
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    テーブル削除（開発時のみ使用）
    """
    Base.metadata.drop_all(bind=engine)
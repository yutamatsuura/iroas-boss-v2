"""
Alembic環境設定

SQLAlchemy 2.0対応のマイグレーション環境
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# アプリケーションモジュールを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Alembicの設定オブジェクト
config = context.config

# ログ設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# モデルのメタデータをインポート
from app.database import Base
from app.models import *  # 全モデルをインポート

target_metadata = Base.metadata

def get_url():
    """データベースURLを環境変数から取得"""
    return os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/iroas_boss_v2")

def run_migrations_offline() -> None:
    """
    オフラインモードでマイグレーション実行
    'alembic upgrade --sql' で SQL出力のみ
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    オンラインモードでマイグレーション実行
    データベース接続を使用して実際にマイグレーション実行
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # PostgreSQL用の型比較設定
            render_as_batch=False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
# IROAS BOSS V2 - ユーザー・認証モデル
# Phase 21対応・MLMビジネス要件準拠

from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class UserRole(str, Enum):
    """ユーザー役割定義"""
    SUPER_ADMIN = "super_admin"      # システム全権限
    ADMIN = "admin"                  # 管理者権限  
    MLM_MANAGER = "mlm_manager"      # MLM管理権限
    VIEWER = "viewer"                # 閲覧専用権限

class UserStatus(str, Enum):
    """ユーザーステータス定義"""
    ACTIVE = "active"                # アクティブ
    SUSPENDED = "suspended"          # 停止中
    LOCKED = "locked"                # ロック中
    PENDING = "pending"              # 承認待ち

class User(Base):
    """認証ユーザーモデル（MLMビジネス要件準拠）"""
    
    __tablename__ = "users"
    
    # 基本情報
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="ユーザー名")
    email = Column(String(255), unique=True, index=True, nullable=False, comment="メールアドレス")
    hashed_password = Column(String(255), nullable=False, comment="ハッシュ化パスワード")
    
    # 認証状態
    is_active = Column(Boolean, default=True, comment="アクティブ状態")
    is_verified = Column(Boolean, default=False, comment="メール認証済み")
    is_superuser = Column(Boolean, default=False, comment="スーパーユーザー")
    
    # ロール・権限
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False, comment="ユーザー役割")
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING, nullable=False, comment="ユーザーステータス")
    permissions = Column(Text, comment="追加権限（JSON形式）")
    
    # プロファイル情報
    full_name = Column(String(100), comment="フルネーム")
    display_name = Column(String(50), comment="表示名")
    phone = Column(String(20), comment="電話番号")
    
    # セキュリティ設定
    login_attempts = Column(Integer, default=0, comment="ログイン試行回数")
    locked_at = Column(DateTime, comment="ロック日時")
    last_login_at = Column(DateTime, comment="最終ログイン日時")
    last_login_ip = Column(String(45), comment="最終ログインIP")
    
    # 多要素認証
    mfa_enabled = Column(Boolean, default=False, comment="MFA有効")
    mfa_secret = Column(String(255), comment="MFA秘密鍵")
    mfa_backup_codes = Column(Text, comment="MFAバックアップコード（JSON形式）")
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    # 関連データ
    access_logs = relationship("UserAccessLog", back_populates="user", cascade="all, delete-orphan")
    session_tokens = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role.value}', status='{self.status.value}')>"

class UserAccessLog(Base):
    """ユーザーアクセスログモデル"""
    
    __tablename__ = "user_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="ユーザーID")
    
    # アクセス情報
    action = Column(String(50), nullable=False, comment="アクション")
    ip_address = Column(String(45), comment="IPアドレス")
    user_agent = Column(Text, comment="ユーザーエージェント")
    
    # リクエスト詳細
    path = Column(String(255), comment="アクセスパス")
    method = Column(String(10), comment="HTTPメソッド")
    status_code = Column(Integer, comment="レスポンスステータス")
    
    # 結果情報
    success = Column(Boolean, default=True, comment="成功フラグ")
    error_message = Column(Text, comment="エラーメッセージ")
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="作成日時")
    
    # リレーション
    user = relationship("User", back_populates="access_logs")
    
    def __repr__(self):
        return f"<UserAccessLog(user_id={self.user_id}, action='{self.action}', success={self.success})>"

class UserSession(Base):
    """ユーザーセッション管理モデル"""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="ユーザーID")
    
    # セッション情報
    session_token = Column(String(255), unique=True, index=True, nullable=False, comment="セッショントークン")
    refresh_token = Column(String(255), unique=True, index=True, comment="リフレッシュトークン")
    jti = Column(String(255), unique=True, index=True, comment="JWT ID")
    
    # セッション詳細
    ip_address = Column(String(45), comment="IPアドレス")
    user_agent = Column(Text, comment="ユーザーエージェント")
    device_info = Column(Text, comment="デバイス情報（JSON形式）")
    
    # 有効期限
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="有効期限")
    refresh_expires_at = Column(DateTime(timezone=True), comment="リフレッシュトークン有効期限")
    
    # 状態
    is_active = Column(Boolean, default=True, comment="アクティブ状態")
    revoked_at = Column(DateTime(timezone=True), comment="無効化日時")
    revoked_reason = Column(String(100), comment="無効化理由")
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="作成日時")
    last_used_at = Column(DateTime(timezone=True), comment="最終使用日時")
    
    # リレーション
    user = relationship("User", back_populates="session_tokens")
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, is_active={self.is_active}, expires_at={self.expires_at})>"

class UserPermission(Base):
    """ユーザー権限管理モデル"""
    
    __tablename__ = "user_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 権限定義
    permission_name = Column(String(100), unique=True, nullable=False, comment="権限名")
    permission_code = Column(String(50), unique=True, nullable=False, comment="権限コード")
    description = Column(Text, comment="権限説明")
    
    # 権限分類
    category = Column(String(50), nullable=False, comment="権限カテゴリ")
    resource = Column(String(50), comment="対象リソース")
    action = Column(String(50), comment="許可アクション")
    
    # 状態
    is_active = Column(Boolean, default=True, comment="アクティブ状態")
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    def __repr__(self):
        return f"<UserPermission(permission_code='{self.permission_code}', category='{self.category}')>"

class UserRolePermission(Base):
    """ユーザー役割権限関連テーブル"""
    
    __tablename__ = "user_role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, comment="ユーザー役割")
    permission_id = Column(Integer, ForeignKey("user_permissions.id"), nullable=False, comment="権限ID")
    
    # 制約・条件
    conditions = Column(Text, comment="権限条件（JSON形式）")
    is_granted = Column(Boolean, default=True, comment="許可フラグ")
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="作成日時")
    
    def __repr__(self):
        return f"<UserRolePermission(role='{self.role.value}', permission_id={self.permission_id})>"
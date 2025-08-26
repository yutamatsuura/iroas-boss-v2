-- IROAS BOSS V2 - データベース初期化スクリプト
-- PostgreSQL 15+ 対応
-- 要件定義書準拠のMLM管理システム

-- ===================
-- データベース作成
-- ===================

-- 本番環境用データベース
CREATE DATABASE iroas_boss_v2_production
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'ja_JP.UTF-8'
    LC_CTYPE = 'ja_JP.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    TEMPLATE template0;

-- ステージング環境用データベース
CREATE DATABASE iroas_boss_v2_staging
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'ja_JP.UTF-8'
    LC_CTYPE = 'ja_JP.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    TEMPLATE template0;

-- 開発環境用データベース
CREATE DATABASE iroas_boss_v2_development
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'ja_JP.UTF-8'
    LC_CTYPE = 'ja_JP.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    TEMPLATE template0;

-- ===================
-- ユーザー作成とアクセス権限設定
-- ===================

-- 本番環境用ユーザー
CREATE USER iroas_boss_production WITH PASSWORD 'secure_production_password_2025';
GRANT ALL PRIVILEGES ON DATABASE iroas_boss_v2_production TO iroas_boss_production;

-- ステージング環境用ユーザー
CREATE USER iroas_boss_staging WITH PASSWORD 'secure_staging_password_2025';
GRANT ALL PRIVILEGES ON DATABASE iroas_boss_v2_staging TO iroas_boss_staging;

-- 開発環境用ユーザー
CREATE USER iroas_boss_development WITH PASSWORD 'secure_development_password_2025';
GRANT ALL PRIVILEGES ON DATABASE iroas_boss_v2_development TO iroas_boss_development;

-- ===================
-- 拡張機能有効化
-- ===================

-- UUID生成用拡張機能
\c iroas_boss_v2_production;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c iroas_boss_v2_staging;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c iroas_boss_v2_development;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ===================
-- 基本テーブル構造
-- ===================

-- 本番環境への接続
\c iroas_boss_v2_production iroas_boss_production;

-- 会員テーブル（29項目対応）
CREATE TABLE members (
    id SERIAL PRIMARY KEY,
    member_number VARCHAR(7) UNIQUE NOT NULL,  -- 7桁会員番号
    
    -- 基本情報
    status VARCHAR(20) NOT NULL DEFAULT 'アクティブ',
    name VARCHAR(100) NOT NULL,
    name_kana VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    gender VARCHAR(10),
    
    -- 住所情報
    postal_code VARCHAR(8),
    prefecture VARCHAR(20),
    address_1 VARCHAR(200),
    address_2 VARCHAR(200),
    address_3 VARCHAR(200),
    
    -- MLM情報
    title VARCHAR(50) NOT NULL DEFAULT '称号なし',
    user_type VARCHAR(20) NOT NULL DEFAULT '通常',
    plan VARCHAR(30) NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    
    -- 組織情報
    upline_id VARCHAR(7),
    upline_name VARCHAR(100),
    referrer_id VARCHAR(7),
    referrer_name VARCHAR(100),
    
    -- 銀行情報
    bank_name VARCHAR(100),
    bank_code VARCHAR(10),
    branch_name VARCHAR(100),
    branch_code VARCHAR(10),
    account_number VARCHAR(20),
    yucho_symbol VARCHAR(10),
    yucho_number VARCHAR(20),
    account_type VARCHAR(10),
    
    -- システム情報
    registration_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    withdrawal_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 決済データテーブル
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
    payment_method VARCHAR(30) NOT NULL,
    amount INTEGER NOT NULL,  -- 円単位
    status VARCHAR(20) NOT NULL DEFAULT '未処理',
    payment_date DATE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    univapay_transaction_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 報酬計算結果テーブル
CREATE TABLE reward_calculations (
    id SERIAL PRIMARY KEY,
    calculation_date DATE NOT NULL,
    member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
    
    -- 7種類ボーナス
    daily_bonus INTEGER NOT NULL DEFAULT 0,
    title_bonus INTEGER NOT NULL DEFAULT 0,
    referral_bonus INTEGER NOT NULL DEFAULT 0,
    power_bonus INTEGER NOT NULL DEFAULT 0,
    maintenance_bonus INTEGER NOT NULL DEFAULT 0,
    sales_activity_bonus INTEGER NOT NULL DEFAULT 0,
    royal_family_bonus INTEGER NOT NULL DEFAULT 0,
    
    total_bonus INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT '未確定',
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 支払管理テーブル
CREATE TABLE payouts (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
    target_month DATE NOT NULL,
    total_amount INTEGER NOT NULL,
    withholding_tax INTEGER NOT NULL DEFAULT 0,
    net_amount INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT '未処理',
    payout_date DATE,
    gmo_csv_generated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- アクティビティログテーブル
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    activity_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    target_member_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 組織調整履歴テーブル
CREATE TABLE organization_adjustments (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(50) NOT NULL,
    old_upline_id VARCHAR(7),
    new_upline_id VARCHAR(7),
    reason TEXT NOT NULL,
    adjusted_by VARCHAR(50) NOT NULL,
    approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(50),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ===================
-- インデックス作成
-- ===================

-- 会員テーブル用インデックス
CREATE INDEX idx_members_member_number ON members(member_number);
CREATE INDEX idx_members_email ON members(email);
CREATE INDEX idx_members_status ON members(status);
CREATE INDEX idx_members_upline_id ON members(upline_id);
CREATE INDEX idx_members_referrer_id ON members(referrer_id);
CREATE INDEX idx_members_registration_date ON members(registration_date);

-- 決済テーブル用インデックス
CREATE INDEX idx_payments_member_id ON payments(member_id);
CREATE INDEX idx_payments_payment_date ON payments(payment_date);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_payment_method ON payments(payment_method);

-- 報酬計算テーブル用インデックス
CREATE INDEX idx_reward_calculations_member_id ON reward_calculations(member_id);
CREATE INDEX idx_reward_calculations_calculation_date ON reward_calculations(calculation_date);
CREATE INDEX idx_reward_calculations_status ON reward_calculations(status);

-- 支払管理テーブル用インデックス
CREATE INDEX idx_payouts_member_id ON payouts(member_id);
CREATE INDEX idx_payouts_target_month ON payouts(target_month);
CREATE INDEX idx_payouts_status ON payouts(status);

-- アクティビティログテーブル用インデックス
CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_activity_type ON activity_logs(activity_type);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at);

-- 組織調整履歴テーブル用インデックス
CREATE INDEX idx_organization_adjustments_member_id ON organization_adjustments(member_id);
CREATE INDEX idx_organization_adjustments_approved ON organization_adjustments(approved);

-- ===================
-- トリガー関数作成
-- ===================

-- updated_at自動更新関数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- トリガー設定
CREATE TRIGGER update_members_updated_at BEFORE UPDATE ON members FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_reward_calculations_updated_at BEFORE UPDATE ON reward_calculations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payouts_updated_at BEFORE UPDATE ON payouts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===================
-- 初期データ投入
-- ===================

-- システム管理用ユーザーの作成（会員番号0000001）
INSERT INTO members (
    member_number, name, name_kana, email, title, user_type, plan, payment_method,
    upline_id, referrer_id, status, registration_date
) VALUES (
    '0000001', 'システム管理者', 'システムカンリシャ', 'admin@example.com', 
    'エンペラー/エンプレス', '通常', 'ヒーロープラン', 'カード決済',
    NULL, NULL, 'アクティブ', CURRENT_TIMESTAMP
);

-- ===================
-- ステージング・開発環境への複製
-- ===================

-- ステージング環境へのテーブル構造複製
\c iroas_boss_v2_staging iroas_boss_staging;
\i /dev/stdin

-- 開発環境へのテーブル構造複製  
\c iroas_boss_v2_development iroas_boss_development;
\i /dev/stdin

-- 完了メッセージ
SELECT 'IROAS BOSS V2 データベース初期化完了' as status;
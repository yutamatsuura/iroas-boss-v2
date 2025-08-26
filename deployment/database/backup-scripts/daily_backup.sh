#!/bin/bash

# IROAS BOSS V2 - 日次バックアップスクリプト
# PostgreSQL データベースの自動バックアップ

set -e

# ===================
# 設定変数
# ===================

# 日付設定
BACKUP_DATE=$(date +"%Y%m%d_%H%M%S")
CURRENT_DATE=$(date +"%Y-%m-%d")

# バックアップディレクトリ
BACKUP_ROOT="/backup/iroas-boss-v2"
BACKUP_DIR="${BACKUP_ROOT}/${CURRENT_DATE}"

# 保持期間（日数）
RETENTION_DAYS=30

# データベース設定
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5432"}

# 環境別データベース設定
PRODUCTION_DB="iroas_boss_v2_production"
STAGING_DB="iroas_boss_v2_staging"
DEVELOPMENT_DB="iroas_boss_v2_development"

# 通知設定
SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL:-""}
EMAIL_NOTIFY=${EMAIL_NOTIFY:-"admin@example.com"}

# ===================
# ログ関数
# ===================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${BACKUP_DIR}/backup.log"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "${BACKUP_DIR}/backup.log"
}

# ===================
# 通知関数
# ===================

send_notification() {
    local status=$1
    local message=$2
    
    # Slack通知
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🏢 IROAS BOSS V2 Backup $status: $message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    # メール通知（システムのmailコマンドを使用）
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "IROAS BOSS V2 Backup $status" "$EMAIL_NOTIFY"
    fi
}

# ===================
# バックアップディレクトリ作成
# ===================

create_backup_directory() {
    log "バックアップディレクトリ作成: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    
    # 権限設定
    chmod 750 "$BACKUP_DIR"
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        error "バックアップディレクトリの作成に失敗: $BACKUP_DIR"
        exit 1
    fi
}

# ===================
# データベースバックアップ関数
# ===================

backup_database() {
    local db_name=$1
    local env_name=$2
    
    log "データベースバックアップ開始: $db_name ($env_name)"
    
    # バックアップファイル名
    local backup_file="${BACKUP_DIR}/${db_name}_${BACKUP_DATE}.sql.gz"
    
    # pg_dump実行
    if PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$db_name" \
        --verbose \
        --no-password \
        --format=custom \
        --compress=9 \
        --no-owner \
        --no-privileges | gzip > "$backup_file"; then
        
        log "バックアップ完了: $backup_file"
        
        # ファイルサイズ確認
        local file_size=$(du -h "$backup_file" | cut -f1)
        log "バックアップサイズ: $file_size"
        
        # 整合性チェック
        if gzip -t "$backup_file"; then
            log "整合性チェック成功: $backup_file"
        else
            error "整合性チェック失敗: $backup_file"
            return 1
        fi
        
    else
        error "バックアップ失敗: $db_name"
        return 1
    fi
}

# ===================
# スキーマのみバックアップ
# ===================

backup_schema_only() {
    local db_name=$1
    local env_name=$2
    
    log "スキーマバックアップ開始: $db_name ($env_name)"
    
    local schema_file="${BACKUP_DIR}/${db_name}_schema_${BACKUP_DATE}.sql"
    
    if PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$db_name" \
        --schema-only \
        --verbose \
        --no-password \
        --no-owner \
        --no-privileges > "$schema_file"; then
        
        log "スキーマバックアップ完了: $schema_file"
    else
        error "スキーマバックアップ失敗: $db_name"
    fi
}

# ===================
# 古いバックアップ削除
# ===================

cleanup_old_backups() {
    log "古いバックアップ削除開始（${RETENTION_DAYS}日以上前）"
    
    find "$BACKUP_ROOT" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
    find "$BACKUP_ROOT" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_ROOT" -name "*.sql" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    log "古いバックアップ削除完了"
}

# ===================
# バックアップ統計
# ===================

generate_backup_report() {
    local total_size=$(du -sh "$BACKUP_DIR" | cut -f1)
    local file_count=$(find "$BACKUP_DIR" -name "*.sql.gz" | wc -l)
    
    log "=== バックアップレポート ==="
    log "日付: $CURRENT_DATE"
    log "総サイズ: $total_size"
    log "ファイル数: $file_count"
    log "保存場所: $BACKUP_DIR"
    log "=========================="
}

# ===================
# メイン処理
# ===================

main() {
    log "IROAS BOSS V2 日次バックアップ開始"
    
    # バックアップディレクトリ作成
    create_backup_directory
    
    local backup_success=true
    
    # 本番環境バックアップ
    if [[ -n "${PRODUCTION_DB_PASSWORD}" ]]; then
        export DB_PASSWORD="$PRODUCTION_DB_PASSWORD"
        export DB_USER="iroas_boss_production"
        
        if ! backup_database "$PRODUCTION_DB" "production"; then
            backup_success=false
        fi
        backup_schema_only "$PRODUCTION_DB" "production"
    fi
    
    # ステージング環境バックアップ
    if [[ -n "${STAGING_DB_PASSWORD}" ]]; then
        export DB_PASSWORD="$STAGING_DB_PASSWORD"
        export DB_USER="iroas_boss_staging"
        
        if ! backup_database "$STAGING_DB" "staging"; then
            backup_success=false
        fi
        backup_schema_only "$STAGING_DB" "staging"
    fi
    
    # 開発環境バックアップ（週末のみ）
    if [[ $(date +%u) -eq 7 ]] && [[ -n "${DEVELOPMENT_DB_PASSWORD}" ]]; then
        export DB_PASSWORD="$DEVELOPMENT_DB_PASSWORD"
        export DB_USER="iroas_boss_development"
        
        backup_database "$DEVELOPMENT_DB" "development"
        backup_schema_only "$DEVELOPMENT_DB" "development"
    fi
    
    # 古いバックアップ削除
    cleanup_old_backups
    
    # レポート生成
    generate_backup_report
    
    if $backup_success; then
        log "IROAS BOSS V2 日次バックアップ完了"
        send_notification "Success" "日次バックアップが正常に完了しました。総サイズ: $(du -sh "$BACKUP_DIR" | cut -f1)"
    else
        log "IROAS BOSS V2 日次バックアップ完了（エラーあり）"
        send_notification "Warning" "日次バックアップが完了しましたが、一部にエラーがありました。ログを確認してください。"
    fi
}

# ===================
# 実行
# ===================

# エラーハンドリング
trap 'error "バックアップスクリプトでエラーが発生しました"; send_notification "Failed" "バックアップスクリプトでエラーが発生しました"; exit 1' ERR

# メイン処理実行
main "$@"
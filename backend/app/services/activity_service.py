"""
アクティビティログサービス

Phase A-1c: アクティビティログAPI（6.1-6.3）
- 完全独立、いつでも実装可能
- モックアップP-007対応

エンドポイント:
- 6.1 GET /api/activity/logs - ログ一覧
- 6.2 GET /api/activity/logs/filter - ログ検索
- 6.3 GET /api/activity/logs/{id} - ログ詳細
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta

from app.models.activity import ActivityLog, ActivityType
from app.schemas.activity import (
    ActivityLogResponse,
    ActivityLogListResponse,
    ActivityLogFilterResponse,
    ActivityLogSummaryResponse
)


class ActivityService:
    """
    アクティビティログサービスクラス
    システム操作履歴の記録・管理を担当
    """

    def __init__(self, db: Session):
        self.db = db

    async def get_activity_logs(
        self, 
        page: int = 1, 
        per_page: int = 50,
        level_filter: Optional[List[str]] = None
    ) -> ActivityLogListResponse:
        """
        ログ一覧取得
        API 6.1: GET /api/activity/logs
        """
        # ベースクエリ（新しい順）
        query = self.db.query(ActivityLog).order_by(desc(ActivityLog.created_at))
        
        # ログレベルフィルター
        if level_filter:
            query = query.filter(ActivityLog.log_level.in_(level_filter))
        
        # 総件数取得
        total_count = query.count()
        
        # ページネーション
        offset = (page - 1) * per_page
        logs = query.offset(offset).limit(per_page).all()
        
        # レスポンス変換
        log_list = [self._convert_to_response(log) for log in logs]
        
        return ActivityLogListResponse(
            logs=log_list,
            total_count=total_count,
            page=page,
            per_page=per_page,
            total_pages=(total_count + per_page - 1) // per_page,
            has_next=page * per_page < total_count,
            has_previous=page > 1
        )

    async def filter_activity_logs(
        self,
        action_type: Optional[List[str]] = None,
        log_level: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> ActivityLogFilterResponse:
        """
        ログ検索・フィルタリング
        API 6.2: GET /api/activity/logs/filter
        """
        # ベースクエリ
        query = self.db.query(ActivityLog).order_by(desc(ActivityLog.created_at))
        
        # アクションタイプフィルター
        if action_type:
            query = query.filter(ActivityLog.action_type.in_(action_type))
        
        # ログレベルフィルター
        if log_level:
            query = query.filter(ActivityLog.log_level.in_(log_level))
        
        # ユーザーIDフィルター
        if user_id:
            query = query.filter(ActivityLog.user_id.ilike(f"%{user_id}%"))
        
        # 日付範囲フィルター
        if date_from:
            query = query.filter(ActivityLog.created_at >= date_from)
        if date_to:
            # 日付の終了時刻を含むため23:59:59を追加
            end_date = date_to.replace(hour=23, minute=59, second=59)
            query = query.filter(ActivityLog.created_at <= end_date)
        
        # テキスト検索（アクション、詳細、IPアドレス）
        if search_query:
            search_conditions = or_(
                ActivityLog.action.ilike(f"%{search_query}%"),
                ActivityLog.details.ilike(f"%{search_query}%"),
                ActivityLog.ip_address.ilike(f"%{search_query}%")
            )
            query = query.filter(search_conditions)
        
        # 総件数取得
        total_count = query.count()
        
        # ページネーション
        offset = (page - 1) * per_page
        logs = query.offset(offset).limit(per_page).all()
        
        # レスポンス変換
        log_list = [self._convert_to_response(log) for log in logs]
        
        return ActivityLogFilterResponse(
            logs=log_list,
            filter_conditions={
                "action_type": action_type,
                "log_level": log_level,
                "user_id": user_id,
                "date_from": date_from,
                "date_to": date_to,
                "search_query": search_query
            },
            total_count=total_count,
            page=page,
            per_page=per_page,
            total_pages=(total_count + per_page - 1) // per_page,
            filter_summary={
                "filtered_records": total_count,
                "filter_applied": any([action_type, log_level, user_id, date_from, date_to, search_query])
            }
        )

    async def get_activity_log(self, log_id: int) -> ActivityLogResponse:
        """
        ログ詳細取得
        API 6.3: GET /api/activity/logs/{id}
        """
        log = self.db.query(ActivityLog).filter(ActivityLog.id == log_id).first()
        if not log:
            raise ValueError(f"ログID {log_id} は存在しません")
        
        return self._convert_to_response(log)

    async def log_activity(
        self,
        action: str,
        details: str,
        user_id: str,
        action_type: ActionType = ActionType.OTHER,
        log_level: LogLevel = LogLevel.INFO,
        target_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLogResponse:
        """
        アクティビティログ記録
        内部使用：各サービスから呼び出される
        """
        new_log = ActivityLog(
            action=action,
            action_type=action_type,
            details=details,
            log_level=log_level,
            user_id=user_id,
            target_id=target_id,
            ip_address=ip_address or "127.0.0.1",
            user_agent=user_agent or "IROAS BOSS v2 System",
            created_at=datetime.now()
        )
        
        self.db.add(new_log)
        self.db.commit()
        self.db.refresh(new_log)
        
        return self._convert_to_response(new_log)

    async def get_activity_summary(
        self,
        period_days: int = 7
    ) -> ActivityLogSummaryResponse:
        """
        アクティビティサマリー取得
        内部使用：ダッシュボード表示用
        """
        # 集計期間設定
        from_date = datetime.now() - timedelta(days=period_days)
        
        # 期間中の総ログ数
        total_logs = self.db.query(ActivityLog).filter(
            ActivityLog.created_at >= from_date
        ).count()
        
        # アクションタイプ別集計
        action_type_counts = {}
        for action_type in ActionType:
            count = self.db.query(ActivityLog).filter(
                and_(
                    ActivityLog.action_type == action_type,
                    ActivityLog.created_at >= from_date
                )
            ).count()
            action_type_counts[action_type.value] = count
        
        # ログレベル別集計
        log_level_counts = {}
        for log_level in LogLevel:
            count = self.db.query(ActivityLog).filter(
                and_(
                    ActivityLog.log_level == log_level,
                    ActivityLog.created_at >= from_date
                )
            ).count()
            log_level_counts[log_level.value] = count
        
        # ユーザー別集計（上位10位）
        user_activity = self.db.query(
            ActivityLog.user_id,
            self.db.func.count(ActivityLog.id).label('count')
        ).filter(
            ActivityLog.created_at >= from_date
        ).group_by(
            ActivityLog.user_id
        ).order_by(
            desc('count')
        ).limit(10).all()
        
        user_stats = [{"user_id": user.user_id, "count": user.count} for user in user_activity]
        
        # 最新のエラーログ（警告・エラー）
        recent_issues = self.db.query(ActivityLog).filter(
            and_(
                ActivityLog.log_level.in_([LogLevel.WARNING, LogLevel.ERROR]),
                ActivityLog.created_at >= from_date
            )
        ).order_by(desc(ActivityLog.created_at)).limit(5).all()
        
        recent_issues_list = [self._convert_to_response(log) for log in recent_issues]
        
        return ActivityLogSummaryResponse(
            period_days=period_days,
            total_logs=total_logs,
            action_type_distribution=action_type_counts,
            log_level_distribution=log_level_counts,
            top_users=user_stats,
            recent_issues=recent_issues_list,
            summary_generated_at=datetime.now()
        )

    async def cleanup_old_logs(self, retention_days: int = 90) -> Dict[str, Any]:
        """
        古いログの削除
        内部使用：メンテナンス用
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # 削除対象ログ数取得
        old_logs_count = self.db.query(ActivityLog).filter(
            ActivityLog.created_at < cutoff_date
        ).count()
        
        # 削除実行
        deleted = self.db.query(ActivityLog).filter(
            ActivityLog.created_at < cutoff_date
        ).delete()
        
        self.db.commit()
        
        # 削除ログを記録
        await self.log_activity(
            action="ログクリーンアップ実行",
            details=f"保持期間: {retention_days}日, 削除件数: {deleted}件",
            user_id="system",
            action_type=ActionType.MAINTENANCE,
            log_level=LogLevel.INFO
        )
        
        return {
            "retention_days": retention_days,
            "cutoff_date": cutoff_date,
            "deleted_count": deleted,
            "remaining_logs": self.db.query(ActivityLog).count(),
            "cleanup_executed_at": datetime.now()
        }

    def _convert_to_response(self, log: ActivityLog) -> ActivityLogResponse:
        """
        ActivityLog モデルを ActivityLogResponse スキーマに変換
        """
        return ActivityLogResponse(
            id=log.id,
            action=log.action,
            action_type=log.action_type,
            details=log.details,
            log_level=log.log_level,
            user_id=log.user_id,
            target_id=log.target_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
            
            # 表示用フォーマット
            formatted_timestamp=log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            action_display=f"[{log.action_type.value}] {log.action}",
            log_level_color=self._get_log_level_color(log.log_level),
            time_ago=self._calculate_time_ago(log.created_at)
        )

    def _get_log_level_color(self, log_level: LogLevel) -> str:
        """
        ログレベルに応じた表示色を返す
        """
        color_map = {
            LogLevel.DEBUG: "#6b7280",    # グレー
            LogLevel.INFO: "#3b82f6",     # ブルー
            LogLevel.WARNING: "#f59e0b",  # イエロー
            LogLevel.ERROR: "#ef4444",    # レッド
            LogLevel.CRITICAL: "#dc2626"  # ダークレッド
        }
        return color_map.get(log_level, "#6b7280")

    def _calculate_time_ago(self, timestamp: datetime) -> str:
        """
        経過時間を日本語で表現
        """
        now = datetime.now()
        diff = now - timestamp
        
        if diff.total_seconds() < 60:
            return "たった今"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}分前"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}時間前"
        elif diff.days < 30:
            return f"{diff.days}日前"
        else:
            return timestamp.strftime("%Y/%m/%d")
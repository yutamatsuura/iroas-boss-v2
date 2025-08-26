# IROAS BOSS V2 - 権限管理サービス  
# Phase 21対応・MLMビジネス要件準拠

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import UserPermission, UserRolePermission, UserRole, User
from app.schemas.auth import PermissionSummary, RolePermissionsResponse

class PermissionService:
    """権限管理サービス（MLMビジネス要件準拠）"""
    
    def __init__(self):
        pass
    
    # ===================
    # 権限初期化
    # ===================
    
    async def initialize_permissions(self, db: Session):
        """MLMビジネス要件に基づく権限の初期化"""
        
        # 既存の権限をクリア
        db.query(UserRolePermission).delete()
        db.query(UserPermission).delete()
        db.commit()
        
        # MLMビジネス権限定義
        permissions_data = [
            # システム管理権限
            {
                "permission_name": "システム管理",
                "permission_code": "system.admin",
                "description": "システム全体の管理権限",
                "category": "system",
                "resource": "system",
                "action": "admin"
            },
            {
                "permission_name": "ユーザー管理",
                "permission_code": "user.manage",
                "description": "ユーザーアカウントの管理権限",
                "category": "user",
                "resource": "user",
                "action": "manage"
            },
            {
                "permission_name": "ユーザー閲覧",
                "permission_code": "user.view",
                "description": "ユーザー情報の閲覧権限",
                "category": "user",
                "resource": "user",
                "action": "view"
            },
            
            # 会員管理権限（MLM固有）
            {
                "permission_name": "会員管理",
                "permission_code": "member.manage",
                "description": "会員情報の管理権限（29項目データ対応）",
                "category": "mlm",
                "resource": "member",
                "action": "manage"
            },
            {
                "permission_name": "会員閲覧",
                "permission_code": "member.view",
                "description": "会員情報の閲覧権限",
                "category": "mlm",
                "resource": "member",
                "action": "view"
            },
            {
                "permission_name": "会員作成",
                "permission_code": "member.create",
                "description": "新規会員の登録権限",
                "category": "mlm",
                "resource": "member",
                "action": "create"
            },
            {
                "permission_name": "会員編集",
                "permission_code": "member.edit",
                "description": "会員情報の編集権限",
                "category": "mlm",
                "resource": "member",
                "action": "edit"
            },
            {
                "permission_name": "会員削除",
                "permission_code": "member.delete",
                "description": "会員情報の削除・退会処理権限",
                "category": "mlm",
                "resource": "member",
                "action": "delete"
            },
            
            # 組織管理権限（MLM固有）
            {
                "permission_name": "組織管理",
                "permission_code": "organization.manage",
                "description": "組織構造の管理権限（手動調整対応）",
                "category": "mlm",
                "resource": "organization",
                "action": "manage"
            },
            {
                "permission_name": "組織閲覧",
                "permission_code": "organization.view",
                "description": "組織構造の閲覧権限",
                "category": "mlm",
                "resource": "organization",
                "action": "view"
            },
            {
                "permission_name": "スポンサー変更",
                "permission_code": "organization.sponsor_change",
                "description": "スポンサー変更・組織調整権限",
                "category": "mlm",
                "resource": "organization",
                "action": "sponsor_change"
            },
            
            # 決済管理権限（MLM固有）
            {
                "permission_name": "決済管理",
                "permission_code": "payment.manage",
                "description": "決済データの管理権限（Univapay連携）",
                "category": "mlm",
                "resource": "payment",
                "action": "manage"
            },
            {
                "permission_name": "決済閲覧",
                "permission_code": "payment.view",
                "description": "決済データの閲覧権限",
                "category": "mlm",
                "resource": "payment",
                "action": "view"
            },
            {
                "permission_name": "決済CSV出力",
                "permission_code": "payment.csv_export",
                "description": "決済CSV出力権限（Shift-JIS対応）",
                "category": "mlm",
                "resource": "payment",
                "action": "csv_export"
            },
            {
                "permission_name": "決済結果取込",
                "permission_code": "payment.result_import",
                "description": "決済結果CSV取込権限",
                "category": "mlm",
                "resource": "payment",
                "action": "result_import"
            },
            
            # 報酬管理権限（MLM固有）
            {
                "permission_name": "報酬管理",
                "permission_code": "reward.manage",
                "description": "報酬計算の管理権限（7種ボーナス対応）",
                "category": "mlm",
                "resource": "reward",
                "action": "manage"
            },
            {
                "permission_name": "報酬閲覧",
                "permission_code": "reward.view",
                "description": "報酬データの閲覧権限",
                "category": "mlm",
                "resource": "reward",
                "action": "view"
            },
            {
                "permission_name": "報酬計算実行",
                "permission_code": "reward.calculate",
                "description": "報酬計算実行権限（月次処理）",
                "category": "mlm",
                "resource": "reward",
                "action": "calculate"
            },
            {
                "permission_name": "報酬履歴削除",
                "permission_code": "reward.delete_history",
                "description": "報酬履歴削除権限",
                "category": "mlm",
                "resource": "reward",
                "action": "delete_history"
            },
            
            # 支払管理権限（MLM固有）
            {
                "permission_name": "支払管理",
                "permission_code": "payout.manage",
                "description": "支払管理権限（GMO連携）",
                "category": "mlm",
                "resource": "payout",
                "action": "manage"
            },
            {
                "permission_name": "支払閲覧",
                "permission_code": "payout.view",
                "description": "支払データの閲覧権限",
                "category": "mlm",
                "resource": "payout",
                "action": "view"
            },
            {
                "permission_name": "GMO CSV出力",
                "permission_code": "payout.gmo_export",
                "description": "GMOネットバンク用CSV出力権限",
                "category": "mlm",
                "resource": "payout",
                "action": "gmo_export"
            },
            {
                "permission_name": "支払確定",
                "permission_code": "payout.confirm",
                "description": "支払確定権限",
                "category": "mlm",
                "resource": "payout",
                "action": "confirm"
            },
            
            # データ管理権限（MLM固有）
            {
                "permission_name": "データ管理",
                "permission_code": "data.manage",
                "description": "データ入出力管理権限",
                "category": "mlm",
                "resource": "data",
                "action": "manage"
            },
            {
                "permission_name": "データ出力",
                "permission_code": "data.export",
                "description": "データ出力権限",
                "category": "mlm",
                "resource": "data",
                "action": "export"
            },
            {
                "permission_name": "データ取込",
                "permission_code": "data.import",
                "description": "データ取込権限",
                "category": "mlm",
                "resource": "data",
                "action": "import"
            },
            {
                "permission_name": "バックアップ",
                "permission_code": "data.backup",
                "description": "データバックアップ権限",
                "category": "mlm",
                "resource": "data",
                "action": "backup"
            },
            
            # アクティビティ管理権限
            {
                "permission_name": "活動履歴管理",
                "permission_code": "activity.manage",
                "description": "活動履歴の管理権限",
                "category": "mlm",
                "resource": "activity",
                "action": "manage"
            },
            {
                "permission_name": "活動履歴閲覧",
                "permission_code": "activity.view",
                "description": "活動履歴の閲覧権限",
                "category": "mlm",
                "resource": "activity",
                "action": "view"
            },
            
            # システム設定権限
            {
                "permission_name": "システム設定管理",
                "permission_code": "settings.manage",
                "description": "システム設定の管理権限",
                "category": "system",
                "resource": "settings",
                "action": "manage"
            },
            {
                "permission_name": "システム設定閲覧",
                "permission_code": "settings.view",
                "description": "システム設定の閲覧権限",
                "category": "system",
                "resource": "settings",
                "action": "view"
            }
        ]
        
        # 権限を作成
        permissions = []
        for perm_data in permissions_data:
            permission = UserPermission(**perm_data)
            permissions.append(permission)
            db.add(permission)
        
        db.commit()
        
        # ロール別権限を設定
        await self._setup_role_permissions(db, permissions)
    
    async def _setup_role_permissions(self, db: Session, permissions: List[UserPermission]):
        """ロール別権限設定"""
        
        # 権限コードから権限IDのマッピングを作成
        permission_map = {perm.permission_code: perm.id for perm in permissions}
        
        # スーパー管理者権限（全権限）
        super_admin_permissions = list(permission_map.keys())
        
        # 管理者権限（システム管理を除く全権限）
        admin_permissions = [
            code for code in permission_map.keys() 
            if not code.startswith("system.")
        ]
        
        # MLM管理者権限（MLM関連の全権限）
        mlm_manager_permissions = [
            "user.view",
            "member.manage", "member.view", "member.create", "member.edit", "member.delete",
            "organization.manage", "organization.view", "organization.sponsor_change",
            "payment.manage", "payment.view", "payment.csv_export", "payment.result_import",
            "reward.manage", "reward.view", "reward.calculate", "reward.delete_history",
            "payout.manage", "payout.view", "payout.gmo_export", "payout.confirm",
            "data.manage", "data.export", "data.import", "data.backup",
            "activity.manage", "activity.view",
            "settings.view"
        ]
        
        # 閲覧者権限（基本的な閲覧のみ）
        viewer_permissions = [
            "member.view",
            "organization.view",
            "payment.view",
            "reward.view",
            "payout.view",
            "activity.view",
            "settings.view"
        ]
        
        # ロール権限マッピング
        role_permission_mapping = {
            UserRole.SUPER_ADMIN: super_admin_permissions,
            UserRole.ADMIN: admin_permissions,
            UserRole.MLM_MANAGER: mlm_manager_permissions,
            UserRole.VIEWER: viewer_permissions
        }
        
        # ロール権限を作成
        for role, permission_codes in role_permission_mapping.items():
            for permission_code in permission_codes:
                if permission_code in permission_map:
                    role_permission = UserRolePermission(
                        role=role,
                        permission_id=permission_map[permission_code],
                        is_granted=True
                    )
                    db.add(role_permission)
        
        db.commit()
    
    # ===================
    # 権限管理
    # ===================
    
    async def get_all_permissions(self, db: Session) -> List[PermissionSummary]:
        """全権限一覧を取得"""
        
        permissions = db.query(UserPermission).filter(
            UserPermission.is_active == True
        ).order_by(
            UserPermission.category, 
            UserPermission.resource, 
            UserPermission.action
        ).all()
        
        return [PermissionSummary.from_orm(perm) for perm in permissions]
    
    async def get_role_permissions(
        self, 
        role: UserRole, 
        db: Session
    ) -> RolePermissionsResponse:
        """指定されたロールの権限一覧を取得"""
        
        role_permissions = db.query(UserRolePermission).filter(
            and_(
                UserRolePermission.role == role,
                UserRolePermission.is_granted == True
            )
        ).all()
        
        permission_ids = [rp.permission_id for rp in role_permissions]
        
        permissions = db.query(UserPermission).filter(
            and_(
                UserPermission.id.in_(permission_ids),
                UserPermission.is_active == True
            )
        ).order_by(
            UserPermission.category,
            UserPermission.resource,
            UserPermission.action
        ).all()
        
        return RolePermissionsResponse(
            role=role,
            permissions=[PermissionSummary.from_orm(perm) for perm in permissions],
            total=len(permissions)
        )
    
    async def check_user_permission(
        self, 
        user_id: int, 
        permission_code: str, 
        db: Session
    ) -> bool:
        """ユーザーの特定権限をチェック"""
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # スーパーユーザーは全権限を持つ
        if user.is_superuser:
            return True
        
        # 権限コードを取得
        permission = db.query(UserPermission).filter(
            and_(
                UserPermission.permission_code == permission_code,
                UserPermission.is_active == True
            )
        ).first()
        
        if not permission:
            return False
        
        # ロール権限をチェック
        role_permission = db.query(UserRolePermission).filter(
            and_(
                UserRolePermission.role == user.role,
                UserRolePermission.permission_id == permission.id,
                UserRolePermission.is_granted == True
            )
        ).first()
        
        return role_permission is not None
    
    async def check_user_resource_access(
        self, 
        user_id: int, 
        resource: str, 
        action: str, 
        db: Session
    ) -> bool:
        """ユーザーのリソースアクセス権限をチェック"""
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # スーパーユーザーは全権限を持つ
        if user.is_superuser:
            return True
        
        # リソース・アクションに対応する権限を取得
        permissions = db.query(UserPermission).filter(
            and_(
                UserPermission.resource == resource,
                UserPermission.action == action,
                UserPermission.is_active == True
            )
        ).all()
        
        if not permissions:
            return False
        
        # いずれかの権限を持っているかチェック
        for permission in permissions:
            role_permission = db.query(UserRolePermission).filter(
                and_(
                    UserRolePermission.role == user.role,
                    UserRolePermission.permission_id == permission.id,
                    UserRolePermission.is_granted == True
                )
            ).first()
            
            if role_permission:
                return True
        
        return False
    
    async def get_user_accessible_resources(
        self, 
        user_id: int, 
        db: Session
    ) -> Dict[str, List[str]]:
        """ユーザーがアクセス可能なリソース・アクション一覧を取得"""
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # スーパーユーザーは全リソースにアクセス可能
        if user.is_superuser:
            all_permissions = db.query(UserPermission).filter(
                UserPermission.is_active == True
            ).all()
        else:
            # ロール権限から取得
            role_permissions = db.query(UserRolePermission).filter(
                and_(
                    UserRolePermission.role == user.role,
                    UserRolePermission.is_granted == True
                )
            ).all()
            
            permission_ids = [rp.permission_id for rp in role_permissions]
            
            all_permissions = db.query(UserPermission).filter(
                and_(
                    UserPermission.id.in_(permission_ids),
                    UserPermission.is_active == True
                )
            ).all()
        
        # リソース別アクション一覧を作成
        resource_actions = {}
        for permission in all_permissions:
            if permission.resource:
                if permission.resource not in resource_actions:
                    resource_actions[permission.resource] = []
                
                if permission.action and permission.action not in resource_actions[permission.resource]:
                    resource_actions[permission.resource].append(permission.action)
        
        return resource_actions
    
    # ===================
    # MLMビジネス固有権限チェック
    # ===================
    
    async def can_manage_members(self, user_id: int, db: Session) -> bool:
        """会員管理権限チェック"""
        return await self.check_user_permission(user_id, "member.manage", db)
    
    async def can_view_members(self, user_id: int, db: Session) -> bool:
        """会員閲覧権限チェック"""
        return await self.check_user_permission(user_id, "member.view", db)
    
    async def can_manage_organization(self, user_id: int, db: Session) -> bool:
        """組織管理権限チェック"""
        return await self.check_user_permission(user_id, "organization.manage", db)
    
    async def can_calculate_rewards(self, user_id: int, db: Session) -> bool:
        """報酬計算権限チェック"""
        return await self.check_user_permission(user_id, "reward.calculate", db)
    
    async def can_export_payments(self, user_id: int, db: Session) -> bool:
        """決済CSV出力権限チェック"""
        return await self.check_user_permission(user_id, "payment.csv_export", db)
    
    async def can_export_gmo(self, user_id: int, db: Session) -> bool:
        """GMO CSV出力権限チェック"""
        return await self.check_user_permission(user_id, "payout.gmo_export", db)

# サービスインスタンス
permission_service = PermissionService()
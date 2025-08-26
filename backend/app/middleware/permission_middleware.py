# IROAS BOSS V2 - 権限チェックミドルウェア
# Phase 21対応・MLMビジネス要件準拠

from functools import wraps
from typing import List, Optional, Callable, Any
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.permission_service import permission_service
from app.api.endpoints.auth import get_current_user

def require_permissions(
    permissions: List[str], 
    require_all: bool = True,
    resource: Optional[str] = None,
    action: Optional[str] = None
):
    """
    権限チェックデコレータ
    
    Args:
        permissions: 必要な権限コードのリスト
        require_all: True=全権限が必要, False=いずれかの権限があればOK
        resource: リソース名（リソースベースチェック用）
        action: アクション名（リソースベースチェック用）
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 引数から current_user と db を取得
            current_user = None
            db = None
            
            # キーワード引数から取得
            for key, value in kwargs.items():
                if key == "current_user" and isinstance(value, User):
                    current_user = value
                elif key == "db" and isinstance(value, Session):
                    db = value
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="認証が必要です"
                )
            
            # スーパーユーザーは全権限を持つ
            if current_user.is_superuser:
                return await func(*args, **kwargs)
            
            # 権限チェック
            if permissions:
                user_permissions = []
                for permission in permissions:
                    has_permission = await permission_service.check_user_permission(
                        current_user.id, permission, db
                    )
                    if has_permission:
                        user_permissions.append(permission)
                
                if require_all:
                    # 全権限が必要
                    if len(user_permissions) != len(permissions):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="必要な権限がありません"
                        )
                else:
                    # いずれかの権限があればOK
                    if not user_permissions:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="必要な権限がありません"
                        )
            
            # リソースベースチェック
            if resource and action:
                has_access = await permission_service.check_user_resource_access(
                    current_user.id, resource, action, db
                )
                
                if not has_access:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"{resource}の{action}権限がありません"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# MLMビジネス固有の権限デコレータ
def require_member_management():
    """会員管理権限が必要"""
    return require_permissions(["member.manage"])

def require_member_view():
    """会員閲覧権限が必要"""
    return require_permissions(["member.view"])

def require_organization_management():
    """組織管理権限が必要"""
    return require_permissions(["organization.manage"])

def require_payment_management():
    """決済管理権限が必要"""
    return require_permissions(["payment.manage"])

def require_reward_management():
    """報酬管理権限が必要"""
    return require_permissions(["reward.manage"])

def require_reward_calculation():
    """報酬計算権限が必要"""
    return require_permissions(["reward.calculate"])

def require_payout_management():
    """支払管理権限が必要"""
    return require_permissions(["payout.manage"])

def require_gmo_export():
    """GMO CSV出力権限が必要"""
    return require_permissions(["payout.gmo_export"])

def require_data_management():
    """データ管理権限が必要"""
    return require_permissions(["data.manage"])

def require_admin():
    """管理者権限が必要（MLM管理者以上）"""
    return require_permissions(["user.manage"], require_all=False)

def require_system_admin():
    """システム管理者権限が必要"""
    return require_permissions(["system.admin"])

# 権限チェックヘルパー関数
async def check_member_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """会員アクセス権限チェック"""
    return await permission_service.can_view_members(current_user.id, db)

async def check_organization_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """組織アクセス権限チェック"""
    return await permission_service.check_user_permission(
        current_user.id, "organization.view", db
    )

async def check_payment_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """決済アクセス権限チェック"""
    return await permission_service.check_user_permission(
        current_user.id, "payment.view", db
    )

async def check_reward_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """報酬アクセス権限チェック"""
    return await permission_service.check_user_permission(
        current_user.id, "reward.view", db
    )

async def check_admin_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """管理者アクセス権限チェック"""
    return await permission_service.check_user_permission(
        current_user.id, "user.manage", db
    ) or current_user.is_superuser

# コンテキスト情報付きの権限チェック
class PermissionContext:
    """権限チェックコンテキスト"""
    
    def __init__(self, user: User, db: Session):
        self.user = user
        self.db = db
        self.permission_service = permission_service
    
    async def can_access_member(self, member_id: Optional[int] = None) -> bool:
        """会員アクセス権限（個別会員対応）"""
        base_permission = await self.permission_service.can_view_members(
            self.user.id, self.db
        )
        
        # 基本権限がない場合は拒否
        if not base_permission:
            return False
        
        # 管理権限がある場合は全会員にアクセス可能
        if await self.permission_service.can_manage_members(self.user.id, self.db):
            return True
        
        # 将来的に個別会員アクセス制御を実装する場合はここに追加
        return True
    
    async def can_modify_organization(self, target_member_id: Optional[int] = None) -> bool:
        """組織変更権限（特定会員対象）"""
        return await self.permission_service.can_manage_organization(
            self.user.id, self.db
        )
    
    async def can_export_data(self, data_type: str) -> bool:
        """データ出力権限（データタイプ別）"""
        type_permission_map = {
            "payment": "payment.csv_export",
            "gmo": "payout.gmo_export",
            "member": "data.export",
            "reward": "data.export"
        }
        
        permission_code = type_permission_map.get(data_type, "data.export")
        return await self.permission_service.check_user_permission(
            self.user.id, permission_code, self.db
        )
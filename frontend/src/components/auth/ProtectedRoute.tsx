import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth, UserRole } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: UserRole[];
  requiredPermissions?: string[];
  requireAll?: boolean; // true: 全権限が必要, false: いずれかがあればOK
  fallback?: React.ReactNode;
}

/**
 * 保護されたルートコンポーネント
 * Phase 21 MLM認証・権限管理完全準拠
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles,
  requiredPermissions,
  requireAll = true,
  fallback,
}) => {
  const { isAuthenticated, isLoading, user, hasRole, hasPermission } = useAuth();
  const location = useLocation();

  // 認証状態確認中
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          gap: 2,
        }}
      >
        <CircularProgress size={60} />
        <Typography variant="h6" color="text.secondary">
          認証状態を確認中...
        </Typography>
      </Box>
    );
  }

  // 未認証の場合はログインページにリダイレクト
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // ユーザー情報がない場合
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // ロール確認
  if (requiredRoles && requiredRoles.length > 0) {
    if (!hasRole(requiredRoles)) {
      return fallback || (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            gap: 2,
            textAlign: 'center',
            p: 3,
          }}
        >
          <Typography variant="h5" color="error.main" fontWeight="bold">
            アクセス権限がありません
          </Typography>
          <Typography variant="body1" color="text.secondary">
            このページにアクセスするには、以下のいずれかの権限が必要です:
          </Typography>
          <Box sx={{ mt: 1 }}>
            {requiredRoles.map((role) => (
              <Typography key={role} variant="body2" color="text.secondary">
                • {getRoleDisplayName(role)}
              </Typography>
            ))}
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            現在の権限: {getRoleDisplayName(user.role)}
          </Typography>
        </Box>
      );
    }
  }

  // 権限確認
  if (requiredPermissions && requiredPermissions.length > 0) {
    const hasRequiredPermissions = requireAll
      ? requiredPermissions.every((permission) => hasPermission(permission))
      : requiredPermissions.some((permission) => hasPermission(permission));

    if (!hasRequiredPermissions) {
      return fallback || (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            gap: 2,
            textAlign: 'center',
            p: 3,
          }}
        >
          <Typography variant="h5" color="error.main" fontWeight="bold">
            必要な権限がありません
          </Typography>
          <Typography variant="body1" color="text.secondary">
            このページにアクセスするには、以下の権限が必要です:
          </Typography>
          <Box sx={{ mt: 1 }}>
            {requiredPermissions.map((permission) => (
              <Typography key={permission} variant="body2" color="text.secondary">
                • {getPermissionDisplayName(permission)}
              </Typography>
            ))}
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            {requireAll ? '全ての権限' : 'いずれかの権限'}が必要です
          </Typography>
        </Box>
      );
    }
  }

  // アクセス許可
  return <>{children}</>;
};

/**
 * ロール表示名取得
 */
const getRoleDisplayName = (role: UserRole): string => {
  const roleNames: Record<UserRole, string> = {
    [UserRole.SUPER_ADMIN]: 'スーパー管理者',
    [UserRole.ADMIN]: '管理者',
    [UserRole.MLM_MANAGER]: 'MLM管理者',
    [UserRole.VIEWER]: '閲覧者',
  };
  return roleNames[role] || role;
};

/**
 * 権限表示名取得
 */
const getPermissionDisplayName = (permission: string): string => {
  const permissionNames: Record<string, string> = {
    // システム権限
    'system.admin': 'システム管理',
    'user.manage': 'ユーザー管理',
    'user.view': 'ユーザー閲覧',
    
    // 会員管理権限
    'member.manage': '会員管理',
    'member.view': '会員閲覧',
    'member.create': '会員作成',
    'member.edit': '会員編集',
    'member.delete': '会員削除',
    
    // 組織管理権限
    'organization.manage': '組織管理',
    'organization.view': '組織閲覧',
    'organization.sponsor_change': 'スポンサー変更',
    
    // 決済管理権限
    'payment.manage': '決済管理',
    'payment.view': '決済閲覧',
    'payment.csv_export': '決済CSV出力',
    'payment.result_import': '決済結果取込',
    
    // 報酬管理権限
    'reward.manage': '報酬管理',
    'reward.view': '報酬閲覧',
    'reward.calculate': '報酬計算',
    'reward.delete_history': '報酬履歴削除',
    
    // 支払管理権限
    'payout.manage': '支払管理',
    'payout.view': '支払閲覧',
    'payout.gmo_export': 'GMO CSV出力',
    'payout.confirm': '支払確定',
    
    // データ管理権限
    'data.manage': 'データ管理',
    'data.export': 'データ出力',
    'data.import': 'データ取込',
    'data.backup': 'バックアップ',
    
    // アクティビティ管理権限
    'activity.manage': '活動履歴管理',
    'activity.view': '活動履歴閲覧',
    
    // システム設定権限
    'settings.manage': 'システム設定管理',
    'settings.view': 'システム設定閲覧',
  };
  return permissionNames[permission] || permission;
};

export default ProtectedRoute;
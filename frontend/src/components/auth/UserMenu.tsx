import React, { useState } from 'react';
import {
  Box,
  Avatar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Divider,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Chip,
  Badge,
} from '@mui/material';
import {
  AccountCircle,
  Settings,
  Security,
  ExitToApp,
  AdminPanelSettings,
  Shield,
  History,
} from '@mui/icons-material';
import { useAuth, UserRole } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

/**
 * ユーザーメニューコンポーネント
 * Phase 21 MLM認証機能完全準拠
 */
const UserMenu: React.FC = () => {
  const { user, logout, hasRole, hasPermission } = useAuth();
  const navigate = useNavigate();

  // UI状態
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [logoutConfirmOpen, setLogoutConfirmOpen] = useState(false);
  const [logoutAllDevices, setLogoutAllDevices] = useState(false);

  const isMenuOpen = Boolean(anchorEl);

  // メニュー開閉
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // プロフィール表示
  const handleProfile = () => {
    handleMenuClose();
    navigate('/profile');
  };

  // セキュリティ設定表示
  const handleSecurity = () => {
    handleMenuClose();
    navigate('/security');
  };

  // 管理機能表示（管理者のみ）
  const handleAdmin = () => {
    handleMenuClose();
    navigate('/admin');
  };

  // アクセスログ表示（管理者のみ）
  const handleAccessLogs = () => {
    handleMenuClose();
    navigate('/admin/access-logs');
  };

  // ログアウト確認ダイアログ
  const handleLogoutClick = () => {
    handleMenuClose();
    setLogoutConfirmOpen(true);
  };

  const handleLogoutConfirm = async () => {
    try {
      await logout(logoutAllDevices);
      setLogoutConfirmOpen(false);
    } catch (error) {
      console.error('Logout failed:', error);
      // エラーが発生してもログアウト扱いとする
      setLogoutConfirmOpen(false);
    }
  };

  const handleLogoutCancel = () => {
    setLogoutConfirmOpen(false);
    setLogoutAllDevices(false);
  };

  // ロール表示名
  const getRoleDisplayName = (role: UserRole): string => {
    const roleNames: Record<UserRole, string> = {
      [UserRole.SUPER_ADMIN]: 'スーパー管理者',
      [UserRole.ADMIN]: '管理者',
      [UserRole.MLM_MANAGER]: 'MLM管理者',
      [UserRole.VIEWER]: '閲覧者',
    };
    return roleNames[role] || role;
  };

  // ロール色
  const getRoleColor = (role: UserRole) => {
    const roleColors: Record<UserRole, 'error' | 'warning' | 'info' | 'default'> = {
      [UserRole.SUPER_ADMIN]: 'error',
      [UserRole.ADMIN]: 'warning',
      [UserRole.MLM_MANAGER]: 'info',
      [UserRole.VIEWER]: 'default',
    };
    return roleColors[role] || 'default';
  };

  if (!user) return null;

  return (
    <>
      {/* ユーザー情報表示とメニュートリガー */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {/* MFA有効時のバッジ */}
        <Badge
          color="success"
          variant="dot"
          invisible={!user.mfa_enabled}
          sx={{ '& .MuiBadge-dot': { right: 2, top: 2 } }}
        >
          <Avatar
            sx={{
              width: 32,
              height: 32,
              bgcolor: 'primary.main',
              cursor: 'pointer',
              fontSize: '0.875rem',
            }}
            onClick={handleMenuOpen}
          >
            {user.display_name?.[0] || user.username[0]?.toUpperCase()}
          </Avatar>
        </Badge>

        {/* ユーザー名（デスクトップのみ表示） */}
        <Box
          sx={{
            display: { xs: 'none', md: 'flex' },
            flexDirection: 'column',
            alignItems: 'flex-start',
            cursor: 'pointer',
          }}
          onClick={handleMenuOpen}
        >
          <Typography variant="body2" fontWeight={500} noWrap>
            {user.display_name || user.username}
          </Typography>
          <Chip
            label={getRoleDisplayName(user.role)}
            color={getRoleColor(user.role)}
            size="small"
            sx={{ fontSize: '0.6rem', height: 18 }}
          />
        </Box>
      </Box>

      {/* ドロップダウンメニュー */}
      <Menu
        anchorEl={anchorEl}
        open={isMenuOpen}
        onClose={handleMenuClose}
        PaperProps={{
          elevation: 8,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            minWidth: 280,
            '& .MuiAvatar-root': {
              width: 32,
              height: 32,
              ml: -0.5,
              mr: 1,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        {/* ユーザー情報ヘッダー */}
        <Box sx={{ px: 2, py: 1.5, bgcolor: 'grey.50' }}>
          <Typography variant="subtitle2" fontWeight={600}>
            {user.display_name || user.username}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {user.email}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
            <Chip
              label={getRoleDisplayName(user.role)}
              color={getRoleColor(user.role)}
              size="small"
              sx={{ fontSize: '0.65rem' }}
            />
            {user.mfa_enabled && (
              <Chip
                label="MFA有効"
                color="success"
                size="small"
                icon={<Shield />}
                sx={{ fontSize: '0.65rem' }}
              />
            )}
          </Box>
        </Box>

        <Divider />

        {/* メニュー項目 */}
        <MenuItem onClick={handleProfile}>
          <ListItemIcon>
            <AccountCircle fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="プロフィール設定" />
        </MenuItem>

        <MenuItem onClick={handleSecurity}>
          <ListItemIcon>
            <Security fontSize="small" />
          </ListItemIcon>
          <ListItemText
            primary="セキュリティ設定"
            secondary={user.mfa_enabled ? 'MFA有効' : 'MFA無効'}
          />
        </MenuItem>

        {/* 管理者メニュー */}
        {hasRole([UserRole.SUPER_ADMIN, UserRole.ADMIN]) && (
          <>
            <Divider />
            <MenuItem onClick={handleAdmin}>
              <ListItemIcon>
                <AdminPanelSettings fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="管理者機能" />
            </MenuItem>

            {hasPermission('activity.view') && (
              <MenuItem onClick={handleAccessLogs}>
                <ListItemIcon>
                  <History fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="アクセスログ" />
              </MenuItem>
            )}
          </>
        )}

        <Divider />

        {/* ログアウト */}
        <MenuItem onClick={handleLogoutClick} sx={{ color: 'error.main' }}>
          <ListItemIcon sx={{ color: 'error.main' }}>
            <ExitToApp fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="ログアウト" />
        </MenuItem>
      </Menu>

      {/* ログアウト確認ダイアログ */}
      <Dialog open={logoutConfirmOpen} onClose={handleLogoutCancel}>
        <DialogTitle>ログアウトの確認</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            ログアウトしますか？
          </Typography>
          <Box sx={{ mt: 2 }}>
            <MenuItem
              onClick={() => setLogoutAllDevices(!logoutAllDevices)}
              sx={{ px: 0 }}
            >
              <input
                type="checkbox"
                checked={logoutAllDevices}
                onChange={(e) => setLogoutAllDevices(e.target.checked)}
                style={{ marginRight: 8 }}
              />
              <Typography variant="body2">
                すべてのデバイスからログアウトする
              </Typography>
            </MenuItem>
            <Typography variant="caption" color="text.secondary" sx={{ ml: 3 }}>
              他のデバイス・ブラウザのセッションも無効にします
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleLogoutCancel} color="primary">
            キャンセル
          </Button>
          <Button
            onClick={handleLogoutConfirm}
            color="error"
            variant="contained"
          >
            ログアウト
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default UserMenu;
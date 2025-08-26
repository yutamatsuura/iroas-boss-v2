import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Divider,
  Alert,
  Card,
  CardContent,
  Chip,
  Avatar,
  LinearProgress,
} from '@mui/material';
import {
  AccountCircle,
  Email,
  Badge,
  Save,
  Security,
  Shield,
} from '@mui/icons-material';
import { useAuth, UserRole } from '@/contexts/AuthContext';
import { authService } from '@/services/authService';

/**
 * プロフィール設定ページ
 * Phase 21 MLM認証機能準拠
 */
const Profile: React.FC = () => {
  const { user, updateUserInfo } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  // フォーム状態
  const [formData, setFormData] = useState({
    email: user?.email || '',
    full_name: user?.full_name || '',
    display_name: user?.display_name || '',
    phone: '',
  });

  // フォーム変更ハンドラ
  const handleChange = (field: keyof typeof formData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData(prev => ({ ...prev, [field]: event.target.value }));
    setMessage(null);
  };

  // プロフィール更新
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!user) return;

    setIsLoading(true);
    setMessage(null);

    try {
      await authService.updateCurrentUser({
        email: formData.email,
        full_name: formData.full_name || undefined,
        display_name: formData.display_name || undefined,
        phone: formData.phone || undefined,
      });

      await updateUserInfo();
      setMessage({ type: 'success', text: 'プロフィールを更新しました。' });
    } catch (error: any) {
      console.error('Profile update failed:', error);
      setMessage({
        type: 'error',
        text: error?.response?.data?.detail || 'プロフィールの更新に失敗しました。',
      });
    } finally {
      setIsLoading(false);
    }
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

  if (!user) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" color="error">
          ユーザー情報を取得できませんでした。
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
      {/* ページヘッダー */}
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        プロフィール設定
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        アカウント情報とプロフィールの設定
      </Typography>

      {/* メッセージ表示 */}
      {message && (
        <Alert severity={message.type} sx={{ mb: 3 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* アカウント概要 */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar
                sx={{
                  width: 80,
                  height: 80,
                  bgcolor: 'primary.main',
                  fontSize: '2rem',
                  mx: 'auto',
                  mb: 2,
                }}
              >
                {user.display_name?.[0] || user.username[0]?.toUpperCase()}
              </Avatar>
              
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                {user.display_name || user.username}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {user.email}
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 2 }}>
                <Chip
                  label={getRoleDisplayName(user.role)}
                  color={getRoleColor(user.role)}
                  icon={<Badge />}
                />
                
                {user.mfa_enabled && (
                  <Chip
                    label="MFA有効"
                    color="success"
                    icon={<Shield />}
                    size="small"
                  />
                )}
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  最終ログイン: {user.last_login_at ? new Date(user.last_login_at).toLocaleString('ja-JP') : '未記録'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  作成日: {new Date(user.created_at).toLocaleString('ja-JP')}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* プロフィール編集フォーム */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AccountCircle />
              プロフィール情報
            </Typography>

            {isLoading && <LinearProgress sx={{ mb: 2 }} />}

            <form onSubmit={handleSubmit}>
              <Grid container spacing={3}>
                {/* ユーザー名（編集不可） */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="ユーザー名"
                    value={user.username}
                    disabled
                    InputProps={{
                      startAdornment: <AccountCircle sx={{ mr: 1, color: 'text.secondary' }} />,
                    }}
                    helperText="ユーザー名は変更できません"
                  />
                </Grid>

                {/* メールアドレス */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="メールアドレス"
                    type="email"
                    value={formData.email}
                    onChange={handleChange('email')}
                    disabled={isLoading}
                    required
                    InputProps={{
                      startAdornment: <Email sx={{ mr: 1, color: 'text.secondary' }} />,
                    }}
                  />
                </Grid>

                {/* フルネーム */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="フルネーム"
                    value={formData.full_name}
                    onChange={handleChange('full_name')}
                    disabled={isLoading}
                  />
                </Grid>

                {/* 表示名 */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="表示名"
                    value={formData.display_name}
                    onChange={handleChange('display_name')}
                    disabled={isLoading}
                    helperText="システム内で表示される名前"
                  />
                </Grid>

                {/* 電話番号 */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="電話番号"
                    value={formData.phone}
                    onChange={handleChange('phone')}
                    disabled={isLoading}
                    placeholder="090-1234-5678"
                  />
                </Grid>

                {/* 役割（編集不可） */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="役割"
                    value={getRoleDisplayName(user.role)}
                    disabled
                    helperText="役割は管理者のみが変更できます"
                  />
                </Grid>

                {/* 保存ボタン */}
                <Grid item xs={12}>
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={isLoading}
                    startIcon={<Save />}
                    sx={{ minWidth: 120 }}
                  >
                    {isLoading ? '更新中...' : '保存'}
                  </Button>
                </Grid>
              </Grid>
            </form>
          </Paper>
        </Grid>

        {/* セキュリティ設定へのリンク */}
        <Grid item xs={12}>
          <Card sx={{ bgcolor: 'info.light', color: 'info.contrastText' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Security fontSize="large" />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" fontWeight="bold">
                    セキュリティ設定
                  </Typography>
                  <Typography variant="body2">
                    パスワード変更、多要素認証（MFA）、セッション管理
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => window.location.href = '/security'}
                >
                  設定する
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Profile;
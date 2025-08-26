import React, { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  InputAdornment,
  IconButton,
  FormControlLabel,
  Checkbox,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Login as LoginIcon,
  Security,
} from '@mui/icons-material';
import { useAuth } from '@/contexts/AuthContext';

interface LoginFormProps {
  onSuccess?: () => void;
}

/**
 * ログインフォームコンポーネント
 * Phase 21 MLM認証要件完全準拠
 */
const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const { login } = useAuth();
  
  // フォーム状態
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    mfaCode: '',
    rememberMe: true,
  });

  // UI状態
  const [showPassword, setShowPassword] = useState(false);
  const [showMFA, setShowMFA] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // フォーム変更ハンドラ
  const handleChange = (field: keyof typeof formData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (field === 'rememberMe') {
      setFormData(prev => ({ ...prev, [field]: event.target.checked }));
    } else {
      setFormData(prev => ({ ...prev, [field]: event.target.value }));
    }
    setError(null);
  };

  // パスワード表示切り替え
  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  // ログイン処理
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!formData.username.trim() || !formData.password.trim()) {
      setError('ユーザー名とパスワードを入力してください。');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await login(
        formData.username.trim(),
        formData.password,
        formData.mfaCode || undefined
      );
      
      // ログイン成功
      onSuccess?.();
    } catch (err: any) {
      console.error('Login failed:', err);
      
      // エラーハンドリング
      if (err?.response?.status === 202) {
        // MFA必須の場合
        setShowMFA(true);
        setError('多要素認証コードを入力してください。');
      } else if (err?.response?.status === 401) {
        setError('ユーザー名またはパスワードが正しくありません。');
      } else if (err?.response?.status === 423) {
        setError('アカウントがロックされています。しばらく待ってから再試行してください。');
      } else if (err?.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('ログインに失敗しました。ネットワーク接続を確認してください。');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        p: 2,
      }}
    >
      <Paper
        elevation={8}
        sx={{
          p: 4,
          width: '100%',
          maxWidth: 440,
          borderRadius: 2,
        }}
      >
        {/* ヘッダー */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Box
            sx={{
              width: 64,
              height: 64,
              borderRadius: 2,
              bgcolor: 'primary.main',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: 2,
            }}
          >
            <Typography variant="h4" color="white" fontWeight="bold">
              IB
            </Typography>
          </Box>
          
          <Typography variant="h5" fontWeight="bold" color="text.primary" gutterBottom>
            IROAS BOSS V2
          </Typography>
          
          <Typography variant="body2" color="text.secondary">
            MLM管理システムへログイン
          </Typography>
        </Box>

        {/* エラー表示 */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* ログインフォーム */}
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="ユーザー名 または メールアドレス"
            variant="outlined"
            value={formData.username}
            onChange={handleChange('username')}
            disabled={isLoading}
            autoComplete="username"
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LoginIcon color="action" />
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="パスワード"
            type={showPassword ? 'text' : 'password'}
            variant="outlined"
            value={formData.password}
            onChange={handleChange('password')}
            disabled={isLoading}
            autoComplete="current-password"
            sx={{ mb: 2 }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={handleTogglePasswordVisibility}
                    disabled={isLoading}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          {/* MFA入力欄（必要時のみ表示） */}
          {showMFA && (
            <>
              <Divider sx={{ my: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  多要素認証
                </Typography>
              </Divider>
              
              <TextField
                fullWidth
                label="認証コード（6桁）"
                variant="outlined"
                value={formData.mfaCode}
                onChange={handleChange('mfaCode')}
                disabled={isLoading}
                autoComplete="one-time-code"
                inputProps={{
                  maxLength: 6,
                  pattern: '[0-9]{6}',
                }}
                sx={{ mb: 2 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Security color="action" />
                    </InputAdornment>
                  ),
                }}
                helperText="認証アプリで生成された6桁のコードを入力してください"
              />
            </>
          )}

          {/* ログイン状態保持チェックボックス */}
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.rememberMe}
                onChange={handleChange('rememberMe')}
                disabled={isLoading}
                color="primary"
              />
            }
            label="ログイン状態を保持する"
            sx={{ mb: 3 }}
          />

          {/* ログインボタン */}
          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={isLoading}
            sx={{
              py: 1.5,
              fontSize: '1rem',
              fontWeight: 600,
              textTransform: 'none',
            }}
            startIcon={isLoading ? <CircularProgress size={20} /> : <LoginIcon />}
          >
            {isLoading ? 'ログイン中...' : 'ログイン'}
          </Button>
        </form>

        {/* フッター */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            MLMビジネス管理システム
          </Typography>
          <br />
          <Typography variant="caption" color="text.secondary">
            © 2025 IROAS. All rights reserved.
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default LoginForm;
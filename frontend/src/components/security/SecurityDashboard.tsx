import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Alert,
  Chip,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Security,
  Shield,
  Warning,
  CheckCircle,
  Error,
  Visibility,
  VpnKey,
  PhoneAndroid,
  History,
  AssignmentTurnedIn,
} from '@mui/icons-material';
import { useAuth, UserRole } from '@/contexts/AuthContext';
import { authService } from '@/services/authService';

interface SecurityRecommendation {
  priority: 'high' | 'medium' | 'low';
  category: string;
  title: string;
  description: string;
  action_url: string;
}

interface SecurityMetrics {
  passwordStrength: number;
  mfaEnabled: boolean;
  activeSessions: number;
  lastPasswordChange: string | null;
  recentFailedLogins: number;
  trustedDevices: number;
}

/**
 * セキュリティダッシュボードコンポーネント
 * Phase 21 MLM認証セキュリティ強化
 */
const SecurityDashboard: React.FC = () => {
  const { user, hasRole } = useAuth();
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [recommendations, setRecommendations] = useState<SecurityRecommendation[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [mfaDialogOpen, setMfaDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSecurityData();
  }, []);

  const loadSecurityData = async () => {
    try {
      setLoading(true);
      
      // セッション情報取得
      const sessionData = await authService.getSessions();
      setSessions(sessionData.sessions);
      
      // セキュリティメトリクス計算
      const calculatedMetrics: SecurityMetrics = {
        passwordStrength: calculatePasswordStrength(),
        mfaEnabled: user?.mfa_enabled || false,
        activeSessions: sessionData.sessions.length,
        lastPasswordChange: null, // 実装では取得
        recentFailedLogins: 0, // 実装では取得
        trustedDevices: sessionData.sessions.filter(s => s.device_info?.trusted).length,
      };
      setMetrics(calculatedMetrics);
      
      // セキュリティ推奨事項生成
      const generatedRecommendations = generateRecommendations(calculatedMetrics);
      setRecommendations(generatedRecommendations);
      
    } catch (err: any) {
      console.error('Failed to load security data:', err);
      setError('セキュリティ情報の取得に失敗しました。');
    } finally {
      setLoading(false);
    }
  };

  const calculatePasswordStrength = (): number => {
    // 実装では実際の強度計算
    return user?.username === 'admin' ? 85 : 70;
  };

  const generateRecommendations = (metrics: SecurityMetrics): SecurityRecommendation[] => {
    const recommendations: SecurityRecommendation[] = [];
    
    if (!metrics.mfaEnabled) {
      recommendations.push({
        priority: 'high',
        category: 'authentication',
        title: '多要素認証(MFA)を有効にする',
        description: 'アカウントセキュリティを大幅に向上させます',
        action_url: '/security/mfa'
      });
    }
    
    if (metrics.passwordStrength < 80) {
      recommendations.push({
        priority: 'medium',
        category: 'password',
        title: 'より強力なパスワードに変更する',
        description: '現在のパスワード強度は改善の余地があります',
        action_url: '/security/password'
      });
    }
    
    if (metrics.activeSessions > 5) {
      recommendations.push({
        priority: 'medium',
        category: 'sessions',
        title: '不要なセッションを削除する',
        description: `${metrics.activeSessions}個のアクティブセッションがあります`,
        action_url: '/security/sessions'
      });
    }
    
    return recommendations;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      default:
        return 'info';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <Error color="error" />;
      case 'medium':
        return <Warning color="warning" />;
      default:
        return <CheckCircle color="info" />;
    }
  };

  const handleMFASetup = () => {
    setMfaDialogOpen(true);
  };

  const handleSessionRevoke = async (sessionIds: number[]) => {
    try {
      await authService.revokeSessions({
        session_ids: sessionIds,
        reason: 'ユーザーによる手動削除'
      });
      
      await loadSecurityData(); // データ再読み込み
    } catch (err) {
      console.error('Failed to revoke sessions:', err);
      setError('セッションの削除に失敗しました。');
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6">セキュリティ情報を読み込み中...</Typography>
        <LinearProgress sx={{ mt: 2 }} />
      </Box>
    );
  }

  if (!user || !metrics) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          セキュリティ情報を取得できませんでした。
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      {/* ページヘッダー */}
      <Typography variant="h4" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Security />
        セキュリティダッシュボード
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        アカウントのセキュリティ状況と推奨事項
      </Typography>

      {/* エラー表示 */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* セキュリティメトリクス */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              セキュリティ状況
            </Typography>
            
            <Grid container spacing={2}>
              {/* MFA状態 */}
              <Grid item xs={12} sm={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Shield color={metrics.mfaEnabled ? 'success' : 'error'} />
                      <Typography variant="subtitle1" fontWeight="bold">
                        多要素認証
                      </Typography>
                    </Box>
                    <Chip
                      label={metrics.mfaEnabled ? '有効' : '無効'}
                      color={metrics.mfaEnabled ? 'success' : 'error'}
                      size="small"
                    />
                    {!metrics.mfaEnabled && (
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={handleMFASetup}
                        sx={{ mt: 1, display: 'block' }}
                      >
                        設定する
                      </Button>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* パスワード強度 */}
              <Grid item xs={12} sm={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <VpnKey />
                      <Typography variant="subtitle1" fontWeight="bold">
                        パスワード強度
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={metrics.passwordStrength}
                        sx={{ flex: 1, height: 8, borderRadius: 4 }}
                        color={metrics.passwordStrength >= 80 ? 'success' : 'warning'}
                      />
                      <Typography variant="body2" fontWeight="bold">
                        {metrics.passwordStrength}%
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* アクティブセッション */}
              <Grid item xs={12} sm={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <PhoneAndroid />
                      <Typography variant="subtitle1" fontWeight="bold">
                        アクティブセッション
                      </Typography>
                    </Box>
                    <Typography variant="h6" color="primary">
                      {metrics.activeSessions}個
                    </Typography>
                    <Button
                      size="small"
                      variant="outlined"
                      href="/security/sessions"
                      sx={{ mt: 1 }}
                    >
                      管理する
                    </Button>
                  </CardContent>
                </Card>
              </Grid>

              {/* セキュリティスコア */}
              <Grid item xs={12} sm={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <AssignmentTurnedIn />
                      <Typography variant="subtitle1" fontWeight="bold">
                        総合セキュリティスコア
                      </Typography>
                    </Box>
                    {(() => {
                      const score = Math.round(
                        (metrics.passwordStrength * 0.4) +
                        (metrics.mfaEnabled ? 30 : 0) +
                        (metrics.activeSessions <= 3 ? 20 : 10) +
                        (metrics.trustedDevices > 0 ? 10 : 0)
                      );
                      return (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={Math.min(score, 100)}
                            sx={{ flex: 1, height: 8, borderRadius: 4 }}
                            color={score >= 80 ? 'success' : score >= 60 ? 'warning' : 'error'}
                          />
                          <Typography variant="body2" fontWeight="bold">
                            {score}/100
                          </Typography>
                        </Box>
                      );
                    })()}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* セキュリティ推奨事項 */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              推奨事項
            </Typography>
            
            {recommendations.length === 0 ? (
              <Alert severity="success" icon={<CheckCircle />}>
                セキュリティ設定は良好です！
              </Alert>
            ) : (
              <List>
                {recommendations.map((rec, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemIcon>
                      {getPriorityIcon(rec.priority)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" fontWeight="bold">
                            {rec.title}
                          </Typography>
                          <Chip
                            size="small"
                            label={rec.priority}
                            color={getPriorityColor(rec.priority) as any}
                          />
                        </Box>
                      }
                      secondary={rec.description}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* 最近のセッション */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              最近のアクセス
            </Typography>
            
            <List>
              {sessions.slice(0, 5).map((session, index) => (
                <ListItem key={index} divider>
                  <ListItemIcon>
                    {session.is_current ? <Visibility color="success" /> : <History />}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2">
                          {session.device_info?.browser || 'Unknown Browser'}
                        </Typography>
                        {session.is_current && (
                          <Chip label="現在のセッション" size="small" color="success" />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          IP: {session.ip_address || 'Unknown'}
                        </Typography>
                        <Typography variant="caption" display="block">
                          最終アクセス: {session.last_used_at ? new Date(session.last_used_at).toLocaleString('ja-JP') : '未記録'}
                        </Typography>
                      </Box>
                    }
                  />
                  {!session.is_current && (
                    <Button
                      size="small"
                      color="error"
                      onClick={() => handleSessionRevoke([session.id])}
                    >
                      削除
                    </Button>
                  )}
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>

      {/* MFA設定ダイアログ */}
      <Dialog open={mfaDialogOpen} onClose={() => setMfaDialogOpen(false)}>
        <DialogTitle>多要素認証の設定</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            多要素認証を設定すると、ログイン時にスマートフォンアプリで生成される6桁のコードが必要になります。
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMfaDialogOpen(false)}>
            キャンセル
          </Button>
          <Button
            variant="contained"
            onClick={() => {
              setMfaDialogOpen(false);
              window.location.href = '/security/mfa';
            }}
          >
            設定する
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SecurityDashboard;
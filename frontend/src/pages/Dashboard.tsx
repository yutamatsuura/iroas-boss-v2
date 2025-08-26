import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  IconButton,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  TrendingUp,
  People,
  Payment,
  AccountBalance,
  MoreVert,
} from '@mui/icons-material';

/**
 * P-001: ダッシュボード
 * システム全体の状況を一目で把握
 */
const Dashboard: React.FC = () => {
  // 統計カードデータ（実際はAPIから取得）
  const statsCards = [
    {
      title: 'アクティブ会員数',
      value: '45',
      unit: '名',
      change: '+2',
      changeType: 'increase',
      icon: People,
      color: '#1e3a8a',
      bgColor: '#eff6ff',
    },
    {
      title: '今月の決済成功率',
      value: '93.3',
      unit: '%',
      change: '+1.2%',
      changeType: 'increase',
      icon: Payment,
      color: '#10b981',
      bgColor: '#f0fdf4',
    },
    {
      title: '今月の報酬総額',
      value: '1,250,000',
      unit: '円',
      change: '-5.0%',
      changeType: 'decrease',
      icon: TrendingUp,
      color: '#f59e0b',
      bgColor: '#fffbeb',
    },
    {
      title: '支払予定件数',
      value: '38',
      unit: '件',
      change: '0',
      changeType: 'neutral',
      icon: AccountBalance,
      color: '#3b82f6',
      bgColor: '#eff6ff',
    },
  ];

  // 直近のアクティビティデータ（実際はAPIから取得）
  const recentActivities = [
    { id: 1, action: '会員登録', member: '山田太郎', time: '10分前', status: 'success' },
    { id: 2, action: '決済処理', member: '佐藤花子', time: '30分前', status: 'success' },
    { id: 3, action: '退会処理', member: '鈴木一郎', time: '1時間前', status: 'warning' },
    { id: 4, action: '報酬計算', member: 'システム', time: '2時間前', status: 'info' },
    { id: 5, action: 'CSV出力', member: '管理者', time: '3時間前', status: 'success' },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      default: return 'info';
    }
  };

  return (
    <Box>
      {/* ページタイトル */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold" color="text.primary">
          ダッシュボード
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {new Date().toLocaleDateString('ja-JP', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            weekday: 'long'
          })}
        </Typography>
      </Box>

      {/* 統計カード */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {statsCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography color="text.secondary" variant="body2" gutterBottom>
                        {card.title}
                      </Typography>
                      <Typography variant="h4" fontWeight="bold" color="text.primary">
                        {card.value}
                        <Typography component="span" variant="body1" color="text.secondary" sx={{ ml: 0.5 }}>
                          {card.unit}
                        </Typography>
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Typography
                          variant="body2"
                          color={
                            card.changeType === 'increase' ? 'success.main' :
                            card.changeType === 'decrease' ? 'error.main' :
                            'text.secondary'
                          }
                        >
                          {card.change} 前月比
                        </Typography>
                      </Box>
                    </Box>
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        borderRadius: 2,
                        bgcolor: card.bgColor,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Icon sx={{ color: card.color }} />
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      <Grid container spacing={3}>
        {/* 決済状況 */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" fontWeight="600">
                  今月の決済状況
                </Typography>
                <IconButton size="small">
                  <MoreVert />
                </IconButton>
              </Box>
              
              {/* 決済方法別の進捗 */}
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    カード決済
                  </Typography>
                  <Typography variant="body2" fontWeight="500">
                    35/40件 成功
                  </Typography>
                </Box>
                <LinearProgress variant="determinate" value={87.5} sx={{ height: 8, borderRadius: 4 }} />
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    口座振替
                  </Typography>
                  <Typography variant="body2" fontWeight="500">
                    7/8件 成功
                  </Typography>
                </Box>
                <LinearProgress variant="determinate" value={87.5} sx={{ height: 8, borderRadius: 4 }} />
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    銀行振込
                  </Typography>
                  <Typography variant="body2" fontWeight="500">
                    2/2件 確認済
                  </Typography>
                </Box>
                <LinearProgress variant="determinate" value={100} sx={{ height: 8, borderRadius: 4 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* 直近のアクティビティ */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" fontWeight="600">
                  直近のアクティビティ
                </Typography>
                <IconButton size="small">
                  <MoreVert />
                </IconButton>
              </Box>
              
              <Box>
                {recentActivities.map((activity) => (
                  <Box
                    key={activity.id}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      py: 1.5,
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                      '&:last-child': {
                        borderBottom: 'none',
                      },
                    }}
                  >
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body2" fontWeight="500">
                        {activity.action}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {activity.member} • {activity.time}
                      </Typography>
                    </Box>
                    <Chip
                      label={activity.status}
                      size="small"
                      color={getStatusColor(activity.status)}
                      sx={{ height: 20, fontSize: '0.75rem' }}
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
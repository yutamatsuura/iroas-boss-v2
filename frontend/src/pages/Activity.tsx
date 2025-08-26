import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Button,
  Typography,
  Card,
  CardContent,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Chip,
  IconButton,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import {
  Refresh,
  Download,
  Visibility,
  FilterList,
  Warning,
  Error,
  Info,
  CheckCircle,
  Schedule,
  Search,
  ExpandMore,
  Security,
  Dashboard,
  Timeline,
  BugReport,
  SystemUpdate,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import {
  ActivityService,
  ActivityType,
  ActivityLevel,
  ActivityStatus,
  ActivityLog,
  ActivityStatistics,
  ActivitySearchParams,
  SecurityEvent,
} from '@/services/activityService';

/**
 * P-007: アクティビティログ
 * システムで実行された全操作の履歴を時系列で確認
 * セキュリティ・監査・操作追跡機能
 */
const Activity: React.FC = () => {
  // State管理
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [statistics, setStatistics] = useState<ActivityStatistics | null>(null);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  
  // 検索フィルター
  const [searchParams, setSearchParams] = useState<ActivitySearchParams>({
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10), // 7日前
    endDate: new Date().toISOString().slice(0, 10),
    page: 1,
    perPage: 50,
    sortBy: 'timestamp',
    sortOrder: 'desc',
  });
  
  // ダイアログ管理
  const [detailDialog, setDetailDialog] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState<ActivityLog | null>(null);
  const [filterDialog, setFilterDialog] = useState(false);
  const [exportDialog, setExportDialog] = useState(false);

  // モックデータ
  const mockActivities: ActivityLog[] = [
    {
      id: 1,
      timestamp: '2024-03-25T14:30:00Z',
      type: ActivityType.MEMBER_CREATE,
      level: ActivityLevel.INFO,
      status: ActivityStatus.SUCCESS,
      userId: 1,
      userName: '管理者',
      targetId: 123,
      targetType: 'member',
      targetName: '山田太郎',
      description: '新規会員登録を実行しました',
      details: { memberNumber: '0000123', email: 'yamada@example.com' },
      ipAddress: '192.168.1.100',
      userAgent: 'Mozilla/5.0...',
      duration: 1250,
    },
    {
      id: 2,
      timestamp: '2024-03-25T14:25:00Z',
      type: ActivityType.PAYMENT_CSV_EXPORT,
      level: ActivityLevel.INFO,
      status: ActivityStatus.SUCCESS,
      userId: 1,
      userName: '管理者',
      description: 'カード決済CSVファイルを出力しました',
      details: { fileName: 'card_payment_202403.csv', recordCount: 35 },
      ipAddress: '192.168.1.100',
      duration: 3500,
    },
    {
      id: 3,
      timestamp: '2024-03-25T14:20:00Z',
      type: ActivityType.SYSTEM_ERROR,
      level: ActivityLevel.ERROR,
      status: ActivityStatus.FAILED,
      userId: 1,
      userName: '管理者',
      description: 'データベース接続エラーが発生しました',
      errorMessage: 'Connection timeout after 5000ms',
      details: { query: 'SELECT * FROM members', timeout: 5000 },
      ipAddress: '192.168.1.100',
    },
  ];

  const mockStatistics: ActivityStatistics = {
    totalActivities: 1247,
    successCount: 1156,
    failedCount: 91,
    errorCount: 23,
    topActivityTypes: [
      { type: ActivityType.MEMBER_UPDATE, count: 234, percentage: 18.8 },
      { type: ActivityType.PAYMENT_CSV_EXPORT, count: 156, percentage: 12.5 },
      { type: ActivityType.REWARD_CALCULATION, count: 89, percentage: 7.1 },
    ],
    topUsers: [
      { userId: 1, userName: '管理者', activityCount: 892 },
      { userId: 2, userName: 'システム', activityCount: 355 },
    ],
    hourlyDistribution: Array.from({ length: 24 }, (_, hour) => ({
      hour,
      count: Math.floor(Math.random() * 50),
    })),
    dailyDistribution: Array.from({ length: 7 }, (_, i) => ({
      date: new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
      count: Math.floor(Math.random() * 200) + 50,
    })),
  };

  const mockSecurityEvents: SecurityEvent[] = [
    {
      id: 1,
      timestamp: '2024-03-25T14:30:00Z',
      eventType: 'LOGIN_FAILURE',
      severity: 'MEDIUM',
      userName: 'unknown',
      ipAddress: '203.0.113.10',
      userAgent: 'Unknown',
      description: '連続ログイン試行失敗（5回）',
      details: { attempts: 5, lastAttempt: '2024-03-25T14:30:00Z' },
      resolved: false,
    },
    {
      id: 2,
      timestamp: '2024-03-25T10:15:00Z',
      eventType: 'LOGIN_SUCCESS',
      severity: 'LOW',
      userId: 1,
      userName: '管理者',
      ipAddress: '192.168.1.100',
      userAgent: 'Mozilla/5.0...',
      description: '正常ログイン',
      details: {},
      resolved: true,
    },
  ];

  useEffect(() => {
    fetchActivityData();
  }, [searchParams]);

  // データ取得
  const fetchActivityData = async () => {
    setLoading(true);
    try {
      // 実際のAPI呼び出し（現在はモック）
      await new Promise(resolve => setTimeout(resolve, 500));
      setActivities(mockActivities);
      setStatistics(mockStatistics);
      setSecurityEvents(mockSecurityEvents);
    } catch (error) {
      console.error('アクティビティデータ取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  // 詳細表示
  const handleViewDetail = (activity: ActivityLog) => {
    setSelectedActivity(activity);
    setDetailDialog(true);
  };

  // CSV出力
  const handleExport = async () => {
    try {
      const fileName = `activity_log_${searchParams.startDate}_${searchParams.endDate}.csv`;
      console.log('アクティビティログCSV出力:', fileName);
      setExportDialog(false);
    } catch (error) {
      console.error('CSV出力エラー:', error);
    }
  };

  // レベル別色取得
  const getLevelColor = (level: ActivityLevel) => {
    switch (level) {
      case ActivityLevel.ERROR:
      case ActivityLevel.CRITICAL:
        return 'error';
      case ActivityLevel.WARN:
        return 'warning';
      case ActivityLevel.DEBUG:
        return 'default';
      default:
        return 'info';
    }
  };

  // ステータス別色取得
  const getStatusColor = (status: ActivityStatus) => {
    switch (status) {
      case ActivityStatus.SUCCESS:
        return 'success';
      case ActivityStatus.FAILED:
        return 'error';
      case ActivityStatus.IN_PROGRESS:
        return 'info';
      case ActivityStatus.CANCELLED:
        return 'warning';
      default:
        return 'default';
    }
  };

  // レベル別アイコン取得
  const getLevelIcon = (level: ActivityLevel) => {
    switch (level) {
      case ActivityLevel.ERROR:
      case ActivityLevel.CRITICAL:
        return <Error color="error" />;
      case ActivityLevel.WARN:
        return <Warning color="warning" />;
      case ActivityLevel.DEBUG:
        return <BugReport color="disabled" />;
      default:
        return <Info color="info" />;
    }
  };

  // DataGrid列定義
  const columns: GridColDef[] = [
    {
      field: 'timestamp',
      headerName: '日時',
      width: 180,
      renderCell: (params: GridRenderCellParams) => 
        new Date(params.value).toLocaleString('ja-JP'),
    },
    {
      field: 'level',
      headerName: 'レベル',
      width: 100,
      renderCell: (params: GridRenderCellParams) => (
        <Chip 
          icon={getLevelIcon(params.value)}
          label={params.value} 
          size="small" 
          color={getLevelColor(params.value)} 
        />
      ),
    },
    {
      field: 'type',
      headerName: 'タイプ',
      width: 180,
    },
    {
      field: 'userName',
      headerName: 'ユーザー',
      width: 120,
    },
    {
      field: 'description',
      headerName: '説明',
      width: 300,
      flex: 1,
    },
    {
      field: 'status',
      headerName: 'ステータス',
      width: 100,
      renderCell: (params: GridRenderCellParams) => (
        <Chip 
          label={params.value} 
          size="small" 
          color={getStatusColor(params.value)} 
        />
      ),
    },
    {
      field: 'actions',
      headerName: '操作',
      width: 80,
      sortable: false,
      renderCell: (params: GridRenderCellParams) => (
        <IconButton 
          size="small" 
          onClick={() => handleViewDetail(params.row)}
          title="詳細表示"
        >
          <Visibility fontSize="small" />
        </IconButton>
      ),
    },
  ];

  return (
    <Box>
      {/* ページヘッダー */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">
          アクティビティログ
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          システムで実行された全操作の履歴を時系列で確認
        </Typography>
      </Box>

      {/* 期間選択・アクション */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <DatePicker
              label="開始日"
              value={searchParams.startDate ? new Date(searchParams.startDate) : null}
              onChange={(newValue) => 
                setSearchParams({ 
                  ...searchParams, 
                  startDate: newValue?.toISOString().slice(0, 10) 
                })
              }
              slotProps={{ textField: { fullWidth: true, size: 'small' } }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <DatePicker
              label="終了日"
              value={searchParams.endDate ? new Date(searchParams.endDate) : null}
              onChange={(newValue) => 
                setSearchParams({ 
                  ...searchParams, 
                  endDate: newValue?.toISOString().slice(0, 10) 
                })
              }
              slotProps={{ textField: { fullWidth: true, size: 'small' } }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Button
              variant="outlined"
              startIcon={<FilterList />}
              onClick={() => setFilterDialog(true)}
              fullWidth
            >
              フィルター
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={() => setExportDialog(true)}
              fullWidth
            >
              CSV出力
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <IconButton onClick={fetchActivityData} color="primary" size="large">
              <Refresh />
            </IconButton>
          </Grid>
        </Grid>
      </Paper>

      {/* 統計カード */}
      {statistics && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  総アクティビティ数
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  {statistics.totalActivities.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  成功率
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="success.main">
                  {((statistics.successCount / statistics.totalActivities) * 100).toFixed(1)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  エラー件数
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="error.main">
                  {statistics.errorCount}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  失敗件数
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="warning.main">
                  {statistics.failedCount}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* タブ */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab icon={<Timeline />} label="アクティビティログ" />
          <Tab icon={<Security />} label="セキュリティイベント" />
          <Tab icon={<Dashboard />} label="統計・分析" />
        </Tabs>
      </Paper>

      {/* タブ1: アクティビティログ一覧 */}
      {tabValue === 0 && (
        <Paper sx={{ height: 600 }}>
          <DataGrid
            rows={activities}
            columns={columns}
            loading={loading}
            pageSizeOptions={[25, 50, 100]}
            sx={{
              '& .MuiDataGrid-cell': {
                borderBottom: '1px solid #e0e0e0',
              },
            }}
          />
        </Paper>
      )}

      {/* タブ2: セキュリティイベント */}
      {tabValue === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight="600" sx={{ mb: 2 }}>
            セキュリティイベント
          </Typography>
          
          {securityEvents.length === 0 ? (
            <Alert severity="info">
              現在、セキュリティイベントはありません。
            </Alert>
          ) : (
            <List>
              {securityEvents.map((event) => (
                <React.Fragment key={event.id}>
                  <ListItem>
                    <ListItemIcon>
                      <Security color={event.severity === 'HIGH' || event.severity === 'CRITICAL' ? 'error' : 'warning'} />
                    </ListItemIcon>
                    <ListItemText
                      primary={event.description}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            {new Date(event.timestamp).toLocaleString('ja-JP')} | 
                            IP: {event.ipAddress} | 
                            重要度: {event.severity}
                          </Typography>
                          {event.userName && (
                            <Typography variant="caption" color="text.secondary">
                              ユーザー: {event.userName}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    <Chip 
                      label={event.resolved ? '解決済み' : '未解決'} 
                      size="small" 
                      color={event.resolved ? 'success' : 'warning'} 
                    />
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          )}
        </Paper>
      )}

      {/* タブ3: 統計・分析 */}
      {tabValue === 2 && statistics && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="600" sx={{ mb: 2 }}>
                主要アクティビティタイプ
              </Typography>
              <List>
                {statistics.topActivityTypes.map((item, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={item.type}
                      secondary={`${item.count}件 (${item.percentage.toFixed(1)}%)`}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="600" sx={{ mb: 2 }}>
                アクティブユーザー
              </Typography>
              <List>
                {statistics.topUsers.map((user, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={user.userName}
                      secondary={`${user.activityCount}件のアクティビティ`}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="600" sx={{ mb: 2 }}>
                日次アクティビティ分布
              </Typography>
              {/* グラフ実装は省略（モック表示） */}
              <Typography variant="body2" color="text.secondary">
                日次アクティビティグラフ - 実装中
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* アクティビティ詳細ダイアログ */}
      <Dialog
        open={detailDialog}
        onClose={() => setDetailDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>アクティビティ詳細</DialogTitle>
        <DialogContent>
          {selectedActivity && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="ID"
                  value={selectedActivity.id}
                  InputProps={{ readOnly: true }}
                  size="small"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="日時"
                  value={new Date(selectedActivity.timestamp).toLocaleString('ja-JP')}
                  InputProps={{ readOnly: true }}
                  size="small"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="タイプ"
                  value={selectedActivity.type}
                  InputProps={{ readOnly: true }}
                  size="small"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="レベル"
                  value={selectedActivity.level}
                  InputProps={{ readOnly: true }}
                  size="small"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="説明"
                  value={selectedActivity.description}
                  InputProps={{ readOnly: true }}
                  size="small"
                  multiline
                  rows={2}
                />
              </Grid>
              {selectedActivity.details && (
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="詳細情報"
                    value={JSON.stringify(selectedActivity.details, null, 2)}
                    InputProps={{ readOnly: true }}
                    size="small"
                    multiline
                    rows={4}
                    sx={{ fontFamily: 'monospace' }}
                  />
                </Grid>
              )}
              {selectedActivity.errorMessage && (
                <Grid item xs={12}>
                  <Alert severity="error" sx={{ mt: 2 }}>
                    <strong>エラーメッセージ:</strong><br />
                    {selectedActivity.errorMessage}
                  </Alert>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialog(false)}>閉じる</Button>
        </DialogActions>
      </Dialog>

      {/* フィルターダイアログ */}
      <Dialog
        open={filterDialog}
        onClose={() => setFilterDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>フィルター設定</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth size="small">
                <InputLabel>アクティビティタイプ</InputLabel>
                <Select
                  value={searchParams.type || ''}
                  label="アクティビティタイプ"
                  onChange={(e) => setSearchParams({ 
                    ...searchParams, 
                    type: e.target.value as ActivityType 
                  })}
                >
                  <MenuItem value="">すべて</MenuItem>
                  {Object.values(ActivityType).map((type) => (
                    <MenuItem key={type} value={type}>{type}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth size="small">
                <InputLabel>レベル</InputLabel>
                <Select
                  value={searchParams.level || ''}
                  label="レベル"
                  onChange={(e) => setSearchParams({ 
                    ...searchParams, 
                    level: e.target.value as ActivityLevel 
                  })}
                >
                  <MenuItem value="">すべて</MenuItem>
                  {Object.values(ActivityLevel).map((level) => (
                    <MenuItem key={level} value={level}>{level}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="キーワード検索"
                value={searchParams.keyword || ''}
                onChange={(e) => setSearchParams({ 
                  ...searchParams, 
                  keyword: e.target.value 
                })}
                size="small"
                placeholder="説明文を検索"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSearchParams({ 
            ...searchParams, 
            type: undefined, 
            level: undefined, 
            keyword: undefined 
          })}>
            クリア
          </Button>
          <Button onClick={() => setFilterDialog(false)}>キャンセル</Button>
          <Button 
            variant="contained" 
            onClick={() => {
              setFilterDialog(false);
              fetchActivityData();
            }}
          >
            適用
          </Button>
        </DialogActions>
      </Dialog>

      {/* CSV出力ダイアログ */}
      <Dialog
        open={exportDialog}
        onClose={() => setExportDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>アクティビティログCSV出力</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            現在の検索条件でアクティビティログをCSV形式で出力します。
          </Alert>
          <Typography variant="body2" color="text.secondary">
            期間: {searchParams.startDate} ～ {searchParams.endDate}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialog(false)}>キャンセル</Button>
          <Button
            variant="contained"
            onClick={handleExport}
            startIcon={<Download />}
          >
            CSV出力
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Activity;
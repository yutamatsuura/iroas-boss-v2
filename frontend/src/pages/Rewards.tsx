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
  LinearProgress,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  PlayArrow,
  Refresh,
  Download,
  Error,
  CheckCircle,
  Schedule,
  ExpandMore,
  Visibility,
  Assessment,
  TrendingUp,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import {
  RewardsService,
  BonusType,
  CalculationStatus,
  MonthlyRewardSummary,
  BonusCalculationResult,
  CalculationHistory,
  Title,
} from '@/services/rewardsService';

/**
 * P-005: 報酬計算
 * 7種類のボーナス計算実行と計算結果確認
 * 要件定義: デイリー・タイトル・リファラル・パワー・メンテナンス・セールスアクティビティ・ロイヤルファミリー
 */
const Rewards: React.FC = () => {
  // State管理
  const [selectedMonth, setSelectedMonth] = useState<Date>(new Date());
  const [monthlySummary, setMonthlySummary] = useState<MonthlyRewardSummary | null>(null);
  const [calculationResults, setCalculationResults] = useState<BonusCalculationResult[]>([]);
  const [calculationHistory, setCalculationHistory] = useState<CalculationHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  
  // ダイアログ管理
  const [executeDialog, setExecuteDialog] = useState(false);
  const [selectedBonusTypes, setSelectedBonusTypes] = useState<BonusType[]>([]);
  const [calculationProgress, setCalculationProgress] = useState(0);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [progressDialog, setProgressDialog] = useState(false);

  // モックデータ
  const mockMonthlySummary: MonthlyRewardSummary = {
    targetMonth: selectedMonth.toISOString().slice(0, 7),
    totalRewards: 2450000,
    memberCount: 48,
    bonusBreakdown: {
      [BonusType.DAILY]: 800000,
      [BonusType.TITLE]: 600000,
      [BonusType.REFERRAL]: 450000,
      [BonusType.POWER]: 350000,
      [BonusType.MAINTENANCE]: 120000,
      [BonusType.SALES_ACTIVITY]: 80000,
      [BonusType.ROYAL_FAMILY]: 50000,
    },
    calculationStatus: {
      [BonusType.DAILY]: CalculationStatus.COMPLETED,
      [BonusType.TITLE]: CalculationStatus.COMPLETED,
      [BonusType.REFERRAL]: CalculationStatus.COMPLETED,
      [BonusType.POWER]: CalculationStatus.COMPLETED,
      [BonusType.MAINTENANCE]: CalculationStatus.NOT_STARTED,
      [BonusType.SALES_ACTIVITY]: CalculationStatus.NOT_STARTED,
      [BonusType.ROYAL_FAMILY]: CalculationStatus.NOT_STARTED,
    },
    lastCalculated: '2024-03-25T10:30:00Z',
  };

  const mockCalculationResults: BonusCalculationResult[] = [
    {
      id: 1,
      targetMonth: selectedMonth.toISOString().slice(0, 7),
      bonusType: BonusType.DAILY,
      totalAmount: 800000,
      memberCount: 48,
      status: CalculationStatus.COMPLETED,
      calculatedAt: '2024-03-25T10:15:00Z',
      calculatedBy: '管理者',
      details: [],
    },
    {
      id: 2,
      targetMonth: selectedMonth.toISOString().slice(0, 7),
      bonusType: BonusType.TITLE,
      totalAmount: 600000,
      memberCount: 12,
      status: CalculationStatus.COMPLETED,
      calculatedAt: '2024-03-25T10:20:00Z',
      calculatedBy: '管理者',
      details: [],
    },
  ];

  useEffect(() => {
    fetchRewardsData();
  }, [selectedMonth]);

  // データ取得
  const fetchRewardsData = async () => {
    setLoading(true);
    try {
      // 実際のAPI呼び出し（現在はモック）
      await new Promise(resolve => setTimeout(resolve, 500));
      setMonthlySummary(mockMonthlySummary);
      setCalculationResults(mockCalculationResults);
      
      // 計算履歴も取得
      const historyData: CalculationHistory[] = [
        {
          id: 1,
          targetMonth: '2024-03',
          executedAt: '2024-03-25T10:30:00Z',
          executedBy: '管理者',
          bonusTypes: [BonusType.DAILY, BonusType.TITLE, BonusType.REFERRAL, BonusType.POWER],
          totalAmount: 2200000,
          memberCount: 48,
          status: CalculationStatus.COMPLETED,
          executionTime: 245,
        },
      ];
      setCalculationHistory(historyData);
    } catch (error) {
      console.error('報酬データ取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  // ボーナス計算実行
  const handleExecuteCalculation = async () => {
    try {
      setProgressDialog(true);
      setCalculationProgress(0);
      
      // 実際のAPI呼び出し（現在は模擬）
      const progressInterval = setInterval(() => {
        setCalculationProgress(prev => {
          if (prev >= 100) {
            clearInterval(progressInterval);
            setTimeout(() => {
              setProgressDialog(false);
              fetchRewardsData();
            }, 1000);
            return 100;
          }
          return prev + 10;
        });
      }, 500);
      
    } catch (error) {
      console.error('計算実行エラー:', error);
      setProgressDialog(false);
    }
    setExecuteDialog(false);
  };

  // CSV出力
  const handleExport = async (bonusType?: BonusType) => {
    try {
      const targetMonthStr = selectedMonth.toISOString().slice(0, 7);
      const fileName = bonusType 
        ? `rewards_${bonusType}_${targetMonthStr.replace('-', '')}.csv`
        : `rewards_all_${targetMonthStr.replace('-', '')}.csv`;
      
      // 実際のAPI呼び出し（現在は模擬）
      console.log('CSV出力:', fileName);
      
    } catch (error) {
      console.error('CSV出力エラー:', error);
    }
  };

  // ステータス色取得
  const getStatusColor = (status: CalculationStatus) => {
    switch (status) {
      case CalculationStatus.COMPLETED:
        return 'success';
      case CalculationStatus.IN_PROGRESS:
        return 'info';
      case CalculationStatus.ERROR:
        return 'error';
      default:
        return 'default';
    }
  };

  // ステータスアイコン取得
  const getStatusIcon = (status: CalculationStatus) => {
    switch (status) {
      case CalculationStatus.COMPLETED:
        return <CheckCircle color="success" />;
      case CalculationStatus.IN_PROGRESS:
        return <Schedule color="info" />;
      case CalculationStatus.ERROR:
        return <Error color="error" />;
      default:
        return <Schedule color="disabled" />;
    }
  };

  return (
    <Box>
      {/* ページヘッダー */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">
          報酬計算
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          7種類のボーナス計算実行と計算結果確認
        </Typography>
      </Box>

      {/* 対象月選択 */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <DatePicker
              label="対象月"
              value={selectedMonth}
              onChange={(newValue) => newValue && setSelectedMonth(newValue)}
              views={['year', 'month']}
              format="yyyy年MM月"
              slotProps={{ textField: { fullWidth: true } }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={() => setExecuteDialog(true)}
              fullWidth
            >
              計算実行
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={() => handleExport()}
              fullWidth
            >
              全体CSV出力
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <IconButton onClick={fetchRewardsData} color="primary">
              <Refresh />
            </IconButton>
          </Grid>
        </Grid>
      </Paper>

      {/* 月次サマリーカード */}
      {monthlySummary && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  総報酬額
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="primary.main">
                  ¥{monthlySummary.totalRewards.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  対象会員数
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  {monthlySummary.memberCount}名
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  平均報酬額
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  ¥{Math.round(monthlySummary.totalRewards / monthlySummary.memberCount).toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  最終計算日時
                </Typography>
                <Typography variant="body1" fontWeight="bold">
                  {new Date(monthlySummary.lastCalculated).toLocaleDateString('ja-JP')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* タブ */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="ボーナス別詳細" />
          <Tab label="計算結果一覧" />
          <Tab label="計算履歴" />
        </Tabs>
      </Paper>

      {/* タブ1: ボーナス別詳細 */}
      {tabValue === 0 && monthlySummary && (
        <Grid container spacing={2}>
          {Object.entries(monthlySummary.bonusBreakdown).map(([bonusType, amount]) => {
            const status = monthlySummary.calculationStatus[bonusType as BonusType];
            return (
              <Grid item xs={12} md={6} key={bonusType}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getStatusIcon(status)}
                        <Typography variant="h6" fontWeight="600">
                          {bonusType}
                        </Typography>
                      </Box>
                      <Chip
                        label={status}
                        size="small"
                        color={getStatusColor(status)}
                      />
                    </Box>
                    
                    <Typography variant="h4" fontWeight="bold" color="primary.main" sx={{ mb: 1 }}>
                      ¥{amount.toLocaleString()}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                      <Button
                        size="small"
                        startIcon={<Visibility />}
                        onClick={() => console.log('詳細表示:', bonusType)}
                        disabled={status !== CalculationStatus.COMPLETED}
                      >
                        詳細
                      </Button>
                      <Button
                        size="small"
                        startIcon={<Download />}
                        onClick={() => handleExport(bonusType as BonusType)}
                        disabled={status !== CalculationStatus.COMPLETED}
                      >
                        CSV
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* タブ2: 計算結果一覧 */}
      {tabValue === 1 && (
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ボーナス種別</TableCell>
                  <TableCell align="right">総額</TableCell>
                  <TableCell align="right">対象者数</TableCell>
                  <TableCell>ステータス</TableCell>
                  <TableCell>計算日時</TableCell>
                  <TableCell>実行者</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {calculationResults.map((result) => (
                  <TableRow key={result.id}>
                    <TableCell>{result.bonusType}</TableCell>
                    <TableCell align="right">¥{result.totalAmount.toLocaleString()}</TableCell>
                    <TableCell align="right">{result.memberCount}名</TableCell>
                    <TableCell>
                      <Chip
                        label={result.status}
                        size="small"
                        color={getStatusColor(result.status)}
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(result.calculatedAt).toLocaleString('ja-JP')}
                    </TableCell>
                    <TableCell>{result.calculatedBy}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton size="small" title="詳細表示">
                          <Visibility fontSize="small" />
                        </IconButton>
                        <IconButton size="small" title="CSV出力">
                          <Download fontSize="small" />
                        </IconButton>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* タブ3: 計算履歴 */}
      {tabValue === 2 && (
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>対象月</TableCell>
                  <TableCell>実行日時</TableCell>
                  <TableCell>実行者</TableCell>
                  <TableCell>ボーナス種別</TableCell>
                  <TableCell align="right">総額</TableCell>
                  <TableCell align="right">対象者数</TableCell>
                  <TableCell>実行時間</TableCell>
                  <TableCell>ステータス</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {calculationHistory.map((history) => (
                  <TableRow key={history.id}>
                    <TableCell>{history.targetMonth}</TableCell>
                    <TableCell>
                      {new Date(history.executedAt).toLocaleString('ja-JP')}
                    </TableCell>
                    <TableCell>{history.executedBy}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {history.bonusTypes.map((type, index) => (
                          <Chip key={index} label={type} size="small" variant="outlined" />
                        ))}
                      </Box>
                    </TableCell>
                    <TableCell align="right">¥{history.totalAmount.toLocaleString()}</TableCell>
                    <TableCell align="right">{history.memberCount}名</TableCell>
                    <TableCell>{history.executionTime}秒</TableCell>
                    <TableCell>
                      <Chip
                        label={history.status}
                        size="small"
                        color={getStatusColor(history.status)}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* 計算実行ダイアログ */}
      <Dialog
        open={executeDialog}
        onClose={() => setExecuteDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          報酬計算実行 - {selectedMonth.getFullYear()}年{selectedMonth.getMonth() + 1}月
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            💡 計算実行には数分かかる場合があります。実行中は画面を閉じずにお待ちください。
          </Alert>
          
          <Typography variant="subtitle2" sx={{ mb: 2 }}>
            実行するボーナス種別を選択してください：
          </Typography>
          
          <Grid container spacing={1}>
            {Object.values(BonusType).map((bonusType) => (
              <Grid item xs={12} sm={6} key={bonusType}>
                <Card 
                  variant="outlined"
                  sx={{
                    cursor: 'pointer',
                    bgcolor: selectedBonusTypes.includes(bonusType) ? 'primary.light' : 'transparent',
                    '&:hover': { bgcolor: 'action.hover' },
                  }}
                  onClick={() => {
                    if (selectedBonusTypes.includes(bonusType)) {
                      setSelectedBonusTypes(prev => prev.filter(type => type !== bonusType));
                    } else {
                      setSelectedBonusTypes(prev => [...prev, bonusType]);
                    }
                  }}
                >
                  <CardContent sx={{ py: 1 }}>
                    <Typography variant="body2">{bonusType}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExecuteDialog(false)}>キャンセル</Button>
          <Button
            variant="contained"
            onClick={handleExecuteCalculation}
            disabled={selectedBonusTypes.length === 0}
            startIcon={<PlayArrow />}
          >
            計算実行
          </Button>
        </DialogActions>
      </Dialog>

      {/* 進捗ダイアログ */}
      <Dialog
        open={progressDialog}
        onClose={() => {}}
        maxWidth="sm"
        fullWidth
        disableEscapeKeyDown
      >
        <DialogTitle>報酬計算実行中</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              計算進捗: {calculationProgress}%
            </Typography>
            <LinearProgress variant="determinate" value={calculationProgress} />
          </Box>
          
          <Alert severity="warning">
            計算処理中です。画面を閉じずにお待ちください。
          </Alert>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default Rewards;
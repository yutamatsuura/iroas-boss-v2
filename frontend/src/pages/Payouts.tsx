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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import {
  Download,
  Refresh,
  Payment,
  CheckCircle,
  Error,
  Schedule,
  Visibility,
  Edit,
  Block,
  AttachMoney,
  AccountBalance,
  TrendingUp,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import {
  PayoutService,
  PayoutStatus,
  MonthlyPayoutSummary,
  MemberPayoutDetail,
  PaymentHistory,
  AccountType,
  CSVGenerateRequest,
  CarryForwardManagement,
} from '@/services/payoutService';

/**
 * P-006: 報酬支払管理
 * GMOネットバンク振込CSV生成と支払履歴管理
 * 要件定義: 最低支払金額5,000円、振込手数料会社負担
 */
const Payouts: React.FC = () => {
  // State管理
  const [selectedMonth, setSelectedMonth] = useState<Date>(new Date());
  const [monthlySummary, setMonthlySummary] = useState<MonthlyPayoutSummary | null>(null);
  const [memberDetails, setMemberDetails] = useState<MemberPayoutDetail[]>([]);
  const [paymentHistory, setPaymentHistory] = useState<PaymentHistory[]>([]);
  const [carryForwardData, setCarryForwardData] = useState<CarryForwardManagement[]>([]);
  const [loading, setLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  
  // ダイアログ管理
  const [csvDialog, setCsvDialog] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState(false);
  const [csvPreviewDialog, setCsvPreviewDialog] = useState(false);
  const [csvSettings, setCsvSettings] = useState<CSVGenerateRequest>({
    targetMonth: '',
    includeCarriedForward: true,
    minimumAmount: 5000,
    excludeMembers: [],
  });
  const [csvPreview, setCsvPreview] = useState<any>(null);

  // モックデータ
  const mockMonthlySummary: MonthlyPayoutSummary = {
    targetMonth: selectedMonth.toISOString().slice(0, 7),
    totalMembers: 48,
    payoutEligibleMembers: 35,
    belowMinimumMembers: 13,
    totalRewardAmount: 2450000,
    totalCarriedForward: 180000,
    totalPayoutAmount: 2630000,
    totalWithholdingTax: 263000,
    totalNetPayoutAmount: 2367000,
    averagePayoutAmount: 67629,
    csvGenerated: false,
    paymentCompleted: false,
  };

  const mockMemberDetails: MemberPayoutDetail[] = [
    {
      id: 1,
      memberId: 1,
      memberNumber: '0000001',
      memberName: '山田太郎',
      targetMonth: selectedMonth.toISOString().slice(0, 7),
      totalRewardAmount: 180000,
      carriedForwardAmount: 20000,
      currentMonthAmount: 160000,
      payoutAmount: 180000,
      withholdingTax: 18000,
      netPayoutAmount: 162000,
      status: PayoutStatus.PENDING,
      bankName: '三菱UFJ銀行',
      bankCode: '0005',
      branchName: '新宿支店',
      branchCode: '001',
      accountType: AccountType.SAVINGS,
      accountNumber: '1234567',
      accountHolderName: 'ヤマダタロウ',
    },
    {
      id: 2,
      memberId: 2,
      memberNumber: '0000002',
      memberName: '佐藤花子',
      targetMonth: selectedMonth.toISOString().slice(0, 7),
      totalRewardAmount: 95000,
      carriedForwardAmount: 15000,
      currentMonthAmount: 80000,
      payoutAmount: 95000,
      withholdingTax: 9500,
      netPayoutAmount: 85500,
      status: PayoutStatus.PENDING,
      bankName: 'みずほ銀行',
      bankCode: '0001',
      branchName: '東京支店',
      branchCode: '001',
      accountType: AccountType.SAVINGS,
      accountNumber: '7654321',
      accountHolderName: 'サトウハナコ',
    },
  ];

  useEffect(() => {
    fetchPayoutData();
  }, [selectedMonth]);

  // データ取得
  const fetchPayoutData = async () => {
    setLoading(true);
    try {
      // 実際のAPI呼び出し（現在はモック）
      await new Promise(resolve => setTimeout(resolve, 500));
      setMonthlySummary(mockMonthlySummary);
      setMemberDetails(mockMemberDetails);
      
      // 支払履歴データ
      const historyData: PaymentHistory[] = [
        {
          id: 1,
          targetMonth: '2024-02',
          csvFileName: 'gmo_transfer_202402.csv',
          totalMembers: 32,
          totalAmount: 2100000,
          paymentDate: '2024-03-15',
          confirmedBy: '管理者',
          status: PayoutStatus.COMPLETED,
          createdAt: '2024-03-01T09:00:00Z',
          processedAt: '2024-03-15T14:30:00Z',
        },
      ];
      setPaymentHistory(historyData);
      
    } catch (error) {
      console.error('支払データ取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  // CSV生成プレビュー
  const handleCSVPreview = async () => {
    try {
      const targetMonthStr = selectedMonth.toISOString().slice(0, 7);
      const request: CSVGenerateRequest = {
        ...csvSettings,
        targetMonth: targetMonthStr,
      };
      
      // 実際のAPI呼び出し（現在はモック）
      const previewData = {
        records: mockMemberDetails.filter(m => m.netPayoutAmount >= (csvSettings.minimumAmount || 5000)).map(member => ({
          bankCode: member.bankCode || '0000',
          branchCode: member.branchCode || '000',
          accountType: member.accountType === AccountType.SAVINGS ? '1' : '2',
          accountNumber: member.accountNumber || '0000000',
          recipientName: member.accountHolderName || member.memberName,
          transferAmount: member.netPayoutAmount,
          feeBearer: '',
          ediInfo: '',
        })),
        totalAmount: mockMemberDetails.reduce((sum, m) => sum + (m.netPayoutAmount >= (csvSettings.minimumAmount || 5000) ? m.netPayoutAmount : 0), 0),
        recordCount: mockMemberDetails.filter(m => m.netPayoutAmount >= (csvSettings.minimumAmount || 5000)).length,
        estimatedFees: 0,
      };
      
      setCsvPreview(previewData);
      setCsvPreviewDialog(true);
    } catch (error) {
      console.error('CSVプレビューエラー:', error);
    }
  };

  // CSV出力
  const handleCSVGenerate = async () => {
    try {
      const targetMonthStr = selectedMonth.toISOString().slice(0, 7);
      const fileName = `gmo_transfer_${targetMonthStr.replace('-', '')}.csv`;
      
      // 実際のAPI呼び出し（現在は模擬）
      console.log('GMOネットバンクCSV出力:', fileName);
      
      setCsvDialog(false);
      setCsvPreviewDialog(false);
      fetchPayoutData(); // データ再読み込み
    } catch (error) {
      console.error('CSV出力エラー:', error);
    }
  };

  // 支払確定
  const handlePaymentConfirm = async () => {
    try {
      const targetMonthStr = selectedMonth.toISOString().slice(0, 7);
      
      // 実際のAPI呼び出し（現在は模擬）
      console.log('支払確定処理:', targetMonthStr);
      
      setConfirmDialog(false);
      fetchPayoutData();
    } catch (error) {
      console.error('支払確定エラー:', error);
    }
  };

  // ステータス色取得
  const getStatusColor = (status: PayoutStatus) => {
    switch (status) {
      case PayoutStatus.COMPLETED:
        return 'success';
      case PayoutStatus.PROCESSING:
        return 'info';
      case PayoutStatus.FAILED:
        return 'error';
      case PayoutStatus.CANCELLED:
        return 'warning';
      default:
        return 'default';
    }
  };

  // DataGrid列定義（会員別支払詳細）
  const memberColumns: GridColDef[] = [
    { field: 'memberNumber', headerName: '会員番号', width: 120 },
    { field: 'memberName', headerName: '氏名', width: 150 },
    {
      field: 'totalRewardAmount',
      headerName: '総報酬額',
      width: 120,
      align: 'right',
      renderCell: (params: GridRenderCellParams) => `¥${params.value.toLocaleString()}`,
    },
    {
      field: 'carriedForwardAmount',
      headerName: '繰越額',
      width: 120,
      align: 'right',
      renderCell: (params: GridRenderCellParams) => `¥${params.value.toLocaleString()}`,
    },
    {
      field: 'netPayoutAmount',
      headerName: '実支払額',
      width: 120,
      align: 'right',
      renderCell: (params: GridRenderCellParams) => `¥${params.value.toLocaleString()}`,
    },
    {
      field: 'status',
      headerName: 'ステータス',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Chip label={params.value} size="small" color={getStatusColor(params.value)} />
      ),
    },
    {
      field: 'bankName',
      headerName: '銀行名',
      width: 150,
    },
    {
      field: 'accountNumber',
      headerName: '口座番号',
      width: 120,
    },
    {
      field: 'actions',
      headerName: '操作',
      width: 120,
      sortable: false,
      renderCell: (params: GridRenderCellParams) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton size="small" title="詳細表示">
            <Visibility fontSize="small" />
          </IconButton>
          <IconButton size="small" title="編集">
            <Edit fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  return (
    <Box>
      {/* ページヘッダー */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">
          報酬支払管理
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          GMOネットバンク振込CSV生成と支払履歴管理
        </Typography>
      </Box>

      {/* 対象月選択・アクション */}
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
              startIcon={<Download />}
              onClick={() => setCsvDialog(true)}
              fullWidth
            >
              CSV生成
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="outlined"
              startIcon={<Payment />}
              onClick={() => setConfirmDialog(true)}
              disabled={!monthlySummary?.csvGenerated}
              fullWidth
            >
              支払確定
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <IconButton onClick={fetchPayoutData} color="primary">
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
                  総支払額
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="primary.main">
                  ¥{monthlySummary.totalNetPayoutAmount.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  支払対象者
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="success.main">
                  {monthlySummary.payoutEligibleMembers}名
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  / {monthlySummary.totalMembers}名中
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  平均支払額
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  ¥{Math.round(monthlySummary.averagePayoutAmount).toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  源泉徴収税
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="warning.main">
                  ¥{monthlySummary.totalWithholdingTax.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* 要件アラート */}
      <Alert severity="info" sx={{ mb: 3 }}>
        💼 要件: 最低支払金額5,000円、振込手数料会社負担、GMOネットバンク対応フォーマット
      </Alert>

      {/* タブ */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="会員別支払詳細" />
          <Tab label="繰越管理" />
          <Tab label="支払履歴" />
        </Tabs>
      </Paper>

      {/* タブ1: 会員別支払詳細 */}
      {tabValue === 0 && (
        <Paper sx={{ height: 400 }}>
          <DataGrid
            rows={memberDetails}
            columns={memberColumns}
            loading={loading}
            pageSizeOptions={[10, 25, 50]}
            checkboxSelection
            disableRowSelectionOnClick
            sx={{
              '& .MuiDataGrid-cell': {
                borderBottom: '1px solid #e0e0e0',
              },
            }}
          />
        </Paper>
      )}

      {/* タブ2: 繰越管理 */}
      {tabValue === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight="600" sx={{ mb: 2 }}>
            繰越金管理（5,000円未満の場合自動繰越）
          </Typography>
          
          <Alert severity="warning" sx={{ mb: 2 }}>
            最低支払金額に達しない会員: {monthlySummary?.belowMinimumMembers}名
          </Alert>
          
          {/* 繰越管理テーブルは実装省略（モック表示） */}
          <Typography variant="body2" color="text.secondary">
            繰越管理詳細テーブル - 実装中
          </Typography>
        </Paper>
      )}

      {/* タブ3: 支払履歴 */}
      {tabValue === 2 && (
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>対象月</TableCell>
                  <TableCell>支払日</TableCell>
                  <TableCell>CSVファイル名</TableCell>
                  <TableCell align="right">対象者数</TableCell>
                  <TableCell align="right">支払額</TableCell>
                  <TableCell>実行者</TableCell>
                  <TableCell>ステータス</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paymentHistory.map((history) => (
                  <TableRow key={history.id}>
                    <TableCell>{history.targetMonth}</TableCell>
                    <TableCell>
                      {new Date(history.paymentDate).toLocaleDateString('ja-JP')}
                    </TableCell>
                    <TableCell>{history.csvFileName}</TableCell>
                    <TableCell align="right">{history.totalMembers}名</TableCell>
                    <TableCell align="right">¥{history.totalAmount.toLocaleString()}</TableCell>
                    <TableCell>{history.confirmedBy}</TableCell>
                    <TableCell>
                      <Chip
                        label={history.status}
                        size="small"
                        color={getStatusColor(history.status)}
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" title="詳細表示">
                        <Visibility fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* CSV生成ダイアログ */}
      <Dialog
        open={csvDialog}
        onClose={() => setCsvDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          GMOネットバンクCSV生成 - {selectedMonth.getFullYear()}年{selectedMonth.getMonth() + 1}月
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            GMOネットバンクの一括振込機能対応フォーマットでCSVを出力します
          </Alert>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="最低支払金額"
                type="number"
                value={csvSettings.minimumAmount}
                onChange={(e) => setCsvSettings({
                  ...csvSettings,
                  minimumAmount: Number(e.target.value),
                })}
                InputProps={{
                  startAdornment: <Typography>¥</Typography>,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={csvSettings.includeCarriedForward}
                    onChange={(e) => setCsvSettings({
                      ...csvSettings,
                      includeCarriedForward: e.target.checked,
                    })}
                  />
                }
                label="繰越金を含める"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCsvDialog(false)}>キャンセル</Button>
          <Button
            variant="outlined"
            onClick={handleCSVPreview}
            startIcon={<Visibility />}
          >
            プレビュー
          </Button>
          <Button
            variant="contained"
            onClick={handleCSVGenerate}
            startIcon={<Download />}
          >
            CSV生成
          </Button>
        </DialogActions>
      </Dialog>

      {/* CSVプレビューダイアログ */}
      <Dialog
        open={csvPreviewDialog}
        onClose={() => setCsvPreviewDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          CSVプレビュー
        </DialogTitle>
        <DialogContent>
          {csvPreview && (
            <Box>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={4}>
                  <Typography variant="body2">対象件数: {csvPreview.recordCount}件</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="body2">総金額: ¥{csvPreview.totalAmount.toLocaleString()}</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="body2">手数料: 無料（会社負担）</Typography>
                </Grid>
              </Grid>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                CSVフォーマットプレビュー（最初の5件のみ表示）:
              </Typography>
              
              <Paper variant="outlined" sx={{ p: 2, bgcolor: '#f5f5f5', fontFamily: 'monospace', fontSize: '0.8rem' }}>
                {csvPreview.records.slice(0, 5).map((record: any, index: number) => (
                  <Box key={index}>
                    {record.bankCode},{record.branchCode},{record.accountType},{record.accountNumber},{record.recipientName},{record.transferAmount},,
                  </Box>
                ))}
                {csvPreview.records.length > 5 && (
                  <Typography variant="caption" color="text.secondary">
                    ... 他 {csvPreview.records.length - 5} 件
                  </Typography>
                )}
              </Paper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCsvPreviewDialog(false)}>閉じる</Button>
          <Button
            variant="contained"
            onClick={handleCSVGenerate}
            startIcon={<Download />}
          >
            CSV生成
          </Button>
        </DialogActions>
      </Dialog>

      {/* 支払確定ダイアログ */}
      <Dialog
        open={confirmDialog}
        onClose={() => setConfirmDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>支払確定</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            支払確定を実行すると、対象月の支払処理が完了します。
          </Alert>
          
          <TextField
            fullWidth
            label="支払日"
            type="date"
            margin="normal"
            InputLabelProps={{ shrink: true }}
          />
          
          <TextField
            fullWidth
            label="備考"
            margin="normal"
            multiline
            rows={2}
            placeholder="支払確定に関する備考があれば記入"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog(false)}>キャンセル</Button>
          <Button
            variant="contained"
            color="warning"
            onClick={handlePaymentConfirm}
            startIcon={<CheckCircle />}
          >
            支払確定
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Payouts;
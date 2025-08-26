import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Typography,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tab,
  Tabs,
  Grid,
  Alert,
  LinearProgress,
  Card,
  CardContent,
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { DatePicker } from '@mui/x-date-pickers';
import {
  Download,
  Upload,
  Refresh,
  Add,
  Edit,
  Delete,
  Warning,
  CheckCircle,
  Error,
  Schedule,
} from '@mui/icons-material';
import {
  PaymentService,
  PaymentTarget,
  PaymentResult,
  ManualPaymentRecord,
  PaymentMethod,
  PaymentStatus,
  MonthlyPaymentSummary,
  PaymentExportRequest,
} from '@/services/paymentService';

/**
 * P-004: 決済管理
 * Univapay CSV出力、決済結果取込、手動決済記録を統合
 * 要件定義書: 4種類の決済方法対応、CSV連携、手動記録
 */
const Payments: React.FC = () => {
  // State管理
  const [currentTab, setCurrentTab] = useState(0);
  const [selectedMonth, setSelectedMonth] = useState<Date>(new Date());
  const [loading, setLoading] = useState(false);
  
  // データState
  const [paymentTargets, setPaymentTargets] = useState<PaymentTarget[]>([]);
  const [paymentResults, setPaymentResults] = useState<PaymentResult[]>([]);
  const [manualRecords, setManualRecords] = useState<ManualPaymentRecord[]>([]);
  const [monthlySummary, setMonthlySummary] = useState<MonthlyPaymentSummary | null>(null);
  
  // ダイアログState
  const [exportDialog, setExportDialog] = useState(false);
  const [importDialog, setImportDialog] = useState(false);
  const [manualRecordDialog, setManualRecordDialog] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<ManualPaymentRecord | null>(null);

  // データ取得
  const fetchData = async () => {
    setLoading(true);
    try {
      const monthStr = selectedMonth.toISOString().slice(0, 7);
      
      // モックデータ（実際のAPIコール）
      const mockSummary: MonthlyPaymentSummary = {
        month: monthStr,
        cardPayment: {
          totalTargets: 40,
          successCount: 35,
          failedCount: 3,
          pendingCount: 2,
          successRate: 87.5,
          totalAmount: 2000000,
          successAmount: 1750000,
          failedAmount: 150000,
        },
        bankTransfer: {
          totalTargets: 8,
          successCount: 7,
          failedCount: 1,
          pendingCount: 0,
          successRate: 87.5,
          totalAmount: 400000,
          successAmount: 350000,
          failedAmount: 50000,
        },
        manualPayments: {
          bankDeposit: {
            totalTargets: 2,
            successCount: 2,
            failedCount: 0,
            pendingCount: 0,
            successRate: 100,
            totalAmount: 100000,
            successAmount: 100000,
            failedAmount: 0,
          },
          infocart: {
            totalTargets: 0,
            successCount: 0,
            failedCount: 0,
            pendingCount: 0,
            successRate: 0,
            totalAmount: 0,
            successAmount: 0,
            failedAmount: 0,
          },
        },
        overall: {
          totalTargets: 50,
          successCount: 44,
          failedCount: 4,
          pendingCount: 2,
          successRate: 88.0,
          totalAmount: 2500000,
          successAmount: 2200000,
          failedAmount: 200000,
        },
      };

      const mockTargets: PaymentTarget[] = [
        {
          id: 1,
          memberNumber: '0000001',
          memberName: '山田太郎',
          paymentMethod: PaymentMethod.CARD,
          amount: 50000,
          plan: 'ヒーロープラン',
          targetMonth: monthStr,
          status: PaymentStatus.SUCCESS,
          createdAt: '2024-12-01',
          processedAt: '2024-12-02',
        },
        {
          id: 2,
          memberNumber: '0000002',
          memberName: '佐藤花子',
          paymentMethod: PaymentMethod.BANK_TRANSFER,
          amount: 50000,
          plan: 'ヒーロープラン',
          targetMonth: monthStr,
          status: PaymentStatus.FAILED,
          createdAt: '2024-12-01',
          errorMessage: '口座残高不足',
        },
      ];

      const mockResults: PaymentResult[] = [
        {
          id: 1,
          memberNumber: '0000001',
          memberName: '山田太郎',
          paymentMethod: PaymentMethod.CARD,
          amount: 50000,
          status: PaymentStatus.SUCCESS,
          paymentDate: '2024-12-02',
          transactionId: 'TXN123456',
          csvFileName: 'IPScardresult_20241202.csv',
          importedAt: '2024-12-03',
        },
      ];

      const mockManualRecords: ManualPaymentRecord[] = [
        {
          id: 1,
          memberNumber: '0000003',
          memberName: '田中次郎',
          paymentMethod: PaymentMethod.BANK_DEPOSIT,
          amount: 50000,
          paymentDate: '2024-12-01',
          confirmedBy: '管理者',
          notes: '銀行振込確認済み',
          receiptNumber: 'BANK-001',
          createdAt: '2024-12-01',
        },
      ];

      setMonthlySummary(mockSummary);
      setPaymentTargets(mockTargets);
      setPaymentResults(mockResults);
      setManualRecords(mockManualRecords);
    } catch (error) {
      console.error('決済データ取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedMonth]);

  // CSV出力処理
  const handleExport = async (exportType: PaymentMethod) => {
    try {
      const request: PaymentExportRequest = {
        targetMonth: selectedMonth.toISOString().slice(0, 7),
        paymentMethod: exportType,
        includePendingOnly: true,
      };
      
      const blob = await PaymentService.exportPaymentTargets(request);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      const fileName = exportType === PaymentMethod.CARD 
        ? `card_payment_${selectedMonth.toISOString().slice(0, 7).replace('-', '')}.csv`
        : `bank_transfer_${selectedMonth.toISOString().slice(0, 7).replace('-', '')}.csv`;
      
      a.download = fileName;
      a.click();
      setExportDialog(false);
    } catch (error) {
      console.error('CSV出力エラー:', error);
    }
  };

  // CSV取込処理
  const handleImport = (paymentMethod: PaymentMethod) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    input.onchange = async (e: any) => {
      const file = e.target.files[0];
      if (file) {
        try {
          const result = await PaymentService.importPaymentResults({
            file,
            paymentMethod,
          });
          alert(`取込完了: 成功 ${result.successCount}件, 失敗 ${result.failedCount}件`);
          fetchData();
        } catch (error) {
          console.error('CSV取込エラー:', error);
        }
      }
    };
    input.click();
  };

  // ステータス表示用の色とアイコン
  const getStatusDisplay = (status: PaymentStatus) => {
    switch (status) {
      case PaymentStatus.SUCCESS:
        return { color: 'success', icon: <CheckCircle fontSize="small" /> };
      case PaymentStatus.FAILED:
        return { color: 'error', icon: <Error fontSize="small" /> };
      case PaymentStatus.PENDING:
        return { color: 'warning', icon: <Schedule fontSize="small" /> };
      default:
        return { color: 'default', icon: <Warning fontSize="small" /> };
    }
  };

  // DataGrid列定義
  const targetColumns: GridColDef[] = [
    { field: 'memberNumber', headerName: '会員番号', width: 120 },
    { field: 'memberName', headerName: '氏名', width: 150 },
    { field: 'paymentMethod', headerName: '決済方法', width: 120 },
    { field: 'amount', headerName: '金額', width: 100, valueFormatter: (params) => `¥${params.value?.toLocaleString()}` },
    { field: 'plan', headerName: 'プラン', width: 120 },
    {
      field: 'status',
      headerName: 'ステータス',
      width: 120,
      renderCell: (params: GridRenderCellParams) => {
        const { color, icon } = getStatusDisplay(params.value);
        return (
          <Chip
            label={params.value}
            size="small"
            color={color as any}
            icon={icon}
          />
        );
      },
    },
    { field: 'createdAt', headerName: '作成日', width: 120 },
    { field: 'errorMessage', headerName: 'エラー', width: 200 },
  ];

  const resultColumns: GridColDef[] = [
    { field: 'memberNumber', headerName: '会員番号', width: 120 },
    { field: 'memberName', headerName: '氏名', width: 150 },
    { field: 'paymentMethod', headerName: '決済方法', width: 120 },
    { field: 'amount', headerName: '金額', width: 100, valueFormatter: (params) => `¥${params.value?.toLocaleString()}` },
    {
      field: 'status',
      headerName: 'ステータス',
      width: 120,
      renderCell: (params: GridRenderCellParams) => {
        const { color, icon } = getStatusDisplay(params.value);
        return (
          <Chip
            label={params.value}
            size="small"
            color={color as any}
            icon={icon}
          />
        );
      },
    },
    { field: 'paymentDate', headerName: '決済日', width: 120 },
    { field: 'transactionId', headerName: 'トランザクションID', width: 150 },
    { field: 'csvFileName', headerName: 'CSVファイル名', width: 200 },
  ];

  const manualColumns: GridColDef[] = [
    { field: 'memberNumber', headerName: '会員番号', width: 120 },
    { field: 'memberName', headerName: '氏名', width: 150 },
    { field: 'paymentMethod', headerName: '決済方法', width: 120 },
    { field: 'amount', headerName: '金額', width: 100, valueFormatter: (params) => `¥${params.value?.toLocaleString()}` },
    { field: 'paymentDate', headerName: '決済日', width: 120 },
    { field: 'confirmedBy', headerName: '確認者', width: 100 },
    { field: 'receiptNumber', headerName: '受領番号', width: 120 },
    { field: 'notes', headerName: '備考', width: 200 },
    {
      field: 'actions',
      headerName: '操作',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton
            size="small"
            color="primary"
            onClick={() => {
              setSelectedRecord(params.row);
              setManualRecordDialog(true);
            }}
          >
            <Edit fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            color="error"
            onClick={() => handleDeleteManualRecord(params.row.id)}
          >
            <Delete fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  const handleDeleteManualRecord = async (id: number) => {
    if (window.confirm('この手動決済記録を削除しますか？')) {
      try {
        await PaymentService.deleteManualPaymentRecord(id);
        fetchData();
      } catch (error) {
        console.error('手動決済記録削除エラー:', error);
      }
    }
  };

  return (
    <Box>
      {/* ページヘッダー */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">
          決済管理
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Univapay CSV出力、決済結果取込、手動決済記録を統合
        </Typography>
      </Box>

      {/* 月選択・アクションボタン */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <DatePicker
              label="対象月"
              value={selectedMonth}
              onChange={(newDate) => newDate && setSelectedMonth(newDate)}
              views={['year', 'month']}
              slotProps={{
                textField: { fullWidth: true },
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={9}>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<Download />}
                onClick={() => setExportDialog(true)}
              >
                CSV出力
              </Button>
              <Button
                variant="outlined"
                startIcon={<Upload />}
                onClick={() => setImportDialog(true)}
              >
                CSV取込
              </Button>
              <Button
                variant="outlined"
                startIcon={<Add />}
                onClick={() => {
                  setSelectedRecord(null);
                  setManualRecordDialog(true);
                }}
              >
                手動記録
              </Button>
              <IconButton onClick={fetchData} color="primary">
                <Refresh />
              </IconButton>
            </Box>
          </Grid>
        </Grid>

        {/* 決済処理期間アラート */}
        <Box sx={{ mt: 2 }}>
          <Alert severity="info" sx={{ mb: 1 }}>
            📅 カード決済期間: 月初1～5日 | 口座振替期間: 月初1～12日（27日自動実行）
          </Alert>
        </Box>
      </Paper>

      {/* 月次サマリー */}
      {monthlySummary && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  総決済対象
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  {monthlySummary.overall.totalTargets}
                </Typography>
                <Typography variant="caption" color="success.main">
                  成功率: {monthlySummary.overall.successRate}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  カード決済
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="primary.main">
                  {monthlySummary.cardPayment.successCount}/{monthlySummary.cardPayment.totalTargets}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={monthlySummary.cardPayment.successRate}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  口座振替
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  {monthlySummary.bankTransfer.successCount}/{monthlySummary.bankTransfer.totalTargets}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={monthlySummary.bankTransfer.successRate}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  総決済額
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  ¥{monthlySummary.overall.successAmount.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  /¥{monthlySummary.overall.totalAmount.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* タブ */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
          <Tab label="決済対象者" />
          <Tab label="決済結果" />
          <Tab label="手動決済記録" />
        </Tabs>
      </Paper>

      {/* タブコンテンツ */}
      <Paper>
        {currentTab === 0 && (
          <DataGrid
            rows={paymentTargets}
            columns={targetColumns}
            loading={loading}
            autoHeight
            checkboxSelection
            disableRowSelectionOnClick
          />
        )}
        
        {currentTab === 1 && (
          <DataGrid
            rows={paymentResults}
            columns={resultColumns}
            loading={loading}
            autoHeight
            checkboxSelection
            disableRowSelectionOnClick
          />
        )}
        
        {currentTab === 2 && (
          <DataGrid
            rows={manualRecords}
            columns={manualColumns}
            loading={loading}
            autoHeight
            checkboxSelection
            disableRowSelectionOnClick
          />
        )}
      </Paper>

      {/* CSV出力ダイアログ */}
      <Dialog open={exportDialog} onClose={() => setExportDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>CSV出力</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            出力する決済方法を選択してください
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Button
              variant="outlined"
              onClick={() => handleExport(PaymentMethod.CARD)}
              fullWidth
            >
              カード決済用CSV（Univapay）
            </Button>
            <Button
              variant="outlined"
              onClick={() => handleExport(PaymentMethod.BANK_TRANSFER)}
              fullWidth
            >
              口座振替用CSV（Univapay）
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialog(false)}>キャンセル</Button>
        </DialogActions>
      </Dialog>

      {/* CSV取込ダイアログ */}
      <Dialog open={importDialog} onClose={() => setImportDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>決済結果CSV取込</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            取り込む決済結果CSVの種類を選択してください
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Button
              variant="outlined"
              onClick={() => handleImport(PaymentMethod.CARD)}
              fullWidth
            >
              カード決済結果（IPScardresult_YYYYMMDD.csv）
            </Button>
            <Button
              variant="outlined"
              onClick={() => handleImport(PaymentMethod.BANK_TRANSFER)}
              fullWidth
            >
              口座振替結果（XXXXXX_TrnsCSV_YYYYMMDDHHMMSS.csv）
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialog(false)}>キャンセル</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Payments;
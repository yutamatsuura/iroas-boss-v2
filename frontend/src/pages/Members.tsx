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
  InputAdornment,
  Alert,
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import {
  Add,
  Search,
  Edit,
  Delete,
  Download,
  Upload,
  Refresh,
  PersonOff,
  AccountTree,
  Visibility,
} from '@mui/icons-material';
import {
  MemberService,
  Member,
  MemberStatus,
  MemberSearchParams,
  MemberListResponse,
  Plan,
  PaymentMethod,
  Title,
  UserType,
  Gender,
  AccountType,
} from '@/services/memberService';
import MemberDetail from '@/components/MemberDetail';

// Enum値の表示変換マッピング
const statusDisplayMap: Record<string, string> = {
  'ACTIVE': 'アクティブ',
  'INACTIVE': '休会中',
  'WITHDRAWN': '退会済',
  'アクティブ': 'アクティブ',
  '休会中': '休会中',
  '退会済': '退会済',
};

const titleDisplayMap: Record<string, string> = {
  'NONE': '称号なし',
  'KNIGHT_DAME': 'ナイト/デイム',
  'LORD_LADY': 'ロード/レディ',
  'KING_QUEEN': 'キング/クイーン',
  'EMPEROR_EMPRESS': 'エンペラー/エンプレス',
  'COMPANY': '会社',
};

const planDisplayMap: Record<string, string> = {
  'HERO': 'ヒーロープラン',
  'TEST': 'テストプラン',
  'ヒーロープラン': 'ヒーロープラン',
  'テストプラン': 'テストプラン',
};

const paymentMethodDisplayMap: Record<string, string> = {
  'CARD': 'カード決済',
  'TRANSFER': '口座振替',
  'BANK': '銀行振込',
  'INFOCART': 'インフォカート',
  'カード決済': 'カード決済',
  '口座振替': '口座振替',
  '銀行振込': '銀行振込',
  'インフォカート': 'インフォカート',
};

const userTypeDisplayMap: Record<string, string> = {
  'NORMAL': '通常',
  'ATTENTION': '注意',
  '通常': '通常',
  '注意': '注意',
};

const genderDisplayMap: Record<string, string> = {
  'MALE': '男性',
  'FEMALE': '女性',
  'OTHER': 'その他',
  '男性': '男性',
  '女性': '女性',
  'その他': 'その他',
};

const accountTypeDisplayMap: Record<string, string> = {
  'ORDINARY': '普通',
  'CHECKING': '当座',
  '普通': '普通',
  '当座': '当座',
};

/**
 * P-002: 会員管理
 * 会員の登録・編集・退会処理・組織管理を統合
 * 要件定義書の29項目完全準拠
 */
const Members: React.FC = () => {
  // State管理
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [activeCount, setActiveCount] = useState(0);
  const [inactiveCount, setInactiveCount] = useState(0);
  const [withdrawnCount, setWithdrawnCount] = useState(0);
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [tabValue, setTabValue] = useState(0);
  const [openDetailDialog, setOpenDetailDialog] = useState(false);
  
  // 検索フィルター
  const [searchParams, setSearchParams] = useState<MemberSearchParams>({
    memberNumber: '',
    name: '',
    email: '',
    status: undefined,
    plan: undefined,
    paymentMethod: undefined,
    page: 1,
    perPage: 20,
    sortBy: 'memberNumber',
    sortOrder: 'asc',
  });

  // ページネーション
  const [paginationModel, setPaginationModel] = useState({
    page: 0,
    pageSize: 20,
  });

  // データ取得
  const fetchMembers = async () => {
    setLoading(true);
    try {
      // 実際のAPI呼び出し
      const response = await MemberService.getMembers(searchParams);
      setMembers(response.members || []);
      setTotalCount(response.total_count || response.totalCount || 0);
      setActiveCount(response.active_count || response.activeCount || 0);
      setInactiveCount(response.inactive_count || response.inactiveCount || 0);
      setWithdrawnCount(response.withdrawn_count || response.withdrawnCount || 0);
      
      // モックデータ（APIが動作しない場合のフォールバック）
      /*const mockResponse: MemberListResponse = {
        members: [
          {
            id: 1,
            status: MemberStatus.ACTIVE,
            memberNumber: '0000001',
            name: '山田太郎',
            nameKana: 'ヤマダタロウ',
            email: 'yamada@example.com',
            title: '称号なし' as any,
            userType: '通常' as any,
            plan: Plan.HERO,
            paymentMethod: PaymentMethod.CARD,
            registrationDate: '2024-01-15',
            phone: '090-1234-5678',
          },
          {
            id: 2,
            status: MemberStatus.ACTIVE,
            memberNumber: '0000002',
            name: '佐藤花子',
            nameKana: 'サトウハナコ',
            email: 'sato@example.com',
            title: 'ナイト/デイム' as any,
            userType: '通常' as any,
            plan: Plan.HERO,
            paymentMethod: PaymentMethod.BANK_TRANSFER,
            registrationDate: '2024-02-01',
            phone: '080-2345-6789',
          },
        ],
        totalCount: 50,
        activeCount: 45,
        inactiveCount: 3,
        withdrawnCount: 2,
        page: 1,
        perPage: 20,
        totalPages: 3,
      };
      
      setMembers(mockResponse.members);
      setTotalCount(mockResponse.totalCount);
      setActiveCount(mockResponse.activeCount);
      setInactiveCount(mockResponse.inactiveCount);
      setWithdrawnCount(mockResponse.withdrawnCount);*/
    } catch (error) {
      console.error('会員データ取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  // paginationModelの変更をsearchParamsに反映
  useEffect(() => {
    setSearchParams(prev => ({
      ...prev,
      page: paginationModel.page + 1, // DataGridは0ベース、APIは1ベース
      perPage: paginationModel.pageSize,
    }));
  }, [paginationModel]);

  useEffect(() => {
    fetchMembers();
  }, [searchParams]);

  // DataGrid列定義
  const columns: GridColDef[] = [
    {
      field: 'member_number',
      headerName: '会員番号',
      width: 120,
      sortable: true,
      valueGetter: (params) => params.row.member_number || params.row.memberNumber,
    },
    {
      field: 'status',
      headerName: 'ステータス',
      width: 120,
      renderCell: (params: GridRenderCellParams) => {
        const displayValue = statusDisplayMap[params.value] || params.value;
        const getStatusColor = () => {
          const statusValue = params.value?.toString().toUpperCase();
          switch (statusValue) {
            case 'ACTIVE':
            case 'アクティブ':
              return 'success';
            case 'INACTIVE':
            case '休会中':
              return 'warning';
            case 'WITHDRAWN':
            case '退会済':
              return 'error';
            default:
              return 'default';
          }
        };
        return <Chip label={displayValue} size="small" color={getStatusColor()} />;
      },
    },
    {
      field: 'name',
      headerName: '氏名',
      width: 150,
      sortable: true,
    },
    {
      field: 'title',
      headerName: '称号',
      width: 150,
      sortable: true,
      valueGetter: (params) => {
        const value = params.row.title || 'NONE';
        return titleDisplayMap[value] || value;
      },
    },
    {
      field: 'user_type',
      headerName: 'ユーザータイプ',
      width: 120,
      sortable: true,
      valueGetter: (params) => {
        const value = params.row.user_type || params.row.userType || 'NORMAL';
        return userTypeDisplayMap[value] || value;
      },
    },
    {
      field: 'upline_name',
      headerName: '直上者名',
      width: 150,
      sortable: true,
      valueGetter: (params) => params.row.upline_name || params.row.uplineName || '',
    },
    {
      field: 'email',
      headerName: 'メールアドレス',
      width: 200,
      sortable: true,
    },
    {
      field: 'plan',
      headerName: '加入プラン',
      width: 140,
      valueGetter: (params) => {
        const value = params.row.plan;
        return planDisplayMap[value] || value;
      },
    },
    {
      field: 'payment_method',
      headerName: '決済方法',
      width: 120,
      valueGetter: (params) => {
        const value = params.row.payment_method || params.row.paymentMethod;
        return paymentMethodDisplayMap[value] || value;
      },
    },
    {
      field: 'registration_date',
      headerName: '登録日',
      width: 120,
      sortable: true,
      valueGetter: (params) => {
        const dateStr = params.row.registration_date || params.row.registrationDate || '';
        // 時間部分を削除（Tまたは空白以降を除去）
        if (dateStr.includes('T')) {
          return dateStr.split('T')[0];
        } else if (dateStr.includes(' ')) {
          return dateStr.split(' ')[0];
        }
        return dateStr;
      },
    },
    {
      field: 'actions',
      headerName: '操作',
      width: 180,
      sortable: false,
      renderCell: (params: GridRenderCellParams) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton
            size="small"
            color="info"
            onClick={() => handleView(params.row)}
            title="詳細"
          >
            <Visibility fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            color="primary"
            onClick={() => handleEdit(params.row)}
            title="編集"
          >
            <Edit fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            color="warning"
            onClick={() => handleWithdraw(params.row)}
            title="退会処理"
            disabled={params.row.status === MemberStatus.WITHDRAWN}
          >
            <PersonOff fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            color="info"
            onClick={() => handleOrganization(params.row)}
            title="組織図"
          >
            <AccountTree fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  // ハンドラー関数
  const handleSearch = () => {
    fetchMembers();
  };

  const handleCreate = () => {
    setSelectedMember(null);
    setDialogMode('create');
    setOpenDialog(true);
  };

  const handleView = async (member: Member) => {
    try {
      const memberNumber = member.member_number || member.memberNumber;
      if (memberNumber) {
        const fullMemberData = await MemberService.getMemberByNumber(memberNumber);
        setSelectedMember(fullMemberData);
        setOpenDetailDialog(true);
      }
    } catch (error) {
      console.error('会員詳細取得エラー:', error);
    }
  };

  const handleEdit = async (member: Member) => {
    try {
      // 会員詳細を取得（完全なデータを取得するため）
      const memberNumber = member.member_number || member.memberNumber;
      if (memberNumber) {
        const fullMemberData = await MemberService.getMemberByNumber(memberNumber);
        setSelectedMember(fullMemberData);
      } else {
        setSelectedMember(member);
      }
    } catch (error) {
      console.error('会員詳細取得エラー:', error);
      setSelectedMember(member);
    }
    setDialogMode('edit');
    setOpenDialog(true);
  };

  const handleWithdraw = async (member: Member) => {
    if (window.confirm(`${member.name}さんを退会処理しますか？`)) {
      try {
        const memberNumber = member.member_number || member.memberNumber;
        if (memberNumber) {
          await MemberService.withdrawMemberByNumber(memberNumber, '管理者による退会処理');
          fetchMembers();
        } else {
          console.error('会員番号が見つかりません');
        }
      } catch (error) {
        console.error('退会処理エラー:', error);
      }
    }
  };

  const handleOrganization = (member: Member) => {
    // 組織図表示（P-003へ遷移）
    window.location.href = `/organization?memberId=${member.id}`;
  };

  const handleExport = async () => {
    try {
      const blob = await MemberService.exportMembers(searchParams);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `members_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
    } catch (error) {
      console.error('CSV出力エラー:', error);
    }
  };

  const handleImport = () => {
    // CSV取込ダイアログ表示
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    input.onchange = async (e: any) => {
      const file = e.target.files[0];
      if (file) {
        try {
          await MemberService.importMembers(file);
          fetchMembers();
        } catch (error) {
          console.error('CSV取込エラー:', error);
        }
      }
    };
    input.click();
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedMember(null);
  };

  return (
    <Box>
      {/* ページヘッダー */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">
          会員管理
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          会員の登録・編集・退会処理・組織管理
        </Typography>
      </Box>

      {/* 統計カード */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">
              総会員数
            </Typography>
            <Typography variant="h4" fontWeight="bold">
              {totalCount}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">
              アクティブ
            </Typography>
            <Typography variant="h4" fontWeight="bold" color="success.main">
              {activeCount}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">
              休会中
            </Typography>
            <Typography variant="h4" fontWeight="bold" color="warning.main">
              {inactiveCount}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">
              退会済
            </Typography>
            <Typography variant="h4" fontWeight="bold" color="error.main">
              {withdrawnCount}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* 検索フィルター */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="会員番号"
              value={searchParams.memberNumber}
              onChange={(e) =>
                setSearchParams({ ...searchParams, memberNumber: e.target.value })
              }
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="氏名"
              value={searchParams.name}
              onChange={(e) =>
                setSearchParams({ ...searchParams, name: e.target.value })
              }
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="メールアドレス"
              value={searchParams.email}
              onChange={(e) =>
                setSearchParams({ ...searchParams, email: e.target.value })
              }
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>ステータス</InputLabel>
              <Select
                value={searchParams.status || ''}
                label="ステータス"
                onChange={(e) =>
                  setSearchParams({
                    ...searchParams,
                    status: e.target.value as MemberStatus,
                  })
                }
              >
                <MenuItem value="">すべて</MenuItem>
                <MenuItem value={MemberStatus.ACTIVE}>アクティブ</MenuItem>
                <MenuItem value={MemberStatus.INACTIVE}>休会中</MenuItem>
                <MenuItem value={MemberStatus.WITHDRAWN}>退会済</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
          <Button variant="outlined" onClick={() => setSearchParams({})}>
            クリア
          </Button>
          <Button
            variant="contained"
            startIcon={<Search />}
            onClick={handleSearch}
          >
            検索
          </Button>
        </Box>
      </Paper>

      {/* アクションボタン */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleCreate}
        >
          新規登録
        </Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Upload />}
            onClick={handleImport}
          >
            CSV取込
          </Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={handleExport}
          >
            CSV出力
          </Button>
          <IconButton onClick={fetchMembers} color="primary">
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* 会員一覧テーブル */}
      <Paper>
        <DataGrid
          rows={members}
          columns={columns}
          loading={loading}
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          pageSizeOptions={[10, 20, 50]}
          rowCount={totalCount}
          paginationMode="server"
          checkboxSelection
          disableRowSelectionOnClick
          autoHeight
          sx={{
            '& .MuiDataGrid-cell': {
              borderBottom: '1px solid #e0e0e0',
            },
          }}
        />
      </Paper>

      {/* 会員登録・編集ダイアログ */}
      <MemberDialog
        open={openDialog}
        mode={dialogMode}
        member={selectedMember}
        onClose={handleCloseDialog}
        onSave={fetchMembers}
      />

      {/* 詳細表示ダイアログ */}
      <MemberDetail
        open={openDetailDialog}
        member={selectedMember}
        onClose={() => setOpenDetailDialog(false)}
      />
    </Box>
  );
};

// 会員登録・編集ダイアログコンポーネント
interface MemberDialogProps {
  open: boolean;
  mode: 'create' | 'edit';
  member: Member | null;
  onClose: () => void;
  onSave: () => void;
}

const MemberDialog: React.FC<MemberDialogProps> = ({
  open,
  mode,
  member,
  onClose,
  onSave,
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [formData, setFormData] = useState({
    // 基本情報（1-5）
    status: MemberStatus.ACTIVE,
    memberNumber: '',
    name: '',
    email: '',
    // MLM情報（6-9）
    title: Title.NONE,
    userType: UserType.NORMAL,
    plan: Plan.HERO,
    paymentMethod: PaymentMethod.CARD,
    // 日付情報（10-11）
    registrationDate: '',
    withdrawalDate: '',
    // 連絡先情報（12-17）
    phone: '',
    gender: '',
    postalCode: '',
    prefecture: '',
    address2: '',
    address3: '',
    // 組織情報（18-21）
    uplineId: '',
    uplineName: '',
    referrerId: '',
    referrerName: '',
    // 銀行情報（22-29）
    bankName: '',
    bankCode: '',
    branchName: '',
    branchCode: '',
    accountNumber: '',
    yuchoSymbol: '',
    yuchoNumber: '',
    accountType: '',
    // その他（30）
    notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // フォームデータ初期化
  useEffect(() => {
    if (mode === 'edit' && member) {
      setFormData({
        // 基本情報
        status: member.status || MemberStatus.ACTIVE,
        memberNumber: member.member_number || member.memberNumber || '',
        name: member.name,
        email: member.email,
        // MLM情報
        title: member.title || Title.NONE,
        userType: member.user_type || member.userType || UserType.NORMAL,
        plan: member.plan as Plan,
        paymentMethod: (member.payment_method || member.paymentMethod) as PaymentMethod,
        // 日付情報（時間部分を削除）
        registrationDate: (() => {
          const dateStr = member.registration_date || member.registrationDate || '';
          // 'T'または' 'で分割して日付部分のみ取得
          if (dateStr.includes('T')) {
            return dateStr.split('T')[0];
          } else if (dateStr.includes(' ')) {
            return dateStr.split(' ')[0];
          }
          return dateStr;
        })(),
        withdrawalDate: (() => {
          const dateStr = member.withdrawal_date || member.withdrawalDate || '';
          if (!dateStr) return '';
          // 'T'または' 'で分割して日付部分のみ取得
          if (dateStr.includes('T')) {
            return dateStr.split('T')[0];
          } else if (dateStr.includes(' ')) {
            return dateStr.split(' ')[0];
          }
          return dateStr;
        })(),
        // 連絡先情報
        phone: member.phone || '',
        gender: member.gender || '',
        postalCode: member.postal_code || member.postalCode || '',
        prefecture: member.prefecture || '',
        address2: member.address2 || '',
        address3: member.address3 || '',
        // 組織情報
        uplineId: member.upline_id || member.uplineId || '',
        uplineName: member.upline_name || member.uplineName || '',
        referrerId: member.referrer_id || member.referrerId || '',
        referrerName: member.referrer_name || member.referrerName || '',
        // 銀行情報
        bankName: member.bank_name || member.bankName || '',
        bankCode: member.bank_code || member.bankCode || '',
        branchName: member.branch_name || member.branchName || '',
        branchCode: member.branch_code || member.branchCode || '',
        accountNumber: member.account_number || member.accountNumber || '',
        yuchoSymbol: member.yucho_symbol || member.yuchoSymbol || '',
        yuchoNumber: member.yucho_number || member.yuchoNumber || '',
        accountType: member.account_type || member.accountType || '',
        // その他
        notes: member.notes || '',
      });
    } else {
      // 新規作成時はデフォルト値
      setFormData({
        status: MemberStatus.ACTIVE,
        memberNumber: '',
        name: '',
        email: '',
        title: Title.NONE,
        userType: UserType.NORMAL,
        plan: Plan.HERO,
        paymentMethod: PaymentMethod.CARD,
        registrationDate: '',
        withdrawalDate: '',
        phone: '',
        gender: '',
        postalCode: '',
        prefecture: '',
        address2: '',
        address3: '',
        uplineId: '',
        uplineName: '',
        referrerId: '',
        referrerName: '',
        bankName: '',
        bankCode: '',
        branchName: '',
        branchCode: '',
        accountNumber: '',
        yuchoSymbol: '',
        yuchoNumber: '',
        accountType: '',
        notes: '',
      });
    }
    setError('');
    setTabValue(0);
  }, [mode, member, open]);

  const handleSave = async () => {
    setLoading(true);
    setError('');
    
    try {
      if (mode === 'create') {
        await MemberService.createMember({
          // 基本情報
          status: formData.status,
          member_number: formData.memberNumber,
          name: formData.name,
          email: formData.email,
          // MLM情報
          title: formData.title,
          user_type: formData.userType,
          plan: formData.plan,
          payment_method: formData.paymentMethod,
          // 日付情報
          registration_date: formData.registrationDate || undefined,
          withdrawal_date: formData.withdrawalDate || undefined,
          // 連絡先情報
          phone: formData.phone || undefined,
          gender: formData.gender || undefined,
          postal_code: formData.postalCode || undefined,
          prefecture: formData.prefecture || undefined,
          address2: formData.address2 || undefined,
          address3: formData.address3 || undefined,
          // 組織情報
          upline_id: formData.uplineId || undefined,
          upline_name: formData.uplineName || undefined,
          referrer_id: formData.referrerId || undefined,
          referrer_name: formData.referrerName || undefined,
          // 銀行情報
          bank_name: formData.bankName || undefined,
          bank_code: formData.bankCode || undefined,
          branch_name: formData.branchName || undefined,
          branch_code: formData.branchCode || undefined,
          account_number: formData.accountNumber || undefined,
          yucho_symbol: formData.yuchoSymbol || undefined,
          yucho_number: formData.yuchoNumber || undefined,
          account_type: formData.accountType || undefined,
          // その他
          notes: formData.notes || undefined,
        });
      } else if (member) {
        const memberNumber = member.member_number || member.memberNumber;
        if (memberNumber) {
          console.log('更新データ送信:', {
            registration_date: formData.registrationDate,
            withdrawal_date: formData.withdrawalDate,
          });
          await MemberService.updateMemberByNumber(memberNumber, {
            name: formData.name,
            email: formData.email,
            title: formData.title || undefined,
            user_type: formData.userType || undefined,
            plan: formData.plan || undefined,
            payment_method: formData.paymentMethod || undefined,
            registration_date: formData.registrationDate || undefined,
            withdrawal_date: formData.withdrawalDate || undefined,
            phone: formData.phone || undefined,
            gender: formData.gender || undefined,
            postal_code: formData.postalCode || undefined,
            prefecture: formData.prefecture || undefined,
            address2: formData.address2 || undefined,
            address3: formData.address3 || undefined,
            upline_id: formData.uplineId || undefined,
            upline_name: formData.uplineName || undefined,
            referrer_id: formData.referrerId || undefined,
            referrer_name: formData.referrerName || undefined,
            bank_name: formData.bankName || undefined,
            bank_code: formData.bankCode || undefined,
            branch_name: formData.branchName || undefined,
            branch_code: formData.branchCode || undefined,
            account_number: formData.accountNumber || undefined,
            yucho_symbol: formData.yuchoSymbol || undefined,
            yucho_number: formData.yuchoNumber || undefined,
            account_type: formData.accountType || undefined,
            notes: formData.notes || undefined,
          });
        }
      }
      
      onSave();
      onClose();
    } catch (err: any) {
      setError(err.message || '保存に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        {mode === 'create' ? '新規会員登録（30項目）' : '会員情報編集（30項目）'}
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} sx={{ mb: 3 }}>
          <Tab label="基本情報" />
          <Tab label="連絡先情報" />
          <Tab label="組織情報" />
          <Tab label="銀行情報" />
        </Tabs>

        {/* 基本情報タブ */}
        {tabValue === 0 && (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>ステータス</InputLabel>
                <Select
                  value={formData.status}
                  label="ステータス"
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as MemberStatus })}
                  disabled={mode === 'edit'}
                >
                  <MenuItem value={MemberStatus.ACTIVE}>アクティブ</MenuItem>
                  <MenuItem value={MemberStatus.INACTIVE}>休会中</MenuItem>
                  {mode === 'edit' && <MenuItem value={MemberStatus.WITHDRAWN}>退会済</MenuItem>}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label="会員番号（11桁）"
                value={formData.memberNumber}
                onChange={(e) => setFormData({ ...formData, memberNumber: e.target.value })}
                disabled={mode === 'edit'}
                placeholder="例: 12345678901"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label="氏名"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                type="email"
                label="メールアドレス"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>称号</InputLabel>
                <Select
                  value={formData.title}
                  label="称号"
                  onChange={(e) => setFormData({ ...formData, title: e.target.value as Title })}
                >
                  <MenuItem value={Title.NONE}>称号なし</MenuItem>
                  <MenuItem value={Title.KNIGHT_DAME}>ナイト/デイム</MenuItem>
                  <MenuItem value={Title.LORD_LADY}>ロード/レディ</MenuItem>
                  <MenuItem value={Title.KING_QUEEN}>キング/クイーン</MenuItem>
                  <MenuItem value={Title.EMPEROR_EMPRESS}>エンペラー/エンブレス</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>ユーザータイプ</InputLabel>
                <Select
                  value={formData.userType}
                  label="ユーザータイプ"
                  onChange={(e) => setFormData({ ...formData, userType: e.target.value as UserType })}
                >
                  <MenuItem value={UserType.NORMAL}>通常</MenuItem>
                  <MenuItem value={UserType.ATTENTION}>注意</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>加入プラン</InputLabel>
                <Select
                  value={formData.plan}
                  label="加入プラン"
                  onChange={(e) => setFormData({ ...formData, plan: e.target.value as Plan })}
                >
                  <MenuItem value={Plan.HERO}>ヒーロープラン</MenuItem>
                  <MenuItem value={Plan.TEST}>テストプラン</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>決済方法</InputLabel>
                <Select
                  value={formData.paymentMethod}
                  label="決済方法"
                  onChange={(e) => setFormData({ ...formData, paymentMethod: e.target.value as PaymentMethod })}
                >
                  <MenuItem value={PaymentMethod.CARD}>カード決済</MenuItem>
                  <MenuItem value={PaymentMethod.TRANSFER}>口座振替</MenuItem>
                  <MenuItem value={PaymentMethod.BANK}>銀行振込</MenuItem>
                  <MenuItem value={PaymentMethod.INFOCART}>インフォカート</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="登録日"
                type="text"
                value={formData.registrationDate}
                onChange={(e) => setFormData({ ...formData, registrationDate: e.target.value })}
                placeholder="例: 2025/01/15 または 2025-01-15"
                disabled={false}
                helperText="任意の形式で入力・編集可能"
              />
            </Grid>
            {mode === 'edit' && formData.withdrawalDate && (
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="退会日"
                  type="text"
                  value={formData.withdrawalDate}
                  disabled={true}
                  helperText="退会処理は一覧画面から実行してください"
                />
              </Grid>
            )}
          </Grid>
        )}

        {/* 連絡先情報タブ */}
        {tabValue === 1 && (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="電話番号"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="例: 090-1234-5678"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>性別</InputLabel>
                <Select
                  value={formData.gender}
                  label="性別"
                  onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                >
                  <MenuItem value="">未設定</MenuItem>
                  <MenuItem value={Gender.MALE}>男性</MenuItem>
                  <MenuItem value={Gender.FEMALE}>女性</MenuItem>
                  <MenuItem value={Gender.OTHER}>その他</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="郵便番号"
                value={formData.postalCode}
                onChange={(e) => setFormData({ ...formData, postalCode: e.target.value })}
                placeholder="例: 100-0001"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="都道府県"
                value={formData.prefecture}
                onChange={(e) => setFormData({ ...formData, prefecture: e.target.value })}
                placeholder="例: 東京都"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="住所2（市区町村・番地）"
                value={formData.address2}
                onChange={(e) => setFormData({ ...formData, address2: e.target.value })}
                placeholder="例: 千代田区千代田1-1-1"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="住所3（建物名・部屋番号）"
                value={formData.address3}
                onChange={(e) => setFormData({ ...formData, address3: e.target.value })}
                placeholder="例: サンプルマンション101号室"
              />
            </Grid>
          </Grid>
        )}

        {/* 組織情報タブ */}
        {tabValue === 2 && (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="直上者ID（11桁）"
                value={formData.uplineId}
                onChange={(e) => setFormData({ ...formData, uplineId: e.target.value })}
                placeholder="例: 12345678901"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="直上者名"
                value={formData.uplineName}
                onChange={(e) => setFormData({ ...formData, uplineName: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="紹介者ID（11桁）"
                value={formData.referrerId}
                onChange={(e) => setFormData({ ...formData, referrerId: e.target.value })}
                placeholder="例: 12345678901"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="紹介者名"
                value={formData.referrerName}
                onChange={(e) => setFormData({ ...formData, referrerName: e.target.value })}
              />
            </Grid>
          </Grid>
        )}

        {/* 銀行情報タブ */}
        {tabValue === 3 && (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="報酬振込先の銀行名"
                value={formData.bankName}
                onChange={(e) => setFormData({ ...formData, bankName: e.target.value })}
                placeholder="例: 三菱UFJ銀行"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="銀行コード（4桁）"
                value={formData.bankCode}
                onChange={(e) => setFormData({ ...formData, bankCode: e.target.value })}
                placeholder="例: 0001"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="支店名"
                value={formData.branchName}
                onChange={(e) => setFormData({ ...formData, branchName: e.target.value })}
                placeholder="例: 東京支店"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="支店コード（3桁）"
                value={formData.branchCode}
                onChange={(e) => setFormData({ ...formData, branchCode: e.target.value })}
                placeholder="例: 001"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="口座番号"
                value={formData.accountNumber}
                onChange={(e) => setFormData({ ...formData, accountNumber: e.target.value })}
                placeholder="例: 1234567"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>口座種別</InputLabel>
                <Select
                  value={formData.accountType}
                  label="口座種別"
                  onChange={(e) => setFormData({ ...formData, accountType: e.target.value })}
                >
                  <MenuItem value="">未設定</MenuItem>
                  <MenuItem value={AccountType.ORDINARY}>普通</MenuItem>
                  <MenuItem value={AccountType.CHECKING}>当座</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="ゆうちょの場合の記号（5桁）"
                value={formData.yuchoSymbol}
                onChange={(e) => setFormData({ ...formData, yuchoSymbol: e.target.value })}
                placeholder="例: 12345"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="ゆうちょの場合の番号（8桁以内）"
                value={formData.yuchoNumber}
                onChange={(e) => setFormData({ ...formData, yuchoNumber: e.target.value })}
                placeholder="例: 12345678"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="備考"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="特記事項があれば入力してください"
              />
            </Grid>
          </Grid>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          キャンセル
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={loading || !formData.memberNumber || !formData.name || !formData.email}
        >
          {loading ? '保存中...' : '保存'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default Members;
import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Alert,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  AccountTree,
  Person,
  ExpandMore,
  ExpandLess,
  Search,
  FilterList,
  Refresh,
  SwapHoriz,
  Visibility,
  Download,
} from '@mui/icons-material';
import { Tooltip } from '@mui/material';
import MemberDetail from '../components/MemberDetail';
import { 
  OrganizationService, 
  OrganizationNode, 
  OrganizationTree, 
  OrganizationStats 
} from '@/services/organizationService';

/**
 * P-003: 組織図ビューア
 * MLM組織構造の視覚的表示と階層確認
 * 要件定義書: 手動での組織調整（自動圧縮NG）
 */

// フロントエンド用組織ノード（レガシー互換性のため）
interface LegacyOrganizationNode {
  id: number;
  memberNumber: string;
  name: string;
  title: string;
  level: number;
  totalSales?: number;
  personalSales?: number;
  children: LegacyOrganizationNode[];
  isExpanded?: boolean;
  status: string;
}

const Organization: React.FC = () => {
  // State管理
  const [organizationData, setOrganizationData] = useState<OrganizationNode[]>([]);
  const [organizationStats, setOrganizationStats] = useState<OrganizationStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedMember, setSelectedMember] = useState<OrganizationNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
  const [filterLevel, setFilterLevel] = useState<number | ''>('');
  const [filteredData, setFilteredData] = useState<OrganizationNode[]>([]);
  const [showSponsorDialog, setShowSponsorDialog] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState<OrganizationNode[]>([]);
  const [viewMode, setViewMode] = useState<'tree' | 'table'>('tree');
  const [currentMaxLevel, setCurrentMaxLevel] = useState(5);
  const [focusedMember, setFocusedMember] = useState<OrganizationNode | null>(null);
  const [showMemberDetail, setShowMemberDetail] = useState(false);
  const [showActiveOnly, setShowActiveOnly] = useState(false);


  useEffect(() => {
    fetchOrganizationData();
  }, []);

  useEffect(() => {
    fetchOrganizationData(currentMaxLevel, focusedMember?.member_number);
  }, [showActiveOnly]);

  // デバウンス処理
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
    }, 150); // 150ms待機（高速化）

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // 検索とフィルターの処理
  useEffect(() => {
    let filtered = [...organizationData];
    
    // 検索フィルター（会員番号のみ、高速化）
    if (debouncedSearchQuery) {
      filtered = filterNodesBySearch(filtered, debouncedSearchQuery);
    }
    
    // レベルフィルター
    if (filterLevel !== '') {
      filtered = filterNodesByLevel(filtered, filterLevel);
    }
    
    setFilteredData(filtered);
  }, [organizationData, debouncedSearchQuery, filterLevel]);

  // データ取得
  const fetchOrganizationData = async (maxLevel = currentMaxLevel, focusMember?: string) => {
    setLoading(true);
    try {
      // 組織ツリーデータを取得
      const treeData = await OrganizationService.getOrganizationTree(focusMember, maxLevel, showActiveOnly);
      setOrganizationData(treeData.root_nodes);
      
      // 組織統計データを取得
      const stats = await OrganizationService.getOrganizationStats();
      setOrganizationStats(stats);
    } catch (error) {
      console.error('組織データ取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  // さらに深い階層を表示
  const loadMoreLevels = async () => {
    // 最大55階層に制限
    const newMaxLevel = Math.min(currentMaxLevel + 5, 55);
    if (newMaxLevel === currentMaxLevel) {
      // すでに最大階層に達している
      return;
    }
    setCurrentMaxLevel(newMaxLevel);
    await fetchOrganizationData(newMaxLevel, focusedMember?.member_number);
  };

  // 特定メンバーにフォーカス
  const focusOnMember = async (member: OrganizationNode) => {
    setFocusedMember(member);
    setBreadcrumbs([member]);
    await fetchOrganizationData(currentMaxLevel, member.member_number);
  };

  // 全体表示に戻る
  const resetToFullView = async () => {
    setFocusedMember(null);
    setBreadcrumbs([]);
    await fetchOrganizationData(currentMaxLevel);
  };

  // ノード展開/折りたたみ
  const toggleNodeExpansion = (nodeId: string) => {
    const updatedData = OrganizationService.toggleNodeExpansion(organizationData, nodeId);
    setOrganizationData(updatedData);
  };

  // 検索フィルター関数（会員番号のみ）
  const filterNodesBySearch = (nodes: OrganizationNode[], query: string): OrganizationNode[] => {
    const result: OrganizationNode[] = [];
    
    nodes.forEach(node => {
      // 会員番号のみで検索（パフォーマンス向上）
      const matchesSearch = node.member_number.includes(query);
      
      const filteredChildren = filterNodesBySearch(node.children, query);
      
      if (matchesSearch || filteredChildren.length > 0) {
        result.push({
          ...node,
          children: filteredChildren,
          is_expanded: true // 検索結果を表示するため展開
        });
      }
    });
    
    return result;
  };

  // レベルフィルター関数
  const filterNodesByLevel = (nodes: OrganizationNode[], level: number): OrganizationNode[] => {
    const result: OrganizationNode[] = [];
    
    nodes.forEach(node => {
      const matchesLevel = 
        level === 5 ? node.level >= 5 : node.level === level;
      
      const filteredChildren = filterNodesByLevel(node.children, level);
      
      if (matchesLevel || filteredChildren.length > 0) {
        result.push({
          ...node,
          children: filteredChildren,
          is_expanded: true // フィルター結果を表示するため展開
        });
      }
    });
    
    return result;
  };

  // 現在表示中のデータをCSV出力
  const downloadCurrentView = () => {
    const currentData = debouncedSearchQuery || filterLevel !== '' ? filteredData : organizationData;
    const flattenedData = flattenNodes(currentData);
    
    // CSVヘッダー
    const headers = [
      '会員番号',
      '氏名',
      '称号',
      'ステータス',
      'レベル',
      '左売上',
      '右売上',
      '合計売上',
      '登録日'
    ];
    
    // CSVデータ行
    const rows = flattenedData.map(node => [
      node.member_number,
      node.name,
      node.title,
      node.status === 'ACTIVE' ? 'アクティブ' : '退会済',
      node.level.toString(),
      node.left_sales.toLocaleString(),
      node.right_sales.toLocaleString(),
      (node.left_sales + node.right_sales).toLocaleString(),
      node.registration_date
    ]);
    
    // CSV文字列を生成
    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
    
    // ファイル名を生成
    let filename = '組織図データ';
    if (focusedMember) {
      filename += `_${focusedMember.name}配下`;
    }
    if (showActiveOnly) {
      filename += '_アクティブのみ';
    }
    if (debouncedSearchQuery) {
      filename += `_検索_${debouncedSearchQuery}`;
    }
    if (filterLevel !== '') {
      filename += `_レベル${filterLevel}`;
    }
    filename += `_${new Date().toISOString().split('T')[0]}.csv`;
    
    // ダウンロード実行
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // ノードツリーをフラット配列に変換
  const flattenNodes = (nodes: OrganizationNode[]): OrganizationNode[] => {
    const result: OrganizationNode[] = [];
    
    const flatten = (nodeList: OrganizationNode[]) => {
      nodeList.forEach(node => {
        result.push(node);
        if (node.children.length > 0) {
          flatten(node.children);
        }
      });
    };
    
    flatten(nodes);
    return result;
  };

  // メンバー詳細表示
  const handleMemberDetail = async (member: OrganizationNode) => {
    try {
      // 組織データから詳細情報を取得
      const memberDetail = await OrganizationService.getOrganizationMemberDetail(member.member_number);
      setSelectedMember(memberDetail);
      // パンくずリスト更新（実際は階層を遡って構築）
      setBreadcrumbs([memberDetail]);
    } catch (error) {
      console.error('会員詳細取得エラー:', error);
      // エラーの場合は元のデータを使用
      setSelectedMember(member);
    }
    setShowMemberDetail(true);
  };

  // 紹介者変更ダイアログ表示
  const handleSponsorChange = (member: OrganizationNode) => {
    setSelectedMember(member);
    setShowSponsorDialog(true);
  };

  // 組織ツリーコンポーネント（メモ化でパフォーマンス向上）
  const OrganizationTreeNode: React.FC<{ 
    node: OrganizationNode; 
    depth: number;
  }> = React.memo(({ node, depth }) => {
    const getStatusColor = OrganizationService.getStatusColor;
    const getTitleColor = OrganizationService.getTitleColor;

    // ステータス日本語変換
    const getStatusLabel = (status: string) => {
      switch (status.toUpperCase()) {
        case 'ACTIVE':
          return 'アクティブ';
        case 'INACTIVE':
          return '休会中';
        case 'WITHDRAWN':
          return '退会済';
        default:
          return status;
      }
    };

    // 称号日本語変換
    const getTitleLabel = (title: string) => {
      switch (title.toUpperCase()) {
        case 'NONE':
          return '称号なし';
        case 'COMPANY':
          return '会社';
        case 'KNIGHT_DAME':
          return 'ナイト/デイム';
        case 'LORD_LADY':
          return 'ロード/レディ';
        case 'KING_QUEEN':
          return 'キング/クイーン';
        case 'EMPEROR_EMPRESS':
          return 'エンペラー/エンブレス';
        case 'WITHDRAWN':
          return '退会済';
        default:
          return title;
      }
    };

    // アクティブのみ表示時に、親との階層差を表示
    const parentLevel = depth > 0 ? depth - 1 : 0;
    const levelGap = showActiveOnly && depth > 0 ? node.level - parentLevel : 0;
    
    return (
      <Box key={node.id}>
        {showActiveOnly && levelGap > 1 && (
          <Typography 
            variant="caption" 
            sx={{ 
              ml: (node.level - 1) * 3 + 2, 
              color: 'text.disabled',
              fontStyle: 'italic',
              display: 'block',
              mb: 0.5
            }}
          >
            ... {levelGap - 1}階層スキップ ...
          </Typography>
        )}
        <Card
          sx={{
            mb: 1,
            ml: showActiveOnly ? node.level * 3 : depth * 3,
            border: selectedMember?.id === node.id ? 2 : 1,
            borderColor: selectedMember?.id === node.id ? 'primary.main' : 'divider',
            cursor: 'pointer',
            opacity: node.is_withdrawn ? 0.6 : 1,
            backgroundColor: node.is_withdrawn ? '#f5f5f5' : 'inherit',
            borderStyle: node.is_withdrawn ? 'dashed' : 'solid',
            '&:hover': {
              boxShadow: node.is_withdrawn ? 1 : 2,
            },
          }}
          onClick={() => focusOnMember(node)}
        >
          <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {/* 展開/折りたたみボタン */}
              {node.children.length > 0 && (
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleNodeExpansion(node.id);
                  }}
                >
                  {node.is_expanded ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              )}

              {/* メンバー情報 */}
              <Person sx={{ color: 'primary.main' }} />
              
              <Box sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    {node.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ({node.member_number})
                  </Typography>
                  <Chip
                    label={getStatusLabel(node.status)}
                    size="small"
                    color={getStatusColor(node.status)}
                  />
                  {node.is_direct && (
                    <Chip
                      label="直"
                      size="small"
                      color="secondary"
                      sx={{ fontWeight: 'bold' }}
                    />
                  )}
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 0.5 }}>
                  <Chip
                    label={getTitleLabel(node.title)}
                    size="small"
                    sx={{
                      bgcolor: getTitleColor(node.title),
                      color: 'white',
                      fontSize: '0.7rem',
                    }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    レベル {node.level}
                  </Typography>
                  {/* 売上表示は一時的に非表示 */}
                </Box>
              </Box>

              {/* アクションボタン */}
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                <Tooltip title="会員詳細表示" arrow>
                  <IconButton
                    size="small"
                    color="primary"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleMemberDetail(node);
                    }}
                  >
                    <Visibility fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="紹介者変更" arrow>
                  <IconButton
                    size="small"
                    color="warning"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSponsorChange(node);
                    }}
                    disabled={node.is_withdrawn}
                  >
                    <SwapHoriz fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* 子ノード表示 */}
        {node.is_expanded && node.children.map(child => (
          <OrganizationTreeNode
            key={child.id}
            node={child}
            depth={depth + 1}
          />
        ))}
      </Box>
    );
  }, (prevProps, nextProps) => {
    return prevProps.node.id === nextProps.node.id && 
           prevProps.node.is_expanded === nextProps.node.is_expanded &&
           prevProps.depth === nextProps.depth;
  });

  return (
    <Box>
      {/* ページヘッダー */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">
          組織図ビューア
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          MLM組織構造の視覚的表示と階層確認
        </Typography>
      </Box>

      {/* パンくずナビと階層コントロール */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            {focusedMember ? (
              <Breadcrumbs>
                <Link color="inherit" href="#" onClick={resetToFullView}>
                  組織全体
                </Link>
                <Typography color="text.primary">
                  {focusedMember.name} ({focusedMember.member_number}) の配下組織
                </Typography>
              </Breadcrumbs>
            ) : (
              <Typography variant="h6">組織全体表示</Typography>
            )}
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip 
              label={`${currentMaxLevel}階層まで表示`} 
              size="small" 
              sx={{ mt: 0.5 }}
            />
            <Button
              size="small"
              variant="outlined"
              startIcon={<ExpandMore />}
              onClick={loadMoreLevels}
              disabled={currentMaxLevel >= 55}
            >
              {currentMaxLevel >= 55 ? '最大階層に到達' : `さらに表示 (+${Math.min(5, 55 - currentMaxLevel)}階層)`}
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* 検索・フィルター */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              label="会員検索"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="会員番号（11桁）"
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>レベルフィルター</InputLabel>
              <Select
                value={filterLevel}
                label="レベルフィルター"
                onChange={(e) => setFilterLevel(e.target.value)}
              >
                <MenuItem value="">すべて</MenuItem>
                <MenuItem value={1}>レベル1</MenuItem>
                <MenuItem value={2}>レベル2</MenuItem>
                <MenuItem value={3}>レベル3</MenuItem>
                <MenuItem value={4}>レベル4</MenuItem>
                <MenuItem value={5}>レベル5以上</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Button
              fullWidth
              variant={showActiveOnly ? "contained" : "outlined"}
              color={showActiveOnly ? "success" : "inherit"}
              startIcon={<FilterList />}
              onClick={() => setShowActiveOnly(!showActiveOnly)}
              sx={{ whiteSpace: 'nowrap' }}
            >
              {showActiveOnly ? "全メンバー" : "アクティブのみ"}
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<Download />}
                onClick={() => downloadCurrentView()}
              >
                現在表示CSV出力
              </Button>
              <IconButton onClick={fetchOrganizationData} color="primary">
                <Refresh />
              </IconButton>
            </Box>
          </Grid>
        </Grid>
      </Paper>


      {/* 組織ツリー表示 */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <Typography variant="h6" fontWeight="600">
              組織階層構造
            </Typography>
            
            {/* 統計情報をヘッダーに統合 */}
            <Box sx={{ display: 'flex', gap: 3, alignItems: 'center' }}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" fontWeight="bold" color="success.main">
                    {organizationStats?.active_members || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    アクティブ
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" fontWeight="bold" color="error.main">
                    {organizationStats?.withdrawn_members || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    退会者
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" fontWeight="bold">
                    {organizationStats?.max_level || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    最大階層
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Box>
          
          <Box>
            <Alert severity="info" sx={{ fontSize: '0.875rem' }}>
              💡 要件: 退会時は手動で組織調整を行います（自動圧縮なし）
            </Alert>
          </Box>
        </Box>

        {loading ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography>組織データを読み込み中...</Typography>
          </Box>
        ) : (
          <Box>
            {(debouncedSearchQuery || filterLevel !== '' ? filteredData : organizationData).map(rootNode => (
              <OrganizationTreeNode
                key={rootNode.id}
                node={rootNode}
                depth={0}
              />
            ))}
          </Box>
        )}
      </Paper>

      {/* 紹介者変更ダイアログ */}
      <Dialog
        open={showSponsorDialog}
        onClose={() => setShowSponsorDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          紹介者変更 - {selectedMember?.name}
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            紹介者変更は組織構造に重大な影響を与えます。慎重に実行してください。
          </Alert>
          
          <TextField
            fullWidth
            label="新しい紹介者の会員番号"
            margin="normal"
            placeholder="11桁の会員番号を入力"
          />
          
          <TextField
            fullWidth
            label="変更理由"
            margin="normal"
            multiline
            rows={3}
            placeholder="紹介者変更の理由を詳しく記入してください"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSponsorDialog(false)}>
            キャンセル
          </Button>
          <Button 
            variant="contained"
            color="warning"
            onClick={() => {
              console.log('紹介者変更実行');
              setShowSponsorDialog(false);
            }}
          >
            変更実行
          </Button>
        </DialogActions>
      </Dialog>

      {/* 会員詳細ダイアログ */}
      <MemberDetail
        open={showMemberDetail}
        member={selectedMember}
        onClose={() => setShowMemberDetail(false)}
      />
    </Box>
  );
};

export default Organization;
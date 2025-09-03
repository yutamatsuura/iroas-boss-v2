import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  Typography,
  Divider,
  Box,
  Chip,
} from '@mui/material';
import { Member } from '../services/memberService';
import { OrganizationNode } from '../services/organizationService';

interface MemberDetailProps {
  open: boolean;
  member: Member | OrganizationNode | null;
  onClose: () => void;
}

// 表示用マッピング
const statusDisplayMap: Record<string, string> = {
  'ACTIVE': 'アクティブ',
  'INACTIVE': '休会中',
  'WITHDRAWN': '退会済',
};

const titleDisplayMap: Record<string, string> = {
  'NONE': '称号なし',
  'KNIGHT_DAME': 'ナイト/デイム',
  'LORD_LADY': 'ロード/レディ',
  'KING_QUEEN': 'キング/クイーン',
  'EMPEROR_EMPRESS': 'エンペラー/エンブレス',
};

const userTypeDisplayMap: Record<string, string> = {
  'NORMAL': '通常',
  'ATTENTION': '注意',
};

const planDisplayMap: Record<string, string> = {
  'HERO': 'ヒーロープラン',
  'TEST': 'テストプラン',
};

const paymentMethodDisplayMap: Record<string, string> = {
  'CARD': 'カード決済',
  'TRANSFER': '口座振替',
  'BANK': '銀行振込',
  'INFOCART': 'インフォカート',
};

const genderDisplayMap: Record<string, string> = {
  'MALE': '男性',
  'FEMALE': '女性',
  'OTHER': 'その他',
};

const accountTypeDisplayMap: Record<string, string> = {
  'ORDINARY': '普通',
  'CHECKING': '当座',
};

const MemberDetail: React.FC<MemberDetailProps> = ({ open, member, onClose }) => {
  if (!member) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'success';
      case 'INACTIVE': return 'warning';
      case 'WITHDRAWN': return 'error';
      default: return 'default';
    }
  };

  const DetailRow = ({ label, value }: { label: string; value: any }) => (
    <Grid container spacing={2} sx={{ mb: 1 }}>
      <Grid item xs={4}>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
      </Grid>
      <Grid item xs={8}>
        <Typography variant="body2">
          {value || '-'}
        </Typography>
      </Grid>
    </Grid>
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={2}>
          会員詳細
          <Chip 
            label={statusDisplayMap[member.status] || member.status}
            color={getStatusColor(member.status)}
            size="small"
          />
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        {/* 基本情報 */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>基本情報</Typography>
          <DetailRow label="会員番号" value={member.member_number || (member as any).memberNumber} />
          <DetailRow label="氏名" value={member.name} />
          <DetailRow label="メールアドレス" value={(member as any).email || '-'} />
          <DetailRow label="ステータス" value={statusDisplayMap[member.status] || member.status} />
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* MLM情報 */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>MLM情報</Typography>
          <DetailRow label="称号" value={titleDisplayMap[member.title] || member.title} />
          <DetailRow label="ユーザータイプ" value={userTypeDisplayMap[(member as any).user_type || (member as any).userType] || (member as any).user_type || (member as any).userType} />
          <DetailRow label="加入プラン" value={planDisplayMap[(member as any).plan] || (member as any).plan} />
          <DetailRow label="決済方法" value={paymentMethodDisplayMap[(member as any).payment_method || (member as any).paymentMethod] || (member as any).payment_method || (member as any).paymentMethod} />
          {'level' in member && <DetailRow label="階層レベル" value={member.level} />}
          {'hierarchy_path' in member && <DetailRow label="組織階層" value={member.hierarchy_path} />}
          {'is_direct' in member && <DetailRow label="直紹介" value={member.is_direct ? 'はい' : 'いいえ'} />}
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* 日付情報 */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>日付情報</Typography>
          <DetailRow label="登録日" value={member.registration_date || member.registrationDate} />
          <DetailRow label="退会日" value={member.withdrawal_date || member.withdrawalDate} />
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* 連絡先情報 */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>連絡先情報</Typography>
          <DetailRow label="電話番号" value={member.phone} />
          <DetailRow label="性別" value={genderDisplayMap[member.gender] || member.gender} />
          <DetailRow label="郵便番号" value={member.postal_code || member.postalCode} />
          <DetailRow label="都道府県" value={member.prefecture} />
          <DetailRow label="住所2" value={member.address2} />
          <DetailRow label="住所3" value={member.address3} />
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* 組織情報 */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>組織情報</Typography>
          <DetailRow label="直上者ID" value={member.upline_id || member.uplineId} />
          <DetailRow label="直上者名" value={member.upline_name || member.uplineName} />
          <DetailRow label="紹介者ID" value={member.referrer_id || member.referrerId} />
          <DetailRow label="紹介者名" value={member.referrer_name || member.referrerName} />
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* 銀行情報 */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>銀行情報</Typography>
          <DetailRow label="銀行名" value={member.bank_name || member.bankName} />
          {(member.bank_name || member.bankName) === 'ゆうちょ銀行' ? (
            <>
              <DetailRow label="ゆうちょ記号" value={member.yucho_symbol || member.yuchoSymbol} />
              <DetailRow label="ゆうちょ番号" value={member.yucho_number || member.yuchoNumber} />
            </>
          ) : (
            <>
              <DetailRow label="銀行コード" value={member.bank_code || member.bankCode} />
              <DetailRow label="支店名" value={member.branch_name || member.branchName} />
              <DetailRow label="支店コード" value={member.branch_code || member.branchCode} />
              <DetailRow label="口座番号" value={member.account_number || member.accountNumber} />
              <DetailRow label="口座種別" value={accountTypeDisplayMap[member.account_type || member.accountType] || member.account_type || member.accountType} />
            </>
          )}
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* 売上情報（組織データの場合のみ） */}
        {'left_sales' in member && (
          <>
            <Divider sx={{ my: 2 }} />
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>売上情報</Typography>
              <DetailRow label="左ライン売上" value={`¥${member.left_sales?.toLocaleString() || 0}`} />
              <DetailRow label="右ライン売上" value={`¥${member.right_sales?.toLocaleString() || 0}`} />
              <DetailRow label="左人数" value={member.left_count} />
              <DetailRow label="右人数" value={member.right_count} />
              <DetailRow label="新規購入" value={`¥${(member as any).new_purchase?.toLocaleString() || 0}`} />
              <DetailRow label="リピート購入" value={`¥${(member as any).repeat_purchase?.toLocaleString() || 0}`} />
              <DetailRow label="追加購入" value={`¥${(member as any).additional_purchase?.toLocaleString() || 0}`} />
              <DetailRow label="総売上" value={`¥${(member as any).total_sales?.toLocaleString() || 0}`} />
            </Box>
          </>
        )}

        {/* その他 */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>その他</Typography>
          <DetailRow label="備考" value={(member as any).notes || '-'} />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>閉じる</Button>
      </DialogActions>
    </Dialog>
  );
};

export default MemberDetail;
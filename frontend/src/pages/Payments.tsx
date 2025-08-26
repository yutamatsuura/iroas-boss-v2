import React from 'react';
import { Box, Typography } from '@mui/material';

/**
 * P-004: 決済管理
 * Univapay CSV出力、決済結果取込、手動決済記録を統合
 */
const Payments: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4">決済管理</Typography>
      <Typography variant="body1" sx={{ mt: 2 }}>
        決済管理ページ - 実装中（Step 17で完全実装）
      </Typography>
    </Box>
  );
};

export default Payments;
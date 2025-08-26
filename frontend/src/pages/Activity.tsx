import React from 'react';
import { Box, Typography } from '@mui/material';

/**
 * P-007: アクティビティログ
 * システムで実行された全操作の履歴を時系列で確認
 */
const Activity: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4">アクティビティログ</Typography>
      <Typography variant="body1" sx={{ mt: 2 }}>
        アクティビティログページ - 実装中（Step 17で完全実装）
      </Typography>
    </Box>
  );
};

export default Activity;
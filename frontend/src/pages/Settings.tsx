import React from 'react';
import { Box, Typography } from '@mui/material';

/**
 * P-008: マスタ設定
 * システム固定値の確認表示のみ（変更不可）
 */
const Settings: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4">マスタ設定</Typography>
      <Typography variant="body1" sx={{ mt: 2 }}>
        マスタ設定ページ - 実装中（Step 17で完全実装）
      </Typography>
    </Box>
  );
};

export default Settings;
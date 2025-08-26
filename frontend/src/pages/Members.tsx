import React from 'react';
import { Box, Typography } from '@mui/material';

/**
 * P-002: 会員管理
 * 会員の登録・編集・退会処理・組織管理を統合
 */
const Members: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4">会員管理</Typography>
      <Typography variant="body1" sx={{ mt: 2 }}>
        会員管理ページ - 実装中（Step 17で完全実装）
      </Typography>
    </Box>
  );
};

export default Members;
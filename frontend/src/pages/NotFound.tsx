import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

/**
 * 404 Not Found ページ
 */
const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
      }}
    >
      <Typography variant="h1" color="primary" fontWeight="bold">
        404
      </Typography>
      <Typography variant="h4" color="text.primary" sx={{ mt: 2 }}>
        ページが見つかりません
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
        お探しのページは存在しないか、移動した可能性があります。
      </Typography>
      <Button
        variant="contained"
        color="primary"
        onClick={() => navigate('/')}
        sx={{ mt: 4 }}
      >
        ダッシュボードに戻る
      </Button>
    </Box>
  );
};

export default NotFound;
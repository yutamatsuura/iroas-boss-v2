import { createTheme, ThemeOptions } from '@mui/material/styles';

/**
 * IROAS BOSS V2 エンタープライズテーマ
 * デザインシステムに基づく厳密なテーマ定義
 * Navy Blue (#1e3a8a) を基調としたプロフェッショナルデザイン
 */

// カスタムカラーパレット定義
declare module '@mui/material/styles' {
  interface Palette {
    neutral: {
      main: string;
      light: string;
      dark: string;
      contrastText: string;
    };
  }
  interface PaletteOptions {
    neutral?: {
      main?: string;
      light?: string;
      dark?: string;
      contrastText?: string;
    };
  }
}

const themeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    // プライマリカラー - Navy Blue
    primary: {
      main: '#1e3a8a',
      light: '#3b82f6',
      dark: '#1e40af',
      contrastText: '#ffffff',
    },
    // セカンダリカラー - Blue
    secondary: {
      main: '#3b82f6',
      light: '#60a5fa',
      dark: '#2563eb',
      contrastText: '#ffffff',
    },
    // エラーカラー
    error: {
      main: '#ef4444',
      light: '#fca5a5',
      dark: '#dc2626',
      contrastText: '#ffffff',
    },
    // 警告カラー
    warning: {
      main: '#f59e0b',
      light: '#fbbf24',
      dark: '#d97706',
      contrastText: '#ffffff',
    },
    // 成功カラー
    success: {
      main: '#10b981',
      light: '#34d399',
      dark: '#059669',
      contrastText: '#ffffff',
    },
    // 情報カラー
    info: {
      main: '#3b82f6',
      light: '#60a5fa',
      dark: '#2563eb',
      contrastText: '#ffffff',
    },
    // ニュートラルカラー
    neutral: {
      main: '#64748b',
      light: '#94a3b8',
      dark: '#475569',
      contrastText: '#ffffff',
    },
    // 背景カラー
    background: {
      default: '#f1f5f9',
      paper: '#ffffff',
    },
    // テキストカラー
    text: {
      primary: '#1e293b',
      secondary: '#475569',
      disabled: '#94a3b8',
    },
    // 分割線カラー
    divider: '#e2e8f0',
  },
  // タイポグラフィ設定
  typography: {
    fontFamily: '"Inter", "Noto Sans JP", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.01562em',
    },
    h2: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.3,
      letterSpacing: '-0.00833em',
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '0em',
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '0.0075em',
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.5,
      letterSpacing: '0em',
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.6,
      letterSpacing: '0.0075em',
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.75,
      letterSpacing: '0.00938em',
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.57,
      letterSpacing: '0.00714em',
    },
    body1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.5,
      letterSpacing: '0.00938em',
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.43,
      letterSpacing: '0.01071em',
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.75,
      letterSpacing: '0.02857em',
      textTransform: 'none', // 日本語対応のため大文字変換を無効化
    },
    caption: {
      fontSize: '0.75rem',
      fontWeight: 400,
      lineHeight: 1.66,
      letterSpacing: '0.03333em',
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 400,
      lineHeight: 2.66,
      letterSpacing: '0.08333em',
      textTransform: 'uppercase',
    },
  },
  // シェイプ設定
  shape: {
    borderRadius: 8,
  },
  // コンポーネント設定
  components: {
    // ボタンのデフォルトスタイル
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          textTransform: 'none',
          fontWeight: 500,
          padding: '8px 16px',
          transition: 'all 0.2s ease-in-out',
        },
        contained: {
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
          '&:hover': {
            boxShadow: '0 2px 4px 0 rgba(0, 0, 0, 0.1)',
          },
        },
        outlined: {
          borderWidth: '1.5px',
          '&:hover': {
            borderWidth: '1.5px',
          },
        },
      },
    },
    // カードのデフォルトスタイル
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          },
        },
      },
    },
    // テキストフィールドのデフォルトスタイル
    MuiTextField: {
      defaultProps: {
        variant: 'outlined',
        size: 'medium',
      },
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '&:hover fieldset': {
              borderColor: '#3b82f6',
            },
            '&.Mui-focused fieldset': {
              borderWidth: '2px',
            },
          },
        },
      },
    },
    // データグリッドのデフォルトスタイル
    MuiDataGrid: {
      styleOverrides: {
        root: {
          border: '1px solid #e2e8f0',
          borderRadius: 8,
          '& .MuiDataGrid-cell:focus': {
            outline: 'none',
          },
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: '#f8fafc',
            borderBottom: '2px solid #e2e8f0',
          },
          '& .MuiDataGrid-row:hover': {
            backgroundColor: '#f1f5f9',
          },
        },
      },
    },
    // アプリバーのデフォルトスタイル
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e3a8a',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        },
      },
    },
    // ドロワーのデフォルトスタイル
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#ffffff',
          borderRight: '1px solid #e2e8f0',
        },
      },
    },
    // リストアイテムボタンのデフォルトスタイル
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          margin: '2px 8px',
          '&:hover': {
            backgroundColor: '#f1f5f9',
          },
          '&.Mui-selected': {
            backgroundColor: '#eff6ff',
            borderLeft: '3px solid #1e3a8a',
            '&:hover': {
              backgroundColor: '#dbeafe',
            },
          },
        },
      },
    },
    // アラートのデフォルトスタイル
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
        standardSuccess: {
          backgroundColor: '#f0fdf4',
          color: '#166534',
        },
        standardError: {
          backgroundColor: '#fef2f2',
          color: '#991b1b',
        },
        standardWarning: {
          backgroundColor: '#fffbeb',
          color: '#92400e',
        },
        standardInfo: {
          backgroundColor: '#eff6ff',
          color: '#1e40af',
        },
      },
    },
  },
};

// テーマオブジェクトの作成
const theme = createTheme(themeOptions);

export default theme;
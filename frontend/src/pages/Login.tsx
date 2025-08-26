import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import LoginForm from '@/components/auth/LoginForm';

/**
 * ログインページ
 * Phase 21 MLM認証要件準拠
 */
const Login: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  // 既に認証済みの場合はダッシュボードにリダイレクト
  if (!isLoading && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <LoginForm
      onSuccess={() => {
        // ログイン成功時の処理は AuthProvider で自動的にリダイレクトされる
      }}
    />
  );
};

export default Login;
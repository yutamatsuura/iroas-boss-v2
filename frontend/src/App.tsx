import React from 'react';
import { useRoutes } from 'react-router-dom';
import { routes } from './router/routes';
import { AuthProvider } from './contexts/AuthContext';

/**
 * ルートアプリケーションコンポーネント
 * Phase 21認証機能統合
 */
const App: React.FC = () => {
  const routing = useRoutes(routes);
  
  return (
    <AuthProvider>
      {routing}
    </AuthProvider>
  );
};

export default App;
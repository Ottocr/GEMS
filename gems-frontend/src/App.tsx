import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { AnimatePresence } from 'framer-motion';
import theme from './theme';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './pages/Dashboard/Dashboard';
import RiskManagement from './pages/RiskManagement/RiskManagement';
import AssetDetails from './pages/AssetDetails/AssetDetails';
import Reports from './pages/Reports/Reports';
import Settings from './pages/Settings/Settings';
import Login from './pages/Login/Login';
import { store } from './store';
import { isAuthenticated } from './services/authService';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  
  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

// Global styles
const globalStyles = `
  body {
    margin: 0;
    padding: 0;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    overflow-x: hidden;
  }

  /* Leaflet map container styles */
  .leaflet-container {
    width: 100%;
    height: 100%;
    z-index: 1;
    font-family: inherit;
  }

  .leaflet-popup-content-wrapper {
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .leaflet-popup-content {
    margin: 8px;
  }

  /* Custom scrollbar */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.05);
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 0, 0, 0.3);
  }

  /* Smooth transitions */
  * {
    transition: background-color 0.2s ease,
                border-color 0.2s ease,
                box-shadow 0.2s ease;
  }

  /* Page transitions */
  .page-transition-enter {
    opacity: 0;
    transform: translateY(20px);
  }

  .page-transition-enter-active {
    opacity: 1;
    transform: translateY(0);
    transition: opacity 300ms, transform 300ms;
  }

  .page-transition-exit {
    opacity: 1;
    transform: translateY(0);
  }

  .page-transition-exit-active {
    opacity: 0;
    transform: translateY(-20px);
    transition: opacity 300ms, transform 300ms;
  }
`;

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <style>{globalStyles}</style>
        <Router>
          <AnimatePresence mode="wait">
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />

              {/* Protected Routes */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <MainLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Dashboard />} />
                <Route path="risk-management" element={<RiskManagement />} />
                <Route path="assets/:assetId" element={<AssetDetails />} />
                <Route path="reports" element={<Reports />} />
                <Route path="settings" element={<Settings />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Routes>
          </AnimatePresence>
        </Router>
      </ThemeProvider>
    </Provider>
  );
};

export default App;

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import reportWebVitals from './reportWebVitals';
import axios from 'axios';

// Set up axios defaults
axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Add global styles for leaflet maps and other components
const style = document.createElement('style');
style.textContent = `
  /* Leaflet map container styles */
  .leaflet-container {
    width: 100%;
    height: 100%;
    z-index: 1;
  }

  /* Custom marker styles */
  .custom-marker {
    background-color: #1a237e;
    border-radius: 50%;
    border: 2px solid white;
    width: 12px;
    height: 12px;
  }

  .custom-marker.high-risk {
    background-color: #c62828;
  }

  .custom-marker.medium-risk {
    background-color: #f57c00;
  }

  .custom-marker.low-risk {
    background-color: #2e7d32;
  }

  /* Risk level indicator styles */
  .risk-level {
    padding: 4px 8px;
    border-radius: 4px;
    font-weight: 500;
    font-size: 0.875rem;
  }

  .risk-level.critical {
    background-color: #ffebee;
    color: #c62828;
  }

  .risk-level.high {
    background-color: #fff3e0;
    color: #e65100;
  }

  .risk-level.medium {
    background-color: #fff8e1;
    color: #f57f17;
  }

  .risk-level.low {
    background-color: #e8f5e9;
    color: #2e7d32;
  }

  /* Scrollbar styles */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: #f1f1f1;
  }

  ::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: #555;
  }

  /* Global styles */
  body {
    margin: 0;
    padding: 0;
    font-family: 'Roboto', 'Helvetica', 'Arial', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  /* Loading overlay styles */
  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(255, 255, 255, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
`;
document.head.appendChild(style);

// Create root and render app
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Performance monitoring
reportWebVitals(console.log);

// Add axios response interceptor for handling auth errors
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

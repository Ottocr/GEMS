import axios from 'axios';

// Configure axios defaults
axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Add a request interceptor to include the auth token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle auth errors
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const login = async (username: string, password: string) => {
  try {
    const response = await axios.post('/api/token-auth/', { username, password });
    const { token } = response.data;
    localStorage.setItem('authToken', token);
    return token;
  } catch (error) {
    throw error;
  }
};

export const logout = () => {
  localStorage.removeItem('authToken');
  window.location.href = '/login';
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('authToken');
};

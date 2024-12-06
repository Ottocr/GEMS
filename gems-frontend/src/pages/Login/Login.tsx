import React, { useState } from 'react';
import { 
  Box, 
  Paper, 
  TextField, 
  Button, 
  Typography, 
  useTheme,
  Alert,
} from '@mui/material';
import { motion } from 'framer-motion';
import { login } from '../../services/authService';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to login. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: theme.palette.background.default,
        p: 3,
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Paper
          elevation={4}
          sx={{
            p: 4,
            width: '100%',
            maxWidth: 400,
            borderRadius: 3,
          }}
        >
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Typography 
              variant="h4" 
              component="h1" 
              color="primary"
              sx={{ 
                fontWeight: 600,
                mb: 1,
              }}
            >
              GEMS
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Global Enterprise Monitoring System
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Username"
              variant="outlined"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              sx={{ mb: 2 }}
              disabled={loading}
            />
            <TextField
              fullWidth
              label="Password"
              type="password"
              variant="outlined"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              sx={{ mb: 3 }}
              disabled={loading}
            />
            <Button
              fullWidth
              type="submit"
              variant="contained"
              size="large"
              disabled={loading}
              sx={{
                py: 1.5,
                borderRadius: 2,
                textTransform: 'none',
                fontSize: '1rem',
              }}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
        </Paper>
      </motion.div>
    </Box>
  );
};

export default Login;

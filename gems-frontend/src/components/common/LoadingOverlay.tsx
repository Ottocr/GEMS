import React from 'react';
import { Box, CircularProgress, Typography, useTheme, alpha } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

interface LoadingOverlayProps {
  loading: boolean;
  children: React.ReactNode;
  message?: string;
  fullscreen?: boolean;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  loading,
  children,
  message = 'Loading...',
  fullscreen = false,
}) => {
  const theme = useTheme();

  return (
    <Box position="relative" sx={{ height: fullscreen ? '100vh' : '100%' }}>
      {children}
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: alpha(theme.palette.background.paper, 0.7),
              backdropFilter: 'blur(4px)',
              zIndex: theme.zIndex.modal,
            }}
          >
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.8 }}
              transition={{ duration: 0.2 }}
            >
              <Box sx={{ textAlign: 'center' }}>
                <CircularProgress
                  size={48}
                  thickness={4}
                  sx={{
                    color: theme.palette.primary.main,
                    mb: 2,
                  }}
                />
                <Typography
                  variant="body1"
                  sx={{
                    color: theme.palette.text.primary,
                    fontWeight: 500,
                  }}
                >
                  {message}
                </Typography>
              </Box>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
};

export const PageLoader: React.FC<{ message?: string }> = ({ message }) => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: theme.palette.background.default,
      }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress
            size={56}
            thickness={4}
            sx={{
              color: theme.palette.primary.main,
              mb: 3,
            }}
          />
          <Typography
            variant="h6"
            sx={{
              color: theme.palette.text.primary,
              fontWeight: 500,
            }}
          >
            {message || 'Loading...'}
          </Typography>
        </Box>
      </motion.div>
    </Box>
  );
};

export default LoadingOverlay;

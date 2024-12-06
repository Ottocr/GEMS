import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  CircularProgress,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

type DialogType = 'warning' | 'error' | 'info';

interface ConfirmationDialogProps {
  open: boolean;
  title: string;
  message: string | React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  type?: DialogType;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  type = 'warning',
  loading = false,
  onConfirm,
  onCancel,
}) => {
  const getIcon = () => {
    switch (type) {
      case 'warning':
        return <WarningIcon sx={{ color: 'warning.main', fontSize: 40 }} />;
      case 'error':
        return <ErrorIcon sx={{ color: 'error.main', fontSize: 40 }} />;
      case 'info':
        return <InfoIcon sx={{ color: 'info.main', fontSize: 40 }} />;
    }
  };

  const getColor = () => {
    switch (type) {
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      case 'info':
        return 'info';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onCancel}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderTop: 3,
          borderColor: `${getColor()}.main`,
        },
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {getIcon()}
          <Typography variant="h6" component="span">
            {title}
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        {typeof message === 'string' ? (
          <Typography variant="body1">{message}</Typography>
        ) : (
          message
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={onCancel}
          color="inherit"
          disabled={loading}
        >
          {cancelLabel}
        </Button>
        <Button
          onClick={onConfirm}
          color={getColor()}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : undefined}
        >
          {loading ? 'Processing...' : confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmationDialog;

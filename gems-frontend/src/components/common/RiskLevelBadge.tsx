import React from 'react';
import { Box, Typography, useTheme, alpha } from '@mui/material';
import { motion } from 'framer-motion';

type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

interface RiskLevelBadgeProps {
  level: RiskLevel;
  score?: number;
  showScore?: boolean;
  size?: 'small' | 'medium' | 'large';
  animate?: boolean;
}

const RiskLevelBadge: React.FC<RiskLevelBadgeProps> = ({ 
  level, 
  score, 
  showScore = false,
  size = 'medium',
  animate = true,
}) => {
  const theme = useTheme();

  const getColorsByLevel = (level: RiskLevel) => {
    switch (level) {
      case 'CRITICAL':
        return {
          bg: alpha(theme.palette.error.main, 0.1),
          border: alpha(theme.palette.error.main, 0.2),
          text: theme.palette.error.main,
        };
      case 'HIGH':
        return {
          bg: alpha(theme.palette.warning.main, 0.1),
          border: alpha(theme.palette.warning.main, 0.2),
          text: theme.palette.warning.main,
        };
      case 'MEDIUM':
        return {
          bg: alpha(theme.palette.info.main, 0.1),
          border: alpha(theme.palette.info.main, 0.2),
          text: theme.palette.info.main,
        };
      case 'LOW':
        return {
          bg: alpha(theme.palette.success.main, 0.1),
          border: alpha(theme.palette.success.main, 0.2),
          text: theme.palette.success.main,
        };
    }
  };

  const getSizeStyles = (size: 'small' | 'medium' | 'large') => {
    switch (size) {
      case 'small':
        return {
          py: 0.25,
          px: 1,
          fontSize: '0.75rem',
          scoreSize: '0.75rem',
        };
      case 'large':
        return {
          py: 1,
          px: 2,
          fontSize: '1rem',
          scoreSize: '1rem',
        };
      default:
        return {
          py: 0.5,
          px: 1.5,
          fontSize: '0.875rem',
          scoreSize: '0.875rem',
        };
    }
  };

  const colors = getColorsByLevel(level);
  const sizeStyles = getSizeStyles(size);

  const BadgeContent = () => (
    <>
      <Typography
        variant="body2"
        component="span"
        sx={{
          fontSize: sizeStyles.fontSize,
          fontWeight: 600,
          color: colors.text,
        }}
      >
        {level}
      </Typography>
      {showScore && score !== undefined && (
        <Typography
          variant="body2"
          component="span"
          sx={{
            ml: 0.5,
            fontSize: sizeStyles.scoreSize,
            color: alpha(colors.text, 0.8),
          }}
        >
          ({score.toFixed(1)})
        </Typography>
      )}
    </>
  );

  if (!animate) {
    return (
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          py: sizeStyles.py,
          px: sizeStyles.px,
          borderRadius: '16px',
          backgroundColor: colors.bg,
          border: `1px solid ${colors.border}`,
        }}
      >
        <BadgeContent />
      </Box>
    );
  }

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          py: sizeStyles.py,
          px: sizeStyles.px,
          borderRadius: '16px',
          backgroundColor: colors.bg,
          border: `1px solid ${colors.border}`,
          transition: theme.transitions.create(
            ['background-color', 'border-color'],
            {
              duration: theme.transitions.duration.short,
            }
          ),
          '&:hover': {
            backgroundColor: alpha(colors.bg, 0.8),
            border: `1px solid ${alpha(colors.border, 0.8)}`,
          },
        }}
      >
        <BadgeContent />
      </Box>
    </motion.div>
  );
};

export default RiskLevelBadge;

// Helper function to determine risk level from score
export const getRiskLevel = (score: number): RiskLevel => {
  if (score <= 3) return 'LOW';
  if (score <= 5) return 'MEDIUM';
  if (score <= 8) return 'HIGH';
  return 'CRITICAL';
};

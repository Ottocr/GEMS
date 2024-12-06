import React from 'react';
import { 
  Typography, 
  Box, 
  IconButton, 
  useTheme, 
  alpha,
  Paper,
} from '@mui/material';
import { 
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
    label?: string;
  };
  color?: string;
  delay?: number;
  onClick?: () => void;
  actions?: React.ReactNode;
  subtitle?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon,
  trend,
  color,
  delay = 0,
  onClick,
  actions,
  subtitle,
}) => {
  const theme = useTheme();
  const cardColor = color || theme.palette.primary.main;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        duration: 0.4, 
        delay,
        ease: [0.4, 0, 0.2, 1],
      }}
      style={{ height: '100%' }}
    >
      <Paper
        elevation={1}
        sx={{
          height: '100%',
          position: 'relative',
          overflow: 'hidden',
          cursor: onClick ? 'pointer' : 'default',
          p: 3,
          borderRadius: 3,
          backgroundColor: theme.palette.background.paper,
          transition: theme.transitions.create(['transform', 'box-shadow'], {
            duration: theme.transitions.duration.standard,
          }),
          '&:hover': onClick ? {
            transform: 'translateY(-4px)',
            boxShadow: theme.shadows[8],
            '& .stats-card-bg-icon': {
              transform: 'scale(1.1)',
            },
          } : {},
        }}
        onClick={onClick}
      >
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          {/* Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box>
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
                sx={{ 
                  textTransform: 'uppercase', 
                  letterSpacing: 0.5,
                  fontWeight: 500,
                }}
              >
                {title}
              </Typography>
              {subtitle && (
                <Typography variant="caption" color="text.secondary">
                  {subtitle}
                </Typography>
              )}
            </Box>
            {actions || (
              <IconButton size="small">
                <MoreVertIcon fontSize="small" />
              </IconButton>
            )}
          </Box>

          {/* Value and Icon */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: trend ? 2 : 0 }}>
            <Typography
              variant="h4"
              component="div"
              sx={{ 
                color: cardColor,
                fontWeight: 600,
              }}
            >
              {value}
            </Typography>
            <Box 
              sx={{ 
                color: cardColor,
                backgroundColor: alpha(cardColor, 0.1),
                borderRadius: '50%',
                p: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {icon}
            </Box>
          </Box>

          {/* Trend */}
          {trend && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                color: trend.isPositive ? theme.palette.success.main : theme.palette.error.main,
              }}
            >
              {trend.isPositive ? (
                <TrendingUpIcon fontSize="small" />
              ) : (
                <TrendingDownIcon fontSize="small" />
              )}
              <Typography variant="body2" component="span" sx={{ ml: 0.5, fontWeight: 500 }}>
                {trend.value}%
              </Typography>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ ml: 1 }}
              >
                {trend.label || 'vs last month'}
              </Typography>
            </Box>
          )}
        </Box>

        {/* Background Icon */}
        <Box
          className="stats-card-bg-icon"
          sx={{
            position: 'absolute',
            right: -20,
            bottom: -20,
            opacity: 0.05,
            transform: 'scale(4)',
            color: cardColor,
            transition: theme.transitions.create('transform', {
              duration: theme.transitions.duration.standard,
            }),
          }}
        >
          {icon}
        </Box>
      </Paper>
    </motion.div>
  );
};

export default StatsCard;

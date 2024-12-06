import React from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Switch,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Security as SecurityIcon,
  Language as LanguageIcon,
  Palette as PaletteIcon,
  DataUsage as DataUsageIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import LoadingOverlay from '../../components/common/LoadingOverlay';

const settingsItems = [
  {
    title: 'Notifications',
    description: 'Configure alert and notification preferences',
    icon: NotificationsIcon,
    enabled: true,
  },
  {
    title: 'Security',
    description: 'Manage security settings and permissions',
    icon: SecurityIcon,
    enabled: true,
  },
  {
    title: 'Language',
    description: 'Set your preferred language',
    icon: LanguageIcon,
    enabled: false,
  },
  {
    title: 'Theme',
    description: 'Customize the application appearance',
    icon: PaletteIcon,
    enabled: false,
  },
  {
    title: 'Data Management',
    description: 'Configure data retention and export settings',
    icon: DataUsageIcon,
    enabled: false,
  },
];

const Settings: React.FC = () => {
  return (
    <LoadingOverlay loading={false}>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" color="text.primary" sx={{ fontWeight: 600, mb: 1 }}>
            Settings
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Configure system preferences and options
          </Typography>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper sx={{ borderRadius: 2 }}>
              <List>
                {settingsItems.map((item, index) => (
                  <React.Fragment key={item.title}>
                    <ListItem
                      secondaryAction={
                        <Switch
                          edge="end"
                          disabled={!item.enabled}
                        />
                      }
                    >
                      <ListItemIcon>
                        <item.icon color={item.enabled ? 'primary' : 'disabled'} />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography
                            variant="subtitle1"
                            sx={{
                              fontWeight: 500,
                              color: item.enabled ? 'text.primary' : 'text.disabled',
                            }}
                          >
                            {item.title}
                          </Typography>
                        }
                        secondary={
                          <Typography
                            variant="body2"
                            sx={{
                              color: item.enabled ? 'text.secondary' : 'text.disabled',
                            }}
                          >
                            {item.description}
                            {!item.enabled && ' (Coming Soon)'}
                          </Typography>
                        }
                      />
                    </ListItem>
                    {index < settingsItems.length - 1 && <Divider component="li" />}
                  </React.Fragment>
                ))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      </motion.div>
    </LoadingOverlay>
  );
};

export default Settings;

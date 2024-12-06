import React, { useState } from 'react';
import { 
  Box, 
  AppBar, 
  Toolbar, 
  IconButton, 
  Typography, 
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Tooltip,
  useTheme,
  alpha
} from '@mui/material';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Security as SecurityIcon,
  Business as BusinessIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  ChevronLeft as ChevronLeftIcon,
} from '@mui/icons-material';

const DRAWER_WIDTH = 240;

const menuItems = [
  { path: '/', label: 'Dashboard', icon: DashboardIcon },
  { path: '/risk-management', label: 'Risk Management', icon: SecurityIcon },
  { path: '/assets', label: 'Assets', icon: BusinessIcon },
  { path: '/reports', label: 'Reports', icon: AssessmentIcon },
  { path: '/settings', label: 'Settings', icon: SettingsIcon },
];

const MainLayout: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(true);

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerOpen ? DRAWER_WIDTH : 64}px)` },
          ml: { sm: `${drawerOpen ? DRAWER_WIDTH : 64}px` },
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Toolbar>
          <IconButton
            color="primary"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            {drawerOpen ? <ChevronLeftIcon /> : <MenuIcon />}
          </IconButton>
          <Typography variant="h6" color="primary" noWrap component="div" sx={{ flexGrow: 1 }}>
            GEMS
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Side Navigation */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerOpen ? DRAWER_WIDTH : 64,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerOpen ? DRAWER_WIDTH : 64,
            boxSizing: 'border-box',
            borderRight: `1px solid ${alpha(theme.palette.primary.main, 0.08)}`,
            backgroundColor: theme.palette.background.paper,
            transition: theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
            overflowX: 'hidden',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'hidden' }}>
          <List>
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isSelected = location.pathname === item.path;

              return (
                <ListItem key={item.path} disablePadding>
                  <Tooltip 
                    title={!drawerOpen ? item.label : ''} 
                    placement="right"
                    arrow
                  >
                    <ListItemButton
                      onClick={() => navigate(item.path)}
                      selected={isSelected}
                      sx={{
                        minHeight: 48,
                        justifyContent: drawerOpen ? 'initial' : 'center',
                        px: 2.5,
                        '&.Mui-selected': {
                          backgroundColor: alpha(theme.palette.primary.main, 0.08),
                          '&:hover': {
                            backgroundColor: alpha(theme.palette.primary.main, 0.12),
                          },
                        },
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          minWidth: 0,
                          mr: drawerOpen ? 2 : 'auto',
                          justifyContent: 'center',
                          color: isSelected ? theme.palette.primary.main : theme.palette.text.secondary,
                        }}
                      >
                        <Icon />
                      </ListItemIcon>
                      <ListItemText 
                        primary={item.label} 
                        sx={{ 
                          opacity: drawerOpen ? 1 : 0,
                          color: isSelected ? theme.palette.primary.main : theme.palette.text.primary,
                        }}
                      />
                    </ListItemButton>
                  </Tooltip>
                </ListItem>
              );
            })}
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 2,
          width: { sm: `calc(100% - ${drawerOpen ? DRAWER_WIDTH : 64}px)` },
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          backgroundColor: theme.palette.background.default,
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
};

export default MainLayout;

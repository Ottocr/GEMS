import React from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';
import { motion } from 'framer-motion';
import LoadingOverlay from '../../components/common/LoadingOverlay';

const Reports: React.FC = () => {
  return (
    <LoadingOverlay loading={false}>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" color="text.primary" sx={{ fontWeight: 600, mb: 1 }}>
            Reports
          </Typography>
          <Typography variant="body1" color="text.secondary">
            View and generate security risk reports
          </Typography>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Coming Soon
              </Typography>
              <Typography variant="body1" color="text.secondary">
                The reports feature is currently under development. Check back soon for updates.
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </motion.div>
    </LoadingOverlay>
  );
};

export default Reports;

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Grid,
  Typography,
  Paper,
  TextField,
  MenuItem,
} from '@mui/material';
import { useAppDispatch, useAppSelector } from '../../store';
import {
  fetchAssetDetails,
  reportBarrierIssue,
} from '../../store/slices/assetSlice';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import MapComponent from '../../components/common/MapComponent';
import DataTable from '../../components/common/DataTable';
import RiskLevelBadge, { getRiskLevel } from '../../components/common/RiskLevelBadge';
import ConfirmationDialog from '../../components/common/ConfirmationDialog';
import { TableColumn } from '../../types';

const barrierColumns: TableColumn[] = [
  { id: 'name', label: 'Barrier Name', minWidth: 170 },
  { id: 'category', label: 'Category', minWidth: 130 },
  {
    id: 'effectiveness',
    label: 'Effectiveness',
    minWidth: 100,
    align: 'right',
    format: (value: number) => value.toFixed(1),
  },
  {
    id: 'status',
    label: 'Status',
    minWidth: 100,
    align: 'right',
  },
];

const riskMatrixColumns: TableColumn[] = [
  { id: 'risk_type', label: 'Risk Type', minWidth: 170 },
  {
    id: 'score',
    label: 'Risk Score',
    minWidth: 100,
    align: 'right',
    format: (value: number) => value.toFixed(1),
  },
  {
    id: 'level',
    label: 'Risk Level',
    minWidth: 120,
    align: 'right',
    format: (value: string) => <RiskLevelBadge level={value as any} />,
  },
];

const impactRatings = [
  { value: 'NO_IMPACT', label: 'No Impact' },
  { value: 'MINIMAL', label: 'Minimal Impact' },
  { value: 'SUBSTANTIAL', label: 'Substantial Impact' },
  { value: 'MAJOR', label: 'Major Impact' },
  { value: 'COMPROMISED', label: 'Barrier Compromised' },
];

const AssetDetails: React.FC = () => {
  const { assetId } = useParams<{ assetId: string }>();
  const dispatch = useAppDispatch();
  const { currentAsset, barriers, riskMatrix, loading, error } = useAppSelector(
    (state) => state.asset
  );

  const [barrierIssue, setBarrierIssue] = useState<{
    barrier: any;
    description: string;
    impactRating: string;
  } | null>(null);

  useEffect(() => {
    if (assetId) {
      dispatch(fetchAssetDetails(parseInt(assetId)));
    }
  }, [dispatch, assetId]);

  const handleReportIssue = (barrier: any) => {
    setBarrierIssue({
      barrier,
      description: '',
      impactRating: 'NO_IMPACT',
    });
  };

  const handleSubmitIssue = async () => {
    if (barrierIssue && assetId) {
      await dispatch(
        reportBarrierIssue({
          assetId: parseInt(assetId),
          barrierId: barrierIssue.barrier.id,
          description: barrierIssue.description,
          impactRating: barrierIssue.impactRating as any,
        })
      );
      setBarrierIssue(null);
      dispatch(fetchAssetDetails(parseInt(assetId))); // Refresh data
    }
  };

  if (!currentAsset) {
    return (
      <LoadingOverlay loading={loading}>
        <Typography variant="h6" align="center">
          {error || 'Asset not found'}
        </Typography>
      </LoadingOverlay>
    );
  }

  const mapAsset = {
    id: currentAsset.id,
    name: currentAsset.name,
    latitude: currentAsset.latitude,
    longitude: currentAsset.longitude,
    riskLevel: getRiskLevel(currentAsset.riskScore),
    riskScore: currentAsset.riskScore,
    description: currentAsset.description,
  };

  return (
    <LoadingOverlay loading={loading}>
      <Box>
        <Typography variant="h4" gutterBottom>
          Asset Details: {currentAsset.name}
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Type</Typography>
                  <Typography variant="body1" gutterBottom>
                    {currentAsset.type}
                  </Typography>

                  <Typography variant="subtitle2">Country</Typography>
                  <Typography variant="body1" gutterBottom>
                    {currentAsset.country}
                  </Typography>

                  <Typography variant="subtitle2">Criticality Score</Typography>
                  <Typography variant="body1" gutterBottom>
                    {currentAsset.criticality_score}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Description</Typography>
                  <Typography variant="body1" gutterBottom>
                    {currentAsset.description}
                  </Typography>

                  <Typography variant="subtitle2">Vulnerability Score</Typography>
                  <Typography variant="body1" gutterBottom>
                    {currentAsset.vulnerability_score}
                  </Typography>

                  <Typography variant="subtitle2">Overall Risk Level</Typography>
                  <Box sx={{ mt: 0.5 }}>
                    <RiskLevelBadge
                      level={getRiskLevel(currentAsset.riskScore)}
                      score={currentAsset.riskScore}
                      showScore
                    />
                  </Box>
                </Grid>
              </Grid>
            </Paper>

            <Paper sx={{ mt: 3, height: '400px', overflow: 'hidden' }}>
              <MapComponent
                assets={[mapAsset]}
                height="100%"
                initialCenter={[currentAsset.latitude, currentAsset.longitude]}
                initialZoom={13}
                autoBounds={false}
              />
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Barriers
              </Typography>
              <DataTable
                columns={barrierColumns}
                data={barriers}
                searchEnabled={false}
                refreshEnabled={false}
                onRowClick={handleReportIssue}
              />
            </Paper>

            <Paper sx={{ mt: 3, p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Risk Matrix
              </Typography>
              <DataTable
                columns={riskMatrixColumns}
                data={riskMatrix}
                searchEnabled={false}
                refreshEnabled={false}
              />
            </Paper>
          </Grid>
        </Grid>

        {/* Barrier Issue Dialog */}
        <ConfirmationDialog
          open={!!barrierIssue}
          title="Report Barrier Issue"
          message={
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Barrier: {barrierIssue?.barrier?.name}
              </Typography>
              <TextField
                autoFocus
                margin="dense"
                label="Description"
                fullWidth
                multiline
                rows={4}
                value={barrierIssue?.description || ''}
                onChange={(e) =>
                  setBarrierIssue((prev) =>
                    prev ? { ...prev, description: e.target.value } : null
                  )
                }
              />
              <TextField
                select
                margin="dense"
                label="Impact Rating"
                fullWidth
                value={barrierIssue?.impactRating || ''}
                onChange={(e) =>
                  setBarrierIssue((prev) =>
                    prev ? { ...prev, impactRating: e.target.value } : null
                  )
                }
              >
                {impactRatings.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            </Box>
          }
          confirmLabel="Submit"
          type="warning"
          onConfirm={handleSubmitIssue}
          onCancel={() => setBarrierIssue(null)}
        />
      </Box>
    </LoadingOverlay>
  );
};

export default AssetDetails;

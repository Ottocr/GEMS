import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Paper,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useAppDispatch, useAppSelector } from '../../store';
import {
  fetchCountries,
  fetchCountryData,
} from '../../store/slices/riskManagementSlice';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import DataTable from '../../components/common/DataTable';
import RiskLevelBadge, { getRiskLevel } from '../../components/common/RiskLevelBadge';
import { TableColumn } from '../../types';

const assetColumns: TableColumn[] = [
  { id: 'name', label: 'Asset Name', minWidth: 170 },
  { id: 'type', label: 'Type', minWidth: 130 },
  {
    id: 'criticality_score',
    label: 'Criticality',
    minWidth: 100,
    align: 'right',
    format: (value: number) => value.toFixed(1),
  },
  {
    id: 'vulnerability_score',
    label: 'Vulnerability',
    minWidth: 100,
    align: 'right',
    format: (value: number) => value.toFixed(1),
  },
  {
    id: 'riskScore',
    label: 'Risk Level',
    minWidth: 120,
    align: 'right',
    format: (value: number) => (
      <RiskLevelBadge 
        level={getRiskLevel(value)} 
        score={value}
        showScore
      />
    ),
  },
  {
    id: 'actions',
    label: '',
    minWidth: 50,
    align: 'right',
    format: (_, row: any) => (
      <Tooltip title="Go to asset page">
        <IconButton
          size="small"
          color="primary"
          onClick={(e) => {
            e.stopPropagation();
            window.location.href = `/assets/${row.id}`;
          }}
        >
          <ArrowForwardIcon />
        </IconButton>
      </Tooltip>
    ),
  },
];

const RiskManagement: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [expandedCountry, setExpandedCountry] = React.useState<string | false>(false);
  const {
    countries,
    countryAssets,
    loading,
    error,
  } = useAppSelector(state => state.riskManagement);

  useEffect(() => {
    dispatch(fetchCountries());
  }, [dispatch]);

  useEffect(() => {
    if (expandedCountry) {
      const country = countries.find(c => c.id.toString() === expandedCountry);
      if (country) {
        dispatch(fetchCountryData(country.id));
      }
    }
  }, [dispatch, expandedCountry, countries]);

  const handleCountryClick = (countryCode: string) => {
    navigate(`/risk-management?country=${countryCode}`);
  };

  const handleAssetClick = (assetId: number) => {
    navigate(`/assets/${assetId}`);
  };

  const handleAccordionChange = (countryId: string) => (
    _event: React.SyntheticEvent,
    isExpanded: boolean
  ) => {
    setExpandedCountry(isExpanded ? countryId : false);
  };

  return (
    <LoadingOverlay loading={loading}>
      <Box>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          Risk Management
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mt: 3 }}>
          {countries.map((country) => (
            <Accordion
              key={country.id}
              expanded={expandedCountry === country.id.toString()}
              onChange={handleAccordionChange(country.id.toString())}
              sx={{ mb: 1 }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{ 
                  '&:hover': { 
                    bgcolor: 'action.hover',
                  }
                }}
              >
                <Grid container alignItems="center" spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="h6">
                        {country.name}
                      </Typography>
                      <Tooltip title={`Go to ${country.name} page`}>
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCountryClick(country.code);
                          }}
                          sx={{ ml: 1 }}
                        >
                          <ArrowForwardIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box display="flex" gap={1} alignItems="center">
                      <Typography variant="body2" color="text.secondary">
                        Risk Score:
                      </Typography>
                      <RiskLevelBadge 
                        level={getRiskLevel(country.avg_bta_score || 5)} 
                        score={country.avg_bta_score || 5}
                        showScore
                      />
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box display="flex" gap={1}>
                      {country.bta_scores?.map((score: any) => (
                        <Chip
                          key={score.risk_group}
                          label={`${score.risk_group}: ${score.bta_score.toFixed(1)}`}
                          size="small"
                          color={getRiskLevel(score.bta_score) === 'HIGH' ? 'error' : 'default'}
                        />
                      ))}
                    </Box>
                  </Grid>
                </Grid>
              </AccordionSummary>
              <AccordionDetails>
                <Paper elevation={0} sx={{ bgcolor: 'background.default' }}>
                  <Typography variant="h6" gutterBottom>
                    Country Assets
                  </Typography>
                  <DataTable
                    columns={assetColumns}
                    data={countryAssets}
                    onRowClick={(row) => handleAssetClick(row.id)}
                    searchEnabled
                  />
                </Paper>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      </Box>
    </LoadingOverlay>
  );
};

export default RiskManagement;

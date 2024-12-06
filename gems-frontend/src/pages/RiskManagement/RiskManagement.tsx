import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Box, 
  Grid, 
  Typography, 
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Alert,
} from '@mui/material';
import { useAppDispatch, useAppSelector } from '../../store';
import {
  fetchCountries,
  fetchCountryData,
  setSelectedCountry,
} from '../../store/slices/riskManagementSlice';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import MapComponent from '../../components/common/MapComponent';
import DataTable from '../../components/common/DataTable';
import RiskLevelBadge, { getRiskLevel } from '../../components/common/RiskLevelBadge';
import { TableColumn } from '../../types';
import axios from 'axios';

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
];

const btaColumns: TableColumn[] = [
  { id: 'riskType', label: 'Risk Type', minWidth: 170 },
  {
    id: 'score',
    label: 'BTA Score',
    minWidth: 100,
    align: 'right',
    format: (value: number) => value.toFixed(1),
  },
  {
    id: 'lastUpdated',
    label: 'Last Updated',
    minWidth: 130,
    align: 'right',
    format: (value: string) => new Date(value).toLocaleDateString(),
  },
];

const RiskManagement: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [searchParams] = useSearchParams();
  const [countryGeoJson, setCountryGeoJson] = React.useState<any>(null);
  const {
    countries,
    selectedCountry,
    countryAssets,
    baselineThreats,
    loading,
    error,
  } = useAppSelector(state => state.riskManagement);

  useEffect(() => {
    dispatch(fetchCountries());
    fetchCountryGeoJson();
  }, [dispatch]);

  const fetchCountryGeoJson = async () => {
    try {
      const response = await axios.get('/api/countries/operated/geojson/');
      if (response.data.success && response.data.geojson) {
        setCountryGeoJson(response.data.geojson);
      }
    } catch (err) {
      console.error('Failed to fetch country GeoJSON:', err);
    }
  };

  useEffect(() => {
    const countryCode = searchParams.get('country');
    if (countryCode && countries.length > 0) {
      const country = countries.find(c => c.code === countryCode);
      if (country) {
        dispatch(setSelectedCountry(country));
      }
    }
  }, [searchParams, countries, dispatch]);

  useEffect(() => {
    if (selectedCountry) {
      dispatch(fetchCountryData(selectedCountry.id));
    }
  }, [dispatch, selectedCountry]);

  const handleCountryChange = (event: any) => {
    const country = countries.find(c => c.id === event.target.value);
    dispatch(setSelectedCountry(country || null));
  };

  const handleAssetClick = (assetId: number) => {
    navigate(`/assets/${assetId}`);
  };

  const handleCountryClick = (countryCode: string) => {
    const country = countries.find(c => c.code === countryCode);
    if (country) {
      dispatch(setSelectedCountry(country));
    }
  };

  const mapAssets = countryAssets.map(asset => ({
    id: asset.id,
    name: asset.name,
    latitude: asset.latitude,
    longitude: asset.longitude,
    riskLevel: getRiskLevel(asset.riskScore),
    riskScore: asset.riskScore,
    description: `${asset.type} - Risk Score: ${asset.riskScore.toFixed(1)}`,
  }));

  // Get map center coordinates from selected country or assets
  const getMapCenter = (): [number, number] | undefined => {
    if (selectedCountry?.latitude && selectedCountry?.longitude) {
      return [selectedCountry.latitude, selectedCountry.longitude];
    }
    if (countryAssets.length > 0) {
      const avgLat = countryAssets.reduce((sum, asset) => sum + asset.latitude, 0) / countryAssets.length;
      const avgLng = countryAssets.reduce((sum, asset) => sum + asset.longitude, 0) / countryAssets.length;
      return [avgLat, avgLng];
    }
    return undefined;
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

        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel>Select Country</InputLabel>
          <Select
            value={selectedCountry?.id || ''}
            label="Select Country"
            onChange={handleCountryChange}
          >
            {countries.map((country) => (
              <MenuItem key={country.id} value={country.id}>
                {country.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {selectedCountry && (
          <>
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <MapComponent
                  assets={mapAssets}
                  countries={countryGeoJson}
                  selectedCountry={selectedCountry.code}
                  height="500px"
                  onAssetClick={handleAssetClick}
                  onCountryClick={handleCountryClick}
                  initialCenter={getMapCenter()}
                  initialZoom={5}
                />
              </Grid>

              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Baseline Threat Assessment
                  </Typography>
                  <DataTable
                    columns={btaColumns}
                    data={baselineThreats}
                    searchEnabled={false}
                    refreshEnabled={false}
                  />
                </Paper>
              </Grid>
            </Grid>

            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Country Assets
              </Typography>
              <DataTable
                columns={assetColumns}
                data={countryAssets}
                onRowClick={(row) => handleAssetClick(row.id)}
              />
            </Box>
          </>
        )}
      </Box>
    </LoadingOverlay>
  );
};

export default RiskManagement;

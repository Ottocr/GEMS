import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Grid, 
  Typography, 
  IconButton,
  useTheme,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Business as BusinessIcon,
  Public as PublicIcon,
  Warning as WarningIcon,
  MoreVert as MoreVertIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAppDispatch, useAppSelector } from '../../store';
import { fetchDashboardData } from '../../store/slices/dashboardSlice';
import MapComponent from '../../components/common/MapComponent';
import StatsCard from '../../components/common/StatsCard';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import { getRiskLevel } from '../../components/common/RiskLevelBadge';
import { GeoJSONFeature, GeoJSONFeatureCollection, Country } from '../../types';
import axios from 'axios';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const theme = useTheme();
  const [countryGeoJson, setCountryGeoJson] = React.useState<GeoJSONFeatureCollection | undefined>(undefined);
  const [geoJsonError, setGeoJsonError] = React.useState<string | undefined>(undefined);
  const { 
    totalCountries, 
    totalAssets, 
    globalRiskScore, 
    assets,
    countries,
    loading, 
    error 
  } = useAppSelector(state => state.dashboard);

  useEffect(() => {
    const loadData = async () => {
      await dispatch(fetchDashboardData());
    };
    loadData();
  }, [dispatch]);

  // Fetch GeoJSON when countries data is available
  useEffect(() => {
    if (countries?.length > 0) {
      console.log('Countries data available:', countries);
      fetchCountryGeoJson();
    }
  }, [countries]);

  const fetchCountryGeoJson = async () => {
    try {
      setGeoJsonError(undefined);
      console.log('Fetching operated countries GeoJSON...');
      
      // Fetch GeoJSON for all operated countries
      const response = await axios.get('/api/countries/operated/geojson/');
      console.log('GeoJSON response:', response.data);

      if (response.data.success && response.data.geojson) {
        // Add country data from our state to the GeoJSON properties
        const geoJson = response.data.geojson;
        console.log('Raw GeoJSON:', geoJson);

        const countryMap = new Map(
          countries.map(country => [country.id, country])
        );

        geoJson.features = geoJson.features.map((feature: GeoJSONFeature) => {
          const countryId = feature.properties?.id;
          if (typeof countryId === 'number') {
            const country = countryMap.get(countryId);
            if (country) {
              console.log('Enhancing feature for country:', country.name);
              feature.properties = {
                ...feature.properties,
                code: country.code,
                name: country.name,
                avg_bta_score: country.avg_bta_score || 5,
                bta_scores: country.bta_scores || []
              };
            }
          }
          return feature;
        });

        console.log('Enhanced GeoJSON:', geoJson);
        setCountryGeoJson(geoJson);
      } else {
        console.error('Invalid GeoJSON response:', response.data);
        setGeoJsonError('No valid GeoJSON data available for operated countries');
      }
    } catch (err) {
      console.error('Failed to fetch country GeoJSON:', err);
      setGeoJsonError('Failed to load country data for the map');
    }
  };

  const handleAssetClick = (assetId: number) => {
    navigate(`/assets/${assetId}`);
  };

  const handleCountryClick = (countryCode: string) => {
    navigate(`/risk-management?country=${countryCode}`);
  };

  const handleRefresh = () => {
    dispatch(fetchDashboardData());
    fetchCountryGeoJson();
  };

  const mapAssets = assets.map(asset => ({
    id: asset.id,
    name: asset.name,
    latitude: asset.latitude,
    longitude: asset.longitude,
    riskLevel: getRiskLevel(asset.riskScore),
    riskScore: asset.riskScore,
    description: `${asset.type} - ${asset.country}`,
  }));

  const highRiskAssets = assets.filter(a => 
    getRiskLevel(a.riskScore) === 'HIGH' || getRiskLevel(a.riskScore) === 'CRITICAL'
  );

  // Calculate map center based on assets
  const getMapCenter = (): [number, number] | undefined => {
    if (assets.length > 0) {
      const avgLat = assets.reduce((sum, asset) => sum + asset.latitude, 0) / assets.length;
      const avgLng = assets.reduce((sum, asset) => sum + asset.longitude, 0) / assets.length;
      return [avgLat, avgLng];
    }
    return undefined;
  };

  return (
    <LoadingOverlay loading={loading}>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography 
              variant="h4" 
              color="text.primary" 
              sx={{ 
                fontWeight: 600,
                mb: 1,
              }}
            >
              Global Risk Overview
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Real-time monitoring of global security risks and assets
            </Typography>
          </Box>
          <Box>
            <Tooltip title="Refresh data">
              <IconButton onClick={handleRefresh} color="primary">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="More options">
              <IconButton color="primary">
                <MoreVertIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={1}>
          <Grid item xs={12}>
            <Grid container spacing={1}>
              <Grid item xs={12} sm={6} md={3}>
                <StatsCard
                  title="Total Countries"
                  value={totalCountries}
                  icon={<PublicIcon />}
                  color={theme.palette.primary.main}
                  delay={0.1}
                  subtitle="Countries with active operations"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <StatsCard
                  title="Total Assets"
                  value={totalAssets}
                  icon={<BusinessIcon />}
                  color={theme.palette.info.main}
                  delay={0.2}
                  subtitle="Monitored facilities and infrastructure"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <StatsCard
                  title="Global Risk Score"
                  value={globalRiskScore.toFixed(1)}
                  icon={<SecurityIcon />}
                  color={theme.palette.warning.main}
                  trend={{
                    value: 12,
                    isPositive: false,
                    label: 'vs previous quarter',
                  }}
                  delay={0.3}
                  subtitle="Aggregate risk assessment"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <StatsCard
                  title="High Risk Assets"
                  value={highRiskAssets.length}
                  icon={<WarningIcon />}
                  color={theme.palette.error.main}
                  trend={{
                    value: 5,
                    isPositive: false,
                    label: 'new since last month',
                  }}
                  delay={0.4}
                  subtitle="Assets requiring immediate attention"
                  onClick={() => navigate('/risk-management?filter=high-risk')}
                />
              </Grid>
            </Grid>
          </Grid>

          <Grid item xs={12}>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <MapComponent
                assets={mapAssets}
                countries={countryGeoJson}
                height="600px"
                onAssetClick={handleAssetClick}
                onCountryClick={handleCountryClick}
                initialCenter={getMapCenter()}
                initialZoom={2}
                autoBounds={false}
              />
            </motion.div>
          </Grid>
        </Grid>
      </motion.div>
    </LoadingOverlay>
  );
};

export default Dashboard;

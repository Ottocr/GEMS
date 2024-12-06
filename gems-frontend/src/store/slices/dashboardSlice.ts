import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import { DashboardState, DashboardResponse, Asset, Country } from '../../types';

const initialState: DashboardState = {
  totalCountries: 0,
  totalAssets: 0,
  globalRiskScore: 0,
  assets: [],
  countries: [],
  loading: false,
  error: null,
};

export const fetchDashboardData = createAsyncThunk(
  'dashboard/fetchData',
  async () => {
    // Get dashboard overview
    const response = await axios.get<DashboardResponse>('/api/dashboard/data/');
    
    // Transform assets data to match our frontend structure
    const transformedAssets: Asset[] = response.data.assets.map((asset: any) => ({
      id: asset.id,
      name: asset.name,
      description: '',
      latitude: asset.latitude,
      longitude: asset.longitude,
      asset_type: asset.asset_type,
      type: asset.asset_type,
      country: asset.country.name,
      criticality_score: asset.criticality_score,
      vulnerability_score: asset.vulnerability_score,
      riskScore: calculateAssetRiskScore({
        criticality_score: asset.criticality_score,
        vulnerability_score: asset.vulnerability_score,
        country: asset.country,
      }),
    }));

    // Transform countries data
    const transformedCountries: Country[] = response.data.countries.map((country: any) => ({
      id: country.id,
      name: country.name,
      code: country.code,
      latitude: country.latitude,
      longitude: country.longitude,
      avg_bta_score: country.avg_bta_score,
      bta_scores: country.bta_scores,
    }));

    return {
      totalCountries: response.data.total_countries,
      totalAssets: transformedAssets.length,
      globalRiskScore: response.data.avg_global_risk_score,
      assets: transformedAssets,
      countries: transformedCountries,
    };
  }
);

// Helper function to calculate asset risk score
const calculateAssetRiskScore = (asset: any): number => {
  // If the asset has country BTA scores, use the average
  if (asset.country?.bta_scores?.length > 0) {
    const btaSum = asset.country.bta_scores.reduce(
      (sum: number, bta: any) => sum + bta.bta_score,
      0
    );
    return btaSum / asset.country.bta_scores.length;
  }

  // Otherwise, calculate based on criticality and vulnerability
  const baseScore = (asset.criticality_score + asset.vulnerability_score) / 2;
  return Math.min(Math.max(baseScore, 1), 10); // Ensure score is between 1 and 10
};

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    clearDashboardData: (state) => {
      state.assets = [];
      state.countries = [];
      state.totalCountries = 0;
      state.totalAssets = 0;
      state.globalRiskScore = 0;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        state.loading = false;
        state.totalCountries = action.payload.totalCountries;
        state.totalAssets = action.payload.totalAssets;
        state.globalRiskScore = action.payload.globalRiskScore;
        state.assets = action.payload.assets;
        state.countries = action.payload.countries;
      })
      .addCase(fetchDashboardData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch dashboard data';
        console.error('Dashboard data fetch error:', action.error);
      });
  },
});

export const { clearDashboardData } = dashboardSlice.actions;
export default dashboardSlice.reducer;

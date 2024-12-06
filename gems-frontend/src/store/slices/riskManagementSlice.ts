import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import { RiskManagementState, Asset, SecurityManagerResponse, RiskType } from '../../types';

const initialState: RiskManagementState = {
  countries: [],
  selectedCountry: null,
  countryAssets: [],
  baselineThreats: [],
  loading: false,
  error: null,
};

export const fetchCountries = createAsyncThunk(
  'riskManagement/fetchCountries',
  async () => {
    const response = await axios.get<SecurityManagerResponse>('/api/security-manager/data/');
    return response.data.countries.map((country) => ({
      id: country.id,
      name: country.name,
      code: country.code,
      latitude: country.geo_data?.coordinates?.[1] || 0,
      longitude: country.geo_data?.coordinates?.[0] || 0,
    }));
  }
);

export const fetchCountryData = createAsyncThunk(
  'riskManagement/fetchCountryData',
  async (countryId: number) => {
    // Get country's data including assets and BTA
    const response = await axios.get<SecurityManagerResponse>('/api/security-manager/data/', {
      params: { country_id: countryId }
    });

    // Transform assets data
    const assets: Asset[] = (response.data.assets || []).map((asset: any) => ({
      id: asset.id,
      name: asset.name,
      description: '',
      latitude: asset.latitude,
      longitude: asset.longitude,
      asset_type: asset.asset_type,
      type: asset.asset_type,
      country: response.data.selected_country?.name || '',
      criticality_score: asset.criticality_score,
      vulnerability_score: asset.vulnerability_score,
      riskScore: calculateAssetRiskScore(asset),
    }));

    // Get risk types mapping
    const riskTypesMap = new Map<number, RiskType>();
    response.data.risk_types.forEach((rt: RiskType) => {
      riskTypesMap.set(rt.id, rt);
    });

    // Transform BTA data
    const baselineThreats = (response.data.bta_list || []).map((bta: any) => ({
      id: bta.risk_type_id,
      riskType: riskTypesMap.get(bta.risk_type_id)?.name || 'Unknown',
      riskTypeId: bta.risk_type_id,
      score: bta.baseline_score,
      lastUpdated: bta.date_assessed || new Date().toISOString().split('T')[0],
      impact_on_assets: bta.impact_on_assets,
      notes: bta.notes,
    }));

    return {
      assets,
      baselineThreats,
    };
  }
);

// Helper function to calculate asset risk score
const calculateAssetRiskScore = (asset: any): number => {
  const baseScore = (asset.criticality_score + asset.vulnerability_score) / 2;
  return Math.min(Math.max(baseScore, 1), 10);
};

const riskManagementSlice = createSlice({
  name: 'riskManagement',
  initialState,
  reducers: {
    setSelectedCountry: (state, action) => {
      state.selectedCountry = action.payload;
      if (!action.payload) {
        state.countryAssets = [];
        state.baselineThreats = [];
      }
    },
    clearCountryData: (state) => {
      state.countryAssets = [];
      state.baselineThreats = [];
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Countries
      .addCase(fetchCountries.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCountries.fulfilled, (state, action) => {
        state.loading = false;
        state.countries = action.payload;
      })
      .addCase(fetchCountries.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch countries';
        console.error('Countries fetch error:', action.error);
      })
      // Fetch Country Data
      .addCase(fetchCountryData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCountryData.fulfilled, (state, action) => {
        state.loading = false;
        state.countryAssets = action.payload.assets;
        state.baselineThreats = action.payload.baselineThreats;
      })
      .addCase(fetchCountryData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch country data';
        console.error('Country data fetch error:', action.error);
      });
  },
});

export const { setSelectedCountry, clearCountryData } = riskManagementSlice.actions;
export default riskManagementSlice.reducer;

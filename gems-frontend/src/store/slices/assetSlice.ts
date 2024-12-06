import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import { 
  AssetState, 
  Asset, 
  Barrier, 
  RiskMatrix, 
  AssetResponse 
} from '../../types';

interface AssetDetailsResponse {
  asset: AssetResponse;
  barriers: Barrier[];
  risk_matrices: RiskMatrix[];
}

interface BarrierIssueRequest {
  assetId: number;
  barrierId: number;
  description: string;
  impactRating: 'NO_IMPACT' | 'MINIMAL' | 'SUBSTANTIAL' | 'MAJOR' | 'COMPROMISED';
}

interface VulnerabilityAnswerRequest {
  assetId: number;
  questionId: number;
  answer: string;
}

const initialState: AssetState = {
  currentAsset: null,
  assets: [],
  barriers: [],
  riskMatrix: [],
  vulnerabilityQuestions: [],
  vulnerabilityAnswers: [],
  loading: false,
  error: null,
};

export const fetchAssets = createAsyncThunk(
  'asset/fetchAssets',
  async () => {
    const response = await axios.get<{ assets: AssetResponse[] }>('/api/assets/');
    return response.data.assets.map(asset => ({
      ...asset,
      type: asset.asset_type,
      riskScore: calculateAssetRiskScore(asset),
    }));
  }
);

export const fetchAssetDetails = createAsyncThunk(
  'asset/fetchDetails',
  async (assetId: number) => {
    const response = await axios.get<AssetDetailsResponse>(`/api/assets/${assetId}/`);
    
    const asset: Asset = {
      ...response.data.asset,
      type: response.data.asset.asset_type,
      riskScore: calculateAssetRiskScore(response.data.asset),
    };

    return {
      asset,
      barriers: response.data.barriers,
      riskMatrix: response.data.risk_matrices,
    };
  }
);

export const reportBarrierIssue = createAsyncThunk(
  'asset/reportBarrierIssue',
  async (data: BarrierIssueRequest) => {
    const response = await axios.post('/api/barriers/report-issue/', {
      asset_id: data.assetId,
      barrier_id: data.barrierId,
      description: data.description,
      impact_rating: data.impactRating,
    });
    return response.data;
  }
);

export const updateVulnerabilityAnswer = createAsyncThunk(
  'asset/updateVulnerabilityAnswer',
  async (data: VulnerabilityAnswerRequest) => {
    const response = await axios.post(`/api/assets/${data.assetId}/update-vulnerability/`, {
      question_id: data.questionId,
      selected_choice: data.answer,
    });
    return response.data;
  }
);

// Helper function to calculate asset risk score
const calculateAssetRiskScore = (asset: AssetResponse): number => {
  const baseScore = (asset.criticality_score + asset.vulnerability_score) / 2;
  return Math.min(Math.max(baseScore, 1), 10);
};

const assetSlice = createSlice({
  name: 'asset',
  initialState,
  reducers: {
    clearAssetData: (state) => {
      state.currentAsset = null;
      state.assets = [];
      state.barriers = [];
      state.riskMatrix = [];
      state.vulnerabilityQuestions = [];
      state.vulnerabilityAnswers = [];
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Assets List
      .addCase(fetchAssets.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAssets.fulfilled, (state, action) => {
        state.loading = false;
        state.assets = action.payload;
      })
      .addCase(fetchAssets.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch assets';
      })
      // Fetch Asset Details
      .addCase(fetchAssetDetails.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAssetDetails.fulfilled, (state, action) => {
        state.loading = false;
        state.currentAsset = action.payload.asset;
        state.barriers = action.payload.barriers;
        state.riskMatrix = action.payload.riskMatrix;
      })
      .addCase(fetchAssetDetails.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch asset details';
      })
      // Report Barrier Issue
      .addCase(reportBarrierIssue.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(reportBarrierIssue.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(reportBarrierIssue.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to report barrier issue';
      })
      // Update Vulnerability Answer
      .addCase(updateVulnerabilityAnswer.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateVulnerabilityAnswer.fulfilled, (state, action) => {
        state.loading = false;
        const updatedAnswer = action.payload;
        const index = state.vulnerabilityAnswers.findIndex(
          (answer) => answer.question_id === updatedAnswer.question_id
        );
        if (index !== -1) {
          state.vulnerabilityAnswers[index] = updatedAnswer;
        } else {
          state.vulnerabilityAnswers.push(updatedAnswer);
        }
      })
      .addCase(updateVulnerabilityAnswer.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to update vulnerability answer';
      });
  },
});

export const { clearAssetData } = assetSlice.actions;
export default assetSlice.reducer;

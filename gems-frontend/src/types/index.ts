export interface Country {
    id: number;
    name: string;
    code: string;
    latitude: number;
    longitude: number;
    avg_bta_score?: number;
    bta_scores?: Array<{
        risk_group: string;
        bta_score: number;
    }>;
    geo_data?: any;
    company_operated?: boolean;
}

export interface Asset {
    id: number;
    name: string;
    description: string;
    latitude: number;
    longitude: number;
    asset_type: string;
    type: string;  // Alias for asset_type for convenience
    country: string;
    criticality_score: number;
    vulnerability_score: number;
    riskScore: number;  // Calculated risk score
}

export interface RiskType {
    id: number;
    name: string;
    description: string;
}

export interface BaselineThreatAssessment {
    id: number;
    riskType: string;
    riskTypeId: number;
    score: number;
    lastUpdated: string;
    impact_on_assets?: boolean;
    notes?: string;
}

export interface RiskMatrix {
    risk_type: string;
    score: number;
    level: RiskLevel;
}

export interface Barrier {
    id: number;
    name: string;
    category: string;
    description: string;
    effectiveness_scores: {
        [key: string]: {
            risk_type: string;
            preventive: number;
            detection: number;
            response: number;
            reliability: number;
            coverage: number;
            overall: number;
        };
    };
}

export interface TableColumn<T = any> {
    id: string;
    label: string;
    minWidth?: number;
    align?: 'right' | 'left' | 'center';
    format?: (value: any, row?: T) => React.ReactNode;
}

export interface MapAsset {
    id: number;
    name: string;
    latitude: number;
    longitude: number;
    riskLevel: RiskLevel;
    riskScore?: number;
    description?: string;
}

// GeoJSON Types
export interface GeoJSONFeature {
    type: 'Feature';
    geometry: {
        type: string;
        coordinates: number[][][] | number[][][][] | number[][][][][];
    };
    properties: {
        id?: number;
        name: string;
        code: string;
        avg_bta_score?: number;
        bta_scores?: Array<{
            risk_group: string;
            bta_score: number;
        }>;
    };
}

export interface GeoJSONFeatureCollection {
    type: 'FeatureCollection';
    features: GeoJSONFeature[];
}

export interface DashboardState {
    totalCountries: number;
    totalAssets: number;
    globalRiskScore: number;
    assets: Asset[];
    countries: Country[];
    loading: boolean;
    error: string | null;
}

export interface RiskManagementState {
    countries: Country[];
    selectedCountry: Country | null;
    countryAssets: Asset[];
    baselineThreats: BaselineThreatAssessment[];
    loading: boolean;
    error: string | null;
}

export interface AssetState {
    currentAsset: Asset | null;
    assets: Asset[];  // Added assets array
    barriers: Barrier[];
    riskMatrix: RiskMatrix[];
    vulnerabilityQuestions: any[];
    vulnerabilityAnswers: any[];
    loading: boolean;
    error: string | null;
}

// Common Types
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type ImpactRating = 'NO_IMPACT' | 'MINIMAL' | 'SUBSTANTIAL' | 'MAJOR' | 'COMPROMISED';

// API Response Types
export interface DashboardResponse {
    total_countries: number;
    avg_global_risk_score: number;
    recent_updates: any[];
    countries: Country[];
    assets: any[];
    risk_types: RiskType[];
}

export interface SecurityManagerResponse {
    countries: Country[];
    selected_country?: Country;
    assets?: Asset[];
    bta_list?: any[];
    risk_types: RiskType[];
    barriers: Barrier[];
    vulnerability_questions: any[];
    criticality_questions: any[];
    scenarios: any[];
    asset_types: any[];
}

export interface AssetResponse {
    id: number;
    name: string;
    description: string;
    latitude: number;
    longitude: number;
    asset_type: string;
    country: string;
    criticality_score: number;
    vulnerability_score: number;
}

export interface AssetDetailsResponse {
    asset: AssetResponse;
    barriers: Barrier[];
    risk_matrices: RiskMatrix[];
}

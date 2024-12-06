# GEMS Risk Calculation Methodology

## Overview
This document details the mathematical models and methodologies used in the Global Enterprise Monitoring System (GEMS) for calculating risk scores. The system uses a multi-layered approach that considers:
- Barrier effectiveness
- Scenario-based risk assessment
- Geographic threat baselines
- Asset vulnerability and criticality

## 1. Barrier Effectiveness Calculation

### 1.1 Individual Barrier Component Scoring
Each barrier's effectiveness is calculated using five weighted components:
```
Overall Effectiveness = (
    Preventive Capability × 0.30 +
    Detection Capability × 0.20 +
    Response Capability × 0.20 +
    Reliability × 0.15 +
    Coverage × 0.15
)
```

### 1.2 Performance Adjustment
The base effectiveness score is modified by a performance adjustment factor:
```
Final Effectiveness = Base Effectiveness × Performance Adjustment
```
Performance adjustment ranges from 0.1 to 1.0 based on operational status and reported issues.

### 1.3 Risk-Specific Effectiveness
For each risk type/subtype, the system uses the maximum effectiveness score among applicable measures:
```
Risk-Specific Effectiveness = max(
    Type-Level Effectiveness,
    Subtype-Level Effectiveness
) × Performance Adjustment
```

## 2. Risk Scenario Assessment

### 2.1 Base Risk Calculation
Base risk is calculated using the geometric mean of three factors:
```
Base Risk = (Likelihood × Impact × Vulnerability)^(1/3)
```
This provides a balanced consideration of all factors while preventing any single factor from dominating the calculation.

### 2.2 Barrier Impact Integration
Residual risk after barrier application is calculated as:
```
Residual Risk = Base Risk / (1 + Average Barrier Effectiveness)
```
Where Average Barrier Effectiveness is the mean of all applicable barrier effectiveness scores.

### 2.3 Weighted Scoring
Each component (likelihood, impact, vulnerability) uses weighted question scores:
```
Component Score = Σ(Answer Score × Question Weight) / Σ(Question Weights)
```

## 3. Geographic Risk Integration

### 3.1 Baseline Threat Assessment (BTA)
Each country-risk type combination has a baseline threat score (1-10) that serves as a regional risk indicator.

### 3.2 BTA Integration
Final risk scores combine scenario-based assessments with BTAs:
```
Final Risk Score = (Average Residual Risk + BTA Score) / 2
```
This ensures both local asset conditions and regional threats are considered.

## 4. Final Risk Matrix Calculation

### 4.1 Risk Level Determination
Final risk scores are mapped to risk levels:
- LOW: Score ≤ 3
- MEDIUM: 3 < Score ≤ 5
- HIGH: 5 < Score ≤ 8
- CRITICAL: Score > 8

### 4.2 Asset-Level Aggregation
Overall asset risk considers:
- Scenario-based residual risks
- Geographic baseline threats
- Asset criticality
- Asset vulnerability

### 4.3 Risk Type Aggregation
For each risk type:
```
Risk Type Score = average(
    Scenario Residual Risks,
    Applicable BTAs
)
```

## 5. Data Quality and Confidence

### 5.1 Minimum Data Requirements
- At least one scenario assessment per risk type
- Complete barrier effectiveness scores
- Valid BTA scores for company-operated countries

### 5.2 Update Triggers
Risk scores are recalculated when:
- New scenario assessments are added
- Barrier effectiveness changes
- BTAs are updated
- Asset details are modified
- Barrier issues are reported

## 6. Calculation Chain

1. Calculate barrier effectiveness scores
2. Assess scenarios and calculate base risks
3. Apply barrier effectiveness to get residual risks
4. Integrate BTAs for final risk scores
5. Determine risk levels
6. Generate risk matrices

## 7. Validation and Quality Control

### 7.1 Automated Validation
- Range checks on all input scores (1-10)
- Completeness verification for required data
- Consistency checks across related assessments

### 7.2 Calculation Verification
Regular automated tests verify:
- Barrier effectiveness calculations
- Risk scenario assessments
- BTA integration
- Final risk matrix generation

## 8. System Constraints

### 8.1 Score Ranges
- All input scores: 1-10
- Effectiveness components: 1-10
- Performance adjustment: 0.1-1.0
- Final risk scores: 1-10

### 8.2 Update Frequency
- BTAs: Minimum quarterly review
- Barrier effectiveness: Monthly or on incident
- Scenario assessments: Quarterly or on significant changes
- Risk matrices: Real-time on any component update

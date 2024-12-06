# GEMS Risk Assessment System: Technical Documentation

## Overview
This document details how the GEMS (Global Enterprise Management System) risk assessment system calculates and weighs different factors to produce final risk assessments. Understanding these weightings is crucial as they directly impact operational decisions, security investments, and personnel safety.

## 1. Geographic Risk Context (Baseline Threat Assessment)
### Purpose
- Establishes foundational risk level for a geographic area
- Provides context for all assets in that location

### Implementation
- Score Range: 1-10
- Direct input from security analysts
- Impacts final risk score with 50% weighting when combined with scenario-based assessments
```python
final_score = (avg_residual_risk + bta_score) / 2
```

## 2. Asset Characteristics

### 2.1 Asset Criticality
#### Purpose
- Measures importance of asset to operations
- Amplifies risk scores based on asset's operational value

#### Implementation
- Score Range: 1-10 per question
- Multiple-choice questions with pre-defined scores
- Final criticality score = average of all question scores
- Directly impacts final risk calculation with 33% weighting
```python
final_risk = (risk_score + criticality_score + vulnerability_score) / 3
```

### 2.2 Asset Vulnerability
#### Purpose
- Assesses asset's inherent vulnerabilities to specific risk types
- Identifies weak points requiring additional protection

#### Implementation
- Score Range: 1-10 per question
- Risk type-specific questions
- Final vulnerability score = average of all question scores
- Impacts final risk calculation with 33% weighting

## 3. Scenario-Based Risk Assessment

### 3.1 Components
Each scenario assessment combines:
1. Likelihood Assessment
2. Impact Assessment
3. Vulnerability Assessment

### 3.2 Calculation
```python
base_risk = (likelihood_score * impact_score * vulnerability_score) ** (1/3)
```
- Equal weighting (geometric mean) ensures balance
- Each component equally crucial
- Range: 1-10 for final score

## 4. Barrier System

### 4.1 Barrier Effectiveness Scoring
#### Components and Weights
1. Preventive Capability: 30%
   - Highest weight due to importance of prevention
2. Detection Capability: 20%
   - Critical for early warning
3. Response Capability: 20%
   - Measures mitigation effectiveness
4. Reliability: 15%
   - System consistency
5. Coverage: 15%
   - Scope of protection

#### Calculation
```python
effectiveness = (
    preventive * 0.30 +
    detection * 0.20 +
    response * 0.20 +
    reliability * 0.15 +
    coverage * 0.15
)
```

### 4.2 Barrier Issue Impact
#### Performance Adjustments
- No Impact: 1.0x (no change)
- Minimal Impact: 0.95x (5% reduction)
- Substantial Impact: 0.8x (20% reduction)
- Major Impact: 0.6x (40% reduction)
- Compromised: 0.2x (80% reduction)

#### Application
```python
residual_risk = base_risk / (1 + barrier_effectiveness)
```
- Higher barrier effectiveness = lower residual risk
- Issues reduce effectiveness, increasing risk

## 5. Asset Links and Risk Propagation

### 5.1 Shared Risk Calculation
- Own Assessment: 70% weight
- Linked Asset Impact: 30% weight
```python
shared_risk = (own_assessment * 0.7) + (linked_assessment * 0.3)
```

### 5.2 Barrier Sharing
- Affects all linked assets
- Same weighting as risk sharing (70/30)
- Propagates barrier issues across linked assets

## 6. Final Risk Matrix Generation

### 6.1 Process Flow
1. Calculate scenario-based risks
2. Apply barrier effectiveness
3. Consider BTA score
4. Factor in asset characteristics
5. Apply any barrier issues
6. Process asset links

### 6.2 Final Score Calculation
```python
# Step 1: Scenario + BTA
initial_score = (scenario_risk + bta_score) / 2

# Step 2: Asset Characteristics
final_score = (initial_score + criticality + vulnerability) / 3
```

### 6.3 Risk Level Assignment
- LOW: ≤3
- MEDIUM: ≤5
- HIGH: ≤8
- CRITICAL: >8

## 7. Real-World Impact Considerations

### 7.1 Operational Decisions
- Risk levels guide operational protocols
- HIGH/CRITICAL risks require immediate attention
- Affects business continuity planning

### 7.2 Investment Prioritization
- Barrier effectiveness scores guide security investments
- Low scores indicate improvement needs
- Links between assets help optimize resource allocation

### 7.3 Personnel Safety
- Risk levels determine access protocols
- Affects training requirements
- Guides emergency response planning

## 8. System Maintenance

### 8.1 Regular Reviews
- BTAs: Quarterly review recommended
- Asset Characteristics: Annual review
- Barrier Assessments: Semi-annual review
- Scenario Assessments: Annual or post-incident

### 8.2 Dynamic Updates
- Barrier issues trigger immediate recalculation
- Asset link changes propagate automatically
- Risk scores update in real-time

## 9. Practical Examples

### 9.1 Example: Vehicle-borne IED (VBIED) Risk Assessment

#### Initial Context
- Location: High-risk country
- BTA Score: 8 (High terrorist threat)
- Asset: Main office building
- Criticality Score: 9 (Critical operations center)
- Vulnerability Score: 6 (Some vulnerabilities present)

#### Scenario Assessment
1. Likelihood Questions:
   - Recent incidents in area (Score: 7)
   - Local threat intelligence (Score: 8)
   - Historical patterns (Score: 6)
   * Likelihood Score: 7.0

2. Impact Questions:
   - Estimated casualties (Score: 9)
   - Building damage (Score: 8)
   - Business disruption (Score: 7)
   * Impact Score: 8.0

3. Vulnerability Questions:
   - Distance from road (Score: 7)
   - Access control points (Score: 5)
   - Standoff distance (Score: 6)
   * Vulnerability Score: 6.0

Base Risk Calculation:
```python
base_risk = (7.0 * 8.0 * 6.0) ** (1/3) = 7.0
```

#### Barrier Assessment
1. Vehicle Barriers:
   - Preventive Capability: 8
   - Detection Capability: 7
   - Response Capability: 6
   - Reliability: 8
   - Coverage: 7
   * Effectiveness: (8*0.3 + 7*0.2 + 6*0.2 + 8*0.15 + 7*0.15) = 7.25

2. Security Checkpoints:
   - Preventive Capability: 7
   - Detection Capability: 8
   - Response Capability: 7
   - Reliability: 7
   - Coverage: 6
   * Effectiveness: (7*0.3 + 8*0.2 + 7*0.2 + 7*0.15 + 6*0.15) = 7.05

Combined Barrier Effectiveness: 7.15

#### Impact of Barrier Issue
Scenario: Vehicle barrier partially damaged
- Impact Rating: SUBSTANTIAL (0.8x multiplier)
- Adjusted Barrier Effectiveness: 7.15 * 0.8 = 5.72

#### Risk Calculation With Barriers
```python
residual_risk = 7.0 / (1 + 5.72/10) = 4.46
```

#### Final Risk Score
```python
# Combine with BTA
initial_score = (4.46 + 8.0) / 2 = 6.23

# Factor in asset characteristics
final_score = (6.23 + 9.0 + 6.0) / 3 = 7.08
```

Risk Level: HIGH (score between 5 and 8)

### 9.2 Impact of Changes

#### Barrier Improvement
If vehicle barriers are upgraded:
- Preventive Capability: 8 → 9
- New Effectiveness: 7.25 → 7.85
- Final Score: 7.08 → 6.82
- Still HIGH but closer to MEDIUM threshold

#### Criticality Change
If backup facility becomes operational:
- Criticality: 9 → 7
- Final Score: 7.08 → 6.41
- Remains HIGH but significantly reduced

#### Barrier Issue Impact
If vehicle barrier becomes COMPROMISED:
- Effectiveness: 7.15 → 1.43
- Final Score: 7.08 → 8.45
- Escalates to CRITICAL

### 9.3 Linked Asset Implications

Consider a nearby security post:
- Shares perimeter barriers
- Lower criticality (5)
- When main building barrier is compromised:
  * 70% own assessment + 30% linked impact
  * Barrier effectiveness also reduced
  * Risk level likely to increase by one level

This example demonstrates how:
1. Each component contributes to final risk
2. Barrier issues can escalate risks significantly
3. Asset criticality amplifies risk levels
4. Linked assets are affected by shared vulnerabilities
5. System responds dynamically to changes

Working groups can use these examples to:
- Model potential changes
- Justify security investments
- Plan maintenance schedules
- Develop contingency plans
- Understand cascading effects

## Conclusion
The GEMS risk assessment system provides a comprehensive, mathematically sound approach to risk evaluation. The weighted components ensure that all aspects of risk are properly considered, while the interconnected nature of the system ensures that changes in one area appropriately affect related areas. Regular review of these weightings and their impacts is crucial for maintaining system effectiveness and ensuring appropriate risk management decisions.

Through the practical examples provided, working groups can better understand how different factors influence the final risk assessment and make informed decisions about:
- Security investments
- Operational procedures
- Maintenance priorities
- Emergency response planning
- Resource allocation

The system's dynamic nature ensures that risk assessments remain current and accurate, while the mathematical relationships between components provide a reliable and defensible basis for security-related decisions.

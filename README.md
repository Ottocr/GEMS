Project Overview:
GEMS (Global Enterprise Monitoring System) is a comprehensive web-based application designed for global risk management. It enables security managers to input and manage detailed country and asset risk data, assess a wide spectrum of security risks, and visualize global risk levels. The platform addresses threats such as cyber-attacks, terrorism, activism, insider threats, and more. GEMS evaluates existing mitigations or 'barriers' and their effectiveness in reducing risks, aiming to protect assets and ensure business continuity in an increasingly complex global environment.
________________________________________
Project Objectives:
1.	Global Risk Assessment:
o	Data Input: Allow security managers to input and manage detailed country and asset risk data.
o	Risk Visualization: Provide a platform for assessing security risks and visualizing global risk levels across various threat vectors.
2.	Risk Mitigation and Barrier Evaluation:
o	Barrier Effectiveness: Evaluate existing security mitigations ('barriers') and their effectiveness in reducing risk.
o	Performance Adjustment: Adjust barrier effectiveness based on performance issues and incident reports, affecting overall risk assessments.
3.	Scenario Analysis and Impact Assessment:
o	Scenario Mapping: Map various scenarios (e.g., protests, theft, cyber-attacks) to relevant risks and barriers.
o	Impact Scoring: Provide scoring and impact assessments for scenarios based on current data and methodologies.
4.	Risk Matrix Generation and Trend Analysis:
o	Dynamic Matrices: Generate dynamic risk matrices for assets, incorporating criticality, vulnerability, and barrier effectiveness.
o	Trend Monitoring: Analyze risk trends over time to support proactive risk management and decision-making.
5.	Asset Linking and Shared Risk Management:
o	Asset Connections: Link assets with shared risks and barriers to manage interconnected risk profiles.
o	Assessment Updates: Update linked assets' risk assessments based on shared risks and barriers.
6.	Comprehensive Risk Logging and Auditing:
o	Risk Logs: Maintain detailed logs of risk assessments and changes over time for auditing and compliance.
o	Historical Data: Support data-driven decision-making with historical risk data.
________________________________________
Key Features and Models:
1.	Asset Management:
o	AssetType:
	Purpose: Defines types of assets (e.g., Data Center, Office, Pipeline).
	Options: Name, Description.
o	Asset:
	Purpose: Represents an individual asset with specific attributes.
	Options: Name, Description, Location (Latitude, Longitude), AssetType, Country, Criticality Score, Vulnerability Score, Scenarios, Barriers.
	Relationships: Linked to AssetType, Country, Scenarios, Barriers.
	Methods:
	calculate_criticality_score()
	calculate_vulnerability_score()
	update_scores()
	update_risk_assessment()
2.	Risk Management:
o	RiskType:
	Purpose: Defines main risk categories (e.g., Cyber Threat, Terrorism).
	Options: Name, Description.
o	RiskSubtype:
	Purpose: Specifies subcategories under a RiskType.
	Options: Name, Description, RiskType.
o	Scenario:
	Purpose: Represents potential risk scenarios linked to RiskSubtypes.
	Options: Name, Description, RiskSubtypes, Barriers.
	Relationships: Linked to RiskSubtypes, Barriers.
o	RiskScenarioAssessment:
	Purpose: Stores assessments of risks for an asset in a scenario.
	Options: Asset, Scenario, Likelihood Rating, Impact Score, Barrier Effectiveness, Residual Risk Score.
	Methods:
	calculate_residual_risk_score()
	calculate_barrier_effectiveness()
3.	Barrier Management:
o	BarrierCategory:
	Purpose: Categorizes barriers (e.g., Physical Security, Cybersecurity).
	Options: Name, Description.
o	Barrier:
	Purpose: Represents a mitigation measure or control.
	Options: Name, Description, Category, Performance Adjustment.
	Methods:
	get_overall_effectiveness_score()
	adjust_performance()
	update_overall_effectiveness()
	propagate_effectiveness()
o	BarrierEffectivenessScore:
	Purpose: Stores effectiveness scores of barriers against specific RiskTypes.
	Options: Barrier, RiskType, Preventive Capability, Detection Capability, Response Capability, Reliability, Coverage.
4.	Geographical Management:
o	Continent:
	Purpose: Groups countries by continent.
	Options: Name.
o	Country:
	Purpose: Represents countries with operational data.
	Options: Name, Code, Geo Data, Continent, Company Operated.
5.	Asset Linking:
o	AssetLink:
	Purpose: Links multiple assets with shared risks and barriers.
	Options: Name, Assets, Shared Risks, Shared Barriers.
	Purpose in Pipeline: Manages interconnected risk profiles and updates linked assets' risk assessments.
6.	Risk Matrices and Logs:
o	FinalRiskMatrix:
	Purpose: Generates and stores final risk matrices for assets and RiskTypes.
	Options: Asset, RiskType, Residual Risk Score, Risk Level, Sub-Risk Details, Barrier Details.
	Methods:
	generate_matrices()
	generate_overall_matrix()
	generate_risk_specific_matrices()
	generate_barrier_specific_matrices()
o	RiskLog:
	Purpose: Logs historical risk data for assets over time.
	Options: Asset, RiskType, Scores (BTA, Vulnerability, Criticality, Residual Risk), Timestamp.
7.	Signal Processing and Updates:
o	Purpose: Automates updates to risk assessments and matrices when data changes.
o	Functionality: Listens to model changes and triggers appropriate updates.
________________________________________
Relationships and Data Flow:
•	Assets are linked to AssetTypes, Countries, Scenarios, Barriers, and AssetLinks.
•	Scenarios are linked to RiskSubtypes, which are linked to RiskTypes.
•	Barriers have EffectivenessScores per RiskType.
•	RiskScenarioAssessments link Assets to Scenarios, incorporating barrier effectiveness to calculate residual risk scores.
•	BarrierIssueReports affect barrier performance, propagating updates to risk assessments and matrices.
•	BaselineThreatAssessments provide country-level risk data, impacting the final risk matrices.
•	FinalRiskMatrices compile all relevant data to produce risk levels for assets.
________________________________________
Methodologies and Approaches:
1.	Risk Assessment Process:
o	Combines asset criticality, vulnerability, scenario likelihood, impact, and barrier effectiveness.
o	Uses both quantitative (scores) and qualitative (expert inputs) data.
2.	Barrier Performance Adjustment:
o	Barrier effectiveness is adjusted based on performance issues via BarrierIssueReports.
o	Adjustments propagate through linked assets, affecting risk assessments and matrices.
3.	Dynamic Risk Matrix Generation:
o	FinalRiskMatrices are generated dynamically, reflecting the most current data.
4.	Asset Linking and Shared Risk Management:
o	Assets can be linked to share risks and barriers, allowing efficient updates to risk profiles.
5.	Automated Updates and Signal Processing:
o	Signals automate updates to risk assessments and matrices upon data changes.
6.	Trend Analysis and Risk Logging:
o	RiskLogs track changes over time, supporting trend analysis and historical reviews.
________________________________________
Visualization of Data Pipeline:
 ![image](https://github.com/user-attachments/assets/3bb475d6-975d-4dac-ac0f-258435829b0d)

Data Flow Resulting in a Risk Matrix for an Asset:
1.	Asset Data Collection:
o	Assets are created with essential information and assigned to AssetTypes and Countries.
2.	Assessment of Criticality and Vulnerability:
o	AssetCriticalityQuestions and AssetVulnerabilityQuestions are answered.
o	Scores are calculated to determine the asset's criticality and vulnerability.
3.	Scenario and Barrier Assignment:
o	Assets are linked to relevant Scenarios and Barriers.
4.	Risk Scenario Assessment:
o	For each scenario, a RiskScenarioAssessment is created.
o	Incorporates likelihood, impact, and barrier effectiveness to calculate the residual risk score.
5.	Barrier Effectiveness and Issues:
o	BarrierEffectivenessScores are used to assess barrier effectiveness.
o	BarrierIssueReports can adjust barrier performance, affecting risk assessments.
6.	Baseline Threat Assessment:
o	Country-specific BaselineThreatAssessments provide baseline risk scores.
7.	Final Risk Matrix Generation:
o	FinalRiskMatrix aggregates all data to produce the risk matrix.
o	Determines the overall risk level for the asset.
8.	Risk Logging and Updates:
o	RiskLogs are created for historical tracking.
o	Any changes trigger automated updates via signal processing.
________________________________________
Conclusion:
The updated GEMS system integrates asset management, risk assessment, barrier evaluation, and dynamic risk matrix generation into a cohesive platform. It leverages detailed models and relationships to accurately reflect the complex interplay between assets, risks, barriers, and geopolitical factors. Through automated updates and signal processing, the system ensures that risk assessments and matrices remain current, providing security managers with actionable insights for informed decision-making.


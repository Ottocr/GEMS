# Test API endpoints for GEMS risk assessment system
$baseUrl = "http://localhost:8000/api"
$headers = @{
    "Content-Type" = "application/json"
}

function Test-Endpoint {
    param (
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [string]$Body = $null
    )
    
    Write-Host "Testing $Name..." -NoNewline
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $headers
            UseBasicParsing = $true
        }

        if ($Body) {
            $params['Body'] = $Body
        }

        $response = Invoke-RestMethod @params
        Write-Host " Success" -ForegroundColor Green
        return $response
    } catch {
        Write-Host " Failed" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
            try {
                $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
                $errorBody = $reader.ReadToEnd()
                Write-Host "Response: $errorBody" -ForegroundColor Red
            } catch {
                Write-Host "Could not read error response" -ForegroundColor Red
            }
        }
        return $null
    }
}

Write-Host "=== Starting GEMS API Tests ==="

# 1. Authentication
$loginBody = @{
    username = "admin"
    password = "adminpass"
} | ConvertTo-Json

$tokenResponse = Test-Endpoint -Name "Authentication" -Url "$baseUrl/token-auth/" -Method "POST" -Body $loginBody
if (-not $tokenResponse) { 
    Write-Host "Authentication failed. Exiting..." -ForegroundColor Red
    exit 
}

# Add token to headers for subsequent requests
$headers["Authorization"] = "Token $($tokenResponse.token)"

# 2. Dashboard Data
Write-Host "`n=== Testing Dashboard ==="
$dashboard = Test-Endpoint -Name "Dashboard" -Url "$baseUrl/dashboard/data/"
if ($dashboard) {
    Write-Host "Total Countries: $($dashboard.total_countries)"
    Write-Host "Global Risk Score: $($dashboard.avg_global_risk_score)"
    Write-Host "Assets: $($dashboard.assets.Count)"
    Write-Host "Risk Types: $($dashboard.risk_types.Count)"
    Write-Host "Countries: $($dashboard.countries.Count)"
}

# 3. Security Manager Data
Write-Host "`n=== Testing Security Manager Data ==="
$securityData = Test-Endpoint -Name "Security Manager Data" -Url "$baseUrl/security-manager/data/"
if ($securityData) {
    Write-Host "Countries: $($securityData.countries.Count)"
    Write-Host "Asset Types: $($securityData.asset_types.Count)"
    Write-Host "Risk Types: $($securityData.risk_types.Count)"
    Write-Host "Barriers: $($securityData.barriers.Count)"
    Write-Host "Vulnerability Questions: $($securityData.vulnerability_questions.Count)"
    Write-Host "Criticality Questions: $($securityData.criticality_questions.Count)"
    
    if ($securityData.countries.Count -gt 0) {
        $firstCountry = $securityData.countries[0]
        Write-Host "`nTesting country-specific data..."
        $countryData = Test-Endpoint -Name "Country Data" -Url "$baseUrl/security-manager/data/?country_id=$($firstCountry.id)"
        if ($countryData -and $countryData.selected_country) {
            Write-Host "Selected Country: $($countryData.selected_country.name)"
            Write-Host "Assets: $($countryData.assets.Count)"
            Write-Host "BTA List: $($countryData.bta_list.Count)"
        }
    }
}

# 4. Risk Assessment Data
Write-Host "`n=== Testing Risk Assessment ==="
$riskTypes = Test-Endpoint -Name "Risk Types" -Url "$baseUrl/risk-assessment/data/"
if ($riskTypes) {
    foreach ($riskType in $riskTypes.risk_types) {
        Write-Host "Risk Type: $($riskType.name)"
        Write-Host "Description: $($riskType.description)"
        Write-Host "Subtypes: $($riskType.subtypes.Count)"
        foreach ($subtype in $riskType.subtypes) {
            Write-Host "  - $($subtype.name)"
        }
    }
}

# 5. Barrier Assessments
Write-Host "`n=== Testing Barrier Assessments ==="
$barriers = Test-Endpoint -Name "Barrier Assessments" -Url "$baseUrl/barriers/"
if ($barriers) {
    Write-Host "Total Barriers: $($barriers.barriers.Count)"
    
    foreach ($barrier in $barriers.barriers) {
        Write-Host "`nBarrier: $($barrier.name)"
        Write-Host "Category: $($barrier.category)"
        Write-Host "Effectiveness: $($barrier.avg_effectiveness)"
        Write-Host "Assets: $($barrier.assets_count)"
        
        # Test barrier details
        $details = Test-Endpoint -Name "Barrier Details" -Url "$baseUrl/barriers/$($barrier.id)/"
        if ($details -and $details.barrier) {
            Write-Host "`nBarrier Details:"
            Write-Host "Risk Types:"
            foreach ($rt in $details.barrier.risk_types) {
                Write-Host "  - $($rt.name)"
            }
            Write-Host "Risk Subtypes:"
            foreach ($rs in $details.barrier.risk_subtypes) {
                Write-Host "  - $($rs.risk_type.name): $($rs.name)"
            }
            Write-Host "Effectiveness Scores:"
            $scores = $details.barrier.effectiveness_scores
            $scores.PSObject.Properties | ForEach-Object {
                $score = $_.Value
                Write-Host "  $($score.risk_type)$(if($score.risk_subtype){" - $($score.risk_subtype)"}): $($score.overall)"
            }
        }

        # Test barrier trends
        $trends = Test-Endpoint -Name "Barrier Trends" -Url "$baseUrl/barriers/$($barrier.id)/trends/"
        if ($trends -and $trends.trend_data) {
            Write-Host "`nBarrier Trends:"
            Write-Host "Trend Direction: $($trends.trend_data.trend.direction)"
            Write-Host "Trend Percentage: $($trends.trend_data.trend.percentage)%"
            Write-Host "Risk Impacts:"
            foreach ($impact in $trends.trend_data.risk_impacts) {
                Write-Host "  $($impact.name) ($($impact.type)): $($impact.reduction)"
            }
        }
    }
}

# 6. Assets
Write-Host "`n=== Testing Assets ==="
$globalAssets = Test-Endpoint -Name "Global Assets" -Url "$baseUrl/assets/"
if ($globalAssets) {
    Write-Host "Total Assets: $($globalAssets.assets.Count)"
    foreach ($asset in $globalAssets.assets) {
        Write-Host "`nAsset: $($asset.name)"
        Write-Host "Type: $($asset.asset_type)"
        Write-Host "Country: $($asset.country)"
        Write-Host "Criticality: $($asset.criticality_score)"
        Write-Host "Vulnerability: $($asset.vulnerability_score)"
        
        # Asset Details
        $details = Test-Endpoint -Name "Asset Details" -Url "$baseUrl/assets/$($asset.id)/"
        if ($details -and $details.asset) {
            Write-Host "Description: $($details.asset.description)"
            Write-Host "Scenarios: $($details.asset.scenarios.Count)"
            Write-Host "Barriers: $($details.asset.barriers.Count)"
        }
        
        # Asset Risk Data
        $riskData = Test-Endpoint -Name "Asset Risk Data" -Url "$baseUrl/assets/$($asset.id)/risk-data/"
        if ($riskData -and $riskData.matrices) {
            Write-Host "`nRisk Matrices:"
            Write-Host "Overall: $($riskData.matrices.overall.Count)"
            Write-Host "Risk-Specific: $($riskData.matrices.risk_specific.Count)"
            Write-Host "Barrier-Specific: $($riskData.matrices.barrier_specific.Count)"
            
            # Test risk type specific matrices
            foreach ($matrix in $riskData.matrices.risk_specific) {
                Write-Host "`nRisk Type:"
                Write-Host "Score: $($matrix.residual_risk_score)"
                Write-Host "Level: $($matrix.risk_level)"
                if ($matrix.sub_risk_details) {
                    Write-Host "Scenario Assessments:"
                    foreach ($assessment in $matrix.sub_risk_details.scenario_assessments) {
                        Write-Host "  $($assessment.scenario):"
                        Write-Host "    Likelihood: $($assessment.likelihood)"
                        Write-Host "    Impact: $($assessment.impact)"
                        Write-Host "    Vulnerability: $($assessment.vulnerability)"
                        Write-Host "    Residual Risk: $($assessment.residual_risk)"
                    }
                }
            }
        }

        # Asset Barriers
        $barriers = Test-Endpoint -Name "Asset Barriers" -Url "$baseUrl/assets/$($asset.id)/barriers/"
        if ($barriers) {
            Write-Host "`nBarriers:"
            Write-Host "Categories: $($barriers.total_categories)"
            Write-Host "Asset Barriers: $($barriers.total_barriers)"
            
            # Display barrier categories
            Write-Host "`nBarrier Categories:"
            foreach ($category in $barriers.barrier_categories) {
                Write-Host "  $($category.name):"
                Write-Host "    Description: $($category.description)"
                Write-Host "    Barriers: $($category.barriers.Count)"
            }
            
            # Display asset's barriers
            Write-Host "`nAsset Barriers:"
            foreach ($barrier in $barriers.barriers) {
                Write-Host "`n  Barrier: $($barrier.name)"
                Write-Host "  Category: $($barrier.category.name)"
                Write-Host "  Description: $($barrier.description)"
                Write-Host "  Risk Types:"
                foreach ($rt in $barrier.risk_types) {
                    Write-Host "    - $($rt.name)"
                }
                Write-Host "  Risk Subtypes:"
                foreach ($rs in $barrier.risk_subtypes) {
                    Write-Host "    - $($rs.risk_type.name): $($rs.name)"
                }
                Write-Host "  Effectiveness Scores:"
                $scores = $barrier.effectiveness_scores
                $scores.PSObject.Properties | ForEach-Object {
                    $score = $_.Value
                    Write-Host "    $($score.risk_type)$(if($score.risk_subtype){" - $($score.risk_subtype)"}): $($score.overall)"
                }
            }
        }

        # Asset Form Data
        $formData = Test-Endpoint -Name "Asset Form Data" -Url "$baseUrl/assets/form-data/$($asset.id)/"
        if ($formData) {
            Write-Host "`nForm Data:"
            Write-Host "Asset Types: $($formData.asset_types.Count)"
            Write-Host "Countries: $($formData.countries.Count)"
            Write-Host "Barriers: $($formData.barriers.Count)"
            Write-Host "Scenarios: $($formData.scenarios.Count)"
            if ($formData.asset) {
                Write-Host "Criticality Answers: $($formData.asset.criticality_answers.Count)"
                Write-Host "Vulnerability Answers: $($formData.asset.vulnerability_answers.Count)"
            }
        }
    }
}

Write-Host "`n=== Testing Complete ==="

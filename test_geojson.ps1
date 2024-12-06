$baseUrl = "http://localhost:8000/api"
$headers = @{
    "Content-Type" = "application/json"
}

# 1. Get authentication token
$loginBody = @{
    username = "admin"
    password = "adminpass"
} | ConvertTo-Json

Write-Host "Getting authentication token..."
$tokenResponse = Invoke-RestMethod -Uri "$baseUrl/token-auth/" -Method "POST" -Headers $headers -Body $loginBody

# Add token to headers
$headers["Authorization"] = "Token $($tokenResponse.token)"

# 2. Get Security Manager data to find USA ID
Write-Host "`nFetching Security Manager data to find USA..."
$securityData = Invoke-RestMethod -Uri "$baseUrl/security-manager/data/" -Method "GET" -Headers $headers
$usa = $securityData.countries | Where-Object { $_.name -eq "United States of America" }

if ($usa) {
    Write-Host "Found USA with ID: $($usa.id)"
    
    # 3. Get GeoJSON data for USA
    Write-Host "`nFetching GeoJSON data for USA..."
    $response = Invoke-RestMethod -Uri "$baseUrl/countries/$($usa.id)/geojson/" -Method "GET" -Headers $headers

    # Pretty print the response
    Write-Host "`nResponse Structure:"
    Write-Host "Success: $($response.success)"
    Write-Host "`nGeoJSON Data:"
    $response.geojson | ConvertTo-Json -Depth 10 | Write-Host

    # Save to file for inspection
    $response.geojson | ConvertTo-Json -Depth 10 | Out-File "usa_geojson.json"
    Write-Host "`nGeoJSON data has been saved to 'usa_geojson.json' for inspection"
} else {
    Write-Host "Could not find United States of America in the countries list"
}

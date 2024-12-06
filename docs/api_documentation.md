# GEMS API Documentation

## Authentication

All API endpoints require token authentication. Include the token in the request header:
```
Authorization: Token your-token-here
```

## API Endpoints

### Dashboard APIs

#### Get Dashboard Overview
```http
GET /api/dashboard/
```
Returns global statistics and risk overview.

Response:
```json
{
    "total_countries": 1,
    "total_assets": 2,
    "global_risk_score": 5.0,
    "risk_types": 4,
    "countries": 1
}
```

### Security Manager APIs

#### Get Security Manager Data
```http
GET /api/security-manager/data/
```
Returns reference data for security managers.

Response:
```json
{
    "countries": [
        {
            "id": 1,
            "name": "United States",
            "code": "USA"
        }
    ],
    "asset_types": [
        {
            "id": 1,
            "name": "Office Building"
        }
    ],
    "risk_types": [
        {
            "id": 1,
            "name": "Terrorism",
            "description": "Risks related to terrorist activities"
        }
    ],
    "barriers": [
        {
            "id": 1,
            "name": "Perimeter Fence",
            "category": "Physical Security"
        }
    ]
}
```

### Country APIs

#### Get Country Details
```http
GET /api/countries/{country_id}/
```
Returns detailed information about a specific country.

Response:
```json
{
    "id": 1,
    "name": "United States",
    "code": "USA",
    "assets": [
        {
            "id": 1,
            "name": "Main Office",
            "risk_score": 4.2
        }
    ],
    "baseline_threats": [
        {
            "risk_type": "Terrorism",
            "score": 5
        }
    ]
}
```

### Asset APIs

#### Get Global Assets
```http
GET /api/assets/
```
Returns list of all assets.

Response:
```json
{
    "assets": [
        {
            "id": 1,
            "name": "Main Office",
            "asset_type": "Office Building",
            "country": "United States",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "criticality_score": 8,
            "vulnerability_score": 5
        }
    ]
}
```

#### Get Asset Details
```http
GET /api/assets/{asset_id}/
```
Returns detailed information about a specific asset.

Response:
```json
{
    "id": 1,
    "name": "Main Office",
    "asset_type": "Office Building",
    "description": "Corporate headquarters",
    "country": "United States",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "criticality_score": 8,
    "vulnerability_score": 5,
    "scenarios": [
        {
            "id": 1,
            "name": "Facility Attack",
            "description": "Physical attack on facility"
        }
    ],
    "barriers": [
        {
            "id": 1,
            "name": "Perimeter Fence",
            "category": "Physical Security"
        }
    ]
}
```

#### Get Asset Risk Data
```http
GET /api/assets/{asset_id}/risk-data/
```
Returns risk matrices and assessments for an asset.

Response:
```json
{
    "matrices": {
        "overall": [
            {
                "risk_type": "Terrorism",
                "score": 2.72,
                "level": "LOW"
            }
        ],
        "risk_specific": [...],
        "barrier_specific": [...]
    }
}
```

#### Get Asset Barriers
```http
GET /api/assets/{asset_id}/barriers/
```
Returns barriers and their effectiveness for an asset.

Response:
```json
{
    "barrier_categories": [
        {
            "id": 1,
            "name": "Physical Security",
            "description": "Physical security measures",
            "barriers": [
                {
                    "id": 1,
                    "name": "Perimeter Fence",
                    "description": "Main perimeter security fence"
                }
            ]
        }
    ],
    "barriers": [
        {
            "id": 1,
            "name": "Perimeter Fence",
            "category": {
                "id": 1,
                "name": "Physical Security"
            },
            "description": "Main perimeter security fence",
            "effectiveness_scores": {
                "type_1": {
                    "risk_type": "Terrorism",
                    "preventive": 8,
                    "detection": 7,
                    "response": 7,
                    "reliability": 8,
                    "coverage": 8,
                    "overall": 7.6
                }
            }
        }
    ]
}
```

#### Add Asset Barrier
```http
POST /api/assets/add-barrier/
```
Adds a barrier to an asset.

Request:
```json
{
    "asset_id": 1,
    "barrier_id": 1
}
```

Response:
```json
{
    "success": true
}
```

#### Remove Asset Barrier
```http
POST /api/assets/remove-barrier/
```
Removes a barrier from an asset.

Request:
```json
{
    "asset_id": 1,
    "barrier_id": 1
}
```

Response:
```json
{
    "success": true
}
```

### Barrier APIs

#### Get Barrier Assessments
```http
GET /api/barriers/assessments/
```
Returns effectiveness assessments for all barriers.

Response:
```json
{
    "total_barriers": 3,
    "barriers": [
        {
            "name": "Perimeter Fence",
            "category": "Physical Security",
            "effectiveness": 8.0,
            "assets": 2
        }
    ]
}
```

#### Get Barrier Details
```http
GET /api/barriers/{barrier_id}/details/
```
Returns detailed information about a specific barrier.

Response:
```json
{
    "id": 1,
    "name": "Perimeter Fence",
    "category": "Physical Security",
    "risk_types": [
        {
            "name": "Terrorism",
            "effectiveness": 7.6
        }
    ],
    "risk_subtypes": [
        {
            "name": "Vehicle Attack",
            "risk_type": "Terrorism",
            "effectiveness": 8.6
        }
    ]
}
```

#### Get Barrier Trends
```http
GET /api/barriers/{barrier_id}/trends/
```
Returns trend data for a barrier's effectiveness.

Response:
```json
{
    "trend_direction": "stable",
    "trend_percentage": "0.0%",
    "risk_impacts": {
        "Terrorism": 8.6,
        "Vehicle Attack": 8.6
    }
}
```

### Risk Assessment APIs

#### Get Risk Types
```http
GET /api/risks/types/
```
Returns all risk types and their subtypes.

Response:
```json
{
    "risk_types": [
        {
            "name": "Terrorism",
            "description": "Risks related to terrorist activities",
            "subtypes": [
                {
                    "name": "Physical Attack",
                    "description": "Direct physical attack on asset"
                },
                {
                    "name": "Vehicle Attack",
                    "description": "Attack using vehicles"
                }
            ]
        }
    ]
}
```

## Error Handling

All endpoints return standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

Error Response Format:
```json
{
    "success": false,
    "error": "Error message here"
}
```

## Rate Limiting

- 1000 requests per hour per token
- Rate limit headers included in responses:
  - X-RateLimit-Limit
  - X-RateLimit-Remaining
  - X-RateLimit-Reset

## Pagination

For list endpoints, use query parameters:
- page: Page number (default: 1)
- page_size: Items per page (default: 20, max: 100)

Response includes pagination metadata:
```json
{
    "count": 100,
    "next": "http://api/endpoint/?page=3",
    "previous": "http://api/endpoint/?page=1",
    "results": [...]
}
```

## Filtering

Most list endpoints support filtering via query parameters:
```
/api/assets/?country=US&risk_level=HIGH
/api/barriers/?category=Physical&effectiveness_gt=7
```

## Versioning

API version is specified in the URL:
```
/api/v1/endpoint/
```

Current stable version: v1

# INEsCape API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require authentication using JWT tokens.

### Login

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user&password=pass
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Using Tokens

Include the token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

## Endpoints

### Health Check

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Synthetic Data Generation

```http
POST /api/v1/synthetic-data/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "n_patients": 1000,
  "cancer_ratio": 0.3,
  "seed": 42,
  "save_to_db": true
}
```

### Data Collection

```http
POST /api/v1/data-collection/collect
Authorization: Bearer <token>
Content-Type: application/json

{
  "source": "tcga",
  "query": "esophageal cancer",
  "auto_download": false
}
```

### Machine Learning Models

#### Train Model

```http
POST /api/v1/ml-models/train
Authorization: Bearer <token>
Content-Type: application/json

{
  "data_path": "data.csv",
  "target_column": "has_cancer",
  "model_type": "RandomForest",
  "test_size": 0.2
}
```

#### Predict

```http
POST /api/v1/ml-models/predict
Authorization: Bearer <token>
Content-Type: application/json

{
  "model_id": "model_123",
  "features": {
    "age": 65,
    "bmi": 28.5
  }
}
```

### Clinical Decision Support

#### Risk Prediction

```http
POST /api/v1/cds/risk-prediction
Authorization: Bearer <token>
Content-Type: application/json

{
  "patient_data": {
    "age": 65,
    "gender": "Male",
    "smoking": true
  }
}
```

#### Treatment Recommendation

```http
POST /api/v1/cds/treatment-recommendation
Authorization: Bearer <token>
Content-Type: application/json

{
  "patient_data": {
    "age": 65,
    "gender": "Male"
  },
  "cancer_data": {
    "t_stage": "T3",
    "n_stage": "N1",
    "m_stage": "M0"
  }
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

### Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting

- Authentication endpoints: 5 requests/second
- API endpoints: 10 requests/second

## Interactive Documentation

Visit `/docs` for Swagger UI or `/redoc` for ReDoc.


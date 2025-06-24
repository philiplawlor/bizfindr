# BizFindr API Documentation

This document describes the RESTful API endpoints provided by the BizFindr application.

## Base URL

All API endpoints are relative to the base URL:
```
http://localhost:5000/api
```

## Authentication

All endpoints require authentication via API key. Include the API key in the `X-API-Key` header.

## Endpoints

### Get All Registrations

```
GET /registrations
```

**Query Parameters:**
- `page` (optional, default: 1) - Page number
- `per_page` (optional, default: 20) - Items per page
- `sort` (optional) - Field to sort by (e.g., `date_registration`)
- `order` (optional, default: `desc`) - Sort order (`asc` or `desc`)

**Example Request:**
```http
GET /api/registrations?page=1&per_page=10&sort=date_registration&order=desc
X-API-Key: your-api-key
```

**Response:**
```json
{
  "data": [
    {
      "id": "507f1f77bcf86cd799439011",
      "registration_id": "CT12345678",
      "business_name": "Example Business LLC",
      "business_type": "Limited Liability Company",
      "date_registration": "2025-06-01T00:00:00",
      "status": "Active",
      "address": {
        "street": "123 Main St",
        "city": "Hartford",
        "state": "CT",
        "zip": "06103"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_pages": 5,
    "total_items": 42
  }
}
```

### Search Registrations

```
GET /registrations/search
```

**Query Parameters:**
- `q` (required) - Search query
- `business_type` (optional) - Filter by business type
- `status` (optional) - Filter by status
- `date_from` (optional) - Filter by registration date (ISO 8601 format)
- `date_to` (optional) - Filter by registration date (ISO 8601 format)

**Example Request:**
```http
GET /api/registrations/search?q=restaurant&business_type=LLC&status=Active
X-API-Key: your-api-key
```

**Response:**
```json
{
  "data": [
    {
      "id": "507f1f77bcf86cd799439011",
      "registration_id": "CT12345678",
      "business_name": "Best Restaurant LLC",
      "business_type": "Limited Liability Company",
      "date_registration": "2025-06-15T00:00:00",
      "status": "Active"
    }
  ],
  "meta": {
    "total": 1,
    "query": {
      "q": "restaurant",
      "business_type": "LLC",
      "status": "Active"
    }
  }
}
```

### Get Registration by ID

```
GET /registrations/:id
```

**Path Parameters:**
- `id` - Registration ID

**Example Request:**
```http
GET /api/registrations/507f1f77bcf86cd799439011
X-API-Key: your-api-key
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "registration_id": "CT12345678",
  "business_name": "Example Business LLC",
  "business_type": "Limited Liability Company",
  "date_registration": "2025-06-01T00:00:00",
  "status": "Active",
  "address": {
    "street": "123 Main St",
    "city": "Hartford",
    "state": "CT",
    "zip": "06103"
  },
  "created_at": "2025-06-20T10:30:00Z",
  "updated_at": "2025-06-20T10:30:00Z"
}
```

### Get Latest Registration Date

```
GET /registrations/latest-date
```

**Example Request:**
```http
GET /api/registrations/latest-date
X-API-Key: your-api-key
```

**Response:**
```json
{
  "latest_date": "2025-06-20T00:00:00Z"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": {
    "code": "invalid_request",
    "message": "Invalid request parameters"
  }
}
```

### 401 Unauthorized
```json
{
  "error": {
    "code": "unauthorized",
    "message": "Missing or invalid API key"
  }
}
```

### 404 Not Found
```json
{
  "error": {
    "code": "not_found",
    "message": "The requested resource was not found"
  }
}
```

### 500 Internal Server Error
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected error occurred"
  }
}
```

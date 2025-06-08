# FastAPI Task Management - Authentication API

## Overview

The authentication system provides JWT-based user registration, login, and protected route access.

## Base URL

```
http://localhost:8000/api/v1/auth
```

## Endpoints

### 1. Register User

**POST** `/register`

Create a new user account.

**Request Body:**

```json
{
  "email": "user@example.com",
  "username": "username123",
  "full_name": "John Doe",
  "password": "SecurePass123"
}
```

**Validation Rules:**

- **Email**: Valid email format
- **Username**: 3-50 chars, alphanumeric + underscore/hyphen only
- **Full Name**: 2-255 chars
- **Password**: Min 8 chars with uppercase, lowercase, and digit

**Response (201):**

```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username123",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": false,
    "created_at": "2025-06-08T07:47:34.950154",
    "updated_at": "2025-06-08T07:47:34.950157"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Login User

**POST** `/login`

Authenticate user and get access token.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username123",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": false,
    "created_at": "2025-06-08T07:47:34.950154",
    "updated_at": "2025-06-08T07:47:34.950157"
  }
}
```

### 3. Get Current User Profile

**GET** `/me`

Get the current authenticated user's profile.

**Headers:**

```
Authorization: Bearer <your_jwt_token>
```

**Response (200):**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username123",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-06-08T07:47:34.950154",
  "updated_at": "2025-06-08T07:47:34.950157"
}
```

### 4. Logout

**POST** `/logout`

Logout user (client-side token disposal).

**Response (200):**

```json
{
  "message": "Successfully logged out"
}
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Email already registered"
}
```

### 401 Unauthorized

```json
{
  "detail": "Incorrect email or password"
}
```

### 403 Forbidden

```json
{
  "detail": "Not authenticated"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "password"],
      "msg": "Password must be at least 8 characters long",
      "input": "short"
    }
  ]
}
```

## Usage Examples

### cURL Examples

**Register:**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "TestPassword123"
  }'
```

**Login:**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123"
  }'
```

**Access Protected Route:**

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## Authentication Flow

1. **Register** or **Login** to get JWT token
2. Include token in `Authorization: Bearer <token>` header for protected routes
3. Token expires in 30 minutes (configurable)
4. **Logout** by discarding token client-side

## Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT token-based authentication
- ✅ Input validation and sanitization
- ✅ Unique email and username constraints
- ✅ Strong password requirements
- ✅ Proper error handling and status codes

## Interactive Documentation

Visit `http://localhost:8000/docs` for Swagger UI documentation with interactive testing.

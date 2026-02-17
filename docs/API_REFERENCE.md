# 📚 Doctor Onboarding API Reference

> Complete API documentation for the CAEPY Doctor Onboarding Platform

**Version:** 2.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**Authentication:** JWT Bearer Token (obtained via OTP verification)

---

## 📋 Table of Contents

1. [Authentication](#-authentication)
2. [Health Endpoints](#-health-endpoints)
3. [Doctor CRUD](#-doctor-crud)
4. [Onboarding](#-onboarding)
5. [Voice Onboarding](#-voice-onboarding)
6. [Dropdown Data](#-dropdown-data)
7. [Hospitals](#-hospitals)
8. [Blob Storage](#-blob-storage)
9. [Testimonials](#-testimonials)
10. [Admin Endpoints](#-admin-endpoints)

---

## 🔐 Authentication

### POST `/auth/otp/request`
Request OTP for phone number authentication.

**Request Body:**
```json
{
  "mobile_number": "9988776655"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "mobile_number": "99****6655",
  "expires_in_seconds": 300
}
```

---

### POST `/auth/otp/verify`
Verify OTP and receive JWT token.

**Request Body:**
```json
{
  "mobile_number": "9988776655",
  "otp": "123456"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "OTP verified successfully",
  "doctor_id": 1,
  "is_new_user": false,
  "mobile_number": "9988776655",
  "role": "user",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### POST `/auth/otp/resend`
Resend OTP to the same mobile number.

---

### POST `/validateandlogin` (Development Only)
Mock OTP validation for development.

**Request Body:**
```json
{
  "phone_number": "9988776655",
  "otp": "123456"
}
```

---

## 🏥 Health Endpoints

### GET `/health`
Comprehensive health check for all dependencies.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "doctor-onboarding-service",
  "version": "2.0.0",
  "environment": "development",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 2.5,
      "message": "Connected"
    },
    "ai_service": {
      "status": "healthy",
      "message": "API key configured"
    }
  }
}
```

---

### GET `/ready`
Kubernetes readiness probe.

**Response (200):**
```json
{
  "status": "ready"
}
```

---

## 👨‍⚕️ Doctor CRUD

> **Authentication Required:** Bearer Token

### POST `/doctors`
Create a new doctor record.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com",
  "phone": "+919988776655",
  "primary_specialization": "Cardiology",
  "years_of_experience": 15,
  "medical_registration_number": "MED12345",
  "qualifications": ["MBBS", "MD - Cardiology"]
}
```

**Response (201):**
```json
{
  "message": "Doctor created successfully",
  "data": { /* DoctorResponse */ }
}
```

---

### GET `/doctors`
List all doctors with pagination.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 100) |
| `specialization` | string | null | Filter by specialization |

**Response (200):**
```json
{
  "message": "Doctors retrieved successfully",
  "data": [ /* DoctorSummary[] */ ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 100,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

---

### GET `/doctors/{doctor_id}`
Get doctor by ID.

---

### GET `/doctors/email/{email}`
Get doctor by email address.

---

### GET `/doctors/phone/{phone_number}`
Get doctor by phone number.

---

### PUT `/doctors/{doctor_id}`
Update doctor information.

---

### DELETE `/doctors/{doctor_id}`
Soft-delete a doctor.

---

### DELETE `/doctors/{doctor_id}/erase`
Permanently erase all doctor records (GDPR compliance).

---

### DELETE `/doctors/erase-all` (Development Only)
Erase all records from all tables.

---

## 📄 Onboarding

> **Authentication Required:** Bearer Token

### POST `/onboarding/extract-resume`
Extract structured data from resume (PDF/Image).

**Content-Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `file` | File | Resume file (PDF, PNG, JPG, JPEG) |

**Response (200):**
```json
{
  "success": true,
  "message": "Resume parsed successfully",
  "data": {
    "title": "Dr.",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@example.com",
    "primary_specialization": "Cardiology",
    "qualifications": [
      {
        "degree": "MBBS",
        "institution": "AIIMS Delhi",
        "year": 2010
      }
    ],
    "practice_locations": []
  },
  "processing_time_ms": 2500.5
}
```

---

### POST `/onboarding/generate-profile-content`
Generate AI-written profile sections.

**Request Body:**
```json
{
  "doctor_identifier": "doctor_123",
  "doctor_data": { /* Full doctor data */ },
  "sections": ["professional_overview", "about_me", "professional_tagline"]
}
```

---

### POST `/onboarding/sync-to-linqmd/{doctor_id}`
Sync doctor data to LinqMD platform.

---

## 🎤 Voice Onboarding

> **Authentication Required:** Bearer Token

### POST `/voice/start`
Start a new voice onboarding session.

**Request Body:**
```json
{
  "language": "en"
}
```

**Response (200):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "greeting": "Hello! I'm here to help you complete your doctor registration...",
  "fields_total": 8,
  "created_at": "2026-01-11T09:30:00Z"
}
```

---

### POST `/voice/chat`
Send a message in the voice conversation.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_transcript": "My name is Dr. Sarah Johnson and I specialize in Cardiology"
}
```

**Response (200):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "ai_response": "Nice to meet you, Dr. Sarah Johnson!...",
  "fields_collected": 2,
  "fields_total": 8,
  "fields_status": [ /* FieldStatusItem[] */ ],
  "current_data": { /* Collected data */ },
  "is_complete": false,
  "turn_number": 2
}
```

---

### GET `/voice/session/{session_id}`
Get current session status.

---

### POST `/voice/finalize/{session_id}`
Finalize a completed voice session.

---

### DELETE `/voice/session/{session_id}`
Cancel/delete a voice session.

---

### GET `/voice/field-config`
Get voice field configuration.

---

## 📊 Dropdown Data

> **Authentication Required:** Bearer Token

### GET `/dropdown-data/specialisations`
Get unique specialisation values.

---

### GET `/dropdown-data/sub-specialisations`
Get unique sub-specialisation values.

---

### GET `/dropdown-data/degrees`
Get unique degree values.

---

### GET `/dropdown-data/all`
Get all dropdown data in one request.

**Response (200):**
```json
{
  "message": "Dropdown data retrieved successfully",
  "data": {
    "specialisations": ["Cardiology", "Neurology", "Pediatrics"],
    "sub_specialisations": ["Interventional Cardiology", "Electrophysiology"],
    "degrees": ["MBBS", "MD", "MS", "DM", "MCh"]
  }
}
```

---

### POST `/dropdown-data/values`
Add new dropdown values.

---

## 🏨 Hospitals

> **Authentication Required:** Bearer Token

### GET `/hospitals/search`
Search hospitals for autocomplete.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query |
| `city` | string | Filter by city |
| `state` | string | Filter by state |
| `limit` | int | Max results (default 20) |

---

### GET `/hospitals/{hospital_id}`
Get hospital by ID.

---

### POST `/hospitals`
Create a new hospital.

---

### GET `/hospitals`
List all hospitals (with filters).

---

### PUT `/hospitals/{hospital_id}`
Update hospital details.

---

### DELETE `/hospitals/{hospital_id}`
Soft-delete a hospital.

---

### Doctor-Hospital Affiliations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/hospitals/affiliations` | Create affiliation |
| GET | `/hospitals/doctor/{doctor_id}/affiliations` | Get doctor's affiliations |
| PUT | `/hospitals/affiliations/{affiliation_id}` | Update affiliation |
| DELETE | `/hospitals/affiliations/{affiliation_id}` | Delete affiliation |

---

## 📁 Blob Storage

> **Authentication Required:** Bearer Token

### GET `/blobs/{doctor_id}/{media_category}/{blob_filename}`
Retrieve a blob file.

---

### HEAD `/blobs/{doctor_id}/{media_category}/{blob_filename}`
Check if blob exists.

---

### GET `/blobs/stats`
Get blob storage statistics.

---

## ⭐ Testimonials

### GET `/testimonials`
Get active testimonials (public).

---

### GET `/testimonials/admin`
Get all testimonials (admin view).

---

### GET `/testimonials/{testimonial_id}`
Get testimonial by ID.

---

### POST `/testimonials`
Create a new testimonial.

**Request Body:**
```json
{
  "doctor_name": "Dr. Sarah Johnson",
  "comment": "Excellent platform for doctor onboarding!",
  "specialty": "Cardiology",
  "designation": "Senior Consultant",
  "hospital_name": "Apollo Hospital",
  "location": "Mumbai",
  "rating": 5,
  "is_active": true,
  "display_order": 1
}
```

---

### PATCH `/testimonials/{testimonial_id}`
Update a testimonial.

---

### DELETE `/testimonials/{testimonial_id}`
Delete a testimonial.

---

### POST `/testimonials/{testimonial_id}/toggle-active`
Toggle testimonial active status.

---

## 🔒 Admin Endpoints

> **Authentication Required:** Admin or Operational Role

---

### Onboarding Admin (`/onboarding-admin`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/identities` | Create doctor identity |
| GET | `/identities/{doctor_id}` | Get identity by doctor ID |
| GET | `/identities/by-email` | Get identity by email |
| PUT | `/details/{doctor_id}` | Upsert doctor details |
| GET | `/details/{doctor_id}` | Get doctor details |
| POST | `/media/{doctor_id}` | Add media metadata |
| POST | `/media/{doctor_id}/upload` | Upload file directly |
| GET | `/media/{doctor_id}` | List media for doctor |
| DELETE | `/media/{media_id}` | Delete media |
| POST | `/status-history` | Add status history |
| GET | `/status-history/{doctor_id}` | Get status history |
| GET | `/doctors/by-status` | List doctors by status |

---

### Voice Config Admin (`/voice-config`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `` | Get full voice configuration |
| GET | `/blocks/{block_number}` | Get specific block |
| POST | `/blocks` | Create voice block |
| PUT | `/blocks/{block_id}` | Update voice block |
| DELETE | `/blocks/{block_id}` | Delete voice block |
| POST | `/blocks/{block_id}/fields` | Add field to block |
| PUT | `/fields/{field_id}` | Update field |
| DELETE | `/fields/{field_id}` | Delete field |
| POST | `/seed` | Seed initial configuration |
| POST | `/reset` | Reset to defaults |

---

### Admin Dropdown Options (`/admin/dropdown-options`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fields` | List all dropdown fields |
| GET | `/fields/{field_name}` | Get options for field |
| POST | `/fields/{field_name}` | Add option to field |
| POST | `/fields/{field_name}/bulk` | Bulk add options |
| PUT | `/options/{option_id}` | Update option |
| DELETE | `/options/{option_id}` | Deactivate option |
| GET | `/stats` | Get dropdown statistics |
| GET | `/unverified` | List unverified options |
| POST | `/options/{option_id}/verify` | Verify an option |
| POST | `/seed` | Seed dropdown values |

---

### Admin User Management (`/admin/users`)

> **Authentication Required:** Admin Role Only

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `` | List all users |
| GET | `/admins` | List admin users |
| GET | `/{user_id}` | Get user by ID |
| POST | `` | Create new user |
| PATCH | `/{user_id}` | Update user |
| PATCH | `/{user_id}/role` | Update user role |
| PATCH | `/{user_id}/status` | Update active status |
| DELETE | `/{user_id}` | Deactivate user |

**User Roles:**
- `admin` - Full access to all admin endpoints
- `operational` - Limited admin access (configurable)
- `user` - Regular user (no admin access)

---

## 📊 Response Formats

### Success Response
```json
{
  "message": "Operation successful",
  "data": { /* Response data */ }
}
```

### Paginated Response
```json
{
  "message": "Items retrieved",
  "data": [ /* Array of items */ ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 100,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  },
  "meta": {
    "request_id": null,
    "timestamp": "2026-02-14T12:00:00Z",
    "version": "2.0.0"
  }
}
```

---

## 🔑 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `INVALID_TOKEN` | 401 | Token is invalid |
| `USER_NOT_FOUND` | 401 | User not in users table |
| `USER_INACTIVE` | 403 | User account deactivated |
| `ADMIN_REQUIRED` | 403 | Admin role required |
| `INSUFFICIENT_PERMISSIONS` | 403 | Role lacks permissions |
| `DOCTOR_NOT_FOUND` | 404 | Doctor record not found |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `EXTRACTION_ERROR` | 422 | AI extraction failed |
| `OTP_EXPIRED` | 401 | OTP has expired |
| `INVALID_OTP` | 401 | OTP is incorrect |

---

## 🔧 Rate Limits

| Endpoint Type | Limit |
|--------------|-------|
| OTP Request | 3 per minute per phone |
| OTP Verify | 5 attempts per OTP |
| Resume Extraction | 10 per minute |
| Voice Chat | 60 per minute per session |
| Admin APIs | 100 per minute |

---

## 📝 Notes

1. **Phone Number Format**: Indian mobile numbers (10 digits starting with 6-9), automatically normalized to +91XXXXXXXXXX
2. **File Size Limits**: Resume uploads max 10MB, media uploads max 50MB
3. **Session Timeout**: Voice sessions expire after 30 minutes of inactivity
4. **Token Expiry**: JWT tokens expire after 30 minutes (configurable)

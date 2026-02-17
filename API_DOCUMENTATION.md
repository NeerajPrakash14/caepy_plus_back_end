# Doctor Onboarding API - Complete Documentation

**Base URL:** `http://127.0.0.1:8000/api/v1`

**Total Endpoints:** 109

---

## Table of Contents

1. [Authentication (4 endpoints)](#1-authentication)
2. [Health Check (3 endpoints)](#2-health-check)
3. [Doctors (9 endpoints)](#3-doctors)
4. [Hospitals (11 endpoints)](#4-hospitals)
5. [Hospital Affiliations (6 endpoints)](#5-hospital-affiliations)
6. [Onboarding (14 endpoints)](#6-onboarding)
7. [Onboarding Admin (16 endpoints)](#7-onboarding-admin)
8. [Dropdown Data (5 endpoints)](#8-dropdown-data)
9. [Admin Dropdown Options (11 endpoints)](#9-admin-dropdown-options)
10. [Admin Users (8 endpoints)](#10-admin-users)
11. [Testimonials (7 endpoints)](#11-testimonials)
12. [Blob Storage (3 endpoints)](#12-blob-storage)
13. [Voice Onboarding (5 endpoints)](#13-voice-onboarding)
14. [Voice Config (7 endpoints)](#14-voice-config)

---

## 1. AUTHENTICATION

### 1.1 Request OTP
**POST** `/auth/otp/request`

Send OTP to mobile number for authentication.

**Request Body:**
```json
{
  "mobile_number": "9443453525"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/auth/otp/request' \
--header 'Content-Type: application/json' \
--data '{"mobile_number": "9443453525"}'
```

**Response (200):**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "mobile_number": "94****3525",
  "expires_in_seconds": 300
}
```

---

### 1.2 Resend OTP
**POST** `/auth/otp/resend`

Resend OTP to the same mobile number (invalidates previous OTP).

**Request Body:**
```json
{
  "mobile_number": "9443453525"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/auth/otp/resend' \
--header 'Content-Type: application/json' \
--data '{"mobile_number": "9443453525"}'
```

**Response (200):**
```json
{
  "success": true,
  "message": "OTP resent successfully",
  "mobile_number": "94****3525",
  "expires_in_seconds": 300
}
```

---

### 1.3 Verify OTP
**POST** `/auth/otp/verify`

Verify OTP and get JWT access token.

**Request Body:**
```json
{
  "mobile_number": "9443453525",
  "otp": "123456"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/auth/otp/verify' \
--header 'Content-Type: application/json' \
--data '{"mobile_number": "9443453525", "otp": "123456"}'
```

**Response (200):**
```json
{
  "success": true,
  "message": "OTP verified successfully",
  "doctor_id": 7,
  "is_new_user": false,
  "mobile_number": "9443453525",
  "role": "user",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### 1.4 Validate and Login (Dev Only)
**POST** `/validateandlogin`

Development endpoint - accepts any OTP and returns JWT token.

**Request Body:**
```json
{
  "phone_number": "9443453525",
  "otp": "123456"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/validateandlogin' \
--header 'Content-Type: application/json' \
--data '{"phone_number": "9443453525", "otp": "123456"}'
```

**Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

---

## 2. HEALTH CHECK

### 2.1 Health Check
**GET** `/health`

Returns comprehensive health status of the service.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/health'
```

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
      "latency_ms": 1.2,
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

### 2.2 Liveness Probe
**GET** `/live`

Kubernetes liveness probe endpoint.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/live'
```

**Response (200):**
```json
{
  "status": "alive"
}
```

---

### 2.3 Readiness Probe
**GET** `/ready`

Kubernetes readiness probe endpoint.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/ready'
```

**Response (200):**
```json
{
  "status": "ready"
}
```

---

## 3. DOCTORS

### 3.1 List Doctors
**GET** `/doctors`

Get paginated list of all registered doctors.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `specialization` (string): Filter by specialization

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/doctors?page=1&page_size=20' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

**Response (200):**
```json
{
  "success": true,
  "message": "Doctors retrieved successfully",
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 50,
    "total_pages": 3
  }
}
```

---

### 3.2 Create Doctor
**POST** `/doctors`

Register a new doctor.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone_number": "9876543210",
  "primary_specialization": "Cardiology",
  "medical_registration_number": "MCI12345"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/doctors' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone_number": "9876543210",
  "primary_specialization": "Cardiology",
  "medical_registration_number": "MCI12345"
}'
```

**Response (201):**
```json
{
  "success": true,
  "message": "Doctor created successfully",
  "data": {
    "id": 15,
    "first_name": "John",
    "last_name": "Doe",
    ...
  }
}
```

---

### 3.3 Get Doctor by ID
**GET** `/doctors/{doctor_id}`

Get detailed information about a specific doctor.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/doctors/7' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

**Response (200):**
```json
{
  "success": true,
  "message": "Doctor retrieved successfully",
  "data": {...}
}
```

---

### 3.4 Update Doctor
**PUT** `/doctors/{doctor_id}`

Update an existing doctor's information.

**Request Body:**
```json
{
  "first_name": "Updated Name"
}
```

**cURL:**
```
curl --location --request PUT 'http://127.0.0.1:8000/api/v1/doctors/7' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"first_name": "Updated Name"}'
```

**Response (200):**
```json
{
  "success": true,
  "message": "Doctor updated successfully",
  "data": {...}
}
```

---

### 3.5 Delete Doctor
**DELETE** `/doctors/{doctor_id}`

Soft delete a doctor.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/doctors/7' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

**Response (204):** No content

---

### 3.6 Get Doctor by Email
**GET** `/doctors/email/{email}`

Look up a doctor by email address.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/doctors/email/test@example.com' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

**Response (200):**
```json
{
  "success": true,
  "message": "Doctor retrieved successfully",
  "data": {...}
}
```

---

### 3.7 Get Doctor by Phone
**GET** `/doctors/phone/{phone_number}`

Look up a doctor by phone number.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/doctors/phone/9443453525' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

**Response (200):**
```json
{
  "success": true,
  "message": "Doctor retrieved successfully",
  "data": {...}
}
```

---

### 3.8 Hard Delete Doctor (Erase)
**DELETE** `/doctors/{doctor_id}/erase`

Permanently delete doctor and all related records.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/doctors/7/erase' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

**Response (204):** No content

---

### 3.9 Erase All Records (Dev Only)
**DELETE** `/doctors/erase-all`

⚠️ DANGEROUS: Delete all records from all tables. Only available in development.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/doctors/erase-all' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

**Response (204):** No content

---

## 4. HOSPITALS

### 4.1 List Hospitals
**GET** `/hospitals`

Get list of hospitals with optional filters.

**Query Parameters:**
- `skip` (int): Skip N records (default: 0)
- `limit` (int): Max records (default: 50, max: 100)
- `verification_status` (string): Filter by status
- `city` (string): Filter by city
- `state` (string): Filter by state
- `include_inactive` (bool): Include inactive hospitals

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals?limit=50' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 4.2 Create Hospital
**POST** `/hospitals`

Add a new hospital.

**Request Body:**
```json
{
  "name": "City Hospital",
  "city": "Mumbai",
  "address": "123 Main St",
  "state": "Maharashtra",
  "pincode": "400001"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
  "name": "City Hospital",
  "city": "Mumbai",
  "address": "123 Main St",
  "state": "Maharashtra",
  "pincode": "400001"
}'
```

**Response (201):**
```json
{
  "success": true,
  "message": "Hospital created successfully",
  "data": {...}
}
```

---

### 4.3 Get Hospital by ID
**GET** `/hospitals/{hospital_id}`

Get hospital details.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals/1' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 4.4 Update Hospital
**PATCH** `/hospitals/{hospital_id}`

Update hospital details.

**Request Body:**
```json
{
  "name": "Updated Hospital Name"
}
```

**cURL:**
```
curl --location --request PATCH 'http://127.0.0.1:8000/api/v1/hospitals/1' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"name": "Updated Hospital Name"}'
```

---

### 4.5 Delete Hospital
**DELETE** `/hospitals/{hospital_id}`

Soft delete a hospital.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/hospitals/1' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 4.6 Search Hospitals
**GET** `/hospitals/search`

Search hospitals for autocomplete.

**Query Parameters:**
- `q` (string, required): Search query
- `city` (string): Filter by city
- `state` (string): Filter by state
- `limit` (int): Max results (default: 20)

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals/search?q=City' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 4.7 Verify Hospital (Admin)
**POST** `/hospitals/{hospital_id}/verify`

Verify or reject a hospital.

**Request Body:**
```json
{
  "action": "verify",
  "verified_by": "admin@example.com"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals/1/verify' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"action": "verify", "verified_by": "admin@example.com"}'
```

---

### 4.8 List Pending Hospitals (Admin)
**GET** `/hospitals/admin/pending`

List hospitals pending verification.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals/admin/pending' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 4.9 Get Hospital Stats (Admin)
**GET** `/hospitals/admin/stats`

Get hospital statistics.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals/admin/stats' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 4.10 Merge Hospitals (Admin)
**POST** `/hospitals/admin/merge`

Merge duplicate hospitals.

**Request Body:**
```json
{
  "source_hospital_ids": [2, 3],
  "target_hospital_id": 1
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals/admin/merge' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"source_hospital_ids": [2, 3], "target_hospital_id": 1}'
```

---

## 5. HOSPITAL AFFILIATIONS

### 5.1 Create Affiliation
**POST** `/hospitals/affiliations`

Create doctor-hospital affiliation.

**Query Parameters:**
- `doctor_id` (int, required): Doctor ID

**Request Body:**
```json
{
  "hospital_id": 1,
  "designation": "Senior Consultant",
  "department": "Cardiology",
  "is_primary": true
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals/affiliations?doctor_id=7' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"hospital_id": 1, "designation": "Senior Consultant", "is_primary": true}'
```

---

### 5.2 Create Affiliation with New Hospital
**POST** `/hospitals/affiliations/with-new-hospital`

Create a new hospital and affiliate doctor.

**Query Parameters:**
- `doctor_id` (int, required): Doctor ID

**Request Body:**
```json
{
  "hospital_name": "New Hospital",
  "hospital_city": "Delhi",
  "hospital_address": "456 Test St",
  "hospital_state": "Delhi",
  "hospital_pincode": "110001",
  "designation": "Consultant"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals/affiliations/with-new-hospital?doctor_id=7' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
  "hospital_name": "New Hospital",
  "hospital_city": "Delhi",
  "hospital_address": "456 Test St",
  "hospital_state": "Delhi",
  "hospital_pincode": "110001"
}'
```

---

### 5.3 Get Doctor Affiliations
**GET** `/hospitals/affiliations/doctor/{doctor_id}`

Get all hospital affiliations for a doctor.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals/affiliations/doctor/7' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 5.4 Get Hospital Doctors
**GET** `/hospitals/affiliations/hospital/{hospital_id}`

Get all doctors affiliated with a hospital.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/hospitals/affiliations/hospital/1' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 5.5 Update Affiliation
**PATCH** `/hospitals/affiliations/{affiliation_id}`

Update affiliation details.

**Request Body:**
```json
{
  "is_primary": true
}
```

**cURL:**
```
curl --location --request PATCH 'http://127.0.0.1:8000/api/v1/hospitals/affiliations/AFFILIATION_ID' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"is_primary": true}'
```

---

### 5.6 Delete Affiliation
**DELETE** `/hospitals/affiliations/{affiliation_id}`

Remove a doctor-hospital affiliation.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/hospitals/affiliations/AFFILIATION_ID' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

## 6. ONBOARDING

### 6.1 Create Profile
**POST** `/onboarding/createprofile`

Create a new onboarding profile.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone_number": "9876543210"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/createprofile' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone_number": "9876543210"
}'
```

**Response (201):**
```json
{
  "success": true,
  "message": "Profile created successfully",
  "data": {
    "doctor_id": 15
  }
}
```

---

### 6.2 Save Profile
**POST** `/onboarding/saveprofile/{doctor_id}`

Update profile identity and details.

**Request Body:**
```json
{
  "full_name": "Dr. John Doe",
  "specialty": "Cardiology",
  "bio": "Experienced cardiologist...",
  "years_of_clinical_experience": 15
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/saveprofile/7' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"bio": "Updated bio content"}'
```

---

### 6.3 Submit Profile
**POST** `/onboarding/submit/{doctor_id}`

Submit profile for verification.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/submit/7' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{}'
```

---

### 6.4 Delete Profile
**POST** `/onboarding/delete/{doctor_id}`

Soft delete a profile.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/delete/7' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 6.5 Extract Resume
**POST** `/onboarding/extract-resume`

Upload resume and extract structured data using AI.

**Form Data:**
- `file`: Resume file (PDF, PNG, JPG, JPEG)

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/extract-resume' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--form 'file=@"/path/to/resume.pdf"'
```

---

### 6.6 Generate Profile Content
**POST** `/onboarding/generate-profile-content`

Generate professional overview using AI.

**Request Body:**
```json
{
  "doctor_identifier": "7",
  "personal_details": {
    "first_name": "John",
    "last_name": "Doe"
  },
  "professional_information": {
    "primary_specialization": "Cardiology"
  }
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/generate-profile-content' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"doctor_identifier": "7"}'
```

---

### 6.7 Get Profile Session Stats
**GET** `/onboarding/profile-session/{doctor_identifier}`

Get profile generation session statistics.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/profile-session/7' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 6.8 Clear Profile Session
**DELETE** `/onboarding/profile-session/{doctor_identifier}`

Reset variant tracking for a doctor.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/onboarding/profile-session/7' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 6.9 List Profile Variants
**GET** `/onboarding/profile-variants`

Get available prompt variants for profile generation.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/profile-variants' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 6.10 Upload Files
**POST** `/onboarding/uploads/{doctor_id}`

Register uploaded files for a profile.

**Request Body:**
```json
{
  "uploads": [
    {
      "field_name": "profile_photo",
      "file_name": "photo.jpg",
      "file": "https://example.com/photo.jpg"
    }
  ]
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/uploads/7' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
  "uploads": [
    {"field_name": "profile_photo", "file_name": "photo.jpg", "file": "https://example.com/photo.jpg"}
  ]
}'
```

---

### 6.11 Validate Data
**POST** `/onboarding/validate-data`

Validate extracted data before submission.

**Request Body:** (ResumeExtractedData schema)

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/validate-data' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"personal_details": {"first_name": "John"}}'
```

---

### 6.12 Sync to LinQMD
**POST** `/onboarding/sync-to-linqmd/{doctor_id}`

Sync doctor profile to LinQMD platform.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/sync-to-linqmd/7' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 6.13 Bulk Sync to LinQMD
**POST** `/onboarding/sync-to-linqmd-bulk`

Sync multiple doctors to LinQMD.

**Request Body:**
```json
{
  "doctor_ids": [7, 8, 9]
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/sync-to-linqmd-bulk' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"doctor_ids": [7, 8, 9]}'
```

---

### 6.14 Get LinQMD Sync Status
**GET** `/onboarding/linqmd-sync-status`

Check LinQMD sync configuration status.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding/linqmd-sync-status' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

## 7. ONBOARDING ADMIN

### 7.1 List Doctors with Full Info
**GET** `/onboarding-admin/doctors/full`

Get all doctors with complete onboarding data.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/doctors/full' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 7.2 List Doctors with Filter
**GET** `/onboarding-admin/doctors`

List doctors with optional status filter and pagination.

**Query Parameters:**
- `status` (string): Filter by status (PENDING, SUBMITTED, VERIFIED, REJECTED)
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20)

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/doctors?status=pending&page=1' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 7.3 Get Doctor Full Info by ID
**GET** `/onboarding-admin/doctors/{doctor_id}/full`

Get complete onboarding data for a doctor.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/doctors/7/full' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 7.4 Get Doctor by Email
**POST** `/onboarding-admin/doctors/by-email/full`

Get doctor by email address.

**Request Body:**
```json
{
  "email": "john.doe@example.com"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/doctors/by-email/full' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"email": "john.doe@example.com"}'
```

---

### 7.5 Get Doctor by Phone
**POST** `/onboarding-admin/doctors/by-phone/full`

Get doctor by phone number.

**Request Body:**
```json
{
  "phone_number": "9443453525"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/doctors/by-phone/full' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"phone_number": "9443453525"}'
```

---

### 7.6 Create Identity
**POST** `/onboarding-admin/identities`

Create a new doctor identity.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone_number": "9876543210"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/identities' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"first_name": "John", "last_name": "Doe", "email": "john@example.com", "phone_number": "9876543210"}'
```

---

### 7.7 Get Identity by Doctor ID
**GET** `/onboarding-admin/identities/{doctor_id}`

Get identity by doctor ID.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/identities/7' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 7.8 Get Identity by Email
**GET** `/onboarding-admin/identities/by-email`

Get identity by email.

**Query Parameters:**
- `email` (string): Email address

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/identities/by-email?email=john@example.com' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 7.9 Upsert Details
**PUT** `/onboarding-admin/details/{doctor_id}`

Create or update doctor details.

**Request Body:**
```json
{
  "bio": "Updated bio",
  "speciality": "Cardiology"
}
```

**cURL:**
```
curl --location --request PUT 'http://127.0.0.1:8000/api/v1/onboarding-admin/details/7' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"bio": "Updated bio"}'
```

---

### 7.10 Get Details
**GET** `/onboarding-admin/details/{doctor_id}`

Get doctor details.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/details/7' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 7.11 Add Media
**POST** `/onboarding-admin/media/{doctor_id}`

Add media record for a doctor.

**Request Body:**
```json
{
  "media_type": "image",
  "media_category": "profile_photo",
  "file_uri": "https://example.com/photo.jpg"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/media/7' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"media_type": "image", "media_category": "profile_photo", "file_uri": "https://example.com/photo.jpg"}'
```

---

### 7.12 List Media
**GET** `/onboarding-admin/media/{doctor_id}`

Get all media for a doctor.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/media/7' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 7.13 Upload Media File
**POST** `/onboarding-admin/media/{doctor_id}/upload`

Upload file directly for a doctor.

**Query Parameters:**
- `media_category` (string, required): Media category

**Form Data:**
- `file`: File to upload

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/media/7/upload?media_category=profile_photo' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--form 'file=@"/path/to/image.jpg"'
```

---

### 7.14 Delete Media
**DELETE** `/onboarding-admin/media/{media_id}`

Delete a media record.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/onboarding-admin/media/MEDIA_ID' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 7.15 Get Status History
**GET** `/onboarding-admin/status-history/{doctor_id}`

Get status change history for a doctor.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/status-history/7' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 7.16 Log Status Change
**POST** `/onboarding-admin/status-history/{doctor_id}`

Log a status change.

**Request Body:**
```json
{
  "status": "APPROVED",
  "notes": "Profile approved after review"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/onboarding-admin/status-history/7' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"status": "APPROVED", "notes": "Profile approved"}'
```

---

## 8. DROPDOWN DATA

### 8.1 Get All Dropdown Data
**GET** `/dropdown-data/all`

Get all dropdown values in a single request.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/dropdown-data/all' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 8.2 Get Specialisations
**GET** `/dropdown-data/specialisations`

Get unique specialisation values.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/dropdown-data/specialisations' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 8.3 Get Sub-Specialisations
**GET** `/dropdown-data/sub-specialisations`

Get unique sub-specialisation values.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/dropdown-data/sub-specialisations' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 8.4 Get Degrees
**GET** `/dropdown-data/degrees`

Get unique degree values.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/dropdown-data/degrees' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 8.5 Add Dropdown Values
**POST** `/dropdown-data/values`

Add new values to a dropdown field.

**Request Body:**
```json
{
  "field_name": "specialisations",
  "values": ["New Specialty 1", "New Specialty 2"]
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/dropdown-data/values' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"field_name": "specialisations", "values": ["New Specialty"]}'
```

---

## 9. ADMIN DROPDOWN OPTIONS

### 9.1 List Dropdown Fields
**GET** `/admin/dropdown-options/fields`

Get configuration for all dropdown fields.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/dropdown-options/fields' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 9.2 Get Field Options
**GET** `/admin/dropdown-options/fields/{field_name}`

Get all options for a specific field.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/dropdown-options/fields/specialty' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 9.3 Add Option to Field
**POST** `/admin/dropdown-options/fields/{field_name}`

Add a new option to a dropdown field.

**Request Body:**
```json
{
  "value": "New Option",
  "display_label": "New Option Label"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/dropdown-options/fields/specialty' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"value": "New Option"}'
```

---

### 9.4 Bulk Add Options
**POST** `/admin/dropdown-options/fields/{field_name}/bulk`

Add multiple options at once.

**Request Body:**
```json
{
  "values": ["Option 1", "Option 2", "Option 3"]
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/dropdown-options/fields/specialty/bulk' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"values": ["Option 1", "Option 2"]}'
```

---

### 9.5 Update Option
**PUT** `/admin/dropdown-options/options/{option_id}`

Update an existing option.

**Request Body:**
```json
{
  "value": "Updated Value",
  "display_label": "Updated Label"
}
```

**cURL:**
```
curl --location --request PUT 'http://127.0.0.1:8000/api/v1/admin/dropdown-options/options/OPTION_ID' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"value": "Updated Value"}'
```

---

### 9.6 Delete Option
**DELETE** `/admin/dropdown-options/options/{option_id}`

Deactivate (soft delete) an option.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/admin/dropdown-options/options/OPTION_ID' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 9.7 Verify Option
**POST** `/admin/dropdown-options/options/{option_id}/verify`

Mark a doctor-contributed option as verified.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/dropdown-options/options/OPTION_ID/verify' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 9.8 List Unverified Options
**GET** `/admin/dropdown-options/unverified`

Get all options pending verification.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/dropdown-options/unverified' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 9.9 Get All Dropdown Data
**GET** `/admin/dropdown-options/data`

Get all dropdown data for frontend forms.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/dropdown-options/data' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 9.10 Get Statistics
**GET** `/admin/dropdown-options/stats`

Get dropdown options statistics.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/dropdown-options/stats' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 9.11 Seed Initial Values
**POST** `/admin/dropdown-options/seed`

Seed the database with initial dropdown values.

**Query Parameters:**
- `force` (bool): Force re-seed even if data exists

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/dropdown-options/seed' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

## 10. ADMIN USERS

### 10.1 List Users
**GET** `/admin/users`

Get paginated list of users.

**Query Parameters:**
- `skip` (int): Skip records (default: 0)
- `limit` (int): Max records (default: 50)
- `role` (string): Filter by role
- `is_active` (bool): Filter by status

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/users' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 10.2 List Admins
**GET** `/admin/users/admins`

Get all admin users.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/users/admins' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 10.3 Get User by ID
**GET** `/admin/users/{user_id}`

Get details of a specific user.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/users/1' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 10.4 Create User
**POST** `/admin/users`

Create a new user.

**Request Body:**
```json
{
  "phone": "9876543210",
  "email": "newuser@example.com",
  "role": "user",
  "is_active": true
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/admin/users' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"phone": "9876543210", "email": "newuser@example.com", "role": "user"}'
```

---

### 10.5 Update User
**PATCH** `/admin/users/{user_id}`

Update user details.

**Request Body:**
```json
{
  "email": "updated@example.com"
}
```

**cURL:**
```
curl --location --request PATCH 'http://127.0.0.1:8000/api/v1/admin/users/1' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"email": "updated@example.com"}'
```

---

### 10.6 Update User Role
**PATCH** `/admin/users/{user_id}/role`

Change a user's role.

**Request Body:**
```json
{
  "role": "admin"
}
```

**cURL:**
```
curl --location --request PATCH 'http://127.0.0.1:8000/api/v1/admin/users/1/role' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"role": "admin"}'
```

---

### 10.7 Update User Status
**PATCH** `/admin/users/{user_id}/status`

Activate or deactivate a user.

**Request Body:**
```json
{
  "is_active": true
}
```

**cURL:**
```
curl --location --request PATCH 'http://127.0.0.1:8000/api/v1/admin/users/1/status' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"is_active": true}'
```

---

### 10.8 Delete User
**DELETE** `/admin/users/{user_id}`

Deactivate a user (soft delete).

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/admin/users/1' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

## 11. TESTIMONIALS

### 11.1 List Active Testimonials (Public)
**GET** `/testimonials`

Get active testimonials for homepage.

**Query Parameters:**
- `skip` (int): Skip records (default: 0)
- `limit` (int): Max records (default: 20)

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/testimonials'
```

---

### 11.2 List All Testimonials (Admin)
**GET** `/testimonials/admin`

Get all testimonials including inactive.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/testimonials/admin' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 11.3 Get Testimonial by ID
**GET** `/testimonials/{testimonial_id}`

Get a single testimonial.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/testimonials/TESTIMONIAL_ID'
```

---

### 11.4 Create Testimonial
**POST** `/testimonials`

Create a new testimonial.

**Request Body:**
```json
{
  "doctor_name": "Dr. John Doe",
  "specialty": "Cardiology",
  "comment": "Great platform for doctors!",
  "rating": 5
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/testimonials' \
--header 'Content-Type: application/json' \
--data '{
  "doctor_name": "Dr. John Doe",
  "specialty": "Cardiology",
  "comment": "Great platform!",
  "rating": 5
}'
```

---

### 11.5 Update Testimonial
**PATCH** `/testimonials/{testimonial_id}`

Update a testimonial.

**Request Body:**
```json
{
  "rating": 4
}
```

**cURL:**
```
curl --location --request PATCH 'http://127.0.0.1:8000/api/v1/testimonials/TESTIMONIAL_ID' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"rating": 4}'
```

---

### 11.6 Delete Testimonial
**DELETE** `/testimonials/{testimonial_id}`

Delete a testimonial.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/testimonials/TESTIMONIAL_ID' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 11.7 Toggle Active Status
**POST** `/testimonials/{testimonial_id}/toggle-active`

Toggle testimonial active/inactive status.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/testimonials/TESTIMONIAL_ID/toggle-active' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

## 12. BLOB STORAGE

### 12.1 Get Blob File
**GET** `/blobs/{doctor_id}/{media_category}/{blob_filename}`

Stream a blob file from storage.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/blobs/7/profile_photo/photo.jpg' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 12.2 Check Blob Exists
**HEAD** `/blobs/{doctor_id}/{media_category}/{blob_filename}`

Check if blob exists without downloading.

**cURL:**
```
curl --location --head 'http://127.0.0.1:8000/api/v1/blobs/7/profile_photo/photo.jpg' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 12.3 Get Storage Stats
**GET** `/blobs/stats`

Get blob storage statistics.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/blobs/stats' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

## 13. VOICE ONBOARDING

### 13.1 Start Voice Session
**POST** `/voice/start`

Start a new voice onboarding session.

**Request Body:**
```json
{
  "language": "en"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/voice/start' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"language": "en"}'
```

**Response (201):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "greeting": "Hello! I'm here to help you complete your registration...",
  "fields_total": 8,
  "created_at": "2026-01-11T09:30:00Z"
}
```

---

### 13.2 Voice Chat
**POST** `/voice/chat`

Send a message in the voice conversation.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_transcript": "My name is Dr. Sarah Johnson"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/voice/chat' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
  "session_id": "SESSION_ID",
  "user_transcript": "My name is Dr. Sarah Johnson"
}'
```

---

### 13.3 Get Session Status
**GET** `/voice/session/{session_id}`

Get current status of a voice session.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/voice/session/SESSION_ID' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 13.4 Finalize Session
**POST** `/voice/session/{session_id}/finalize`

Finalize a completed session and get doctor data.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/voice/session/SESSION_ID/finalize' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 13.5 Cancel Session
**DELETE** `/voice/session/{session_id}`

Cancel and delete a voice session.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/voice/session/SESSION_ID' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

## 14. VOICE CONFIG

### 14.1 Get Voice Configuration
**GET** `/voice-config`

Get full voice onboarding configuration.

**Query Parameters:**
- `active_only` (bool): Only return active blocks/fields (default: true)

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/voice-config' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 14.2 Get Field Config
**GET** `/voice-config/field-config`

Get field configuration dictionary for voice service.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/voice-config/field-config' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 14.3 Get Block
**GET** `/voice-config/blocks/{block_number}`

Get a specific block by number.

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/voice-config/blocks/1' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 14.4 Create Block
**POST** `/voice-config/blocks`

Create a new voice onboarding block.

**Request Body:**
```json
{
  "block_number": 1,
  "block_name": "identity",
  "display_name": "Professional Identity",
  "ai_prompt": "Let's start with your basic information...",
  "completion_percentage": 20
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/voice-config/blocks' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
  "block_number": 1,
  "block_name": "identity",
  "display_name": "Professional Identity"
}'
```

---

### 14.5 Update Block
**PATCH** `/voice-config/blocks/{block_id}`

Update a voice onboarding block.

**Request Body:**
```json
{
  "display_name": "Updated Name"
}
```

**cURL:**
```
curl --location --request PATCH 'http://127.0.0.1:8000/api/v1/voice-config/blocks/BLOCK_ID' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"display_name": "Updated Name"}'
```

---

### 14.6 Delete Block
**DELETE** `/voice-config/blocks/{block_id}`

Delete a voice onboarding block.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/voice-config/blocks/BLOCK_ID' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

### 14.7 Create Field
**POST** `/voice-config/fields`

Create a new voice onboarding field.

**Request Body:**
```json
{
  "block_id": 1,
  "field_name": "full_name",
  "display_name": "Full Name",
  "field_type": "text",
  "is_required": true,
  "ai_question": "What is your full name?"
}
```

**cURL:**
```
curl --location 'http://127.0.0.1:8000/api/v1/voice-config/fields' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{
  "block_id": 1,
  "field_name": "full_name",
  "display_name": "Full Name",
  "field_type": "text",
  "is_required": true
}'
```

---

### 14.8 Update Field
**PATCH** `/voice-config/fields/{field_id}`

Update a voice onboarding field.

**Request Body:**
```json
{
  "is_required": false
}
```

**cURL:**
```
curl --location --request PATCH 'http://127.0.0.1:8000/api/v1/voice-config/fields/FIELD_ID' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"is_required": false}'
```

---

### 14.9 Delete Field
**DELETE** `/voice-config/fields/{field_id}`

Delete a voice onboarding field.

**cURL:**
```
curl --location --request DELETE 'http://127.0.0.1:8000/api/v1/voice-config/fields/FIELD_ID' \
--header 'Authorization: Bearer YOUR_TOKEN'
```

---

## Quick Start Guide

### 1. Get Authentication Token

First, request an OTP:
```
curl --location 'http://127.0.0.1:8000/api/v1/auth/otp/request' \
--header 'Content-Type: application/json' \
--data '{"mobile_number": "YOUR_PHONE_NUMBER"}'
```

Then verify the OTP to get your token:
```
curl --location 'http://127.0.0.1:8000/api/v1/auth/otp/verify' \
--header 'Content-Type: application/json' \
--data '{"mobile_number": "YOUR_PHONE_NUMBER", "otp": "RECEIVED_OTP"}'
```

**Or use the dev endpoint (accepts any OTP):**
```
curl --location 'http://127.0.0.1:8000/api/v1/validateandlogin' \
--header 'Content-Type: application/json' \
--data '{"phone_number": "YOUR_PHONE_NUMBER", "otp": "123456"}'
```

### 2. Use Token in Requests

Add the token to all authenticated requests:
```
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

### 3. Token Expiry

Tokens expire after 30 minutes (1800 seconds). Request a new token when expired.

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid/expired token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 410 | Gone - Session expired |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## Total: 109 Endpoints

| Category | Count |
|----------|-------|
| Authentication | 4 |
| Health | 3 |
| Doctors | 9 |
| Hospitals | 11 |
| Affiliations | 6 |
| Onboarding | 14 |
| Onboarding Admin | 16 |
| Dropdown Data | 5 |
| Admin Dropdown | 11 |
| Admin Users | 8 |
| Testimonials | 7 |
| Blob Storage | 3 |
| Voice | 5 |
| Voice Config | 7 |
| **Total** | **109** |

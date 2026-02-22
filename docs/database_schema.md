# Database Schema Documentation

**Project:** Doctor Onboarding Smart-Fill API  
**Database:** PostgreSQL (Production) / SQLite (Development)  
**ORM:** SQLAlchemy 2.0 (Async)  
**Last Updated:** 2026-02-22  

---

## Overview

This document provides a comprehensive reference for all database tables, columns, data types, and relationships in the Doctor Onboarding system. The schema supports three modes of doctor onboarding: resume upload, voice assistant, and manual CRUD operations.

---

## Table of Contents

1. [Doctor Onboarding Tables](#doctor-onboarding-tables)
   - [doctor_identity](#1-doctor_identity)
   - [doctor_details](#2-doctor_details)
   - [doctor_media](#3-doctor_media)
   - [doctor_status_history](#4-doctor_status_history)
   - [dropdown_options](#5-dropdown_options)
2. [Hospital Management Tables](#hospital-management-tables)
   - [hospitals](#6-hospitals)
   - [doctor_hospital_affiliations](#7-doctor_hospital_affiliations)
3. [RBAC & Authentication Tables](#rbac--authentication-tables)
   - [users](#8-users)
4. [Content & Configuration Tables](#content--configuration-tables)
   - [testimonials](#9-testimonials)
5. [Voice Onboarding Configuration Tables](#voice-onboarding-configuration-tables)
   - [voice_onboarding_blocks](#10-voice_onboarding_blocks)
   - [voice_onboarding_fields](#11-voice_onboarding_fields)
6. [Legacy Tables](#legacy-tables)
   - [doctors](#12-doctors)
7. [Enumerations](#enumerations)
8. [Relationships](#relationships)
9. [Indexes](#indexes)

---

## Doctor Onboarding Tables

### 1. `doctor_identity`

**Purpose:** Core doctor identification and contact information table.

**Description:** Stores basic doctor identity, contact details, and onboarding status. Acts as the primary entity for doctor records.

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID v4 | Unique identifier |
| `doctor_id` | `BIGINT` | UNIQUE, NOT NULL, AUTO INCREMENT | Auto | Numeric doctor ID for references |
| `title` | `ENUM` | NULLABLE | NULL | Doctor title: 'dr', 'prof', 'prof.dr' |
| `first_name` | `VARCHAR(100)` | NOT NULL | - | Doctor's first name |
| `last_name` | `VARCHAR(100)` | NOT NULL | - | Doctor's last name |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL | - | Email address (unique constraint) |
| `phone_number` | `VARCHAR(20)` | NOT NULL | - | Contact phone number |
| `onboarding_status` | `ENUM` | NOT NULL | 'pending' | Status: 'pending', 'submitted', 'verified', 'rejected' |
| `status_updated_at` | `TIMESTAMP WITH TZ` | NULLABLE | NULL | When status was last changed |
| `status_updated_by` | `VARCHAR(36)` | NULLABLE | NULL | Who updated the status |
| `rejection_reason` | `TEXT` | NULLABLE | NULL | Reason for rejection (if rejected) |
| `verified_at` | `TIMESTAMP WITH TZ` | NULLABLE | NULL | When verification was completed |
| `is_active` | `BOOLEAN` | NOT NULL | TRUE | Soft delete flag |
| `registered_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Initial registration timestamp |
| `created_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record creation timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record update timestamp |
| `deleted_at` | `TIMESTAMP WITH TZ` | NULLABLE | NULL | Soft delete timestamp |

**Indexes:**
- Primary Key: `id`
- Unique: `doctor_id`, `email`
- Index: `doctor_id`, `email`

**Relationships:**
- ONE-TO-ONE with `doctor_details` (via doctor_id)
- ONE-TO-MANY with `doctor_media` (media records)
- ONE-TO-MANY with `doctor_status_history` (audit trail)

---

### 2. `doctor_details`

**Purpose:** Comprehensive professional information and credentials.

**Description:** Stores detailed professional data organized into 6 blocks matching the voice onboarding questionnaire, plus legacy fields for backward compatibility. All JSON fields default to empty arrays/objects.

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `detail_id` | `VARCHAR(36)` | PRIMARY KEY | UUID v4 | Unique identifier |
| `doctor_id` | `BIGINT` | FK, UNIQUE, NOT NULL | - | References doctor_identity.doctor_id |
| **Block 1: Professional Identity** |||||
| `full_name` | `VARCHAR(200)` | NULLABLE | NULL | Doctor's full name |
| `specialty` | `VARCHAR(100)` | NULLABLE | NULL | Primary specialty (new field) |
| `primary_practice_location` | `VARCHAR(100)` | NULLABLE | NULL | Primary city/location |
| `centres_of_practice` | `JSON` | NOT NULL | [] | Array of practice centre names |
| `years_of_clinical_experience` | `INTEGER` | NULLABLE | NULL | Total clinical experience years |
| `years_post_specialisation` | `INTEGER` | NULLABLE | NULL | Years since specialisation |
| **Block 2: Credentials & Trust Markers** |||||
| `year_of_mbbs` | `INTEGER` | NULLABLE | NULL | Year of MBBS completion |
| `year_of_specialisation` | `INTEGER` | NULLABLE | NULL | Year of specialisation completion |
| `fellowships` | `JSON` | NOT NULL | [] | Array of fellowship details |
| `qualifications` | `JSON` | NOT NULL | [] | Array of qualifications |
| `professional_memberships` | `JSON` | NOT NULL | [] | Array of professional body memberships |
| `awards_academic_honours` | `JSON` | NOT NULL | [] | Array of awards and honours |
| **Block 3: Clinical Focus & Expertise** |||||
| `areas_of_clinical_interest` | `JSON` | NOT NULL | [] | Array of clinical interest areas |
| `practice_segments` | `VARCHAR(50)` | NULLABLE | NULL | Practice segment type |
| `conditions_commonly_treated` | `JSON` | NOT NULL | [] | Array of commonly treated conditions |
| `conditions_known_for` | `JSON` | NOT NULL | [] | Array of conditions known for |
| `conditions_want_to_treat_more` | `JSON` | NOT NULL | [] | Array of conditions to treat more |
| **Block 4: The Human Side** |||||
| `training_experience` | `JSON` | NOT NULL | [] | Array of training experiences |
| `motivation_in_practice` | `JSON` | NOT NULL | [] | Array of practice motivations |
| `unwinding_after_work` | `JSON` | NOT NULL | [] | Array of unwinding activities |
| `recognition_identity` | `JSON` | NOT NULL | [] | Array of recognition/identity items |
| `quality_time_interests` | `JSON` | NOT NULL | [] | Array of quality time interests |
| `quality_time_interests_text` | `TEXT` | NULLABLE | NULL | Free-text quality time description |
| `professional_achievement` | `TEXT` | NULLABLE | NULL | Key professional achievement |
| `personal_achievement` | `TEXT` | NULLABLE | NULL | Key personal achievement |
| `professional_aspiration` | `TEXT` | NULLABLE | NULL | Professional aspiration |
| `personal_aspiration` | `TEXT` | NULLABLE | NULL | Personal aspiration |
| **Block 5: Patient Value & Choice Factors** |||||
| `what_patients_value_most` | `TEXT` | NULLABLE | NULL | What patients value most |
| `approach_to_care` | `TEXT` | NULLABLE | NULL | Approach to patient care |
| `availability_philosophy` | `TEXT` | NULLABLE | NULL | Availability philosophy |
| **Block 6: Content Seed** |||||
| `content_seeds` | `JSON` | NOT NULL | [] | Array of content seed objects |
| **Legacy/Compatibility Fields** |||||
| `gender` | `VARCHAR(20)` | NULLABLE | NULL | Gender identification |
| `speciality` | `VARCHAR(100)` | NULLABLE | NULL | Primary medical specialization (legacy) |
| `sub_specialities` | `JSON` | NOT NULL | [] | Array of sub-specializations |
| `areas_of_expertise` | `JSON` | NOT NULL | [] | Array of expertise areas |
| `registration_number` | `VARCHAR(100)` | UNIQUE, NULLABLE | NULL | Medical registration number |
| `registration_year` | `INTEGER` | NULLABLE | NULL | Year of medical registration |
| `registration_authority` | `VARCHAR(100)` | NULLABLE | NULL | Issuing authority |
| `consultation_fee` | `FLOAT` | NULLABLE | NULL | Default consultation fee |
| `years_of_experience` | `INTEGER` | NULLABLE | NULL | Total years practicing |
| `conditions_treated` | `JSON` | NOT NULL | [] | Array of conditions treated |
| `procedures_performed` | `JSON` | NOT NULL | [] | Array of procedures performed |
| `age_groups_treated` | `JSON` | NOT NULL | [] | Array of age groups treated |
| `languages_spoken` | `JSON` | NOT NULL | [] | Array of languages |
| `achievements` | `JSON` | NOT NULL | [] | Array of awards and recognitions |
| `publications` | `JSON` | NOT NULL | [] | Array of research publications |
| `practice_locations` | `JSON` | NOT NULL | [] | Array of practice locations (legacy) |
| `external_links` | `JSON` | NOT NULL | {} | Object with social links |
| `professional_overview` | `TEXT` | NULLABLE | NULL | Professional summary/bio |
| `about_me` | `TEXT` | NULLABLE | NULL | Personal introduction |
| `professional_tagline` | `TEXT` | NULLABLE | NULL | Short professional tagline |
| `media_urls` | `JSON` | NOT NULL | {} | Object with media URLs (legacy) |
| `profile_summary` | `TEXT` | NULLABLE | NULL | Auto-generated profile summary |
| `created_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record creation timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record update timestamp |

**Indexes:**
- Primary Key: `detail_id`
- Unique: `doctor_id`, `registration_number`
- Foreign Key: `doctor_id` → `doctor_identity.doctor_id` (CASCADE DELETE)

**Relationships:**
- ONE-TO-ONE with `doctor_identity`

---

### 3. `doctor_media`

**Purpose:** Media file references for doctor profiles.

**Description:** Stores references (URIs) and metadata for uploaded files such as profile photos, certificates, achievement images, etc. Actual files are stored in blob storage (local or S3).

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `media_id` | `VARCHAR(36)` | PRIMARY KEY | UUID v4 | Unique identifier |
| `doctor_id` | `BIGINT` | FK, NOT NULL | - | References doctor_identity.doctor_id |
| `field_name` | `VARCHAR(100)` | NULLABLE | NULL | Form field name (e.g., 'profile_photo') |
| `media_type` | `VARCHAR(50)` | NOT NULL | - | Type: 'image', 'document', 'video' |
| `media_category` | `VARCHAR(50)` | NOT NULL | - | Category: 'profile_photo', 'certificate', etc. |
| `file_uri` | `TEXT` | NOT NULL | - | Storage URI (local path or S3 URL) |
| `file_name` | `VARCHAR(255)` | NOT NULL | - | Original filename |
| `file_size` | `BIGINT` | NULLABLE | NULL | File size in bytes |
| `mime_type` | `VARCHAR(100)` | NULLABLE | NULL | MIME type (e.g., 'image/jpeg') |
| `is_primary` | `BOOLEAN` | NOT NULL | FALSE | Primary file for this category |
| `upload_date` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Upload timestamp |
| `metadata` | `JSON` | NOT NULL | {} | Additional metadata (dimensions, hash, etc.) |

**Indexes:**
- Primary Key: `media_id`
- Index: `doctor_id`
- Foreign Key: `doctor_id` → `doctor_identity.doctor_id` (CASCADE DELETE)

**Relationships:**
- MANY-TO-ONE with `doctor_identity`

---

### 4. `doctor_status_history`

**Purpose:** Audit trail for onboarding status changes.

**Description:** Tracks all status transitions for compliance and debugging.

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `history_id` | `VARCHAR(36)` | PRIMARY KEY | UUID v4 | Unique identifier |
| `doctor_id` | `BIGINT` | FK, NOT NULL | - | References doctor_identity.doctor_id |
| `previous_status` | `ENUM` | NULLABLE | NULL | Status before change |
| `new_status` | `ENUM` | NOT NULL | - | Status after change |
| `changed_by` | `VARCHAR(36)` | NULLABLE | NULL | Admin user ID who made change |
| `changed_by_email` | `VARCHAR(255)` | NULLABLE | NULL | Email of who changed |
| `rejection_reason` | `TEXT` | NULLABLE | NULL | Reason if status changed to 'rejected' |
| `notes` | `TEXT` | NULLABLE | NULL | Additional notes |
| `ip_address` | `VARCHAR(50)` | NULLABLE | NULL | IP address of requester |
| `user_agent` | `TEXT` | NULLABLE | NULL | Browser user agent |
| `changed_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | When change occurred |

**Indexes:**
- Primary Key: `history_id`
- Index: `doctor_id`
- Foreign Key: `doctor_id` → `doctor_identity.doctor_id` (CASCADE DELETE)

**Relationships:**
- MANY-TO-ONE with `doctor_identity`

---

### 5. `dropdown_options`

**Purpose:** Enhanced configurable dropdown values for onboarding forms.

**Description:** Stores custom dropdown options with categories, verification status, and creator tracking. Supersedes the original simple dropdown_options table.

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID v4 | Unique identifier |
| `field_name` | `VARCHAR(100)` | NOT NULL | - | Field identifier (e.g., 'specialty', 'fellowships') |
| `category` | `VARCHAR(50)` | NOT NULL | - | Field category (professional_identity, credentials, etc.) |
| `value` | `VARCHAR(255)` | NOT NULL | - | Option value |
| `display_label` | `VARCHAR(255)` | NULLABLE | NULL | Display text (if different from value) |
| `description` | `TEXT` | NULLABLE | NULL | Option description |
| `creator_type` | `VARCHAR(20)` | NOT NULL | 'system' | Who created: 'system', 'admin', 'doctor' |
| `created_by_doctor_id` | `INTEGER` | NULLABLE | NULL | Doctor who created (if doctor-created) |
| `is_active` | `BOOLEAN` | NOT NULL | TRUE | Active flag |
| `is_verified` | `BOOLEAN` | NOT NULL | TRUE | Verification flag |
| `display_order` | `INTEGER` | NOT NULL | 0 | Sort order |
| `created_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record creation timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | NULLABLE | NULL | Record update timestamp |

**Indexes:**
- Primary Key: `id`
- Unique: `(field_name, value)`
- Index: `field_name`, `category`, `(field_name, is_active)`

**Supported Fields:**
- `specialty` – Medical specializations
- `primary_practice_location` – Cities/locations
- `qualifications` – Degrees (MBBS, MD, etc.)
- `fellowships` – Fellowship programs
- `professional_memberships` – Professional associations
- `languages_spoken` – Languages
- `age_groups_treated` – Patient demographics
- `practice_segments` – Practice types
- `training_experience` – Training highlights
- `motivation_in_practice` – Practice motivations
- `unwinding_after_work` – Personal interests
- `quality_time_interests` – Quality time activities

---

## Hospital Management Tables

### 6. `hospitals`

**Purpose:** Master table for hospitals and clinics.

**Description:** Centralized repository of healthcare facilities. Doctors select from this list during onboarding. Supports verification workflow for doctor-added hospitals.

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `id` | `INTEGER` | PRIMARY KEY, AUTO INCREMENT | Auto | Unique identifier |
| `name` | `VARCHAR(255)` | NOT NULL | - | Hospital or clinic name |
| `address` | `TEXT` | NULLABLE | NULL | Full street address |
| `city` | `VARCHAR(100)` | NULLABLE | NULL | City name |
| `state` | `VARCHAR(100)` | NULLABLE | NULL | State or province |
| `pincode` | `VARCHAR(20)` | NULLABLE | NULL | Postal/ZIP code |
| `phone_number` | `VARCHAR(20)` | NULLABLE | NULL | Hospital contact number |
| `email` | `VARCHAR(255)` | NULLABLE | NULL | Hospital email |
| `website` | `VARCHAR(500)` | NULLABLE | NULL | Hospital website URL |
| `verification_status` | `ENUM` | NOT NULL | 'pending' | Status: 'pending', 'verified', 'rejected' |
| `verified_at` | `TIMESTAMP WITH TZ` | NULLABLE | NULL | When hospital was verified |
| `verified_by` | `VARCHAR(100)` | NULLABLE | NULL | Admin who verified |
| `rejection_reason` | `TEXT` | NULLABLE | NULL | Reason for rejection |
| `created_by_doctor_id` | `BIGINT` | NULLABLE | NULL | Doctor ID who added this hospital |
| `is_active` | `BOOLEAN` | NOT NULL | TRUE | Soft delete flag |
| `created_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record creation timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record update timestamp |

**Indexes:**
- Primary Key: `id`
- Index: `name`, `city`, `state`, `verification_status`
- Composite: `(name, city)`, `(verification_status, is_active)`

**Relationships:**
- ONE-TO-MANY with `doctor_hospital_affiliations`

---

### 7. `doctor_hospital_affiliations`

**Purpose:** Links doctors to hospitals with location-specific details.

**Description:** Many-to-many relationship table storing doctor-specific information for each hospital affiliation.

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID v4 | Unique identifier |
| `doctor_id` | `BIGINT` | NOT NULL | - | References doctor_identity.doctor_id |
| `hospital_id` | `INTEGER` | FK, NOT NULL | - | References hospitals.id |
| `consultation_fee` | `FLOAT` | NULLABLE | NULL | Consultation fee at this hospital |
| `consultation_type` | `VARCHAR(100)` | NULLABLE | NULL | Type: 'In-person', 'Online', 'Both' |
| `weekly_schedule` | `TEXT` | NULLABLE | NULL | Schedule at this hospital |
| `designation` | `VARCHAR(200)` | NULLABLE | NULL | Doctor's designation at this hospital |
| `department` | `VARCHAR(200)` | NULLABLE | NULL | Department at this hospital |
| `is_primary` | `BOOLEAN` | NOT NULL | FALSE | Is this the primary practice location? |
| `is_active` | `BOOLEAN` | NOT NULL | TRUE | Soft delete flag |
| `created_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record creation timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record update timestamp |

**Indexes:**
- Primary Key: `id`
- Index: `doctor_id`, `hospital_id`
- Composite: `(doctor_id, is_primary)`
- Foreign Key: `hospital_id` → `hospitals.id` (CASCADE DELETE)

**Constraints:**
- UNIQUE: `(doctor_id, hospital_id)` – A doctor can only have one affiliation per hospital

**Relationships:**
- MANY-TO-ONE with `hospitals`
- MANY-TO-ONE with `doctor_identity` (via doctor_id)

---

## RBAC & Authentication Tables

### 8. `users`

**Purpose:** RBAC user accounts for authentication and authorization.

**Description:** Stores user accounts with role-based access control. Users can be linked to doctors for profile management.

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `id` | `SERIAL` | PRIMARY KEY | Auto | Unique identifier |
| `phone` | `VARCHAR(20)` | UNIQUE, NOT NULL | - | Phone number (+91XXXXXXXXXX) |
| `email` | `VARCHAR(255)` | UNIQUE, NULLABLE | NULL | Email address |
| `role` | `VARCHAR(20)` | NOT NULL | 'user' | Role: 'admin', 'operational', 'user' |
| `is_active` | `BOOLEAN` | NOT NULL | TRUE | Soft delete flag |
| `doctor_id` | `INTEGER` | FK, NULLABLE | NULL | Link to doctor profile |
| `created_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record creation timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | NULLABLE | NULL | Record update timestamp |
| `last_login_at` | `TIMESTAMP WITH TZ` | NULLABLE | NULL | Last login timestamp |

**Indexes:**
- Primary Key: `id`
- Unique: `phone`, `email`
- Index: `role`, `is_active`, `doctor_id`, `phone`
- Composite: `(role, is_active)`, `(phone, is_active)`
- Foreign Key: `doctor_id` → `doctors.id` (SET NULL on delete)

**Role Definitions:**
- `admin` – Full system access (all admin endpoints)
- `operational` – Limited admin access (onboarding, voice config, dropdowns)
- `user` – Regular user access (public endpoints only)

---

## Content & Configuration Tables

### 9. `testimonials`

**Purpose:** Doctor testimonials for homepage carousel.

**Description:** Stores testimonial content displayed on the public homepage.

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID v4 | Unique identifier |
| `doctor_name` | `VARCHAR(200)` | NOT NULL | - | Testimonial author name |
| `specialty` | `VARCHAR(100)` | NULLABLE | NULL | Doctor's specialty |
| `designation` | `VARCHAR(200)` | NULLABLE | NULL | Professional designation |
| `hospital_name` | `VARCHAR(200)` | NULLABLE | NULL | Hospital affiliation |
| `location` | `VARCHAR(100)` | NULLABLE | NULL | Location/city |
| `comment` | `TEXT` | NOT NULL | - | Testimonial text |
| `rating` | `INTEGER` | NULLABLE | NULL | Star rating |
| `profile_image_url` | `TEXT` | NULLABLE | NULL | Profile image URL |
| `is_active` | `BOOLEAN` | NOT NULL | TRUE | Display flag |
| `display_order` | `INTEGER` | NOT NULL | 0 | Sort order |
| `created_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record creation timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record update timestamp |

---

## Voice Onboarding Configuration Tables

### 10. `voice_onboarding_blocks`

**Purpose:** Voice questionnaire block configuration.

**Description:** Defines the 6-block structure of the voice onboarding questionnaire with AI prompts and progress tracking.

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `id` | `SERIAL` | PRIMARY KEY | Auto | Unique identifier |
| `block_number` | `INTEGER` | UNIQUE, NOT NULL | - | Block sequence number (1-6) |
| `block_name` | `VARCHAR(100)` | NOT NULL | - | Internal block name |
| `display_name` | `VARCHAR(200)` | NOT NULL | - | User-facing block title |
| `ai_prompt` | `TEXT` | NULLABLE | NULL | AI system prompt for this block |
| `ai_disclaimer` | `TEXT` | NULLABLE | NULL | Disclaimer shown before AI interaction |
| `completion_percentage` | `INTEGER` | NOT NULL | 0 | Progress % when completed |
| `completion_message` | `VARCHAR(200)` | NULLABLE | NULL | Message shown on completion |
| `is_active` | `BOOLEAN` | NOT NULL | TRUE | Active flag |
| `display_order` | `INTEGER` | NOT NULL | 0 | Display sequence |
| `created_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record creation timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record update timestamp |

**Block Structure:**
- Block 1: Professional Identity (0–17%)
- Block 2: Credentials & Trust Markers (17–33%)
- Block 3: Clinical Focus & Expertise (33–50%)
- Block 4: The Human Side (50–67%)
- Block 5: Patient Value & Choice Factors (67–83%)
- Block 6: Content Seeds (83–100%)

---

### 11. `voice_onboarding_fields`

**Purpose:** Voice questionnaire field configuration.

**Description:** Defines individual fields within each voice onboarding block, including validation rules and AI questions.

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `id` | `SERIAL` | PRIMARY KEY | Auto | Unique identifier |
| `block_id` | `INTEGER` | FK, NOT NULL | - | References voice_onboarding_blocks.id |
| `field_name` | `VARCHAR(100)` | UNIQUE, NOT NULL | - | Internal field name |
| `display_name` | `VARCHAR(200)` | NOT NULL | - | User-facing field label |
| `field_type` | `VARCHAR(50)` | NOT NULL | - | Type: text, number, select, multi_select, year, multi_entry |
| `is_required` | `BOOLEAN` | NOT NULL | FALSE | Required validation |
| `validation_regex` | `VARCHAR(500)` | NULLABLE | NULL | Regex pattern for validation |
| `min_length` | `INTEGER` | NULLABLE | NULL | Minimum text length |
| `max_length` | `INTEGER` | NULLABLE | NULL | Maximum text length |
| `min_value` | `INTEGER` | NULLABLE | NULL | Minimum numeric value |
| `max_value` | `INTEGER` | NULLABLE | NULL | Maximum numeric value |
| `max_selections` | `INTEGER` | NULLABLE | NULL | Max selections for multi_select |
| `options` | `JSON` | NULLABLE | NULL | Options for select/multi_select |
| `ai_question` | `TEXT` | NULLABLE | NULL | AI question prompt |
| `ai_followup` | `TEXT` | NULLABLE | NULL | AI follow-up prompt |
| `is_active` | `BOOLEAN` | NOT NULL | TRUE | Active flag |
| `display_order` | `INTEGER` | NOT NULL | 0 | Display sequence within block |
| `created_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record creation timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record update timestamp |

**Indexes:**
- Primary Key: `id`
- Unique: `field_name`
- Foreign Key: `block_id` → `voice_onboarding_blocks.id` (CASCADE DELETE)

---

## Legacy Tables

### 12. `doctors`

**Purpose:** Legacy main doctor entity from initial implementation.

**Description:** Original doctor table with comprehensive fields including the 6-block questionnaire data. Used alongside the onboarding tables. Linked to the `users` table via an optional reverse relationship.

| Column Name | Data Type | Constraints | Default | Description |
|------------|-----------|-------------|---------|-------------|
| `id` | `SERIAL` | PRIMARY KEY | Auto | Unique identifier |
| `title` | `VARCHAR(20)` | NULLABLE | NULL | Dr., Prof., Prof. Dr. |
| `gender` | `VARCHAR(20)` | NULLABLE | NULL | Gender |
| `first_name` | `VARCHAR(100)` | NOT NULL | - | First name |
| `last_name` | `VARCHAR(100)` | NOT NULL | - | Last name |
| `email` | `VARCHAR(100)` | UNIQUE, NOT NULL | - | Email address |
| `phone` | `VARCHAR(20)` | UNIQUE, NULLABLE | NULL | Phone number |
| `role` | `VARCHAR(20)` | NOT NULL | 'user' | Role: admin, operational, user |
| `onboarding_status` | `VARCHAR(20)` | NOT NULL | 'pending' | Status: pending, submitted, verified, rejected |
| **Block 1: Professional Identity** |||||
| `full_name` | `VARCHAR(200)` | NULLABLE | NULL | Full name |
| `specialty` | `VARCHAR(100)` | NULLABLE | NULL | Primary specialty |
| `primary_practice_location` | `VARCHAR(100)` | NULLABLE | NULL | Primary city/location |
| `centres_of_practice` | `JSON` | NOT NULL | [] | Practice centres |
| `years_of_clinical_experience` | `INTEGER` | NULLABLE | NULL | Clinical experience |
| `years_post_specialisation` | `INTEGER` | NULLABLE | NULL | Post-specialisation years |
| **Block 2: Credentials & Trust Markers** |||||
| `year_of_mbbs` | `INTEGER` | NULLABLE | NULL | MBBS year |
| `year_of_specialisation` | `INTEGER` | NULLABLE | NULL | Specialisation year |
| `fellowships` | `JSON` | NOT NULL | [] | Fellowships |
| `qualifications` | `JSON` | NOT NULL | [] | Qualifications |
| `professional_memberships` | `JSON` | NOT NULL | [] | Professional memberships |
| `awards_academic_honours` | `JSON` | NOT NULL | [] | Awards and honours |
| **Block 3: Clinical Focus & Expertise** |||||
| `areas_of_clinical_interest` | `JSON` | NOT NULL | [] | Clinical interests |
| `practice_segments` | `VARCHAR(50)` | NULLABLE | NULL | Practice segment |
| `conditions_commonly_treated` | `JSON` | NOT NULL | [] | Commonly treated conditions |
| `conditions_known_for` | `JSON` | NOT NULL | [] | Known-for conditions |
| `conditions_want_to_treat_more` | `JSON` | NOT NULL | [] | Want to treat more |
| **Block 4: The Human Side** |||||
| `training_experience` | `JSON` | NOT NULL | [] | Training experiences |
| `motivation_in_practice` | `JSON` | NOT NULL | [] | Motivations |
| `unwinding_after_work` | `JSON` | NOT NULL | [] | Unwinding activities |
| `recognition_identity` | `JSON` | NOT NULL | [] | Recognition items |
| `quality_time_interests` | `JSON` | NOT NULL | [] | Quality time interests |
| `quality_time_interests_text` | `TEXT` | NULLABLE | NULL | Quality time text |
| `professional_achievement` | `TEXT` | NULLABLE | NULL | Professional achievement |
| `personal_achievement` | `TEXT` | NULLABLE | NULL | Personal achievement |
| `professional_aspiration` | `TEXT` | NULLABLE | NULL | Professional aspiration |
| `personal_aspiration` | `TEXT` | NULLABLE | NULL | Personal aspiration |
| **Block 5: Patient Value & Choice Factors** |||||
| `what_patients_value_most` | `TEXT` | NULLABLE | NULL | Patient value |
| `approach_to_care` | `TEXT` | NULLABLE | NULL | Care approach |
| `availability_philosophy` | `TEXT` | NULLABLE | NULL | Availability philosophy |
| **Block 6: Content Seed** |||||
| `content_seeds` | `JSON` | NOT NULL | [] | Content seeds |
| **Legacy Compatibility Fields** |||||
| `primary_specialization` | `TEXT` | NULLABLE | NULL | Primary specialty (legacy) |
| `years_of_experience` | `INTEGER` | NULLABLE | NULL | Experience years |
| `consultation_fee` | `FLOAT` | NULLABLE | NULL | Consultation fee |
| `consultation_currency` | `VARCHAR(10)` | NULLABLE | 'INR' | Currency code |
| `medical_registration_number` | `VARCHAR(100)` | NULLABLE | NULL | Registration number |
| `registration_year` | `INTEGER` | NULLABLE | NULL | Registration year |
| `registration_authority` | `VARCHAR(100)` | NULLABLE | NULL | Registration authority |
| `conditions_treated` | `JSON` | NOT NULL | [] | Conditions treated |
| `procedures_performed` | `JSON` | NOT NULL | [] | Procedures performed |
| `age_groups_treated` | `JSON` | NOT NULL | [] | Age groups treated |
| `sub_specialties` | `JSON` | NOT NULL | [] | Sub-specializations |
| `areas_of_expertise` | `JSON` | NOT NULL | [] | Areas of expertise |
| `languages` | `JSON` | NOT NULL | [] | Languages spoken |
| `achievements` | `JSON` | NOT NULL | [] | Achievements |
| `publications` | `JSON` | NOT NULL | [] | Publications |
| `practice_locations` | `JSON` | NOT NULL | [] | Practice locations |
| `onboarding_source` | `VARCHAR(50)` | NULLABLE | NULL | How onboarded: manual, resume, voice |
| `resume_url` | `VARCHAR(500)` | NULLABLE | NULL | Resume file URL |
| `profile_photo` | `VARCHAR(500)` | NULLABLE | NULL | Profile photo URL |
| `verbal_intro_file` | `VARCHAR(500)` | NULLABLE | NULL | Verbal intro file URL |
| `professional_documents` | `JSON` | NOT NULL | [] | Professional document URLs |
| `achievement_images` | `JSON` | NOT NULL | [] | Achievement image URLs |
| `external_links` | `JSON` | NOT NULL | [] | External links |
| `raw_extraction_data` | `JSON` | NULLABLE | NULL | Raw AI extraction output |
| `created_at` | `TIMESTAMP WITH TZ` | NOT NULL | UTC NOW | Record creation timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | NULLABLE | NULL | Record update timestamp |

**Indexes:**
- Primary Key: `id`
- Unique: `email`, `phone`
- Index: `first_name`, `last_name`, `role`, `onboarding_status`, `onboarding_source`, `medical_registration_number`
- Composite: `(first_name, last_name)`, `(primary_specialization, years_of_experience)`

**Relationships:**
- ONE-TO-ONE with `users` (optional, via users.doctor_id)

---

## Enumerations

### OnboardingStatus
```python
PENDING = "pending"      # Initial state after profile creation
SUBMITTED = "submitted"  # Doctor submitted for review
VERIFIED = "verified"    # Admin approved
REJECTED = "rejected"    # Admin rejected
```

### DoctorTitle
```python
DR = "dr"               # Doctor
PROF = "prof"           # Professor
PROF_DR = "prof.dr"     # Professor Doctor
```

### HospitalVerificationStatus
```python
PENDING = "pending"     # Awaiting admin review
VERIFIED = "verified"   # Admin verified
REJECTED = "rejected"   # Admin rejected
```

### UserRole
```python
ADMIN = "admin"             # Full system access
OPERATIONAL = "operational" # Limited admin access
USER = "user"               # Regular user access
```

### DropdownFieldCategory
```python
PROFESSIONAL_IDENTITY = "professional_identity"
CREDENTIALS = "credentials"
CLINICAL_EXPERTISE = "clinical_expertise"
PERSONAL = "personal"
LOCATION = "location"
GENERAL = "general"
```

### CreatorType
```python
SYSTEM = "system"   # Seeded by the system
ADMIN = "admin"     # Added by admin
DOCTOR = "doctor"   # Contributed by doctor
```

---

## Relationships

### Entity Relationship Diagram

```
doctor_identity (1) ──────────── (1) doctor_details
       │
       │ (1)
       │
       ├───────────── (*) doctor_media
       │
       │ (1)
       │
       └───────────── (*) doctor_status_history

doctor_identity (*)
       │
       │ (via doctor_id)
       │
       └───────────── (*) doctor_hospital_affiliations ──── (*) hospitals

doctors (1) ─────────────────── (0..1) users
```

**Key Relationships:**

1. **doctor_identity ↔ doctor_details**: One-to-One (via doctor_id)
2. **doctor_identity ↔ doctor_media**: One-to-Many
3. **doctor_identity ↔ doctor_status_history**: One-to-Many
4. **doctor_identity ↔ doctor_hospital_affiliations**: One-to-Many (via doctor_id)
5. **hospitals ↔ doctor_hospital_affiliations**: One-to-Many
6. **doctors ↔ users**: One-to-One (optional, via users.doctor_id → doctors.id)
7. **voice_onboarding_blocks ↔ voice_onboarding_fields**: One-to-Many (via block_id)

---

## Indexes

### Performance Indexes

| Table | Index | Type | Purpose |
|-------|-------|------|---------|
| `doctor_identity` | `doctor_id` | UNIQUE | Lookups |
| `doctor_identity` | `email` | UNIQUE | Authentication |
| `doctor_details` | `doctor_id` | UNIQUE | Joins |
| `doctor_details` | `registration_number` | UNIQUE | Validation |
| `doctor_media` | `doctor_id` | INDEX | Fetch all media |
| `doctor_status_history` | `doctor_id` | INDEX | Audit trail |
| `dropdown_options` | `field_name` | INDEX | Value lookups |
| `dropdown_options` | `(field_name, value)` | UNIQUE | Deduplication |
| `dropdown_options` | `(field_name, is_active)` | INDEX | Active option queries |
| `dropdown_options` | `category` | INDEX | Category lookups |
| `hospitals` | `(name, city)` | COMPOSITE | Duplicate detection |
| `hospitals` | `(verification_status, is_active)` | COMPOSITE | Admin queries |
| `doctor_hospital_affiliations` | `(doctor_id, hospital_id)` | UNIQUE | One affiliation per hospital |
| `doctor_hospital_affiliations` | `(doctor_id, is_primary)` | COMPOSITE | Primary location |
| `users` | `(role, is_active)` | COMPOSITE | Role queries |
| `users` | `(phone, is_active)` | COMPOSITE | Auth queries |
| `doctors` | `(first_name, last_name)` | COMPOSITE | Name search |
| `doctors` | `(primary_specialization, years_of_experience)` | COMPOSITE | Filtering |

---

## Notes

1. **Cascade Deletes**: Onboarding relationships use `CASCADE DELETE` to maintain referential integrity. The `users.doctor_id` FK uses `SET NULL` on delete.
2. **Soft Deletes**: Tables use `is_active` and/or `deleted_at` for soft deletion.
3. **Timestamps**: All tables include `created_at` and `updated_at` timestamps.
4. **UUIDs**: Primary keys for doctor and affiliation tables use UUID v4 for global uniqueness.
5. **JSON Fields**: Used extensively for flexible, schema-less data (arrays, objects).
6. **Timezone Awareness**: All timestamps are `TIMESTAMP WITH TIME ZONE` in UTC.
7. **Enums**: Implemented with `native_enum=False` for SQLite compatibility.

---

## Migration History

Database schema is managed via **Alembic** migrations:

| Migration | Description |
|-----------|-------------|
| `000_initial_doctors_table.py` | Initial schema |
| `001_add_comprehensive_doctor_fields.py` | Extended fields |
| `002_comprehensive_doctor_schema.py` | Complete refactor |
| `003_unique_email_and_phone.py` | Added unique constraints |
| `004_phone_to_varchar.py` | Changed phone to VARCHAR |
| `005_add_hospitals_table.py` | Hospital management |
| `006_remove_field_name_from_doctor_media.py` | Media schema update |
| `007_add_consultation_fee_to_doctor_details.py` | Fee field |
| `008_add_field_name_to_doctor_media.py` | Restored field_name |
| `009_add_dropdown_options_table.py` | Dynamic dropdown support |
| `010_add_testimonials_table.py` | Testimonials table |
| `011_add_voice_onboarding_fields.py` | Voice onboarding config tables |
| `012_add_questionnaire_fields_to_doctors.py` | 6-block questionnaire fields on doctors |
| `013_enhance_dropdown_options.py` | Dropdown options v2 (categories, creator) |
| `014_add_role_to_doctors.py` | RBAC role field on doctors |
| `015_make_required_fields_nullable.py` | Nullable fields update |
| `016_add_users_table.py` | RBAC users table |
| `017_add_missing_doctor_details_columns.py` | 30 new columns on doctor_details (6-block questionnaire) |

**Running Migrations:**
```bash
# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one step
alembic downgrade -1

# Show current version
alembic current
```

---

**Last Updated:** 2026-02-22  
**Schema Version:** 4.0.0

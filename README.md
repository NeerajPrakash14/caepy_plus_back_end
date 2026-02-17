# 🏥 Doctor Onboarding Smart-Fill API

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

**Production-grade FastAPI backend for AI-powered doctor onboarding with resume parsing and voice registration**

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Development](#-development-guide)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Database Schema](#-database-schema)
- [Voice Onboarding Flow](#-voice-onboarding-flow)
- [Development Guide](#-development-guide)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## 🎯 Overview

Doctor Onboarding Smart-Fill is a **production-grade FastAPI microservice** that streamlines doctor registration for healthcare platforms. It offers three intelligent onboarding modes powered by Google Gemini AI:

1. **📄 Resume Upload** - Upload PDF/Image CVs and AI extracts structured professional data
2. **🎤 Voice Assistant** - Natural conversational AI collects registration details via speech
3. **📝 Manual CRUD** - RESTful API for traditional form-based data entry

Built with modern Python patterns, comprehensive type safety, and enterprise-grade architecture.

---

## ✨ Features

### Core Features
| Feature | Description |
|---------|-------------|
| **🤖 AI Resume Parsing** | Extract doctor information from PDF/image resumes using Gemini Vision API |
| **🎤 Voice Onboarding** | Conversational AI assistant for hands-free data collection |
| **🔄 Smart Auto-fill** | Extracted data automatically populates registration forms |
| **✅ Real-time Validation** | End-to-end validation with Pydantic schemas |
| **📁 Multi-format Support** | PDF, PNG, JPG, JPEG uploads (up to 10MB) |

### Technical Features
| Feature | Description |
|---------|-------------|
| **⚡ High Performance** | Async FastAPI with ORJSON responses and connection pooling |
| **🔒 Type Safety** | 100% type-hinted Python with Pydantic V2 validation |
| **📚 OpenAPI 3.0** | Auto-generated Swagger UI with comprehensive documentation |
| **🗄️ Modern Database** | SQLAlchemy 2.0 async ORM with PostgreSQL/SQLite support |
| **🔄 Session Management** | In-memory voice session tracking with automatic cleanup |
| **🏥 Health Checks** | Kubernetes-ready health, readiness, and liveness probes |
| **📊 Structured Logging** | JSON logging with context and correlation IDs |
| **🐳 Container Ready** | Multi-stage Docker builds with optimized images |

---

## 🛠 Tech Stack

### Backend (FastAPI Microservice)
| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.115+ | High-performance async web framework |
| **Python** | 3.12+ | Runtime with modern async/await patterns |
| **SQLAlchemy** | 2.0.36+ | Async ORM with modern syntax |
| **Pydantic** | 2.10+ | Data validation and serialization |
| **Google Gemini** | 1.0+ | AI for extraction & conversation (new SDK) |
| **Uvicorn** | 0.32+ | ASGI server with performance optimizations |
| **PostgreSQL** | 16+ | Production database (asyncpg driver) |
| **SQLite** | - | Development database (aiosqlite) |
| **Alembic** | 1.14+ | Database migrations |
| **Structlog** | 24.4+ | Structured logging |
| **ORJSON** | 3.10+ | Fast JSON serialization |

### Development & Quality
| Technology | Version | Purpose |
|------------|---------|---------|
| **Ruff** | 0.8+ | Fast Python linter and formatter |
| **MyPy** | 1.13+ | Static type checker |
| **Pytest** | 8.3+ | Testing framework with async support |
| **Pre-commit** | 4.0+ | Git hooks for code quality |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    REST API / OpenAPI 3.0                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │   │
│  │  │   /doctors   │  │ /onboarding  │  │    /voice/*          │   │   │
│  │  │   (CRUD)     │  │ (extraction) │  │  (conversation)      │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP/REST
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            API LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Endpoints                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │   │
│  │  │ DoctorsAPI   │  │ OnboardingAPI│  │ VoiceAPI             │   │   │
│  │  │ Controller   │  │ Controller   │  │ Controller           │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Dependency Injection
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           SERVICE LAYER                                 │
│  ┌──────────────────┐  ┌───────────────────┐  ┌────────────────────┐   │
│  │ DoctorRepository │  │ ExtractionService │  │ VoiceOnboardingSvc │   │
│  │ (Data Access)    │  │ (Gemini Vision)   │  │ (Gemini Chat)      │   │
│  └──────────────────┘  └───────────────────┘  └────────────────────┘   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
           ┌──────────────┐                 ┌─────────────────┐
           │ PostgreSQL   │                 │  Google Gemini  │
           │ Database     │                 │  AI API         │
           │ (Doctors,    │                 │  (Vision + Chat)│
           │Qualifications)│                 └─────────────────┘
           └──────────────┘
```

### Clean Architecture Principles

- **Dependency Inversion**: Services depend on abstractions (repositories, external APIs)
- **Single Responsibility**: Each layer has one clear purpose
- **Interface Segregation**: Focused, minimal interfaces
- **Open/Closed**: Extensible without modifying existing code

### Data Flow Patterns

**Resume Extraction Flow:**
```
Upload PDF/Image → Validate → Gemini Vision API → Parse JSON → Validate Schema → Return Structured Data
```

**Voice Onboarding Flow:**
```
Start Session → User Speech → Gemini Chat API → Extract Fields → Update Session → Generate Response → Continue Loop
```

**CRUD Operations:**
```
Request → Validate → Repository → Database → Response
```

---

## 📁 Project Structure

```
doctor-onboarding-service/
├── src/app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                       # FastAPI application factory
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── endpoints/            # API route handlers
│   │       │   ├── __init__.py
│   │       │   ├── doctors.py        # Doctor CRUD endpoints
│   │       │   ├── health.py         # Health check endpoints
│   │       │   ├── onboarding.py     # Resume extraction endpoint
│   │       │   └── voice.py          # Voice conversation endpoints
│   │       └── __init__.py           # API version router
│   ├── core/                         # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py                 # Pydantic settings (12-factor)
│   │   ├── exceptions.py             # Custom exception classes
│   │   ├── prompts.py                # External AI prompt management
│   │   └── responses.py              # Standardized API responses
│   ├── db/                           # Database layer
│   │   ├── __init__.py
│   │   └── session.py                # SQLAlchemy async session management
│   ├── models/                       # SQLAlchemy 2.0 ORM models
│   │   ├── __init__.py
│   │   └── doctor.py                 # Doctor & Qualification entities
│   ├── repositories/                 # Data access layer
│   │   ├── __init__.py
│   │   └── doctor_repository.py      # Doctor CRUD operations
│   ├── schemas/                      # Pydantic V2 DTOs
│   │   ├── __init__.py
│   │   ├── doctor.py                 # Doctor data validation schemas
│   │   └── voice.py                  # Voice session schemas
│   └── services/                     # Business logic layer
│       ├── __init__.py
│       ├── extraction_service.py     # Resume parsing (Gemini Vision)
│       ├── gemini_service.py         # Gemini AI wrapper
│       └── voice_service.py          # Voice conversation state machine
├── config/
│   └── prompts.yaml                  # External AI prompt configuration
├── data/
│   └── doctor_onboarding.db          # SQLite database (development)
├── alembic/                          # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                     # Migration files
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   ├── test_doctors.py               # Doctor API tests
│   └── test_health.py                # Health check tests
├── pyproject.toml                    # Python project configuration
├── Dockerfile                        # Multi-stage container build
├── docker-compose.yml                # Development environment
├── .env.example                      # Environment template
└── README.md                         # This documentation
```

---

## 🚀 Quick Start (From Scratch)

> **Complete setup guide for someone starting fresh with this codebase**

### Prerequisites

> ⚠️ **IMPORTANT**: This project requires **Python 3.10 or higher**. Python 3.9 and below are NOT supported due to modern type hint syntax (`str | tuple` instead of `Union[str, tuple]`).

| Requirement | Version | Installation |
|-------------|---------|--------------|
| **Python** | **3.10, 3.11, or 3.12** (3.12 recommended) | [Download](https://www.python.org/downloads/) or `brew install python@3.12` |
| **PostgreSQL** | 15+ or 16+ | `brew install postgresql@15` (macOS) |
| **pip** | Latest | Comes with Python |

---

### Step 1: Extract & Navigate

```bash
# If you received a zip file
unzip caepy_plus_backend.zip
cd caepy_plus_backend
```

---

### Step 2: Verify Python Version

```bash
# Check Python version (MUST be 3.10+)
python3 --version

# If you have Python 3.9 or below, install a newer version:
brew install python@3.12        # macOS
# or download from https://www.python.org/downloads/

# Verify you have Python 3.10+
python3.12 --version  # Should show 3.12.x
# OR
python3.11 --version  # Should show 3.11.x
# OR  
python3.10 --version  # Should show 3.10.x
```

---

### Step 3: Create Python Virtual Environment

```bash
# Create virtual environment with Python 3.10+ (use the version you verified above)
python3.12 -m venv venv     # Recommended: Python 3.12
# OR
# python3.11 -m venv venv   # Python 3.11 also works
# OR
# python3.10 -m venv venv   # Python 3.10 minimum

# Activate it
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Verify the venv is using Python 3.10+
python3 --version               # Should show 3.10+ inside venv
```

---

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5: Install & Start PostgreSQL

#### macOS (Homebrew)
```bash
# Install PostgreSQL 15
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Verify it's running
brew services list | grep postgres
# Should show: postgresql@15 started
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Windows
Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

---

### Step 6: Create Database & User

#### macOS (PostgreSQL 15)
```bash
/opt/homebrew/opt/postgresql@15/bin/psql -U $(whoami) -d postgres << 'EOF'
-- Create user
CREATE USER linqdev WITH PASSWORD 'linqdev123';

-- Create database
CREATE DATABASE doctor_onboarding OWNER linqdev;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE doctor_onboarding TO linqdev;

-- Connect and grant schema access
\c doctor_onboarding
GRANT ALL ON SCHEMA public TO linqdev;
EOF
```

#### Linux/Windows (using psql)
```bash
sudo -u postgres /opt/homebrew/opt/postgresql@15/bin/psql << 'EOF'
CREATE USER linqdev WITH PASSWORD 'linqdev123';
CREATE DATABASE doctor_onboarding OWNER linqdev;
GRANT ALL PRIVILEGES ON DATABASE doctor_onboarding TO linqdev;
\c doctor_onboarding
GRANT ALL ON SCHEMA public TO linqdev;
EOF
```

---

### Step 7: Verify .env Configuration

The `.env` file should already exist with these settings:

```properties
# Database (already configured)
DATABASE_URL=postgresql+asyncpg://linqdev:linqdev123@localhost:5432/doctor_onboarding

# Google Gemini AI (get your key from https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

> ⚠️ If `.env` is missing, create it with the values above. Get your Google API key from https://makersuite.google.com/app/apikey

---

### Step 8: Start the Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start the server (tables auto-create on startup)
./venv/bin/uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Database tables created
INFO:     Application startup complete.
```

---

### Step 9: Verify Everything Works

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "doctor-onboarding-service",
  "checks": {
    "database": {"status": "healthy"},
    "ai_service": {"status": "healthy"}
  }
}
```

---

### Step 10: Access the API

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI (Interactive API docs) |
| http://localhost:8000/redoc | ReDoc (Alternative docs) |
| http://localhost:8000/api/v1/health | Health check endpoint |

---

### 🎉 Quick Start Summary (Copy-Paste Commands)

```bash
# === ONE-TIME SETUP ===

# 1. Extract and enter directory
cd caepy_plus_backend

# 2. Verify Python version (MUST be 3.10+)
python3 --version
# If 3.9 or below, install Python 3.12:
brew install python@3.12

# 3. Create & activate virtual environment with Python 3.10+
python3.12 -m venv venv  # Use python3.12, python3.11, or python3.10
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# 6. Create database
/opt/homebrew/opt/postgresql@15/bin/psql -U $(whoami) -d postgres -c "
CREATE USER linqdev WITH PASSWORD 'linqdev123';
CREATE DATABASE doctor_onboarding OWNER linqdev;
GRANT ALL PRIVILEGES ON DATABASE doctor_onboarding TO linqdev;
"

# 7. Grant schema permissions
/opt/homebrew/opt/postgresql@15/bin/psql -U linqdev -d doctor_onboarding -c "GRANT ALL ON SCHEMA public TO linqdev;"

# === START SERVER ===
./venv/bin/uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# === VERIFY ===
curl http://localhost:8000/api/v1/health
```

---

### Troubleshooting Quick Start

| Problem | Solution |
|---------|----------|
| **`TypeError: unsupported operand type(s) for \|`** | **🔴 CRITICAL: You're using Python 3.9 or below. This project requires Python 3.10+. Delete venv and recreate with Python 3.10+: `rm -rf venv && python3.12 -m venv venv`** |
| `command not found: psql` | Use full path: `/opt/homebrew/opt/postgresql@15/bin/psql` |
| `role "linqdev" already exists` | User exists, skip creation |
| `database "doctor_onboarding" already exists` | Database exists, skip creation |
| `Address already in use (port 8000)` | Kill existing process: `lsof -ti:8000 \| xargs kill -9` |
| `ModuleNotFoundError` | Activate venv: `source venv/bin/activate` |
| `Connection refused` to database | Start PostgreSQL: `brew services start postgresql@15` |
| `python3.12: command not found` | Install Python 3.12: `brew install python@3.12` |
# Database
DATABASE_URL=postgresql+asyncpg://linqdev:linqdev123@localhost:5432/doctor_onboarding

# Google Gemini AI (get your key from Google AI Studio)
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 4. Run Database Migrations

```bash
# Apply all migrations
./venv/bin/alembic upgrade head
```

### 5. Start the Server

```bash
# Development mode with auto-reload
./venv/bin/uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Verify Installation

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Open API docs
open http://localhost:8000/docs
```

---

## ⚙️ Configuration

### Current Configuration (.env)

```properties
# Application
APP_NAME=doctor-onboarding-service
APP_VERSION=2.0.0
APP_ENV=development
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://linqdev:linqdev123@localhost:5432/doctor_onboarding

# Google Gemini AI (get your key from Google AI Studio)
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_TOKENS=4096

# File Uploads
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg

# Blob Storage Configuration
STORAGE_BACKEND=local  # or 's3' for AWS S3
BLOB_STORAGE_PATH=./blob_storage
BLOB_BASE_URL=/api/v1/blobs

# AWS S3 Settings (when STORAGE_BACKEND=s3)
# AWS_ACCESS_KEY_ID=your_access_key_here
# AWS_SECRET_ACCESS_KEY=your_secret_key_here
# AWS_REGION=us-east-1
# AWS_S3_BUCKET=your-bucket-name
# AWS_S3_PREFIX=doctors
# AWS_S3_USE_SIGNED_URLS=false
# AWS_S3_SIGNED_URL_EXPIRY=3600
```

### Database Credentials

| Parameter | Value |
|-----------|-------|
| **Host** | `localhost` |
| **Port** | `5432` |
| **Database** | `doctor_onboarding` |
| **Username** | `linqdev` |
| **Password** | `linqdev123` |
| **Connection URL** | `postgresql+asyncpg://linqdev:linqdev123@localhost:5432/doctor_onboarding` |

### Blob Storage Configuration

The application supports **two storage backends** for managing doctor profile files (photos, documents, certificates):

#### Local Storage (Default)

Files are stored on the local filesystem:

```properties
STORAGE_BACKEND=local
BLOB_STORAGE_PATH=./blob_storage
BLOB_BASE_URL=/api/v1/blobs
```

**Directory Structure:**
```
blob_storage/
├── {doctor_id}/
│   ├── profile_photo/
│   │   └── {blob_id}.jpg
│   ├── documents/
│   │   └── {blob_id}.pdf
│   └── achievements/
│       └── {blob_id}.png
```

**Best For:** Development, small deployments, single-server setups

---

#### AWS S3 Storage

Files are stored in AWS S3 bucket with optional signed URLs:

```properties
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET=my-doctor-profiles
AWS_S3_PREFIX=doctors
AWS_S3_USE_SIGNED_URLS=false
AWS_S3_SIGNED_URL_EXPIRY=3600  # seconds
```

**S3 Key Structure:**
```
s3://my-doctor-profiles/
└── doctors/
    └── {doctor_id}/
        ├── profile_photo/
        │   └── {blob_id}.jpg
        └── documents/
            └── {blob_id}.pdf
```

**Best For:** Production, scalability, multi-region deployment, CDN integration

---

#### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `STORAGE_BACKEND` | `local` \| `s3` | `local` | Storage backend to use |
| `BLOB_STORAGE_PATH` | string | `./blob_storage` | Local storage directory path |
| `BLOB_BASE_URL` | string | `/api/v1/blobs` | Base URL for serving local blobs |
| `AWS_ACCESS_KEY_ID` | string | - | AWS access key (required for S3) |
| `AWS_SECRET_ACCESS_KEY` | string | - | AWS secret key (required for S3) |
| `AWS_REGION` | string | `us-east-1` | AWS region for S3 bucket |
| `AWS_S3_BUCKET` | string | - | S3 bucket name (required for S3) |
| `AWS_S3_PREFIX` | string | `doctors` | Prefix for all S3 object keys |
| `AWS_S3_USE_SIGNED_URLS` | boolean | `false` | Use signed URLs for private buckets |
| `AWS_S3_SIGNED_URL_EXPIRY` | integer | `3600` | Signed URL expiry time (seconds) |

---

#### Switching Between Backends

**No code changes required!** Simply update the `.env` file and restart:

```bash
# Switch from Local to S3
STORAGE_BACKEND=s3  # Change this line
# Add S3 credentials...

# Restart server
./venv/bin/uvicorn src.app.main:app --reload
```

The factory pattern automatically selects the correct storage implementation.

---

#### S3 Setup Guide

**1. Create S3 Bucket**
```bash
aws s3 mb s3://my-doctor-profiles --region us-east-1
```

**2. Configure Bucket Policy (Public Access)**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-doctor-profiles/*"
  }]
}
```

**3. Create IAM User with Permissions**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:HeadObject"
    ],
    "Resource": "arn:aws:s3:::my-doctor-profiles/*"
  }]
}
```

**4. Update Environment Variables**
```properties
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=my-doctor-profiles
```

**5. For Private Buckets (Recommended for Production)**
```properties
AWS_S3_USE_SIGNED_URLS=true
AWS_S3_SIGNED_URL_EXPIRY=3600  # URLs expire after 1 hour
```

Keep bucket private and use signed URLs for secure access.

---

#### Storage Backend Comparison

| Feature | Local Storage | S3 Storage |
|---------|--------------|------------|
| **Setup** | ✅ Instant | ⚠️ Requires AWS account |
| **Cost** | ✅ Free (disk only) | 💰 Pay per GB + requests |
| **Scalability** | ⚠️ Limited by disk | ✅ Unlimited |
| **Availability** | ⚠️ Single point of failure | ✅ 99.99% SLA |
| **Backup** | ⚠️ Manual | ✅ Automatic versioning |
| **CDN Integration** | ❌ | ✅ CloudFront ready |
| **Multi-region** | ❌ | ✅ Built-in |
| **Performance** | ✅ Fast (local I/O) | ✅ Fast (global CDN) |

---


### AI Prompt Configuration

AI prompts are externalized in `config/prompts.yaml` for easy maintenance:

```yaml
# config/prompts.yaml
version: "2.0.0"
resume_extraction:
  system_prompt: |
    You are a medical document parser...
  response_schema: |
    { "personal_details": {...}, ... }
```

---

## 📡 API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Interactive Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Authentication
> **Note:** Authentication disabled in development. Use OAuth2/JWT in production.

### Core Endpoints

#### Health Checks
```http
GET /health          # Comprehensive health check
GET /ready           # Kubernetes readiness probe
GET /live            # Kubernetes liveness probe
```

#### Doctor Management
```http
POST   /doctors              # Create doctor
GET    /doctors              # List doctors (paginated)
GET    /doctors/{id}         # Get doctor by ID
PUT    /doctors/{id}         # Update doctor
DELETE /doctors/{id}         # Delete doctor
GET    /doctors/email/{email} # Get by email
```

#### Resume Extraction
```http
POST /onboarding/extract-resume  # Upload & extract from resume
POST /onboarding/validate-data   # Validate extracted data
```

#### Voice Onboarding
```http
POST   /voice/start                    # Start conversation session
POST   /voice/chat                     # Send message & get response
GET    /voice/session/{session_id}     # Get session status
POST   /voice/session/{session_id}/finalize  # Complete session
DELETE /voice/session/{session_id}     # Cancel session
```

### Example Usage

#### Extract Data from Resume
```bash
curl -X POST http://localhost:8000/api/v1/onboarding/extract-resume \
  -F "file=@doctor_resume.pdf"
```

#### Create Doctor Record
```bash
curl -X POST http://localhost:8000/api/v1/doctors \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Sarah",
    "last_name": "Johnson",
    "email": "sarah.johnson@hospital.com",
    "primary_specialization": "Cardiology",
    "medical_registration_number": "MED123456"
  }'
```

#### Start Voice Session
```bash
curl -X POST http://localhost:8000/api/v1/voice/start \
  -H "Content-Type: application/json" \
  -d '{"language": "en"}'
```

---

## 🗄️ Dual Database Architecture

This application implements a **dual database strategy** for optimal performance and data redundancy:

### Architecture Overview

```
┌──────────────┐      Write       ┌──────────────┐
│              │ ────────────────> │              │
│   SQLite     │                   │ PostgreSQL   │
│  (Local DB)  │ <───────────────  │ (Cloud SQL)  │
│              │      Write        │              │
└──────────────┘                   └──────────────┘
       ↑                                    
       │ Read (Fast)                        
       │                                    
```

### Database Roles

| Database | Purpose | Use Case |
|----------|---------|----------|
| **SQLite** | Local development, fast reads | Development environment, read operations |
| **PostgreSQL** | Production database | Cloud deployment, data persistence |

### Write Operations (Dual Write)
All **CREATE, UPDATE, DELETE** operations are performed on **BOTH** databases simultaneously:
- Doctor record creation
- Profile updates
- Data deletion

This ensures data consistency and redundancy.

### Read Operations (Single Read)
All **GET** operations default to **SQLite** for optimal performance:
- Fetching doctor profiles
- Listing doctors
- Search operations

### Configuration

```env
# SQLite (Local Development)
DATABASE_URL=sqlite+aiosqlite:///./data/doctor_onboarding.db

# PostgreSQL (Production - Cloud SQL)
POSTGRES_HOST=project-58d9930a-f1a3-44b6-ac8:asia-south1:linqmd
POSTGRES_PORT=5432
POSTGRES_USER=linqdev
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=doctor_onboarding
```

### Benefits

✅ **High Performance**: Fast local reads from SQLite  
✅ **Data Redundancy**: Automatic backup to PostgreSQL  
✅ **Cloud Ready**: PostgreSQL for production deployment  
✅ **Development Friendly**: SQLite for local testing  
✅ **Zero Configuration**: Automatic dual-write management  

### Implementation

The system uses `DualDoctorRepository` which automatically handles:
- Dual database connections
- Transaction management across both databases
- Automatic rollback if either database fails
- Connection pooling for PostgreSQL
- Health checks for both databases

For more details, see [DUAL_DATABASE_IMPLEMENTATION.md](./DUAL_DATABASE_IMPLEMENTATION.md).

---

## 🗄️ Database Schema

### Tables

#### `doctors` (Single Comprehensive Table)

The system uses a **single table design** with all doctor information stored in one place:

```sql
CREATE TABLE doctors (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Personal Details
    title VARCHAR(20),                                  -- Dr., Prof., etc.
    gender VARCHAR(100),                                -- Male, Female, Other
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone INTEGER,                                      -- Contact number
    
    -- Professional Information
    primary_specialization TEXT NOT NULL,              -- Main specialty
    years_of_experience INTEGER,
    consultation_fee FLOAT,
    registration_number VARCHAR(100),                   -- Medical council number
    registration_year INTEGER,                          -- Year of registration
    registration_authority VARCHAR(100),                -- Issuing council
    
    -- Qualifications (JSON Array)
    qualifications JSON DEFAULT '[]',                   -- [{degree, institution, year, specialization}]
    
    -- Clinical Practice Details (JSON Arrays)
    sub_specialties JSON DEFAULT '[]',                  -- Sub-specializations
    areas_of_expertise JSON DEFAULT '[]',               -- Expertise areas
    conditions_treated JSON DEFAULT '[]',               -- Conditions treated
    procedures_performed JSON DEFAULT '[]',             -- Procedures performed
    age_groups_treated JSON DEFAULT '[]',               -- Age groups (pediatric, geriatric, etc.)
    
    -- Professional Information (JSON Arrays)
    professional_memberships JSON DEFAULT '[]',         -- Professional body memberships
    languages JSON DEFAULT '[]',                        -- Languages spoken
    
    -- Achievements (JSON)
    achievements JSON,                                  -- Awards and recognitions
    publications JSON,                                  -- Research publications
    
    -- Media & Documents (BLOB/Binary)
    profile_photo BLOB,                                 -- Profile picture
    verbal_intro_file BLOB,                             -- Audio introduction
    professional_documents BLOB,                        -- Certificates, licenses
    achievement_images BLOB,                            -- Award images
    
    -- Practice Locations (JSON Array)
    -- Each location: {hospital_name, address, city, state, phone_number, 
    --                 consultation_fee, consultation_type, weekly_schedule}
    practice_locations JSON DEFAULT '[]',
    
    -- External Links (JSON Object)
    external_links JSON,                                -- {linkedin: url, website: url, etc.}
    
    -- Metadata
    onboarding_source VARCHAR(50),                      -- resume, voice, manual
    resume_url VARCHAR(500),
    raw_extraction_data JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Data Type Details

| Field Type | Storage | Purpose | Example |
|------------|---------|---------|---------|
| **BLOB** | Binary | Files, images, audio | Profile photos, documents |
| **JSON (Object)** | JSON | Complex structures | Qualifications, achievements |
| **JSON (Array)** | JSON | Lists | Languages, specialties |
| **TEXT** | Text | Long text | Specialization description |
| **VARCHAR(100)** | String | Short text | Names, email |
| **INTEGER** | Number | Numeric values | Phone, years of experience |
| **FLOAT** | Decimal | Currency | Consultation fee |

### Single Table Benefits

✅ **No JOINs Required**: All data in one query  
✅ **Better Performance**: Simplified queries  
✅ **Easier Migrations**: Single table to manage  
✅ **JSON Flexibility**: Complex nested structures supported  
✅ **ACID Compliance**: All changes in one transaction  

**Note**: The previous `qualifications` table has been merged into the `doctors` table as a JSON array field.

### Indexes
- Primary keys on all tables
- Unique index on `doctors.email`
- Index on `doctors.medical_registration_number`
- Index on `doctors.first_name` and `doctors.last_name`
- Composite indexes for common queries (`full_name`, `spec_exp`)

---

## 🎤 Voice Onboarding Flow

The voice onboarding system implements a **state machine** pattern for natural conversations:

### Session States
- `active`: Collecting information
- `completed`: All fields collected
- `expired`: Session timed out

### Field Collection Order
1. `full_name` - Professional title + name
2. `primary_specialization` - Medical specialty
3. `years_of_experience` - Practice duration
4. `medical_registration_number` - License number
5. `email` - Contact email
6. `phone_number` - Phone contact
7. `languages` - Spoken languages

### Conversation Flow
```
User: "Hi, I'm Dr. Sarah Johnson, a cardiologist"

AI: "Nice to meet you, Dr. Johnson! I've noted your specialization as Cardiology.
     What's your medical registration number?"

User: "It's MED123456"

AI: "Your registration number is MED123456. Can you confirm that's correct?"

[... continues until all fields collected ...]

AI: "Perfect! I've collected all the information. Let me summarize..."
```

### Session Management
- **In-memory storage** with automatic cleanup
- **30-minute expiry** with periodic background cleanup
- **Field confidence scoring** for data quality
- **Graceful error recovery** for unclear responses

---

## 🛠 Development Guide

### Code Quality

```bash
# Run all checks
pre-commit run --all-files

# Format code
ruff format .

# Lint code
ruff check . --fix

# Type check
mypy src/

# Run tests
pytest
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_doctors.py::test_create_doctor
```

### API Development

```bash
# Auto-reload during development
uvicorn src.app.main:app --reload

# With custom host/port
uvicorn src.app.main:app --host 0.0.0.0 --port 8000

# Production server
uvicorn src.app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

---

## 🧪 Testing

### Test Structure
```
tests/
├── conftest.py           # Shared fixtures
├── test_doctors.py       # Doctor CRUD tests
├── test_health.py        # Health endpoint tests
└── test_voice.py         # Voice onboarding tests (planned)
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Async tests
pytest -k "async" --asyncio-mode=auto

# Integration tests
pytest -m "integration"
```

### Test Categories
- **Unit Tests**: Individual functions and classes
- **Integration Tests**: API endpoints with database
- **E2E Tests**: Full user workflows (planned)

---

## 🚢 Deployment

### Docker Production Build

```bash
# Build production image
docker build -t doctor-onboarding:latest .

# Run with environment
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY=your_key \
  -e DATABASE_URL=postgresql+asyncpg://... \
  doctor-onboarding:latest
```

### Docker Compose (Full Stack)

```bash
# Production deployment
docker compose -f docker-compose.prod.yml up -d

# With custom environment
docker compose --env-file .env.prod up -d
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: doctor-onboarding
spec:
  replicas: 3
  selector:
    matchLabels:
      app: doctor-onboarding
  template:
    spec:
      containers:
      - name: api
        image: doctor-onboarding:latest
        ports:
        - containerPort: 8000
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-secrets
              key: api-key
        livenessProbe:
          httpGet:
            path: /api/v1/live
            port: 8000
        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8000
```

---

## 🔧 Troubleshooting

### Common Issues

#### API Key Issues
```bash
# Check API key configuration
curl http://localhost:8000/api/v1/health

# Verify Gemini API access
python -c "import google.genai as genai; genai.configure(api_key='your_key')"
```

#### Database Connection
```bash
# Test database connectivity
alembic current

# Reset database
alembic downgrade base
alembic upgrade head
```

#### Memory Issues
```bash
# Monitor memory usage
docker stats

# Check voice session cleanup
curl http://localhost:8000/api/v1/health
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Check application logs
docker compose logs api
```

### Performance Tuning

```bash
# Database connection pooling
export DATABASE_POOL_SIZE=10
export DATABASE_MAX_OVERFLOW=20

# Worker processes
uvicorn src.app.main:app --workers 4

# Memory limits
docker run --memory=1g --memory-swap=2g
```

---

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/new-feature`
3. **Make** your changes with tests
4. **Run** quality checks: `pre-commit run --all-files`
5. **Submit** a pull request

### Code Standards

- **Type Hints**: 100% coverage required
- **Docstrings**: Google style for all public functions
- **Tests**: Minimum 80% coverage
- **Linting**: Ruff compliant
- **Formatting**: Black compatible

### Commit Messages

```
feat: add voice session timeout handling
fix: resolve database connection leak
docs: update API reference for v2 endpoints
test: add integration tests for doctor CRUD
```

---

## 📄 License

**MIT License** - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** team for the excellent framework
- **Google AI** for Gemini API access
- **SQLAlchemy** for robust ORM capabilities
- **Pydantic** for type-safe data validation

---

**Built with ❤️ for healthcare professionals worldwide**

# 🚀 Production Deployment Checklist

## Pre-Deployment Checklist

### Environment Configuration

- [ ] **APP_ENV** is set to `production`
- [ ] **DEBUG** is set to `False`
- [ ] **SECRET_KEY** is a strong random key (64+ chars)
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(64))"
  ```
- [ ] **DATABASE_URL** points to production PostgreSQL (not localhost)
- [ ] **GOOGLE_API_KEY** is set for Gemini AI features
- [ ] **SMS_USER_ID** and **SMS_USER_PASS** are set for OTP functionality

### Database

- [ ] PostgreSQL 16+ is running and accessible
- [ ] Connection pooling is configured appropriately:
  - `DATABASE_POOL_SIZE`: 10-20 for moderate load
  - `DATABASE_MAX_OVERFLOW`: 20-40 for burst capacity
- [ ] All migrations are applied: `alembic upgrade head`
- [ ] Database backups are configured
- [ ] SSL/TLS is enabled for database connections

### Security

- [ ] CORS origins are restricted (not `*`)
- [ ] HTTPS is enforced (SSL termination at load balancer)
- [ ] Rate limiting is configured
- [ ] API documentation is disabled in production:
  - `docs_url=None`
  - `redoc_url=None`
  - `openapi_url=None`

### Redis (Optional but Recommended)

- [ ] Redis is running for OTP storage (production-grade)
- [ ] `REDIS_URL` is configured
- [ ] `REDIS_ENABLED=True`

### S3 Storage (If using)

- [ ] `STORAGE_BACKEND=s3`
- [ ] AWS credentials configured
- [ ] S3 bucket exists with proper permissions
- [ ] Signed URLs enabled for security

### Monitoring

- [ ] Health endpoint accessible: `/api/v1/health`
- [ ] Readiness probe configured: `/api/v1/ready`
- [ ] Liveness probe configured: `/api/v1/live`
- [ ] Structured logging enabled (JSON format)
- [ ] Log aggregation configured (CloudWatch, Datadog, etc.)

---

## Deployment Commands

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Database Migrations
```bash
alembic upgrade head
```

### 3. Seed Dropdown Values (First Deploy)
```bash
python scripts/seed_dropdown_values.py
```

### 4. Create Admin User
```bash
python -c "
import psycopg2
from datetime import datetime, timezone

conn = psycopg2.connect('YOUR_DATABASE_URL')
cur = conn.cursor()
cur.execute('''
    INSERT INTO users (phone, email, role, is_active, created_at)
    VALUES ('+91XXXXXXXXXX', 'admin@example.com', 'admin', true, %s)
    ON CONFLICT (phone) DO UPDATE SET role = 'admin'
    RETURNING id
''', (datetime.now(timezone.utc),))
print(f'Admin user ID: {cur.fetchone()[0]}')
conn.commit()
conn.close()
"
```

### 5. Start Production Server
```bash
# Using gunicorn with uvicorn workers (recommended)
gunicorn src.app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --timeout 120

# Or using uvicorn directly
uvicorn src.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

---

## Docker Deployment

```bash
# Build image
docker build -t caepy-backend:latest .

# Run container
docker run -d \
  --name caepy-backend \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e SECRET_KEY=your-secret-key \
  -e GOOGLE_API_KEY=your-api-key \
  caepy-backend:latest
```

---

## Post-Deployment Verification

### 1. Health Check
```bash
curl https://your-domain.com/api/v1/health
# Expected: {"status": "healthy", ...}
```

### 2. Readiness Check
```bash
curl https://your-domain.com/api/v1/ready
# Expected: {"status": "ready"}
```

### 3. Test OTP Flow
```bash
# Request OTP
curl -X POST https://your-domain.com/api/v1/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"mobile_number": "9876543210"}'

# Verify OTP
curl -X POST https://your-domain.com/api/v1/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"mobile_number": "9876543210", "otp": "123456"}'
```

### 4. Test Admin Access
```bash
# Get JWT token first, then:
curl https://your-domain.com/api/v1/admin/users \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Rollback Procedure

### Database Rollback
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

### Application Rollback
```bash
# If using Docker
docker pull caepy-backend:previous-version
docker stop caepy-backend
docker run -d --name caepy-backend ... caepy-backend:previous-version
```

---

## Performance Tuning

### Database Pool Sizing
```
Recommended pool size = (2 * CPU cores) + effective_spindle_count
For cloud databases: Start with 10, monitor, and adjust
```

### Worker Processes
```
workers = (2 * CPU cores) + 1
For 4-core server: 9 workers
```

### Memory
```
Minimum: 512MB per worker
Recommended: 1GB per worker for AI operations
```

---

## Troubleshooting

### Common Issues

1. **Database Connection Refused**
   - Check DATABASE_URL
   - Verify PostgreSQL is running
   - Check firewall rules

2. **Redis Connection Failed**
   - Falls back to in-memory (not recommended for production)
   - Check REDIS_URL
   - Verify Redis is running

3. **SMS Not Sending**
   - Verify SMS_USER_ID and SMS_USER_PASS are configured
   - Check SMS API rate limits

4. **AI Features Not Working**
   - Verify GOOGLE_API_KEY is valid
   - Check Gemini API quota

---

**Last Updated:** 2026-02-14
**Version:** 2.0.0

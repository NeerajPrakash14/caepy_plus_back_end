"""Pytest fixtures and configuration."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.app.core.config import settings
from src.app.db.session import get_db, Base
from src.app.main import app

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


def _base64url_encode(data: bytes) -> str:
    """Encode bytes using base64 URL-safe encoding without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _create_test_jwt(
    subject: str = "+1-555-0123",
    doctor_id: int | None = 1,
    email: str | None = "test@example.com",
    role: str = "admin",
    expire_minutes: int = 30,
) -> str:
    """Create a test JWT token for authentication in tests.
    
    Uses the same encoding logic as the production auth module.
    """
    secret = settings.SECRET_KEY
    algorithm = "HS256"
    
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expire_minutes)
    
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "doctor_id": doctor_id,
        "phone": subject,
        "email": email,
        "role": role,
    }
    
    header = {"alg": algorithm, "typ": "JWT"}
    
    header_json = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    
    encoded_header = _base64url_encode(header_json)
    encoded_payload = _base64url_encode(payload_json)
    
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    encoded_signature = _base64url_encode(signature)
    
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Get authentication headers with a valid test JWT token."""
    token = _create_test_jwt()
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_factory() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture(scope="function")
async def client(test_engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with overridden dependencies."""
    
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async_session_factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def sample_doctor_data() -> dict:
    """Sample doctor data for tests.
    
    Matches the current DoctorCreate schema.
    """
    return {
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@hospital.com",
        "phone_number": "+1-555-0123",
        "title": "Dr.",
        "gender": "Male",
        "primary_specialization": "Cardiology",
        "medical_registration_number": "MED-12345",
        "registration_year": 2005,
        "registration_authority": "Medical Council",
        "years_of_experience": 15,
        "consultation_fee": 150.00,
        # qualifications is list[str] in current schema
        "qualifications": [
            "MBBS - Harvard Medical School (2005)",
            "MD Cardiology - Johns Hopkins (2008)",
        ],
        # practice_locations now uses PracticeLocationBase schema
        "practice_locations": [
            {
                "hospital_name": "City Hospital",
                "address": "123 Medical Center Drive",
                "city": "New York",
                "state": "NY",
                "phone_number": "+1-555-0100",
            }
        ],
    }

@pytest.fixture
def sample_update_data() -> dict:
    """Sample update data for tests."""
    return {
        "first_name": "Jonathan",
        "phone_number": "+1-555-9999",
        "years_of_experience": 16,
    }

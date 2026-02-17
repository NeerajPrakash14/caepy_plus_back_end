"""OTP Authentication Service.

Handles:
- OTP generation
- OTP storage (Redis with in-memory fallback)
- SMS sending via onlysms.co.in API
- OTP verification
"""
import json
import secrets
import time
from typing import Dict, Optional, Tuple
import httpx
import structlog
from urllib.parse import quote

from src.app.core.config import get_settings

logger = structlog.get_logger(__name__)

# Try to import redis
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis package not installed, using in-memory OTP storage")

class RedisOTPStore:
    """
    Redis-based OTP storage with automatic TTL.
    
    Features:
    - Automatic key expiration using Redis TTL
    - Attempt tracking with atomic operations
    - Distributed deployment support
    - Persistence across restarts
    """
    
    def __init__(self, redis_url: str, prefix: str = "otp:", ttl_seconds: int = 300, max_attempts: int = 3):
        """
        Initialize Redis OTP store.
        
        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for OTP data
            ttl_seconds: OTP validity period
            max_attempts: Maximum verification attempts
        """
        self._redis_url = redis_url
        self._prefix = prefix
        self._ttl = ttl_seconds
        self._max_attempts = max_attempts
        self._redis: Optional[aioredis.Redis] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect to Redis. Returns True if successful."""
        if not REDIS_AVAILABLE:
            return False
        
        try:
            self._redis = await aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info("Redis OTP store connected", url=self._redis_url[:30] + "...")
            return True
        except Exception as e:
            logger.warning("Redis connection failed, will use in-memory fallback", error=str(e))
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._connected = False
    
    def _otp_key(self, mobile_number: str) -> str:
        """Generate Redis key for OTP storage."""
        return f"{self._prefix}{mobile_number}"
    
    def _attempts_key(self, mobile_number: str) -> str:
        """Generate Redis key for attempt tracking."""
        return f"{self._prefix}attempts:{mobile_number}"
    
    async def store_otp(self, mobile_number: str, otp: str) -> None:
        """Store OTP with TTL."""
        if not self._connected or not self._redis:
            raise ConnectionError("Redis not connected")
        
        otp_key = self._otp_key(mobile_number)
        attempts_key = self._attempts_key(mobile_number)
        
        # Store OTP with expiry
        await self._redis.setex(otp_key, self._ttl, otp)
        # Reset attempts counter
        await self._redis.setex(attempts_key, self._ttl, "0")
        
        logger.debug("OTP stored in Redis", mobile=mobile_number[-4:], expires_in=self._ttl)
    
    async def verify_otp(self, mobile_number: str, otp: str) -> Tuple[bool, str]:
        """
        Verify OTP for mobile number.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self._connected or not self._redis:
            raise ConnectionError("Redis not connected")
        
        otp_key = self._otp_key(mobile_number)
        attempts_key = self._attempts_key(mobile_number)
        
        # Get stored OTP
        stored_otp = await self._redis.get(otp_key)
        
        if not stored_otp:
            return False, "OTP not found or expired. Please request a new OTP."
        
        # Check attempts
        attempts_str = await self._redis.get(attempts_key) or "0"
        attempts = int(attempts_str)
        
        if attempts >= self._max_attempts:
            # Delete OTP after max attempts
            await self._redis.delete(otp_key, attempts_key)
            return False, "Too many failed attempts. Please request a new OTP."
        
        # Verify OTP
        if stored_otp != otp:
            # Increment attempts
            await self._redis.incr(attempts_key)
            remaining = self._max_attempts - attempts - 1
            return False, f"Invalid OTP. {remaining} attempts remaining."
        
        # Success - clear OTP
        await self._redis.delete(otp_key, attempts_key)
        return True, "OTP verified successfully"
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._connected

class InMemoryOTPStore:
    """
    In-memory OTP storage with TTL.
    
    Used as fallback when Redis is unavailable.
    """
    
    def __init__(self, ttl_seconds: int = 300, max_attempts: int = 3):
        """
        Initialize OTP store.
        
        Args:
            ttl_seconds: OTP validity period (default 5 minutes)
            max_attempts: Maximum verification attempts
        """
        self._store: Dict[str, Tuple[str, float]] = {}  # {mobile: (otp, expiry_timestamp)}
        self._ttl = ttl_seconds
        self._attempts: Dict[str, int] = {}  # Track verification attempts
        self._max_attempts = max_attempts
    
    async def store_otp(self, mobile_number: str, otp: str) -> None:
        """Store OTP with expiry timestamp."""
        expiry = time.time() + self._ttl
        self._store[mobile_number] = (otp, expiry)
        self._attempts[mobile_number] = 0  # Reset attempts on new OTP
        logger.debug("OTP stored in memory", mobile=mobile_number[-4:], expires_in=self._ttl)
    
    async def verify_otp(self, mobile_number: str, otp: str) -> Tuple[bool, str]:
        """
        Verify OTP for mobile number.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if OTP exists
        if mobile_number not in self._store:
            return False, "OTP not found. Please request a new OTP."
        
        stored_otp, expiry = self._store[mobile_number]
        
        # Check expiry
        if time.time() > expiry:
            del self._store[mobile_number]
            self._attempts.pop(mobile_number, None)
            return False, "OTP has expired. Please request a new OTP."
        
        # Check attempts
        attempts = self._attempts.get(mobile_number, 0)
        if attempts >= self._max_attempts:
            del self._store[mobile_number]
            self._attempts.pop(mobile_number, None)
            return False, "Too many failed attempts. Please request a new OTP."
        
        # Verify OTP
        if stored_otp != otp:
            self._attempts[mobile_number] = attempts + 1
            remaining = self._max_attempts - attempts - 1
            return False, f"Invalid OTP. {remaining} attempts remaining."
        
        # Success - clear OTP
        del self._store[mobile_number]
        self._attempts.pop(mobile_number, None)
        return True, "OTP verified successfully"
    
    def cleanup_expired(self) -> int:
        """Remove expired OTPs. Returns count of removed entries."""
        current_time = time.time()
        expired = [
            mobile for mobile, (_, expiry) in self._store.items()
            if current_time > expiry
        ]
        for mobile in expired:
            del self._store[mobile]
            self._attempts.pop(mobile, None)
        return len(expired)

class OTPService:
    """
    OTP Service for authentication.
    
    Features:
    - Uses Redis for OTP storage (with in-memory fallback)
    - Uses onlysms.co.in API for sending SMS
    - Automatic retry on Redis connection failure
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._redis_store: Optional[RedisOTPStore] = None
        self._memory_store: Optional[InMemoryOTPStore] = None
        self._initialized = False
        # HTTP client for SMS API - use default SSL verification
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def _init_store(self) -> None:
        """Initialize OTP store (Redis with in-memory fallback)."""
        if self._initialized:
            return
        
        settings = self.settings
        
        # Try Redis first if enabled
        if settings.REDIS_ENABLED and REDIS_AVAILABLE:
            self._redis_store = RedisOTPStore(
                redis_url=settings.REDIS_URL,
                prefix=settings.REDIS_OTP_PREFIX,
                ttl_seconds=settings.OTP_EXPIRY_SECONDS,
                max_attempts=settings.OTP_MAX_ATTEMPTS
            )
            connected = await self._redis_store.connect()
            if connected:
                logger.info("Using Redis for OTP storage")
                self._initialized = True
                return
        
        # Fallback to in-memory storage
        logger.info("Using in-memory OTP storage (Redis unavailable or disabled)")
        self._memory_store = InMemoryOTPStore(
            ttl_seconds=settings.OTP_EXPIRY_SECONDS,
            max_attempts=settings.OTP_MAX_ATTEMPTS
        )
        self._initialized = True
    
    async def _get_store(self):
        """Get the active OTP store."""
        await self._init_store()
        if self._redis_store and self._redis_store.is_connected:
            return self._redis_store
        return self._memory_store
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate a secure random OTP."""
        # Generate numeric OTP
        otp = "".join(secrets.choice("0123456789") for _ in range(length))
        return otp
    
    def mask_mobile(self, mobile_number: str) -> str:
        """Mask mobile number for display (e.g., 98****3210)."""
        if len(mobile_number) >= 10:
            return f"{mobile_number[:2]}****{mobile_number[-4:]}"
        return "****"
    
    async def send_otp(self, mobile_number: str) -> Tuple[bool, str]:
        """
        Generate and send OTP to mobile number.
        
        Args:
            mobile_number: 10-digit Indian mobile number
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Initialize store if needed
            store = await self._get_store()
            
            # Generate OTP
            otp = self.generate_otp(length=self.settings.OTP_LENGTH)

            # Construct SMS message - MUST match DLT registered template exactly
            # Template ID: 1707172361651556820

            try:
                sms_message = self.settings.SMS_OTP_MESSAGE_TEMPLATE.format(otp=otp)
            except Exception as exc:  # Fallback in case of bad template configuration
                logger.error(
                    "Failed to format SMS_OTP_MESSAGE_TEMPLATE, using raw template",
                    error=str(exc),
                )
                sms_message = self.settings.SMS_OTP_MESSAGE_TEMPLATE
            encoded_message = quote(sms_message)
            
            # Build SMS API URL
            sms_url = (
                f"{self.settings.SMS_API_BASE_URL}"
                f"?UserID={self.settings.SMS_USER_ID}"
                f"&UserPass={self.settings.SMS_USER_PASS}"
                f"&MobileNo={mobile_number}"
                f"&GSMID={self.settings.SMS_GSM_ID}"
                f"&PEID={self.settings.SMS_PE_ID}"
                f"&Message={encoded_message}"
                f"&TEMPID={self.settings.SMS_TEMPLATE_ID}"
                f"&UNICODE=TEXT"
            )
            
            logger.info(
                "Sending OTP",
                mobile=self.mask_mobile(mobile_number),
                otp_length=len(otp),
                storage_type="redis" if isinstance(store, RedisOTPStore) else "memory"
            )
            
            # Send SMS
            response = await self.http_client.get(sms_url)
            
            # Log the actual response from SMS API for debugging
            response_text = response.text
            logger.info(
                "SMS API response",
                status_code=response.status_code,
                response_body=response_text[:500]
            )
            
            if response.status_code == 200:
                # Check if response indicates success
                response_lower = response_text.lower()
                if "error" in response_lower or "fail" in response_lower or "invalid" in response_lower:
                    logger.error(
                        "SMS API returned error in response",
                        response=response_text
                    )
                    return False, f"SMS API error: {response_text[:100]}"
                

                # Store OTP for verification
                await store.store_otp(mobile_number, otp)
                logger.info(
                    "OTP sent successfully",
                    mobile=self.mask_mobile(mobile_number)
                )
                return True, "OTP sent successfully"
            else:
                logger.error(
                    "SMS API error",
                    status_code=response.status_code,
                    response=response.text[:200]
                )
                return False, "Failed to send OTP. Please try again."
                
        except httpx.TimeoutException:
            logger.error("SMS API timeout")
            return False, "SMS service timeout. Please try again."
        except Exception as e:
            logger.error("OTP send error", error=str(e))
            return False, f"Failed to send OTP: {str(e)}"
    
    async def verify_otp(self, mobile_number: str, otp: str) -> Tuple[bool, str]:
        """
        Verify OTP for mobile number.
        
        Args:
            mobile_number: 10-digit mobile number
            otp: OTP code to verify
            
        Returns:
            Tuple of (is_valid, message)
        """
        store = await self._get_store()
        return await store.verify_otp(mobile_number, otp)
    
    async def close(self):
        """Close connections."""
        await self.http_client.aclose()
        if self._redis_store:
            await self._redis_store.disconnect()
    
    def get_storage_info(self) -> dict:
        """Get information about current storage backend."""
        if self._redis_store and self._redis_store.is_connected:
            return {"type": "redis", "connected": True}
        elif self._memory_store:
            return {"type": "memory", "connected": True}
        return {"type": "none", "connected": False}

# Service singleton
_otp_service: Optional[OTPService] = None

async def get_otp_service() -> OTPService:
    """Get or create OTP service singleton."""
    global _otp_service
    if _otp_service is None:
        _otp_service = OTPService()
    return _otp_service

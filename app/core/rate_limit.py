from fastapi import Request, HTTPException
from redis.exceptions import RedisError
from app.core.redis import redis_client

RATE_LIMIT = 5
WINDOW_SECONDS = 60

def rate_limiter(request: Request):
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"

    try:
        current_count = redis_client.incr(key)

        if current_count == 1:
            redis_client.expire(key, WINDOW_SECONDS)

        if current_count > RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

    except HTTPException:
        # IMPORTANT: re-raise it
        raise

    except RedisError:
        # Redis down → fail open
        return

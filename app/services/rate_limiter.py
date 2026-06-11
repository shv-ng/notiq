import logging
import time
import uuid

from app.core import redis_client

logger = logging.getLogger(__name__)


def is_rate_limited(tenant_id: int, limit: int = 100, window_seconds: int = 60) -> bool:
    key = f"ratelimit:{tenant_id}"

    now_ms = int(time.time() * 1000)
    window_start_ms = now_ms - window_seconds * 1000

    member_id = f"{now_ms}:{uuid.uuid4().hex[:8]}"

    pipeline = redis_client.pipeline()

    try:
        pipeline.zremrangebyscore(key, 0, window_start_ms)
        pipeline.zadd(key, {member_id: now_ms})
        pipeline.zcard(key)
        pipeline.expire(key, window_seconds)

        results = pipeline.execute()
        cardinality = results[2]

        if cardinality >= limit:
            return True
        return False

    except Exception as e:
        logger.error(f"Error while removing rate limit members: {e}")
        return False

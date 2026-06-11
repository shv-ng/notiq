from redis import Redis

from .config import settings

r = Redis.from_url(settings.REDIS_URL)

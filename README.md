## Notification/Webhook Delivery Engine

Real problem every product has. Non-trivial backend concerns:

- delivery guarantees (at-least-once), retry with exponential backoff
- Celery + Redis for async dispatch
- per-tenant rate limiting
- webhook signature verification (HMAC)
- delivery log + dead-letter queue
- subscription management API Stack: FastAPI, PostgreSQL, Celery, Redis, Docker. 

No LLM needed — pure backend story.

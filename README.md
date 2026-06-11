# NotiQ — Webhook Delivery Engine

A multi-tenant webhook delivery service. Tenants subscribe to event types with target URLs; you fire an event, NotiQ fans it out, retries on failure, and parks dead deliveries in a DLQ for replay.

---

## What this is

- **Multi-tenant** — each tenant auth'd via hashed API key, fully isolated
- **Async delivery** — Celery workers handle fan-out; API returns 202 immediately
- **Retry with backoff** — up to 5 retries, countdown = `5^attempt` seconds
- **Dead Letter Queue** — exhausted retries land here; replay or resolve via API
- **Signed payloads** — every webhook includes `X-Webhook-Signature: sha256=<hmac>`
- **Per-tenant rate limiting** — sliding window via Redis sorted sets (100 req/60s default)
- **Delivery logs** — full attempt history with HTTP status, latency, error

---

## Architecture

```
Client
  │
  ▼
┌─────────────────────────────────────┐
│  FastAPI  (app:8000)                │
│                                     │
│  POST /events  ──► fan-out loop     │
│                        │            │
│                  dispatch_event     │
│                  .delay() × N subs  │
└────────────────────────┬────────────┘
                         │ enqueue
                         ▼
                  ┌─────────────┐
                  │    Redis    │◄── rate limiter (sorted sets)
                  │   (broker)  │
                  └──────┬──────┘
                         │ consume
                         ▼
              ┌─────────────────────┐
              │   Celery Worker     │
              │                     │
              │  is_rate_limited?   │
              │    └─ yes → retry   │
              │                     │
              │  deliver_event()    │
              │  (httpx POST)       │
              │    ├─ 2xx → log ✓   │
              │    └─ fail → retry  │
              │         └─ max → DLQ│
              └──────────┬──────────┘
                         │ write
                         ▼
              ┌─────────────────────┐
              │     PostgreSQL      │
              │                     │
              │  tenant             │
              │  subscription       │
              │  delivery_log       │
              │  deadletterqueue    │
              └─────────────────────┘
```

---

## Quick start

```bash
cp example.env .env
docker compose up --build
```

Migrations run automatically on container start.

### End-to-end in 3 curls

**1. Create tenant**
```bash
curl -s -X POST http://localhost:8000/tenants/ \
  -H "Content-Type: application/json" \
  -d '{"name": "acme"}' | tee /tmp/tenant.json
```
Grab `api_key` from response — shown **once only**.

**2. Subscribe to an event**
```bash
curl -s -X POST http://localhost:8000/subscriptions/ \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: <your_api_key>" \
  -d '{"event_type": "order.created", "target_url": "https://webhook.site/<your-id>"}'
```

**3. Fire an event**
```bash
curl -s -X POST http://localhost:8000/events/ \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: <your_api_key>" \
  -d '{"event_type": "order.created", "payload": {"order_id": 42}}'
```

Response `202 Accepted` → worker picks up → your URL receives signed POST.

---

## API reference

All routes (except `POST /tenants/`) require `X-Api-Key` header.

### Tenants
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/tenants/` | Create tenant, returns `api_key` (once) |
| `GET` | `/tenants/me` | Get current tenant |
| `DELETE` | `/tenants/` | Delete current tenant |

### Subscriptions
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/subscriptions/` | Create subscription |
| `GET` | `/subscriptions/` | List active subscriptions (filter: `?event_type=`) |
| `GET` | `/subscriptions/{id}` | Get subscription |
| `DELETE` | `/subscriptions/{id}` | Soft-delete (sets `is_active=false`) |

### Events
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/events/` | Dispatch event to all matching subscribers |

Body: `{ "event_type": str, "payload": {}, "event_id": str (auto-generated) }`

Returns `202` if queued, `200` if no subscribers.

### Delivery Logs
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/delivery-logs/` | List logs (filter: `event_id`, `subscription_id`, `success`) |
| `GET` | `/delivery-logs/stats` | Aggregate stats (totals, success rate, avg latency) |

### Dead Letter Queue
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/dlq/` | List unresolved DLQ entries |
| `POST` | `/dlq/{id}/replay` | Re-enqueue event for delivery |
| `POST` | `/dlq/{id}/resolve` | Mark resolved without replay |

---

## Webhook signing

Every delivery includes:
```
X-Webhook-Signature: sha256=<hex>
```

HMAC-SHA256 over the raw JSON payload bytes, keyed with `SECRET_KEY`. Verify on receiver:

```python
import hashlib, hmac

expected = hmac.new(SECRET_KEY.encode(), raw_body, hashlib.sha256).hexdigest()
assert f"sha256={expected}" == request.headers["X-Webhook-Signature"]
```

---

## Retry + DLQ behavior

Failed deliveries (non-2xx or network error) retry with exponential backoff:

| Attempt | Delay |
|---------|-------|
| 1 | immediate |
| 2 | 25s |
| 3 | 125s |
| 4 | 625s |
| 5 | 3125s |

After `CELERY_MAX_RETRIES` exhausted → pushed to DLQ. On successful retry of a DLQ event, all matching DLQ entries for that `(subscription_id, event_id)` are auto-resolved.

Rate-limited deliveries retry after 60s flat (not counted against max retries).

---

## Rate limiting

Sliding window per tenant: **100 events / 60 seconds** (configurable in `is_rate_limited()`).

Implemented via Redis sorted sets — members are timestamped UUIDs, expired outside window on each check. On Redis failure, defaults to **not** rate-limiting (fail open).

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `postgres` | DB user |
| `POSTGRES_PASSWORD` | `postgres` | DB password |
| `POSTGRES_HOST` | `postgres` | DB host |
| `POSTGRES_POST` | `5432` | DB port |
| `POSTGRES_DB` | `postgres` | DB name |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `SECRET_KEY` | `abc123` | HMAC signing key — **change in prod** |
| `CELERY_MAX_RETRIES` | `5` | Max delivery attempts before DLQ |


---
 
## Performance
 
Benchmarked locally (Docker, single Celery worker) using [`hey`](https://github.com/rakyll/hey).
 
### Event ingestion — `POST /events/`
 
| Concurrency | Requests | RPS | p50 | p95 | p99 |
|-------------|----------|-----|-----|-----|-----|
| 50 | 1000 | 114 | 384ms | 824ms | 1210ms |
| 200 | 200 | ~10 | 652ms | 828ms | — |
 
At c=50 all 1000 requests returned `202`. At c=200 the app saturated — 177/200 timed out client-side (default `hey` timeout). Bottleneck is synchronous SQLAlchemy session acquisition under high concurrency; connection pool exhaustion, not business logic.
 
### Delivery log reads — `GET /delivery-logs/`
 
| Concurrency | Requests | RPS | p50 | p95 | p99 |
|-------------|----------|-----|-----|-----|-----|
| 20 | 500 | 124 | 145ms | 259ms | 323ms |
 
Each response ~12 KB (50 logs). Stable under load, no errors.
 
### Query plan — delivery log fetch
 
```
SELECT * FROM deliverylog WHERE tenant_id = 1 ORDER BY created_at DESC LIMIT 50;
 
Execution Time: 0.900 ms  |  Planning Time: 6.035 ms
Rows examined: 99  →  50 returned  (quicksort, 38kB memory)
```
 
Seq scan on `deliverylog` is acceptable at current data volume — `tenant_id` index exists but planner prefers seq scan when row count is low. Will switch to index scan as table grows; no action needed now.
 

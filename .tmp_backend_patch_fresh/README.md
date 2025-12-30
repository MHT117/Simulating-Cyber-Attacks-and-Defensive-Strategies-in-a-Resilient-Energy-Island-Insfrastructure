# Backend patch (optional): defense middleware + runtime toggle

Use this **only if you want a clean, predictable “defended” mode**.

## 1) Add the middleware

In `config/settings.py` (or your settings module), add:

```python
MIDDLEWARE = [
    "api.abuse_middleware.AbuseProtectionMiddleware",
    # ... keep the rest of your middleware after it
]
```

If you already have a middleware stack, place it near the top so it blocks early.

## 2) Configure Redis cache (recommended)

If you already use Redis, set Django cache to Redis. Example:

```python
CACHES = {
  "default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": "redis://127.0.0.1:6379/1",
  }
}
```

(If you already have this, don’t change it.)

## 3) Enable defenses

Option A (simple): restart your backend with env var

```powershell
$env:EGISLAND_DEFENSE_ENABLED="1"
$env:EGISLAND_DEFENSE_MAX_REQUESTS="50"
$env:EGISLAND_DEFENSE_WINDOW_SECONDS="10"
$env:EGISLAND_DEFENSE_BLOCK_STATUS="403"  # avoid 429 if you want
```

Option B (runtime toggle): add endpoints + a secret key (local only)

In `api/urls.py` (or wherever you include api routes):

```python
from django.urls import include, path

urlpatterns += [
    path("api/admin/", include("api.defense_urls")),
]
```

Set the toggle key:

```powershell
$env:EGISLAND_DEFENSE_TOGGLE_KEY="some-long-secret"
```

Then toggle:

```powershell
curl -X POST http://127.0.0.1:8000/api/admin/defense/on  -H "X-DEFENSE-KEY: some-long-secret"
curl -X POST http://127.0.0.1:8000/api/admin/defense/off -H "X-DEFENSE-KEY: some-long-secret"
```

## 4) What you should see

- Under attack with defense OFF: high 401 (bad tokens), moderate 200 (valid traffic still passes)
- Under attack with defense ON: high 403 (blocked), and **lower total work** on the backend

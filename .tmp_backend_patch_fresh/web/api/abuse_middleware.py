"""
Abuse / rate-limit middleware (defense option) for the Energy Island Django API.

Goal for the dissertation experiment:
- Under attack, you should see more 401/403 and fewer 200s.
- When defenses are ON, abusive traffic should be blocked quickly and consistently.

How it works:
- When enabled, it rate-limits by (client_ip, path) using Django cache.
- If cache is backed by Redis, this becomes multi-process safe.

Enable/disable:
- Env var: EGISLAND_DEFENSE_ENABLED=1  (default 0)
- Optional runtime toggle via cache key: "egisland:defense_enabled" (bool)
  (see defense_views.py for endpoints to set it)

Response when blocked:
- Status code controlled by EGISLAND_DEFENSE_BLOCK_STATUS (default 403)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class RateLimit:
    window_seconds: int = 10
    max_requests: int = 50


def client_ip(request) -> str:
    # If behind nginx, you might have X-Forwarded-For. Use the first IP in the list.
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


class AbuseProtectionMiddleware(MiddlewareMixin):
    """
    Apply basic rate limiting to the API.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.enabled = _env_bool("EGISLAND_DEFENSE_ENABLED", False)
        self.block_status = _env_int("EGISLAND_DEFENSE_BLOCK_STATUS", 403)

        # You can tune these per endpoint later; start simple and stable.
        self.default_limit = RateLimit(
            window_seconds=_env_int("EGISLAND_DEFENSE_WINDOW_SECONDS", 10),
            max_requests=_env_int("EGISLAND_DEFENSE_MAX_REQUESTS", 50),
        )

        # Apply to these path prefixes only (avoid admin/static)
        self.protected_prefixes = tuple(
            p.strip() for p in os.getenv(
                "EGISLAND_DEFENSE_PATH_PREFIXES",
                "/api/auth/token/,/api/secure/ping,/api/secure/state"
            ).split(",")
            if p.strip()
        )

    def _runtime_enabled(self) -> bool:
        # runtime override wins if present
        v = cache.get("egisland:defense_enabled")
        if v is None:
            return self.enabled
        return bool(v)

    def _limit_for_path(self, path: str) -> RateLimit:
        # Example: stricter on token endpoint
        if path.startswith("/api/auth/token"):
            return RateLimit(window_seconds=self.default_limit.window_seconds, max_requests=max(10, self.default_limit.max_requests // 2))
        return self.default_limit

    def process_request(self, request):
        if not self._runtime_enabled():
            return None

        path = request.path or ""
        if not any(path.startswith(pref) for pref in self.protected_prefixes):
            return None

        ip = client_ip(request)
        limit = self._limit_for_path(path)

        now = int(time.time())
        window = now // max(1, limit.window_seconds)
        key = f"egisland:rl:{ip}:{path}:{window}"

        # cache.add returns True if key was added (i.e., first request)
        if cache.add(key, 1, timeout=limit.window_seconds + 2):
            return None

        try:
            count = cache.incr(key)
        except Exception:
            # Some cache backends don't support incr; fallback to get+set
            count = int(cache.get(key, 1)) + 1
            cache.set(key, count, timeout=limit.window_seconds + 2)

        if count > limit.max_requests:
            return JsonResponse(
                {
                    "detail": "Blocked by rate limit",
                    "reason": "rate_limit",
                    "path": path,
                },
                status=self.block_status,
            )

        return None

import os

import redis
from django.http import JsonResponse

REDIS_HOST = os.getenv("ABUSE_REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("ABUSE_REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("ABUSE_REDIS_DB", "1"))

# Safety: don't block localhost by default (set ABUSE_ALLOW_LOCAL=0 to test)
ALLOW_LOCAL = os.getenv("ABUSE_ALLOW_LOCAL", "1") == "1"

# Thresholds (tune later; keep modest for first run)
WINDOW_SECONDS = int(os.getenv("ABUSE_WINDOW_SECONDS", "60"))
MAX_401 = int(os.getenv("ABUSE_MAX_401", "15"))
BLOCK_SECONDS = int(os.getenv("ABUSE_BLOCK_SECONDS", "600"))

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
)


def _client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


class AbuseBlockMiddleware:
    """
    - If IP is blocked => return 403 for API routes.
    - If IP causes too many 401s on auth/secure endpoints => block for BLOCK_SECONDS.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""
        ip = _client_ip(request)

        if ALLOW_LOCAL and ip in ("127.0.0.1", "::1"):
            return self.get_response(request)

        protect = path.startswith("/api/auth/") or path.startswith("/api/secure/")
        if protect:
            if r.exists(f"abuse:block:{ip}"):
                return JsonResponse({"detail": "blocked"}, status=403)

        response = self.get_response(request)

        if protect and response.status_code == 401:
            key = f"abuse:401:{ip}"
            count = r.incr(key)
            if count == 1:
                r.expire(key, WINDOW_SECONDS)
            if count >= MAX_401:
                r.setex(f"abuse:block:{ip}", BLOCK_SECONDS, "1")

        return response

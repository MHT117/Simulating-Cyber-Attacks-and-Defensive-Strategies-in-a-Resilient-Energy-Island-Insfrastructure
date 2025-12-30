"""
Optional defense toggle endpoints.
Only enable these in local/dev environments.

Add to urls.py under something like:
  path("api/admin/", include("api.defense_urls"))

Then:
  POST /api/admin/defense/on   with header X-DEFENSE-KEY: <key>
  POST /api/admin/defense/off  with header X-DEFENSE-KEY: <key>
"""

from __future__ import annotations

import os
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST


def _auth_ok(request) -> bool:
    expected = os.getenv("EGISLAND_DEFENSE_TOGGLE_KEY", "")
    if not expected:
        # If no key set, disable endpoints by default.
        return False
    got = request.headers.get("X-DEFENSE-KEY", "")
    return got == expected


@require_POST
def defense_on(request):
    if not _auth_ok(request):
        return JsonResponse({"detail": "forbidden"}, status=403)
    cache.set("egisland:defense_enabled", True, timeout=None)
    return JsonResponse({"defense_enabled": True})


@require_POST
def defense_off(request):
    if not _auth_ok(request):
        return JsonResponse({"detail": "forbidden"}, status=403)
    cache.set("egisland:defense_enabled", False, timeout=None)
    return JsonResponse({"defense_enabled": False})

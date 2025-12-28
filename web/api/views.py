from time import time
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from .metrics_custom import experiment_marker_total


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def state_public(request):
    return JsonResponse({
        "ts": int(time()),
        "mw_generation": 120.5,
        "mw_demand": 115.2,
        "storage": {"level_pct": 62.0},
        "stakeholders": {"gov": 84, "ngo": 77, "inv": 69, "com": 72},
        "tick": 1,
    })
state_public.throttle_scope = "public_state"


@api_view(["POST"])
@permission_classes([AllowAny])
def mark(request):
    name = (request.data.get("name") or "unknown")
    experiment_marker_total.labels(name=name).inc()
    return JsonResponse({"marked": name})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def state_secure(request):
    # RBAC stub: add role checks here later
    return JsonResponse({"ok": True, "user": str(request.user), "scope": "secure_state"})
state_secure.throttle_scope = "secure"


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def ping_secure(request):
    return JsonResponse({"pong": True, "user": str(request.user)})
ping_secure.throttle_scope = "secure"

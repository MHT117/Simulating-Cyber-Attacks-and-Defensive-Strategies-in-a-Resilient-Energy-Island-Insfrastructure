from time import time
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated


@api_view(["GET"])
@permission_classes([AllowAny])
def state_public(request):
    return JsonResponse({
        "ts": int(time()),
        "mw_generation": 120.5,
        "mw_demand": 115.2,
        "storage": {"level_pct": 62.0},
        "stakeholders": {"gov": 84, "ngo": 77, "inv": 69, "com": 72},
        "tick": 1,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def state_secure(request):
    # RBAC stub: add role checks here later
    return JsonResponse({"ok": True, "user": str(request.user), "scope": "secure_state"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ping_secure(request):
    return JsonResponse({"pong": True, "user": str(request.user)})

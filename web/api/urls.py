from django.urls import path
from .views import state_public, state_secure, ping_secure, mark
from .auth_views import TokenObtainPairThrottledView, TokenRefreshThrottledView

urlpatterns = [
    # Auth (JWT) throttled
    path("auth/token/", TokenObtainPairThrottledView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshThrottledView.as_view(), name="token_refresh"),

    # Public (no token)
    path("state", state_public),
    path("state/", state_public),
    path("mark/", mark),

    # Secure (JWT required)
    path("secure/state", state_secure),
    path("secure/state/", state_secure),
    path("secure/ping", ping_secure),
    path("secure/ping/", ping_secure),
]

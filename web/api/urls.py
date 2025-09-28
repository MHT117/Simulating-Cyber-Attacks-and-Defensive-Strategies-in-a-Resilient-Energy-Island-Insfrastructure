from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import state_public, state_secure, ping_secure

urlpatterns = [
    # Auth (JWT)
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Public (no token)
    path("state", state_public),
    path("state/", state_public),

    # Secure (JWT required)
    path("secure/state", state_secure),
    path("secure/state/", state_secure),
    path("secure/ping", ping_secure),
    path("secure/ping/", ping_secure),
]

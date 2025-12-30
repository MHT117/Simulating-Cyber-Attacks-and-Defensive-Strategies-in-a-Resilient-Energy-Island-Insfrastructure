from django.urls import path
from . import defense_views

urlpatterns = [
    path("defense/on", defense_views.defense_on, name="defense_on"),
    path("defense/off", defense_views.defense_off, name="defense_off"),
]

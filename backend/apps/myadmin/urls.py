from django.urls import path
from .views import *

urlpatterns = [
    path("plans/", PlanCreateView.as_view(), name="plans"),
]
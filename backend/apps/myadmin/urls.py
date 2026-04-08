from django.urls import path
from .views import *

urlpatterns = [
    path("plans/", PlanCreate.as_view(), name="plans"),
    path("plansView/", PlanCreateView.as_view(), name="plansView"),
]
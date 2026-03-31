from django.urls import path
from .views import SubmitCompanyView

urlpatterns = [
    path('submit-company/', SubmitCompanyView.as_view(), name='submit-comapny'),
]
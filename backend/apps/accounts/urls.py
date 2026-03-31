from django.urls import path
from .views import SubmitNameView

urlpatterns = [
    path('submit-name/', SubmitNameView.as_view(), name='submit-name'),
]
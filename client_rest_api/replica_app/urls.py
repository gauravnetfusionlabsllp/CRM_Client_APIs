
from django.urls import path
from .views import *

urlpatterns = [
   path('check-email/', CheckEmail.as_view(), name="check-email")
]
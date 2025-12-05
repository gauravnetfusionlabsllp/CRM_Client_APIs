
from django.urls import path
from apps.dashboard_admin.views import FinancialTransaction, UpdatePSPRate

urlpatterns = [
    path('transactions/', FinancialTransaction.as_view(), name="transactions"),
    path('update-psp-rate/', UpdatePSPRate.as_view(), name="update-psp-rate"),
    path('get-psp-rate/', UpdatePSPRate.as_view(), name="get-psp-rate")
]
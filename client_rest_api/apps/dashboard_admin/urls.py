
from django.urls import path
from apps.dashboard_admin.views import FinancialTransaction

urlpatterns = [
    path('transactions/', FinancialTransaction.as_view(), name="transactions")
]
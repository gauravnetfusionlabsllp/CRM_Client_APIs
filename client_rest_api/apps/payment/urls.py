
from django.urls import path
from apps.payment import views

urlpatterns = [
   path('jenapay-pay-in/', views.JenaPayPayIn.as_view(), name="jenapay-pay-in"),
   path('cheezeepay-upi-payin/', views.CheezeePayUPIPayIN.as_view(), name='cheesepay-upi-payin'),

   # --------------------------Webhook---------------------------

   path('cheezeepay-upi-payin-webhook/', views.CheezeePayInCallBackWebhook.as_view(), name='cheezeepay-upi-payin-webhook'),
]

from django.urls import path
from apps.payment import views

urlpatterns = [
   path('jenapay-pay-in/', views.JenaPayPayIn.as_view(), name="jenapay-pay-in"),
   path('cheezeepay-upi-payin/', views.CheezeePayUPIPayIN.as_view(), name='cheesepay-upi-payin'),

   
   path('match2pay-pay-in/', views.Match2PayPayIn.as_view(), name="match2pay-pay-in"),
   path('match2pay-pay-in-webhook/', views.Match2PayPayInWebHook.as_view(), name="match2pay-pay-in-webhook"),

   # --------------------------Webhook---------------------------

   path('cheezeepay-upi-payin-webhook/', views.CheezeePayInCallBackWebhook.as_view(), name='cheezeepay-upi-payin-webhook'),
   path('jenapay-payin-webhook/', views.JenaPayPayInCallBack.as_view(), name="jenapay-payin-webhook"),
]
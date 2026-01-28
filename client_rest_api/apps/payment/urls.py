
from django.urls import path
from apps.payment import views

urlpatterns = [
   path('jenapay-pay-in/', views.JenaPayPayIn.as_view(), name="jenapay-pay-in"),
   path('cheezeepay-upi-payin/', views.CheezeePayUPIPayIN.as_view(), name='cheesepay-upi-payin'),
   path('cheezeepay-upi-payout/', views.CheezeePayUPIPayOut.as_view(), name='cheesepay-upi-payin'),

   
   path('acc-transfer/', views.BankTransfer.as_view(), name="acc-transfer"),
   path('match2pay-pay-in/', views.Match2PayPayIn.as_view(), name="match2pay-pay-in"),
   path('match2pay-pay-in-webhook/', views.Match2PayPayInWebHook.as_view(), name="match2pay-pay-in-webhook"),
   path('match2pay-pay-out-webhook/', views.Match2PayPayOutWebHook.as_view(), name="match2pay-pay-out-webhook"),


   path('withdrawal-request/', views.WithdrawalRequest.as_view(), name="withdrawal-request"),
   path('withdrawal-request/<int:pk>/', views.WithdrawalRequest.as_view(), name="withdrawal-request"),

   # --------------------------Webhook---------------------------

   path('cheezeepay-upi-payin-webhook/', views.CheezeePayInCallBackWebhook.as_view(), name='cheezeepay-upi-payin-webhook'),
   path('jenapay-payin-webhook/', views.JenaPayPayInCallBack.as_view(), name="jenapay-payin-webhook"),

   path('cheezeepay-upi-payout-webhook/', views.CheezeePayOutWebhook.as_view(), name="cheezeepay-upi-payin-webhook"),



   path('banking-details/', views.BankingDetailsRequest.as_view(), name="banking-details"),


   # -------------------------------Withdrawal OTP Verification ----------------------------

   path('withdrawal-request-otp/', views.SendWithdrawalRequestOTP.as_view(), name="Send-Withdrawal-RequestOTP"),
   path('verify-withdrawal-otp/', views.VerifyWithdrawalOTP.as_view(), name="Verify-Withdrawal-OTP"),


   path('change-regulation/', views.ChangeRegulation.as_view(), name="change-regulation"),

   path('cancel-withdarawl-request/', views.CancelWithdrawalRequest.as_view(), name="cancel-withdarawl-request/"),

   path('hide-withdrawal-request/', views.HideWithdarwalRequest.as_view(), name="hide-delete-request"),

   

]